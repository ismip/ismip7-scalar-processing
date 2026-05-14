# Run scalars_MINI.py for all MINI variants and experiments, then print a summary
# Heiko Goelzer 2026 (heig@norceresearch.no)

import subprocess
import sys
import os
import netCDF4 as nc

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

models = ["MINI0", "MINI1"]
exps   = ["exp0", "expc", "expg"]

for exp in exps:
    for model in models:
        print(f"=== {model} / {exp} ===", flush=True)
        subprocess.run(
            [sys.executable, "scalars_MINI.py", "--model", model, "--exp", exp],
            check=True
        )

print("\n=== Summary ===")
model_rank = {m: i for i, m in enumerate(reversed(models))}
files = sorted(
    (f for f in os.listdir("output") if f.endswith(".nc")),
    key=lambda f: (f.split("_")[-1], model_rank.get(f.split("_")[-2], 99))
)
for f in files:
    ds = nc.Dataset(os.path.join("output", f))
    t   = ds.variables["time"][:]
    vaf  = ds.variables["slc_VAF"][:]
    g20  = ds.variables["slc_G2020"][:]
    a20  = ds.variables["slc_A2020"][:]
    vtot = ds.variables["slc_Vtot"][:]
    vgr  = ds.variables["slc_Vgr"][:]
    vfl  = ds.variables["slc_Vfl"][:]
    g0   = ds.variables["slc_G0"][:]
    print(f)
    print("  nt=%d  t=%.4f-%.4f %s" % (len(t), t[0], t[-1], ds.variables["time"].units))
    print("  VAF  : %.4f -> %.4f mm" % (vaf[0]*1000,  vaf[-1]*1000))
    print("  G2020: %.4f -> %.4f mm" % (g20[0]*1000,  g20[-1]*1000))
    print("  A2020: %.4f -> %.4f mm" % (a20[0]*1000,  a20[-1]*1000))
    print("  G0   : %.4f -> %.4f mm" % (g0[0]*1000,   g0[-1]*1000))
    print("  Vtot : %.4f -> %.4f mm" % (vtot[0]*1000, vtot[-1]*1000))
    print("  Vgr  : %.4f -> %.4f mm" % (vgr[0]*1000,  vgr[-1]*1000))
    print("  Vfl  : %.4f -> %.4f mm" % (vfl[0]*1000,  vfl[-1]*1000))
    ds.close()
