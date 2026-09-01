# Running the tests

```bash
conda activate ismip7-scalars
pytest -v
```

The suite needs no external data: everything it reads is either written by the
tests themselves or committed under `test-data/`. It takes a few seconds.

## What is where

`tests/test_slc_units.py`
: the sea-level methods, on synthetic arrays small enough to check by hand.
  Analytic cases (a metre of grounded ice over a square kilometre), the volume
  identity `Vtot = Vgr + Vfl`, the A2020 masks, `slc_G2020` against the
  published formulation in `slc_G2020_publ`, and the properties all three
  methods share -- additivity over disjoint masks, antisymmetry in the two
  states, agreement for uniform grounded thinning.

`tests/test_naming.py`
: the filename conventions -- what parses, what does not, and what happens when
  two files match one lookup.

`tests/test_writers.py`
: the NetCDF and CSV writers, including which year each CSV column holds.

`tests/test_params.py`
: the `params.nc` writer and its entry point.

`tests/test_ensemble.py`
: the batch driver's planning: which directories are units, which historical
  run each projection pairs with, and what each skip reason is. It does not run
  any unit.

`tests/test_scalars.py`
: the pipeline end to end, over a miniature submission written by
  `tests/synthetic.py`. `--histout`, `--refyear`, `--basins`, `--no-mm`, the
  CSV contents, the exit codes, and every way an input can be missing.

`tests/test_mini_smoke.py`
: the MINI cases, from the committed inputs. See {doc}`mini`.

## The synthetic submission

`tests/synthetic.py` writes a strictly ISMIP7-shaped submission on an 8 × 10
grid at 16 km: a rectangular ice sheet on a bed sloping from above sea level in
the east to deep water in the west, thinning linearly in time, with the two
westernmost columns left ice-free. It is not meant to look like an ice sheet.
It is meant to have grounded ice, floating ice and open ocean at once, so that
every branch of the integration is exercised, and to thin monotonically, so that
a test can say what the answer should do without hard-coding what it is.

Writing it rather than committing a fixture tree keeps the geometry under the
tests' control and keeps the repository free of binary files nobody can review.

Adding a case usually means calling `write_experiment` with different
`variables` or `fluxes` -- that is how the "missing `sftgrf` skips only the
state scalars" test builds a submission without mask files.

## What CI runs

`.github/workflows/pytest.yml` runs the whole suite on Linux and macOS, against
both a fresh solve of the dependency ranges and the pinned floor, so that both
ends of every range are tested. It installs the package the way the docs tell
you to and then runs `pytest` from **outside** the checkout, so the tests import
the installed package: a data file or entry point that did not make it into the
wheel fails there rather than passing against the source tree.

`.github/workflows/docs.yml` builds these pages with `-W`, so a broken
cross-reference or a page missing from every toctree fails the build.

## What is not tested here

Two things need data that cannot live in the repository, and are in
`manual-tests/`:

- `compare_outputs.py`, the Python-versus-MATLAB comparison. See
  {doc}`matlab`.
- the MINI `setup/` scripts, which need CDO and NCO to regenerate the MINI
  input files. The files they produce *are* committed, so the MINI tests
  themselves run in CI.
