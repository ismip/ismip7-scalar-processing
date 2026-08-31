"""Tests for the ISMIP7 naming conventions."""

from __future__ import annotations

import pytest

from ismip7_scalars.naming import (
    MissingInput,
    configid_to_exp_group,
    find_model_file,
    make_file_stem,
    make_out_stem,
    parse_ismip7_name,
    region_display_name,
    resolution_string,
)

FIELDS = dict(region='GrIS', group='NORCE', model='CISM16x-MAR312-p50',
              modelid='m001', esm='CESM2-WACCM', forcingid='f001',
              experiment='ssp585', configid='E001')


class TestConfigidToExpGroup:
    @pytest.mark.parametrize('configid,expected', [
        ('C001', 'CORE'), ('E001', 'ESM'), ('P042', 'PPE'),
        ('c001', 'CORE'), ('e999', 'ESM'),
    ])
    def test_prefix(self, configid, expected):
        assert configid_to_exp_group(configid) == expected

    def test_unknown_prefix_falls_back_to_core(self):
        assert configid_to_exp_group('X001') == 'CORE'

    def test_empty_does_not_raise(self):
        """An empty configid used to raise IndexError on ``cid[0]``."""
        assert configid_to_exp_group('') == 'CORE'


class TestResolutionString:
    @pytest.mark.parametrize('dx_m,expected', [
        (16000.0, '16'), (8000.0, '08'), (2000.0, '02'), (1000.0, '01'),
        (32000.0, '32'), (4000.0, '04'),
    ])
    def test_known_grids(self, dx_m, expected):
        assert resolution_string(dx_m) == expected

    def test_rounds_to_nearest_km(self):
        assert resolution_string(15999.5) == '16'


class TestParseIsmip7Name:
    def test_full_name(self):
        meta = parse_ismip7_name(
            'lithk_GrIS_NORCE_CISM16x-MAR312-p50_m001_CESM2-WACCM_f001'
            '_ssp585_E001_2015-2300.nc')
        assert meta['var'] == 'lithk'
        for key, value in FIELDS.items():
            assert meta[key] == value

    def test_trailing_fields_ignored(self):
        """Anything after the configid is not part of a run's identity."""
        meta = parse_ismip7_name(
            'lithk_GrIS_NORCE_CISM16x-MAR312-p50_m001_CESM2-WACCM_f001'
            '_ssp585_E001_2015-2300_c.nc')
        assert meta['configid'] == 'E001'

    def test_without_extension(self):
        meta = parse_ismip7_name(
            'lithk_GrIS_NORCE_M_m001_CESM2-WACCM_f001_ssp585_E001_2015-2300')
        assert meta['experiment'] == 'ssp585'

    @pytest.mark.parametrize('fname', [
        'lithk_GrIS_NORCE_M_m001_CESM2-WACCM_f001_ssp585_E001.nc',  # 9 fields
        'lithk.nc',
        'compliance_checker_log.txt',
    ])
    def test_non_strict_names_rejected(self, fname):
        assert parse_ismip7_name(fname) is None

    def test_underscore_in_model_name_shifts_fields(self):
        """A model name with an underscore breaks positional parsing.

        Pinned because it is the one way a *plausible* name is silently
        misread rather than rejected: the extra field pushes the configid one
        place along, and ``ensemble`` then rejects the unit for a mismatch
        against its directory rather than processing the wrong thing.
        """
        meta = parse_ismip7_name(
            'lithk_GrIS_NORCE_CISM_MAR_m001_CESM2-WACCM_f001_ssp585_E001'
            '_2015-2300.nc')
        assert meta['configid'] != 'E001'


class TestRegionDisplayName:
    def test_mm_becomes_lowercase_region(self):
        assert region_display_name('mm', 'AIS') == 'ais'
        assert region_display_name('mm', 'GrIS') == 'gris'

    def test_basin_names_pass_through(self):
        assert region_display_name('wais', 'AIS') == 'wais'
        assert region_display_name('r01', 'AIS') == 'r01'


class TestMakeOutStem:
    def test_whole_sheet_default_mode_omits_mask(self):
        stem = make_out_stem('slvaf', '', 'mm', 'ais', 'BASE', flg_bm=False)
        assert stem == 'slvaf_BASE'

    def test_whole_sheet_basin_mode_includes_mask(self):
        stem = make_out_stem('slvaf', '', 'mm', 'ais', 'BASE', flg_bm=True)
        assert stem == 'slvaf_ais_BASE'

    def test_basin_always_includes_mask(self):
        stem = make_out_stem('slvaf', '', 'wais', 'wais', 'BASE',
                             flg_bm=True)
        assert stem == 'slvaf_wais_BASE'

    def test_gic_suffix_attaches_to_variable(self):
        """The suffix qualifies the variable, not the mask."""
        stem = make_out_stem('slvaf', '-gic', 'wais', 'wais', 'BASE',
                             flg_bm=True)
        assert stem == 'slvaf-gic_wais_BASE'


class TestMakeFileStem:
    def test_field_order(self):
        stem = make_file_stem('AIS', 'ISMIP7', 'SYNTH1', 'm001', 'CESM2', 'f001',
                              'ssp585', 'C007', 2015, 2300)
        assert stem == 'AIS_ISMIP7_SYNTH1_m001_CESM2_f001_ssp585_C007_2015-2300'

    def test_round_trips_through_parse(self):
        """An output filename is itself a strict ISMIP7 name."""
        stem = make_file_stem('AIS', 'ISMIP7', 'SYNTH1', 'm001', 'CESM2',
                              'f001', 'ssp585', 'C007', 2015, 2300)
        meta = parse_ismip7_name(f'slvaf_{stem}.nc')
        assert meta['configid'] == 'C007'
        assert meta['experiment'] == 'ssp585'


class TestFindModelFile:
    def _touch(self, directory, name):
        path = directory / name
        path.write_bytes(b'')
        return str(path)

    def test_single_match(self, tmp_path):
        expected = self._touch(
            tmp_path,
            'lithk_GrIS_NORCE_CISM16x-MAR312-p50_m001_CESM2-WACCM_f001'
            '_ssp585_E001_2015-2300.nc')
        found = find_model_file(str(tmp_path), 'lithk', **FIELDS)
        assert found == expected

    def test_missing_required_raises(self, tmp_path):
        with pytest.raises(MissingInput):
            find_model_file(str(tmp_path), 'lithk', **FIELDS)

    def test_missing_optional_returns_none(self, tmp_path):
        assert find_model_file(str(tmp_path), 'lithk', required=False,
                               **FIELDS) is None

    def test_ambiguous_raises_even_when_optional(self, tmp_path):
        """Two candidates is a broken directory whether or not var is optional.

        Returning either one would silently process a different run from the
        one the caller asked for.
        """
        base = ('lithk_GrIS_NORCE_CISM16x-MAR312-p50_m001_CESM2-WACCM_f001'
                '_ssp585_E001_')
        self._touch(tmp_path, base + '2015-2100.nc')
        self._touch(tmp_path, base + '2015-2300.nc')
        with pytest.raises(MissingInput, match='multiple'):
            find_model_file(str(tmp_path), 'lithk', required=False, **FIELDS)

    def test_does_not_match_a_different_experiment(self, tmp_path):
        self._touch(
            tmp_path,
            'lithk_GrIS_NORCE_CISM16x-MAR312-p50_m001_CESM2-WACCM_f001'
            '_ssp126_E001_2015-2300.nc')
        assert find_model_file(str(tmp_path), 'lithk', required=False,
                               **FIELDS) is None
