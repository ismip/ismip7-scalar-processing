"""Compute ISMIP7 scalar variables from gridded ice sheet model output.

The pipeline reads a model's ``lithk`` and ``topg`` (and, where present, the
mask and flux variables), integrates them over the whole ice sheet and
optionally over IMBIE3 basins, and writes one time series per variable.  See
:doc:`../user/running` for the command line and :doc:`../user/output` for what
comes out.

Originally written as a script by Heiko Goelzer 2026 (heig@norceresearch.no).
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass, field
from types import SimpleNamespace

import netCDF4 as nc
import numpy as np

from ismip7_scalars import __version__
from ismip7_scalars.naming import (
    DEFAULTS,
    FILE_CONFIG,
    MissingInput,
    configid_to_exp_group,
    find_model_file,
    make_file_stem,
    make_out_stem,
    region_display_name,
    resolution_string,
)
from ismip7_scalars.slc import slc_A2020, slc_G2020, slc_vaf
from ismip7_scalars.variables import variable_metadata
from ismip7_scalars.writers import (
    TimeAxis,
    warn_years_out_of_range,
    write_scalar_nc,
    write_slc_csv,
)

#: Ocean area used to convert an ice volume to a sea-level equivalent,
#: Gregory et al. (2019).
OCEAN_AREA = 3.625e14  # m2

#: Output format switches, per class of scalar.  SLC without GIC masking is
#: the headline product and gets both forms; the GIC-masked variant is what the
#: sea-level community consumes as CSV.
FLG_SLC_NC = True       # SLC, no GIC masking: write NetCDF
FLG_SLC_CSV = True      # SLC, no GIC masking: write CSV
FLG_SLC_GIC_NC = False  # SLC, GIC masked:     write NetCDF
FLG_SLC_GIC_CSV = True  # SLC, GIC masked:     write CSV
FLG_ST_NC = True        # ST scalars:          write NetCDF
FLG_FL_NC = True        # FL scalars:          write NetCDF

#: A2020 mode.  ``True`` accumulates step by step across the historical and
#: projection runs seamlessly and offsets the result to zero at the reference
#: year; ``False`` evaluates every step against the reference state directly.
FLG_A20_CUMUL = True

#: The three SLC methods, as ``(variable name, long name)``.  These are the one
#: class of output not in the ISMIP7 data request -- a sea-level contribution
#: is derived here rather than submitted by a model -- so their metadata is
#: this package's own rather than read from isschecker.
SLC_SPECS = (
    ('slvaf', 'Sea level contribution based on Vaf'),
    ('slg20', 'Sea level contribution based on G2020'),
    ('sla20', 'Sea level contribution based on A2020'),
)

#: ST (state) scalars this package writes.  Their standard_name, units and
#: long_name come from the ISMIP7 data request via
#: :func:`~ismip7_scalars.variables.variable_metadata`, not from here: each is
#: a requested variable in its own right, and restating its metadata is how the
#: two tools come to disagree about what it is called.
ST_SCALAR_NAMES = ('lim', 'limnsw', 'iareagr', 'iareafl')

#: FL (flux) scalars, as ``(output name, the gridded variable integrated to
#: produce it)``.  Metadata likewise comes from the data request.
FL_SCALAR_SPECS = (
    ('tendacabf', 'acabf'),
    ('tendlibmassbfgr', 'libmassbfgr'),
    ('tendlibmassbffl', 'libmassbffl'),
    ('tendlicalvf', 'licalvf'),
    ('tendlifmassbf', 'lifmassbf'),
    ('tendligroundf', 'ligroundf'),
)

#: IMBIE3 mask names per region, as ``(NetCDF variable, {name: id})``.
BASIN_MASKS = {
    'AIS': [
        # IMBIE3 regions: 1 West Antarctica, 2 East Antarctica, 3 Peninsula
        ('regions', {'wais': 1, 'eais': 2, 'pina': 3}),
        # IMBIE3 basins 1 to 18
        ('basins', {f'r{i:02d}': i for i in range(1, 19)}),
    ],
    'GrIS': [
        # IMBIE3 Mouginot basins: from NO clockwise
        ('basins', {'no': 1, 'ne': 2, 'ce': 3, 'se': 4, 'sw': 5, 'cw': 6,
                    'nw': 7}),
    ],
}


@dataclass
class Settings:
    """Everything one run needs, with every default already resolved."""

    region: str
    group: str
    model: str
    exp: str
    modelid: str
    esm: str
    forcingid: str
    configid: str
    exp_group: str
    hist: str
    hist_exp_group: str
    hist_configid: str
    datapath: str
    modelpath: str
    params_path: str
    outpath: str
    refyear: int | None = None
    histout: int = -1
    flg_mm: bool = True
    flg_bm: bool = False
    verbose: bool = False

    @property
    def exppath(self):
        """Directory holding the projection experiment's model output."""
        return os.path.join(self.modelpath, self.group, self.model,
                            self.exp_group, self.configid)

    @property
    def histpath(self):
        """Directory holding the historical experiment's model output."""
        return os.path.join(self.modelpath, self.group, self.model,
                            self.hist_exp_group, self.hist_configid)

    @property
    def params_file(self):
        """The model's ``params.nc``, holding its density parameters."""
        return os.path.join(self.params_path, self.group, self.model,
                            'params.nc')

    @property
    def ncpath(self):
        """Output directory for NetCDF, mirroring the model tree."""
        return os.path.join(self.outpath, 'nc', self.region, self.group,
                            self.model, self.exp_group, self.configid)

    @property
    def csvpath(self):
        """Output directory for CSV, flat."""
        return os.path.join(self.outpath, 'csv')

    @property
    def unit_label(self):
        """Short identifier of this run, for log lines."""
        return (f'{self.region} {self.group}/{self.model}/{self.exp_group}'
                f'/{self.configid}')


