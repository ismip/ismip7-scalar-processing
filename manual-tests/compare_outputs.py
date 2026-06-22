#!/usr/bin/env python3
"""Compare MATLAB and Python scalar output files — all NC variables.

Discovers all Python NC files, matches by filename against MATLAB output,
and reports max absolute diff, RMS, and relative diff for each.

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
ABS_TOL  = 1e-10   # metres — applied to SLC variables
REL_TOL  = 1e-10   # applied to all other variables (relative to data max)

py_dir  = args.py_outpath
mat_dir = args.mat_outpath

# Discover all Python NC files (skip GIC NC files — Python doesn't write them by default)
py_files = sorted(glob.glob(os.path.join(py_dir, '*.nc')))
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

    mat_path = os.path.join(mat_dir, basename)
    if not os.path.exists(mat_path):
        print(f'MISSING MATLAB: {basename}')
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
    ds_py.close()
    ds_mat.close()

    diff     = np.abs(py_data - mat_data)
    max_diff = float(diff.max())
    rms_diff = float(np.sqrt(np.mean(diff**2)))
    scale    = float(np.max(np.abs(py_data)))
    rel_diff = max_diff / scale if scale > 0 else 0.0

    if nc_varname in SLC_VARS:
        ok = max_diff < ABS_TOL
    else:
        ok = rel_diff < REL_TOL

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
