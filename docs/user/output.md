# The output files

Two trees under `--outpath` (`./Output` by default):

```
Output/
├── nc/{region}/{group}/{model}/{exp_group}/{configid}/    # mirrors the model tree
└── csv/                                                   # flat
```

The NetCDF tree mirrors the model tree so that a submission's output sits where
its input does; the CSVs are flat because they are meant to be concatenated
into one community-wide table.

## Filenames

```
{varname}[-gic]_[{mask}_]{region}_{group}_{model}_{modelid}_{ESM}_{forcingid}_{experiment}_{configid}_{y0}-{y1}
```

Everything from `{region}` on is the same for every file of one run, and
`{y0}-{y1}` is the nominal year range actually written -- which depends on
`--histout`.

The `{mask}` field is where it gets subtle:

| Mode | Whole sheet | A basin |
|---|---|---|
| default | `slvaf_AIS_...` | *(not written)* |
| `--basins` | `slvaf_ais_AIS_...` | `slvaf_r01_AIS_...` |
| `--basins --no-mm` | *(not written)* | `slvaf_r01_AIS_...` |

The whole-sheet file omits the mask name in default mode, so that its name
matches the structure of the model files it came from. Ask for basins and it
gains one -- `ais` or `gris` -- so that every file in the directory is named the
same way.

The `-gic` suffix marks the variant with glaciers and ice caps excluded from
the integral. It attaches to the variable, not the mask: `slvaf-gic_r01_...`.

## Sea-level contribution

Three variables, one file each, in metres:

| Variable | Method |
|---|---|
| `slvaf` | Volume above flotation |
| `slg20` | Goelzer et al. (2020) |
| `sla20` | Adhikari et al. (2020) |

described in {doc}`slc-methods`. Each is written twice, once with glaciers and
ice caps masked out (`-gic`) and once without, and in two formats:

| | NetCDF | CSV |
|---|---|---|
| without GIC masking | ✓ | ✓ |
| with GIC masking (`-gic`) | | ✓ |

A positive value means sea-level rise. Every series is zero at the reference
timestep by construction.

### The CSV form

One header row and one data row. Nine metadata columns:

`ice_source`
: the region, `AIS` or `GrIS`

`region`
: the mask's display name -- `ais`/`gris` or a basin name -- with `-gic`
  appended for the GIC-masked variant, so that the two variants stay
  distinguishable once rows from many runs are concatenated

`group`, `model`, `model_variant`, `scenario`, `GCM`, `forcingid`, `configid`
: the identifying fields of the run, `model_variant` being the ISM member ID
  and `scenario` the experiment

then one column per **nominal** year from `y1850` to `y2300`. Years the run
does not cover are `NA`; a run reaching outside that window has those years
dropped, with a warning naming them.

## State scalars

One NetCDF file each, no GIC masking:

| Variable | Long name | Units |
|---|---|---|
| `lim` | `land_ice_mass` | kg |
| `limnsw` | `land_ice_mass_not_displacing_sea_water` | kg |
| `iareagr` | `grounded_ice_sheet_area` | m² |
| `iareafl` | `floating_ice_shelf_area` | m² |

These need `sftgrf` and `sftflf` in the model output. Without them the whole
block is skipped with a warning and the rest of the run still succeeds.

## Flux scalars

The gridded mass fluxes, integrated over the mask. One NetCDF file each, no GIC
masking, all in kg s⁻¹:

| Output | From | Long name |
|---|---|---|
| `tendacabf` | `acabf` | `tendency_of_land_ice_mass_due_to_surface_mass_balance` |
| `tendlibmassbfgr` | `libmassbfgr` | `..._due_to_basal_mass_balance_grounded` |
| `tendlibmassbffl` | `libmassbffl` | `..._due_to_basal_mass_balance_floating` |
| `tendlicalvf` | `licalvf` | `..._due_to_calving` |
| `tendlifmassbf` | `lifmassbf` | `..._due_to_ice_front_melting` |
| `tendligroundf` | `ligroundf` | `..._due_to_grounding_line_migration` |

Each is skipped on its own if its input file is absent, and the names of the
ones that were skipped are listed at the end of the run.

Flux files sit on their own time axis -- timestamps at Jul 1 of year N, against
Jan 1 of year N+1 for the state variables -- so their `{y0}-{y1}` may differ
from that of the other output of the same run.

## Every file

`time` plus one variable, both `f8`, on an unlimited `time` dimension. The time
coordinate carries the `units`, `calendar` and `long_name` of the model file it
came from, and the data variable its own `long_name` and `units`. A
`description` global attribute names the processing.
