# Installation

## From a checkout

The package is not on conda-forge yet. Until it is, install from a checkout
of the repository:

```bash
git clone https://github.com/ismip/ismip7-scalar-processing.git
cd ismip7-scalar-processing
conda env create -f ismip7_scalars_env.yml
conda activate ismip7-scalars
python -m pip install --no-deps --no-build-isolation .
ismip7-scalars --version
```

The last line should print a version. Once a conda-forge package exists,
this page will say `conda create` instead.

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

ismip7_scalars_env.yml installs these:

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
