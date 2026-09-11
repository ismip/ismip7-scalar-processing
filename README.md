# ISMIP7 Scalar Processing

Turns gridded ISMIP7 ice sheet model output into the scalar time series the
community compares: three sea-level contributions, four state scalars and six
integrated mass fluxes, for the whole ice sheet and optionally for each IMBIE3
basin. Covers Antarctica (AIS) and Greenland (GrIS).

**Documentation: <https://ismip.github.io/ismip7-scalar-processing/>**

## Install and run

```bash
conda create -n ismip7-scalars -c conda-forge ismip7-scalars
conda activate ismip7-scalars
ismip7-scalars --region AIS \
    --group VUW --model PISM1 --modelid m001 \
    --esm CESM2-WACCM --forcingid f001 \
    --experiment ssp585 --configid C007 --hist-configid C001 \
    --modelpath Models/AIS --datapath Data/AIS
```

Three commands are installed:

- `ismip7-scalars` processes one experiment
- `ismip7-scalars-ensemble` processes every experiment in a submission tree
- `ismip7-scalars-set-params` writes the density file each model needs

## What you need

Your model output laid out as in an ISMIP7 submission, the area factors and
masks for your grid resolution, and a params.nc holding the densities your
model was run with. For the VUW group's PISM1 model:

```
Models/AIS/                <-- --modelpath: the ice sheet directory, not your model's
└── VUW/
    └── PISM1/
        ├── params.nc
        └── CORE/
            ├── C001/      lithk_AIS_VUW_PISM1_m001_CESM2-WACCM_f001_historical_C001_1850-2014.nc ...
            └── C007/      lithk_AIS_VUW_PISM1_m001_CESM2-WACCM_f001_ssp585_C007_2015-2300.nc ...
Data/AIS/                  <-- --datapath, from the ISMIP Globus server under Output-Processing
```

Output goes to Output/nc, in a tree mirroring the model tree, and to
Output/csv, flat. The
[getting started](https://ismip.github.io/ismip7-scalar-processing/getting-started.html)
page walks through this.

## Where to read more

| | |
|---|---|
| [Getting started](https://ismip.github.io/ismip7-scalar-processing/getting-started.html) | install, lay out the files, run one experiment |
| [File conventions](https://ismip.github.io/ismip7-scalar-processing/user/file-conventions.html) | filenames, directory layout, time encoding, params.nc |
| [Running the processing](https://ismip.github.io/ismip7-scalar-processing/user/running.html) | every option |
| [The output files](https://ismip.github.io/ismip7-scalar-processing/user/output.html) | what each file and CSV column holds |
| [The sea-level methods](https://ismip.github.io/ismip7-scalar-processing/user/slc-methods.html) | VAF, G2020 and A2020 |
| [Processing an ensemble](https://ismip.github.io/ismip7-scalar-processing/user/ensemble.html) | the batch driver |
| [Developer guide](https://ismip.github.io/ismip7-scalar-processing/dev/index.html) | source install, tests, MATLAB parity, releases |

## MATLAB

matlab/scalars.m computes the same scalars from the same inputs into the same
layout, and is kept numerically identical to the Python implementation. It is
run from a checkout rather than installed; see the
[MATLAB page](https://ismip.github.io/ismip7-scalar-processing/dev/matlab.html).

## Contributing

Problems and questions go in
[the issue tracker](https://github.com/ismip/ismip7-scalar-processing/issues).
Pull requests are welcome; the
[developer guide](https://ismip.github.io/ismip7-scalar-processing/dev/index.html)
covers the source install, the tests and the release process. If a change
touches a computed number, change the MATLAB implementation with it and say so
in the pull request.

Distributed under the MIT License; see [LICENSE](LICENSE).
