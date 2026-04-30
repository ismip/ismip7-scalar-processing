#!/usr/bin/env python3
"""
Compare MATLAB and Python GrIS scalar output files.
Run from test/GrIS/ after both versions have produced output.

Python output: ../../GrIS/python/output/scalars_*_GrIS_*.nc
MATLAB output: ../../GrIS/matlab/output/scalars_*_GrIS_*.nc
"""

import sys
import os
import glob
import numpy as np
import netCDF4 as nc

VARS    = ['slc_VAF', 'slc_G2020', 'slc_A2020']
TOL     = 1e-10  # absolute tolerance in metres
py_dir  = '../../GrIS/python/output'
mat_dir = '../../GrIS/matlab/output'

# Find all Python output files
py_files = sorted(glob.glob(os.path.join(py_dir, 'scalars_*.nc')))
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

    region = basename.split('_')[1]  # scalars_<region>_GrIS_...

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