@dataclass
class Geometry:
    """The model fields a run integrates, and the time axis they sit on."""

    lithk: np.ndarray
    topg: np.ndarray
    lithk_ref: np.ndarray
    topg_ref: np.ndarray
    time_model: np.ndarray
    time_units: str
    time_long_name: str
    time_calendar: str
    time_hist: np.ndarray
    n_hist: int
    ref_idx: int
    ref_idx_exp: int | None = None
    lithk_hist: np.ndarray | None = None
    topg_hist: np.ndarray | None = None
    hist_n_out: int = 0
    hist_start: int = 0
    sftgrf: np.ndarray | None = None
    sftflf: np.ndarray | None = None
    sftgrf_hist: np.ndarray | None = None
    sftflf_hist: np.ndarray | None = None
    st_ok: bool = False
    time_out: np.ndarray = field(default_factory=lambda: np.array([]))
    nominal_yrs: list = field(default_factory=list)

    @property
    def nt(self):
        """Number of timesteps in the projection experiment."""
        return len(self.lithk)


# --------------------------------------------------------------------------
# Command line


def build_parser():
    """The ``ismip7-scalars`` command line."""
    parser = argparse.ArgumentParser(
        prog='ismip7-scalars', description='ISMIP7 scalar processing')
    parser.add_argument('--version', action='version',
                        version=f'ismip7-scalars {__version__}')
    parser.add_argument('--region', required=True, choices=['AIS', 'GrIS'],
                        help='Ice sheet region')
    parser.add_argument('--group', default=None,
                        help='Submitting group/lab')
    parser.add_argument('--model', default=None,
                        help='Ice sheet model name')
    parser.add_argument('--experiment', default=None,
                        help='Experiment name (e.g. ssp126, ctrl)')
    parser.add_argument('--modelid', '--ism-member-id', default=None,
                        help='ISM member ID (e.g. m001)')
    parser.add_argument('--esm', default=None,
                        help='Climate forcing model (e.g. NorESM2-MM)')
    parser.add_argument('--forcingid', default=None,
                        help='Forcing realization (e.g. f001)')
    parser.add_argument('--configid', default=None,
                        help='Configuration ID (e.g. C001)')
    parser.add_argument('--exp-group', default=None,
                        help='Experiment directory name (CORE, ESM, or PPE)')
    parser.add_argument('--hist', default=None,
                        help='Historical experiment name '
                             '(default: region-specific)')
    parser.add_argument('--hist-exp-group', default=None,
                        help='History experiment directory '
                             '(default: same as --exp-group)')
    parser.add_argument('--hist-configid', default=None,
                        help='Configuration ID for the hist experiment '
                             '(default: same as --configid)')
    parser.add_argument('--refyear', type=int, default=None,
                        help='Year to use as SLC reference '
                             '(default: last timestep of hist experiment)')
    parser.add_argument('--datapath', default=None,
                        help='Path to generic data files '
                             '(default: ./Data/<region>)')
    parser.add_argument('--modelpath', default=None,
                        help='Path to model output '
                             '(default: ./Models/<region>)')
    parser.add_argument('--params-path', default=None,
                        help='Root for params.nc: '
                             '<params-path>/<group>/<model>/params.nc '
                             '(default: same as --modelpath)')
    parser.add_argument('--outpath', default=None,
                        help='Root path for output (nc/ and csv/ created as '
                             'subdirectories; default: ./Output)')
    parser.add_argument('--histout', type=int, default=-1,
                        help='Hist timesteps to prepend to output: 0=none, '
                             '1=last only, -1=all (default), N=last N')
    parser.add_argument('--basins', action='store_true',
                        help='Compute per-basin and per-region integrals in '
                             'addition to the whole ice sheet')
    parser.add_argument('--no-mm', action='store_true',
                        help='Skip the whole-ice-sheet (mm) integral; '
                             'requires --basins')
    parser.add_argument('--verbose', action='store_true',
                        help='Print field shapes and integrals as they are '
                             'computed')
    return parser


