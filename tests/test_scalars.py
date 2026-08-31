"""End-to-end tests of the scalar processing.

Each test runs the real command line over a synthetic submission written by
``tests.synthetic`` and reads the output back.  Together they replace the
``manual-tests`` scripts of earlier versions, which needed a submission tree
nobody had in CI.
"""

from __future__ import annotations

import csv
import glob
import os

import netCDF4 as nc
import numpy as np
import pytest

from ismip7_scalars.scalars import (
    _hist_times_on_exp_axis,
    build_parser,
    main,
    resolve_hist_n_out,
    settings_from_args,
)
from tests import synthetic

BASE_ARGS = ['--region', 'AIS', '--experiment', 'ssp585', '--configid',
             'C007', '--hist', 'historical', '--hist-configid', 'C001']


def run_scalars(submission, outpath, *extra):
    """Run the tool over the fixture submission.  Returns its exit code."""
    argv = BASE_ARGS + [
        '--datapath', submission.datapath,
        '--modelpath', submission.modelpath,
        '--outpath', str(outpath),
    ] + list(extra)
    return main(argv)


def nc_dir(outpath):
    """Where the run's NetCDF output lands, mirroring the model tree."""
    return os.path.join(str(outpath), 'nc', 'AIS', 'ISMIP7', 'SYNTH1', 'CORE',
                        'C007')


def read_series(outpath, varname, mask=None):
    """Read one output variable and its dates back."""
    pattern = os.path.join(nc_dir(outpath),
                           f'{varname}_{mask + "_" if mask else ""}*.nc')
    matches = glob.glob(pattern)
    assert len(matches) == 1, f'{pattern} matched {matches}'
    with nc.Dataset(matches[0]) as ds:
        tv = ds.variables['time']
        dates = nc.num2date(tv[:], tv.units, calendar=tv.calendar)
        return np.array(ds.variables[varname][:]), [d.year for d in dates]


@pytest.fixture
def default_run(submission, tmp_path):
    """One run with every default, shared by the tests that only read it."""
    assert run_scalars(submission, tmp_path) == 0
    return tmp_path


# ---------------------------------------------------------------------------
# Argument resolution


class TestSettings:
    def test_exp_group_defaults_from_the_configid(self):
        args = build_parser().parse_args(['--region', 'AIS', '--configid',
                                          'E001'])
        assert settings_from_args(args).exp_group == 'ESM'

    def test_explicit_exp_group_wins(self):
        args = build_parser().parse_args(['--region', 'AIS', '--configid',
                                          'E001', '--exp-group', 'PPE'])
        assert settings_from_args(args).exp_group == 'PPE'

    def test_hist_configid_defaults_to_configid(self):
        args = build_parser().parse_args(['--region', 'AIS', '--configid',
                                          'C007'])
        assert settings_from_args(args).hist_configid == 'C007'

    def test_params_path_defaults_to_modelpath(self):
        args = build_parser().parse_args(['--region', 'AIS', '--modelpath',
                                          '/models'])
        settings = settings_from_args(args)
        assert settings.params_path == '/models'
        assert settings.params_file == \
            '/models/ISMIP7/SYNTH1/params.nc'

    def test_paths_default_relative_to_the_working_directory(self):
        """An installed tool has no repository root to hang defaults off."""
        args = build_parser().parse_args(['--region', 'GrIS'])
        settings = settings_from_args(args, cwd='/work')
        assert settings.datapath == '/work/Data/GrIS'
        assert settings.modelpath == '/work/Models/GrIS'
        assert settings.outpath == '/work/Output'

    def test_region_defaults_differ(self):
        ais = settings_from_args(
            build_parser().parse_args(['--region', 'AIS']))
        gris = settings_from_args(
            build_parser().parse_args(['--region', 'GrIS']))
        assert ais.exp == 'ssp585'
        assert gris.exp == 'ctrl'

    def test_ism_member_id_is_an_alias_for_modelid(self):
        args = build_parser().parse_args(['--region', 'AIS',
                                          '--ism-member-id', 'm042'])
        assert settings_from_args(args).modelid == 'm042'

    def test_output_paths_mirror_the_model_tree(self):
        args = build_parser().parse_args(
            ['--region', 'AIS', '--configid', 'C007', '--outpath', '/out'])
        settings = settings_from_args(args)
        assert settings.ncpath == \
            '/out/nc/AIS/ISMIP7/SYNTH1/CORE/C007'
        assert settings.csvpath == '/out/csv'


