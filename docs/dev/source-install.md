# Installing from source

You only need this to work *on* the package -- to test a change that has not
been released yet, or to develop one. To process a submission, install from
conda-forge instead (see {doc}`../user/installation`).

Create the conda environment and install the package into it:

```bash
conda env create -f ismip7_scalars_env.yml
conda activate ismip7-scalars
python -m pip install --no-deps --no-build-isolation -e .
```

Note that `ismip7_scalars_env.yml` installs the dependencies but not the
package itself, so the environment it creates is not the one conda-forge gives
you: an `ismip7-scalars` environment made this way holds no `ismip7-scalars`
package until the `pip install` runs. If you already have an environment of
that name from conda-forge, `conda env create` will refuse to create another
over it; give this one a different name with
`conda env create -n ismip7-scalars-dev -f ismip7_scalars_env.yml` and keep
both.

```{warning}
**Use those pip flags.** All dependencies come from conda-forge, and a plain
`pip install .` can silently replace them with PyPI wheels -- `netCDF4` in
particular bundles its own copy of the netCDF C library -- which is exactly how
two people end up with different results from the same files. `--no-deps`
keeps pip from resolving anything, and `--no-build-isolation` builds with the
environment's `setuptools` instead of downloading one from PyPI. Add
`--no-index` if you want any accidental network fetch to fail loudly rather
than succeed quietly.
```

`-e` gives an editable install, which is worth having while developing: the
tests import the installed package, so after a non-editable install an edit to
the source tree does not affect a test run until you reinstall. Drop the `-e`
to check that a real install works -- which is what CI does.

(`pytest` and the documentation packages come from the conda environment, so
neither the `[test]` nor the `[docs]` extra is needed; see
{doc}`building-docs`.)

If a rebuild ever behaves as though it were still running older code, delete
the `build/` directory: `setuptools` reuses its contents, so files that have
since been renamed or removed can otherwise end up back in the installed
package.

## Dependency ranges

Three lists say the same thing and have to agree:

`ismip7_scalars_env.yml`
: the developer environment, and the source of truth for the ranges.

`pyproject.toml`
: the package metadata, so that it is honest about what the package needs even
  though the supported install path never makes pip resolve it.

`ci/ismip7_scalars_env_floor.yml`
: every floor above, pinned exactly. CI runs the suite against this as well as
  a fresh solve of the ranges, so both ends of every range are verified rather
  than assumed.

When a floor moves, move it in all three. {doc}`../user/installation` has the
table of what each bound is for.

`isschecker` is in that list as a data dependency rather than a code one: none
of its functions are called, but the ISMIP7 data request it ships fixes the
metadata of every scalar this package writes. {doc}`../user/data-sources`
explains the split, and what it means for releases.
