"""Tests for the ensemble driver's planning logic.

The driver's job is to decide, for each directory under a submissions root,
whether it is a processable unit and which historical run it pairs with.  Those
decisions are what these tests pin; actually running the units is covered by
the integration tests.
"""

from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

from ismip7_scalars.ensemble import (
    SELF_PAIRED_SCENARIOS,
    build_command,
    build_parser,
    discover_units,
    format_report,
    hist_configid_for,
    keep_unit,
    load_core_csv,
    unit_status,
)

CORE = {
    'C001': {'scenario': 'historical', 'esm': 'CESM-WACCM'},
    'C002': {'scenario': 'historical', 'esm': 'MRI-ESM2-0'},
    'C003': {'scenario': 'ssp370', 'esm': 'CESM-WACCM'},
    'C004': {'scenario': 'ssp370', 'esm': 'MRI-ESM2-0'},
}


def make_args(modelpath, **overrides):
    args = dict(region='AIS', modelpath=modelpath, datapath=None,
                params_path=None, outpath=None, exp_group=None, groups=None,
                models=None, configids=None, histout=None, basins=False,
                python='python')
    args.update(overrides)
    return SimpleNamespace(**args)


def make_unit(root, group='ISMIP7', model='SYNTH1', exp_group='CORE',
              configid='C003', var='lithk', esm='CESM2-WACCM',
              experiment='ssp370', region='AIS', years='2015-2100',
              fname=None):
    """Create one unit directory holding a single model file."""
    path = os.path.join(root, group, model, exp_group, configid)
    os.makedirs(path, exist_ok=True)
    if fname is None:
        fname = (f'{var}_{region}_{group}_{model}_m001_{esm}_f001'
                 f'_{experiment}_{configid}_{years}.nc')
    open(os.path.join(path, fname), 'wb').close()
    return (group, model, exp_group, configid, path)


class TestLoadCoreCsv:
    def test_bundled_table_is_readable(self):
        """The CORE table ships as package data, not as a repo-relative path."""
        core = load_core_csv()
        assert core['C001']['scenario'] == 'historical'
        assert 'CESM' in core['C001']['esm']

    def test_bundled_table_pairs_every_esm_driven_projection(self):
        core = load_core_csv()
        for cid, row in core.items():
            if row['scenario'] in SELF_PAIRED_SCENARIOS:
                continue
            if row['esm'] in ('', '-'):
                continue  # no forcing ESM, so no historical run to pair with
            hcid = hist_configid_for(cid, core)
            assert hcid is not None, cid
            assert core[hcid]['scenario'] == 'historical'

    def test_experiment_without_a_forcing_esm_is_left_to_a_human(self):
        """``ocx`` (C011) has no ESM column, so no historical run follows from it.

        The old parity rule handed back C011 itself, which made the run its own
        reference: every value would then be measured against the run's last
        timestep rather than a historical state.
        """
        core = load_core_csv()
        assert core['C011']['esm'] == '-'
        assert hist_configid_for('C011', core) is None

    def test_missing_file_returns_empty(self, tmp_path, capsys):
        assert load_core_csv(str(tmp_path / 'nope.csv')) == {}
        assert 'WARNING' in capsys.readouterr().out


class TestHistConfigidFor:
    def test_cesm_projection_pairs_with_c001(self):
        assert hist_configid_for('C003', CORE) == 'C001'

    def test_mri_projection_pairs_with_c002(self):
        assert hist_configid_for('C004', CORE) == 'C002'

    def test_even_configid_outside_the_table_falls_back_to_parity(self):
        assert hist_configid_for('E004', CORE) == 'E003'

    def test_odd_configid_outside_the_table_has_no_pair(self):
        """It must not pair a projection with itself.

        The parity rule used to return the configid unchanged for an odd
        number, which made a projection its own historical reference: every
        SLC series would then be measured against its own last timestep.
        """
        assert hist_configid_for('E003', CORE) is None

    def test_unparseable_configid_has_no_pair(self):
        assert hist_configid_for('Cabc', CORE) is None


