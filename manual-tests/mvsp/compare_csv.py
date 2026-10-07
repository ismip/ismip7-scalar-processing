#!/usr/bin/env python3
"""Compare the MATLAB and Python run-level SLC CSVs.

``compare_outputs.py`` compares NetCDF only, so the consolidated CSV that
both implementations now write is checked here instead.

The two files must agree on:
  * the header (same ten metadata columns, same year columns),
  * the set of (region, scalar) rows,
  * every value, to a tolerance.

The tolerance is relative, because MATLAB writes the values with ``%.10g``
(ten significant digits) while Python writes full precision.  The rounding
that costs is about ``5e-10`` relative, so the default ``--rel-tol`` is
``1e-9``; the underlying agreement is much tighter (the NetCDF comparison
shows ~1e-13 relative).

Usage:
    python compare_csv.py --py-csv DIR --mat-csv DIR
"""

import argparse
import csv
import glob
import os
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--py-csv', required=True,
                    help='directory holding the Python sl_*.csv')
parser.add_argument('--mat-csv', required=True,
                    help='directory holding the MATLAB sl_*.csv')
parser.add_argument('--rel-tol', type=float, default=1e-9,
                    help='relative tolerance on the SLC values '
                         '(default 1e-9, for the %.10g MATLAB formatting)')
parser.add_argument('--abs-tol', type=float, default=1e-12,
                    help='absolute floor in metres; a row passes if it is '
                         'within --abs-tol OR --rel-tol (default 1e-12, so '
                         'near-zero basin values are not judged on relative '
                         'error)')
args = parser.parse_args()

py_files = sorted(glob.glob(os.path.join(args.py_csv, 'sl_*.csv')))
if not py_files:
    print(f'No Python CSV found in {args.py_csv}')
    sys.exit(1)

fail = False
for py_path in py_files:
    name = os.path.basename(py_path)
    mat_path = os.path.join(args.mat_csv, name)
    if not os.path.exists(mat_path):
        print(f'MISSING MATLAB CSV: {name}')
        fail = True
        continue

    with open(py_path, newline='') as f:
        py_rows = list(csv.reader(f))
    with open(mat_path, newline='') as f:
        mat_rows = list(csv.reader(f))

    print(f'=== {name} ===')
    print(f'  rows: python {len(py_rows)}  matlab {len(mat_rows)}')

    if py_rows[0] != mat_rows[0]:
        print('  HEADER MISMATCH')
        print(f'    python: {py_rows[0][:12]} ...')
        print(f'    matlab: {mat_rows[0][:12]} ...')
        fail = True
        continue

    header = py_rows[0]
    key_cols = [header.index(c) for c in ('region', 'scalar')]

    def keyed(rows):
        return {tuple(r[i] for i in key_cols): r for r in rows[1:]}

    py_keyed = keyed(py_rows)
    mat_keyed = keyed(mat_rows)

    only_py = sorted(set(py_keyed) - set(mat_keyed))
    only_mat = sorted(set(mat_keyed) - set(py_keyed))
    if only_py:
        print(f'  only in python: {only_py}')
        fail = True
    if only_mat:
        print(f'  only in matlab: {only_mat}')
        fail = True

    year_cols = [i for i, c in enumerate(header) if c.startswith('y')]
    worst_rel = 0.0
    worst_rel_where = None
    worst_abs = 0.0
    worst_abs_where = None
    for key in sorted(set(py_keyed) & set(mat_keyed)):
        py_row, mat_row = py_keyed[key], mat_keyed[key]
        for i in year_cols:
            pv, mv = py_row[i], mat_row[i]
            if pv == 'NA' or mv == 'NA':
                if pv != mv:
                    print(f'  {key} {header[i]}: NA mismatch '
                          f'(python {pv!r}, matlab {mv!r})')
                    fail = True
                continue
            pf, mf = float(pv), float(mv)
            diff = abs(pf - mf)
            scale = max(abs(pf), abs(mf))
            rel = diff / scale if scale > 0 else 0.0
            if diff > worst_abs:
                worst_abs, worst_abs_where = diff, (key, header[i])
            if rel > worst_rel:
                worst_rel, worst_rel_where = rel, (key, header[i])
            if diff > args.abs_tol and rel > args.rel_tol:
                print(f'  {key} {header[i]}: python {pv} matlab {mv} '
                      f'diff {diff:.3e} rel {rel:.3e}')
                fail = True
    print(f'  rows compared: {len(set(py_keyed) & set(mat_keyed))}, '
          f'years per row: {len(year_cols)}')
    print(f'  max abs diff: {worst_abs:.3e} m'
          + (f' at {worst_abs_where}' if worst_abs_where else ''))
    print(f'  max rel diff: {worst_rel:.3e}'
          + (f' at {worst_rel_where}' if worst_rel_where else '')
          + '  (large only where the value is ~0)')

print()
if fail:
    print('RESULT: CSV DIFFERENCES EXCEED TOLERANCE or files missing')
    sys.exit(1)
print('RESULT: All CSVs match within tolerance')
