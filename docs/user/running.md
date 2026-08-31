# Running the processing

```bash
ismip7-scalars --region {AIS,GrIS} [options]
```

`--region` is the only required option. Everything else defaults to the
ISMIP7/SYNTH1 synthetic test case produced by the
[ISM_SimulationChecker](https://github.com/ismip/ISM_SimulationChecker):
`--group ISMIP7 --model SYNTH1 --modelid m001 --esm CESM2-WACCM --forcingid
f001 --configid C001 --hist historical`, with `--experiment ssp585` for
Antarctica and `--experiment ctrl` for Greenland.

## Identifying the run

| Option | Meaning |
|---|---|
| `--region {AIS,GrIS}` | Ice sheet. Required. |
| `--group` | Submitting institution |
| `--model` | Ice sheet model name |
| `--modelid`, `--ism-member-id` | ISM member ID (`mNNN`) |
| `--esm` | Climate forcing model |
| `--forcingid` | Forcing realization (`fNNN`) |
| `--experiment` | Scenario, e.g. `ssp585` |
| `--configid` | Configuration counter (`[CEP]NNN`) |
| `--exp-group` | `CORE`, `ESM` or `PPE`; defaults from the configid prefix |

Together these pick exactly one set of files, as described in
{doc}`file-conventions`. The resolution is not among them: it is detected from
the spacing of the model's `x` axis.

## The historical reference

Sea-level contribution is a *change*, so every series needs a state to measure
against. By default that is the last timestep of the historical experiment.

| Option | Meaning |
|---|---|
| `--hist` | Historical experiment name (default: `historical`) |
| `--hist-configid` | Its configid (default: same as `--configid`) |
| `--hist-exp-group` | Its directory level (default: same as `--exp-group`) |
| `--refyear` | Use this year as the reference instead of the last historical timestep |

`--hist-configid` is what a CORE run normally needs: C001 is the shared
historical reference for the C003, C005 and C007 projections, so

```bash
ismip7-scalars --region AIS --configid C007 --experiment ssp585 \
    --hist historical --hist-configid C001
```

Setting `--experiment` equal to `--hist` processes the historical run on its
own. It is then its own reference, and nothing is prepended.

```{note}
`--refyear` names a **timestamp** year, which for a state variable is one more
than the nominal year: `--refyear 2050` selects the timestep stamped Jan 1
2050, the last one of nominal year 2049. The year is looked for in the
historical run first and then in the projection; if it is in neither, the run
skips with an explanation.
```

## How much history to write out

`--histout N`

The reference state comes from the historical run whether or not any of that
run appears in the output. `--histout` controls how much of it is prepended:

| Value | Effect |
|---|---|
| `-1` | All historical timesteps (the default) |
| `0` | None; the output covers the projection only |
| `1` | The last historical timestep only, so the series starts at zero |
| `N` | The last `N`, clamped to the run's length with a warning |

Prepending history never changes the projection values it precedes -- only what
comes before them, and the year range in the filename.

## Which masks to integrate over

| Option | Effect |
|---|---|
| *(default)* | The whole ice sheet |
| `--basins` | The IMBIE3 basins and regions **as well as** the whole ice sheet |
| `--basins --no-mm` | The basins only |

For Antarctica `--basins` adds the three IMBIE3 regions (`wais`, `eais`,
`pina`) and the 18 IMBIE3 basins (`r01`…`r18`); for Greenland it adds the seven
Mouginot basins (`no`, `ne`, `ce`, `se`, `sw`, `cw`, `nw`). Each partitions the
grid, so the per-basin values sum to the whole-sheet value.

`--no-mm` on its own is refused: it would leave nothing to compute.

Turning `--basins` on also changes the whole-sheet filenames, which gain the
mask name as a second field -- see {doc}`output`.

## Paths

| Option | Default |
|---|---|
| `--datapath` | `./Data/{region}` |
| `--modelpath` | `./Models/{region}` |
| `--params-path` | same as `--modelpath` |
| `--outpath` | `./Output` |

All four are relative to the directory you run the command in. Use
`--params-path` when the model tree is read-only -- a submissions tree on NIRD,
say -- and the densities live somewhere you can write.

## Other

`--verbose` prints field shapes and the computed series as it goes.
`--version` prints the version and exits.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | The run finished |
| 2 | A required input was missing; one `SKIP:` line says which |
| other | A genuine failure |

Exit 2 exists so that {doc}`ensemble` can log a unit it could not process and
carry on to the next one. Some inputs are only needed for part of the output:
missing `sftgrf`/`sftflf` skips the state scalars and still writes everything
else, and each flux variable is skipped on its own if its input file is absent.
Those are warnings, and the run still exits 0.