def settings_from_args(args, cwd=None):
    """Resolve parsed arguments into a fully-defaulted :class:`Settings`.

    Paths default relative to ``cwd`` (the working directory by default) rather
    than to the installed package, so that an installed tool behaves the same
    way whichever checkout it is run from.
    """
    cwd = os.getcwd() if cwd is None else cwd
    region = args.region
    defaults = DEFAULTS[region]

    configid = args.configid or defaults['configid']
    exp_group = args.exp_group or configid_to_exp_group(configid)
    modelpath = args.modelpath or os.path.join(cwd, 'Models', region)

    return Settings(
        region=region,
        group=args.group or defaults['group'],
        model=args.model or defaults['model'],
        exp=args.experiment or defaults['experiment'],
        modelid=args.modelid or defaults['modelid'],
        esm=args.esm or defaults['esm'],
        forcingid=args.forcingid or defaults['forcingid'],
        configid=configid,
        exp_group=exp_group,
        hist=args.hist or defaults['hist'],
        hist_exp_group=args.hist_exp_group or exp_group,
        hist_configid=args.hist_configid or configid,
        datapath=args.datapath or os.path.join(cwd, 'Data', region),
        modelpath=modelpath,
        params_path=args.params_path or modelpath,
        outpath=args.outpath or os.path.join(cwd, 'Output'),
        refyear=args.refyear,
        histout=args.histout,
        flg_mm=not args.no_mm,
        flg_bm=args.basins,
        verbose=args.verbose,
    )


# --------------------------------------------------------------------------
# Input


def detect_resolution(settings):
    """Two-digit resolution in km, from the x-spacing of the model grid."""
    path = find_model_file(settings.exppath, 'lithk', settings.region,
                           settings.group, settings.model, settings.modelid,
                           settings.esm, settings.forcingid, settings.exp,
                           settings.configid)
    with nc.Dataset(path, 'r') as ds:
        x = ds.variables['x']
        if len(x) < 2:
            raise MissingInput(
                f'cannot detect resolution: {path} has a length-{len(x)} x '
                f'axis')
        dx_m = abs(float(x[1]) - float(x[0]))
    return resolution_string(dx_m)


def data_file(settings, res, role):
    """Path to one of the generic data files, checked for existence."""
    path = os.path.join(settings.datapath,
                        FILE_CONFIG[settings.region][role].format(res=res))
    if not os.path.exists(path):
        raise MissingInput(f'missing {role} data file {path}')
    return path


def load_masks(settings, res):
    """Load the area factors and every mask the run integrates over.

    Returns ``(regions, af2, maxmask1, iaf2GIC)`` where ``regions`` maps a mask
    name to a 0/1 field.  ``mm`` -- the whole grid -- comes first unless
    ``--no-mm`` was given.
    """
    with nc.Dataset(data_file(settings, res, 'maxmask'), 'r') as ds:
        maxmask1 = ds.variables['maxmask1'][:, :]
    with nc.Dataset(data_file(settings, res, 'af2'), 'r') as ds:
        af2 = ds.variables['af2'][:, :]
    with nc.Dataset(data_file(settings, res, 'gic'), 'r') as ds:
        iaf2GIC = ds.variables['iaf2'][:, :]

    regions = {}
    if settings.flg_mm:
        # The whole grid: the ice sheet mask is applied to the ice thickness,
        # not to the region, so `mm` really is every cell.
        regions['mm'] = maxmask1 * 0 + 1

    if settings.flg_bm:
        with nc.Dataset(data_file(settings, res, 'basins'), 'r') as ds:
            for ncvar, names in BASIN_MASKS[settings.region]:
                basinid = ds.variables[ncvar][:, :]
                for name, value in names.items():
                    regions[name] = (basinid == value).astype(float)

    if settings.verbose:
        print('af2:', af2.shape)
        print('maxmask1:', maxmask1.shape)
        print('iaf2GIC:', iaf2GIC.shape)
        for name, mask in regions.items():
            print(f'{name}: {np.sum(mask)} of {mask.size} cells')

    return regions, af2, maxmask1, iaf2GIC


def load_constants(settings):
    """Read the model's densities from ``params.nc``.

    The ocean area is *not* read from the file even where one is present:
    every submission is normalised by the same :data:`OCEAN_AREA` so that
    sea-level contributions are comparable across models.
    """
    if not os.path.exists(settings.params_file):
        raise MissingInput(
            f'missing params.nc -- expected {settings.params_file} '
            f'(generate one with ismip7-scalars-set-params, or point '
            f'--params-path at its root)')
    with nc.Dataset(settings.params_file, 'r') as ds:
        c = SimpleNamespace()
        c.RHOI = float(ds.variables['rhoi'][()])   # kg/m3
        c.RHOSW = float(ds.variables['rhow'][()])  # kg/m3
        c.RHOFW = float(ds.variables['rhof'][()])  # kg/m3
    c.AO = OCEAN_AREA  # m2
    return c


