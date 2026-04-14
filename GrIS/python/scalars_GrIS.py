# Calculate scalar variables from ISMIP7 3D model output
# Heiko Goelzer 2026 (heig@norceresearch.no)

import netCDF4 as nc
import numpy as np
import os, glob
from types import SimpleNamespace

# SL methods
from slc import slc_vaf
from slc import slc_G2020
from slc import slc_A2020

# User settings
lab="NORCE"
model="CISM08-MAR312-p50"
exp="historical"
histref="historical" # last year of historical is needed for SL reference 
res="08"
# Path to generic data
datapath="../../../Data/GrIS"
# Path to model output
modelpath="../../../Models/GrIS"
# Path for prcessing
procpath="./proc"
# Path for resulting scalar files
outpath="./output"
## What output to produce
flg_mm=True  # Integrals on model mask
flg_bm=True  # IMBIE3-Mouginot basins

# Description for netcdf global
file_description = "ISMIP7 scalar output. Heiko Goelzer 2026, heig@norceresearch.no"

# Options
## What masking to apply If true, applied to all output
# Remove GIC contribution  
flg_GICmask=True # [Default True!]
# Remove ice outside observed ice mask (can be combined with GIC masking) 
flg_OBSmask=True # [Default False!]

# Define ocean area
oarea = 3.625e14 # m2 (Gregory et al., 2019)

################################################################
# File names and mapping 

# area factors
af2input=datapath+"/af2_ISMIP6_GrIS_"+res+"000m.nc"
# af2

# Greenland mask
mminput=datapath+"/maxmask1_"+res+"000m.nc"
# maxmask1

# Observed masks
obsinput=datapath+"/BM3_GrIS_nn_e"+res+"000m.nc"
# sftgif_OBS, sftgrf_OBS, sftflf_OBS

# IMBIE3 Mouginot extended basin masks 1-NO, 2-NE, 3-CE, 4-SE, 5-SW, 6-CW, 7-NW
basininput=datapath+"/GrIS_Basins_Mouginot_extended_e"+res+"000m_v1.nc"
# IDs

# GIC area factors
gicinput=datapath+"/rgi60_connect01_iaf2_"+res+"000m_v1.nc"
# iaf2

# Possible output files
scfile_mm=outpath+"/scalars_mm_GrIS_"+lab+"_"+model+"_"+exp+"_"+res+"000m.nc"
scfile_bm=outpath+"/scalars_bm_GrIS_"+lab+"_"+model+"_"+exp+"_"+res+"000m.nc"

####################################################
# Prepare generic data file

# Prepare Greenland mask
idat = nc.Dataset(mminput, 'r')
maxmask1  = idat.variables["maxmask1"][:,:]
idat.close()

# Prepare observed masks
idat = nc.Dataset(obsinput, 'r')
sftgif_OBS  = idat.variables["sftgif"][:,:]
sftgrf_OBS  = idat.variables["sftgrf"][:,:]
sftflf_OBS  = idat.variables["sftflf"][:,:]
idat.close()

# Prepare IMBIE3 Mouginot masks, ID: From NO clockwise
if flg_bm:
    idat = nc.Dataset(basininput, 'r')
    basinid = idat.variables["ID"][:,:]
    no  = (basinid==1).astype(float)
    ne  = (basinid==2).astype(float)
    ce  = (basinid==3).astype(float)
    se  = (basinid==4).astype(float)
    sw  = (basinid==5).astype(float)
    cw  = (basinid==6).astype(float)
    nw  = (basinid==7).astype(float)
    idat.close()

# Prepare area factors
idat = nc.Dataset(af2input, 'r')
af2  = idat.variables["af2"][:,:]
idat.close()
# inlcude GIC masking if requested
if flg_GICmask:
    # Prepare GIC masking file
    idat = nc.Dataset(gicinput, 'r')
    iaf2  = idat.variables["iaf2"][:,:]
    idat.close()
    # Combine with area factors
    af2 = af2*iaf2

###########################################################
# Prepare model output

# Main experiment
exppath=modelpath+"/"+lab+"/"+model+"/"+exp+"_"+res
# Model geometry
idat = nc.Dataset(exppath+"/lithk_GrIS_"+lab+"_"+model+"_"+exp+".nc", 'r')
lithk  = idat.variables["lithk"][:,:,:]
# Pick up time axis
time_model  = idat.variables["time"][:]
time_units = idat.variables["time"].units
time_long_name = idat.variables["time"].long_name
time_calendar = idat.variables["time"].calendar
idat.close()
idat = nc.Dataset(exppath+"/topg_GrIS_"+lab+"_"+model+"_"+exp+".nc", 'r')
topg  = idat.variables["topg"][:,:,:]
idat.close()

