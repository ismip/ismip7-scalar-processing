# Getting started

## Install

```bash
conda create -n ismip7-scalars -c conda-forge ismip7-scalars
conda activate ismip7-scalars
```

That gives you three commands: `ismip7-scalars` for one experiment,
`ismip7-scalars-ensemble` for a whole submissions tree, and
`ismip7-scalars-set-params` for the density file each model needs.
{doc}`user/installation` covers installing from source instead.

## What you need on disk

Three things, in addition to the model output itself.

**The model output**, laid out as
`{modelpath}/{group}/{model}/{exp_group}/{configid}/`, with filenames following
the ten-field ISMIP7 convention. {doc}`user/file-conventions` spells both out.

**The generic data files** -- area factors, the ice sheet mask, the glacier and
ice cap mask, and the basin masks -- for the resolution your model output is on.
They are on the ISMIP Globus server under `Output-Processing`. Point
`--datapath` at the directory holding them.

**A `params.nc`** for your model, holding the densities it was integrated with.
Write one with:

```bash
ismip7-scalars-set-params --region AIS --group VUW --model PISM1 \
    --rhoi 910 --rhow 1028 --rhof 1000 --modelpath ./Models/AIS
```

Densities matter: the sea-level methods convert ice volume to a water-equivalent
depth, so using the wrong ones puts a systematic error into the comparison.
That is why the file is required rather than defaulted.

## Run it

```bash
ismip7-scalars --region AIS \
    --group VUW --model PISM1 --modelid m001 \
    --esm CESM2-WACCM --forcingid f001 \
    --experiment ssp585 --configid C007 --hist-configid C001 \
    --datapath ./Data/AIS --modelpath ./Models/AIS
```

`--configid` names the projection; `--hist-configid` names the historical run it
is measured against, which for CORE experiments is usually a different configid.
The resolution is detected from the model grid, and `--exp-group` defaults from
the configid prefix, so neither has to be given.

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

The NetCDF tree mirrors the model tree; the CSVs are flat, one row per file,
with a column per year from 1850 to 2300. Override the root with `--outpath`.

## When something is missing

A run that cannot find an input it needs prints one `SKIP:` line saying what
and exits 2, rather than raising. A batch can then log the unit and carry on.
Exit 0 means the run finished, and any exit code other than 0 or 2 is a genuine
failure.

Some inputs are only needed for part of the output: without `sftgrf` and
`sftflf` the state scalars are skipped and everything else is still written, and
each flux variable is skipped on its own if its input file is absent.

## Next

{doc}`user/running` for every option, {doc}`user/output` for what the files
contain, and {doc}`user/ensemble` for processing a whole submission at once.
