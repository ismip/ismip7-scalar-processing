"""Locating the data files this package reads.

Two directories, from two packages, and the split is deliberate.

The ISMIP7 data request is the project's, not this tool's.  It is maintained in
`ISM_SimulationChecker <https://github.com/ismip/ISM_SimulationChecker>`_ and
read out of the installed ``isschecker`` package rather than copied into this
one.  A copy is a thing that can drift, and this package's copy silently had:
it wrote the data request's ``standard_name`` into each output file's
``long_name`` attribute and no ``standard_name`` at all, which the compliance
checker reports as an error.  Two ISMIP7 tools disagreeing about what a
variable is called is exactly the failure a shared source of truth prevents.

What *is* this package's own is ``data/ISMIP7_experiments_CORE.csv``: which
CORE configid runs which scenario under which forcing ESM, from which the
ensemble driver works out the historical run to pair each projection with.
That pairing is a decision this tool makes, not part of the data request.
"""

from __future__ import annotations

import atexit
from contextlib import ExitStack
from functools import lru_cache
from importlib import resources
from pathlib import Path

#: This package's own data: the CORE experiment table.
DATA_PACKAGE = f'{__package__}.data'

#: The ISMIP7 project's data, maintained in ISM_SimulationChecker.
ISSCHECKER_DATA_PACKAGE = 'isschecker.data'

#: The ISMIP7 data request, within the isschecker data package.
VARIABLE_REQUEST_CSV = 'ISMIP7_variable_request.csv'

#: The CORE experiment table, within this package's data.
CORE_EXPERIMENTS_CSV = 'ISMIP7_experiments_CORE.csv'


class MissingDataError(RuntimeError):
    """A data file this package reads is not where it should be."""


@lru_cache(maxsize=None)
def _materialise(package: str) -> Path:
    """Return the on-disk path of a data package's directory.

    ``importlib.resources`` hands back a ``Traversable``, which need not be a
    real file on disk, so each directory is materialised once on first use and
    kept for the life of the process.
    """
    try:
        traversable = resources.files(package)
    except ModuleNotFoundError as exc:
        raise MissingDataError(
            f'{package} is not installed.  The ISMIP7 data request is read '
            f'from the isschecker package rather than copied into this one; '
            f'install ismip7-scalars from conda-forge, which brings it, or '
            f'add isschecker to your environment.') from exc
    stack = ExitStack()
    atexit.register(stack.close)
    return Path(stack.enter_context(resources.as_file(traversable)))


def variable_request_path() -> Path:
    """Return the path of the ISMIP7 data request."""
    path = _materialise(ISSCHECKER_DATA_PACKAGE) / VARIABLE_REQUEST_CSV
    if not path.is_file():  # pragma: no cover - install error
        raise MissingDataError(
            f'isschecker is installed but ships no data request at {path}')
    return path


def core_experiments_path() -> Path:
    """Return the path of this package's CORE experiment table."""
    path = _materialise(DATA_PACKAGE) / CORE_EXPERIMENTS_CSV
    if not path.is_file():  # pragma: no cover - install error
        raise MissingDataError(
            f'ismip7_scalars ships no CORE experiment table at {path}')
    return path
