#!/usr/bin/env python3
"""Compare MATLAB and Python scalar output files — all NC variables.

Discovers all Python NC files, matches by filename against MATLAB output,
and reports max absolute diff, RMS, and relative diff for each. Also checks
each file's time bounds (presence, (time, nv) dimension order, values) and
the five checker-required global attributes.

Usage:
    python compare_outputs.py                           # both default to ../Output/nc
    python compare_outputs.py --region AIS              # compare only AIS files
    python compare_outputs.py --region GrIS             # compare only GrIS files
    python compare_outputs.py --py-outpath  ../Output-py/nc \
                              --mat-outpath ../Output-mat/nc
"""

import sys
import os
import glob
import argparse
import numpy as np
import netCDF4 as nc

parser = argparse.ArgumentParser(description="Compare MATLAB and Python scalar outputs")
parser.add_argument("--region", choices=["AIS", "GrIS"], default=None,
                    help="Filter by ice-sheet region (default: compare all files)")
parser.add_argument("--py-outpath",  default="../Output/nc")
parser.add_argument("--mat-outpath", default="../Output/nc")
args = parser.parse_args()

SLC_VARS = {'slvaf', 'slg20', 'sla20'}
ABS_TOL  = 1e-6    # metres — applied to SLC variables; f4 output storage
                   # quantises values to ~6e-8 relative
REL_TOL  = 1e-6    # applied to all other variables (relative to data max)
REQUIRED_ATTRS = ('group', 'model', 'contact_name', 'contact_email', 'crs')


def check_time_bounds(ds_py, ds_mat, rel_tol):
    """Compare the time bounds of two scalar files.

    Both files must either carry bounds or not, the bounds variable must
    sit on a (time, nv) dimension — CF puts the vertex dimension last —
    and the values must agree within rel_tol.
    """
    def bounds_var(ds):
        tv = ds.variables.get('time')
        if tv is None or not hasattr(tv, 'bounds'):
            return None
        return ds.variables.get(tv.bounds)

    py_b, mat_b = bounds_var(ds_py), bounds_var(ds_mat)
    if (py_b is None) != (mat_b is None):
        print('  BOUNDS MISMATCH: Python and MATLAB disagree on whether '
              'time_bounds exists')
        return False
    if py_b is None:
        return True
    for name, b in (('Python', py_b), ('MATLAB', mat_b)):
        if tuple(b.dimensions) != ('time', 'nv'):
            print(f'  BOUNDS DIMS ({name}): {b.dimensions} '
                  '(CF requires (time, nv))')
            return False
    py_arr, mat_arr = np.array(py_b[:]), np.array(mat_b[:])
    scale = float(np.max(np.abs(py_arr)))
    rel = float(np.max(np.abs(py_arr - mat_arr))) / scale if scale else 0.0
    if rel >= rel_tol:
        print(f'  BOUNDS DIFF: rel {rel:.2e} exceeds tolerance')
        return False
    return True


def check_global_attrs(ds_py, ds_mat):
    """The five checker-required global attributes must agree."""
    ok = True
    for a in REQUIRED_ATTRS:
        va, vb = getattr(ds_py, a, None), getattr(ds_mat, a, None)
        if va != vb:
            print(f'  ATTR MISMATCH {a}: Python {va!r} vs MATLAB {vb!r}')
            ok = False
    return ok

py_dir  = args.py_outpath
mat_dir = args.mat_outpath

# Discover all Python NC files (skip GIC NC files — Python doesn't write them by default).
# Search recursively so the {region}/{group}/{model}/{exp_group}/{configid}/ output tree
# is covered; fall back to the flat layout too.
py_files = sorted(set(glob.glob(os.path.join(py_dir, '**', '*.nc'), recursive=True)))
if args.region:
    py_files = [f for f in py_files if f'_{args.region}_' in os.path.basename(f)]
if not py_files:
    print(f'No Python output files found in {py_dir}')
    sys.exit(1)

max_diff_global = 0.0
fail = False

hdr = (f'{"Variable":<20}  {"Stem":<50}  '
       f'{"MaxAbsDiff":>14}  {"RMS":>14}  {"RelDiff":>10}  Status')
print(hdr)
print('-' * len(hdr))

for py_path in py_files:
    basename = os.path.basename(py_path)   # e.g. slvaf_AIS_... or lim_AIS_...
    # Extract variable name (everything before the first field of the ISMIP7 stem)
    # Stem starts at the first uppercase letter following an underscore that begins AIS/GrIS
    varname = basename.split('_')[0]
    # Handle gic suffix in SLC names: slvaf-gic → slvaf-gic (skip GIC files since no MATLAB NC)
    if varname not in SLC_VARS and varname.split('-')[0] not in SLC_VARS:
        varname = basename[:basename.index('_')]
    stem = basename[len(varname) + 1:]     # AIS_ISMIP7_..._2014-2300.nc

    # Match the MATLAB file by the same sub-path relative to its output root, so
    # separate --py-outpath / --mat-outpath nested trees line up; fall back to a
    # basename search (covers the flat layout and mixed trees).
    rel = os.path.relpath(py_path, py_dir)
    mat_path = os.path.join(mat_dir, rel)
    if not os.path.exists(mat_path):
        cand = glob.glob(os.path.join(mat_dir, '**', basename), recursive=True)
        mat_path = cand[0] if cand else mat_path
    if not os.path.exists(mat_path):
        print(f'MISSING MATLAB: {rel}')
        fail = True
        continue

    ds_py  = nc.Dataset(py_path,  'r')
    ds_mat = nc.Dataset(mat_path, 'r')

    # Variable name inside the NC matches the file prefix (strip -gic suffix if present)
    nc_varname = varname.split('-')[0]

    if nc_varname not in ds_py.variables:
        print(f'SKIP (variable {nc_varname!r} not found in {basename})')
        ds_py.close(); ds_mat.close()
        continue

    py_data  = np.array(ds_py.variables[nc_varname][:])
    mat_data = np.array(ds_mat.variables[nc_varname][:])

    diff     = np.abs(py_data - mat_data)
    max_diff = float(diff.max())
    rms_diff = float(np.sqrt(np.mean(diff**2)))
    scale    = float(np.max(np.abs(py_data)))
    rel_diff = max_diff / scale if scale > 0 else 0.0

    if nc_varname in SLC_VARS:
        var_ok = max_diff < ABS_TOL
    else:
        var_ok = rel_diff < REL_TOL

    bounds_ok = check_time_bounds(ds_py, ds_mat, REL_TOL)
    attrs_ok  = check_global_attrs(ds_py, ds_mat)
    ds_py.close()
    ds_mat.close()

    ok = var_ok and bounds_ok and attrs_ok

    status = 'OK' if ok else 'FAIL'
    if not ok:
        fail = True
    max_diff_global = max(max_diff_global, max_diff)

    stem_short = stem[:-3]  # strip .nc
    print(f'{varname:<20}  {stem_short:<50}  '
          f'{max_diff:>14.3e}  {rms_diff:>14.3e}  {rel_diff:>10.2e}  {status}')

print('-' * len(hdr))
print(f'Max absolute difference across all variables: {max_diff_global:.3e}')
print()
if fail:
    print('RESULT: DIFFERENCES EXCEED TOLERANCE or files missing')
    sys.exit(1)
else:
    print('RESULT: All outputs match within tolerance')
    sys.exit(0)
