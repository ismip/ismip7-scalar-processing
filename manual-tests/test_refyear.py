#!/usr/bin/env python3
"""Integration test for --refyear: verifies SLC = 0 at the specified reference year.

Runs scalars.py with --refyear 2050 and checks:
  - year 2050 is present in the output time axis
  - slc_VAF and slc_A2020 at year 2050 are < 1e-9 m in absolute value
  - values before 2050 are negative (ice less melted than at 2050 reference)
  - values after 2050 are positive (ice loss continues)
  - a "not found in hist" warning is printed (2050 falls in the projection period)

Usage (run from manual-tests/ or any directory):
    python test_refyear.py --datapath <path> --modelpath <path>

Optional overrides (defaults match VUW/PISM1/ssp585 AIS run):
    --region   AIS|GrIS   (default: AIS)
    --lab      <lab>      (default: VUW)
    --model    <model>    (default: PISM1)
    --exp      <exp>      (default: ssp585)
    --hist     <hist>     (default: historical)
    --refyear  <year>     (default: 2050)
"""

import sys
import os
import tempfile
import shutil
import subprocess
import argparse
import netCDF4 as nc
import numpy as np

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../python/scalars.py')

parser = argparse.ArgumentParser()
parser.add_argument("--region",    default="AIS")
parser.add_argument("--lab",       default="VUW")
parser.add_argument("--model",     default="PISM1")
parser.add_argument("--exp",       default="ssp585")
parser.add_argument("--hist",      default="historical")
parser.add_argument("--refyear",   type=int, default=2050)
parser.add_argument("--datapath",  required=True)
parser.add_argument("--modelpath", required=True)
args = parser.parse_args()

fail = False
tmpdir = tempfile.mkdtemp(prefix='test_refyear_')

def check(label, cond, detail=''):
    global fail
    status = 'OK' if cond else 'FAIL'
    if not cond:
        fail = True
    print(f'  {label}: {status}' + (f'  ({detail})' if detail else ''))

try:
    cmd = [sys.executable, SCRIPT,
           '--region',     args.region,
           '--group',      args.lab,
           '--model',      args.model,
           '--experiment', args.exp,
           '--hist',       args.hist,
           '--refyear',    str(args.refyear),
           '--datapath',   args.datapath,
           '--modelpath',  args.modelpath,
           '--outpath',    tmpdir]
    r = subprocess.run(cmd, capture_output=True, text=True)

    if r.returncode != 0:
        print(f'Script failed:\n{r.stderr}')
        sys.exit(1)

    nc_dir = os.path.join(tmpdir, 'nc')
    vaf_files = [f for f in os.listdir(nc_dir) if f.startswith('slvaf_') and f.endswith('.nc')]
    a20_files = [f for f in os.listdir(nc_dir) if f.startswith('sla20_') and f.endswith('.nc')]
    if not vaf_files:
        print('No output file found')
        sys.exit(1)

    ds_v  = nc.Dataset(os.path.join(nc_dir, vaf_files[0]))
    ds_a  = nc.Dataset(os.path.join(nc_dir, a20_files[0]))
    t     = ds_v.variables['time'][:]
    dates = nc.num2date(t, ds_v.variables['time'].units, ds_v.variables['time'].calendar)
    years = np.array([d.year for d in dates])
    vaf   = np.array(ds_v.variables['slvaf'][:])
    a20   = np.array(ds_a.variables['sla20'][:])
    ds_v.close(); ds_a.close()

    ref_idx = np.where(years == args.refyear)[0]
    print(f'refyear={args.refyear}: nt={len(t)}, years={years[0]}..{years[-1]}')

    check('refyear present in time axis', len(ref_idx) > 0)

    if len(ref_idx) > 0:
        ri = ref_idx[-1]
        check(f'VAF[{args.refyear}] ~ 0', abs(float(vaf[ri])) < 1e-9,
              f'{float(vaf[ri]):.2e} m')
        check(f'A2020[{args.refyear}] ~ 0', abs(float(a20[ri])) < 1e-9,
              f'{float(a20[ri]):.2e} m')

        if ri > 0:
            check('values before refyear are negative', float(vaf[0]) < 0,
                  f'VAF[0]={float(vaf[0]):.4f} m')
        if ri < len(t) - 1:
            check('values after refyear are positive', float(vaf[-1]) > 0,
                  f'VAF[-1]={float(vaf[-1]):.4f} m')

    check('warning: refyear not in hist', 'not found in hist' in r.stdout)

finally:
    shutil.rmtree(tmpdir, ignore_errors=True)

print()
if fail:
    print('RESULT: FAIL')
    sys.exit(1)
else:
    print('RESULT: PASS')
