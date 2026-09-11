# Running the processing

```bash
ismip7-scalars --region AIS [options]
```

Only `--region` is required. Everything else defaults to the synthetic
ISMIP7/SYNTH1 test case from the
[ISM_SimulationChecker](https://github.com/ismip/ISM_SimulationChecker), so a
real run sets at least the options in the first table.

## Identifying the run

| Option | Meaning | Example |
|---|---|---|
| `--region` | ice sheet; required | AIS, GrIS |
| `--group` | submitting institution | VUW |
| `--model` | ice sheet model | PISM1 |
| `--modelid` | ISM member ID | m001 |
| `--esm` | climate forcing model | CESM2-WACCM |
| `--forcingid` | forcing realization | f001 |
| `--experiment` | scenario | ssp585 |
| `--configid` | configuration counter | C007 |
| `--exp-group` | CORE, ESM or PPE; normally taken from the configid's first letter | CORE |

Together these name exactly one set of files, as described in
{doc}`file-conventions`. Resolution is not among them: it is read from the
spacing of the model grid.

## The historical reference

Sea-level contribution is a change, so every series needs a state to measure
from. By default that is the last timestep of the historical experiment.

| Option | Meaning | Default |
|---|---|---|
| `--hist` | historical experiment name | historical |
| `--hist-configid` | its configid | same as `--configid` |
| `--hist-exp-group` | its experiment group | same as `--exp-group` |
| `--refyear` | use this year as the reference instead | last historical step |

A CORE projection normally needs `--hist-configid`, because C001 is the
shared historical run for the C003, C005 and C007 projections:

```bash
ismip7-scalars --region AIS --configid C007 --experiment ssp585 \
    --hist historical --hist-configid C001
```

To process the historical run on its own, give it as the experiment too
(`--experiment historical`). It is then its own reference and nothing is
prepended.

```{note}
`--refyear` takes a **timestamp** year, which for a state variable is one more
than the nominal year: `--refyear 2050` selects the step stamped 2050-01-01,
the end of nominal year 2049. The year is looked for in the historical run
first and then in the projection. If it is in neither, the run skips and
says so.
```

## How much history to write out

The reference always comes from the historical run. `--histout` controls how
much of that run is prepended to the output:

| `--histout` | Output starts at |
|---|---|
| -1 | the first historical step (the default) |
| 0 | the first projection step |
| 1 | the last historical step, so the series starts at zero |
| N | the last N historical steps, or all of them with a warning if there are fewer |

Prepending history never changes the projection values, only what comes before
them and the year range in the filename.

## Which masks to integrate over

| Option | Masks |
|---|---|
| (default) | the whole ice sheet |
| `--basins` | the whole ice sheet **and** each basin and region |
| `--basins --no-mm` | each basin and region only |

For Antarctica the basins are the three IMBIE3 regions (wais, eais, pina) and
the 18 IMBIE3 basins (r01 to r18). For Greenland they are the seven Mouginot
basins (no, ne, ce, se, sw, cw, nw). Each set partitions the grid, so the
per-basin values sum to the whole-sheet value.

`--no-mm` on its own is refused: it would leave nothing to compute. Turning
`--basins` on also adds the mask name to the whole-sheet filenames; see
{doc}`output`.

## Paths

| Option | Points at | Default |
|---|---|---|
| `--modelpath` | the ice sheet directory of the model tree, which holds a folder per group | Models/AIS or Models/GrIS |
| `--datapath` | the area factors and masks | Data/AIS or Data/GrIS |
| `--params-path` | the ice sheet directory of a tree holding params.nc files | same as `--modelpath` |
| `--outpath` | where the output goes | Output |

Defaults are relative to the directory you run the command in. The model path
is *not* your model's own directory; see {doc}`file-conventions`. Use
`--params-path` when the model tree is read-only.

## Other

`--verbose` prints field shapes and the computed series as it goes.
`--version` prints the version and exits.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | the run finished |
| 2 | a required input was missing; one SKIP line says which |
| anything else | a bug; please report it |

Exit 2 lets {doc}`ensemble` log a unit it could not process and carry on.
Some inputs are only needed for part of the output: without sftgrf and sftflf
the state scalars are skipped and everything else is still written, and each
flux variable is skipped on its own if its file is absent. Those are
warnings, and the run still exits 0.
