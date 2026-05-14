# Calculate scalar variables from ISMIP7 3D model output
# Heiko Goelzer 2026 (heig@norceresearch.no)

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

import argparse
import netCDF4 as nc
import numpy as np
from types import SimpleNamespace

from slc import slc_vaf
from slc import slc_G2020
from slc import slc_A2020

# Region-specific data file naming
FILE_CONFIG = {
    "AIS": {
        "af2":    "af2_AIS_{res}000m_v1.nc",
        "maxmask":"maxmask1_AIS_{res}000m_v0.nc",
        "gic":    "iaf2_GIC_AIS_{res}000m_v0.nc",
        "basins": "basins_regions_AIS_Rignot_extended_{res}000m_v1.nc",
    },
    "GrIS": {
        "af2":    "af2_GrIS_{res}000m_v1.nc",
        "maxmask":"maxmask1_GrIS_{res}000m_v1.nc",
        "gic":    "iaf2_GIC_GrIS_{res}000m_v0.nc",
        "basins": "basins_GrIS_Mouginot_extended_{res}000m_v1.nc",
    },
}

# Region-specific defaults
DEFAULTS = {
    "AIS":  {"lab": "VUW",   "model": "PISM1",             "exp": "expAE04"},
    "GrIS": {"lab": "NORCE", "model": "CISM08-MAR312-p50", "exp": "historical"},
}

# User settings
parser = argparse.ArgumentParser(description="ISMIP7 scalar processing")
parser.add_argument("--region",    required=True, choices=["AIS", "GrIS"],
                                                                   help="Ice sheet region")
parser.add_argument("--lab",       default=None,                   help="Lab identifier")
parser.add_argument("--model",     default=None,                   help="Model name")
parser.add_argument("--exp",       default=None,                   help="Experiment name")
parser.add_argument("--ref",       default="historical",           help="Reference experiment")
parser.add_argument("--refyear",   type=int, default=None,         help="Year to use as SLC reference (default: last timestep of ref experiment)")
parser.add_argument("--res",       default="08",                   help="Resolution (e.g. 08 for 8 km)")
parser.add_argument("--datapath",  default=None,                   help="Path to generic data files (default: ../Data/<region>)")
parser.add_argument("--modelpath", default=None,                   help="Path to model output (default: ../Models/<region>)")
parser.add_argument("--outpath",   default="./output",             help="Path for output scalar files")
args = parser.parse_args()

region    = args.region
lab       = args.lab       or DEFAULTS[region]["lab"]
model     = args.model     or DEFAULTS[region]["model"]
exp       = args.exp       or DEFAULTS[region]["exp"]
ref       = args.ref
res       = args.res
datapath  = args.datapath  if args.datapath  else "../Data/" + region
modelpath = args.modelpath if args.modelpath else "../Models/" + region
outpath   = args.outpath
## What output to produce
flg_mm = True  # Integrals on model mask
flg_bm = False  # IMBIE3 basins

# Description for netcdf global
file_description = "ISMIP7 scalar output. Heiko Goelzer 2026, heig@norceresearch.no"

# Options
## What masking to apply. If true, applied to all output
# Remove GIC contribution
flg_GICmask = True  # [Default True!]

# A2020: stepwise cumulative (True, default) vs. all relative to reference (False)
flg_A20_cumul = False

# More output
verbose = False

################################################################
# File names and mapping

cfg        = FILE_CONFIG[region]
af2input   = datapath + "/" + cfg["af2"].format(res=res)
mminput    = datapath + "/" + cfg["maxmask"].format(res=res)
gicinput   = datapath + "/" + cfg["gic"].format(res=res)
basininput = datapath + "/" + cfg["basins"].format(res=res)
file_suffix = region + "_" + lab + "_" + model + "_" + exp + "_" + res + "000m.nc"

####################################################
# Prepare generic data file

# Defined ocean area
oarea = 3.625e14  # m2 (Gregory et al., 2019)

# Prepare ice sheet mask
idat = nc.Dataset(mminput, 'r')
maxmask1 = idat.variables["maxmask1"][:,:]
idat.close()
sheet = maxmask1 * 0 + 1  # sheet region covers the entire grid
regions = SimpleNamespace()
regions.mm = sheet

