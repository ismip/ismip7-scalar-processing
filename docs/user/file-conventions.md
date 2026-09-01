# File and directory conventions

The processing finds its inputs by name. Nothing is inferred from the contents
of a file, so a file in the wrong place or with the wrong name is a file that
does not exist as far as the tools are concerned -- which is deliberate: a run
that quietly processed a neighbouring experiment would be far worse than one
that stopped.

## Model output filenames

Ten underscore-separated fields:

```
{var}_{region}_{group}_{model}_{modelid}_{ESM}_{forcingid}_{experiment}_{configid}_{startyear}-{endyear}.nc
```

```
lithk_GrIS_NORCE_CISM16x-MAR312-p50_m001_CESM2-WACCM_f001_ssp585_E001_2015-2300.nc
```

| Field | Meaning | Example |
|-------|---------|---------|
| `{var}` | Variable name | `lithk` |
| `{region}` | Ice sheet | `AIS`, `GrIS` |
| `{group}` | Submitting institution | `NORCE` |
| `{model}` | Ice sheet model | `CISM16x-MAR312-p50` |
| `{modelid}` | ISM member ID | `m001` |
| `{ESM}` | Climate forcing model | `CESM2-WACCM` |
| `{forcingid}` | Forcing realization | `f001` |
| `{experiment}` | Scenario | `historical`, `ssp126`, `ctrl` |
| `{configid}` | Configuration counter | `C007`, `E001`, `P042` |
| `{startyear}-{endyear}` | Nominal simulation years | `2015-2300` |

Anything after the configid -- the year range, an optional trailing `_c` -- is
ignored when a file is looked up, so the year range does not have to be known
in advance.

```{warning}
**No field may contain an underscore.** The fields are addressed by position,
so a group or model name with an underscore in it shifts every later field
along by one. A `lithk_AIS_MY_GROUP_...` file is read as though `MY` were the
group and `GROUP` the model. Use hyphens.
```

Exactly one file must match a lookup. Two files that differ only in their year
range -- a truncated run left beside the full one, say -- make the directory
ambiguous, and the run stops with a `SKIP:` rather than picking one.

## Directory layout

```
{modelpath}/{group}/{model}/{exp_group}/{configid}/
```

`{exp_group}` is `CORE`, `ESM` or `PPE`, and normally follows from the configid
prefix: `C` → `CORE`, `E` → `ESM`, `P` → `PPE`. `--exp-group` overrides it, for
both input and output.

The default `{modelpath}` is `./Models/{region}` and the default `{datapath}` is
`./Data/{region}`, both relative to wherever you run the command.

## Time encoding

ST (state) variables -- `lithk`, `topg`, `sftgrf`, `sftflf` -- carry timestamps
at **Jan 1 of year N+1** for nominal simulation year N. FL (flux) variables --
`acabf`, `licalvf` and the rest -- carry timestamps at **Jul 1 of year N**, with
time bounds.

The nominal year is what appears in filenames and in the CSV column headers.
So a file named `..._2015-2300.nc` holds ST timestamps from Jan 1 2016 to
Jan 1 2301, and the output written from it is named for 2015-2300 too.

```{note}
`--refyear` is the one place a *timestamp* year is meant rather than a nominal
one: `--refyear 2050` selects the timestep stamped Jan 1 2050, which is nominal
year 2049. See {doc}`running`.
```

## Generic data files

Named for the region and the resolution, which is detected from the model grid
and written as two digits of kilometres (`16` → `16000m`):

| Role | Antarctica | Greenland |
|---|---|---|
| Area factors | `af2_AIS_{res}000m_v1.nc` | `af2_GrIS_{res}000m_v1.nc` |
| Ice sheet mask | `maxmask1_AIS_{res}000m_v0.nc` | `maxmask1_GrIS_{res}000m_v1.nc` |
| Glaciers and ice caps | `iaf2_GIC_AIS_{res}000m_v0.nc` | `iaf2_GIC_GrIS_{res}000m_v0.nc` |
| Basins | `basins_regions_AIS_Rignot_extended_{res}000m_v1.nc` | `basins_GrIS_Mouginot_extended_{res}000m_v1.nc` |

The basin file is only read with `--basins`. All of them are on the ISMIP
Globus server under `Output-Processing`.

## params.nc

`{params-path}/{group}/{model}/params.nc`, holding scalar variables `rhoi`,
`rhow` and `rhof` -- the ice, ocean water and fresh water densities the model
was integrated with. `--params-path` defaults to `--modelpath`; set it
separately when the model tree is read-only.

Write one with `ismip7-scalars-set-params`:

```bash
ismip7-scalars-set-params --region AIS --group VUW --model PISM1 \
    --rhoi 910 --rhow 1028 --rhof 1000 --modelpath ./Models/AIS
```

The file may also carry an `oarea`, but the processing does not read it: every
submission is normalised by the same ocean area, 3.625 × 10¹⁴ m² (Gregory et
al., 2019), so that the sea-level contributions are comparable across models.
