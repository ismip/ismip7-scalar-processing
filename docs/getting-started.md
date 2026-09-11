# Getting started

## Install

```bash
conda create -n ismip7-scalars -c conda-forge ismip7-scalars
conda activate ismip7-scalars
```

You get three commands:

- `ismip7-scalars` processes one experiment
- `ismip7-scalars-ensemble` processes every experiment in a submission tree
- `ismip7-scalars-set-params` writes the density file each model needs

{doc}`user/installation` covers installing from source.

## Lay out your files

Suppose your group is VUW, your model is PISM1, and you want to process the
Antarctic ssp585 projection C007 against the historical run C001. The tools
expect this layout, which is the same as an ISMIP7 submission:

```
Models/AIS/                    <-- this is --modelpath
└── VUW/
    └── PISM1/
        ├── params.nc
        └── CORE/
            ├── C001/
            │   ├── lithk_AIS_VUW_PISM1_m001_CESM2-WACCM_f001_historical_C001_1850-2014.nc
            │   ├── topg_AIS_VUW_PISM1_m001_CESM2-WACCM_f001_historical_C001_1850-2014.nc
            │   └── ...
            └── C007/
                ├── lithk_AIS_VUW_PISM1_m001_CESM2-WACCM_f001_ssp585_C007_2015-2300.nc
                ├── topg_AIS_VUW_PISM1_m001_CESM2-WACCM_f001_ssp585_C007_2015-2300.nc
                └── ...

Data/AIS/                      <-- this is --datapath
├── af2_AIS_16000m_v1.nc
├── maxmask1_AIS_16000m_v0.nc
├── iaf2_GIC_AIS_16000m_v0.nc
└── basins_regions_AIS_Rignot_extended_16000m_v1.nc
```

Two things to notice:

- **The model path is the ice sheet directory**, Models/AIS here: the one
  holding a folder per group. The tools add the group and model themselves.
  If you point it at your own model's folder, Models/AIS/VUW/PISM1, the tools
  look for files under Models/AIS/VUW/PISM1/VUW/PISM1 and put params.nc there
  too.
- **The data files** are the area factors and masks for your grid resolution.
  Download them from the ISMIP Globus server, under Output-Processing.

Models/AIS and Data/AIS are the defaults, so if you run from the directory
above them you can leave off `--modelpath` and `--datapath`.

## Write params.nc

Each model needs a small file recording the ice, sea-water and fresh-water
densities it was run with:

```bash
ismip7-scalars-set-params --region AIS --group VUW --model PISM1 \
    --rhoi 910 --rhow 1028 --rhof 1000 --modelpath Models/AIS
```

This writes Models/AIS/VUW/PISM1/params.nc. There is no default because the
wrong densities put a systematic error into the sea-level numbers.

## Run it

```bash
ismip7-scalars --region AIS \
    --group VUW --model PISM1 --modelid m001 \
    --esm CESM2-WACCM --forcingid f001 \
    --experiment ssp585 --configid C007 --hist-configid C001 \
    --modelpath Models/AIS --datapath Data/AIS
```

The projection is C007. Its sea-level change is measured from the end of the
historical run, C001. The resolution is read from the model grid.

## What comes out

```
Output/
├── nc/AIS/VUW/PISM1/CORE/C007/
│   ├── slvaf_AIS_VUW_PISM1_m001_CESM2-WACCM_f001_ssp585_C007_1850-2300.nc
│   ├── slg20_...nc   sla20_...nc
│   ├── lim_...nc     limnsw_...nc   iareagr_...nc   iareafl_...nc
│   └── tendacabf_...nc  ...
└── csv/
    ├── slvaf_AIS_VUW_PISM1_...csv
    └── slvaf-gic_AIS_VUW_PISM1_...csv
```

NetCDF files go in a tree that mirrors your model tree. CSVs go in one flat
directory, one row per file with a column per year from 1850 to 2300, so that
rows from many models can be joined into one table. Change the root with
`--outpath`.

## When something is missing

If a required input is missing, the run prints one line starting with SKIP:
saying what it could not find, and exits with code 2. Exit 0 means it
finished. Anything other than 0 or 2 is a bug; please report it.

Some inputs are only needed for part of the output. Without sftgrf and sftflf
the state scalars are skipped and everything else is still written. Each flux
variable is skipped on its own if its file is missing.

## Next

{doc}`user/running` for every option, {doc}`user/output` for what the files
contain, and {doc}`user/ensemble` for processing a whole submission at once.
