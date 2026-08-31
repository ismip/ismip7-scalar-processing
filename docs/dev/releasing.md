# Releasing

This page is for maintainers -- those with write access to
[the main repository](https://github.com/ismip/ismip7-scalar-processing). If
you are contributing from a fork, nothing here is yours to do; open the pull
request and a maintainer will fold it into the next release.

Modelers get the tools from conda-forge, and conda-forge builds from a tag.
Anything on `main` that has not been tagged therefore does not exist as far as
they are concerned.

**So tag a release whenever a change reaches `main` that a user would notice.**
That is deliberately a low bar: a change to any computed number, a new or
altered command-line option, a change to the output filenames or CSV columns, a
bug fix, or a widened dependency range. Releases are cheap; someone chasing a
discrepancy against a source checkout that turns out to be six months of
untagged changes is not. Refactorings, tests, CI and documentation-only changes
need no release, though there is no harm in folding them into the next one.

```{important}
A change that alters a computed value deserves a **minor** bump at least, and a
line in the release notes saying which variable moved and by how much. People
compare these numbers across submissions; a silent change to one of them is
worse than no release at all.
```

## The relationship with `isschecker`

This package reads the ISMIP7 data request out of `isschecker` at runtime (see
{doc}`../user/data-sources`), which has two consequences for releases.

**A data request change is released by `isschecker`, not here.** If a
variable's `standard_name` or `long_name` is corrected upstream, updating
`isschecker` is enough; this package needs no release at all. That is the point
of not keeping a copy.

**A change of shape does need a release here** — a renamed column makes the
lookup fail loudly, and the fix is a change here plus the `isschecker` floor
raised to the version that has it.

## Cutting a release

1. Bump `version` in `pyproject.toml` following
   [semantic versioning](https://semver.org/) -- patch for a fix that does not
   change any output, minor for a new option or a corrected number, major for a
   change to the output layout or filenames -- and merge that to `main`.

2. Draft a new
   [GitHub release](https://github.com/ismip/ismip7-scalar-processing/releases/new)
   against `main`. In the tag field, type the new version and choose **Create
   new tag on publish**, so that publishing the release creates the tag: one
   action, and the two can never disagree about which commit they point at.
   Write notes saying what changed for users, then publish.

   The tag is the bare version number -- `0.2.0`, no `v` prefix -- because the
   feedstock builds its source URL from it, and it must match `version` in
   `pyproject.toml` exactly.

3. Wait for the conda-forge bot to open a version-bump PR on the
   `ismip7-scalars` feedstock, usually within a few hours. Review and merge it;
   the package appears on conda-forge shortly after the build finishes. Merging
   it needs write access to the feedstock, which is separate from write access
   here -- see [Maintaining the feedstock](#maintaining-the-feedstock).

If the release changed the dependency ranges, edit the feedstock PR before
merging so that the `run:` requirements in `recipe/recipe.yaml` match
`pyproject.toml` and `ismip7_scalars_env.yml` -- the bot updates the version and
hash, not the requirements. Those three lists are the same constraints written
down three times, and it is worth checking them against one another at each
release.

## The first release

The package has no feedstock until someone creates one. Open a pull request
against
[`conda-forge/staged-recipes`](https://github.com/conda-forge/staged-recipes)
adding a `recipes/ismip7-scalars/recipe.yaml`. It is a pure-Python `noarch`
recipe: the source is the GitHub tag tarball, the build is
`pip install . -vv --no-deps --no-build-isolation`, the run requirements are the
`dependencies` from `pyproject.toml`, and the tests should import
`ismip7_scalars` and run each entry point's `--version`. Once that merges,
conda-forge creates the feedstock and the bot takes over from there.

## Confirming what was published

Optionally, confirm what was published rather than assuming it:

```bash
conda create -n ismip7-scalars-test -c conda-forge --override-channels \
    ismip7-scalars pytest
conda activate ismip7-scalars-test
ismip7-scalars --version    # should print the version you tagged
cd $(mktemp -d) && pytest -v /path/to/ismip7-scalar-processing/tests
```

Run that from a checkout of the tag, not of `main`: the tests come from the
source tree while the package comes from conda-forge, so with `main` checked out
any change made since the tag shows up as a test failure that says nothing about
the release.

It is optional because of the wait. A merged feedstock PR does not put the
package within reach immediately: the build has to finish, and the result then
takes roughly an hour to propagate. Until it has, `conda create` either cannot
find the new version or reports the old one, and neither means anything is
wrong. So this is not a step to sit and retry -- come back to it later in the
day, or skip it. CI already runs the full suite against the tagged source at
both ends of every dependency range, and the feedstock runs the recipe's own
import and `--version` tests before publishing at all.

## Maintaining the feedstock

The conda-forge package is built by its own repository, separate from this one,
with its own list of maintainers -- being a maintainer here does not make you
one there. Only feedstock maintainers can merge the bot's version-bump PRs, so
a release stalls if nobody available has that access. It is worth having more
than one of us on the list.

The list lives in the recipe itself, under `extra: recipe-maintainers:`. To be
added, open an **issue** on the feedstock titled:

```
@conda-forge-admin, please add user @your-github-username
```

A bot then opens a PR adding you, which an existing feedstock maintainer merges.
GitHub will email you an invitation to the feedstock's team in the conda-forge
organization; **you have to accept it**, or the merge has given you nothing.
This is conda-forge's documented mechanism, described under
[Updating the maintainer list](https://conda-forge.org/docs/maintainer/updating_pkgs/#updating-the-maintainer-list);
leave the bot's PR alone rather than editing it, since it is built to skip a
package rebuild.

[The conda-forge maintainer documentation](https://conda-forge.org/docs/maintainer/)
covers the rest. Very little of it is needed for a package as simple as this
one -- a pure-Python `noarch` recipe whose releases are usually nothing more
than a version and a hash.
