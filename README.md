# ISMIP7 Scalar Processing

Scripts for computing sea-level contributions (SLC) and other scalar variables from ISMIP7 ice sheet model output for the Antarctic Ice Sheet (AIS) and Greenland Ice Sheet (GrIS). All scripts expect ISMIP7-compliant model output on the diagnostic ISMIP grid following the **new ISMIP7 naming conventions** (10-field filename, see below).

Two implementations are provided: **Python** (primary) and **MATLAB**. Conversion scripts for older (ISMIP6) submissions live in the sibling repo `convert-submissions-ismip6-to-ismip7`.

## Requirements

```bash
conda create -n nc
conda activate nc
conda install -c conda-forge cdo=2.4.4 nco netCDF4 scipy pytest
```

## Input data

In addition to model output, the scripts require masks and area factors available on the ISMIP Globus server under `Output-Processing`. Model-specific density parameters (`rhoi`, `rhow`, `rhof`) are read from a `params.nc` file in the model directory.

## Directory structure

By default, `Data/` and `Models/` are expected at the repository root. Any location on the file system can be used instead via the `--datapath` and `--modelpath` command-line options.

```
ismip7-scalar-processing/                        # repository root
├── python/
│   ├── scalars.py                               # AIS + GrIS (--region flag)
│   └── slc/                                     # shared SLC computation package
├── matlab/scalars.m                             # AIS + GrIS (region variable, mirrors python/)
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
├── Output/
│   ├── nc/                                      # NetCDF output (gitignored)
│   └── csv/                                     # CSV output (gitignored)
├── tests/
│   ├── test_slc_units.py                        # pytest: slc/ physics unit tests (no ext data)
│   └── test_mini_smoke.py                       # pytest: MINI end-to-end smoke tests
├── test-data/                                   # committed MINI inputs for self-contained CI
│   ├── Data/{MINI0,MINI1}/
│   └── Models/MINI/ISMIP7/{MINI0,MINI1}/{exp}/
└── manual-tests/
    ├── compare_outputs.py                       # Python vs MATLAB comparison (--region filter)
    ├── test_histout.py                          # integration test for --histout
    ├── test_refyear.py                          # integration test for --refyear
    ├── test_basins.py                           # static check: sum-of-basins == whole-sheet area
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

Example: `lithk_GrIS_NORCE_CISM16x-MAR312-p50_m001_CESM2-WACCM_f001_ssp585_E001_2015-2300.nc`

| Field | Meaning | Example |
|-------|---------|---------|
| `{group}` | Submitting institution | `NORCE` |
| `{model}` | Ice sheet model | `CISM16x-MAR312-p50` |
| `{modelid}` | ISM member ID (`mNNN`) | `m001` |
| `{ESM}` | Climate forcing model (CMIP6/7) | `NorESM2-MM` |
| `{forcingid}` | Forcing realization (`fNNN`) | `f001` |
| `{experiment}` | Scenario | `historical`, `ssp126`, `ctrl` |
| `{configid}` | Configuration counter (`[C/E/P]NNN`) | `E001` |
| `{startyear}-{endyear}` | Nominal simulation years | `1960-2014` |

Files are stored under `Models/{region}/{group}/{model}/{exp_group}/` where `{exp_group}` is one of `CORE`, `ESM`, or `PPE`.

**Time encoding:** ST (state) variables carry timestamps at Jan 1 of year N+1; FL (flux) variables carry timestamps at Jul 1 of year N with `time_bounds`. The filename year range always refers to nominal simulation years (ST timestamp year − 1).


## Running the scripts

All scripts accept CLI arguments; the default settings match the NORCE/CISM16x-MAR312-p50/ssp585 (GrIS) and VUW/PISM1/ssp585 (AIS) reference configurations. Resolution is auto-detected from the model grid — no `--res` flag needed.

### Python (primary)

```bash
# Run from repo root
conda run -n nc python3 python/scalars.py --region AIS
conda run -n nc python3 python/scalars.py --region GrIS
conda run -n nc python3 python/scalars.py --region AIS --basins          # add per-basin output
conda run -n nc python3 python/scalars.py --region AIS --basins --no-mm  # basins only, skip whole-sheet
conda run -n nc python3 python/scalars.py --region GrIS --group NORCE --model CISM16x-MAR312-p50 \
  --modelid m001 --esm CESM2-WACCM --forcingid f001 --experiment ssp585 --configid E001 \
  --exp-group ESM
