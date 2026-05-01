# ISMIP7 Scalar Processing

Scripts for computing sea-level contributions (SLC) and other scalar variables from ISMIP7 ice sheet model output for the Antarctic Ice Sheet (AIS) and Greenland Ice Sheet (GrIS). All scripts expect ISMIP7-compliant model output on the diagnostic ISMIP grid following ISMIP7 conventions for file names and units.

Three parallel implementations are provided: **Python** (primary), **NCO/bash** (GrIS only), and **MATLAB**.

## Requirements

```bash
conda create -n nc
conda activate nc
conda install -c conda-forge cdo=2.4.4 nco netCDF4 scipy
```

## Input data

In addition to model output, the scripts require masks and area factors available on the ISMIP Globus server under `Output-Processing`. Model-specific density parameters (`rhoi`, `rhow`, `rhof`) are read from a `params.nc` file in the model directory.

## Directory structure

By default, `Data/` and `Models/` are expected at the repository root. Any location on the file system can be used instead via the `--datapath` and `--modelpath` command-line options.

```
ismip7-scalar-processing/                        # repository root
├── slc/                                         # shared SLC computation package
├── python/scalars.py                            # AIS + GrIS (--region flag)
├── matlab/scalars.m                             # AIS + GrIS (region variable)
├── nco/scalars_GrIS.sh                          # GrIS NCO/bash implementation
├── MINI/                                        # lightweight test suite
│   └── python/
├── Data/                                        # default location for masks and area factors
│   ├── AIS/
│   ├── GrIS/
│   ├── MINI0/
│   └── MINI1/
├── Models/                                      # default location for model output
│   ├── AIS/{lab}/{model}/{exp}_{res}/
│   ├── GrIS/{lab}/{model}/{exp}_{res}/
│   └── MINI/ISMIP7/{MINI0,MINI1}/{exp}/
└── test/
    ├── AIS/compare_outputs.py
    └── GrIS/compare_outputs.py
```

## Running the scripts

All scripts accept CLI arguments; the default settings match the NORCE/CISM08-MAR312-p50 (GrIS) and VUW/PISM1 (AIS) reference configurations.

### Python (primary)

```bash
cd python
conda run -n nc python3 scalars.py --region AIS
conda run -n nc python3 scalars.py --region GrIS
conda run -n nc python3 scalars.py --region AIS --lab ISMIP7 --model TEST --exp exp0 --ref historical
```

Key arguments: `--region {AIS,GrIS}` (required), `--lab`, `--model`, `--exp`, `--ref`, `--refyear`, `--res`, `--datapath`, `--modelpath`, `--outpath`.

Output is written to `./output/` relative to the script directory.

### MATLAB

```bash
cd matlab
matlab -nodisplay -nosplash -r "region='AIS'; run('scalars.m'); exit"
matlab -nodisplay -nosplash -r "region='GrIS'; run('scalars.m'); exit"
```

Set workspace variables before `run()` to override any default (`lab`, `model`, `exp`, `ref`, `refyear`, `res`, `datapath`, `modelpath`, `outpath`).

### NCO/bash (GrIS only)

First create the model-specific parameter file, then run the main script:

```bash
cd nco
bash set_params.sh
bash scalars_GrIS.sh
```

## MINI test suite

The MINI suite provides lightweight test cases on a coarse 11×11 grid (600 km pixels) for rapid validation.

```bash
cd MINI/python

# Run a single case
conda run -n nc python3 scalars_MINI.py --model MINI1 --exp exp0

# Run all combinations (MINI0/MINI1 × exp0/expg) and print summary
conda run -n nc python3 run_MINI.py
```

Two grid variants are available:

| Grid  | Size  | Origin (xfirst, yfirst) | Notes |
|-------|-------|--------------------------|-------|
| MINI1 | 11×11 | −3,040,000 m             | primary test grid |
| MINI0 | 12×12 | −3,340,000 m             | half-cell-offset variant for CDO remapping tests |

MINI differs from the full AIS/GrIS scripts in three ways: the first time step serves as the SLC baseline (no separate historical reference), standard densities are used directly (no `params.nc`), and area weighting uses `dx²` directly.

## SLC methods

The `slc/` package implements three sea-level contribution methods:

| Method | Description |
|--------|-------------|
| `slc_vaf` | Volume Above Flotation — ISMIP6 method, freshwater conversion |
| `slc_G2020` | [Goelzer et al. 2020 (TC)](https://doi.org/10.5194/tc-14-833-2020) — adds potential ocean volume and density corrections |
| `slc_A2020` | [Adhikari et al. 2020 (TC)](https://doi.org/10.5194/tc-14-2819-2020) — absolute reference frame with grounding-line migration |

Three volume diagnostics are also computed (total, grounded, floating ice volume change).

Ocean area normalization uses `oarea = 3.625 × 10¹⁴ m²` (Gregory et al. 2019).

## Testing

After running both Python and MATLAB versions, compare outputs:

```bash
cd test/AIS && conda run -n nc python3 compare_outputs.py
cd test/GrIS && conda run -n nc python3 compare_outputs.py
```

Expected tolerance: < 1 × 10⁻¹⁰ m.