def _load_field(settings, dirpath, var, experiment, configid, required=False):
    """Load one 3D model field, or ``None`` when its file is absent."""
    path = find_model_file(dirpath, var, settings.region, settings.group,
                           settings.model, settings.modelid, settings.esm,
                           settings.forcingid, experiment, configid,
                           required=required)
    if path is None:
        return None
    with nc.Dataset(path, 'r') as ds:
        return ds.variables[var][:, :, :]


def _hist_times_on_exp_axis(time_hist, hist_units, hist_calendar,
                            exp_units, exp_calendar):
    """Re-express historical times in the projection file's time units.

    The two runs are written independently and need not share a time origin.
    Concatenating their raw numeric values would then put the historical part
    of the output at the wrong dates, so convert whenever the encodings differ.
    """
    if hist_units == exp_units and hist_calendar == exp_calendar:
        return np.asarray(time_hist)
    dates = nc.num2date(time_hist, hist_units, calendar=hist_calendar)
    return np.asarray(nc.date2num(dates, exp_units, calendar=exp_calendar))


def resolve_hist_n_out(histout, n_hist, exp_is_hist):
    """How many historical timesteps to prepend to the output.

    ``0`` when the projection *is* the historical run -- its full length is
    already written -- and otherwise ``histout`` clamped to what the historical
    run actually has.
    """
    if exp_is_hist or histout == 0:
        return 0
    if histout == -1:
        return n_hist
    if histout > n_hist:
        print(f'Warning: --histout {histout} exceeds hist length {n_hist}; '
              f'using all {n_hist} timesteps')
        return n_hist
    return histout


def load_geometry(settings):
    """Load ``lithk`` and ``topg`` for the projection and historical runs.

    Also resolves the reference state the SLC methods measure against, the
    historical timesteps to prepend, and the shared output time axis.
    """
    exp_is_hist = settings.exp == settings.hist

    # ---- projection experiment ----
    lithk_file = find_model_file(
        settings.exppath, 'lithk', settings.region, settings.group,
        settings.model, settings.modelid, settings.esm, settings.forcingid,
        settings.exp, settings.configid, required=False)
    if lithk_file is None:
        raise MissingInput(f'missing lithk for exp in {settings.exppath}')
    with nc.Dataset(lithk_file, 'r') as ds:
        lithk = ds.variables['lithk'][:, :, :]
        tv = ds.variables['time']
        time_model = tv[:]
        time_units = tv.units
        time_long_name = tv.long_name
        time_calendar = tv.calendar

    topg = _load_field(settings, settings.exppath, 'topg', settings.exp,
                       settings.configid)
    if topg is None:
        raise MissingInput(f'missing topg for exp in {settings.exppath}')

    # ---- historical experiment ----
    hist_lithk_file = find_model_file(
        settings.histpath, 'lithk', settings.region, settings.group,
        settings.model, settings.modelid, settings.esm, settings.forcingid,
        settings.hist, settings.hist_configid, required=False)
    if hist_lithk_file is None:
        raise MissingInput(f'missing lithk for hist in {settings.histpath}')

    with nc.Dataset(hist_lithk_file, 'r') as ds:
        tv = ds.variables['time']
        n_hist = len(tv)
        time_hist = _hist_times_on_exp_axis(
            tv[:], tv.units, tv.calendar, time_units, time_calendar)

        ref_in_exp = False
        if settings.refyear is not None:
            dates = nc.num2date(tv[:], tv.units, calendar=tv.calendar)
            idx = np.where(
                np.array([d.year for d in dates]) == settings.refyear)[0]
            if len(idx) > 0:
                ref_idx = int(idx[-1])
            else:
                # Not in hist; searched in the projection once it is loaded.
                ref_idx = n_hist - 1
                ref_in_exp = True
        else:
            ref_idx = n_hist - 1  # last historical timestep

        hist_n_out = resolve_hist_n_out(settings.histout, n_hist, exp_is_hist)
        hist_start = n_hist - hist_n_out

        lithk_ref = ds.variables['lithk'][ref_idx, :, :]
        # The seamless-cumulative A2020 walks the whole historical run, so it
        # needs the full array even when none of it is written out.
        need_hist_arrays = ((not exp_is_hist and FLG_A20_CUMUL)
                            or hist_n_out > 0)
        lithk_hist = ds.variables['lithk'][:, :, :] if need_hist_arrays \
            else None

    topg_hist_file = find_model_file(
        settings.histpath, 'topg', settings.region, settings.group,
        settings.model, settings.modelid, settings.esm, settings.forcingid,
        settings.hist, settings.hist_configid, required=False)
    if topg_hist_file is None:
        raise MissingInput(f'missing topg for hist in {settings.histpath}')
    with nc.Dataset(topg_hist_file, 'r') as ds:
        topg_ref = ds.variables['topg'][ref_idx, :, :]
        topg_hist = ds.variables['topg'][:, :, :] if need_hist_arrays else None

    if exp_is_hist and FLG_A20_CUMUL:
        # Same file: reuse the arrays already in memory.
        lithk_hist = lithk
        topg_hist = topg

    geom = Geometry(
        lithk=lithk, topg=topg, lithk_ref=lithk_ref, topg_ref=topg_ref,
        time_model=time_model, time_units=time_units,
        time_long_name=time_long_name, time_calendar=time_calendar,
        time_hist=time_hist, n_hist=n_hist, ref_idx=ref_idx,
        lithk_hist=lithk_hist, topg_hist=topg_hist,
        hist_n_out=hist_n_out, hist_start=hist_start)

    if ref_in_exp:
        print(f'Warning: --refyear {settings.refyear} not found in hist '
              f"experiment '{settings.hist}'; searching exp '{settings.exp}'")
        dates_exp = nc.num2date(time_model, time_units,
                                calendar=time_calendar)
        idx = np.where(
            np.array([d.year for d in dates_exp]) == settings.refyear)[0]
        if len(idx) == 0:
            raise MissingInput(
                f'--refyear {settings.refyear} not found in hist experiment '
                f"'{settings.hist}' or exp '{settings.exp}'")
        geom.ref_idx_exp = int(idx[-1])
        geom.lithk_ref = lithk[geom.ref_idx_exp, :, :]
        geom.topg_ref = topg[geom.ref_idx_exp, :, :]

    _load_st_masks(settings, geom, exp_is_hist)
    _build_time_axis(geom)
    return geom


