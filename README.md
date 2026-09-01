# ISMIP7 Scalar Processing

Turns gridded ISMIP7 ice sheet model output into the scalar time series the
community compares: three sea-level contributions, four state scalars and six
integrated mass fluxes, for the whole ice sheet and optionally for each IMBIE3
basin. Covers the Antarctic (AIS) and Greenland (GrIS) ice sheets.

**Documentation: <https://ismip.github.io/ismip7-scalar-processing/>**

## Install and run

```bash
conda create -n ismip7-scalars -c conda-forge ismip7-scalars
conda activate ismip7-scalars
ismip7-scalars --region AIS \
    --group VUW --model PISM1 --modelid m001 \
    --esm CESM2-WACCM --forcingid f001 \
    --experiment ssp585 --configid C007 --hist-configid C001 \
    --datapath ./Data/AIS --modelpath ./Models/AIS
```

NetCDF output lands in a tree mirroring the model layout,
`Output/nc/{region}/{group}/{model}/{exp_group}/{configid}/`; the sea-level
CSVs land flat in `Output/csv/`.

Three commands are installed:

| | |
|---|---|
| `ismip7-scalars` | process one experiment |
| `ismip7-scalars-ensemble` | process every unit under a submissions root |
| `ismip7-scalars-set-params` | write the `params.nc` holding a model's densities |

## What you need

Model output following the ten-field ISMIP7 filename convention, laid out as
`{modelpath}/{group}/{model}/{exp_group}/{configid}/`; the generic data files
(area factors and masks) for your resolution, from the ISMIP Globus server
under `Output-Processing`; and a `params.nc` giving the densities your model
was integrated with. The resolution is detected from the model grid.

A run that cannot find an input prints one `SKIP:` line and exits 2 rather than
raising, so a batch can log it and move on. Missing `sftgrf`/`sftflf` skips only
the state scalars, and each flux variable is skipped on its own.

## Where to read more

| | |
|---|---|
| [Getting started](https://ismip.github.io/ismip7-scalar-processing/getting-started.html) | install, run one experiment, find the output |
| [File conventions](https://ismip.github.io/ismip7-scalar-processing/user/file-conventions.html) | filenames, directory layout, time encoding, `params.nc` |
| [Running the processing](https://ismip.github.io/ismip7-scalar-processing/user/running.html) | every command-line option |
| [The output files](https://ismip.github.io/ismip7-scalar-processing/user/output.html) | what each file and CSV column holds |
| [The sea-level methods](https://ismip.github.io/ismip7-scalar-processing/user/slc-methods.html) | VAF, G2020 and A2020, and how they differ |
| [Processing an ensemble](https://ismip.github.io/ismip7-scalar-processing/user/ensemble.html) | the batch driver over a submissions tree |
| [Developer guide](https://ismip.github.io/ismip7-scalar-processing/dev/index.html) | source install, tests, MATLAB parity, releases |

## MATLAB

`matlab/scalars.m` computes the same scalars from the same inputs into the same
layout, and is kept numerically identical to the Python implementation --
observed differences are at machine epsilon. It is run from a checkout rather
than installed; see the
[MATLAB page](https://ismip.github.io/ismip7-scalar-processing/dev/matlab.html).

## Contributing

Problems and questions belong in
[the issue tracker](https://github.com/ismip/ismip7-scalar-processing/issues).
Pull requests are welcome; the
[developer guide](https://ismip.github.io/ismip7-scalar-processing/dev/index.html)
covers the source install, the test suite and the release process. If a change
touches a computed number, change the MATLAB implementation with it and say so
in the pull request.

Distributed under the MIT License; see [LICENSE](LICENSE).
