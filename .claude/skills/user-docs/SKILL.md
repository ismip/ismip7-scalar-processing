---
name: user-docs
description: Write or revise anything a person computing scalars reads. That is docs/user/, docs/getting-started.md, docs/index.md, README.md, the --help strings and the log, SKIP and error messages. Use when documenting a command, an option, an output file or a sea-level method, or wording a message. Not for docs/dev/.
---

# User documentation

The reader has model output and a terminal in front of them: a modeler
processing their own submission, or a member of the ISMIP7 team running
the whole ensemble on NIRD. They do not read the code, and English may
not be their first language.

- Say what to do, then show what they will see: the command, then the
  files or the lines it produces. The natural mistake, shown with what
  it gives, teaches more than a rule against it.
- Show a path or a file name as it is, annotated, not as a template with
  field names. A template is how a modeler came to pass their own
  model's directory as `--modelpath` (#10).
- Backticks are for what the reader types: commands, options and their
  values. Paths, file names and variable names go in plain text.
- Say what the tools do, not why they were designed that way. Cut any
  sentence whose job is to justify the one before it.
- Each thing is explained on one page. Other pages link to it with
  `{doc}` rather than explaining it again.
- The getting-started page goes in the order the reader meets things:
  install, lay out the files, write params.nc, run, read the output.
  The user guide is a reference, and the reader jumps to the page they
  need.
- A `--help` string is a lowercase phrase, as argparse's own are. It says
  what the option takes, gives an example value where the form is not
  obvious, and ends with the default in parentheses.
- A SKIP or error line names what is missing or wrong and what was
  expected, then stops. At most one thing to check.

## Calibration

#10 rewrote these pages to this standard. Outside code blocks, the README
and the user pages went from 384 backticked spans to 100, from 4770 words
to 4430, and from 25 words per sentence to 22. Since then they have
crept back to 132 spans and 4840 words. Hold the line at #10.

## Enough

The natural mistake, with what it produces (docs/getting-started.md):

> **The model path is the ice sheet directory**, Models/AIS here: the one
> holding a folder per group. The tools add the group and model
> themselves. If you point it at your own model's folder,
> Models/AIS/VUW/PISM1, the tools look for files under
> Models/AIS/VUW/PISM1/VUW/PISM1 and put params.nc there too.

What a missing input looks like, and what the exit codes mean, in four
sentences (docs/getting-started.md):

> If a required input is missing, the run prints one line starting with
> SKIP: saying what it could not find, and exits with code 2. Exit 0
> means it finished. Anything other than 0 or 2 is a bug; please report
> it.

## Described, not shown

The model path before #10, as a template the reader had to fill in:

> ```
> {modelpath}/{group}/{model}/{exp_group}/{configid}/
> ```

After, as a tree the reader can hold beside their own:

> ```
> Models/AIS/                    <-- this is --modelpath
> └── VUW/
>     └── PISM1/
>         ├── params.nc
>         └── CORE/
>             ├── C001/
>             └── C007/
> ```
