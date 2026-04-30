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

The `Data/` and `Models/` directories for AIS and GrIS live **one level above the repository root**. MINI data lives at the repository root.

```
../                                              # one level above repo
├── Data/
│   ├── AIS/                                     # AIS masks and area factors
│   └── GrIS/                                    # GrIS masks and area factors
└── Models/
    ├── AIS/
    │   └── {lab}/{model}/{exp}_{res}/           # AIS model output
    └── GrIS/
        └── {lab}/{model}/{exp}_{res}/           # GrIS model output

ismip7-scalar-processing/                        # repository root
├── slc/                                         # shared SLC computation package
├── AIS/
│   ├── python/scalars_AIS.py
│   └── matlab/scalars_AIS.m
├── GrIS/
│   ├── python/scalars_GrIS.py
│   ├── matlab/scalars_GrIS.m
│   └── nco/scalars_GrIS.sh
├── MINI/                                        # lightweight test suite
│   └── python/
├── Data/                                        # MINI masks and area factors
│   ├── MINI0/
│   └── MINI1/
├── Models/                                      # MINI model output
│   └── MINI/ISMIP7/{MINI0,MINI1}/{exp}/
└── test/
    ├── AIS/compare_outputs.py
    └── GrIS/compare_outputs.py
```

## Running the scripts

Before running, set the user configuration at the top of each script (`lab`, `model`, `exp`, `res`, paths, flags).

### Python (primary)

```bash
cd AIS/python && conda run -n nc python3 scalars_AIS.py
cd GrIS/python && conda run -n nc python3 scalars_GrIS.py
```

Output is written to `./output/` relative to the script directory.

### MATLAB

```bash
cd AIS/matlab && matlab -nodisplay -nosplash -r "run('scalars_AIS.m'); exit"
cd GrIS/matlab && matlab -nodisplay -nosplash -r "run('scalars_GrIS.m'); exit"
```

### NCO/bash (GrIS only)

First create the model-specific parameter file, then run the main script:

```bash
cd GrIS/nco
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
| `slc_A2020` | [Adhikari et al. 2020 (TC)](https://doi.org/10.5194/tc-14-833-2020) — absolute reference frame with grounding-line migration |

Three volume diagnostics are also computed (total, grounded, floating ice volume change).

Ocean area normalization uses `oarea = 3.625 × 10¹⁴ m²` (Gregory et al. 2019).

## Testing

After running both Python and MATLAB versions, compare outputs:

```bash
cd test/AIS && conda run -n nc python3 compare_outputs.py
cd test/GrIS && conda run -n nc python3 compare_outputs.py
```

Expected tolerance: < 1 × 10⁻¹⁰ m.

## License

MIT — see [LICENSE](LICENSE).