```

Key arguments: `--region {AIS,GrIS}` (required), `--group`, `--model`, `--experiment`, `--modelid`, `--esm`, `--forcingid`, `--configid`, `--exp-group`, `--hist`, `--hist-exp-group`, `--refyear`, `--histout` (default `-1` = all hist), `--basins`, `--no-mm`, `--datapath`, `--modelpath`, `--outpath`.

Output is written to `Output/nc/` and `Output/csv/` at the repository root, regardless of which directory you invoke the script from.

**SLC output** — six files per mask region (three NetCDF + three CSV, one per SLC method), always in two variants: with and without GIC masking:

```
Output/nc/slvaf_{mask}-gic_{...}.nc    # with GIC masking
Output/nc/slvaf_{mask}_{...}.nc        # without GIC masking
Output/nc/slg20_{mask}-gic_{...}.nc
Output/nc/slg20_{mask}_{...}.nc
Output/nc/sla20_{mask}-gic_{...}.nc
Output/nc/sla20_{mask}_{...}.nc
Output/csv/slvaf_{mask}-gic_{...}.csv
...
```

where `{mask}` is `ais`/`gris` (whole ice sheet) or a basin name (`wais`, `ce`, `no`, `r01`, …), and `{y0}-{y1}` is the nominal simulation year range. The `-gic` suffix means glaciers and ice caps (GIC) are excluded from the integral. Each NetCDF contains `time` and the SLC variable (in metres). Each CSV has one data row with metadata columns (`ice_source`, `region`, `group`, `model`, `model_variant`, `scenario`, `GCM`, `forcingid`, `configid`) followed by annual columns `y1850`–`y2300` (NA outside the simulation period). The `region` column in the CSV matches the `{mask}` field in the filename.

**Other scalar output** — one NetCDF per variable per mask region, no GIC masking, plain region name:

```
Output/nc/lim_{mask}_{...}.nc
Output/nc/limnsw_{mask}_{...}.nc
Output/nc/iareagr_{mask}_{...}.nc
Output/nc/iareafl_{mask}_{...}.nc
Output/nc/tendacabf_{mask}_{...}.nc
Output/nc/tendlibmassbfgr_{mask}_{...}.nc
...
```

### MATLAB

```bash
cd matlab
matlab -nodisplay -nosplash -r "region='AIS'; run('scalars.m'); exit"
matlab -nodisplay -nosplash -r "region='GrIS'; run('scalars.m'); exit"
```

Set workspace variables before `run()` to override any default (`group`, `model`, `exp`, `modelid`, `esm`, `forcingid`, `configid`, `exp_group`, `hist`, `hist_exp_group`, `refyear`, `histout`, `flg_mm`, `flg_bm`, `datapath`, `modelpath`, `outpath`). Resolution is auto-detected — no `res` override needed.

### Model density parameters

Each model directory must contain a `params.nc` file with ice (`rhoi`), ocean (`rhow`), and freshwater (`rhof`) densities. Use `tools/set_params.sh` to generate one from `tools/params_template.nc`:

```bash
bash tools/set_params.sh <region> <group> <model> [rhoi] [rhow] [rhof]

# Examples:
bash tools/set_params.sh GrIS NORCE CISM16x-MAR312-p50
bash tools/set_params.sh AIS  VUW   PISM1 910 1028 1000
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

The `python/slc/` package implements three sea-level contribution methods:

| Method | Description |
|--------|-------------|
| `slc_vaf` | Volume Above Flotation — ISMIP6 method, freshwater conversion |
| `slc_G2020` | [Goelzer et al. 2020 (TC)](https://doi.org/10.5194/tc-14-833-2020) — adds potential ocean volume and density corrections |
| `slc_A2020` | [Adhikari et al. 2020 (TC)](https://doi.org/10.5194/tc-14-2819-2020) — absolute reference frame with grounding-line migration |

Three volume diagnostics are also computed (total, grounded, floating ice volume change).

Ocean area normalization uses `oarea = 3.625 × 10¹⁴ m²` (Gregory et al. 2019).

## Testing

### Automatic tests (no external data needed)

The `tests/` directory contains a `pytest` suite that runs on every push via CI.
It requires only `pytest` in addition to the standard conda environment:

```bash
conda run -n nc pytest tests/ -v
```

This runs:
- **`test_slc_units.py`** — unit tests for the `slc/` physics (VAF, G2020, A2020):
  analytic cases with synthetic arrays (identical states → zero SLC, mass loss →
  positive SLC, volume decomposition identity `Vtot = Vgr + Vfl`, etc.).
- **`test_mini_smoke.py`** — integration smoke test for all four MINI combinations
  (MINI0/MINI1 × exp0/expg), using input files committed to `test-data/`.

### Manual integration tests

These require model output under `Data/` and `Models/` (defaults use the VUW/PISM1
AIS reference run):

```bash
cd manual-tests
conda run -n nc python3 test_histout.py --datapath ../Data/AIS --modelpath ../Models/AIS
conda run -n nc python3 test_refyear.py --datapath ../Data/AIS --modelpath ../Models/AIS
conda run -n nc python3 test_basins.py \
    --datapath-ais ../Data/AIS --datapath-gris ../Data/GrIS
```

`test_basins.py` is a fast static check (no model output needed): it loads the basin mask files and verifies that the sum of basin area weights equals the whole-sheet total. Accepts `--region AIS|GrIS` to test a single region.

### Python vs MATLAB comparison

Run each implementation into a separate output tree, then compare:

```bash
conda run -n nc python3 python/scalars.py --region AIS --outpath Output-py
# (MATLAB): outpath='../Output-mat'; run('scalars.m')
cd manual-tests
conda run -n nc python3 compare_outputs.py --region AIS \
    --py-outpath ../Output-py/nc --mat-outpath ../Output-mat/nc
```

The comparison script matches files by their full ISMIP7 stem and checks all three SLC methods. Expected tolerance: < 1 × 10⁻¹⁰ m.

## Converting old-format submissions

Conversion scripts for old-format (ISMIP6, 5-field naming) submissions live in the separate repo `convert-submissions-ismip6-to-ismip7` (sibling directory). See that repo for usage.

Converted files can be validated with the [ISM_SimulationChecker](https://github.com/ismip/ISM_SimulationChecker):

```bash
cd ISM_SimulationChecker
python compliance_checker.py --source-path ../ismip7-scalar-processing/Models/GrIS/NORCE/CISM16x-MAR312-p50/ESM --variable-list ismip7_xyt
```
