"""Writing the scalar output: one NetCDF per variable, and the SLC CSV rows."""

from __future__ import annotations

import csv
import os

import netCDF4 as nc
import numpy as np

#: Global attribute written to every output file.
FILE_DESCRIPTION = ('ISMIP7 scalar output. Heiko Goelzer 2026, '
                    'heig@norceresearch.no')

#: First and last nominal year of the fixed CSV column window.  Every SLC CSV
#: has a column for each year in it, whether or not the run covers that year.
CSV_YEAR_FIRST = 1850
CSV_YEAR_LAST = 2300

#: Metadata columns that precede the annual columns of an SLC CSV.
CSV_META_KEYS = ('ice_source', 'region', 'group', 'model', 'model_variant',
                 'scenario', 'GCM', 'forcingid', 'configid')


class TimeAxis:
    """The time coordinate of an output file, and the attributes it carries."""

    def __init__(self, values, units, long_name, calendar):
        self.values = np.asarray(values)
        self.units = units
        self.long_name = long_name
        self.calendar = calendar

    def __len__(self):
        return len(self.values)


def write_scalar_nc(path, varname, values, time_axis, long_name, units,
                    standard_name=None):
    """Write one time-series variable to a NetCDF file, creating its directory.

    ``standard_name`` is written only when there is one: the data request
    leaves it blank for a couple of the flux scalars, and the compliance
    checker asks for the attribute only where the request supplies a value.

    Returns the path written, so a caller can log or collect it.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with nc.Dataset(path, 'w', format='NETCDF4') as ds:
        ds.createDimension('time', None)
        ds.description = FILE_DESCRIPTION
        var_time = ds.createVariable('time', 'f8', ('time',), zlib=True)
        var_data = ds.createVariable(varname, 'f8', ('time',), zlib=True)
        var_time.units = time_axis.units
        var_time.long_name = time_axis.long_name
        var_time.calendar = time_axis.calendar
        var_data.long_name = long_name
        var_data.units = units
        if standard_name:
            var_data.standard_name = standard_name
        var_time[:] = time_axis.values
        var_data[:] = np.asarray(values)
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


def write_slc_csv(path, meta, nominal_yrs, values):
    """Write a one-row SLC CSV, creating its directory."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(csv_header())
        writer.writerow(csv_row(meta, nominal_yrs, values))
    print('Created file ', path)
    return path
