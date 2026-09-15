# File and directory conventions

The tools find their inputs by name and never look inside a file to decide
what it is. A file with the wrong name or in the wrong place is invisible to
them. That is on purpose: stopping is better than quietly processing a
neighbouring experiment.

## Directory layout

The same layout as an ISMIP7 submission. For the VUW group's PISM1 model:

```
Models/AIS/                    <-- --modelpath
└── VUW/                       <-- group
    └── PISM1/                 <-- model
        ├── params.nc
        ├── CORE/              <-- experiment group
        │   ├── C001/          <-- configid
        │   └── C007/
        └── ESM/
            └── E001/
```

The model path is the ice sheet directory, one level above the groups. The
tools add the group, model, experiment group and configid to it. Passing your
model's own directory, Models/AIS/VUW/PISM1, doubles them up: the tools then
look under Models/AIS/VUW/PISM1/VUW/PISM1.

The experiment group is CORE, ESM or PPE and follows from the first letter of
the configid. `--exp-group` overrides that, for both input and output.

The default model path is Models/AIS or Models/GrIS and the default data path
is Data/AIS or Data/GrIS, relative to wherever you run the command.

## Model output filenames

Ten fields separated by underscores. For example:

```
lithk_GrIS_NORCE_CISM16x-MAR312-p50_m001_CESM2-WACCM_f001_ssp585_E001_2015-2300.nc
```

| Field | Example | Meaning |
|---|---|---|
| variable | lithk | |
| region | GrIS | AIS or GrIS |
| group | NORCE | submitting institution |
| model | CISM16x-MAR312-p50 | ice sheet model |
| model ID | m001 | ISM member |
| ESM | CESM2-WACCM | climate forcing model |
| forcing ID | f001 | forcing realization |
| experiment | ssp585 | scenario; also historical or ctrl |
| configid | E001 | configuration counter; C for CORE, E for ESM, P for PPE |
| years | 2015-2300 | nominal simulation years |

The year range does not need to be known in advance: anything after the
configid is ignored when a file is looked up.

```{warning}
**No underscores inside a field.** Fields are counted by position, so a group
called MY_GROUP shifts everything after it by one: the tools read MY as the
group and GROUP as the model. Use hyphens.
```

Exactly one file must match. Two files that differ only in their year range,
say a truncated run left beside the full one, stop the run with a SKIP rather
than have it guess.

## Time encoding

State variables (lithk, topg, sftgrf, sftflf) are stamped Jan 1 of the
*following* year: the value for 2015 carries the timestamp 2016-01-01. Flux
variables (acabf, licalvf and the rest) are stamped Jul 1 of the year itself,
with time bounds.

Filenames and CSV column headers use the nominal year. A file named
..._2015-2300.nc holds state timestamps from 2016-01-01 to 2301-01-01, and the
output made from it is also named 2015-2300.

```{note}
`--refyear` is the one option that takes a timestamp year rather than a
nominal one. `--refyear 2050` selects the step stamped 2050-01-01, which is
the end of nominal year 2049. See {doc}`running`.
```

## Generic data files

Area factors and masks, named for the region and the grid resolution in
metres. At 16 km for Antarctica:

```
Data/AIS/
├── af2_AIS_16000m_v1.nc                               area factors
├── maxmask1_AIS_16000m_v0.nc                          ice sheet mask
├── iaf2_GIC_AIS_16000m_v0.nc                          glaciers and ice caps
└── basins_regions_AIS_Rignot_extended_16000m_v1.nc    basins (only with --basins)
```

and for Greenland:

```
Data/GrIS/
├── af2_GrIS_16000m_v1.nc
├── maxmask1_GrIS_16000m_v1.nc
├── iaf2_GIC_GrIS_16000m_v0.nc
└── basins_GrIS_Mouginot_extended_16000m_v1.nc
```

The resolution is read from the model grid, so the names have to match it.
All of these are on the ISMIP Globus server under Output-Processing.

## params.nc

One per model, in the model's directory: Models/AIS/VUW/PISM1/params.nc. It
holds three numbers, the ice, sea-water and fresh-water densities the model
was run with, as variables rhoi, rhow and rhof. Write it with:

```bash
ismip7-scalars-set-params --region AIS --group VUW --model PISM1 \
    --rhoi 910 --rhow 1028 --rhof 1000 --modelpath Models/AIS
```

If the model tree is read-only, a submissions tree on NIRD for instance, keep
params.nc in a tree of your own with the same group and model folders. Write
it there by giving that tree to `ismip7-scalars-set-params` as
`--modelpath`, and then give the same tree to `ismip7-scalars` as
`--params-path`:

```bash
ismip7-scalars-set-params --region AIS --group VUW --model PISM1 \
    --rhoi 910 --rhow 1028 --rhof 1000 --modelpath /home/me/params/AIS
ismip7-scalars --region AIS --group VUW --model PISM1 ... \
    --modelpath /nird/.../ISMIP7_submissions/AIS --params-path /home/me/params/AIS
```

The file may also hold an ocean area, but it is not used. Every submission is
normalised by the same 3.625 × 10¹⁴ m² (Gregory et al., 2019) so that models
are comparable.
