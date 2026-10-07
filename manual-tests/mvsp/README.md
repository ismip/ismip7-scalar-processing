# MATLAB-versus-Python SLC CSV comparison

`compare_outputs.py` in the parent directory compares NetCDF only, so the
consolidated run-level CSV that both implementations write is checked here
instead. This directory holds the drivers that produce the two CSV trees and
the comparator that diffs them.

## What is compared

Both implementations write `sl_<run-fields>_<mask>.csv`: one header row, then
one row per SLC method, GIC variant and selected mask, with the same ten
metadata columns and the same `NA` padding outside the run. The comparator
checks the header, the set of `(region, scalar)` rows, and every value.

The mask combinations and the flags that select them:

| CSV suffix | Python | MATLAB |
|---|---|---|
| `_mm` | (default) | `flg_mm=true, flg_bm=false` |
| `_basins` | `--basins --no-mm` | `flg_mm=false, flg_bm=true` |
| `_mm-basins` | `--basins` | `flg_mm=true, flg_bm=true` |

Note that Python's `--basins` *adds* basins to the whole-ice-sheet integral;
`--no-mm` is what drops the integral, matching MATLAB's `flg_mm=false`.

## Tolerance

MATLAB writes the values with `%.10g` (ten significant digits) while Python
writes full precision, so the CSV agreement is limited by that rounding to
about `5e-10` relative. The comparator therefore passes a value if it is
within `--abs-tol` (default `1e-12` m) **or** `--rel-tol` (default `1e-9`),
and reports both the maximum absolute and the maximum relative difference.
The relative figure is large only where the value itself is near zero, which
is why the absolute floor exists.

The underlying agreement is much tighter: the NetCDF comparison shows about
`1e-13` relative.

## Running it

The drivers are written for NIRD, where the submission tree and MATLAB live.
Set `root` in the driver to the directory holding `Data/`, `Models/` and the
checkout, then run each side into its own output tree.

```bash
# Python
ismip7-scalars --region AIS --group NORCE --model CISM \
    --experiment ssp370 --configid C003 --hist-configid C001 \
    --modelpath "$root/Models/AIS" --datapath "$root/Data/AIS" \
    --outpath "$root/Scalars_mvsp/py"

# MATLAB
matlab -nodisplay -nosplash -nojvm -singleCompThread \
    -r "run('$root/ismip7-scalar-processing/manual-tests/mvsp/run_mvsp.m'); exit"
```

Then compare:

```bash
python compare_csv.py \
    --py-csv  "$root/Scalars_mvsp/py/csv" \
    --mat-csv "$root/Scalars_mvsp/mat/csv"
```

`run_mvsp.m` is the whole-ice-sheet case, `run_mvsp_basins.m` the basins-only
case and `run_mvsp_mmbasins.m` the combined case. Each writes to its own
`Scalars_mvsp/mat*` tree so the three can be compared independently.

## The `-gic` NetCDF asymmetry

MATLAB always writes the GIC-masked SLC NetCDF (`slvaf-gic`, `slg20-gic`,
`sla20-gic`); Python writes it only when NetCDF is explicitly enabled
(`FLG_SLC_GIC_NC = False`, `FLG_SLC_GIC_CSV = True` in `scalars.py`). This is
deliberate and documented in `docs/user/output.md`; pass `--netcdf` to Python
for a like-for-like NetCDF comparison. The CSV is unaffected -- both write the
`-gic` rows by default.

## MATLAB driver notes

Every setting must be a single-quoted char row: `scalars.m` concatenates them
with `[]`, and a double-quoted `string` array makes `dir()` fail with "Name
must be a text scalar". Pass an absolute path to `run()`, or MATLAB changes
directory to a nonexistent `/tmp/matlab`.
