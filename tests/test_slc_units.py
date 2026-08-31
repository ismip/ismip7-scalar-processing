"""Unit tests for the sea-level contribution methods.

Every test builds its own synthetic array, so nothing here reads a file.  The
``c`` fixture supplies the standard densities.
"""

from __future__ import annotations

import numpy as np
import pytest

from ismip7_scalars.slc import (
    sl_constants,
    slc_A2020,
    slc_G2020,
    slc_G2020_publ,
    slc_vaf,
)


def cells(H0_val, H_val, B0_val, B_val, S_val=0.0, area=1e6):
    """One-cell arrays for a reference and a later state."""
    return (np.array([[float(H0_val)]]), np.array([[float(H_val)]]),
            np.array([[float(B0_val)]]), np.array([[float(B_val)]]),
            np.array([[float(S_val)]]), np.array([[float(area)]]))


def random_state(rng, shape=(4, 5)):
    """A mixed grounded/floating/ice-free pair of states on a random bed."""
    H0 = rng.uniform(0, 1500, shape)
    H = np.maximum(H0 - rng.uniform(0, 300, shape), 0.0)
    B0 = rng.uniform(-1200, 400, shape)
    B = B0 + rng.uniform(-5, 5, shape)
    S = np.zeros(shape)
    A = np.full(shape, 1e8)
    return H0, H, B0, B, S, A


# ---------------------------------------------------------------------------
# Constants


class TestConstants:
    def test_published_values(self):
        assert sl_constants.RHOI == 917.0
        assert sl_constants.RHOSW == 1027.0
        assert sl_constants.RHOFW == 1.0e3
        assert sl_constants.AO == 3.625e14

    def test_ice_is_less_dense_than_the_water_it_floats_in(self):
        assert sl_constants.RHOI < sl_constants.RHOFW < sl_constants.RHOSW


# ---------------------------------------------------------------------------
# VAF


