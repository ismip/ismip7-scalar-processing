# Calculate scalar variables from ISMIP7 3D model output - MINI test case
# Heiko Goelzer 2026 (heig@norceresearch.no)

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../python'))

import argparse
import netCDF4 as nc
import numpy as np
from types import SimpleNamespace

from slc import slc_vaf
from slc import slc_G2020
from slc import slc_A2020
from slc.sl_constants import RHOI, RHOSW, RHOFW, AO

# Data file naming
FILE_CONFIG = {
    "af2":    "af2_{model}_vCDO.nc",
    "maxmask":"maxmask1_{model}_v0.nc",
    "gic":    "iaf2_{model}_v0.nc",
}

# User settings
parser = argparse.ArgumentParser(description="ISMIP7 MINI scalar processing")
parser.add_argument("--lab",       default="ISMIP7",               help="Lab identifier")
parser.add_argument("--model",     required=True, choices=["MINI0", "MINI1"],
                                                                    help="MINI variant (MINI0 or MINI1)")
parser.add_argument("--exp",       required=True,                  help="Experiment name (e.g. exp0, expg)")
parser.add_argument("--ref",       default=None,                   help="Reference experiment; if omitted, uses first timestep of exp")
parser.add_argument("--refyear",   type=int, default=None,         help="Year to use as SLC reference (default: last timestep of ref experiment)")
parser.add_argument("--res",       default=None,                   help="Resolution (not used in MINI file naming)")
parser.add_argument("--datapath",  default=None,                   help="Path to generic data (default: ../../Data/<model>)")
parser.add_argument("--modelpath", default=None,                   help="Path to model output (default: ../../Models/MINI/ISMIP7/<model>)")
parser.add_argument("--outpath",   default="./output",             help="Path for output scalar files")
args = parser.parse_args()

lab       = args.lab
model     = args.model
exp       = args.exp
datapath  = args.datapath  if args.datapath  else "../../Data/" + model
modelpath = args.modelpath if args.modelpath else "../../Models/MINI/ISMIP7/" + model
outpath   = args.outpath
## What output to produce
flg_mm = True   # Integrals on model mask
flg_bm = False  # IMBIE3 basins

# Description for netcdf global
file_description = "ISMIP7 scalar output. Heiko Goelzer 2026, heig@norceresearch.no"

# Options
# Remove GIC contribution
flg_GICmask = True  # [Default True!]

# A2020: stepwise cumulative (True, default) vs. all relative to reference (False)
flg_A20_cumul = True

# More output
verbose = False

# Pixel size for area weighting
dx = 600000.0  # m (600 km)

################################################################
# File names and mapping

cfg      = FILE_CONFIG
af2input = datapath + "/" + cfg["af2"].format(model=model)
mminput  = datapath + "/" + cfg["maxmask"].format(model=model)
gicinput = datapath + "/" + cfg["gic"].format(model=model)
file_suffix = "AIS_" + lab + "_" + model + "_" + exp + ".nc"

####################################################
# Prepare generic data file

# Defined ocean area
oarea = AO  # m2 (Gregory et al., 2019)

# Prepare ice sheet mask
idat = nc.Dataset(mminput, 'r')
maxmask1 = idat.variables["maxmask1"][:,:]
idat.close()
sheet = maxmask1 * 0 + 1  # sheet region covers the entire grid
regions = SimpleNamespace()
regions.mm = sheet

# Prepare area factors
idat = nc.Dataset(af2input, 'r')
af2 = idat.variables["af2"][:,:]
idat.close()
# include GIC masking if requested
if flg_GICmask:
    idat = nc.Dataset(gicinput, 'r')
    iaf2GIC = idat.variables["iaf2"][:,:]
    idat.close()

###########################################################
# Prepare model output

exppath = modelpath + "/" + exp
# Model geometry
idat = nc.Dataset(exppath + "/lithk_AIS_" + lab + "_" + model + "_" + exp + ".nc", 'r')
lithk = idat.variables["lithk"][:,:,:]
# Pick up time axis
time_model     = idat.variables["time"][:]
time_units     = idat.variables["time"].units
time_long_name = idat.variables["time"].long_name
time_calendar  = idat.variables["time"].calendar
idat.close()
idat = nc.Dataset(exppath + "/topg_AIS_" + lab + "_" + model + "_" + exp + ".nc", 'r')
topg = idat.variables["topg"][:,:,:]
idat.close()

# Reference experiment
if args.ref:
    refpath = modelpath + "/" + args.ref
    idat = nc.Dataset(refpath + "/lithk_AIS_" + lab + "_" + model + "_" + args.ref + ".nc", 'r')
    if args.refyear is not None:
        time_ref = idat.variables["time"]
        dates = nc.num2date(time_ref[:], time_ref.units, calendar=time_ref.calendar)
        ref_idx = int(np.where(np.array([d.year for d in dates]) == args.refyear)[0][-1])
    else:
        ref_idx = -1
    lithk_ref = idat.variables["lithk"][ref_idx, :, :]
    idat.close()
    idat = nc.Dataset(refpath + "/topg_AIS_" + lab + "_" + model + "_" + args.ref + ".nc", 'r')
    topg_ref = idat.variables["topg"][ref_idx, :, :]
    idat.close()
else:
    # No separate reference — use first time step of exp
    lithk_ref = lithk[0, :, :]
    topg_ref  = topg[0,  :, :]

# Physical constants from sl_constants (no params.nc for MINI)
c = SimpleNamespace()
c.RHOI  = RHOI   # kg/m3
c.RHOSW = RHOSW  # kg/m3
c.RHOFW = RHOFW  # kg/m3
c.AO    = oarea  # m2

