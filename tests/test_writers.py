"""Tests for the output writers."""

from __future__ import annotations

import csv
import os

import netCDF4 as nc
import numpy as np
import pytest

from ismip7_scalars.writers import (
    CSV_META_KEYS,
    CSV_YEAR_FIRST,
    CSV_YEAR_LAST,
    TimeAxis,
    csv_header,
    csv_row,
    warn_years_out_of_range,
    write_scalar_nc,
    write_slc_csv,
)


@pytest.fixture
def time_axis():
    return TimeAxis(np.array([0.0, 365.0, 730.0]), 'days since 1850-01-01',
                    'time', 'noleap')


@pytest.fixture
def meta():
    return {k: k.upper() for k in CSV_META_KEYS}


class TestWriteScalarNc:
    def test_round_trip(self, tmp_path, time_axis):
        path = str(tmp_path / 'sub' / 'slvaf_TEST.nc')
        write_scalar_nc(path, 'slvaf', [1.0, 2.0, 3.0], time_axis,
                        'Sea level contribution', 'm')
        with nc.Dataset(path) as ds:
            assert ds.variables['slvaf'].units == 'm'
            assert ds.variables['slvaf'].long_name == 'Sea level contribution'
            assert ds.variables['time'].calendar == 'noleap'
            assert ds.variables['time'].units == 'days since 1850-01-01'
            np.testing.assert_allclose(ds.variables['slvaf'][:],
                                       [1.0, 2.0, 3.0])
            np.testing.assert_allclose(ds.variables['time'][:],
                                       time_axis.values)

    def test_creates_missing_directories(self, tmp_path, time_axis):
        path = str(tmp_path / 'a' / 'b' / 'c' / 'x.nc')
        write_scalar_nc(path, 'x', [0.0, 0.0, 0.0], time_axis, 'x', 'm')
        assert os.path.exists(path)

    def test_time_dimension_is_unlimited(self, tmp_path, time_axis):
        path = str(tmp_path / 'x.nc')
        write_scalar_nc(path, 'x', [0.0, 0.0, 0.0], time_axis, 'x', 'm')
        with nc.Dataset(path) as ds:
            assert ds.dimensions['time'].isunlimited()


class TestCsvRow:
    def test_header_shape(self):
        header = csv_header()
        assert header[:len(CSV_META_KEYS)] == list(CSV_META_KEYS)
        assert header[len(CSV_META_KEYS)] == f'y{CSV_YEAR_FIRST}'
        assert header[-1] == f'y{CSV_YEAR_LAST}'
        assert len(header) == len(CSV_META_KEYS) + (
            CSV_YEAR_LAST - CSV_YEAR_FIRST + 1)

    def test_row_length_matches_header(self, meta):
        row = csv_row(meta, [2015, 2016], [1.0, 2.0])
        assert len(row) == len(csv_header())

    def test_values_land_in_their_year_columns(self, meta):
        header = csv_header()
        row = csv_row(meta, [2015, 2016], [1.5, 2.5])
        assert row[header.index('y2015')] == 1.5
        assert row[header.index('y2016')] == 2.5

    def test_uncovered_years_are_na(self, meta):
        header = csv_header()
        row = csv_row(meta, [2015], [1.5])
        assert row[header.index('y2014')] == 'NA'
        assert row[header.index('y2300')] == 'NA'

    def test_years_outside_window_are_dropped(self, meta):
        """A value at year 2400 has no column, so it cannot be written."""
        row = csv_row(meta, [2299, 2400], [1.0, 2.0])
        assert 2.0 not in row[len(CSV_META_KEYS):]

    def test_metadata_in_declared_order(self, meta):
        row = csv_row(meta, [], [])
        assert row[:len(CSV_META_KEYS)] == [k.upper() for k in CSV_META_KEYS]


class TestWarnYearsOutOfRange:
    def test_reports_years_beyond_the_window(self):
        assert warn_years_out_of_range([2299, 2300, 2301]) == [2301]

    def test_silent_when_all_years_fit(self, capsys):
        assert warn_years_out_of_range([1850, 2300]) == []
        assert capsys.readouterr().out == ''

    def test_message_names_the_real_last_year(self, capsys):
        """The window ends at 2300; the message used to claim 2301."""
        warn_years_out_of_range([2400])
        out = capsys.readouterr().out
        assert f'{CSV_YEAR_FIRST}-{CSV_YEAR_LAST}' in out
        assert '2301' not in out


class TestWriteSlcCsv:
    def test_two_rows_header_then_data(self, tmp_path, meta):
        path = str(tmp_path / 'out' / 'slvaf_TEST.csv')
        write_slc_csv(path, meta, [2015, 2016], [1.0, 2.0])
        with open(path, newline='') as f:
            rows = list(csv.reader(f))
        assert len(rows) == 2
        assert rows[0] == csv_header()
        assert rows[1][rows[0].index('y2015')] == '1.0'
