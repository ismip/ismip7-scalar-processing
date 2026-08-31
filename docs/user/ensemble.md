# Processing a whole ensemble

```bash
ismip7-scalars-ensemble --region GrIS --modelpath <submissions root> [options]
```

`ismip7-scalars-ensemble` walks a submissions root, works out for each
`{group}/{model}/{exp_group}/{configid}` directory whether it is a processable
unit and which historical run it pairs with, and runs `ismip7-scalars` once per
unit. Each unit runs in a subprocess of its own, so one bad submission cannot
take the batch down with it.

Point `--modelpath` at the region directory of the submissions tree -- note the
doubled region in the NIRD path:

```bash
ismip7-scalars-ensemble --region GrIS \
  --modelpath /nird/datalake/NS5011K/ISMIP/ISMIP7/GrIS/ISMIP7_output/ISMIP7_submissions/GrIS \
  --datapath /nird/datalake/NS5011K/ISMIP/ISMIP7/Output-Processing/Data/GrIS \
  --params-path /nird/datalake/NS5011K/ISMIP/ISMIP7/Output-Processing/Models/GrIS \
  --dry-run
```

`--dry-run` prints the command planned for each unit and runs none of them.
Start there.

## What counts as a unit

A directory four levels below the root, whose third and fourth levels are
`{CORE|ESM|PPE}` and `{[CEP]NNN}`, holding a `lithk` file whose `region`,
`group`, `model` and `configid` fields match the directory it is in.

Everything else is logged and skipped: ad-hoc directories (`old_CORE`,
`CORE_old`), filenames that break the ten-field convention, a `lithk` file that
says it belongs to a different configid than the directory it sits in. The
point is that a mislabelled file is never silently processed as though it were
something else.

## How projections are paired with a historical run

The bundled CORE experiment table (`ISMIP7_experiments_CORE.csv`) gives each
configid its scenario and forcing ESM. A projection pairs with the historical
run driven by the same ESM -- CESM with `C001`, MRI with `C002`. Experiments
whose scenario is `historical` or `ctrl` are their own reference and pair with
themselves.

For a configid the table does not list -- a future ESM or PPE experiment -- the
driver falls back on the numbering convention, pairing an even configid with the
odd one below it. Where even that gives no candidate the unit is skipped with a
reason rather than paired against itself, because a projection measured against
its own last timestep would produce a plausible-looking series that is entirely
wrong. Pair those by hand with `ismip7-scalars --hist-configid`.

## Options

| Option | Meaning |
|---|---|
| `--region {AIS,GrIS}` | Required |
| `--modelpath` | Submissions root. Required |
| `--dry-run` | Print the planned commands, run nothing |
| `--exp-group` | Only this experiment group |
| `--groups`, `--models`, `--configids` | Comma-separated filters |
| `--datapath`, `--params-path`, `--outpath`, `--histout`, `--basins` | Passed through to each unit |
| `--core-csv` | Use a different experiment table |
| `--python` | Interpreter to run each unit with |
| `--log-dir` | Where the logs go (default `./Output/logs`) |

## Logs

One log per unit, plus a run summary naming every unit and what happened to it:

```
ISMIP7 ensemble run -- GrIS -- 20260301T142530
modelpath: /nird/.../ISMIP7_submissions/GrIS
units: 24   ok: 19   skipped: 4   failed: 1

  NORCE/CISM16x-MAR312-p50/CORE/C001                       OK   [GrIS_NORCE_..._C001.log]
  NORCE/CISM16x-MAR312-p50/CORE/C003                       OK   [GrIS_NORCE_..._C003.log]
  VUW/PISM1/CORE/C005                                      SKIP: ... -- missing topg for exp in ...
  ...
```

A unit that skipped itself over a missing input reports the reason it gave,
lifted out of its own log, rather than a bare exit code.

The driver itself exits 0 unless it hits a driver-level error: a unit that could
not be processed is a line in the summary, not a failure of the batch. Read the
summary.
