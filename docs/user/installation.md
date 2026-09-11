# Installation

## From conda-forge

```bash
conda create -n ismip7-scalars -c conda-forge ismip7-scalars
conda activate ismip7-scalars
ismip7-scalars --version
```

This is the supported way to install, and the one to use unless you are
working on the tools themselves. Everything needed comes with it.

## What it installs

Three commands:

- `ismip7-scalars` processes one experiment ({doc}`running`)
- `ismip7-scalars-ensemble` processes every experiment in a submission tree
  ({doc}`ensemble`)
- `ismip7-scalars-set-params` writes a model's params.nc
  ({doc}`file-conventions`)

and a Python package, ismip7_scalars, whose slc subpackage holds the sea-level
methods in {doc}`slc-methods`. You can call those from your own analysis:

```python
from ismip7_scalars.slc import slc_vaf
```

`python -m ismip7_scalars` does the same as `ismip7-scalars`, which helps when
several environments are on the path at once.

## Dependencies

Installing from conda-forge brings these along. They matter if you install
from source ({doc}`../dev/source-install`):

| Package | Versions | Reason for the bounds |
|---|---|---|
| python | 3.11 to 3.14 | uses tomllib and modern type syntax |
| numpy | 2.1 up to 3 | what recent conda-forge netCDF4 builds are built against |
| netCDF4 | 1.7 up to 2 | every file is read and written through it |
| isschecker | 0.2 up to 1 | ships the ISMIP7 data request; see {doc}`data-sources` |

The test suite runs at both ends of every range. If you report a problem,
please include the output of `conda list` for your environment.

## MATLAB

The MATLAB implementation is not installed by any of this. It is the
matlab/scalars.m script in the repository, run from a checkout. See
{doc}`../dev/matlab`.
