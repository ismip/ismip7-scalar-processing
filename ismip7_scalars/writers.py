"""Writing the scalar output: one NetCDF per variable, and the SLC CSV rows."""

from __future__ import annotations

import csv
import os

import netCDF4 as nc
import numpy as np

#: Global attribute written to every output file.
FILE_DESCRIPTION = ('ISMIP7 scalar output. Heiko Goelzer 2026, '
                    'heig@norceresearch.no')

#: Global attributes copied from the input files to the output files: each
#: output inherits them from the model file its scalar is computed from.  The
#: compliance checker requires all of them, and submissions set them on every
#: model file; a missing one is warned about and simply not written.
REQUIRED_GLOBAL_ATTRS = ('group', 'model', 'contact_name', 'contact_email',
                         'crs')

#: The fill value written as ``_FillValue``: the netCDF default for the f4
#: dtype, which is what the compliance checker compares against.
FILL_VALUE_F4 = nc.default_fillvals['f4']

#: First and last nominal year of the fixed CSV column window.  Every SLC CSV
#: has a column for each year in it, whether or not the run covers that year.
CSV_YEAR_FIRST = 1850
CSV_YEAR_LAST = 2300

#: Metadata columns that precede the annual columns of an SLC CSV.
CSV_META_KEYS = ('ice_source', 'region', 'scalar', 'group', 'model',
                 'model_variant', 'scenario', 'GCM', 'forcingid', 'configid')


class TimeAxis:
    """The time coordinate of an output file, and the attributes it carries."""

    def __init__(self, values, units, long_name, calendar, bounds=None):
        self.values = np.asarray(values)
        self.units = units
        self.long_name = long_name
        self.calendar = calendar
        # Cell boundaries as an (n, 2) array, inherited from the input file;
        # written as ``time_bounds`` only when every input had them.
        self.bounds = None if bounds is None else np.asarray(bounds)

    def __len__(self):
        return len(self.values)


def write_scalar_nc(path, varname, values, time_axis, long_name, units,
                    standard_name=None, global_attrs=None):
    """Write one time-series variable to a NetCDF file, creating its directory.

    ``standard_name`` is written only when there is one: the data request
    leaves it blank for a couple of the flux scalars, and the compliance
    checker asks for the attribute only where the request supplies a value.

    ``global_attrs`` is copied onto the file verbatim -- the checker requires
    ``group``, ``model``, ``contact_name``, ``contact_email`` and ``crs``,
    which each output inherits from the model file its scalar is computed
    from (see :data:`REQUIRED_GLOBAL_ATTRS`).

    Variables are stored as single precision with the default f4 fill value
    recorded as ``_FillValue``, as the data request and the checker require.

    Returns the path written, so a caller can log or collect it.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with nc.Dataset(path, 'w', format='NETCDF4') as ds:
        ds.createDimension('time', None)
        for attr, value in (global_attrs or {}).items():
            ds.setncattr(attr, value)
        ds.description = FILE_DESCRIPTION
        var_time = ds.createVariable('time', 'f4', ('time',), zlib=True,
                                     fill_value=FILL_VALUE_F4)
        var_data = ds.createVariable(varname, 'f4', ('time',), zlib=True,
                                     fill_value=FILL_VALUE_F4)
        var_time.units = time_axis.units
        var_time.long_name = time_axis.long_name
        var_time.calendar = time_axis.calendar
        var_data.long_name = long_name
        var_data.units = units
        if standard_name:
            var_data.standard_name = standard_name
        var_time[:] = np.asarray(time_axis.values, dtype='f4')
        var_data[:] = np.asarray(values, dtype='f4')
        if time_axis.bounds is not None:
            ds.createDimension('nv', 2)
            var_tb = ds.createVariable('time_bounds', 'f4',
                                       ('time', 'nv'),
                                       fill_value=FILL_VALUE_F4)
            var_tb.units = time_axis.units
            var_time.bounds = 'time_bounds'
            var_tb[:] = np.asarray(time_axis.bounds, dtype='f4')
    print('Created file ', path)
    return path


def csv_years():
    """The annual columns of an SLC CSV, as a ``range``."""
    return range(CSV_YEAR_FIRST, CSV_YEAR_LAST + 1)


def csv_header():
    """Header row of an SLC CSV: the metadata keys, then one column per year."""
    return list(CSV_META_KEYS) + [f'y{y}' for y in csv_years()]


def csv_row(meta, nominal_yrs, values):
    """One CSV data row: metadata, then one value per year and ``NA`` elsewhere.

    ``nominal_yrs`` and ``values`` line up element by element.  Years outside
    the fixed window are dropped -- :func:`warn_years_out_of_range` reports
    them -- and years the run does not cover are ``NA``.
    """
    year_to_value = dict(zip(nominal_yrs, values))
    return [meta[k] for k in CSV_META_KEYS] + [
        year_to_value[y] if y in year_to_value else 'NA' for y in csv_years()
    ]


def warn_years_out_of_range(nominal_yrs):
    """Print a warning for run years the fixed CSV window cannot hold."""
    window = csv_years()
    out_of_range = [y for y in nominal_yrs if y not in window]
    if out_of_range:
        shown = out_of_range[:5]
        ellipsis = '...' if len(out_of_range) > 5 else ''
        print(f'Warning: {len(out_of_range)} year(s) outside CSV window '
              f'{CSV_YEAR_FIRST}-{CSV_YEAR_LAST} will be dropped: '
              f'{shown}{ellipsis}')
    return out_of_range


def write_slc_csv(path, rows):
    """Write labeled SLC rows to one CSV, creating its directory.

    Each item in ``rows`` is ``(meta, nominal_yrs, values)``.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(csv_header())
        for meta, nominal_yrs, values in rows:
            writer.writerow(csv_row(meta, nominal_yrs, values))
    print('Created file ', path)
    return path
