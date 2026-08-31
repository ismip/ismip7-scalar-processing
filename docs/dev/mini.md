# The MINI cases

MINI is a hand-checkable ice sheet: an 11 × 11 grid of 600 km pixels, small
enough that the whole state fits on a screen and a wrong answer is visibly
wrong. It exists to catch mistakes that a full ice sheet would hide in its own
noise.

```bash
cd manual-tests/MINI
python scalars_MINI.py --model MINI1 --exp exp0   # one case
python run_MINI.py                                # all four, with a summary
```

Both read their input from the committed `test-data/` tree, so they run in a
fresh checkout with nothing else set up. Output goes to
`manual-tests/MINI/output/`.

## The cases

Two grids and two experiments:

| Grid | Size | Origin | Notes |
|---|---|---|---|
| MINI1 | 11 × 11 | −3,040,000 m | the primary test grid |
| MINI0 | 12 × 12 | −3,340,000 m | offset by half a cell, for CDO remapping tests |

`exp0`
: ice loss that includes partially floating cells, so the grounding line falls
  inside a cell and the two grids resolve it differently.

`expg`
: grounded ice only. With no floating ice and no grounding-line migration the
  three sea-level methods are describing the same physics, so they must agree
  exactly -- which makes this the sharpest check in the suite. Any disagreement
  is a bug in one of them.

The pair of grids is what makes remapping testable: the same ice on a grid
offset by half a cell must give the same *total* ice volume change, while VAF
may legitimately differ by a few per cent where the grounding line is
unresolved. `tests/test_mini_smoke.py` asserts both.

## How MINI differs from the real processing

`scalars_MINI.py` is a separate, deliberately simpler script, not a mode of
`ismip7-scalars`:

- the first timestep of the experiment is the reference; there is no separate
  historical run;
- the standard densities from `slc.sl_constants` are used directly, with no
  `params.nc`;
- area weighting is `dx²` directly;
- it writes the volume diagnostics (`slc_Vtot`, `slc_Vgr`, `slc_Vfl`) that the
  full processing does not.

It shares the `ismip7_scalars.slc` package with the real processing, which is
the part worth cross-checking; the rest is scaffolding around it.

## Regenerating the input files

`manual-tests/MINI/setup/` holds the scripts that built the committed inputs --
`derive_exp0.py`, `check_masks.py`, and the CDO/NCO shell scripts for
remapping and grounding. They need CDO and NCO on the path, which is why they
are not part of the test suite. The files they produce are committed under
`test-data/`, so nothing routine needs them.
