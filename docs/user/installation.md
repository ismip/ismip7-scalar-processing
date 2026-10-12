# Installation

## From conda-forge

The tools are packaged on
[conda-forge](https://anaconda.org/conda-forge/ismip7-scalars), for Linux and
macOS. There is no need to clone the repository:

```bash
conda create -n ismip7-scalars -c conda-forge ismip7-scalars
conda activate ismip7-scalars
ismip7-scalars --version
```

The last line should print a version. `mamba` and `micromamba` work the same
way. If your conda is set up with the `defaults` channel, add
`--override-channels`; packages from the two channels do not mix.

## Updating

New releases come often, with bug fixes and new features. Update before you
process new output:

```bash
conda update -n ismip7-scalars -c conda-forge ismip7-scalars
ismip7-scalars --version
```

The conda-forge package is built from tagged releases, so a fix can be on the
repository's main branch for a while before it reaches you.

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

The conda-forge package brings these with it:

| Package | Versions | Reason for the bounds |
|---|---|---|
| python | 3.11 to 3.14 | uses tomllib and modern type syntax |
| numpy | 2.1 up to 3 | what recent conda-forge netCDF4 builds are built against |
| netCDF4 | 1.7 up to 2 | every file is read and written through it |
| isschecker | 0.2 up to 1 | ships the ISMIP7 data request; see {doc}`data-sources` |

The test suite runs at both ends of every range. If you report a problem,
please include the output of `ismip7-scalars --version` and of `conda list`.

## From source

You only need a source install to work *on* the package: to test a change
that has not been released yet, or to develop one. {doc}`../dev/source-install`
covers it.

## MATLAB

The MATLAB implementation is not in the conda-forge package. It is the
matlab/scalars.m script in the repository, run from a clone. See
{doc}`../dev/matlab`.
