---
name: review-comments
description: Write a review comment, review findings, or a reply to review feedback on a GitHub pull request. Use when reviewing code, reporting what testing someone else's branch turned up, or answering a reviewer's question.
---

# Review comments

The reader is deciding what to change.

- Put each finding as an inline comment on the line it concerns, one point
  each. That is where colleagues put them, and it is why their review
  bodies are short.
- The review body summarizes: what you ran, and the verdict. Two or three
  sentences.
- A finding that has no line in the diff, such as a file the pull request
  should have changed and did not, goes in the body, one short paragraph
  each.
- No section on what already works. One line for all of it, if any.
- Say what you could not check, such as MATLAB itself or a real
  submission.
- A reply answers the question asked. Quote the question only when the
  thread has moved on since it was put.

## Calibration

Review bodies here run from four words ("Looks good, thanks
@hgoelzer!") to about 200, and inline comments from 18 words to 83.
That is too few to measure a tail, so take the rule of thumb from
[polaris]: review bodies at 14 words at the median, 55 at the ninetieth
percentile and 239 at the longest; inline comments at 22 to 32 words at
the median and 170 at the longest.

[polaris]: https://github.com/E3SM-Project/polaris

## Enough

One finding, on the line, with the case that shows it and a way out
(#12):

> The filename doesn't change with `--basins` or `--no-mm`, so runs of
> the same experiment with different mask selections now write the same
> CSV. For example, a default run followed by `--basins --no-mm` into the
> same `--outpath` silently loses the whole-sheet rows. Before this PR
> those were separate files, and the NetCDF files still are, because
> `--basins` adds the mask name. If people run mask selections
> separately, the filename should say which masks it holds. If not, a
> warning in the docs would do.

A minor point, marked as one (#12):

> Minor: once this is merged, "existing" no longer refers to anything.
> Maybe "omitted: use the per-scalar defaults"? The same applies on line
> 269 and in `docs/user/running.md`.

A reply that says what changed and how it was checked (#12):

> Hi Xylar, all points addressed with the revised code. In particular,
> matlab version is again identical to python version and verified with
> comparison across various outputs of a real submission.

## Too much

The review body on #12 opened with what already worked:

> This looks good overall: the consolidated CSV and the format switches
> do what the description says, and the defaults are unchanged when
> neither switch is given. I have a few comments inline, plus two that
> don't fit on a line in the diff:

"A few comments inline, plus two that don't fit on a line" would do. The
two that followed, a missing `parser.error` and the MATLAB CSV no longer
matching, were the right things to put in the body.

A finding is checked before it is written. A bot review on
ismip/ISM_SimulationChecker#25 reported a missing docs section that
existed, after 455 words restating the pull request.
