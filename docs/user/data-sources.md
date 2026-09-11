# Where the conventions come from

Three kinds of fact go into a run, and they come from three places.

## The ISMIP7 data request, from isschecker

The state and flux scalars this package writes (lim, limnsw, iareagr, iareafl
and the six tend fluxes) are ISMIP7 variables in their own right, and the data
request fixes their standard names, units and long names. That request is
maintained in [ISM_SimulationChecker](https://github.com/ismip/ISM_SimulationChecker)
and shipped in its isschecker package.

This package reads the request from isschecker at runtime rather than keeping
a copy, which is why isschecker is a dependency even though none of its code
runs. A copy once drifted, and the files this tool wrote were rejected by the
compliance checker.

Two things follow:

- A correction to a variable's name or units is released by isschecker, not
  here. Update isschecker and the files pick it up.
- A change to the *shape* of the request, such as a renamed column, needs a
  release here as well.

The sea-level scalars (slvaf, slg20, sla20) are derived here rather than
submitted by a model, so they are not in the data request and carry no
standard name.

## The CORE experiment table, from this package

ISMIP7_experiments_CORE.csv, inside the package, records which CORE configid
runs which scenario under which forcing ESM. The ensemble driver uses it to
pair each projection with its historical run: C001 for CESM, C002 for MRI.
Override it with `ismip7-scalars-ensemble --core-csv`.

## The area factors and masks, from Globus

These are large gridded fields, distributed on the ISMIP Globus server under
Output-Processing rather than packaged with anything. Point `--datapath` at
them. {doc}`file-conventions` lists the names.
