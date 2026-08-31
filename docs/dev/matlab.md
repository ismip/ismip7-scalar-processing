# The MATLAB implementation

`matlab/scalars.m` computes the same scalars as `ismip7-scalars`, from the same
inputs, into the same output layout. It exists because part of the community
works in MATLAB, and because two independent implementations agreeing to
machine precision is a stronger statement about the processing than either one
passing its own tests.

It is not installed by conda-forge; run it from a checkout.

```bash
cd matlab
matlab -nodisplay -nosplash -r "region='AIS'; run('scalars.m'); exit"
matlab -nodisplay -nosplash -r "region='GrIS'; run('scalars.m'); exit"
```

Set workspace variables before `run()` to override any default: `group`,
`model`, `exp`, `modelid`, `esm`, `forcingid`, `configid`, `exp_group`, `hist`,
`hist_exp_group`, `hist_configid`, `refyear`, `histout`, `flg_mm`, `flg_bm`,
`datapath`, `modelpath`, `params_path`, `outpath`. They correspond one for one
with the command-line options in {doc}`../user/running`; `flg_bm` is
`--basins` and `flg_mm=false` is `--no-mm`. Resolution is auto-detected the same
way.

## Where the two differ

**Missing input.** MATLAB raises; Python prints one `SKIP:` line and exits 2.
The Python behaviour exists for the batch driver, which has no MATLAB
counterpart.

**Optional variables.** Python treats `sftgrf`/`sftflf` and the flux variables
as optional, skipping the output that needs them; MATLAB requires them.

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
methods, the four state scalars and the six flux scalars -- checking SLC against
an absolute tolerance of 1 × 10⁻¹⁰ m and everything else against a relative
tolerance of 1 × 10⁻¹⁰.

Observed differences are at machine epsilon, around 10⁻¹⁵ relative, for every
variable; most recently against `Submission_Tests_v1` AIS VUW/PISM1 and GrIS
NORCE/CISM16x-MAR312-p50 on NIRD.

This comparison cannot run in CI -- there is no MATLAB there, and no submission
tree -- so it is a manual step. Run it when you change anything that touches
the numbers, and change both implementations together.
