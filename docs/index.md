---
hide-toc: true
---

# ISMIP7 Scalar Processing

`ismip7-scalars` turns gridded ISMIP7 ice sheet model output into the scalar
time series the community compares: three sea-level contributions, four state
scalars, and six integrated mass fluxes, for the whole ice sheet and
optionally for each IMBIE3 basin.

```bash
conda create -n ismip7-scalars -c conda-forge ismip7-scalars
conda activate ismip7-scalars
ismip7-scalars --region AIS --group NORCE --model CISM16x-MAR312-p50 \
    --experiment ssp585 --configid C007 --hist-configid C001
```

::: {card} Getting started
:link: getting-started
:link-type: doc

Install the tools, run them over one experiment, and find the output.
:::

::: {card} User guide
:link: user/index
:link-type: doc

The filename conventions, every command-line option, what each output file
contains, the three sea-level methods, and how to process a whole ensemble.
:::

::: {card} Developer guide
:link: dev/index
:link-type: doc

Work on the package: install from source, run the tests, build these pages,
compare against the MATLAB implementation, and cut a release.
:::

## What it computes

For each experiment, and for each mask it is asked about:

**Sea-level contribution**, by three methods -- volume above flotation, and the
formulations of Goelzer et al. (2020) and Adhikari et al. (2020) -- each in two
variants, with and without glaciers and ice caps. See {doc}`user/slc-methods`.

**State scalars** `lim`, `limnsw`, `iareagr` and `iareafl`: the ice mass, the
ice mass not displacing sea water, and the grounded and floating areas.

**Flux scalars** `tendacabf`, `tendlibmassbfgr`, `tendlibmassbffl`,
`tendlicalvf`, `tendlifmassbf` and `tendligroundf`: the gridded mass fluxes
integrated over the mask.

{doc}`user/output` describes the files, their names and their contents.

## Where things live

The tools are developed at
[ismip/ismip7-scalar-processing](https://github.com/ismip/ismip7-scalar-processing)
and released through conda-forge. Problems and questions belong in
[the issue tracker](https://github.com/ismip/ismip7-scalar-processing/issues).

A MATLAB implementation of the same processing lives in `matlab/scalars.m` and
is kept numerically identical to the Python one; see {doc}`dev/matlab`.

```{toctree}
:hidden:

getting-started
user/index
dev/index
```
