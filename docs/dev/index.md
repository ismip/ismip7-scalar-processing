# Developer guide

Guidance for contributing to the package and for maintaining its releases. If
you only want to process a submission, you do not need any of this -- install
from conda-forge as described in {doc}`../getting-started`.

The repository is laid out like this:

`ismip7_scalars/scalars.py`
: the processing pipeline and the `ismip7-scalars` entry point.

`ismip7_scalars/ensemble.py`
: the batch driver and the `ismip7-scalars-ensemble` entry point.

`ismip7_scalars/naming.py`
: the ISMIP7 filename conventions, as pure functions.

`ismip7_scalars/writers.py`
: the NetCDF and CSV output.

`ismip7_scalars/params.py`
: the `params.nc` writer and the `ismip7-scalars-set-params` entry point.

`ismip7_scalars/slc/`
: the three sea-level methods, plus `slc_G2020_publ` as a cross-check.

`ismip7_scalars/paths.py`, `ismip7_scalars/variables.py`
: where the data files come from, and the ISMIP7 data request lookup. The
  data request is read from `isschecker`, not copied; see
  {doc}`../user/data-sources`.

`ismip7_scalars/data/`
: the CORE experiment table — this package's own, unlike the data request.

`tests/`
: the test suite, including `synthetic.py`, which writes the miniature
  submissions the integration tests run over.

`matlab/scalars.m`
: the MATLAB implementation of the same processing. See {doc}`matlab`.

`manual-tests/`
: what cannot run in CI -- the Python/MATLAB comparison -- and the MINI cases.
  See {doc}`mini`.

`test-data/`
: the committed MINI inputs.

`docs/`
: these pages.

```{toctree}
:maxdepth: 2
:caption: Contents

source-install
testing
mini
matlab
building-docs
releasing
```