class TestResolveHistNOut:
    @pytest.mark.parametrize('histout,expected', [
        (0, 0), (1, 1), (3, 3), (-1, 5),
    ])
    def test_modes(self, histout, expected):
        assert resolve_hist_n_out(histout, 5, exp_is_hist=False) == expected

    def test_clamped_to_the_run_length(self, capsys):
        assert resolve_hist_n_out(9999, 5, exp_is_hist=False) == 5
        assert 'Warning' in capsys.readouterr().out

    def test_nothing_prepended_when_exp_is_hist(self):
        """The historical run already writes its own full length."""
        assert resolve_hist_n_out(-1, 5, exp_is_hist=True) == 0


class TestHistTimesOnExpAxis:
    def test_identical_encodings_pass_through_untouched(self):
        values = np.array([0.0, 365.0])
        out = _hist_times_on_exp_axis(values, 'days since 1850-01-01',
                                      'noleap', 'days since 1850-01-01',
                                      'noleap')
        np.testing.assert_array_equal(out, values)

    def test_different_origins_are_converted(self):
        """Two runs need not share a time origin; raw values would misplace one.

        60 days after 2000-01-01 is 54 785 days after 1850-01-01 in the noleap
        calendar (150 years of 365 days, plus 60).
        """
        out = _hist_times_on_exp_axis(np.array([60.0]),
                                      'days since 2000-01-01', 'noleap',
                                      'days since 1850-01-01', 'noleap')
        assert out[0] == pytest.approx(150 * 365 + 60)


# ---------------------------------------------------------------------------
# What a default run produces


class TestDefaultRun:
    def test_exit_code(self, default_run):
        assert os.path.isdir(nc_dir(default_run))

    @pytest.mark.parametrize('varname', [
        'slvaf', 'slg20', 'sla20',                       # SLC
        'lim', 'limnsw', 'iareagr', 'iareafl',           # ST
        'tendacabf',                                     # FL
    ])
    def test_variable_is_written(self, default_run, varname):
        values, _ = read_series(default_run, varname)
        assert len(values) > 0

    def test_gic_variant_is_csv_only_by_default(self, default_run):
        """The GIC-masked SLC goes to CSV; only the plain variant gets NetCDF."""
        assert glob.glob(os.path.join(nc_dir(default_run),
                                      'slvaf-gic_*.nc')) == []
        assert len(glob.glob(os.path.join(str(default_run), 'csv',
                                          'slvaf-gic_*.csv'))) == 1

    def test_whole_sheet_filename_carries_no_mask_name(self, default_run):
        names = [os.path.basename(p)
                 for p in glob.glob(os.path.join(nc_dir(default_run),
                                                 'slvaf_*.nc'))]
        assert names == ['slvaf_AIS_ISMIP7_SYNTH1_m001_CESM2-WACCM_f001'
                         '_ssp585_C007_2010-2020.nc']

    def test_filename_year_range_is_nominal(self, default_run):
        """The stem's years are nominal; the ST timestamps are a year later."""
        _, years = read_series(default_run, 'slvaf')
        assert years == list(range(2011, 2022))

    def test_slc_is_zero_at_the_reference_timestep(self, default_run):
        """With no --refyear the reference is the last historical timestep."""
        for varname in ('slvaf', 'slg20', 'sla20'):
            values, years = read_series(default_run, varname)
            idx = years.index(2015)  # nominal 2014, the last hist year
            assert abs(float(values[idx])) < 1e-12, varname

    def test_thinning_ice_raises_sea_level(self, default_run):
        """The synthetic run thins monotonically, so SLC must rise throughout."""
        for varname in ('slvaf', 'slg20', 'sla20'):
            values, _ = read_series(default_run, varname)
            assert np.all(np.diff(values) > 0), varname

    def test_before_the_reference_slc_is_negative(self, default_run):
        values, _ = read_series(default_run, 'slvaf')
        assert values[0] < 0

    def test_land_ice_mass_decreases(self, default_run):
        lim, _ = read_series(default_run, 'lim')
        assert np.all(np.diff(lim) < 0)

    def test_limnsw_never_exceeds_lim(self, default_run):
        """Ice not displacing sea water is a subset of all the ice."""
        lim, _ = read_series(default_run, 'lim')
        limnsw, _ = read_series(default_run, 'limnsw')
        assert np.all(limnsw <= lim + 1e-6 * np.abs(lim))

    def test_grounded_and_floating_areas_are_disjoint_and_bounded(
            self, default_run):
        gr, _ = read_series(default_run, 'iareagr')
        fl, _ = read_series(default_run, 'iareafl')
        total = (synthetic.NY * synthetic.NX) * synthetic.DX ** 2
        assert np.all(gr >= 0) and np.all(fl >= 0)
        assert np.all(gr + fl <= total * (1 + 1e-12))

    def test_flux_time_axis_uses_nominal_years_directly(self, default_run):
        """FL timestamps sit at Jul 1 of year N, not Jan 1 of N+1."""
        _, years = read_series(default_run, 'tendacabf')
        assert years == list(range(2010, 2021))

    def test_absent_flux_variables_are_reported_not_fatal(self, submission,
                                                          tmp_path, capsys):
        assert run_scalars(submission, tmp_path) == 0
        out = capsys.readouterr().out
        assert 'Skipped scalars' in out
        assert 'tendlicalvf' in out
        assert 'tendacabf' not in out.split('Skipped scalars')[1]


