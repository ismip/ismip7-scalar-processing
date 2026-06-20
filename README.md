# ISMIP7 Scalar Processing

Scripts for computing sea-level contributions (SLC) and other scalar variables from ISMIP7 ice sheet model output for the Antarctic Ice Sheet (AIS) and Greenland Ice Sheet (GrIS). All scripts expect ISMIP7-compliant model output on the diagnostic ISMIP grid following the **new ISMIP7 naming conventions** (10-field filename, see below).

Two implementations are provided: **Python** (primary) and **MATLAB**. Conversion scripts for older (ISMIP6) submissions live in the sibling repo `convert-submissions-ismip6-to-ismip7`.

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
├── tools/                                       # shared helper scripts
│   ├── set_params.sh                            # generate params.nc for a model
│   └── params_template.nc                       # template for model-specific densities
├── Data/                                        # default location for masks and area factors
│   ├── AIS/
│   ├── GrIS/
│   ├── MINI0/
│   └── MINI1/
├── Models/                                      # default location for model output
│   ├── AIS/{group}/{model}/{exp_group}/
│   ├── GrIS/{group}/{model}/{exp_group}/
│   └── MINI/ISMIP7/{MINI0,MINI1}/{exp}/
└── manual-tests/
    ├── compare_outputs.py                       # Python vs MATLAB comparison (--region filter)
    ├── test_histout.py                          # integration test for --histout
    ├── test_refyear.py                          # integration test for --refyear
    └── MINI/                                   # lightweight MINI test suite
        ├── scalars_MINI.py
        ├── run_MINI.py
        ├── output/
        └── setup/                              # experiment generation and remapping tools
            ├── derive_exp0.py
            ├── check_masks.py
            ├── ground.sh
            ├── interpolate.sh
            ├── remapCDO.sh
            ├── gdf_ISMIP7_MINI0.txt
            └── gdf_ISMIP7_MINI1.txt
```

## ISMIP7 filename convention

Model output files follow the new 10-field ISMIP7 naming convention:

```
{var}_{region}_{group}_{model}_{modelid}_{ESM}_{forcingid}_{experiment}_{configid}_{startyear}-{endyear}.nc
```

Example: `lithk_GrIS_NORCE_CISM08-MAR312-p50_m001_NorESM2-MM_f001_historical_E001_1960-2014.nc`

| Field | Meaning | Example |
|-------|---------|---------|
| `{group}` | Submitting institution | `NORCE` |
| `{model}` | Ice sheet model | `CISM08-MAR312-p50` |
| `{modelid}` | ISM member ID (`mNNN`) | `m001` |
| `{ESM}` | Climate forcing model (CMIP6/7) | `NorESM2-MM` |
| `{forcingid}` | Forcing realization (`fNNN`) | `f001` |
| `{experiment}` | Scenario | `historical`, `ssp126`, `ctrl` |
| `{configid}` | Configuration counter (`[C/E/P]NNN`) | `E001` |
| `{startyear}-{endyear}` | Nominal simulation years | `1960-2014` |

Files are stored under `Models/{region}/{group}/{model}/{exp_group}/` where `{exp_group}` is one of `CORE`, `ESM`, or `PPE`.

**Time encoding:** ST (state) variables carry timestamps at Jan 1 of year N+1; FL (flux) variables carry timestamps at Jul 1 of year N with `time_bounds`. The filename year range always refers to nominal simulation years (ST timestamp year − 1).


## Running the scripts

All scripts accept CLI arguments; the default settings match the NORCE/CISM08-MAR312-p50 (GrIS) and VUW/PISM1 (AIS) reference configurations.

### Python (primary)

```bash
cd python
conda run -n nc python3 scalars.py --region AIS
conda run -n nc python3 scalars.py --region GrIS
conda run -n nc python3 scalars.py --region GrIS --group NORCE --model CISM08-MAR312-p50 \
  --modelid m001 --esm NorESM2-MM --forcingid f001 --experiment historical --configid E001 \
  --exp-group ESM
