# Derive a new MINI experiment from exp0 with frozen bedrock topg
# topg is set constant at its t=0 state; sftgrf/sftflf are recomputed
# from the floatation criterion using the frozen bed.
# Heiko Goelzer 2026 (heig@norceresearch.no)

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..'))

import argparse
import datetime
import numpy as np
import netCDF4 as nc
from slc.sl_constants import RHOI, RHOSW

parser = argparse.ArgumentParser(
    description="Derive MINI experiment from exp0 with frozen bedrock")
parser.add_argument("--model", required=True, choices=["MINI0", "MINI1"],
                    help="MINI variant")
parser.add_argument("--exp",   required=True,
                    help="Output experiment name (e.g. expc)")
args = parser.parse_args()

model = args.model
exp   = args.exp

srcpath = os.path.join("..", "..", "Models", "MINI", "ISMIP7", model, "exp0")
dstpath = os.path.join("..", "..", "Models", "MINI", "ISMIP7", model, exp)
os.makedirs(dstpath, exist_ok=True)

lab = "ISMIP7"
region = "AIS"
suffix_src = f"{region}_{lab}_{model}_exp0"
suffix_dst = f"{region}_{lab}_{model}_{exp}"

history_note = (
    f"{datetime.datetime.utcnow().strftime('%a %b %d %H:%M:%S %Y')}: "
    f"derive_exp0.py --model {model} --exp {exp}: "
    f"topg frozen at t=0; sftgrf/sftflf recomputed from floatation criterion"
)


def copy_dims(src, dst):
    for name, dim in src.dimensions.items():
        dst.createDimension(name, None if dim.isunlimited() else len(dim))


def copy_coord_var(src, dst, varname):
    if varname not in src.variables:
        return
    sv = src.variables[varname]
    dv = dst.createVariable(varname, sv.dtype, sv.dimensions)
    dv[:] = sv[:]
    for attr in sv.ncattrs():
        setattr(dv, attr, getattr(sv, attr))


def copy_global_attrs(src, dst, extra_history=""):
    for attr in src.ncattrs():
        val = getattr(src, attr)
        if attr == "history" and extra_history:
            val = extra_history + "\n" + val
        setattr(dst, attr, val)


def open_src(varname):
    path = os.path.join(srcpath, f"{varname}_{suffix_src}.nc")
    return nc.Dataset(path, "r")


def create_dst(varname):
    path = os.path.join(dstpath, f"{varname}_{suffix_dst}.nc")
    return nc.Dataset(path, "w", format="NETCDF4_CLASSIC")


# ── load source data ──────────────────────────────────────────────────────────

src_topg  = open_src("topg")
src_lithk = open_src("lithk")
src_gif   = open_src("sftgif")
src_grf   = open_src("sftgrf")
src_flf   = open_src("sftflf")

topg  = src_topg.variables["topg"][:]
lithk = src_lithk.variables["lithk"][:]
gif   = src_gif.variables["sftgif"][:]

nt = topg.shape[0]

# freeze bedrock: all time steps equal t=0
topg_frozen = np.empty_like(topg)
for t in range(nt):
    topg_frozen[t] = topg[0]

# recompute grounding masks from floatation criterion (S=0)
topg0 = topg[0]
grf_new = np.zeros_like(gif)
flf_new = np.zeros_like(gif)
for t in range(nt):
    ice = gif[t] == 1
    grounded = ice & (lithk[t] > -topg0 * RHOSW / RHOI)
    grf_new[t] = grounded.astype(np.float32)
    flf_new[t] = (ice & ~grounded).astype(np.float32)

# ── write topg ────────────────────────────────────────────────────────────────

dst = create_dst("topg")
copy_dims(src_topg, dst)
copy_global_attrs(src_topg, dst, extra_history=history_note)
for cv in ("x", "y", "time", "time_bounds"):
    copy_coord_var(src_topg, dst, cv)
sv = src_topg.variables["topg"]
dv = dst.createVariable("topg", sv.dtype, sv.dimensions)
for attr in sv.ncattrs():
    setattr(dv, attr, getattr(sv, attr))
dv[:] = topg_frozen
dst.close()
print(f"Written topg_{suffix_dst}.nc")

# ── write lithk (unchanged data) ─────────────────────────────────────────────

dst = create_dst("lithk")
copy_dims(src_lithk, dst)
copy_global_attrs(src_lithk, dst, extra_history=history_note)
for cv in ("x", "y", "time", "time_bounds"):
    copy_coord_var(src_lithk, dst, cv)
sv = src_lithk.variables["lithk"]
dv = dst.createVariable("lithk", sv.dtype, sv.dimensions)
for attr in sv.ncattrs():
    setattr(dv, attr, getattr(sv, attr))
dv[:] = sv[:]
dst.close()
print(f"Written lithk_{suffix_dst}.nc")

# ── write sftgif (unchanged data) ────────────────────────────────────────────

dst = create_dst("sftgif")
copy_dims(src_gif, dst)
copy_global_attrs(src_gif, dst, extra_history=history_note)
for cv in ("x", "y", "time", "time_bounds"):
    copy_coord_var(src_gif, dst, cv)
sv = src_gif.variables["sftgif"]
dv = dst.createVariable("sftgif", sv.dtype, sv.dimensions)
for attr in sv.ncattrs():
    setattr(dv, attr, getattr(sv, attr))
dv[:] = sv[:]
dst.close()
print(f"Written sftgif_{suffix_dst}.nc")

# ── write sftgrf (recomputed) ─────────────────────────────────────────────────

dst = create_dst("sftgrf")
copy_dims(src_grf, dst)
copy_global_attrs(src_grf, dst, extra_history=history_note)
for cv in ("x", "y", "time"):
    copy_coord_var(src_grf, dst, cv)
sv = src_grf.variables["sftgrf"]
dv = dst.createVariable("sftgrf", sv.dtype, sv.dimensions)
for attr in sv.ncattrs():
    setattr(dv, attr, getattr(sv, attr))
dv[:] = grf_new
dst.close()
print(f"Written sftgrf_{suffix_dst}.nc")

# ── write sftflf (recomputed) ─────────────────────────────────────────────────

dst = create_dst("sftflf")
copy_dims(src_flf, dst)
copy_global_attrs(src_flf, dst, extra_history=history_note)
for cv in ("x", "y", "time"):
    copy_coord_var(src_flf, dst, cv)
sv = src_flf.variables["sftflf"]
dv = dst.createVariable("sftflf", sv.dtype, sv.dimensions)
for attr in sv.ncattrs():
    setattr(dv, attr, getattr(sv, attr))
dv[:] = flf_new
dst.close()
print(f"Written sftflf_{suffix_dst}.nc")

# ── close sources ─────────────────────────────────────────────────────────────

for ds in (src_topg, src_lithk, src_gif, src_grf, src_flf):
    ds.close()

print("Done.")
