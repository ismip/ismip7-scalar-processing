# Building the documentation

These pages are Markdown in `docs/`, built with Sphinx through
[MyST](https://myst-parser.readthedocs.io/) and the
[Furo](https://pradyunsg.me/furo/) theme.

The build reads the version from `pyproject.toml` and nothing else, so neither
the package nor any of its dependencies has to be installed. If you already
have the developer environment from {doc}`source-install`, it has everything:

```bash
conda activate ismip7-scalars
sphinx-build -b html docs docs/_build/html
```

Otherwise the smaller environment CI uses will do:

```bash
conda env create -f ci/docs_env.yml
conda activate ismip7-scalars-docs
sphinx-build -b html docs docs/_build/html
```

Open `docs/_build/html/index.html`.

## Before opening a pull request

Build the way CI does:

```bash
sphinx-build -W --keep-going -b html docs docs/_build/html
```

`-W` turns every warning into an error -- a broken cross-reference, a page in no
toctree, a malformed directive -- and `--keep-going` reports all of them rather
than stopping at the first. CI does this on every push, so a warning you leave
behind fails your pull request.

If a rebuild seems to ignore an edit, delete `docs/_build/` and try again;
Sphinx caches aggressively.

## Publishing

`.github/workflows/docs.yml` builds the pages on every push and pull request,
and publishes them to GitHub Pages from `main` only. There is nothing to do by
hand: merging to `main` updates
<https://ismip.github.io/ismip7-scalar-processing/> a minute or two later.

## Writing

Three conventions worth keeping:

**Cross-reference with roles, not URLs.** `` {doc}`../user/running` `` breaks
the build if the page is renamed; a hand-written link quietly rots.

**Say why, not only what.** The reference material -- which option does what --
is in the tables. The prose around them is for the things a table cannot say:
why `--hist-configid` exists, why the ocean area is not per-model, why a
projection is never paired against itself.

**Keep the user and developer guides apart.** {doc}`../user/index` is for
someone with output to process; this guide is for someone changing the code.
Anything a modeler needs belongs on the user side even if a developer wrote it.
