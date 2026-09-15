# Processing a whole ensemble

`ismip7-scalars-ensemble` walks a submission tree, finds every experiment it
can process, pairs each projection with its historical run, and runs
`ismip7-scalars` once per experiment. Each run is a separate process, so one
bad submission cannot take the batch down.

Point `--modelpath` at the ice sheet directory of the submission tree, the one
holding a folder per group. On NIRD that is the *second* GrIS in the path:

```bash
ismip7-scalars-ensemble --region GrIS \
  --modelpath /nird/datalake/NS5011K/ISMIP/ISMIP7/GrIS/ISMIP7_output/ISMIP7_submissions/GrIS \
  --datapath /nird/datalake/NS5011K/ISMIP/ISMIP7/Output-Processing/Data/GrIS \
  --params-path /nird/datalake/NS5011K/ISMIP/ISMIP7/Output-Processing/Models/GrIS \
  --dry-run
```

`--dry-run` prints the command planned for each experiment and runs none of
them. Start there.

## What gets processed

An experiment directory four levels below the model path, for example
NORCE/CISM16x-MAR312-p50/CORE/C001, whose lithk file names the same region,
group, model and configid as the directory it sits in.

Anything else is logged and skipped: ad-hoc directories like old_CORE,
filenames that break the ten-field convention, a file that says it belongs to
a different configid than its directory. A mislabelled file is never
processed as though it were something else.

## How projections are paired with a historical run

The CORE experiment table bundled with the package gives each configid its
scenario and forcing ESM. A projection is paired with the historical run
driven by the same ESM: CESM projections with C001, MRI projections with
C002. Historical and ctrl experiments are their own reference.

For a configid the table does not know, such as a future ESM or PPE
experiment, the driver pairs an even configid with the odd one below it. If
that gives nothing, the experiment is skipped with a reason rather than
measured against itself, which would produce a plausible-looking series that
is wrong. Pair those by hand with `ismip7-scalars --hist-configid`.

## Options

| Option | Meaning |
|---|---|
| `--region` | AIS or GrIS; required |
| `--modelpath` | ice sheet directory of the submission tree; required |
| `--dry-run` | print the planned commands, run nothing |
| `--exp-group` | only this experiment group |
| `--groups`, `--models`, `--configids` | comma-separated filters |
| `--datapath`, `--params-path`, `--outpath`, `--histout`, `--basins` | passed through to each run |
| `--core-csv` | use a different experiment table |
| `--python` | interpreter to run each experiment with |
| `--log-dir` | where the logs go; default Output/logs |

## Logs

One log per experiment, plus a summary naming every experiment and what
happened to it:

```
ISMIP7 ensemble run -- GrIS -- 20260301T142530
modelpath: /nird/.../ISMIP7_submissions/GrIS
units: 24   ok: 19   skipped: 4   failed: 1

  NORCE/CISM16x-MAR312-p50/CORE/C001                       OK   [GrIS_NORCE_..._C001.log]
  NORCE/CISM16x-MAR312-p50/CORE/C003                       OK   [GrIS_NORCE_..._C003.log]
  VUW/PISM1/CORE/C005                                      SKIP: ... -- missing topg for exp in ...
  ...
```

The driver exits 0 unless something went wrong with the driver itself. An
experiment that could not be processed is a line in the summary, not a failure
of the batch, so read the summary.