class TestVAF:
    def test_identical_state_zero_slc(self, c):
        H0, H, B0, B, S0, A = cells(1000, 1000, -500, -500)
        assert slc_vaf.get_slc_vaf(H0, H, B0, B, S0, S0, A, c) == \
            pytest.approx(0.0)

    def test_fully_floating_zero_vaf(self, c):
        """Below the flotation thickness -- here 500*1027/917 ~ 560 m -- the
        ice displaces exactly its own weight and adds nothing to VAF."""
        vaf = slc_vaf.get_vaf(np.array([[500.0]]), np.array([[-500.0]]),
                              np.array([[0.0]]), np.array([[1e6]]), c)
        assert vaf == pytest.approx(0.0)

    def test_at_the_flotation_threshold_vaf_is_zero(self, c):
        H = np.array([[500.0 * c.RHOSW / c.RHOI]])
        vaf = slc_vaf.get_vaf(H, np.array([[-500.0]]), np.array([[0.0]]),
                              np.array([[1e6]]), c)
        assert vaf == pytest.approx(0.0, abs=1e-9)

    def test_mass_loss_positive_slc(self, c):
        H0, H, B0, B, S0, A = cells(1000, 800, -300, -300)
        assert slc_vaf.get_slc_vaf(H0, H, B0, B, S0, S0, A, c) > 0.0

    def test_mass_gain_negative_slc(self, c):
        H0, H, B0, B, S0, A = cells(800, 1000, -300, -300)
        assert slc_vaf.get_slc_vaf(H0, H, B0, B, S0, S0, A, c) < 0.0

    def test_grounded_loss_matches_the_analytic_value(self, c):
        """A metre of grounded ice over 1 km2 raises sea level by
        ``dH * area * RHOI / RHOFW / AO``, with no flotation correction to
        make because the bed is above sea level."""
        H0, H, B0, B, S0, A = cells(1000, 999, 100, 100, area=1e6)
        expected = 1.0 * 1e6 * c.RHOI / c.RHOFW / c.AO
        assert slc_vaf.get_slc_vaf(H0, H, B0, B, S0, S0, A, c) == \
            pytest.approx(expected, rel=1e-12)

    def test_losing_floating_ice_does_not_move_sea_level(self, c):
        """Shelf ice already displaces its own weight."""
        H0, H, B0, B, S0, A = cells(400, 200, -900, -900)
        assert slc_vaf.get_slc_vaf(H0, H, B0, B, S0, S0, A, c) == \
            pytest.approx(0.0)

    def test_scales_linearly_with_area(self, c):
        H0, H, B0, B, S0, A = cells(1000, 900, -300, -300, area=1e6)
        single = slc_vaf.get_slc_vaf(H0, H, B0, B, S0, S0, A, c)
        double = slc_vaf.get_slc_vaf(H0, H, B0, B, S0, S0, 2 * A, c)
        assert double == pytest.approx(2 * single, rel=1e-12)

    def test_zero_area_gives_zero(self, c):
        H0, H, B0, B, S0, A = cells(1000, 800, -300, -300, area=0.0)
        assert slc_vaf.get_slc_vaf(H0, H, B0, B, S0, S0, A, c) == 0.0

    def test_vtot_equals_vgr_plus_vfl(self, c):
        """Every cell is either grounded or floating, never both nor neither."""
        H0, H, B0, B, S0, A = cells(1000, 900, -400, -400)
        vtot = slc_vaf.get_slc_vtot(H0, H, A, c)
        vgr = slc_vaf.get_slc_vgr(H0, H, B0, B, S0, S0, A, c)
        vfl = slc_vaf.get_slc_vfl(H0, H, B0, B, S0, S0, A, c)
        assert vtot == pytest.approx(vgr + vfl, rel=1e-10)

    def test_vtot_vgr_vfl_on_a_mixed_grid(self, c):
        rng = np.random.default_rng(42)
        H0, H, B0, B, S0, A = random_state(rng, (3, 3))
        vtot = slc_vaf.get_slc_vtot(H0, H, A, c)
        vgr = slc_vaf.get_slc_vgr(H0, H, B0, B, S0, S0, A, c)
        vfl = slc_vaf.get_slc_vfl(H0, H, B0, B, S0, S0, A, c)
        assert vtot == pytest.approx(vgr + vfl, rel=1e-10)

    def test_hba_form_matches_the_general_form_when_sea_level_is_zero(self, c):
        """``*_HBA`` assumes S=0 rather than taking it as an argument."""
        rng = np.random.default_rng(11)
        H0, H, B0, B, S0, A = random_state(rng)
        assert slc_vaf.get_slc_vaf_HBA(H0, H, B0, B, A, c) == \
            pytest.approx(slc_vaf.get_slc_vaf(H0, H, B0, B, S0, S0, A, c),
                          rel=1e-12)

    def test_mean_diff_is_an_area_weighted_mean(self, c):
        R0 = np.zeros((2, 2))
        R = np.array([[1.0, 1.0], [3.0, 3.0]])
        A = np.ones((2, 2))
        assert slc_vaf.get_mean_diff(R0, R, A, 4.0) == pytest.approx(2.0)


# ---------------------------------------------------------------------------
# G2020