class TestCsvOutput:
    def _read(self, outpath, name):
        matches = glob.glob(os.path.join(str(outpath), 'csv', name))
        assert len(matches) == 1, f'{name} matched {matches}'
        with open(matches[0], newline='') as f:
            header, row = list(csv.reader(f))
        return header, row

    def test_one_header_and_one_row(self, default_run):
        header, row = self._read(default_run, 'slvaf_*.csv')
        assert len(header) == len(row)

    def test_metadata_columns(self, default_run):
        header, row = self._read(default_run, 'slvaf_*.csv')
        record = dict(zip(header, row))
        assert record['ice_source'] == 'AIS'
        assert record['group'] == 'ISMIP7'
        assert record['model'] == 'SYNTH1'
        assert record['model_variant'] == 'm001'
        assert record['scenario'] == 'ssp585'
        assert record['GCM'] == 'CESM2-WACCM'
        assert record['configid'] == 'C007'

    def test_region_column_is_the_display_name(self, default_run):
        header, row = self._read(default_run, 'slvaf_*.csv')
        assert dict(zip(header, row))['region'] == 'ais'

    def test_gic_variant_region_column_carries_the_suffix(self, default_run):
        """Otherwise the two variants' rows are indistinguishable once merged."""
        header, row = self._read(default_run, 'slvaf-gic_*.csv')
        assert dict(zip(header, row))['region'] == 'ais-gic'

    def test_years_outside_the_run_are_na(self, default_run):
        header, row = self._read(default_run, 'slvaf_*.csv')
        record = dict(zip(header, row))
        assert record['y1850'] == 'NA'
        assert record['y2300'] == 'NA'

    def test_values_match_the_netcdf(self, default_run):
        header, row = self._read(default_run, 'slvaf_*.csv')
        record = dict(zip(header, row))
        values, years = read_series(default_run, 'slvaf')
        for value, year in zip(values, years):
            # The CSV is indexed by nominal year, the NetCDF by timestamp.
            assert float(record[f'y{year - 1}']) == pytest.approx(value)


# ---------------------------------------------------------------------------
# Options


