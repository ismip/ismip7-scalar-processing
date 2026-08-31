"""End-to-end tests of the MINI cases.

MINI is a hand-checkable ice sheet on an 11x11 grid of 600 km pixels, in two
grid variants that differ by half a cell so that CDO remapping between them can
be checked.  Its input files are committed under ``test-data/``, so these tests
need nothing from the Globus server.
"""

from __future__ import annotations

import os
import subprocess
import sys

import netCDF4 as nc
import numpy as np
import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MINI_DIR = os.path.join(REPO_ROOT, 'manual-tests', 'MINI')
TEST_DATA = os.path.join(REPO_ROOT, 'test-data')

MODELS = ['MINI0', 'MINI1']
EXPERIMENTS = ['exp0', 'expg']

#: Every series the MINI script writes.
VARIABLES = ['slc_VAF', 'slc_G2020', 'slc_A2020', 'slc_Vtot', 'slc_Vgr',
             'slc_Vfl']


def run_mini(model, exp, outpath):
    """Run one MINI case into ``outpath``.  Returns ``{variable: array}``."""
    result = subprocess.run(
        [sys.executable, 'scalars_MINI.py', '--model', model, '--exp', exp,
         '--outpath', str(outpath),
         '--datapath', os.path.join(TEST_DATA, 'Data', model),
         '--modelpath', os.path.join(TEST_DATA, 'Models', 'MINI', 'ISMIP7',
                                     model)],
        capture_output=True, text=True, cwd=MINI_DIR)
    assert result.returncode == 0, (
        f'scalars_MINI.py {model}/{exp} failed:\n{result.stdout}\n'
        f'{result.stderr}')

    outfile = os.path.join(str(outpath),
                           f'scalars_mm_AIS_ISMIP7_{model}_{exp}.nc')
    assert os.path.exists(outfile), f'Output file not created: {outfile}'
    with nc.Dataset(outfile) as ds:
        return {name: np.array(ds.variables[name][:]) for name in VARIABLES}


@pytest.fixture(scope='session')
def mini_results(tmp_path_factory):
    """Every MINI case, run once for the whole session."""
    outpath = tmp_path_factory.mktemp('mini')
    return {(model, exp): run_mini(model, exp, outpath)
            for model in MODELS for exp in EXPERIMENTS}


@pytest.mark.parametrize('model', MODELS)
@pytest.mark.parametrize('exp', EXPERIMENTS)
class TestEveryCase:
    def test_all_variables_written(self, mini_results, model, exp):
        series = mini_results[(model, exp)]
        for name in VARIABLES:
            assert len(series[name]) > 0, name

    def test_first_timestep_is_the_reference(self, mini_results, model, exp):
        """MINI takes its own first timestep as the reference state."""
        series = mini_results[(model, exp)]
        for name in VARIABLES:
            assert abs(float(series[name][0])) < 1e-12, name

    def test_ice_loss_raises_sea_level(self, mini_results, model, exp):
        series = mini_results[(model, exp)]
        assert float(series['slc_VAF'][-1]) > 1e-9

    def test_methods_agree_in_sign(self, mini_results, model, exp):
        series = mini_results[(model, exp)]
        expected = np.sign(series['slc_VAF'][-1])
        for name in ('slc_G2020', 'slc_A2020'):
            assert np.sign(series[name][-1]) == expected, name

    def test_volume_decomposition(self, mini_results, model, exp):
        """Total ice volume change splits into grounded plus floating."""
        series = mini_results[(model, exp)]
        np.testing.assert_allclose(
            series['slc_Vgr'] + series['slc_Vfl'], series['slc_Vtot'],
            rtol=1e-10, atol=1e-15)


@pytest.mark.parametrize('model', MODELS)
class TestGroundedCase:
    """``expg`` removes only grounded ice sitting above sea level."""

    def test_no_floating_ice_is_lost(self, mini_results, model):
        assert float(mini_results[(model, 'expg')]['slc_Vfl'][-1]) == \
            pytest.approx(0.0, abs=1e-12)

    def test_every_method_gives_the_same_answer(self, mini_results, model):
        """With no floating ice and no grounding-line migration, the three
        methods describe the same physics, so any disagreement between them is
        a bug in one of them rather than a modelling choice."""
        series = mini_results[(model, 'expg')]
        reference = float(series['slc_Vtot'][-1])
        for name in ('slc_VAF', 'slc_G2020', 'slc_A2020', 'slc_Vgr'):
            assert float(series[name][-1]) == pytest.approx(reference,
                                                            rel=1e-10), name


class TestAcrossGridVariants:
    """MINI0 is MINI1 offset by half a cell -- the same ice on a shifted grid."""

    @pytest.mark.parametrize('exp', EXPERIMENTS)
    def test_total_volume_change_is_grid_independent(self, mini_results, exp):
        """Total ice volume does not depend on how the grid is laid out, so the
        two variants must agree to remapping accuracy."""
        mini0 = float(mini_results[('MINI0', exp)]['slc_Vtot'][-1])
        mini1 = float(mini_results[('MINI1', exp)]['slc_Vtot'][-1])
        assert mini0 == pytest.approx(mini1, rel=1e-5)

    def test_grounded_case_agrees_across_variants(self, mini_results):
        mini0 = float(mini_results[('MINI0', 'expg')]['slc_VAF'][-1])
        mini1 = float(mini_results[('MINI1', 'expg')]['slc_VAF'][-1])
        assert mini0 == pytest.approx(mini1, rel=1e-5)

    def test_partial_flotation_differs_between_variants(self, mini_results):
        """Where the grounding line falls inside a cell, the two grids resolve
        it differently, and VAF is expected to differ by a few per cent.  This
        pins that difference so a change in the flotation criterion shows up as
        a test failure rather than a quiet drift."""
        mini0 = float(mini_results[('MINI0', 'exp0')]['slc_VAF'][-1])
        mini1 = float(mini_results[('MINI1', 'exp0')]['slc_VAF'][-1])
        assert 0.0 < abs(mini0 - mini1) / mini1 < 0.10