def _load_st_masks(settings, geom, exp_is_hist):
    """Load ``sftgrf``/``sftflf``, which only the ST scalars need.

    A submission missing them still gets its SLC and FL output; only the ST
    block is skipped.
    """
    geom.sftgrf = _load_field(settings, settings.exppath, 'sftgrf',
                              settings.exp, settings.configid)
    geom.sftflf = _load_field(settings, settings.exppath, 'sftflf',
                              settings.exp, settings.configid)
    geom.st_ok = geom.sftgrf is not None and geom.sftflf is not None
    if not geom.st_ok:
        print('WARNING: sftgrf/sftflf missing -- skipping ST scalars '
              '(lim, limnsw, iareagr, iareafl)')
        return

    geom.sftgrf_hist = geom.sftgrf
    geom.sftflf_hist = geom.sftflf
    if geom.hist_n_out > 0 and not exp_is_hist:
        geom.sftgrf_hist = _load_field(settings, settings.histpath, 'sftgrf',
                                       settings.hist, settings.hist_configid)
        geom.sftflf_hist = _load_field(settings, settings.histpath, 'sftflf',
                                       settings.hist, settings.hist_configid)
        if geom.sftgrf_hist is None or geom.sftflf_hist is None:
            geom.st_ok = False
            print('WARNING: hist sftgrf/sftflf missing -- skipping ST '
                  'scalars')
        elif (len(geom.sftgrf_hist) != geom.n_hist
                or len(geom.sftflf_hist) != geom.n_hist):
            # The prepended block is indexed by the lithk time axis, so a
            # shorter mask file would silently misalign the two.
            geom.st_ok = False
            print(f'WARNING: hist sftgrf/sftflf have '
                  f'{len(geom.sftgrf_hist)}/{len(geom.sftflf_hist)} timesteps '
                  f'but hist lithk has {geom.n_hist} -- skipping ST scalars')


def _build_time_axis(geom):
    """Concatenate the historical and projection times, and their nominal years.

    ST timestamps sit at Jan 1 of year N+1, so the nominal simulation year is
    the timestamp year minus one.
    """
    if geom.hist_n_out > 0:
        geom.time_out = np.concatenate(
            [geom.time_hist[geom.hist_start:], geom.time_model])
    else:
        geom.time_out = np.asarray(geom.time_model)
    dates_out = nc.num2date(geom.time_out, geom.time_units,
                            calendar=geom.time_calendar)
    geom.nominal_yrs = [d.year - 1 for d in dates_out]


# --------------------------------------------------------------------------
# Computation


