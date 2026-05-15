#!/usr/bin/env python3
"""Compare MATLAB and Python scalar output files.
Run from manual-tests/ after both versions have produced output.

Python output: ../python/output/scalars_*.nc
MATLAB output: ../matlab/output/scalars_*.nc

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

VARS    = ['slc_VAF', 'slc_G2020', 'slc_A2020']
TOL     = 1e-10  # absolute tolerance in metres
py_dir  = '../python/output'
mat_dir = '../matlab/output'

# Find Python output files, optionally filtered by region
py_files = sorted(glob.glob(os.path.join(py_dir, 'scalars_*.nc')))
if args.region:
    py_files = [f for f in py_files if args.region in os.path.basename(f)]
if not py_files:
    print(f'No Python output files found in {py_dir}')
    sys.exit(1)

max_diff_global = 0.0
fail = False

print(f'{"Region":<10}  {"Variable":<12}  {"MaxAbsDiff":>14}  {"RMS":>14}  Status')
print('-' * 60)

for py_file in py_files:
    basename = os.path.basename(py_file)
    mat_file = os.path.join(mat_dir, basename)

    if not os.path.exists(mat_file):
        print(f'MISSING MATLAB file: {mat_file}')
        fail = True
        continue

    region = basename.split('_')[1]  # scalars_<region>_AIS_... or scalars_<region>_GrIS_...

    ds_py  = nc.Dataset(py_file,  'r')
    ds_mat = nc.Dataset(mat_file, 'r')

    for var in VARS:
        py_data  = np.array(ds_py.variables[var][:])
        mat_data = np.array(ds_mat.variables[var][:])

        diff = np.abs(py_data - mat_data)
        max_diff = diff.max()
        rms_diff = np.sqrt(np.mean(diff**2))
        max_diff_global = max(max_diff_global, max_diff)

        status = 'OK' if max_diff < TOL else 'FAIL'
        if status == 'FAIL':
            fail = True
        print(f'{region:<10}  {var:<12}  {max_diff:>14.3e}  {rms_diff:>14.3e}  {status}')

    ds_py.close()
    ds_mat.close()

print('-' * 60)
print(f'Max absolute difference across all variables: {max_diff_global:.3e} m')
print(f'Tolerance: {TOL:.3e} m')
print()
if fail:
    print('RESULT: DIFFERENCES EXCEED TOLERANCE or files missing')
    sys.exit(1)
else:
    print('RESULT: All outputs match within tolerance')
    sys.exit(0)