class TestDiscoverUnits:
    def test_finds_well_formed_units(self, tmp_path):
        make_unit(str(tmp_path), configid='C001')
        make_unit(str(tmp_path), configid='C003')
        units, skips = discover_units(str(tmp_path))
        assert sorted(u[3] for u in units) == ['C001', 'C003']
        assert skips == []

    @pytest.mark.parametrize('exp_group,configid', [
        ('old_CORE', 'C001'),
        ('CORE_old', 'C001'),
        ('CORE', 'C1'),
        ('CORE', 'X001'),
        ('SCENARIO', 'C001'),
    ])
    def test_non_standard_directories_are_skipped(self, tmp_path, exp_group,
                                                  configid):
        make_unit(str(tmp_path), exp_group=exp_group, configid=configid)
        units, skips = discover_units(str(tmp_path))
        assert units == []
        assert len(skips) == 1
        assert 'non-standard' in skips[0][1]

    def test_hidden_directories_are_invisible(self, tmp_path):
        """A `.snapshot` beside a real unit is neither processed nor reported."""
        make_unit(str(tmp_path), group='.snapshot', exp_group='CORE',
                  configid='C001')
        assert discover_units(str(tmp_path)) == ([], [])

    def test_files_at_unit_depth_are_ignored(self, tmp_path):
        path = os.path.join(str(tmp_path), 'g', 'm', 'CORE')
        os.makedirs(path)
        open(os.path.join(path, 'stray.txt'), 'wb').close()
        units, skips = discover_units(str(tmp_path))
        assert units == [] and skips == []

    def test_empty_root(self, tmp_path):
        assert discover_units(str(tmp_path)) == ([], [])


class TestBuildCommand:
    def test_projection_pairs_with_its_historical(self, tmp_path):
        root = str(tmp_path)
        make_unit(root, configid='C001', experiment='historical',
                  years='1850-2014')
        unit = make_unit(root, configid='C003', experiment='ssp370')
        cmd, note = build_command(make_args(root), unit, CORE)
        assert cmd is not None
        assert cmd[cmd.index('--hist-configid') + 1] == 'C001'
        assert cmd[cmd.index('--hist') + 1] == 'historical'
        assert cmd[cmd.index('--experiment') + 1] == 'ssp370'
        assert 'hist C001' in note

    def test_historical_is_self_paired(self, tmp_path):
        root = str(tmp_path)
        unit = make_unit(root, configid='C001', experiment='historical',
                         years='1850-2014')
        cmd, note = build_command(make_args(root), unit, CORE)
        assert cmd[cmd.index('--hist-configid') + 1] == 'C001'
        assert 'self-paired' in note

    def test_invokes_the_installed_module(self, tmp_path):
        root = str(tmp_path)
        unit = make_unit(root, configid='C001', experiment='historical')
        cmd, _ = build_command(make_args(root), unit, CORE)
        assert cmd[1:3] == ['-m', 'ismip7_scalars']

    def test_missing_historical_is_skipped(self, tmp_path):
        root = str(tmp_path)
        unit = make_unit(root, configid='C003', experiment='ssp370')
        cmd, note = build_command(make_args(root), unit, CORE)
        assert cmd is None
        assert 'no historical C001' in note

    def test_self_pairing_projection_is_refused(self, tmp_path):
        """An ESM projection with no known historical must not pair with itself."""
        root = str(tmp_path)
        unit = make_unit(root, exp_group='ESM', configid='E003',
                         experiment='ssp585')
        cmd, note = build_command(make_args(root), unit, CORE)
        assert cmd is None
        assert 'E003' in note

    def test_no_lithk_is_skipped(self, tmp_path):
        root = str(tmp_path)
        unit = make_unit(root, configid='C001', var='topg',
                         experiment='historical')
        cmd, note = build_command(make_args(root), unit, CORE)
        assert cmd is None and note == 'no lithk file'

    def test_non_strict_filename_is_skipped(self, tmp_path):
        root = str(tmp_path)
        unit = make_unit(root, configid='C001', fname='lithk_AIS_junk.nc')
        cmd, note = build_command(make_args(root), unit, CORE)
        assert cmd is None and 'non-strict filename' in note

    def test_filename_configid_must_match_the_directory(self, tmp_path):
        root = str(tmp_path)
        unit = make_unit(root, configid='C001', experiment='historical')
        # A file for C005 sitting in the C001 directory.
        os.rename(
            os.path.join(unit[4], os.listdir(unit[4])[0]),
            os.path.join(unit[4],
                         'lithk_AIS_ISMIP7_SYNTH1_m001_CESM2-WACCM_f001'
                         '_historical_C005_1850-2014.nc'))
        cmd, note = build_command(make_args(root), unit, CORE)
        assert cmd is None and 'non-strict filename' in note

    def test_filename_group_must_match_the_directory(self, tmp_path):
        root = str(tmp_path)
        path = os.path.join(root, 'ISMIP7', 'SYNTH1', 'CORE', 'C001')
        os.makedirs(path)
        open(os.path.join(path,
                          'lithk_AIS_OTHER_SYNTH1_m001_CESM2-WACCM_f001'
                          '_historical_C001_1850-2014.nc'), 'wb').close()
        unit = ('ISMIP7', 'SYNTH1', 'CORE', 'C001', path)
        cmd, note = build_command(make_args(root), unit, CORE)
        assert cmd is None and 'group/model field' in note

    def test_wrong_region_is_skipped(self, tmp_path):
        root = str(tmp_path)
        unit = make_unit(root, configid='C001', region='GrIS',
                         experiment='historical')
        cmd, note = build_command(make_args(root), unit, CORE)
        assert cmd is None and 'non-strict filename' in note

    @pytest.mark.parametrize('option,value,flag', [
        ('params_path', '/params', '--params-path'),
        ('datapath', '/data', '--datapath'),
        ('outpath', '/out', '--outpath'),
    ])
    def test_paths_are_passed_through(self, tmp_path, option, value, flag):
        root = str(tmp_path)
        unit = make_unit(root, configid='C001', experiment='historical')
        args = make_args(root, **{option: value})
        cmd, _ = build_command(args, unit, CORE)
        assert cmd[cmd.index(flag) + 1] == value

    def test_histout_zero_is_passed_through(self, tmp_path):
        """0 is a meaningful value, so it must not be treated as unset."""
        root = str(tmp_path)
        unit = make_unit(root, configid='C001', experiment='historical')
        cmd, _ = build_command(make_args(root, histout=0), unit, CORE)
        assert cmd[cmd.index('--histout') + 1] == '0'

    def test_basins_flag_is_passed_through(self, tmp_path):
        root = str(tmp_path)
        unit = make_unit(root, configid='C001', experiment='historical')
        cmd, _ = build_command(make_args(root, basins=True), unit, CORE)
        assert '--basins' in cmd

    def test_scenario_unknown_to_the_table_uses_the_filename(self, tmp_path):
        """A PPE experiment is not in the CORE table but is still a projection."""
        root = str(tmp_path)
        make_unit(root, exp_group='PPE', configid='P001',
                  experiment='historical', years='1850-2014')
        unit = make_unit(root, exp_group='PPE', configid='P002',
                         experiment='ssp585')
        cmd, note = build_command(make_args(root), unit, CORE)
        assert cmd is not None
        assert cmd[cmd.index('--hist-configid') + 1] == 'P001'
        assert cmd[cmd.index('--exp-group') + 1] == 'PPE'


