---
name: testing-comments
description: Write a Testing comment on a pull request, recording what was run beyond CI and what the results were. Use after a Python/MATLAB comparison, a run on a real submission, or checking output numbers for a PR.
---

# Testing comments

What you ran that CI does not, and what came of it.

CI already runs the whole suite on Linux and macOS, against both the
newest and the oldest dependencies, and builds the docs with `-W`. The
reader can see those checks. Do not report them again.

- Say what you ran and on what, in one sentence: the command, and the
  submission or synthetic data it read, on NIRD or a local copy.
- Say the result. For a comparison with matlab/scalars.m, how many
  variables agreed and to what tolerance, and whether it ran in MATLAB
  or Octave. For a change to a computed number, the before and after for
  one experiment.
- If nothing was run beyond CI, say so in one line, or post nothing.
- Paste output only when the reader needs to see it, and then do not
  restate it in prose.
- Failures unrelated to the branch go under their own heading at the end.

## Calibration

The one Testing comment here (#11) ran 68 words. [Polaris] measured its
Testing comments at 21 to 43 words, and a recent agent-written one there
at 606.

[polaris]: https://github.com/E3SM-Project/polaris

## Enough

A MATLAB comparison and what the fix does to one number (#11):

> I compared Python with `matlab/scalars.m` under Octave 10.3 on a
> synthetic submission with partly floating cells. That took small
> test-only shims for `datetime` and `sum(..., 'all')`. All 13 variables
> agree to about 1e-15 relative. On that submission the fix moves the
> final slvaf from 6.6 mm to 2.3 mm, and sla20 doesn't change.

A modeler's check against their own numbers, as a table with no prose
restating it (#11, trimmed):

> | experiment | year | slvaf, main | slvaf, PR 11 | sla20, main and PR |
> |---|---|---|---|---|
> | ssp126, CESM2-WACCM | 2300 | +14.6 | +0.89 | +14.2 |
> | ctrl, CESM2-WACCM | 2300 | +6.2 | +0.29 | +6.1 |

## Too much

The same comment on #11 opened with the green checks:

> The test suite passes (295, 9 of them new), and the docs build with
> `-W`.

CI already says that. The comparison was the part worth posting.

The description of #6 carried a test plan of six ticked boxes, among
them "CI workflow triggers on push". Testing goes in its own comment, and
CI's own checks go nowhere.