class TestG2020:
    def test_identical_state_zero_slc(self, c):
        H0, H, B0, B, _, A = cells(1000, 1000, -500, -500)
        assert slc_G2020.get_slc_G2020(H0, H, B0, B, A, c) == \
            pytest.approx(0.0)

    def test_three_component_sum(self, c):
        """Total = above-flotation + potential ocean volume + density."""
        H0, H, B0, B, _, A = cells(1000, 900, -400, -420, area=1e8)
        total = slc_G2020.get_slc_G2020(H0, H, B0, B, A, c)
        af = slc_G2020.get_slc_af_owv_G2020(H0, H, B0, B, A, c)
        pov = slc_G2020.get_slc_pov_G2020(B0, B, A, c)
        den = slc_G2020.get_slc_den_G2020(H0, H, A, c)
        assert total == pytest.approx(af + pov + den, rel=1e-10)

    def test_mass_loss_positive_slc(self, c):
        H0, H, B0, B, _, A = cells(1000, 800, -300, -300)
        assert slc_G2020.get_slc_G2020(H0, H, B0, B, A, c) > 0.0

    def test_pov_responds_to_a_deepening_bed(self, c):
        """A bed that sinks makes more room for ocean water, lowering sea level."""
        B0 = np.array([[-500.0]])
        B = np.array([[-600.0]])
        A = np.array([[1e8]])
        assert slc_G2020.get_slc_pov_G2020(B0, B, A, c) < 0.0

    def test_pov_ignores_bed_above_sea_level(self, c):
        """Only the below-sea-level part of the bed holds potential ocean."""
        A = np.array([[1e8]])
        assert slc_G2020.get_slc_pov_G2020(np.array([[100.0]]),
                                           np.array([[300.0]]), A, c) == \
            pytest.approx(0.0)

    def test_den_correction_vanishes_if_the_densities_are_equal(self):
        from types import SimpleNamespace
        equal = SimpleNamespace(RHOI=917.0, RHOSW=1000.0, RHOFW=1000.0,
                                AO=3.625e14)
        H0, H, _, _, _, A = cells(1000, 900, 0, 0, area=1e8)
        assert slc_G2020.get_slc_den_G2020(H0, H, A, equal) == \
            pytest.approx(0.0)

    def test_grounded_split_uses_the_flotation_criterion(self, c):
        """Grounded means ``H > -B * RHOSW/RHOI``."""
        A = np.array([[1e8]])
        # Bed above sea level: all grounded.
        vgr = slc_G2020.get_vgr_G2020(np.array([[1000.0]]),
                                      np.array([[100.0]]), A, c)
        assert vgr == pytest.approx(1000.0 * 1e8, rel=1e-10)
        # 1000 m of water needs > 1120 m of ice to stay grounded.
        vgr2 = slc_G2020.get_vgr_G2020(np.array([[500.0]]),
                                       np.array([[-1000.0]]), A, c)
        assert vgr2 == pytest.approx(0.0)

    def test_total_volume_is_area_weighted(self, c):
        """``get_vtot_G2020`` took an area argument but ignored it, so its
        answer was a sum of thicknesses rather than a volume."""
        H = np.array([[100.0, 200.0]])
        A = np.array([[1e8, 1e8]])
        expected = (100.0 + 200.0) * 1e8 * c.RHOSW / c.RHOI
        assert slc_G2020.get_vtot_G2020(H, A, c) == \
            pytest.approx(expected, rel=1e-12)

    def test_total_volume_scales_with_area(self, c):
        H = np.array([[100.0]])
        A = np.array([[1e8]])
        assert slc_G2020.get_vtot_G2020(H, 2 * A, c) == \
            pytest.approx(2 * slc_G2020.get_vtot_G2020(H, A, c))

    def test_slc_tot_matches_the_freshwater_free_conversion(self, c):
        H0 = np.array([[1000.0]])
        H = np.array([[900.0]])
        A = np.array([[1e8]])
        expected = 100.0 * 1e8 / c.AO
        assert slc_G2020.get_slc_tot_G2020(H0, H, A, c) == \
            pytest.approx(expected, rel=1e-12)


class TestG2020AgainstThePublishedForm:
    """``slc_G2020`` folds the geoid height into the bed; ``slc_G2020_publ``
    keeps them apart as the paper does.  With ``zn=0`` they must agree."""

    @pytest.fixture
    def states(self):
        rng = np.random.default_rng(2020)
        return random_state(rng)

    def test_total_slc_agrees(self, c, states):
        H0, H, B0, B, _, A = states
        zero = np.zeros_like(B)
        assert slc_G2020.get_slc_G2020(H0, H, B0, B, A, c) == pytest.approx(
            slc_G2020_publ.get_slc_G2020(H0, H, B0, B, zero, zero, A, c),
            rel=1e-12)

    def test_above_flotation_term_agrees(self, c, states):
        H0, H, B0, B, _, A = states
        zero = np.zeros_like(B)
        assert slc_G2020.get_vaf_G2020(H, B, A, c) == pytest.approx(
            slc_G2020_publ.get_vaf_G2020(H, B, zero, A, c), rel=1e-12)

    def test_potential_ocean_volume_term_agrees(self, c, states):
        _, _, B0, B, _, A = states
        zero = np.zeros_like(B)
        assert slc_G2020.get_vpov_G2020(B, A) == pytest.approx(
            slc_G2020_publ.get_vpov_G2020(B, zero, A), rel=1e-12)

    def test_density_term_is_the_same_function(self, c, states):
        H0, H, _, _, _, A = states
        assert slc_G2020.get_vden_G2020(H, A, c) == pytest.approx(
            slc_G2020_publ.get_vden_G2020(H, A, c), rel=1e-12)