def compute_slc_series(geom, c, region_mask, af2, maxmask1, gic_mask, area_m2,
                       exp_is_hist):
    """The three SLC time series for one mask and one GIC mode.

    Returns ``(slvaf, slg20, sla20)``, each covering the prepended historical
    timesteps followed by the projection.
    """
    H0 = geom.lithk_ref * maxmask1 * gic_mask
    B0 = geom.topg_ref
    # TODO clarify if S0=0 is correct for all models
    S0 = geom.topg_ref * 0.0  # sea level fixed to 0

    A = region_mask * af2 * area_m2

    vaf_hist, g20_hist, a20_hist = [], [], []
    vaf_list, g20_list, a20_list = [], [], []

    # ---- historical portion (VAF, G2020, and non-cumulative A2020) ----
    if geom.hist_n_out > 0:
        for n in range(geom.hist_start, geom.n_hist):
            H = geom.lithk_hist[n, :, :] * maxmask1 * gic_mask
            B = geom.topg_hist[n, :, :]
            vaf_hist.append(slc_vaf.get_slc_vaf(H0, H, B0, B, S0, S0, A, c))
            g20_hist.append(slc_G2020.get_slc_G2020(H0, H, B0, B, A, c))
            if not FLG_A20_CUMUL:
                a20_hist.append(
                    slc_A2020.get_slc_A2020(H0, H, B0, B, S0, S0, A, c))

    # ---- VAF and G2020, always relative to the reference state ----
    for n in range(geom.nt):
        H = geom.lithk[n, :, :] * maxmask1 * gic_mask
        B = geom.topg[n, :, :]
        vaf_list.append(slc_vaf.get_slc_vaf(H0, H, B0, B, S0, S0, A, c))
        g20_list.append(slc_G2020.get_slc_G2020(H0, H, B0, B, A, c))

    # ---- A2020, method-dependent ----
    if not FLG_A20_CUMUL:
        for n in range(geom.nt):
            H = geom.lithk[n, :, :] * maxmask1 * gic_mask
            B = geom.topg[n, :, :]
            a20_list.append(
                slc_A2020.get_slc_A2020(H0, H, B0, B, S0, S0, A, c))
    else:
        a20_hist, a20_list = _cumulative_a2020(
            geom, c, maxmask1, gic_mask, A, S0, exp_is_hist)

    return (np.concatenate([vaf_hist, vaf_list]),
            np.concatenate([g20_hist, g20_list]),
            np.concatenate([a20_hist, a20_list]))


def _cumulative_a2020(geom, c, maxmask1, gic_mask, A, S0, exp_is_hist):
    """Seamless hist+exp cumulative A2020, offset to zero at the reference.

    A2020 measures the sea-level change between two consecutive states, so a
    time series of it has to be accumulated.  Starting the accumulation at the
    first historical timestep and subtracting the value at the reference year
    makes the projection continue the historical curve without a step.
    """
    lh = geom.lithk if exp_is_hist else geom.lithk_hist
    th = geom.topg if exp_is_hist else geom.topg_hist
    n_lh = geom.nt if exp_is_hist else geom.n_hist

    H_prev = lh[0, :, :] * maxmask1 * gic_mask
    B_prev = th[0, :, :]
    acc = 0.0
    hist_cumul = [0.0]
    for n_h in range(1, n_lh):
        H_h = lh[n_h, :, :] * maxmask1 * gic_mask
        B_h = th[n_h, :, :]
        acc += slc_A2020.get_slc_A2020(H_prev, H_h, B_prev, B_h, S0, S0, A, c)
        hist_cumul.append(acc)
        H_prev = H_h.copy()
        B_prev = B_h.copy()
    offset = hist_cumul[geom.ref_idx]

    if exp_is_hist:
        return [], [v - offset for v in hist_cumul]

    # H_prev/B_prev are at hist[-1]; carry straight on into the projection.
    raw_exp = []
    for n in range(geom.nt):
        H = geom.lithk[n, :, :] * maxmask1 * gic_mask
        B = geom.topg[n, :, :]
        acc += slc_A2020.get_slc_A2020(H_prev, H, B_prev, B, S0, S0, A, c)
        raw_exp.append(acc)
        H_prev = H.copy()
        B_prev = B.copy()
    if geom.ref_idx_exp is not None:
        offset = raw_exp[geom.ref_idx_exp]

    a20_list = [v - offset for v in raw_exp]
    a20_hist = ([v - offset for v in hist_cumul[geom.hist_start:]]
                if geom.hist_n_out > 0 else [])
    return a20_hist, a20_list


def compute_st_series(geom, c, region_mask, af2, maxmask1, area_m2):
    """The four ST scalars for one mask, as ``{name: array}``."""
    A = region_mask * af2 * area_m2

    values = {name: [] for name in ST_SCALAR_NAMES}

    def accumulate(lithk, topg, sftgrf, sftflf, indices):
        for n in indices:
            H = lithk[n, :, :] * maxmask1
            B = topg[n, :, :]
            hf = np.maximum(-B, 0) * c.RHOSW / c.RHOI
            values['lim'].append(np.sum(H * A) * c.RHOI)
            values['limnsw'].append(
                np.sum(np.maximum(H - hf, 0) * A) * c.RHOI)
            values['iareagr'].append(np.sum(sftgrf[n, :, :] * A))
            values['iareafl'].append(np.sum(sftflf[n, :, :] * A))

    if geom.hist_n_out > 0:
        accumulate(geom.lithk_hist, geom.topg_hist, geom.sftgrf_hist,
                   geom.sftflf_hist, range(geom.hist_start, geom.n_hist))
    accumulate(geom.lithk, geom.topg, geom.sftgrf, geom.sftflf,
               range(geom.nt))

    return {name: np.asarray(vals) for name, vals in values.items()}


