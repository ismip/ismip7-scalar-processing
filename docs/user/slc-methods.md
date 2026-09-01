# The sea-level methods

Three published ways of turning a change in ice geometry into a change in
global mean sea level. They are not alternatives to choose between: all three
are written out for every run, and the spread between them is itself
informative, because it says how much of a model's sea-level contribution
depends on the accounting rather than on the ice.

Each is implemented in `ismip7_scalars.slc` and can be called directly.

## Volume above flotation -- `slvaf`

The ISMIP6 method. Ice above the flotation thickness is the only ice whose loss
moves sea level; the rest already displaces its own weight. The volume above
flotation is converted straight to a freshwater depth:

```
hf   = max(S - B, 0) * ρsw / ρi
Vaf  = Σ max(H - hf, 0) * A
slc  = -(Vaf - Vaf_ref) / A_ocean * ρi / ρfw
```

Simple, and the one most directly comparable with earlier intercomparisons.
It says nothing about bedrock motion or about the salinity of the water the ice
displaces.

See [Seroussi et al. (2020)](https://doi.org/10.5194/tc-14-3071-2020) and
[Nowicki et al. (2024)](https://doi.org/10.1029/2024EF004561).

## Goelzer et al. (2020) -- `slg20`

[TC 14, 833-840](https://doi.org/10.5194/tc-14-833-2020). Adds two corrections
to the volume-above-flotation term:

**Potential ocean volume**, for bedrock that moves. A bed that rebounds
displaces water it used to hold; a bed that subsides makes room for more.

**Density**, for the difference between the fresh water the ice becomes and the
sea water it mixes into.

```
slc = slc_af + slc_pov + slc_den
```

The implementation folds the geoid height into the bedrock elevation, which is
equivalent to the published equations when sea level is fixed at zero.
`slc_G2020_publ` restates them in the notation of the paper and exists to
cross-check the version that is used; the test suite checks that the two agree.

## Adhikari et al. (2020) -- `sla20`

[TC 14, 2819-2833](https://doi.org/10.5194/tc-14-2819-2020). Works in an
absolute reference frame, with the bed and sea level measured against the same
ellipsoid, and accounts explicitly for cells that change between grounded and
floating -- grounding-line migration, which the other two methods handle only
through the flotation criterion.

A2020 measures the change between *two* states rather than the departure from a
reference, so a time series of it has to be accumulated. The processing does
that seamlessly across the historical and projection runs -- starting the
accumulation at the first historical timestep and subtracting the value at the
reference year -- so that the projection continues the historical curve without
a step at the join.

## Volume diagnostics

`slc_vaf` also provides total, grounded and floating ice volume change, related
by

```
Vtot = Vgr + Vfl
```

The processing does not write them out for the full ice sheets; the MINI cases
do, and the test suite uses the identity above as a check.

## Densities and ocean area

Every method takes the densities from the model's `params.nc`: using the
densities a model was actually integrated with is what makes its sea-level
contribution mean the same thing as another model's.

The ocean area is *not* per-model. Every submission is normalised by

```
A_ocean = 3.625e14 m²
```

from [Gregory et al. (2019)](https://doi.org/10.1007/s10712-019-09525-z), so
that the numbers are comparable. A `params.nc` may carry its own `oarea`; the
processing ignores it.

## Glaciers and ice caps

Every sea-level series is written twice. The `-gic` variant excludes glaciers
and ice caps from the integral, using the `iaf2_GIC_*` mask; the plain variant
includes everything on the grid. Which one you want depends on whether the
glaciers around the ice sheet are being accounted for elsewhere in your budget.