```

Key arguments: `--region {AIS,GrIS}` (required), `--group`, `--model`, `--experiment`, `--modelid`, `--esm`, `--forcingid`, `--configid`, `--exp-group`, `--hist`, `--hist-exp-group`, `--refyear`, `--histout`, `--res`, `--datapath`, `--modelpath`, `--outpath`.

Output is written to `./output/` (NetCDF) and `./csv/` (CSV) relative to the script directory. Six files are produced per ice-sheet mask region (three NetCDF + three CSV, one per SLC method):

```
output/slvaf_{mask}_{region}_{group}_{model}_{modelid}_{esm}_{forcingid}_{exp}_{configid}_{y0}-{y1}.nc
output/slg20_{mask}_{region}_{group}_{model}_{modelid}_{esm}_{forcingid}_{exp}_{configid}_{y0}-{y1}.nc
output/sla20_{mask}_{region}_{group}_{model}_{modelid}_{esm}_{forcingid}_{exp}_{configid}_{y0}-{y1}.nc
csv/slvaf_{mask}_{region}_{group}_{model}_{modelid}_{esm}_{forcingid}_{exp}_{configid}_{y0}-{y1}.csv
csv/slg20_{mask}_{region}_{group}_{model}_{modelid}_{esm}_{forcingid}_{exp}_{configid}_{y0}-{y1}.csv
csv/sla20_{mask}_{region}_{group}_{model}_{modelid}_{esm}_{forcingid}_{exp}_{configid}_{y0}-{y1}.csv
```

where `{mask}` is `mm` (whole ice sheet) or a basin name, and `{y0}-{y1}` is the nominal simulation year range covered by the output (historical reference year through end of projection). Each NetCDF contains `time` and the SLC variable (in metres). Each CSV has one data row with metadata columns (`ice_source`, `region`, `group`, `model`, `model_variant`, `scenario`, `GCM`, `forcingid`, `configid`) followed by annual columns `y1850`–`y2300` (NA outside the simulation period).

### MATLAB

```bash
cd matlab
matlab -nodisplay -nosplash -r "region='AIS'; run('scalars.m'); exit"
matlab -nodisplay -nosplash -r "region='GrIS'; run('scalars.m'); exit"
```

Set workspace variables before `run()` to override any default (`group`, `model`, `exp`, `modelid`, `esm`, `forcingid`, `configid`, `exp_group`, `hist`, `hist_exp_group`, `refyear`, `res`, `datapath`, `modelpath`, `outpath`).

### Model density parameters

Each model directory must contain a `params.nc` file with ice (`rhoi`), ocean (`rhow`), and freshwater (`rhof`) densities. Use `tools/set_params.sh` to generate one from `tools/params_template.nc`:

```bash
bash tools/set_params.sh
```

## MINI test suite

The MINI suite provides lightweight test cases on a coarse 11×11 grid (600 km pixels) for rapid validation.

```bash
cd manual-tests/MINI

# Run a single case
conda run -n nc python3 scalars_MINI.py --model MINI1 --exp exp0

# Run all combinations (MINI0/MINI1 × exp0/expg) and print summary
conda run -n nc python3 run_MINI.py
```

Experiment generation and grid remapping tools live in `manual-tests/MINI/setup/`.

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

**Smoke test** — lightweight MINI suite, no external data required:

```bash
cd manual-tests
conda run -n nc python3 test_mini.py
```

**Integration tests** — require model output under `Data/` and `Models/` (defaults use the VUW/PISM1 AIS reference run):

```bash
cd manual-tests
conda run -n nc python3 test_histout.py --datapath ../Data/AIS --modelpath ../Models/AIS
conda run -n nc python3 test_refyear.py --datapath ../Data/AIS --modelpath ../Models/AIS
```

**Python vs MATLAB comparison** — after running both implementations for the same submission:

```bash
cd manual-tests
conda run -n nc python3 compare_outputs.py --region AIS
conda run -n nc python3 compare_outputs.py --region GrIS
```

The comparison script matches files by their full ISMIP7 stem and checks all three SLC methods. Expected tolerance: < 1 × 10⁻¹⁰ m.

## Converting old-format submissions

Conversion scripts for old-format (ISMIP6, 5-field naming) submissions live in the separate repo `convert-submissions-ismip6-to-ismip7` (sibling directory). See that repo for usage.

Converted files can be validated with the [ISM_SimulationChecker](https://github.com/ismip/ISM_SimulationChecker):

```bash
cd ISM_SimulationChecker
python compliance_checker.py --source-path ../ismip7-scalar-processing/Models/GrIS/NORCE/CISM08-MAR312-p50/ESM --variable-list ismip7_xyt
```
