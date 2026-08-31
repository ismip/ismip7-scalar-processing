"""The ISMIP7 file and directory naming conventions.

Everything in this module is a pure function of strings and paths, with the one
exception of :func:`find_model_file`, which globs a directory.  The
conventions themselves are described in :doc:`../user/file-conventions`.
"""

from __future__ import annotations

import glob
import os

#: Data files each region needs, by role.  ``{res}`` is the two-digit
#: resolution in kilometres, as returned by :func:`resolution_string`.
FILE_CONFIG = {
    'AIS': {
        'af2': 'af2_AIS_{res}000m_v1.nc',
        'maxmask': 'maxmask1_AIS_{res}000m_v0.nc',
        'gic': 'iaf2_GIC_AIS_{res}000m_v0.nc',
        'basins': 'basins_regions_AIS_Rignot_extended_{res}000m_v1.nc',
    },
    'GrIS': {
        'af2': 'af2_GrIS_{res}000m_v1.nc',
        'maxmask': 'maxmask1_GrIS_{res}000m_v1.nc',
        'gic': 'iaf2_GIC_GrIS_{res}000m_v0.nc',
        'basins': 'basins_GrIS_Mouginot_extended_{res}000m_v1.nc',
    },
}

#: Region-specific defaults for the identifying fields of a run.  They match
#: the ISMIP7/SYNTH1 synthetic test case produced by the ISM_SimulationChecker.
DEFAULTS = {
    'AIS': {
        'group': 'ISMIP7', 'model': 'SYNTH1', 'experiment': 'ssp585',
        'hist': 'historical', 'modelid': 'm001', 'esm': 'CESM2-WACCM',
        'forcingid': 'f001', 'configid': 'C001', 'exp_group': 'CORE',
    },
    'GrIS': {
        'group': 'ISMIP7', 'model': 'SYNTH1', 'experiment': 'ctrl',
        'hist': 'historical', 'modelid': 'm001', 'esm': 'CESM2-WACCM',
        'forcingid': 'f001', 'configid': 'C001', 'exp_group': 'CORE',
    },
}

#: The fields of an ISMIP7 filename, in order, up to and including the
#: configid.  Anything after it (the year range, an optional ``_c``) is not
#: part of the identity of a run.
FILENAME_FIELDS = ('var', 'region', 'group', 'model', 'modelid', 'esm',
                   'forcingid', 'experiment', 'configid')

#: Directory level a configid belongs under, from its prefix letter.
EXP_GROUP_FROM_PREFIX = {'C': 'CORE', 'E': 'ESM', 'P': 'PPE'}


class MissingInput(Exception):
    """A required input file or directory is not there.

    The command-line tools turn this into a single ``SKIP:`` line and exit 2,
    so that a batch run can log the unit and move on rather than stopping.
    """


def configid_to_exp_group(configid):
    """Default ``exp_group`` directory for a configid (C→CORE, E→ESM, P→PPE).

    Anything else falls back to ``CORE``.
    """
    if not configid:
        return 'CORE'
    return EXP_GROUP_FROM_PREFIX.get(configid[0].upper(), 'CORE')


def resolution_string(dx_m):
    """Two-digit resolution string in km from a grid spacing in metres.

    ``16000.0`` becomes ``'16'``, which the templates in :data:`FILE_CONFIG`
    expand to ``16000m``.
    """
    return f'{round(dx_m / 1000):02d}'


def model_file_pattern(dirpath, var, region, group, model, modelid, esm,
                       forcingid, experiment, configid):
    """The glob an ISMIP7 model output file for one variable must match."""
    return os.path.join(
        dirpath,
        f'{var}_{region}_{group}_{model}_{modelid}_{esm}_{forcingid}'
        f'_{experiment}_{configid}_*.nc')


def find_model_file(dirpath, var, region, group, model, modelid, esm,
                    forcingid, experiment, configid, required=True):
    """Locate the one model output file for ``var``, or ``None``.

    Raises :class:`MissingInput` when ``required`` and nothing matches, and
    always raises it when more than one file matches -- an ambiguous directory
    is a problem whether or not the variable was optional, and picking one
    arbitrarily would silently process the wrong run.
    """
    pattern = model_file_pattern(dirpath, var, region, group, model, modelid,
                                 esm, forcingid, experiment, configid)
    files = sorted(glob.glob(pattern))
    if len(files) == 0:
        if not required:
            print(f'WARNING: no file for {var}\n  {pattern}')
            return None
        raise MissingInput(f'no file matching\n  {pattern}')
    if len(files) > 1:
        raise MissingInput(
            f'multiple files match for {var} -- cannot disambiguate:\n  '
            + '\n  '.join(files))
    return files[0]


def parse_ismip7_name(fname):
    """Parse a strict ISMIP7 filename into its fields, or return ``None``.

    ``{var}_{region}_{group}_{model}_{modelid}_{esm}_{forcingid}``
    ``_{experiment}_{configid}_{years}[...]``

    Everything after the configid is ignored.  A name with fewer than ten
    underscore-separated fields is not a strict ISMIP7 name, and no group or
    model name may itself contain an underscore -- that is what makes the
    fields addressable by position.
    """
    stem = fname[:-3] if fname.endswith('.nc') else fname
    parts = stem.split('_')
    if len(parts) < 10:
        return None
    return dict(zip(FILENAME_FIELDS, parts))


def region_display_name(regionName_raw, region):
    """Output name for a mask: ``mm`` becomes ``ais``/``gris``, others stand."""
    return region.lower() if regionName_raw == 'mm' else regionName_raw


def make_out_stem(varname, suffix, regionName_raw, regionName, base_stem,
                  flg_bm):
    """Build an output filename stem, without the extension.

    The whole-sheet (``mm``) integral in default mode carries no mask name, so
    that the output filename matches the structure of the model files it came
    from.  In basin mode, and for every basin mask, the mask name is the second
    field.
    """
    if regionName_raw == 'mm' and not flg_bm:
        return f'{varname}{suffix}_{base_stem}'
    return f'{varname}{suffix}_{regionName}_{base_stem}'


def make_file_stem(region, group, model, modelid, esm, forcingid, exp,
                   configid, year_start, year_end):
    """The identifying part of an output filename, shared by every variable."""
    return (f'{region}_{group}_{model}_{modelid}_{esm}_{forcingid}'
            f'_{exp}_{configid}_{year_start}-{year_end}')
