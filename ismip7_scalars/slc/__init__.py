"""Sea-level contribution methods.

Three of them, each a published way of turning a change in ice geometry into a
change in global mean sea level:

``slc_vaf``
: volume above flotation, the ISMIP6 method, converted directly to freshwater.

``slc_G2020``
: `Goelzer et al. (2020) <https://doi.org/10.5194/tc-14-833-2020>`_, which
  adds a potential-ocean-volume and a density correction.

``slc_A2020``
: `Adhikari et al. (2020) <https://doi.org/10.5194/tc-14-2819-2020>`_, in an
  absolute reference frame, which accounts for grounding-line migration.

``slc_G2020_publ`` restates G2020 in the notation of the paper and exists to
cross-check ``slc_G2020``; nothing in the processing imports it.

Every function takes the densities and ocean area as an object ``c`` with
attributes ``RHOI``, ``RHOSW``, ``RHOFW`` and ``AO``, so that one run can use
the densities its own model was integrated with.
"""

from ismip7_scalars.slc import (  # noqa: F401
    sl_constants,
    slc_A2020,
    slc_G2020,
    slc_G2020_publ,
    slc_vaf,
)

__all__ = ['sl_constants', 'slc_A2020', 'slc_G2020', 'slc_G2020_publ',
           'slc_vaf']
