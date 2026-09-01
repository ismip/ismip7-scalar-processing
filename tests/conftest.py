"""Fixtures shared by the test suite."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from tests import synthetic


@pytest.fixture
def c():
    """Standard densities and ocean area, as the SLC methods expect them."""
    ns = SimpleNamespace()
    ns.RHOI = 917.0
    ns.RHOSW = 1027.0
    ns.RHOFW = 1000.0
    ns.AO = 3.625e14
    return ns


@pytest.fixture(scope='session')
def submission(tmp_path_factory):
    """A miniature AIS submission: historical C001 plus an ssp585 projection.

    Session-scoped because writing it costs more than any test that reads it,
    and nothing in the suite modifies it -- every run writes its output into a
    temporary directory of its own.
    """
    root = tmp_path_factory.mktemp('submission')
    datapath, modelpath = synthetic.write_submission(str(root))
    return SimpleNamespace(root=str(root), datapath=datapath,
                           modelpath=modelpath, region='AIS',
                           group='ISMIP7', model='SYNTH1',
                           experiment='ssp585', configid='C007',
                           hist_configid='C001', exp_group='CORE',
                           hist_years=5, exp_years=6,
                           hist_start=2010, exp_start=2015)
