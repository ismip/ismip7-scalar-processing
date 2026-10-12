---
name: pr-descriptions
description: Write or update a pull request description. Use when opening a pull request or editing its body.
---

# Pull request descriptions

The reader is deciding whether to review.

- What changed and why, in a few sentences. Not how.
- Anything needing a reviewer decision goes in its own short list near the
  top, never mid-paragraph.
- A list of changed behaviors is fine. A trace of the mechanism is not.
- If a computed number changes, say which variable and roughly by how
  much, and whether matlab/scalars.m changes with it.
- No commit list. No testing; that goes in a separate `Testing` comment.
- Link the issue that gives context, with a closing keyword if the pull
  request fixes it.
- Several fixes usually means several pull requests.

## Calibration

Heiko's descriptions here run from 1 word to 97, and 25 at the median.
The ones written with an agent ran 140 (#11), 240 (#10) and 1239 (#9).
[Polaris], a larger repository with the same maintainer, gives a rule of
thumb for the tail: 27 words at the median, 45 to 62 at the
seventy-fifth percentile, 103 to 110 at the ninetieth, 354 at the
longest.

[polaris]: https://github.com/E3SM-Project/polaris

## Enough

A change in behavior, in one sentence plus what was kept (#1):

> A2020 is now computed incrementally (each year relative to the
> previous) and accumulated as a cumulative sum, tracking grounding-line
> migration. The previous all-relative-to-reference approach is retained
> under flg_A20_cumul=False for comparison.

Several changes as a list, each with the reason a user wants it (#12):

> 1. Write enabled SLC methods, GIC variants, and masks to one run-level
>    CSV. This was requested by Tamsin, to put all csv output for one
>    experiment into one file.
> 2. Add tri-state --csv/--no-csv and --netcdf/--no-netcdf options to the
>    single-run and ensemble CLIs while preserving existing defaults.
>    Allows to produce only the sea-level csv files, or only the netcdf
>    scalars (or both) in a flexible way.

A numerical fix, with the decisions for the reviewer in their own list
(#11):

> Computes slvaf, the above-flotation term of slg20, and limnsw from
> `base` instead of `topg`, as @dlilien proposed in discussion #19. In a
> cell that is part grounded and part floating, the bed counts the water
> under the shelf against the grounded ice, so a thinning shelf showed up
> as sea-level rise. [...] MATLAB is updated to match.
>
> For review:
> - Without `base`, the run warns and falls back to `topg`. It could skip
>   instead, since `base` is mandatory.
> - sla20 is unchanged and has the same bias, from its grounded and ocean
>   masks. Fixing it means reformulating A2020, which needs Heiko.

## Too much

The description of #9 ran 1239 words in seven sections, two of which,
"Verification" and "Commits", the rules above leave out. Its "Why"
section traced what the old script could not do:

> `python/scalars.py` did its work at import time, which meant it could
> not be installed, could not be called from anything but a shell, and
> could not be tested below the level of spawning a subprocess. Its path
> defaults resolved against the script's own location, so it only really
> worked from a checkout laid out a particular way — and never against a
> read-only submissions tree.

Someone deciding whether to review does not need the old script traced.
"The scripts only ran from a checkout; this makes them an installable
package" would do, and the rest belongs in the commit messages. The ten
bugs it fixed on the way, each a paragraph, were several pull requests'
worth; the four that changed submitted numbers deserved their own.