# Historical reference experiment; use last year
histrefpath=modelpath+"/"+lab+"/"+model+"/"+histref+"_"+res
# Model geometry
idat = nc.Dataset(histrefpath+"/lithk_GrIS_"+lab+"_"+model+"_"+histref+".nc", 'r')
lithk_ref  = idat.variables["lithk"][-1,:,:]
idat.close()
idat = nc.Dataset(histrefpath+"/topg_GrIS_"+lab+"_"+model+"_"+histref+".nc", 'r')
topg_ref  = idat.variables["topg"][-1,:,:]
idat.close()

# Add model params
idat = nc.Dataset(modelpath+"/"+lab+"/"+model+"/params.nc", 'r')
scalar = idat.variables["rhoi"]; rhoi = scalar[()]
scalar = idat.variables["rhow"]; rhow = scalar[()]
scalar = idat.variables["rhof"]; rhof = scalar[()]
idat.close()
c = SimpleNamespace()
c.RHOI  = rhoi # kg/m3
c.RHOSW = rhow # kg/m3
c.RHOFW = rhof # kg/m3
c.AO = oarea # m2

# Model masks
idat = nc.Dataset(exppath+"/sftgif_GrIS_"+lab+"_"+model+"_"+exp+".nc", 'r')
sftgif  = idat.variables["sftgif"][:,:,:]
idat.close()
idat = nc.Dataset(exppath+"/sftgrf_GrIS_"+lab+"_"+model+"_"+exp+".nc", 'r')
sftgrf  = idat.variables["sftgrf"][:,:,:]
idat.close()
idat = nc.Dataset(exppath+"/sftflf_GrIS_"+lab+"_"+model+"_"+exp+".nc", 'r')
sftflf  = idat.variables["sftflf"][:,:,:]
idat.close()

# inlcude OBS masking if requested
if flg_OBSmask:
    sftgif = sftgif*sftgif_OBS
    sftgrf = sftgrf*sftgrf_OBS
    sftflf = sftflf*sftflf_OBS

#######################################
# See what have
print("# Generic")
print("no:", no.shape)
print("af2:", af2.shape)
print("maxmask1:", maxmask1.shape)
if flg_OBSmask:
    print("sftgif_OBS:", sftgif_OBS.shape)
    print("sftgrf_OBS:", sftgrf_OBS.shape)
    print("sftflf_OBS:", sftflf_OBS.shape)
if flg_GICmask:
    print("iaf2:", iaf2.shape)

print("# Model")
print("lithk_ref:", lithk_ref.shape)
print("topg_ref:", topg_ref.shape)
print("lithk:", lithk.shape)
print("topg:", topg.shape)
print(rhoi, rhow, rhof)
print("sftgif:", sftgif.shape)
print("sftgrf:", sftgrf.shape)
print("sftflf:", sftflf.shape)

##################################################################################
# Greenland wide integrals
##################################################################################

VAF_list=[]
G20_list=[]
A20_list=[]

# Reference state
H0 = lithk_ref
B0 = topg_ref
S0 = topg_ref * 0.0 # Fix sealevel at 0
A = af2*(float(res)*1000.0)**2

nt = len(lithk)

# time loop
for n in range(0,nt):
    print(str(n))

    H = lithk[n,:,:]
    B = topg[n,:,:]
    
    VAF_list.append(slc_vaf.get_slc_vaf(H0,H,B0,B0,S0,S0,A,c))
    G20_list.append(slc_G2020.get_slc_G2020(H0,H,B0,B,A,c))
    A20_list.append(slc_A2020.get_slc_A2020(H0,H,B0,B0,S0,S0,A,c))

sl_VAF = np.array(VAF_list)
sl_G20 = np.array(G20_list)
sl_A20 = np.array(A20_list)

print(sl_VAF)
print(sl_G20)
print(sl_A20)

###############################################
# Write results

ds = nc.Dataset(scfile_mm, 'w', format='NETCDF4')
ds.createDimension('time', None)
# Variables
time = ds.createVariable('time', 'float', ('time'), zlib=True)
slc_VAF = ds.createVariable('slc_VAF', 'float', ('time'), zlib=True)
slc_G2020 = ds.createVariable('slc_G2020', 'float', ('time'), zlib=True)
slc_A2020 = ds.createVariable('slc_A2020', 'float', ('time'), zlib=True)
# Attributes
ds.description = file_description
time.units = time_units
time.long_name = time_long_name
time.calendar = time_calendar
slc_VAF.long_name = 'Sea level contribution based on Vaf'
slc_VAF.units = 'm'
slc_G2020.long_name = 'Sea level contribution based on G2020'
slc_G2020.units = 'm'
slc_A2020.long_name = 'Sea level contribution based on A2020'
slc_A2020.units = 'm'
# assign data 
time[:] = time_model
slc_VAF[:] = sl_VAF[:]
slc_G2020[:] = sl_G20[:]
slc_A2020[:] = sl_A20[:]

# close file
ds.close()
