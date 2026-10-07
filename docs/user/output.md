# The output files

Two trees under the output path (Output by default):

```
Output/
├── nc/AIS/VUW/PISM1/CORE/C007/     one NetCDF file per scalar; mirrors the model tree
└── csv/                            one CSV per run with all enabled SLC rows; flat
```

The NetCDF tree mirrors the model tree so a submission's output sits where its
input does. The CSVs are flat because they are meant to be joined into one
community-wide table.

## Filenames

A NetCDF file's name is the scalar, then the same nine fields as the model
files it came from, then the years actually written:

```
slvaf_AIS_VUW_PISM1_m001_CESM2-WACCM_f001_ssp585_C007_1850-2300.nc
```

The year range depends on `--histout`; here all of the historical run was
prepended.

The SLC CSV is named `sl_` followed by those run fields and years, then the
mask selection it holds. It contains all enabled SLC methods, GIC variants, and
selected masks for that run:

| Mask selection | CSV name |
|---|---|
| default | sl_AIS_..._mm.csv |
| `--basins` | sl_AIS_..._mm-basins.csv |
| `--basins --no-mm` | sl_AIS_..._basins.csv |

The selection is part of the name so that two runs of the same experiment with
different masks do not overwrite each other.

With `--basins` the mask name is added after the scalar in NetCDF filenames,
and the whole-sheet file gains one too so that every file in the directory is
named the same way:

| | Whole sheet | Basin r01 |
|---|---|---|
| default | slvaf_AIS_... | not written |
| `--basins` | slvaf_ais_AIS_... | slvaf_r01_AIS_... |
| `--basins --no-mm` | not written | slvaf_r01_AIS_... |

A -gic suffix on the scalar marks the variant with glaciers and ice caps left
out of the integral: slvaf-gic_r01_AIS_... .

## Sea-level contribution

Three scalars, in metres of global mean sea level, positive for sea-level rise.
Every series is zero at the reference timestep.

| Scalar | Method |
|---|---|
| slvaf | volume above flotation |
| slg20 | Goelzer et al. (2020) |
| sla20 | Adhikari et al. (2020) |

{doc}`slc-methods` describes them. Each is computed twice, with and without
glaciers and ice caps, and written like this:

| | NetCDF | CSV |
|---|---|---|
| including glaciers and ice caps | yes | yes |
| excluding them (-gic) | | yes |

`--csv` and `--no-csv` override CSV output for both SLC variants. `--netcdf`
and `--no-netcdf` override NetCDF output for all scalar classes; explicitly
enabling NetCDF also enables the GIC-masked SLC NetCDF. When omitted, each
format keeps the defaults shown above and in the state/flux sections below.
Disabling NetCDF skips the state and flux scalars entirely, because they have
no CSV form.

### The CSV form

One header row and one data row per SLC method, GIC mode, and selected mask.
The first ten columns identify the run and scalar:

| Column | Holds |
|---|---|
| ice_source | AIS or GrIS |
| region | the geographic mask name (ais, gris or a basin) |
| scalar | `slvaf`, `slg20`, or `sla20`; `-gic` marks the GIC-excluded variant |
| group, model, model_variant, scenario, GCM, forcingid, configid | the run's fields; model_variant is the ISM member ID, scenario the experiment |

Then one column per nominal year, y1850 to y2300. Years the run does not cover
are NA. A run that reaches outside that window has those years dropped, with a
warning naming them. With AIS `--basins`, the CSV has 132 data rows when the
whole-sheet mask is included, or 126 with `--no-mm`.

## State scalars

One NetCDF file each, integrated over the mask:

| Scalar | What it is | Units |
|---|---|---|
| lim | ice mass | kg |
| limnsw | ice mass not displacing sea water | kg |
| iareagr | grounded ice area | m² |
| iareafl | floating ice area | m² |

These need sftgrf and sftflf in the model output. Without them the four are
skipped with a warning and the rest of the run still succeeds.

## Flux scalars

The gridded mass fluxes integrated over the mask, one NetCDF file each, all
in kg/s:

| Scalar | From | Flux |
|---|---|---|
| tendacabf | acabf | surface mass balance |
| tendlibmassbfgr | libmassbfgr | basal mass balance, grounded |
| tendlibmassbffl | libmassbffl | basal mass balance, floating |
| tendlicalvf | licalvf | calving |
| tendlifmassbf | lifmassbf | ice front melting |
| tendligroundf | ligroundf | grounding line migration |

Each is skipped on its own if its input file is absent, and the run lists the
ones it skipped at the end. Flux files have their own time axis (Jul 1 of each
year rather than Jan 1 of the next), so their year range can differ from the
other files of the same run.

## Attributes

Every NetCDF file holds a time coordinate and one variable, both double
precision, on an unlimited time dimension. The time coordinate copies its
units, calendar and long name from the model file. The state and flux scalars
carry the long name, units and standard name given in the ISMIP7 data request,
read from the isschecker package (see {doc}`data-sources`); the data request
gives no standard name for tendlifmassbf and tendligroundf, so those two carry
none. The sea-level scalars are this package's own and have no standard name
either.
