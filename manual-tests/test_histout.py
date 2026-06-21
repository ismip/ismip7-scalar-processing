#!/usr/bin/env python3
"""Integration test for --histout: verifies output time-axis length for each mode.

Runs scalars.py four times (--histout 0, 1, -1, 9999) and checks:
  histout=0   -> pure exp output; earliest year = first exp year
  histout=1   -> exactly 1 extra year prepended; first VAF and A2020 values ~ 0
  histout=-1  -> all hist years prepended
  histout=9999 -> identical to -1; warning printed to stdout

Usage (run from manual-tests/ or any directory):
    python test_histout.py --datapath <path> --modelpath <path>

Optional overrides (defaults match VUW/PISM1/ssp585 AIS run):
    --region  AIS|GrIS   (default: AIS)
    --lab     <lab>      (default: VUW)
    --model   <model>    (default: PISM1)
    --exp     <exp>      (default: ssp585)
    --hist    <hist>     (default: historical)
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
parser.add_argument("--datapath",  required=True)
parser.add_argument("--modelpath", required=True)
args = parser.parse_args()

def run_scalars(histout, outdir):
    cmd = [sys.executable, SCRIPT,
           '--region',    args.region,
           '--group',     args.lab,
           '--model',     args.model,
           '--experiment', args.exp,
           '--hist',      args.hist,
           '--datapath',  args.datapath,
           '--modelpath', args.modelpath,
           '--outpath',   outdir,
           '--histout',   str(histout)]
    return subprocess.run(cmd, capture_output=True, text=True)

def read_output(outdir):
    nc_dir = os.path.join(outdir, 'nc')
    vaf_files = [f for f in os.listdir(nc_dir) if f.startswith('slvaf_') and f.endswith('.nc')]
    a20_files = [f for f in os.listdir(nc_dir) if f.startswith('sla20_') and f.endswith('.nc')]
    if not vaf_files:
        return None, None, None, None, None
    ds_v  = nc.Dataset(os.path.join(nc_dir, vaf_files[0]))
    ds_a  = nc.Dataset(os.path.join(nc_dir, a20_files[0]))
    t     = ds_v.variables['time'][:]
    dates = nc.num2date(t, ds_v.variables['time'].units, ds_v.variables['time'].calendar)
    vaf   = np.array(ds_v.variables['slvaf'][:])
    a20   = np.array(ds_a.variables['sla20'][:])
    ds_v.close(); ds_a.close()
    return len(t), dates[0].year, dates[-1].year, vaf, a20

fail = False
results = {}
tmpdir = tempfile.mkdtemp(prefix='test_histout_')

def check(label, cond, detail=''):
    global fail
    status = 'OK' if cond else 'FAIL'
    if not cond:
        fail = True
    print(f'  {label}: {status}' + (f'  ({detail})' if detail else ''))

try:
    for h in [0, 1, -1, 9999]:
        d = os.path.join(tmpdir, f'h{h}')
        os.makedirs(d)
        r = run_scalars(h, d)
        if r.returncode != 0:
            print(f'histout={h}: script error')
            print(r.stderr)
            fail = True
            continue
        nt, yr0, yr1, vaf, a20 = read_output(d)
        if nt is None:
            print(f'histout={h}: no output file')
            fail = True
            continue
        results[h] = (nt, yr0, yr1, vaf, a20, r.stdout)

    if 0 not in results:
        print('Cannot proceed: histout=0 run failed')
        sys.exit(1)

    nt0, yr0_0, yr1, vaf0, a20_0, _ = results[0]
    print(f'histout=0: nt={nt0}, years={yr0_0}..{yr1}')
    check('first value non-zero (no hist prepended)', abs(float(vaf0[0])) > 1e-9,
          f'VAF[0]={float(vaf0[0]):.2e}')

    if 1 in results:
        nt1, yr0_1, yr1_1, vaf1, a20_1, _ = results[1]
        print(f'histout=1: nt={nt1}, years={yr0_1}..{yr1_1}')
        check('nt = nt0 + 1', nt1 == nt0 + 1, f'{nt1} vs {nt0}+1')
        check('first year = first_exp_year - 1', yr0_1 == yr0_0 - 1, f'{yr0_1} vs {yr0_0-1}')
        check('VAF[0] ~ 0 (reference year)', abs(float(vaf1[0])) < 1e-9,
              f'{float(vaf1[0]):.2e}')
        check('A2020[0] ~ 0 (reference year)', abs(float(a20_1[0])) < 1e-9,
              f'{float(a20_1[0]):.2e}')

    if -1 in results:
        nt_all, yr0_all, yr1_all, _, _, _ = results[-1]
        print(f'histout=-1: nt={nt_all}, years={yr0_all}..{yr1_all}')
        check('more timesteps than histout=0', nt_all > nt0)

    if 9999 in results:
        nt9, yr0_9, yr1_9, _, _, stdout9 = results[9999]
        print(f'histout=9999: nt={nt9}, years={yr0_9}..{yr1_9}')
        check('identical to histout=-1', (nt9, yr0_9, yr1_9) == (nt_all, yr0_all, yr1_all))
        check('warning printed', 'Warning' in stdout9)

finally:
    shutil.rmtree(tmpdir, ignore_errors=True)

print()
if fail:
    print('RESULT: FAIL')
    sys.exit(1)
else:
    print('RESULT: PASS')
