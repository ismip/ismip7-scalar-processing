# The MATLAB implementation

`matlab/scalars.m` computes the same scalars as `ismip7-scalars`, from the same
inputs, into the same output layout. It exists because part of the community
works in MATLAB, and because two independent implementations agreeing to
machine precision is a stronger statement about the processing than either one
passing its own tests.

Neither the conda-forge package nor the pip install includes it; run it from
the checkout.

```bash
cd matlab
matlab -nodisplay -nosplash -r "region='AIS'; run('scalars.m'); exit"
matlab -nodisplay -nosplash -r "region='GrIS'; run('scalars.m'); exit"
```

Set workspace variables before `run()` to override any default: `group`,
`model`, `exp`, `modelid`, `esm`, `forcingid`, `configid`, `exp_group`, `hist`,
`hist_exp_group`, `hist_configid`, `refyear`, `histout`, `flg_mm`, `flg_bm`,
`flg_base`, `datapath`, `modelpath`, `params_path`, `outpath`. They correspond
one for one with the command-line options in {doc}`../user/running`; `flg_bm`
is `--basins`, `flg_mm=false` is `--no-mm` and `flg_base=true` is
`--base-variants`. Resolution is auto-detected the same
way. As in Python, `refyear` defaults to the last hist step, or 2015 for a
self-paired ocx run.

## Where the two differ

**Missing input.** MATLAB raises; Python prints one `SKIP:` line and exits 2.
The Python behaviour exists for the batch driver, which has no MATLAB
counterpart.

**Optional variables.** Python treats `sftgrf`/`sftflf` and the flux variables
as optional, skipping the output that needs them, and with `--base-variants`
skips the base variants when `base` is missing. MATLAB requires them all.

**Variable metadata.** Python reads each scalar's `standard_name`, `units` and
`long_name` from the data request in the installed `isschecker` package (see
{doc}`../user/data-sources`). MATLAB cannot, so the same values are restated in
`st_vars` and `fl_scalar_specs` near the end of `scalars.m`. When the data
request changes one of them, change those tables too — `compare_outputs.py`
compares values, not attributes, so this is the one divergence it would not
catch.

**CSV output.** Both write the same run-level `sl_<run-fields>_<mask>.csv`:
one header row, then one row per SLC method, GIC variant and selected mask,
with the same ten metadata columns and the same `NA` padding outside the run.
`compare_outputs.py` compares NetCDF only, so the CSV is checked by
`manual-tests/mvsp/compare_csv.py` instead.

**GIC-masked NetCDF.** MATLAB always writes the GIC-masked SLC NetCDF
(`slvaf-gic`, `slg20-gic`, `sla20-gic`); Python writes it only when NetCDF is
explicitly enabled. This is deliberate -- see {doc}`../user/output` -- and
does not affect the CSV, which carries the `-gic` rows in both. Pass
`--netcdf` to Python for a like-for-like NetCDF comparison.

Everything that both compute, they compute identically.

## Comparing them

Run each into its own output tree, then compare:

```bash
ismip7-scalars --region AIS --outpath Output-py
# in MATLAB:  outpath='../Output-mat'; region='AIS'; run('scalars.m')

cd manual-tests
python compare_outputs.py --region AIS \
    --py-outpath ../Output-py/nc --mat-outpath ../Output-mat/nc
```

`compare_outputs.py` walks the Python output tree recursively and matches each
file against the MATLAB file at the same relative path, falling back to a
recursive search by basename. It covers every output variable -- the three SLC
methods and their base variants, the four state scalars and the six flux
scalars -- checking SLC against an absolute tolerance of 1 × 10⁻⁶ m and
everything else against a relative
tolerance of 1 × 10⁻⁶, loose enough for the single precision (f4) the outputs
are stored in. It also checks each file's `time_bounds` -- present in both or
neither, on a `(time, nv)` dimension with the vertex dimension last as CF
requires, and equal within tolerance -- and the five checker-required global
attributes.

The consolidated CSV is compared separately, by
`manual-tests/mvsp/compare_csv.py`; `manual-tests/mvsp/` also holds the MATLAB
drivers for the three mask combinations. See the README there.

The outputs are f4, so differences below f4 resolution (about 10⁻⁷ relative)
round away. In the latest full check (branch `hgoelzer/pass-meta`, C001 and
C003 on NIRD) every variable, the time bounds and the global attributes
matched exactly, with no differences at all. Both implementations compute in
double precision and round once at write time, so a genuine disagreement
would still show up at f4 resolution. Earlier checks against
`Submission_Tests_v1` AIS VUW/PISM1 and GrIS NORCE/CISM16x-MAR312-p50 saw
only the cumulative SLC methods `slvaf` and `slg20` differ, by a few 10⁻¹² m
-- differences of two large volume sums, sensitive to the last bits of the
input fields; with f4 output those now round away too.

This comparison cannot run in CI -- there is no MATLAB there, and no submission
tree -- so it is a manual step. Run it when you change anything that touches
the numbers, and change both implementations together.
