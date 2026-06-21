#!/usr/bin/env python3
"""Fast basin-definition test: checks that basin/region masks partition the model domain.

Loads static data files only (basin masks, area factors, maxmask) — no model output
or scalars.py run needed. Checks that the sum of area-weighted basin integrals equals
the whole-ice-sheet (mm) integral.

For AIS:
  - 3 regions (wais, eais, pina) must sum to mm
  - 18 basins (r01..r18) must sum to mm
For GrIS:
  - 7 Mouginot basins (no, ne, ce, se, sw, cw, nw) must sum to mm

Tolerance: 1e-10 (relative, fraction of mm total).

Usage (run from manual-tests/ or any directory):
    python test_basins.py --datapath-ais <path> --modelpath-ais <path> \\
                          --datapath-gris <path> --modelpath-gris <path>
"""

import sys
import os
import argparse
import netCDF4 as nc
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("--region",        choices=["AIS", "GrIS"], default=None,
                    help="Run for one region only (default: both)")
parser.add_argument("--datapath-ais",  default=None)
parser.add_argument("--datapath-gris", default=None)
parser.add_argument("--res",           default="08")
args = parser.parse_args()

regions_to_run = ([args.region] if args.region
                  else ["AIS", "GrIS"])

if "AIS"  in regions_to_run and not args.datapath_ais:
    parser.error("--datapath-ais is required when testing AIS")
if "GrIS" in regions_to_run and not args.datapath_gris:
    parser.error("--datapath-gris is required when testing GrIS")

TOL = 1e-6  # relative tolerance (edge cells with af2>0 but outside all basins contribute ~1e-7)

fail = False


def check(label, cond, detail=""):
    global fail
    status = "OK" if cond else "FAIL"
    if not cond:
        fail = True
    print(f"  {label}: {status}" + (f"  ({detail})" if detail else ""))


def weighted_sum(mask, af2):
    return np.sum(mask * af2)


def test_basin_sums(region, datapath, res):
    print(f"\n{region}")

    # Static data files
    if region == "AIS":
        af2file   = os.path.join(datapath, f"af2_AIS_{res}000m_v1.nc")
        basinfile = os.path.join(datapath, f"basins_regions_AIS_Rignot_extended_{res}000m_v1.nc")
    else:
        af2file   = os.path.join(datapath, f"af2_GrIS_{res}000m_v1.nc")
        basinfile = os.path.join(datapath, f"basins_GrIS_Mouginot_extended_{res}000m_v1.nc")

    ds = nc.Dataset(af2file); af2 = np.array(ds.variables["af2"][:]); ds.close()
    # In scalars.py, regions.mm = sheet = all-ones (entire grid); af2 provides the masking.
    # So the mm reference is simply sum(af2).
    ref = np.sum(af2)
    print(f"  mm area (sum af2): {ref:.6e} m²")

    ds = nc.Dataset(basinfile)

    if region == "AIS":
        regionid = np.array(ds.variables["regions"][:])
        basinid  = np.array(ds.variables["basins"][:])
        ds.close()

        total_3  = sum(weighted_sum((regionid == i).astype(float), af2) for i in range(1, 4))
        total_18 = sum(weighted_sum((basinid  == i).astype(float), af2) for i in range(1, 19))

        rel3  = abs(total_3  - ref) / (abs(ref) + 1e-30)
        rel18 = abs(total_18 - ref) / (abs(ref) + 1e-30)
        check("3 regions (wais+eais+pina) sum == mm", rel3  < TOL, f"rel diff = {rel3:.3e}")
        check("18 basins (r01..r18) sum  == mm",      rel18 < TOL, f"rel diff = {rel18:.3e}")

    else:  # GrIS
        basinid = np.array(ds.variables["basins"][:])
        ds.close()

        total_7 = sum(weighted_sum((basinid == i).astype(float), af2) for i in range(1, 8))
        rel7 = abs(total_7 - ref) / (abs(ref) + 1e-30)
        check("7 basins (no+ne+ce+se+sw+cw+nw) sum == mm", rel7 < TOL, f"rel diff = {rel7:.3e}")


datapaths = {"AIS": args.datapath_ais, "GrIS": args.datapath_gris}
for region in regions_to_run:
    test_basin_sums(region, datapaths[region], args.res)

print()
if fail:
    print("RESULT: FAIL")
    sys.exit(1)
else:
    print("RESULT: PASS")
