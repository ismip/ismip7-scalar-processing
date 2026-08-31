"""Build a miniature but strictly ISMIP7-shaped submission on disk.

The integration tests need a model tree the processing will accept: filenames
with all ten fields, a grid it can detect a resolution from, ST timestamps at
Jan 1 of year N+1 and FL timestamps at Jul 1 of year N.  Writing that here,
rather than committing a fixture tree, keeps the geometry under the tests'
control -- a test that wants ice loss can ask for it -- and keeps the repository
free of binary files that no one can review.

The geometry is deliberately crude: a rectangular ice sheet on a sloping bed,
thinning linearly in time, with a floating margin.  It is not meant to look
like an ice sheet, only to exercise every branch of the integration.
"""

from __future__ import annotations

import os

import netCDF4 as nc
import numpy as np

#: Grid spacing of the synthetic grid, in metres.  16 km, so the generic data
#: files are named ``*_16000m_*`` and the processing reports ``16 km``.
DX = 16000.0

#: Grid shape, as ``(ny, nx)``.  Small enough that a whole test suite of runs
#: costs less than a second, large enough to hold distinguishable basins.
NY, NX = 8, 10

#: Time unit every synthetic file uses.
TIME_UNITS = 'days since 1850-01-01'
CALENDAR = 'noleap'

#: The flux variables the processing looks for, and a per-cell magnitude for
#: each, in kg m-2 s-1.  Sign follows the ISMIP7 convention, where a positive
#: surface mass balance adds mass.
FLUX_VARS = {
    'acabf': 1.0e-5,
    'libmassbfgr': -2.0e-6,
    'libmassbffl': -5.0e-6,
    'licalvf': -3.0e-6,
    'lifmassbf': -1.0e-6,
    'ligroundf': -4.0e-7,
}

DAYS_PER_YEAR = 365  # noleap


def _year_start_days(year):
    """Days from 1850-01-01 to Jan 1 of ``year`` in the noleap calendar."""
    return (year - 1850) * DAYS_PER_YEAR


def st_time(nominal_years):
    """ST timestamps: Jan 1 of year N+1 for each nominal year N."""
    return np.array([_year_start_days(y + 1) for y in nominal_years],
                    dtype=float)


def fl_time(nominal_years):
    """FL timestamps: Jul 1 of year N for each nominal year N."""
    return np.array([_year_start_days(y) + 181 for y in nominal_years],
                    dtype=float)


def _add_grid(ds):
    """Give a dataset the x/y axes the resolution detection reads."""
    ds.createDimension('x', NX)
    ds.createDimension('y', NY)
    x = ds.createVariable('x', 'f8', ('x',))
    y = ds.createVariable('y', 'f8', ('y',))
    x.units = 'm'
    y.units = 'm'
    x[:] = np.arange(NX) * DX
    y[:] = np.arange(NY) * DX


def _write_field(path, varname, data, time_values, units, long_name):
    """Write one ``(time, y, x)`` variable to an ISMIP7-shaped file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with nc.Dataset(path, 'w', format='NETCDF4') as ds:
        ds.createDimension('time', None)
        _add_grid(ds)
        tv = ds.createVariable('time', 'f8', ('time',))
        tv.units = TIME_UNITS
        tv.calendar = CALENDAR
        tv.long_name = 'time'
        tv[:] = time_values
        var = ds.createVariable(varname, 'f8', ('time', 'y', 'x'))
        var.units = units
        var.long_name = long_name
        var[:] = data
    return path


def bed():
    """A bed sloping from above sea level in the east to deep water in the west.

    The transect gives the run grounded ice, floating ice and open ocean at
    once, so the grounding-line terms of every method are exercised.
    """
    profile = np.linspace(-900.0, 300.0, NX)
    return np.tile(profile, (NY, 1))


def thickness(nt, thinning_per_step=20.0, initial=1200.0):
    """Ice thinning uniformly in time over the eastern two thirds of the grid.

    The westernmost columns are left ice-free so that the ``mm`` integral is
    not simply the whole grid.
    """
    field = np.zeros((nt, NY, NX))
    for n in range(nt):
        column = np.full(NX, initial - n * thinning_per_step)
        column[:2] = 0.0  # open ocean in the west
        field[n] = np.tile(column, (NY, 1))
    return np.maximum(field, 0.0)


def masks_from_geometry(lithk, topg, rhoi=917.0, rhosw=1027.0):
    """Grounded and floating area fractions consistent with the geometry."""
    hf = np.maximum(-topg, 0.0) * rhosw / rhoi
    has_ice = lithk > 0.0
    grounded = has_ice & (lithk > hf)
    floating = has_ice & ~grounded
    return grounded.astype(float), floating.astype(float)


def write_data_files(datapath, region='AIS', with_basins=True):
    """Write the generic data files -- area factors, ice sheet and GIC masks.

    ``af2`` is 1 everywhere so that the area weight of a cell is exactly
    ``DX**2``, which makes the expected integrals of the tests plain
    arithmetic.
    """
    os.makedirs(datapath, exist_ok=True)
    res = f'{round(DX / 1000):02d}'
    ones = np.ones((NY, NX))

    def write(name, varname, data):
        with nc.Dataset(os.path.join(datapath, name), 'w',
                        format='NETCDF4') as ds:
            _add_grid(ds)
            var = ds.createVariable(varname, 'f8', ('y', 'x'))
            var[:] = data

    if region == 'AIS':
        write(f'af2_AIS_{res}000m_v1.nc', 'af2', ones)
        write(f'maxmask1_AIS_{res}000m_v0.nc', 'maxmask1', ones)
        # No glaciers and ice caps to exclude: the -gic and plain variants
        # then agree, which is itself worth asserting.
        write(f'iaf2_GIC_AIS_{res}000m_v0.nc', 'iaf2', ones)
        if with_basins:
            # Three IMBIE3 regions and 18 basins, both partitioning the grid
            # exactly, so the sum over basins must equal the whole sheet.
            regions = np.zeros((NY, NX), dtype=int)
            regions[:, :NX // 3] = 1
            regions[:, NX // 3:2 * NX // 3] = 2
            regions[:, 2 * NX // 3:] = 3
            basins = np.zeros((NY, NX), dtype=int)
            flat = basins.reshape(-1)
            flat[:] = (np.arange(NY * NX) % 18) + 1
            path = os.path.join(
                datapath,
                f'basins_regions_AIS_Rignot_extended_{res}000m_v1.nc')
            with nc.Dataset(path, 'w', format='NETCDF4') as ds:
                _add_grid(ds)
                ds.createVariable('regions', 'i4', ('y', 'x'))[:] = regions
                ds.createVariable('basins', 'i4', ('y', 'x'))[:] = basins
    else:
        write(f'af2_GrIS_{res}000m_v1.nc', 'af2', ones)
        write(f'maxmask1_GrIS_{res}000m_v1.nc', 'maxmask1', ones)
        write(f'iaf2_GIC_GrIS_{res}000m_v0.nc', 'iaf2', ones)
        if with_basins:
            basins = np.zeros((NY, NX), dtype=int)
            basins.reshape(-1)[:] = (np.arange(NY * NX) % 7) + 1
            path = os.path.join(
                datapath,
                f'basins_GrIS_Mouginot_extended_{res}000m_v1.nc')
            with nc.Dataset(path, 'w', format='NETCDF4') as ds:
                _add_grid(ds)
                ds.createVariable('basins', 'i4', ('y', 'x'))[:] = basins
    return datapath


def write_params(modelpath, group='ISMIP7', model='SYNTH1', rhoi=917.0,
                 rhow=1027.0, rhof=1000.0):
    """Write the model's ``params.nc``."""
    from ismip7_scalars.params import write_params as _write
    return _write(os.path.join(modelpath, group, model, 'params.nc'),
                  rhoi=rhoi, rhow=rhow, rhof=rhof)


