# Check mask consistency for any MINI experiment:
#   - sftgrf + sftflf == sftgif at every cell and time step
#   - topg constant in time (optional check with --check-topg)
# Heiko Goelzer 2026 (heig@norceresearch.no)

import sys
import os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, '../../..'))

import argparse
import numpy as np
import netCDF4 as nc
from slc.sl_constants import RHOI, RHOSW

parser = argparse.ArgumentParser(description="Check MINI experiment mask consistency")
parser.add_argument("--model", required=True, choices=["MINI0", "MINI1"])
parser.add_argument("--exp",   required=True)
parser.add_argument("--check-topg", action="store_true",
                    help="Verify topg is identical at all time steps")
args = parser.parse_args()

model = args.model
exp   = args.exp
lab   = "ISMIP7"
region = "AIS"

exppath = os.path.join(SCRIPT_DIR, "..", "..", "..", "Models", "MINI", "ISMIP7", model, exp)
suffix  = f"{region}_{lab}_{model}_{exp}"

def load(varname):
    path = os.path.join(exppath, f"{varname}_{suffix}.nc")
    ds = nc.Dataset(path, "r")
    data = ds.variables[varname][:]
    ds.close()
    return data

topg  = load("topg")
lithk = load("lithk")
gif   = load("sftgif")
grf   = load("sftgrf")
flf   = load("sftflf")

nt = topg.shape[0]
ok = True

# mask consistency: sftgrf + sftflf == sftgif
for t in range(nt):
    match = np.all((grf[t] + flf[t]) == gif[t])
    status = "OK" if match else "FAIL"
    print(f"  sftgrf + sftflf == sftgif  t={t}: {status}")
    ok = ok and match

# floatation criterion consistency
topg0 = topg[0]
for t in range(nt):
    ice = gif[t] == 1
    grounded_expected = ice & (lithk[t] > -topg0 * RHOSW / RHOI)
    match_grf = np.all(grf[t] == grounded_expected.astype(np.float32))
    match_flf = np.all(flf[t] == (ice & ~grounded_expected).astype(np.float32))
    status = "OK" if (match_grf and match_flf) else "FAIL"
    print(f"  floatation criterion match t={t}: {status}")
    ok = ok and match_grf and match_flf

# optional: topg constant in time
if args.check_topg:
    for t in range(1, nt):
        const = np.allclose(topg[t], topg[0])
        status = "OK" if const else "FAIL"
        print(f"  topg[{t}] == topg[0]: {status}")
        ok = ok and const

print(f"\n{'All checks passed.' if ok else 'SOME CHECKS FAILED.'}")
sys.exit(0 if ok else 1)