class TestHistout:
    @pytest.mark.parametrize('histout,expected_first_year', [
        (0, 2016),    # projection only; first ST timestamp is Jan 1 2016
        (1, 2015),    # one historical step
        (3, 2013),
        (-1, 2011),   # every historical step
    ])
    def test_prepended_length(self, submission, tmp_path, histout,
                              expected_first_year):
        assert run_scalars(submission, tmp_path, '--histout',
                           str(histout)) == 0
        _, years = read_series(tmp_path, 'slvaf')
        assert years[0] == expected_first_year
        assert years[-1] == 2021

    def test_more_than_available_uses_all_and_warns(self, submission,
                                                    tmp_path, capsys):
        assert run_scalars(submission, tmp_path, '--histout', '9999') == 0
        assert 'exceeds hist length' in capsys.readouterr().out
        _, years = read_series(tmp_path, 'slvaf')
        assert years[0] == 2011

    def test_histout_zero_starts_away_from_the_reference(self, submission,
                                                         tmp_path):
        assert run_scalars(submission, tmp_path, '--histout', '0') == 0
        values, _ = read_series(tmp_path, 'slvaf')
        assert abs(float(values[0])) > 1e-9

    def test_the_projection_values_do_not_depend_on_histout(self, submission,
                                                            tmp_path):
        """Prepending history must not change the projection it precedes."""
        out_none, out_all = tmp_path / 'none', tmp_path / 'all'
        assert run_scalars(submission, out_none, '--histout', '0') == 0
        assert run_scalars(submission, out_all, '--histout', '-1') == 0
        for varname in ('slvaf', 'slg20', 'sla20', 'lim'):
            none_values, _ = read_series(out_none, varname)
            all_values, _ = read_series(out_all, varname)
            np.testing.assert_allclose(all_values[-len(none_values):],
                                       none_values, rtol=1e-12, atol=1e-15)

    def test_filename_year_range_follows_the_output(self, submission,
                                                    tmp_path):
        assert run_scalars(submission, tmp_path, '--histout', '0') == 0
        names = [os.path.basename(p)
                 for p in glob.glob(os.path.join(nc_dir(tmp_path),
                                                 'slvaf_*.nc'))]
        assert names[0].endswith('_2015-2020.nc')


class TestRefyear:
    def test_reference_inside_the_historical_run(self, submission, tmp_path,
                                                 capsys):
        """--refyear names a *timestamp* year, one more than the nominal year."""
        assert run_scalars(submission, tmp_path, '--refyear', '2013') == 0
        for varname in ('slvaf', 'sla20'):
            values, years = read_series(tmp_path, varname)
            assert abs(float(values[years.index(2013)])) < 1e-12, varname

    def test_reference_inside_the_projection(self, submission, tmp_path,
                                             capsys):
        assert run_scalars(submission, tmp_path, '--refyear', '2018') == 0
        assert 'not found in hist' in capsys.readouterr().out
        for varname in ('slvaf', 'sla20'):
            values, years = read_series(tmp_path, varname)
            idx = years.index(2018)
            assert abs(float(values[idx])) < 1e-12, varname
            assert values[0] < 0 and values[-1] > 0

    def test_reference_in_neither_run_is_skipped(self, submission, tmp_path,
                                                 capsys):
        assert run_scalars(submission, tmp_path, '--refyear', '1900') == 2
        assert 'SKIP:' in capsys.readouterr().out

    def test_shifting_the_reference_shifts_the_whole_series(self, submission,
                                                            tmp_path):
        """VAF is measured against a reference state, so a different reference
        is a constant offset -- nothing about the trajectory changes."""
        a, b = tmp_path / 'a', tmp_path / 'b'
        assert run_scalars(submission, a, '--refyear', '2012') == 0
        assert run_scalars(submission, b, '--refyear', '2014') == 0
        va, _ = read_series(a, 'slvaf')
        vb, _ = read_series(b, 'slvaf')
        np.testing.assert_allclose(np.diff(va), np.diff(vb), rtol=1e-10)