# --------------------------------------------------------------------------
# Output


def _slc_meta(settings, regionName, gic_suffix):
    """Metadata columns for an SLC CSV row."""
    return {
        'ice_source': settings.region,
        # The GIC variants differ only here, so the suffix has to be part of
        # the row: without it two rows from the same run are indistinguishable
        # once they are concatenated into a community-wide table.
        'region': f'{regionName}{gic_suffix}',
        'group': settings.group,
        'model': settings.model,
        'model_variant': settings.modelid,
        'scenario': settings.exp,
        'GCM': settings.esm,
        'forcingid': settings.forcingid,
        'configid': settings.configid,
    }


def write_slc_outputs(settings, geom, regionName_raw, regionName, gic_suffix,
                      file_stem, series, time_axis, write_nc, write_csv):
    """Write the NetCDF and CSV forms of one mask's three SLC series."""
    for (varname, long_name), values in zip(SLC_SPECS, series):
        stem = make_out_stem(varname, gic_suffix, regionName_raw, regionName,
                             file_stem, settings.flg_bm)
        if write_nc:
            write_scalar_nc(os.path.join(settings.ncpath, f'{stem}.nc'),
                            varname, values, time_axis, long_name, 'm')
        if write_csv:
            write_slc_csv(os.path.join(settings.csvpath, f'{stem}.csv'),
                          _slc_meta(settings, regionName, gic_suffix),
                          geom.nominal_yrs, values)


# --------------------------------------------------------------------------
# The run


def run(settings):
    """Process one experiment.  Returns the number of scalars skipped."""
    res = detect_resolution(settings)
    print(f'Auto-detected resolution: {res} km')
    area_m2 = (float(res) * 1000.0) ** 2

    regions, af2, maxmask1, iaf2GIC = load_masks(settings, res)
    c = load_constants(settings)
    geom = load_geometry(settings)
    exp_is_hist = settings.exp == settings.hist

    if settings.verbose:
        print('lithk:', geom.lithk.shape, 'topg:', geom.topg.shape)
        print('lithk_ref:', geom.lithk_ref.shape,
              'topg_ref:', geom.topg_ref.shape)
        print('densities:', c.RHOI, c.RHOSW, c.RHOFW)

    year_start = geom.nominal_yrs[0]
    year_end = geom.nominal_yrs[-1]
    file_stem = make_file_stem(
        settings.region, settings.group, settings.model, settings.modelid,
        settings.esm, settings.forcingid, settings.exp, settings.configid,
        year_start, year_end)
    time_axis = TimeAxis(geom.time_out, geom.time_units, geom.time_long_name,
                         geom.time_calendar)

    # ---- SLC, once with GIC masking and once without ----
    warned_csv_years = False
    for gic_mask, gic_suffix in [(iaf2GIC, '-gic'),
                                 (np.ones_like(iaf2GIC), '')]:
        is_gic = gic_suffix == '-gic'
        write_nc = FLG_SLC_GIC_NC if is_gic else FLG_SLC_NC
        write_csv = FLG_SLC_GIC_CSV if is_gic else FLG_SLC_CSV
        if write_csv and not warned_csv_years:
            warn_years_out_of_range(geom.nominal_yrs)
            warned_csv_years = True

        for regionName_raw, region_mask in regions.items():
            regionName = region_display_name(regionName_raw, settings.region)
            print(f'{regionName}{gic_suffix}')
            series = compute_slc_series(geom, c, region_mask, af2, maxmask1,
                                        gic_mask, area_m2, exp_is_hist)
            if settings.verbose:
                for (varname, _), values in zip(SLC_SPECS, series):
                    print(f'  {varname}: {values}')
            write_slc_outputs(settings, geom, regionName_raw, regionName,
                              gic_suffix, file_stem, series, time_axis,
                              write_nc, write_csv)

    # ---- ST scalars, no GIC masking ----
    if geom.st_ok:
        for regionName_raw, region_mask in regions.items():
            regionName = region_display_name(regionName_raw, settings.region)
            values = compute_st_series(geom, c, region_mask, af2, maxmask1,
                                       area_m2)
            for varname in ST_SCALAR_NAMES:
                standard_name, units, long_name = variable_metadata(varname)
                stem = make_out_stem(varname, '', regionName_raw, regionName,
                                     file_stem, settings.flg_bm)
                if FLG_ST_NC:
                    write_scalar_nc(
                        os.path.join(settings.ncpath, f'{stem}.nc'), varname,
                        values[varname], time_axis, long_name, units,
                        standard_name=standard_name)

    # ---- FL scalars, no GIC masking ----
    skipped_scalars = run_fl_scalars(settings, geom, regions, af2, area_m2,
                                     exp_is_hist)

    if skipped_scalars:
        print('\nSkipped scalars (input files not found):')
        for name in skipped_scalars:
            print(f'  {name}')
    return len(skipped_scalars)