# ---------------------------------------------------------------------------
# A2020


class TestA2020:
    def test_identical_state_zero_slc(self, c):
        H0, H, B0, B, S0, A = cells(1000, 1000, -500, -500)
        assert slc_A2020.get_slc_A2020(H0, H, B0, B, S0, S0, A, c) == \
            pytest.approx(0.0)

    def test_mass_loss_positive_slc(self, c):
        H0, H, B0, B, S0, A = cells(1000, 800, -300, -300)
        assert slc_A2020.get_slc_A2020(H0, H, B0, B, S0, S0, A, c) > 0.0

    def test_grounded_loss_matches_vaf(self, c):
        """Where both states are land, A2020 reduces to the mass change."""
        H0, H, B0, B, S0, A = cells(1000, 900, 200, 200, area=1e8)
        assert slc_A2020.get_slc_A2020(H0, H, B0, B, S0, S0, A, c) == \
            pytest.approx(slc_vaf.get_slc_vaf(H0, H, B0, B, S0, S0, A, c),
                          rel=1e-12)

    def test_accumulating_steps_telescopes_to_the_direct_difference(self, c):
        """A2020 is a difference between two states, so walking a trajectory
        step by step must land on the same value as comparing its ends.

        This is what the seamless-cumulative mode relies on, and it holds
        exactly only while no cell changes between land and ocean.
        """
        B = np.array([[200.0, 300.0]])
        S = np.zeros_like(B)
        A = np.full((1, 2), 1e8)
        thicknesses = [np.array([[1000.0, 900.0]]),
                       np.array([[980.0, 870.0]]),
                       np.array([[950.0, 860.0]]),
                       np.array([[900.0, 800.0]])]
        stepwise = sum(
            slc_A2020.get_slc_A2020(prev, nxt, B, B, S, S, A, c)
            for prev, nxt in zip(thicknesses, thicknesses[1:]))
        direct = slc_A2020.get_slc_A2020(thicknesses[0], thicknesses[-1],
                                         B, B, S, S, A, c)
        assert stepwise == pytest.approx(direct, rel=1e-12)

    def test_with_masks_matches_computing_them_internally(self, c):
        rng = np.random.default_rng(5)
        H0, H, B0, B, S0, A = random_state(rng)
        _, L0, G0 = slc_A2020.get_masks_A2020(H0, B0, S0, c)
        _, L, G = slc_A2020.get_masks_A2020(H, B, S0, c)
        assert slc_A2020.get_slc_A2020_with_masks(
            H0, H, B0, B, S0, S0, L0, L, G0, G, A, c) == pytest.approx(
            slc_A2020.get_slc_A2020(H0, H, B0, B, S0, S0, A, c), rel=1e-12)

    def test_scales_linearly_with_area(self, c):
        H0, H, B0, B, S0, A = cells(1000, 900, -300, -300, area=1e6)
        single = slc_A2020.get_slc_A2020(H0, H, B0, B, S0, S0, A, c)
        double = slc_A2020.get_slc_A2020(H0, H, B0, B, S0, S0, 2 * A, c)
        assert double == pytest.approx(2 * single, rel=1e-12)


