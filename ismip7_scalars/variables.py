"""What the ISMIP7 data request says each scalar variable is called.

The state and flux scalars this package writes -- ``lim``, ``limnsw``,
``iareagr``, ``iareafl`` and the six ``tend*`` fluxes -- are requested
variables in their own right, and the data request already fixes each one's
``standard_name``, ``units`` and ``long_name``.  Those are read from the
installed ``isschecker`` package rather than restated here, so that a file this
package writes carries the same metadata the compliance checker will look for.
See :mod:`ismip7_scalars.paths` for why.

The sea-level contributions are not in the data request -- they are derived
products, not something a model submits -- so their metadata is this package's
own and lives in :mod:`ismip7_scalars.scalars`.
"""

from __future__ import annotations

import csv
from functools import lru_cache

from ismip7_scalars.paths import MissingDataError, variable_request_path

#: Column headings this module relies on in the data request CSV.  Checked on
#: every read so that an upstream rename fails here, loudly, rather than
#: quietly writing empty attributes into every output file.
_REQUIRED_COLUMNS = ('Variable Name', 'standard_name', 'units', 'long_name')


class DataRequestError(MissingDataError):
    """The data request could not be read, or lacks something needed."""


@lru_cache(maxsize=None)
def variable_request():
    """Return the ISMIP7 data request, one dict per variable."""
    path = variable_request_path()
    with open(path, newline='') as handle:
        reader = csv.DictReader(handle)
        missing = [column for column in _REQUIRED_COLUMNS
                   if column not in (reader.fieldnames or ())]
        if missing:
            raise DataRequestError(
                f'{path} has no {", ".join(missing)} column(s); the ISMIP7 '
                f'data request has changed shape and this package needs '
                f'updating')
        return tuple(dict(row) for row in reader)


@lru_cache(maxsize=None)
def _by_name():
    """The data request indexed by variable name."""
    return {row['Variable Name'].strip(): row for row in variable_request()}


@lru_cache(maxsize=None)
def variable_metadata(name):
    """Return ``(standard_name, units, long_name)`` for a requested variable.

    ``standard_name`` is ``None`` where the data request leaves it blank --
    ``tendlifmassbf`` and ``tendligroundf`` have no CF standard name yet -- and
    the attribute is then simply not written, which is what the compliance
    checker expects.
    """
    row = _by_name().get(name)
    if row is None:
        raise DataRequestError(
            f"'{name}' is not in the ISMIP7 data request at "
            f'{variable_request_path()}; either the variable was renamed '
            f'upstream or this package is asking for something that was '
            f'never requested')
    standard_name = (row['standard_name'] or '').strip()
    return (standard_name or None,
            (row['units'] or '').strip(),
            (row['long_name'] or '').strip())