# Model masks (loaded for completeness, not used in SLC computation)
idat = nc.Dataset(exppath + "/sftgif_AIS_" + lab + "_" + model + "_" + exp + ".nc", 'r')
sftgif = idat.variables["sftgif"][:,:,:]
idat.close()
idat = nc.Dataset(exppath + "/sftgrf_AIS_" + lab + "_" + model + "_" + exp + ".nc", 'r')
sftgrf = idat.variables["sftgrf"][:,:,:]
idat.close()
idat = nc.Dataset(exppath + "/sftflf_AIS_" + lab + "_" + model + "_" + exp + ".nc", 'r')
sftflf = idat.variables["sftflf"][:,:,:]
idat.close()

#######################################
# See what we have

if verbose:
    print("# Generic")
    print("af2:", af2.shape)
    print("maxmask1:", maxmask1.shape)
    if flg_GICmask:
        print("iaf2GIC:", iaf2GIC.shape)
    print("# Model")
    print("lithk_ref:", lithk_ref.shape)
    print("topg_ref:", topg_ref.shape)
    print("lithk:", lithk.shape)
    print("topg:", topg.shape)
    print("sftgif:", sftgif.shape)
    print("sftgrf:", sftgrf.shape)
    print("sftflf:", sftflf.shape)

#############################################################
# Ice sheet wide integrals

for regionName, region_mask in vars(regions).items():
    print(f"{regionName}")

    VAF_list  = []
    G20_list  = []
    A20_list  = []
    Vtot_list = []
    Vgr_list  = []
    Vfl_list  = []

    # Reference state
    H0 = lithk_ref * maxmask1 * iaf2GIC
    B0 = topg_ref
    S0 = topg_ref * 0.0  # Fix sealevel to 0

    # Use A for weighting and region masking
    A = region_mask * af2 * dx**2

    nt = len(lithk)

    # time loop
    if flg_A20_cumul:
        H_prev = H0.copy()
        B_prev = B0.copy()
        S_prev = S0.copy()
        A20_cumsum = 0.0

    for n in range(0, nt):

        H = lithk[n,:,:] * maxmask1 * iaf2GIC
        B = topg[n,:,:]

        VAF_list.append(slc_vaf.get_slc_vaf(H0, H, B0, B, S0, S0, A, c))
        G20_list.append(slc_G2020.get_slc_G2020(H0, H, B0, B, A, c))
        if flg_A20_cumul:
            A20_cumsum += slc_A2020.get_slc_A2020(H_prev, H, B_prev, B, S_prev, S_prev, A, c)
            A20_list.append(A20_cumsum)
            H_prev = H.copy()
            B_prev = B.copy()
            S_prev = S_prev  # sea level fixed at 0, no update needed
        else:
            # A2020 relative to reference state, like G2020 and VAF
            A20_list.append(slc_A2020.get_slc_A2020(H0, H, B0, B, S0, S0, A, c))
        Vtot_list.append(slc_vaf.get_slc_vtot(H0, H, A, c))
        Vgr_list.append(slc_vaf.get_slc_vgr(H0, H, B0, B, S0, S0, A, c))
        Vfl_list.append(slc_vaf.get_slc_vfl(H0, H, B0, B, S0, S0, A, c))

    sl_VAF  = np.array(VAF_list)
    sl_G20  = np.array(G20_list)
    sl_A20  = np.array(A20_list)
    sl_Vtot = np.array(Vtot_list)
    sl_Vgr  = np.array(Vgr_list)
    sl_Vfl  = np.array(Vfl_list)

    if verbose:
        print(sl_VAF)
        print(sl_G20)
        print(sl_A20)
        print(sl_Vtot)
        print(sl_Vgr)
        print(sl_Vfl)

    ###############################################
    # Write netcdf file

    scfile = outpath + "/scalars_" + regionName + "_" + file_suffix
    ds = nc.Dataset(scfile, 'w', format='NETCDF4')
    ds.createDimension('time', None)
    # Variables
    var_time  = ds.createVariable('time',     'float', ('time'), zlib=True)
    var_VAF   = ds.createVariable('slc_VAF',  'float', ('time'), zlib=True)
    var_G2020 = ds.createVariable('slc_G2020','float', ('time'), zlib=True)
    var_A2020 = ds.createVariable('slc_A2020','float', ('time'), zlib=True)
    var_Vtot  = ds.createVariable('slc_Vtot', 'float', ('time'), zlib=True)
    var_Vgr   = ds.createVariable('slc_Vgr',  'float', ('time'), zlib=True)
    var_Vfl   = ds.createVariable('slc_Vfl',  'float', ('time'), zlib=True)
    # Attributes
    ds.description = file_description
    var_time.units     = time_units
    var_time.long_name = time_long_name
    var_time.calendar  = time_calendar
    var_VAF.long_name   = 'Sea level contribution based on Vaf'
    var_VAF.units       = 'm'
    var_G2020.long_name = 'Sea level contribution based on G2020'
    var_G2020.units     = 'm'
    var_A2020.long_name = 'Sea level contribution based on A2020'
    var_A2020.units     = 'm'
    var_Vtot.long_name  = 'Sea level contribution based on total ice volume change'
    var_Vtot.units      = 'm'
    var_Vgr.long_name   = 'Sea level contribution based on grounded ice volume change'
    var_Vgr.units       = 'm'
    var_Vfl.long_name   = 'Sea level contribution based on floating ice volume change'
    var_Vfl.units       = 'm'
    # assign data
    var_time[:]  = time_model
    var_VAF[:]   = sl_VAF[:]
    var_G2020[:] = sl_G20[:]
    var_A2020[:] = sl_A20[:]
    var_Vtot[:]  = sl_Vtot[:]
    var_Vgr[:]   = sl_Vgr[:]
    var_Vfl[:]   = sl_Vfl[:]

    ds.close()
    print("Created file ", scfile)