class TestKeepUnit:
    UNIT = ('NORCE', 'CISM', 'ESM', 'E001', '/path')

    @pytest.mark.parametrize('option,value,kept', [
        ('exp_group', 'ESM', True), ('exp_group', 'CORE', False),
        ('groups', 'NORCE', True), ('groups', 'VUW', False),
        ('groups', 'VUW,NORCE', True),
        ('models', 'CISM', True), ('models', 'PISM1', False),
        ('configids', 'E001', True), ('configids', 'E002', False),
    ])
    def test_filters(self, option, value, kept):
        args = make_args('/root', **{option: value})
        assert keep_unit(args, self.UNIT) is kept

    def test_no_filters_keeps_everything(self):
        assert keep_unit(make_args('/root'), self.UNIT) is True


class TestUnitStatus:
    def test_success(self, tmp_path):
        assert unit_status(0, str(tmp_path / 'x.log')) == 'OK'

    def test_crash(self, tmp_path):
        assert unit_status(1, str(tmp_path / 'x.log')) == 'FAIL: exit 1'

    def test_skip_reason_is_lifted_from_the_log(self, tmp_path):
        log = tmp_path / 'x.log'
        log.write_text('noise\nSKIP: AIS a/b/CORE/C001 -- missing topg\n')
        assert unit_status(2, str(log)) == \
            'SKIP: AIS a/b/CORE/C001 -- missing topg'

    def test_skip_without_a_log_still_reports_a_skip(self, tmp_path):
        assert unit_status(2, str(tmp_path / 'gone.log')) == 'SKIP: (see log)'


class TestFormatReport:
    def test_counts_each_category(self):
        results = [('a', 'OK', ''), ('b', 'SKIP: nope', ''),
                   ('c', 'FAIL: exit 1', ''), ('d', 'DRY-RUN', '')]
        report = format_report(make_args('/root'), '20260101T000000', results)
        assert 'ok: 1' in report
        assert 'skipped: 2' in report
        assert 'failed: 1' in report
        assert 'units: 4' in report


class TestParser:
    def test_region_is_required(self):
        with pytest.raises(SystemExit):
            build_parser().parse_args(['--modelpath', '/root'])

    def test_modelpath_is_required(self):
        with pytest.raises(SystemExit):
            build_parser().parse_args(['--region', 'AIS'])