def run_fl_scalars(settings, geom, regions, af2, area_m2, exp_is_hist):
    """Integrate and write every FL scalar whose input file is present.

    FL variables have their own time axis -- timestamps at Jul 1 of year N,
    with bounds -- and their own file length, so they cannot ride on the ST
    axis.  Returns the names of the variables that were skipped.
    """
    skipped = []
    weight_base = af2 * area_m2

    for tendvarname, input_var in FL_SCALAR_SPECS:
        standard_name, units, long_name = variable_metadata(tendvarname)
        fl_exp_file = find_model_file(
            settings.exppath, input_var, settings.region, settings.group,
            settings.model, settings.modelid, settings.esm,
            settings.forcingid, settings.exp, settings.configid,
            required=False)
        if fl_exp_file is None:
            skipped.append(tendvarname)
            continue

        with nc.Dataset(fl_exp_file, 'r') as ds:
            fl_exp = np.ma.filled(ds.variables[input_var][:, :, :], 0.0)
            tv = ds.variables['time']
            fl_time_exp = tv[:]
            fl_time_units = tv.units
            fl_time_calendar = tv.calendar
            fl_time_long_name = tv.long_name

        fl_hist, fl_time_hist = None, None
        if geom.hist_n_out > 0 and not exp_is_hist:
            fl_hist_file = find_model_file(
                settings.histpath, input_var, settings.region, settings.group,
                settings.model, settings.modelid, settings.esm,
                settings.forcingid, settings.hist, settings.hist_configid,
                required=False)
            if fl_hist_file is not None:
                # A missing hist FL file is not fatal: the projection period
                # is still written on its own.
                with nc.Dataset(fl_hist_file, 'r') as ds:
                    fl_hist = np.ma.filled(
                        ds.variables[input_var][:, :, :], 0.0)
                    htv = ds.variables['time']
                    fl_time_hist = _hist_times_on_exp_axis(
                        htv[:], htv.units, htv.calendar, fl_time_units,
                        fl_time_calendar)

        n_fl_hist = len(fl_time_hist) if fl_time_hist is not None else 0
        if fl_hist is not None and geom.hist_n_out > 0:
            fl_n_out = (n_fl_hist if settings.histout == -1
                        else min(geom.hist_n_out, n_fl_hist))
            if fl_n_out < geom.hist_n_out and settings.histout != -1:
                print(f'Warning: FL hist file for {tendvarname} has '
                      f'{n_fl_hist} steps; requested {geom.hist_n_out} via '
                      f'--histout -- using {fl_n_out}')
            fl_hist_start = n_fl_hist - fl_n_out
            fl_time_out = np.concatenate(
                [fl_time_hist[fl_hist_start:], fl_time_exp])
        else:
            fl_hist_start = n_fl_hist
            fl_time_out = np.asarray(fl_time_exp)

        # FL timestamps sit at Jul 1 of year N, so the nominal year is the
        # timestamp year -- no offset, unlike ST.
        fl_dates = nc.num2date(fl_time_out, fl_time_units,
                               calendar=fl_time_calendar)
        fl_file_stem = make_file_stem(
            settings.region, settings.group, settings.model, settings.modelid,
            settings.esm, settings.forcingid, settings.exp, settings.configid,
            fl_dates[0].year, fl_dates[-1].year)
        fl_time_axis = TimeAxis(fl_time_out, fl_time_units, fl_time_long_name,
                                fl_time_calendar)

        for regionName_raw, region_mask in regions.items():
            regionName = region_display_name(regionName_raw, settings.region)
            W = region_mask * weight_base  # (ny, nx)
            exp_integral = np.einsum('nyx,yx->n', fl_exp, W)
            if fl_hist is not None and geom.hist_n_out > 0:
                hist_integral = np.einsum('nyx,yx->n',
                                          fl_hist[fl_hist_start:], W)
                fl_integral = np.concatenate([hist_integral, exp_integral])
            else:
                fl_integral = exp_integral

            stem = make_out_stem(tendvarname, '', regionName_raw, regionName,
                                 fl_file_stem, settings.flg_bm)
            if FLG_FL_NC:
                write_scalar_nc(os.path.join(settings.ncpath, f'{stem}.nc'),
                                tendvarname, fl_integral, fl_time_axis,
                                long_name, units,
                                standard_name=standard_name)

    return skipped


def main(argv=None):
    """``ismip7-scalars`` entry point.

    Returns 0 on success and 2 when a required input was missing, so that a
    batch driver can tell a skipped unit from a crash.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.no_mm and not args.basins:
        parser.error('--no-mm skips the only output --basins was not asked '
                     'for; use it together with --basins')
    settings = settings_from_args(args)
    try:
        run(settings)
    except MissingInput as exc:
        print(f'SKIP: {settings.unit_label} -- {exc}')
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