def write_experiment(modelpath, region='AIS', group='ISMIP7', model='SYNTH1',
                     modelid='m001', esm='CESM2-WACCM', forcingid='f001',
                     experiment='historical', configid='C001',
                     exp_group='CORE', start_year=1990, nyears=5,
                     initial=1200.0, thinning_per_step=20.0,
                     variables=('lithk', 'topg', 'sftgrf', 'sftflf'),
                     fluxes=('acabf',)):
    """Write one experiment's model output.  Returns its directory.

    ``variables`` and ``fluxes`` name what to write, so a test can leave out
    ``sftgrf`` and check that only the ST scalars are skipped.
    """
    nominal_years = list(range(start_year, start_year + nyears))
    exppath = os.path.join(modelpath, group, model, exp_group, configid)
    os.makedirs(exppath, exist_ok=True)

    lithk = thickness(nyears, thinning_per_step=thinning_per_step,
                      initial=initial)
    topg = np.tile(bed(), (nyears, 1, 1))
    grounded, floating = masks_from_geometry(lithk, topg)
    fields = {
        'lithk': (lithk, 'm', 'land_ice_thickness'),
        'topg': (topg, 'm', 'bedrock_altitude'),
        'sftgrf': (grounded, '1', 'grounded_ice_sheet_area_fraction'),
        'sftflf': (floating, '1', 'floating_ice_shelf_area_fraction'),
        'sftgif': ((lithk > 0).astype(float), '1', 'land_ice_area_fraction'),
    }

    stem = (f'{region}_{group}_{model}_{modelid}_{esm}_{forcingid}'
            f'_{experiment}_{configid}_'
            f'{nominal_years[0]}-{nominal_years[-1]}.nc')

    for var in variables:
        data, units, long_name = fields[var]
        _write_field(os.path.join(exppath, f'{var}_{stem}'), var, data,
                     st_time(nominal_years), units, long_name)

    for var in fluxes:
        magnitude = FLUX_VARS[var]
        data = np.full((nyears, NY, NX), magnitude)
        data[lithk <= 0.0] = 0.0
        _write_field(os.path.join(exppath, f'{var}_{stem}'), var, data,
                     fl_time(nominal_years), 'kg m-2 s-1', var)

    return exppath


def write_submission(root, region='AIS', hist_years=5, exp_years=6,
                     hist_configid='C001', exp_configid='C007',
                     experiment='ssp585', hist_start=2010, exp_start=2015,
                     **kwargs):
    """Write a historical run and a projection that continues from it.

    Returns ``(datapath, modelpath)``, ready to hand to ``--datapath`` and
    ``--modelpath``.
    """
    datapath = write_data_files(os.path.join(root, 'Data', region),
                                region=region)
    modelpath = os.path.join(root, 'Models', region)
    write_params(modelpath, group=kwargs.get('group', 'ISMIP7'),
                 model=kwargs.get('model', 'SYNTH1'))
    write_experiment(modelpath, region=region, experiment='historical',
                     configid=hist_configid, start_year=hist_start,
                     nyears=hist_years, initial=1200.0, **kwargs)
    # The projection picks up where the historical run left off, so the two
    # concatenate into one continuous thinning curve.
    write_experiment(modelpath, region=region, experiment=experiment,
                     configid=exp_configid, start_year=exp_start,
                     nyears=exp_years,
                     initial=1200.0 - hist_years * 20.0, **kwargs)
    return datapath, modelpath