class TestBasins:
    def test_basins_sum_to_the_whole_sheet(self, submission, tmp_path):
        """The 18 IMBIE3 basins partition the grid, so their SLC must add up."""
        assert run_scalars(submission, tmp_path, '--basins') == 0
        for varname in ('slvaf', 'slg20', 'sla20', 'lim', 'iareagr'):
            whole, _ = read_series(tmp_path, varname, mask='ais')
            total = np.zeros_like(whole)
            for i in range(1, 19):
                part, _ = read_series(tmp_path, varname, mask=f'r{i:02d}')
                total += part
            np.testing.assert_allclose(total, whole, rtol=1e-10,
                                       atol=1e-15 * np.max(np.abs(whole) + 1))

    def test_imbie_regions_sum_to_the_whole_sheet(self, submission, tmp_path):
        assert run_scalars(submission, tmp_path, '--basins') == 0
        whole, _ = read_series(tmp_path, 'slvaf', mask='ais')
        total = sum(read_series(tmp_path, 'slvaf', mask=name)[0]
                    for name in ('wais', 'eais', 'pina'))
        np.testing.assert_allclose(total, whole, rtol=1e-10,
                                   atol=1e-15 * np.max(np.abs(whole) + 1))

    def test_basin_mode_names_the_whole_sheet_mask(self, submission,
                                                   tmp_path):
        """Without --basins the mm file has no mask field; with it, it does."""
        assert run_scalars(submission, tmp_path, '--basins') == 0
        assert glob.glob(os.path.join(nc_dir(tmp_path), 'slvaf_ais_*.nc'))
        assert glob.glob(os.path.join(nc_dir(tmp_path),
                                      'slvaf_AIS_*.nc')) == []

    def test_flux_scalars_are_split_too(self, submission, tmp_path):
        assert run_scalars(submission, tmp_path, '--basins') == 0
        whole, _ = read_series(tmp_path, 'tendacabf', mask='ais')
        total = np.zeros_like(whole)
        for i in range(1, 19):
            part, _ = read_series(tmp_path, 'tendacabf', mask=f'r{i:02d}')
            total += part
        np.testing.assert_allclose(total, whole, rtol=1e-10)


class TestNoMm:
    def test_skips_the_whole_sheet_integral(self, submission, tmp_path):
        """`--no-mm` used to be silently ignored, writing the mm output anyway."""
        assert run_scalars(submission, tmp_path, '--basins', '--no-mm') == 0
        assert glob.glob(os.path.join(nc_dir(tmp_path), 'slvaf_ais_*.nc')) \
            == []
        assert glob.glob(os.path.join(nc_dir(tmp_path), 'slvaf_r01_*.nc'))

    def test_without_basins_it_is_an_error(self, submission, tmp_path):
        """It would otherwise ask for no output at all."""
        with pytest.raises(SystemExit):
            run_scalars(submission, tmp_path, '--no-mm')


# ---------------------------------------------------------------------------
# Missing and malformed input