# Prepare basin masks
if flg_bm:
    idat = nc.Dataset(basininput, 'r')
    if region == "AIS":
        # IMBIE3 regions: 1 West Antarctica, 2 East Antarctica, 3 Peninsula
        basinid = idat.variables["regions"][:,:]
        regions.wais = (basinid==1).astype(float)
        regions.eais = (basinid==2).astype(float)
        regions.pina = (basinid==3).astype(float)
        # IMBIE3 basins 1 to 18
        basinid = idat.variables["basins"][:,:]
        regions.r01 = (basinid== 1).astype(float)
        regions.r02 = (basinid== 2).astype(float)
        regions.r03 = (basinid== 3).astype(float)
        regions.r04 = (basinid== 4).astype(float)
        regions.r05 = (basinid== 5).astype(float)
        regions.r06 = (basinid== 6).astype(float)
        regions.r07 = (basinid== 7).astype(float)
        regions.r08 = (basinid== 8).astype(float)
        regions.r09 = (basinid== 9).astype(float)
        regions.r10 = (basinid==10).astype(float)
        regions.r11 = (basinid==11).astype(float)
        regions.r12 = (basinid==12).astype(float)
        regions.r13 = (basinid==13).astype(float)
        regions.r14 = (basinid==14).astype(float)
        regions.r15 = (basinid==15).astype(float)
        regions.r16 = (basinid==16).astype(float)
        regions.r17 = (basinid==17).astype(float)
        regions.r18 = (basinid==18).astype(float)
        idat.close()
        # Test no gaps
        sheettest = regions.wais + regions.eais + regions.pina
        nx, ny = regions.wais.shape
        if verbose:
            print(np.sum(sheet), np.sum(sheettest), nx*ny)
    elif region == "GrIS":
        # IMBIE3 Mouginot basins: From NO clockwise
        basinid = idat.variables["basins"][:,:]
        regions.no = (basinid==1).astype(float)
        regions.ne = (basinid==2).astype(float)
        regions.ce = (basinid==3).astype(float)
        regions.se = (basinid==4).astype(float)
        regions.sw = (basinid==5).astype(float)
        regions.cw = (basinid==6).astype(float)
        regions.nw = (basinid==7).astype(float)
        idat.close()
        # Test no gaps
        sheettest = regions.no + regions.ne + regions.ce + regions.se + regions.sw + regions.cw + regions.nw
        nx, ny = regions.no.shape
        if verbose:
            print(np.sum(sheet), np.sum(sheettest), nx*ny)

# Prepare area factors
idat = nc.Dataset(af2input, 'r')
af2  = idat.variables["af2"][:,:]
idat.close()
# include GIC masking if requested
if flg_GICmask:
    idat = nc.Dataset(gicinput, 'r')
    iaf2GIC = idat.variables["iaf2"][:,:]
    idat.close()

###########################################################
# Prepare model output

# Main experiment
exppath = modelpath + "/" + lab + "/" + model + "/" + exp + "_" + res
# Model geometry
idat = nc.Dataset(exppath + "/lithk_" + region + "_" + lab + "_" + model + "_" + exp + ".nc", 'r')
lithk = idat.variables["lithk"][:,:,:]
# Pick up time axis
time_model     = idat.variables["time"][:]
time_units     = idat.variables["time"].units
time_long_name = idat.variables["time"].long_name
time_calendar  = idat.variables["time"].calendar
idat.close()
idat = nc.Dataset(exppath + "/topg_" + region + "_" + lab + "_" + model + "_" + exp + ".nc", 'r')
topg = idat.variables["topg"][:,:,:]
idat.close()

# Reference experiment
refpath = modelpath + "/" + lab + "/" + model + "/" + ref + "_" + res
# Model geometry
idat = nc.Dataset(refpath + "/lithk_" + region + "_" + lab + "_" + model + "_" + ref + ".nc", 'r')
if args.refyear is not None:
    time_ref = idat.variables["time"]
    dates = nc.num2date(time_ref[:], time_ref.units, calendar=time_ref.calendar)
    ref_idx = int(np.where(np.array([d.year for d in dates]) == args.refyear)[0][-1])
else:
    ref_idx = -1
