---
name: plan-documents
description: Write a plan for work not yet started, for a colleague or the user to approve before implementation begins.
---

# Plan documents

The reader is deciding whether to let you proceed.

- Open questions and anything needing a decision go at the top.
- The steps, in order, one line each.
- Do not justify each step. Do not list the files you will touch. Do not
  restate the codebase back.
- If a step needs a paragraph to explain, it belongs in an issue, not in
  the plan.

## Enough

Plans are approved in conversation rather than committed, so there is no
colleague-written example to copy. The following is constructed, from a
follow-up #10 left open.

> **Open:** should a `--modelpath` that already ends in the group and
> model be an error, or a warning?
>
> 1. Check whether `--modelpath` ends in `<group>/<model>`.
> 2. If it does, print one line naming the path and the one expected.
> 3. Do the same in `ismip7-scalars-set-params`.
> 4. Add the message to the getting-started page, beside the doubled
>    directory it catches.