class TestMissingInput:
    def test_missing_experiment_directory_skips(self, submission, tmp_path,
                                                capsys):
        rc = run_scalars(submission, tmp_path, '--configid', 'C999')
        assert rc == 2
        assert 'SKIP:' in capsys.readouterr().out

    def test_missing_generic_data_skips(self, submission, tmp_path, capsys):
        rc = main(BASE_ARGS + ['--datapath', str(tmp_path / 'nothing'),
                               '--modelpath', submission.modelpath,
                               '--outpath', str(tmp_path)])
        assert rc == 2
        assert 'SKIP:' in capsys.readouterr().out

    def test_missing_params_skips_and_says_how_to_fix_it(self, tmp_path,
                                                         capsys):
        root = str(tmp_path / 'sub')
        datapath = synthetic.write_data_files(
            os.path.join(root, 'Data', 'AIS'))
        modelpath = os.path.join(root, 'Models', 'AIS')
        synthetic.write_experiment(modelpath, experiment='historical',
                                   configid='C001', start_year=2010,
                                   nyears=3)
        synthetic.write_experiment(modelpath, experiment='ssp585',
                                   configid='C007', start_year=2013,
                                   nyears=3)
        rc = main(BASE_ARGS + ['--datapath', datapath, '--modelpath',
                               modelpath, '--outpath', str(tmp_path / 'out')])
        assert rc == 2
        out = capsys.readouterr().out
        assert 'params.nc' in out
        assert 'ismip7-scalars-set-params' in out

    def test_missing_masks_skip_only_the_st_scalars(self, tmp_path, capsys):
        """SLC and FL do not use sftgrf/sftflf, so they are still written."""
        root = str(tmp_path / 'sub')
        datapath = synthetic.write_data_files(
            os.path.join(root, 'Data', 'AIS'))
        modelpath = os.path.join(root, 'Models', 'AIS')
        synthetic.write_params(modelpath)
        for experiment, configid, start in [('historical', 'C001', 2010),
                                            ('ssp585', 'C007', 2013)]:
            synthetic.write_experiment(
                modelpath, experiment=experiment, configid=configid,
                start_year=start, nyears=3,
                variables=('lithk', 'topg'), fluxes=('acabf',))
        outpath = tmp_path / 'out'
        assert main(BASE_ARGS + ['--datapath', datapath, '--modelpath',
                                 modelpath, '--outpath', str(outpath)]) == 0
        assert 'skipping ST scalars' in capsys.readouterr().out
        assert glob.glob(os.path.join(nc_dir(outpath), 'slvaf_*.nc'))
        assert glob.glob(os.path.join(nc_dir(outpath), 'tendacabf_*.nc'))
        assert glob.glob(os.path.join(nc_dir(outpath), 'lim_*.nc')) == []

    def test_ambiguous_model_file_skips(self, submission, tmp_path, capsys):
        """Two lithk files for one run: processing either would be a guess."""
        root = str(tmp_path / 'sub')
        datapath = synthetic.write_data_files(
            os.path.join(root, 'Data', 'AIS'))
        modelpath = os.path.join(root, 'Models', 'AIS')
        synthetic.write_params(modelpath)
        exppath = synthetic.write_experiment(
            modelpath, experiment='ssp585', configid='C007', start_year=2013,
            nyears=3)
        synthetic.write_experiment(modelpath, experiment='historical',
                                   configid='C001', start_year=2010, nyears=3)
        original = glob.glob(os.path.join(exppath, 'lithk_*.nc'))[0]
        with open(original, 'rb') as src:
            data = src.read()
        with open(original.replace('2013-2015', '2013-2016'), 'wb') as dst:
            dst.write(data)
        rc = main(BASE_ARGS + ['--datapath', datapath, '--modelpath',
                               modelpath, '--outpath', str(tmp_path / 'out')])
        assert rc == 2
        assert 'multiple files match' in capsys.readouterr().out


# ---------------------------------------------------------------------------
# The historical run processed on its own


class TestHistoricalRunAlone:
    def test_self_referenced_run(self, tmp_path):
        """With --experiment equal to --hist there is no separate reference."""
        root = str(tmp_path / 'sub')
        datapath = synthetic.write_data_files(
            os.path.join(root, 'Data', 'AIS'))
        modelpath = os.path.join(root, 'Models', 'AIS')
        synthetic.write_params(modelpath)
        synthetic.write_experiment(modelpath, experiment='historical',
                                   configid='C001', start_year=2010,
                                   nyears=4)
        outpath = tmp_path / 'out'
        rc = main(['--region', 'AIS', '--experiment', 'historical',
                   '--configid', 'C001', '--hist', 'historical',
                   '--hist-configid', 'C001', '--datapath', datapath,
                   '--modelpath', modelpath, '--outpath', str(outpath)])
        assert rc == 0
        ncpath = os.path.join(str(outpath), 'nc', 'AIS', 'ISMIP7', 'SYNTH1',
                              'CORE', 'C001')
        matches = glob.glob(os.path.join(ncpath, 'slvaf_*.nc'))
        assert len(matches) == 1
        with nc.Dataset(matches[0]) as ds:
            values = np.array(ds.variables['slvaf'][:])
        # Four timesteps, not four plus a prepended copy of themselves.
        assert len(values) == 4
        # The reference is the last timestep, so the series ends at zero.
        assert abs(float(values[-1])) < 1e-12
        assert values[0] < 0


class TestVersionAndHelp:
    def test_version(self, capsys):
        with pytest.raises(SystemExit) as excinfo:
            main(['--version'])
        assert excinfo.value.code == 0
        assert 'ismip7-scalars' in capsys.readouterr().out

    def test_region_is_required(self):
        with pytest.raises(SystemExit):
            main([])
