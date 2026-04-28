# Calculate scalar variables from ISMIP7 3D model output - MINI test case
# Heiko Goelzer 2026 (heig@norceresearch.no)

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../AIS/python'))

import netCDF4 as nc
import numpy as np
from types import SimpleNamespace

# SL methods
from slc import slc_vaf
from slc import slc_G2020
from slc import slc_A2020
from slc.sl_constants import RHOI, RHOSW, RHOFW, AO

# User settings
lab   = "ISMIP7"
model = "MINI0"
exp   = "expg"
# Path to generic data
datapath  = "../../Data/MINI0"
# Path to model output
modelpath = "../../Models/MINI/ISMIP7/MINI0"
# Path for resulting scalar files
outpath = "./output"
## What output to produce
flg_mm = True   # Integrals on model mask
flg_bm = False  # IMBIE3 basins

# Description for netcdf global
file_description = "ISMIP7 scalar output. Heiko Goelzer 2026, heig@norceresearch.no"

# Options
# Remove GIC contribution
flg_GICmask = True  # [Default True!]

# More output
verbose = False

# Pixel size for area weighting
dx = 600000.0  # m (600 km)

################################################################
# File names and mapping

# area factors
af2input = datapath + "/af2_MINI0_vCDO.nc"
# af2

# Antarctic mask
mminput = datapath + "/maxmask1_MINI0_v0.nc"
# maxmask1

# GIC area factors
gicinput = datapath + "/iaf2_MINI0_v0.nc"
# iaf2

# Output files
file_suffix = "AIS_" + lab + "_" + model + "_" + exp + ".nc"

####################################################
# Prepare generic data file

# Defined ocean area
oarea = AO  # m2 (Gregory et al., 2019)

# Prepare Antarctic mask
idat = nc.Dataset(mminput, 'r')
maxmask1 = idat.variables["maxmask1"][:,:]
idat.close()
ais = maxmask1 * 0 + 1  # ais region covers the entire grid
regions = SimpleNamespace()
regions.mm = ais

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

# Reference state: first time step of exp (no separate historical run for MINI)
lithk_ref = lithk[0, :, :]
topg_ref  = topg[0,  :, :]

# Physical constants from sl_constants (no params.nc for MINI)
c = SimpleNamespace()
c.RHOI  = RHOI
c.RHOSW = RHOSW
c.RHOFW = RHOFW
c.AO    = oarea

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
# Antarctic wide integrals

for regionName, region in vars(regions).items():
    print(f"{regionName}")

    VAF_list = []
    G20_list = []
    A20_list = []

    # Reference state
    H0 = lithk_ref * maxmask1 * iaf2GIC
    B0 = topg_ref
    S0 = topg_ref * 0.0  # Fix sealevel to 0

    # Use A for weighting and region masking
    A = region * af2 * dx**2

    nt = len(lithk)

    # time loop
    for n in range(0, nt):

        H = lithk[n,:,:] * maxmask1 * iaf2GIC
        B = topg[n,:,:]

        VAF_list.append(slc_vaf.get_slc_vaf(H0, H, B0, B0, S0, S0, A, c))
        G20_list.append(slc_G2020.get_slc_G2020(H0, H, B0, B, A, c))
        A20_list.append(slc_A2020.get_slc_A2020(H0, H, B0, B0, S0, S0, A, c))

    sl_VAF = np.array(VAF_list)
    sl_G20 = np.array(G20_list)
    sl_A20 = np.array(A20_list)

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
    # Attributes
    ds.description = file_description
    var_time.units      = time_units
    var_time.long_name  = time_long_name
    var_time.calendar   = time_calendar
    var_VAF.long_name   = 'Sea level contribution based on Vaf'
    var_VAF.units       = 'm'
    var_G2020.long_name = 'Sea level contribution based on G2020'
    var_G2020.units     = 'm'
    var_A2020.long_name = 'Sea level contribution based on A2020'
    var_A2020.units     = 'm'
    # assign data
    var_time[:]  = time_model
    var_VAF[:]   = sl_VAF[:]
    var_G2020[:] = sl_G20[:]
    var_A2020[:] = sl_A20[:]

    ds.close()
    print("Created file ", scfile)
