# Where the conventions come from

Two kinds of fact go into a run, and they come from two different places on
purpose.

## The ISMIP7 data request comes from `isschecker`

The state and flux scalars this package writes — `lim`, `limnsw`, `iareagr`,
`iareafl` and the six `tend*` fluxes — are requested ISMIP7 variables in their
own right. The data request already fixes each one's `standard_name`, `units`
and `long_name`, and it is maintained in
[ISM_SimulationChecker](https://github.com/ismip/ISM_SimulationChecker), which
publishes it as part of the `isschecker` package.

This package reads it from there at runtime rather than keeping a copy. That is
why `isschecker` is a dependency even though none of its code is called: it is
a *data* dependency.

```{important}
A copy is a thing that can drift, and this package's copy did. It wrote the
data request's `standard_name` into each file's `long_name` attribute and no
`standard_name` at all — which the compliance checker reports as an error. So
the tool that produces ISMIP7 scalars was writing files that its sibling tool
would reject. Reading one shared definition is what stops that recurring.
```

Two consequences worth knowing:

**A data request change is released by `isschecker`, not here.** If a variable's
`standard_name` or `long_name` is corrected upstream, updating `isschecker` is
enough — the files this package writes pick it up with no release of its own.

**A change of *shape* does need a release here.** If a column is renamed, the
lookup fails loudly rather than quietly writing empty attributes, and the fix
is a change here plus an `isschecker` floor raised to the version that has it.

The sea-level contributions are the exception. `slvaf`, `slg20` and `sla20` are
derived here rather than submitted by a model, so they are not in the data
request; their metadata is this package's own, and they carry no
`standard_name` because there is no agreed one to carry.

## The CORE experiment table is this package's own

`ismip7_scalars/data/ISMIP7_experiments_CORE.csv` records which CORE configid
runs which scenario under which forcing ESM. The ensemble driver uses it to
work out the historical run to pair each projection with — C001 for the
CESM-driven projections, C002 for the MRI-driven ones.

That pairing is a decision this tool makes, not part of the data request, so
the table lives here, the way `ismip7-interpolation` keeps its remapping policy
in its own package. Override it with `ismip7-scalars-ensemble --core-csv`.

## The generic data files come from Globus

Area factors and masks are neither: they are large NetCDF fields, distributed
on the ISMIP Globus server under `Output-Processing` rather than packaged with
anything. Point `--datapath` at them. {doc}`file-conventions` lists the names.
