"""Tests for the data request lookup and where the data files come from.

The point of these is the split: what the ISMIP7 project defines is read from
``isschecker``, and what this package decides for itself stays here.  A test
that only checked the values would pass just as happily against a local copy,
which is the arrangement this replaced.
"""

from __future__ import annotations

import csv

import pytest

from ismip7_scalars import paths, variables
from ismip7_scalars.scalars import FL_SCALAR_SPECS, ST_SCALAR_NAMES


class TestWhereTheDataComesFrom:
    def test_data_request_is_read_from_isschecker(self):
        """Not from a copy in this package -- a copy is a thing that drifts."""
        assert 'isschecker' in paths.variable_request_path().parts

    def test_core_table_is_this_package_s_own(self):
        """Which historical run a projection pairs with is the driver's call,
        not part of the ISMIP7 data request."""
        assert 'ismip7_scalars' in paths.core_experiments_path().parts

    def test_both_files_exist_where_they_are_expected(self):
        assert paths.variable_request_path().is_file()
        assert paths.core_experiments_path().is_file()

    def test_a_missing_data_package_says_what_to_install(self):
        paths._materialise.cache_clear()
        try:
            with pytest.raises(paths.MissingDataError, match='isschecker'):
                paths._materialise('isschecker_that_is_not_installed')
        finally:
            paths._materialise.cache_clear()


class TestVariableMetadata:
    @pytest.mark.parametrize('name', ST_SCALAR_NAMES)
    def test_every_state_scalar_is_in_the_data_request(self, name):
        standard_name, units, long_name = variables.variable_metadata(name)
        assert standard_name and units and long_name

    @pytest.mark.parametrize('name,_input',
                             FL_SCALAR_SPECS)
    def test_every_flux_scalar_is_in_the_data_request(self, name, _input):
        _standard_name, units, long_name = variables.variable_metadata(name)
        assert units and long_name

    @pytest.mark.parametrize('_name,input_var', FL_SCALAR_SPECS)
    def test_every_flux_input_is_in_the_data_request(self, _name, input_var):
        """The gridded variable each flux scalar integrates is requested too;
        if one is renamed upstream, this package stops finding its files."""
        _standard_name, units, _long_name = variables.variable_metadata(
            input_var)
        assert units

    def test_known_values(self):
        assert variables.variable_metadata('lim') == (
            'land_ice_mass', 'kg', 'Total ice mass')

    def test_blank_standard_name_becomes_none(self):
        """Two flux scalars have no CF standard name yet.  The attribute is
        then not written at all, which is what the checker expects."""
        standard_name, units, long_name = variables.variable_metadata(
            'tendligroundf')
        assert standard_name is None
        assert units == 'kg s-1'
        assert long_name

    def test_unknown_variable_raises(self):
        with pytest.raises(variables.DataRequestError, match='not in the'):
            variables.variable_metadata('notavariable')

    def test_a_renamed_column_fails_loudly(self, tmp_path, monkeypatch):
        """Silently writing empty attributes into every output file would be
        far worse than refusing to run."""
        bad = tmp_path / 'request.csv'
        with open(bad, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Variable Name', 'units'])
            writer.writerow(['lim', 'kg'])
        monkeypatch.setattr(variables, 'variable_request_path',
                            lambda: bad)
        variables.variable_request.cache_clear()
        variables._by_name.cache_clear()
        variables.variable_metadata.cache_clear()
        try:
            with pytest.raises(variables.DataRequestError,
                               match='standard_name'):
                variables.variable_request()
        finally:
            variables.variable_request.cache_clear()
            variables._by_name.cache_clear()
            variables.variable_metadata.cache_clear()
