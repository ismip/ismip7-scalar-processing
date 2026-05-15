#!/usr/bin/env python3
"""Smoke test for the MINI test suite.

Verifies that scalars_MINI.py, run_MINI.py, and the setup/ scripts
all resolve their paths correctly after the manual-tests/ reorganisation.

Usage (run from manual-tests/ or any directory):
    python test_mini.py
"""

import sys
import os
import subprocess
import netCDF4 as nc
import numpy as np

MINI_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'MINI')
SETUP_DIR = os.path.join(MINI_DIR, 'setup')

fail = False

def check(label, cond, detail=''):
    global fail
    status = 'OK' if cond else 'FAIL'
    if not cond:
        fail = True
    print(f'  {label}: {status}' + (f'  ({detail})' if detail else ''))

# ---- 1. run_MINI.py (all 4 combinations) ------------------------------------
print('run_MINI.py (MINI0/MINI1 × exp0/expg):')
r = subprocess.run([sys.executable, 'run_MINI.py'],
                   capture_output=True, text=True, cwd=MINI_DIR)
check('exit code 0', r.returncode == 0,
      r.stderr.strip()[:120] if r.returncode else '')

if r.returncode == 0:
    outdir = os.path.join(MINI_DIR, 'output')
    for exp in ['exp0', 'expg']:
        for model in ['MINI1', 'MINI0']:
            fname = f'scalars_mm_AIS_ISMIP7_{model}_{exp}.nc'
            fpath = os.path.join(outdir, fname)
            exists = os.path.exists(fpath)
            check(f'{fname} created', exists)
            if exists:
                ds  = nc.Dataset(fpath)
                vaf = np.array(ds.variables['slc_VAF'][:])
                ds.close()
                check(f'  non-zero VAF', float(vaf[-1]) != 0.0,
                      f'{float(vaf[-1]*1000):.2f} mm')

# ---- 2. check_masks.py (MINI1/exp0) ----------------------------------------
print('check_masks.py (MINI1/exp0):')
r = subprocess.run(
    [sys.executable, 'check_masks.py', '--model', 'MINI1', '--exp', 'exp0'],
    capture_output=True, text=True, cwd=SETUP_DIR)
check('exit code 0', r.returncode == 0)
check('all checks passed', 'All checks passed.' in r.stdout,
      (r.stdout + r.stderr).strip()[-80:])

# ---- 3. derive_exp0.py import (--help) --------------------------------------
print('derive_exp0.py (slc import check):')
r = subprocess.run([sys.executable, 'derive_exp0.py', '--help'],
                   capture_output=True, text=True, cwd=SETUP_DIR)
check('--help exits 0', r.returncode == 0,
      r.stderr.strip()[:80] if r.returncode else '')

print()
if fail:
    print('RESULT: FAIL')
    sys.exit(1)
else:
    print('RESULT: PASS')
