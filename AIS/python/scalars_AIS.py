# Calculate scalar variables from ISMIP7 3D model output
# Heiko Goelzer 2026 (heig@norceresearch.no)

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..'))

import netCDF4 as nc
import numpy as np
from types import SimpleNamespace

# SL methods
from slc import slc_vaf
from slc import slc_G2020
from slc import slc_A2020

# User settings
#lab="NORCE"
#model="CISM4-MAR364-ERA-t1"
#exp="expAE01"
lab="ISMIP7"
model="TEST"
#exp="historical"
exp="exp0"
histref="historical" # last year of historical is needed for SL reference 
res="08"
# Path to generic data
datapath="../../Data/AIS"
# Path to model output
modelpath="../../Models/AIS"
# Path for resulting scalar files
outpath="./output"
## What output to produce
flg_mm=True  # Integrals on model mask
flg_bm=False  # IMBIE3-Mouginot basins

# Description for netcdf global
file_description = "ISMIP7 scalar output. Heiko Goelzer 2026, heig@norceresearch.no"

# Options
## What masking to apply If true, applied to all output
# Remove GIC contribution  
flg_GICmask=True # [Default True!]

# More output
verbose = False

################################################################
# File names and mapping 

# area factors
af2input=datapath+"/af2_AIS_"+res+"000m_v1.nc"
# af2

# Antarctic mask; TODO needs to be defined if needed
mminput=datapath+"/maxmask1_AIS_"+res+"000m_v0.nc"
# maxmask1

# IMBIE3 basins: 1 to 18; 1 = H-HP; 2 = EP-F; 3 = F-G; 4 = G-H; 5 = J-Jpp; 6 = E-Ep 7; = D-Dp 8; = Cp-D 9; = B-C 10; = A-Ap 11; = Jpp-K 12; = Dp-E 13; = Ap-B; 14; = C-CP; 15 = K-A; 16 = Ipp-J; 17 = I-Ipp; 18 = Hp-I
# IMBIE3 regions: West Antarctica, 2 East Antarctica, 3 Peninsula
basininput=datapath+"/basins_regions_AIS_Rignot_extended_"+res+"000m_v1.nc"
# basins, regions

## GIC area factors; TODO needs to be defined if needed
gicinput=datapath+"/iaf2_GIC_AIS_"+res+"000m_v0.nc"
## iaf2

# Output files
file_suffix="AIS_"+lab+"_"+model+"_"+exp+"_"+res+"000m.nc"

####################################################
# Prepare generic data file

# Defined ocean area
oarea = 3.625e14 # m2 (Gregory et al., 2019)

# Prepare Antarctic mask
idat = nc.Dataset(mminput, 'r')
maxmask1  = idat.variables["maxmask1"][:,:]
idat.close()
ais = maxmask1*0+1 # ais region covers the entire grid
regions = SimpleNamespace()
regions.mm = ais

# Prepare regions masks
if flg_bm:
    idat = nc.Dataset(basininput, 'r')
    # regions
    basinid = idat.variables["regions"][:,:]
    regions.wais  = (basinid==1).astype(float)
    regions.eais  = (basinid==2).astype(float)
    regions.pina  = (basinid==3).astype(float)
    ## basins
    basinid = idat.variables["basins"][:,:]
    regions.r01 = (basinid==1).astype(float)
    regions.r02 = (basinid==2).astype(float)
    regions.r03 = (basinid==3).astype(float)
    regions.r04 = (basinid==4).astype(float)
    regions.r05 = (basinid==5).astype(float)
    regions.r06 = (basinid==6).astype(float)
    regions.r07 = (basinid==7).astype(float)
    regions.r08 = (basinid==8).astype(float)
    regions.r09 = (basinid==9).astype(float)
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
    aistest = regions.wais+regions.eais+regions.pina
    nx,ny = regions.wais.shape
    if verbose:
        print(np.sum(ais), np.sum(aistest),nx*ny)

# Prepare area factors
idat = nc.Dataset(af2input, 'r')
af2  = idat.variables["af2"][:,:]
idat.close()
# inlcude GIC masking if requested
if flg_GICmask:
    # Prepare GIC masking file
    idat = nc.Dataset(gicinput, 'r')
    iaf2GIC  = idat.variables["iaf2"][:,:]
    idat.close()

###########################################################
# Prepare model output

