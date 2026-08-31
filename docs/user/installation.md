# Installation

## From conda-forge

```bash
conda create -n ismip7-scalars -c conda-forge ismip7-scalars
conda activate ismip7-scalars
```

This is the supported way to install the tools, and the one to use unless you
are working *on* them. It brings the dependencies with it, so nothing else has
to be installed.

Check what you got:

```bash
ismip7-scalars --version
```

## What it installs

Three commands:

`ismip7-scalars`
: process one experiment. {doc}`running`

`ismip7-scalars-ensemble`
: process every unit under a submissions root. {doc}`ensemble`

`ismip7-scalars-set-params`
: write the `params.nc` holding a model's densities.

and one importable package, `ismip7_scalars`, whose `slc` subpackage holds the
sea-level methods described in {doc}`slc-methods`. Nothing stops you calling
those directly from your own analysis:

```python
from ismip7_scalars.slc import slc_vaf
```

`python -m ismip7_scalars` is equivalent to `ismip7-scalars`, which is
occasionally useful when several environments are on the path at once.

## Dependencies

Installing from conda-forge pulls these in for you. They matter when you
install from source, where the environment is yours to create -- see
{doc}`../dev/source-install`.

| Package | Constraint | Why bounded |
|---|---|---|
| `python` | `>=3.11,<3.15` | `tomllib` and `X \| None` annotations; 3.10 is EOL in Oct 2026 |
| `numpy` | `>=2.1,<3` | what recent conda-forge `netCDF4` builds are built against |
| `netCDF4` | `>=1.7,<2` | every input is read and every output written through it |

The constraints live in `ismip7_scalars_env.yml`, and the same ones appear in
`pyproject.toml`. The test suite runs at both ends of every range, so results
should agree across machines and operating systems within these bounds.

If you report a problem, please include the output of `conda list` for your
environment.

## MATLAB

The MATLAB implementation is not installed by any of this; it is the
`matlab/scalars.m` script in the repository, run from a checkout. See
{doc}`../dev/matlab`.
