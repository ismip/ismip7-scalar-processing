# The sea-level methods

Three published ways of turning a change in ice geometry into a change in
global mean sea level. All three are written for every run. The spread between
them shows how much of a model's sea-level contribution depends on the
accounting rather than on the ice.

Each is a function in the ismip7_scalars.slc subpackage and can be called from
your own code.

## Volume above flotation (slvaf)

The ISMIP6 method. Only ice above the flotation thickness moves sea level when
it is lost; the rest already displaces its own weight. The volume above
flotation is converted straight to a fresh-water depth:

```
hf   = max(S - Zb, 0) * ρsw / ρi
Vaf  = Σ max(H - hf, 0) * A
slc  = -(Vaf - Vaf_ref) / A_ocean * ρi / ρfw
```

Simple, and the most directly comparable with earlier intercomparisons. It
ignores bedrock motion and the density difference between the ice's fresh
water and the sea water it displaces.

Zb is the ice base, the model's base variable, not the bed. Under grounded ice
the two are the same. They differ in a cell that is partly grounded and
partly floating, where H and Zb are cell means. With the bed, the water under
the floating part is counted against the grounded ice, so the cell loses
volume above flotation as its shelf thins, though no grounded ice is lost.
With the ice base, the cell mean gives the right answer wherever the cell is
below sea level. The same is true at the ice front, as long as base is at sea
level over open water.

If base is missing, the bed is used instead and the run prints a warning. The
state scalar limnsw is the same volume above flotation, as a mass, and is
computed the same way.

See [Seroussi et al. (2020)](https://doi.org/10.5194/tc-14-3071-2020) and
[Nowicki et al. (2024)](https://doi.org/10.1029/2024EF004561).

## Goelzer et al. (2020) (slg20)

[TC 14, 833-840](https://doi.org/10.5194/tc-14-833-2020). Adds two corrections
to the volume-above-flotation term:

- **Potential ocean volume**, for bedrock that moves. A bed that rebounds
  displaces water it used to hold; a bed that subsides makes room for more.
- **Density**, for the difference between the fresh water the ice becomes and
  the sea water it mixes into.

```
slc = slc_af + slc_pov + slc_den
```

The volume above flotation comes from the ice base, as for slvaf. The
potential ocean volume is the space between the bed and sea level, so it comes
from the bed.

The implementation folds the geoid height into the bedrock elevation, which
matches the published equations when sea level is fixed at zero. A second
function, slc_G2020_publ, restates the paper's equations in its own notation
as a cross-check, and the test suite checks that the two agree.

## Adhikari et al. (2020) (sla20)

[TC 14, 2819-2833](https://doi.org/10.5194/tc-14-2819-2020). Works in an
absolute frame, with bed and sea level both measured from the same ellipsoid,
and explicitly accounts for cells that switch between grounded and floating.
The other two methods only see grounding-line migration through the flotation
criterion.

Its grounded and ocean masks come from cell means of thickness and bed, so a
cell the grounding line crosses is treated as all grounded or all floating.
That gives sla20 the same bias in partly floating cells that slvaf had before
it used the ice base, and the ice base alone does not remove it.

This method measures the change between two consecutive states rather than the
departure from a reference, so a time series has to be accumulated. The
processing accumulates from the first historical timestep and subtracts the
value at the reference year, so the projection continues the historical curve
without a step at the join.

## Densities and ocean area

Every method takes the densities from the model's params.nc. Using the
densities a model was actually run with is what makes its sea-level
contribution comparable with another model's.

The ocean area is the same for every model, 3.625 × 10¹⁴ m² from
[Gregory et al. (2019)](https://doi.org/10.1007/s10712-019-09525-z). A
params.nc may hold its own ocean area, but it is ignored.

## Glaciers and ice caps

Every sea-level method is calculated twice. The `-gic` variant leaves glaciers
and ice caps out of the integral, using the iaf2_GIC mask; the plain variant
includes everything on the grid. Both variants are rows in the run-level SLC
CSV; by default, only the plain variant is also written to NetCDF. Which
variant you want depends on whether the glaciers around the ice sheet are
being counted elsewhere in your budget.
