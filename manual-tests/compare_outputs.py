#!/usr/bin/env python3
"""Compare MATLAB and Python scalar output files.
Run from manual-tests/ after both versions have produced output.

Output files follow the naming: {varname}_{regionmask}_{stem}.nc
where varname is slvaf, slg20, or sla20, and stem contains the full ISMIP7 fields.

Python output: ../python/output/{varname}_*.nc
MATLAB output: ../matlab/output/{varname}_*.nc

Usage:
    python compare_outputs.py               # compare all output files
    python compare_outputs.py --region AIS  # compare only AIS files
    python compare_outputs.py --region GrIS # compare only GrIS files
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
args = parser.parse_args()

VARS    = ['slvaf', 'slg20', 'sla20']
TOL     = 1e-10  # absolute tolerance in metres
py_dir  = '../python/output'
mat_dir = '../matlab/output'

# Find Python output files for one varname, optionally filtered by region
py_files = sorted(glob.glob(os.path.join(py_dir, 'slvaf_*.nc')))
if args.region:
    py_files = [f for f in py_files if f'_{args.region}_' in os.path.basename(f)]
if not py_files:
    print(f'No Python output files found in {py_dir}')
    sys.exit(1)

max_diff_global = 0.0
fail = False

print(f'{"Variable":<8}  {"Mask":<6}  {"Stem":<55}  {"MaxAbsDiff":>14}  {"RMS":>14}  Status')
print('-' * 115)

for py_slvaf in py_files:
    basename = os.path.basename(py_slvaf)          # slvaf_mm_AIS_..._2014-2300.nc
    stem = basename[len('slvaf_'):]                # mm_AIS_..._2014-2300.nc
    mask = stem.split('_')[0]                      # mm

    for var in VARS:
        py_file  = os.path.join(py_dir,  f'{var}_{stem}')
        mat_file = os.path.join(mat_dir, f'{var}_{stem}')

        if not os.path.exists(py_file):
            print(f'MISSING Python file: {py_file}')
            fail = True
            continue
        if not os.path.exists(mat_file):
            print(f'MISSING MATLAB file: {mat_file}')
            fail = True
            continue

        ds_py  = nc.Dataset(py_file,  'r')
        ds_mat = nc.Dataset(mat_file, 'r')

        py_data  = np.array(ds_py.variables[var][:])
        mat_data = np.array(ds_mat.variables[var][:])
        ds_py.close()
        ds_mat.close()

        diff = np.abs(py_data - mat_data)
        max_diff = diff.max()
        rms_diff = np.sqrt(np.mean(diff**2))
        max_diff_global = max(max_diff_global, max_diff)

        status = 'OK' if max_diff < TOL else 'FAIL'
        if status == 'FAIL':
            fail = True
        print(f'{var:<8}  {mask:<6}  {stem[len(mask)+1:-3]:<55}  {max_diff:>14.3e}  {rms_diff:>14.3e}  {status}')

print('-' * 115)
print(f'Max absolute difference across all variables: {max_diff_global:.3e} m')
print(f'Tolerance: {TOL:.3e} m')
print()
if fail:
    print('RESULT: DIFFERENCES EXCEED TOLERANCE or files missing')
    sys.exit(1)
else:
    print('RESULT: All outputs match within tolerance')
    sys.exit(0)