# Main experiment
exppath=modelpath+"/"+lab+"/"+model+"/"+exp+"_"+res
# Model geometry
idat = nc.Dataset(exppath+"/lithk_AIS_"+lab+"_"+model+"_"+exp+".nc", 'r')
lithk  = idat.variables["lithk"][:,:,:]
# Pick up time axis
time_model  = idat.variables["time"][:]
time_units = idat.variables["time"].units
time_long_name = idat.variables["time"].long_name
time_calendar = idat.variables["time"].calendar
idat.close()
idat = nc.Dataset(exppath+"/topg_AIS_"+lab+"_"+model+"_"+exp+".nc", 'r')
topg  = idat.variables["topg"][:,:,:]
idat.close()

# Historical reference experiment; use last year
histrefpath=modelpath+"/"+lab+"/"+model+"/"+histref+"_"+res
# Model geometry
idat = nc.Dataset(histrefpath+"/lithk_AIS_"+lab+"_"+model+"_"+histref+".nc", 'r')
lithk_ref  = idat.variables["lithk"][-1,:,:]
idat.close()
idat = nc.Dataset(histrefpath+"/topg_AIS_"+lab+"_"+model+"_"+histref+".nc", 'r')
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
idat = nc.Dataset(exppath+"/sftgif_AIS_"+lab+"_"+model+"_"+exp+".nc", 'r')
sftgif  = idat.variables["sftgif"][:,:,:]
idat.close()
idat = nc.Dataset(exppath+"/sftgrf_AIS_"+lab+"_"+model+"_"+exp+".nc", 'r')
sftgrf  = idat.variables["sftgrf"][:,:,:]
idat.close()
idat = nc.Dataset(exppath+"/sftflf_AIS_"+lab+"_"+model+"_"+exp+".nc", 'r')
sftflf  = idat.variables["sftflf"][:,:,:]
idat.close()

#######################################
# See what have

if verbose:
    print("# Generic")
    print("no:", regions.no.shape)
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
# Antarctic and basin wide integrals

for regionName, region in vars(regions).items():
    print(f"{regionName}")

    VAF_list=[]
    G20_list=[]
    A20_list=[]
    
    # Reference state
    H0 = lithk_ref * maxmask1 * iaf2GIC
    B0 = topg_ref
    # TODO clarify if S0=0 is correct for all models
    S0 = topg_ref * 0.0 # Fix sealevel to 0; 
    
    # Use A for weigthing and basin masking
    A = region * af2 * (float(res)*1000.0)**2
    
    nt = len(lithk)
    
    # time loop; 
    for n in range(0,nt):
        #print(regionName, str(n))
    
        H = lithk[n,:,:] * maxmask1 * iaf2GIC
        B = topg[n,:,:]
        
        # TODO clarify if this is how A2020 should be calculated
        # TODO check potential issues with partial masks
        VAF_list.append(slc_vaf.get_slc_vaf(H0,H,B0,B0,S0,S0,A,c))
        G20_list.append(slc_G2020.get_slc_G2020(H0,H,B0,B,A,c))
        A20_list.append(slc_A2020.get_slc_A2020(H0,H,B0,B0,S0,S0,A,c))
    
    sl_VAF = np.array(VAF_list)
    sl_G20 = np.array(G20_list)
    sl_A20 = np.array(A20_list)

    if verbose:
        print(sl_VAF)
        print(sl_G20)
        print(sl_A20)
    
    ###############################################
    # Write netcdf file

    scfile = outpath+"/scalars_"+regionName+"_"+file_suffix
    ds = nc.Dataset(scfile, 'w', format='NETCDF4')
    ds.createDimension('time', None)
    # Variables
    var_time = ds.createVariable('time', 'float', ('time'), zlib=True)
    var_VAF = ds.createVariable('slc_VAF', 'float', ('time'), zlib=True)
    var_G2020 = ds.createVariable('slc_G2020', 'float', ('time'), zlib=True)
    var_A2020 = ds.createVariable('slc_A2020', 'float', ('time'), zlib=True)
    # Attributes
    ds.description = file_description
    var_time.units = time_units
    var_time.long_name = time_long_name
    var_time.calendar = time_calendar
    var_VAF.long_name = 'Sea level contribution based on Vaf'
    var_VAF.units = 'm'
    var_G2020.long_name = 'Sea level contribution based on G2020'
    var_G2020.units = 'm'
    var_A2020.long_name = 'Sea level contribution based on A2020'
    var_A2020.units = 'm'
    # assign data 
    var_time[:] = time_model
    var_VAF[:] = sl_VAF[:]
    var_G2020[:] = sl_G20[:]
    var_A2020[:] = sl_A20[:]
    
    # close file
    ds.close()
    print("Created file ", scfile)
    