lithk_ref = idat.variables["lithk"][ref_idx,:,:]
idat.close()
idat = nc.Dataset(refpath + "/topg_" + region + "_" + lab + "_" + model + "_" + ref + ".nc", 'r')
topg_ref = idat.variables["topg"][ref_idx,:,:]
idat.close()

# Add model params
idat = nc.Dataset(modelpath + "/" + lab + "/" + model + "/params.nc", 'r')
scalar = idat.variables["rhoi"]; rhoi = scalar[()]
scalar = idat.variables["rhow"]; rhow = scalar[()]
scalar = idat.variables["rhof"]; rhof = scalar[()]
idat.close()
c = SimpleNamespace()
c.RHOI  = rhoi  # kg/m3
c.RHOSW = rhow  # kg/m3
c.RHOFW = rhof  # kg/m3
c.AO    = oarea  # m2

# Model masks
idat = nc.Dataset(exppath + "/sftgif_" + region + "_" + lab + "_" + model + "_" + exp + ".nc", 'r')
sftgif = idat.variables["sftgif"][:,:,:]
idat.close()
idat = nc.Dataset(exppath + "/sftgrf_" + region + "_" + lab + "_" + model + "_" + exp + ".nc", 'r')
sftgrf = idat.variables["sftgrf"][:,:,:]
idat.close()
idat = nc.Dataset(exppath + "/sftflf_" + region + "_" + lab + "_" + model + "_" + exp + ".nc", 'r')
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
    print(rhoi, rhow, rhof)
    print("sftgif:", sftgif.shape)
    print("sftgrf:", sftgrf.shape)
    print("sftflf:", sftflf.shape)

#############################################################
# Ice sheet and basin wide integrals

for regionName, region_mask in vars(regions).items():
    print(f"{regionName}")

    VAF_list = []
    G20_list = []
    A20_list = []
    G0_list = []
    
    # Reference state
    H0 = lithk_ref * maxmask1 * iaf2GIC
    B0 = topg_ref
    # TODO clarify if S0=0 is correct for all models
    S0 = topg_ref * 0.0  # Fix sealevel to 0

    # Use A for weighting and basin masking
    A = region_mask * af2 * (float(res)*1000.0)**2

    nt = len(lithk)

    # time loop
    if flg_A20_cumul:
        H_prev = H0.copy()
        B_prev = B0.copy()
        S_prev = S0.copy()
        A20_cumsum = 0.0
        G0_cumsum = 0.0

    for n in range(0, nt):

        H = lithk[n,:,:] * maxmask1 * iaf2GIC
        B = topg[n,:,:]

        # TODO check potential issues with partial masks
        VAF_list.append(slc_vaf.get_slc_vaf(H0, H, B0, B, S0, S0, A, c))
        G20_list.append(slc_G2020.get_slc_G2020(H0, H, B0, B, A, c))
        if flg_A20_cumul:
            A20_cumsum += slc_A2020.get_slc_A2020(H_prev, H, B_prev, B, S_prev, S_prev, A, c)
            A20_list.append(A20_cumsum)
            G0_cumsum += slc_G2020.get_slc_G2020(H_prev, H, B_prev, B_prev, A, c)
            G0_list.append(G0_cumsum)
            H_prev = H.copy()
            B_prev = B.copy()
            S_prev = S_prev  # sea level fixed at 0, no update needed
        else:
            # A2020 relative to reference state, like G2020 and VAF
            A20_list.append(slc_A2020.get_slc_A2020(H0, H, B0, B, S0, S0, A, c))
            G0_list.append(slc_G2020.get_slc_G2020(H0, H, B0, B0, A, c))

    sl_VAF = np.array(VAF_list)
    sl_G20 = np.array(G20_list)
    sl_A20 = np.array(A20_list)
    sl_G0 = np.array(G0_list)

    if verbose:
        print(sl_VAF)
        print(sl_G20)
        print(sl_A20)

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
    var_G0 = ds.createVariable('slc_G0','float', ('time'), zlib=True)
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
    var_G0.long_name = 'Sea level contribution based on G2020 with fixed bedrock'
    var_G0.units     = 'm'
    # assign data
    var_time[:]  = time_model
    var_VAF[:]   = sl_VAF[:]
    var_G2020[:] = sl_G20[:]
    var_A2020[:] = sl_A20[:]
    var_G0[:] = sl_G0[:]

    ds.close()
    print("Created file ", scfile)