class TestA2020Masks:
    def test_land_and_ocean_are_complementary(self, c):
        H = np.array([[1000.0, 0.0], [200.0, 800.0]])
        B = np.array([[-200.0, -100.0], [-1000.0, 100.0]])
        S = np.zeros_like(H)
        _, L, G = slc_A2020.get_masks_A2020(H, B, S, c)
        assert np.all(L + (1 - L) == 1)
        assert np.all(G <= L)

    def test_grounded_implies_ice(self, c):
        rng = np.random.default_rng(7)
        H = rng.uniform(0, 1500, (5, 5))
        B = rng.uniform(-600, 200, (5, 5))
        S = np.zeros((5, 5))
        I, _, G = slc_A2020.get_masks_A2020(H, B, S, c)
        assert np.all(G <= I)

    def test_bare_land_above_sea_level_is_land_but_not_ice(self, c):
        H = np.array([[0.0]])
        B = np.array([[100.0]])
        S = np.zeros_like(H)
        I, L, G = slc_A2020.get_masks_A2020(H, B, S, c)
        assert I[0, 0] == 0 and L[0, 0] == 1 and G[0, 0] == 0

    def test_open_ocean_is_neither_land_nor_ice(self, c):
        H = np.array([[0.0]])
        B = np.array([[-500.0]])
        S = np.zeros_like(H)
        I, L, G = slc_A2020.get_masks_A2020(H, B, S, c)
        assert I[0, 0] == 0 and L[0, 0] == 0 and G[0, 0] == 0

    def test_thick_ice_over_deep_water_is_grounded(self, c):
        H = np.array([[2000.0]])
        B = np.array([[-500.0]])
        S = np.zeros_like(H)
        _, _, G = slc_A2020.get_masks_A2020(H, B, S, c)
        assert G[0, 0] == 1

    def test_thin_ice_over_deep_water_is_floating(self, c):
        H = np.array([[100.0]])
        B = np.array([[-500.0]])
        S = np.zeros_like(H)
        I, L, G = slc_A2020.get_masks_A2020(H, B, S, c)
        assert I[0, 0] == 1 and L[0, 0] == 0 and G[0, 0] == 0


# ---------------------------------------------------------------------------
# Properties every method shares


ALL_METHODS = {
    'vaf': lambda H0, H, B0, B, S, A, c: slc_vaf.get_slc_vaf(
        H0, H, B0, B, S, S, A, c),
    'G2020': lambda H0, H, B0, B, S, A, c: slc_G2020.get_slc_G2020(
        H0, H, B0, B, A, c),
    'A2020': lambda H0, H, B0, B, S, A, c: slc_A2020.get_slc_A2020(
        H0, H, B0, B, S, S, A, c),
}


@pytest.mark.parametrize('name', sorted(ALL_METHODS))
class TestSharedProperties:
    def test_additive_over_disjoint_masks(self, c, name):
        """Splitting the domain into basins must not change the total.

        This is what makes the per-basin output add up to the whole-sheet
        output, which the integration tests then check end to end.
        """
        method = ALL_METHODS[name]
        rng = np.random.default_rng(99)
        H0, H, B0, B, S, A = random_state(rng, (4, 6))
        left, right = np.zeros_like(A), np.zeros_like(A)
        left[:, :3] = 1.0
        right[:, 3:] = 1.0
        whole = method(H0, H, B0, B, S, A, c)
        parts = (method(H0, H, B0, B, S, A * left, c)
                 + method(H0, H, B0, B, S, A * right, c))
        assert whole == pytest.approx(parts, rel=1e-10)

    def test_antisymmetric_in_the_two_states(self, c, name):
        """Reversing a change reverses its sea-level contribution."""
        method = ALL_METHODS[name]
        rng = np.random.default_rng(123)
        H0, H, B0, B, S, A = random_state(rng)
        forward = method(H0, H, B0, B, S, A, c)
        backward = method(H, H0, B, B0, S, A, c)
        assert forward == pytest.approx(-backward, rel=1e-10)

    def test_no_change_gives_no_contribution(self, c, name):
        method = ALL_METHODS[name]
        rng = np.random.default_rng(321)
        H0, _, B0, _, S, A = random_state(rng)
        assert method(H0, H0, B0, B0, S, A, c) == pytest.approx(0.0,
                                                                abs=1e-15)

    def test_uniform_grounded_thinning_agrees_across_methods(self, c, name):
        """High on a bed well above sea level, the three methods describe the
        same physics and must give the same number."""
        method = ALL_METHODS[name]
        H0 = np.full((3, 3), 1000.0)
        H = np.full((3, 3), 900.0)
        B = np.full((3, 3), 500.0)
        S = np.zeros((3, 3))
        A = np.full((3, 3), 1e8)
        expected = 100.0 * 9e8 * c.RHOI / c.RHOFW / c.AO
        assert method(H0, H, B, B, S, A, c) == pytest.approx(expected,
                                                             rel=1e-12)
