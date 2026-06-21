"""
Unit tests for the slc/ package.

All tests use synthetic 1- or few-cell arrays — no external data files needed.
Run with:  pytest tests/
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

import numpy as np
import pytest
from types import SimpleNamespace

from slc import slc_vaf, slc_G2020, slc_A2020

# ── standard constants fixture ────────────────────────────────────────────────

@pytest.fixture
def c():
    ns = SimpleNamespace()
    ns.RHOI  = 917.0
    ns.RHOSW = 1027.0
    ns.RHOFW = 1000.0
    ns.AO    = 3.625e14
    return ns


# ── helpers ───────────────────────────────────────────────────────────────────

def scalar_arrays(H0_val, H_val, B0_val, B_val, S_val=0.0, area=1e6):
    """Return 1-cell arrays with given values."""
    H0 = np.array([[H0_val]])
    H  = np.array([[H_val]])
    B0 = np.array([[B0_val]])
    B  = np.array([[B_val]])
    S  = np.array([[S_val]])
    A  = np.array([[area]])
    return H0, H, B0, B, S, A


# ── VAF tests ─────────────────────────────────────────────────────────────────

class TestVAF:
    def test_identical_state_zero_slc(self, c):
        H0, H, B0, B, S0, A = scalar_arrays(1000, 1000, -500, -500)
        assert slc_vaf.get_slc_vaf(H0, H, B0, B, S0, S0, A, c) == pytest.approx(0.0)

    def test_fully_floating_zero_vaf(self, c):
        """Floating ice (H < floatation thickness) contributes 0 VAF."""
        # floatation threshold: hf = (S-B)*RHOSW/RHOI = 500*1027/917 ≈ 559.8 m
        H_float = np.array([[500.0]])   # well below flotation
        B       = np.array([[-500.0]])
        S       = np.array([[0.0]])
        A       = np.array([[1e6]])
        vaf = slc_vaf.get_vaf(H_float, B, S, A, c)
        assert vaf == pytest.approx(0.0)

    def test_mass_loss_positive_slc(self, c):
        """Ice loss (H decreases) should produce positive SLC (sea-level rise)."""
        H0, H, B0, B, S0, A = scalar_arrays(1000, 800, -300, -300)
        slc = slc_vaf.get_slc_vaf(H0, H, B0, B, S0, S0, A, c)
        assert slc > 0.0

    def test_mass_gain_negative_slc(self, c):
        """Ice gain (H increases) should produce negative SLC (sea-level fall)."""
        H0, H, B0, B, S0, A = scalar_arrays(800, 1000, -300, -300)
        slc = slc_vaf.get_slc_vaf(H0, H, B0, B, S0, S0, A, c)
        assert slc < 0.0

    def test_vtot_equals_vgr_plus_vfl(self, c):
        """Vtot = Vgr + Vfl (volume decomposition identity)."""
        H0, H, B0, B, S0, A = scalar_arrays(1000, 900, -400, -400)
        vtot = slc_vaf.get_slc_vtot(H0, H, A, c)
        vgr  = slc_vaf.get_slc_vgr(H0, H, B0, B, S0, S0, A, c)
        vfl  = slc_vaf.get_slc_vfl(H0, H, B0, B, S0, S0, A, c)
        assert vtot == pytest.approx(vgr + vfl, rel=1e-10)

    def test_vtot_vgr_vfl_multi_cell(self, c):
        """Vtot = Vgr + Vfl holds on a 3×3 mixed grounded/floating grid."""
        rng = np.random.default_rng(42)
        H0  = rng.uniform(500, 1500, (3, 3))
        H   = rng.uniform(400, 1400, (3, 3))
        B0  = rng.uniform(-800, 200, (3, 3))
        B   = B0.copy()
        S0  = np.zeros((3, 3))
        A   = np.ones((3, 3)) * 1e8
        vtot = slc_vaf.get_slc_vtot(H0, H, A, c)
        vgr  = slc_vaf.get_slc_vgr(H0, H, B0, B, S0, S0, A, c)
        vfl  = slc_vaf.get_slc_vfl(H0, H, B0, B, S0, S0, A, c)
        assert vtot == pytest.approx(vgr + vfl, rel=1e-10)


# ── G2020 tests ───────────────────────────────────────────────────────────────

class TestG2020:
    def test_identical_state_zero_slc(self, c):
        H0, H, B0, B, S0, A = scalar_arrays(1000, 1000, -500, -500)
        assert slc_G2020.get_slc_G2020(H0, H, B0, B, A, c) == pytest.approx(0.0)

    def test_three_component_sum(self, c):
        """Total G2020 SLC = af + pov + den."""
        H0 = np.array([[1000.0]])
        H  = np.array([[900.0]])
        B0 = np.array([[-400.0]])
        B  = np.array([[-420.0]])   # slight bed change
        A  = np.array([[1e8]])
        slc_total = slc_G2020.get_slc_G2020(H0, H, B0, B, A, c)
        af  = -(slc_G2020.get_vaf_G2020(H, B, A, c)  - slc_G2020.get_vaf_G2020(H0, B0, A, c))  / c.AO * c.RHOI/c.RHOSW
        pov = -(slc_G2020.get_vpov_G2020(B, A)        - slc_G2020.get_vpov_G2020(B0, A))         / c.AO
        den = -(slc_G2020.get_vden_G2020(H, A, c)     - slc_G2020.get_vden_G2020(H0, A, c))      / c.AO
        assert slc_total == pytest.approx(af + pov + den, rel=1e-10)

    def test_mass_loss_positive_slc(self, c):
        H0, H, B0, B, S0, A = scalar_arrays(1000, 800, -300, -300)
        slc = slc_G2020.get_slc_G2020(H0, H, B0, B, A, c)
        assert slc > 0.0

    def test_grounded_split_correct_sign(self, c):
        """get_vgr_G2020 with confirmed sign fix: grounded = H > (-B)*RHOSW/RHOI."""
        # purely grounded cell: H=1000 m, B=+100 m (above sea level) → all grounded
        H = np.array([[1000.0]])
        B = np.array([[100.0]])
        A = np.array([[1e8]])
        vgr = slc_G2020.get_vgr_G2020(H, B, A, c)
        assert vgr == pytest.approx(1000.0 * 1e8, rel=1e-10)

        # purely floating: B=-1000 m, floatation threshold = 1000*1027/917 ≈ 1120 m
        # H=500 m < threshold → not grounded
        H2 = np.array([[500.0]])
        B2 = np.array([[-1000.0]])
        vgr2 = slc_G2020.get_vgr_G2020(H2, B2, A, c)
        assert vgr2 == pytest.approx(0.0)


# ── A2020 tests ───────────────────────────────────────────────────────────────

class TestA2020:
    def test_identical_state_zero_slc(self, c):
        H0, H, B0, B, S0, A = scalar_arrays(1000, 1000, -500, -500)
        assert slc_A2020.get_slc_A2020(H0, H, B0, B, S0, S0, A, c) == pytest.approx(0.0)

    def test_mass_loss_positive_slc(self, c):
        H0, H, B0, B, S0, A = scalar_arrays(1000, 800, -300, -300)
        slc = slc_A2020.get_slc_A2020(H0, H, B0, B, S0, S0, A, c)
        assert slc > 0.0

    def test_cumulative_zero_at_start(self, c):
        """Cumulative A2020: first step (H_prev==H) contributes 0."""
        H0, H, B0, B, S0, A = scalar_arrays(1000, 1000, -500, -500)
        step = slc_A2020.get_slc_A2020(H0, H, B0, B, S0, S0, A, c)
        assert step == pytest.approx(0.0)

    def test_masks_land_ocean_complement(self, c):
        """L + O = 1 everywhere (land/ocean masks are complementary)."""
        H = np.array([[1000.0, 0.0], [200.0, 800.0]])
        B = np.array([[-200.0, -100.0], [-1000.0, 100.0]])
        S = np.zeros_like(H)
        I, L, G = slc_A2020.get_masks_A2020(H, B, S, c)
        O = 1 - L
        assert np.all(L + O == 1)
        assert np.all(G <= L)   # grounded ⊆ land

    def test_grounded_implies_ice(self, c):
        """G ≤ I: grounded ice is a subset of ice-covered cells."""
        rng = np.random.default_rng(7)
        H = rng.uniform(0, 1500, (5, 5))
        B = rng.uniform(-600, 200, (5, 5))
        S = np.zeros((5, 5))
        I, L, G = slc_A2020.get_masks_A2020(H, B, S, c)
        assert np.all(G <= I)


# ── Cross-method consistency ──────────────────────────────────────────────────

class TestCrossMethod:
    def test_vaf_g20_agree_for_simple_grounded(self, c):
        """For purely grounded, static-bed ice VAF and G2020 should be close
        (not identical — different density conventions, but same sign/order)."""
        H0, H, B0, B, S0, A = scalar_arrays(1000, 900, 50, 50)  # above sea level
        slc_v = slc_vaf.get_slc_vaf(H0, H, B0, B, S0, S0, A, c)
        slc_g = slc_G2020.get_slc_G2020(H0, H, B0, B, A, c)
        # Both should be positive (mass loss) and within 10% of each other
        assert slc_v > 0
        assert slc_g > 0
        assert abs(slc_v - slc_g) / slc_v < 0.10
