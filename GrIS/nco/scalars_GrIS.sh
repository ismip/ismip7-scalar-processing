#!/bin/bash
# Calculate scalar variables from ISMIP7 3D model output
# Heiko Goelzer 2026 (heig@norceresearch.no)

# Scalars
# multiply with masks, multiply with area factors, integrate spatially
# calculate sea-level equivalents

set -x
set -e

# User settings
lab=NORCE
model=CISM08-MAR312-p50
exp=historical
res=08
# Path to generic data
datapath=../../../Data/GrIS
# Path to model output
modelpath=../../../Models/GrIS
# Path for prcessing
procpath=./proc
# Path for resulting scalar files
outpath=./output
## What output to produce
flg_mm=true  # Integrals on model mask
flg_bm=true  # IMBIE3-Mouginot basins

# Options
## What masking to apply If true, applied to all output
# Remove GIC contribution  
flg_GICmask=true # [Default true!]
# Remove ice outside observed ice mask (can be combined with GIC masking) 
flg_OBSmask=true # [Default false!]

#################################################################
# Checks

# Check we have generic data
# Check we have model parameters
# Check we have model output
# Check resolution = res

################################################################
# File names and mapping 

# area factors
af2input=$datapath/af2_ISMIP6_GrIS_${res}000m.nc
af2file=${procpath}/af2.nc
# af2

# Greenland mask
mminput=$datapath/maxmask1_${res}000m.nc
mmfile=${procpath}/maxmask1.nc
# maxmask1

# Observed masks
obsinput=$datapath/BM3_GrIS_nn_e${res}000m.nc
obsfile=${procpath}/masksOBS.nc
# sftgif_OBS, sftgrf_OBS, sftflf_OBS

# IMBIE3 Mouginot extended basin masks 1-NO, 2-NE, 3-CE, 4-SE, 5-SW, 6-CW, 7-NW
basininput=$datapath/GrIS_Basins_Mouginot_extended_e${res}000m_v1.nc
basinfile=${procpath}/basins.nc
# IDs

# GIC area factors
gicinput=$datapath/rgi60_connect01_iaf2_${res}000m_v1.nc
gicfile=${procpath}/afGIC.nc
# iaf2

# Model file name
modelfile=${procpath}/model.nc
paramfile=${procpath}/params.nc

# Intermediate working files
maskfile=${procpath}/icemasks.nc
procfile=${procpath}/mainproc.nc

# Temporary files
tmp_file=${procpath}/tmp.nc
tmp_af=${procpath}/tmpaf.nc
tmp_sc=${procpath}/tmpsc.nc

# Possible output files
scfile_mm=${outpath}/scalars_mm_GrIS_${lab}_${model}_${exp}_${res}.nc
scfile_bm=${outpath}/scalars_bm_GrIS_${lab}_${model}_${exp}_${res}.nc

####################################################
# Prepare generic data file

# Prepare Greenland mask
ncks -3 -O -v maxmask1 ${mminput} ${mmfile}

# Prepare observed masks
ncks -3 -O -v sftgif ${obsinput} ${obsfile} 
ncks -3 -A -v sftgrf ${obsinput} ${obsfile}
ncks -3 -A -v sftflf ${obsinput} ${obsfile}
ncrename -v sftgif,sftgif_OBS ${obsfile}
ncrename -v sftgrf,sftgrf_OBS ${obsfile}
ncrename -v sftflf,sftflf_OBS ${obsfile}

# Prepare IMBIE3 Mouginot masks, ID: From NO clockwise
if $flg_bm; then
    ncap2 -3 -O -s 'no=ID==1' -v ${basininput} ${basinfile} 
    ncap2 -3 -A -s 'ne=ID==2' -v ${basininput} ${basinfile} 
    ncap2 -3 -A -s 'ce=ID==3' -v ${basininput} ${basinfile} 
    ncap2 -3 -A -s 'se=ID==4' -v ${basininput} ${basinfile} 
    ncap2 -3 -A -s 'sw=ID==5' -v ${basininput} ${basinfile} 
    ncap2 -3 -A -s 'cw=ID==6' -v ${basininput} ${basinfile} 
    ncap2 -3 -A -s 'nw=ID==7' -v ${basininput} ${basinfile} 
fi

# Prepare area factors
ncks -3 -O -v af2 ${af2input} ${af2file}
# inlcude GIC masking if requested
if $flg_GICmask; then
# Prepare GIC masking file
    ncks -3 -O -v iaf2 ${gicinput} ${gicfile}
    # remove mapping attribute to avoid conflict 
    ncatted -a grid_mapping,iaf2,d,, ${gicfile}
    # Combine with area factors
    ncks -A -v iaf2 ${gicfile} ${af2file}
    ncap2 -O -s "af2 = af2*iaf2" ${af2file} ${af2file}
fi

###########################################################
# Prepare model output

exppath=${modelpath}/${lab}/${model}/${exp}_${res}
# Model geometry
anc=${exppath}/lithk_GrIS_${lab}_${model}_${exp}.nc
ncks -3 -O -v lithk ${anc} ${modelfile}
anc=${exppath}/topg_GrIS_${lab}_${model}_${exp}.nc
ncks -3 -A -v topg ${anc} ${modelfile}

# Add model params
ncks -3 -O ${modelpath}/${lab}/${model}/params.nc ${paramfile}
ncks -3 -A ${paramfile} ${modelfile}

# Model masks
anc=${exppath}/sftgif_GrIS_${lab}_${model}_${exp}.nc
ncks -3 -O -v sftgif ${anc} ${maskfile}
anc=${exppath}/sftgrf_GrIS_${lab}_${model}_${exp}.nc
ncks -3 -A -v sftgrf ${anc} ${maskfile}
anc=${exppath}/sftflf_GrIS_${lab}_${model}_${exp}.nc
ncks -3 -A -v sftflf ${anc} ${maskfile}

# inlcude OBS masking if requested
if $flg_OBSmask; then
    ncks -3 -A -v sftgif_OBS ${obsfile} ${maskfile}
    ncks -3 -A -v sftgrf_OBS ${obsfile} ${maskfile}
    ncks -3 -A -v sftflf_OBS ${obsfile} ${maskfile}
    ncap2 -3 -A -s "sftgif = sftgif*sftgif_OBS" ${maskfile} ${maskfile}
    ncap2 -3 -A -s "sftgrf = sftgrf*sftgrf_OBS" ${maskfile} ${maskfile}
    ncap2 -3 -A -s "sftflf = sftflf*sftflf_OBS" ${maskfile} ${maskfile}
fi

##########################################################
# Make master netcdf file 

ncks -3 -O -v sftgif ${maskfile} ${procfile}
ncks -3 -A -v sftgrf ${maskfile} ${procfile}
ncks -3 -A -v sftflf ${maskfile} ${procfile}
ncks -3 -A -v maxmask1 ${mmfile} ${procfile}
ncks -3 -A -v af2 ${af2file} ${procfile}
ncks -3 -A -v lithk,topg,rhoi,rhow,rhof,oarea ${modelfile} ${procfile}
ncap2 -3 -O -s "dx=${res}000" ${procfile} ${procfile}

if $flg_bm; then
    ncks -3 -A ${basinfile} ${procfile}
fi

##################################################################################
# Greenland wide integrals
##################################################################################

if $flg_mm; then

# Make dummy container for scalar output
ncks -3 -O scalars_template.nc ${scfile_mm}
ncks -A -v rhoi,rhow,rhof,oarea ${paramfile} ${scfile_mm}

# Ice area Model
# sftgif
/bin/cp scalars_template.nc ${tmp_af}
ncap2 -O -s 'af=sftgif*maxmask1*af2; dx=dx' -v ${procfile} ${tmp_af}
ncap2 -O -s 'iarea=af.total($x,$y)*dx^2' -v ${tmp_af} ${tmp_sc}
ncks -A -v iarea ${tmp_sc} ${scfile_mm}
ncatted -a standard_name,iarea,d,, ${scfile_mm}
ncatted -a long_name,iarea,o,c,"ice sheet area" ${scfile_mm}
ncatted -a units,iarea,o,c,"m2" ${scfile_mm}
/bin/rm ${tmp_af} ${tmp_sc} 

# Grounded ice area Model
# sftgrf
/bin/cp scalars_template.nc ${tmp_af}
ncap2 -O -s 'af=sftgrf*maxmask1*af2; dx=dx' -v ${procfile} ${tmp_af}
ncap2 -O -s 'iareagr=af.total($x,$y)*dx^2' -v ${tmp_af} ${tmp_sc}
ncks -A -v iareagr ${tmp_sc} ${scfile_mm}
ncatted -a standard_name,iareagr,d,, ${scfile_mm}
ncatted -a long_name,iareagr,o,c,"grounded ice sheet area" ${scfile_mm}
ncatted -a units,iareagr,o,c,"m2" ${scfile_mm}
/bin/rm ${tmp_af} ${tmp_sc} 

# Floating ice area Model
# sftflf
/bin/cp scalars_template.nc ${tmp_af}
ncap2 -O -s 'af=sftflf*maxmask1*af2; dx=dx' -v ${procfile} ${tmp_af}
ncap2 -O -s 'iareafl=af.total($x,$y)*dx^2' -v ${tmp_af} ${tmp_sc}
ncks -A -v iareafl ${tmp_sc} ${scfile_mm}
ncatted -a standard_name,iareafl,d,, ${scfile_mm}
ncatted -a long_name,iareafl,o,c,"floating ice sheet area" ${scfile_mm}
ncatted -a units,iareafl,o,c,"m2" ${scfile_mm}
/bin/rm ${tmp_af} ${tmp_sc} 

# Ice volume model
# sftgif
/bin/cp scalars_template.nc ${tmp_af}
ncap2 -O -s 'af=lithk*sftgif*maxmask1*af2; dx=dx' -v ${procfile} ${tmp_af}
ncap2 -O -s 'ivol=af.total($x,$y)*dx^2' -v ${tmp_af} ${tmp_sc}
ncks -A -v ivol ${tmp_sc} ${scfile_mm}
ncatted -a standard_name,ivol,d,, ${scfile_mm}
ncatted -a long_name,ivol,o,c,"ice volume" ${scfile_mm}
ncatted -a units,ivol,o,c,"m3" ${scfile_mm}
/bin/rm ${tmp_af} ${tmp_sc} 

# Grounded ice volume model
# sftgrf
/bin/cp scalars_template.nc ${tmp_af}
ncap2 -O -s 'af=lithk*sftgrf*maxmask1*af2; dx=dx' -v ${procfile} ${tmp_af}
ncap2 -O -s 'ivolgr=af.total($x,$y)*dx^2' -v ${tmp_af} ${tmp_sc}
ncks -A -v ivolgr ${tmp_sc} ${scfile_mm}
ncatted -a standard_name,ivolgr,d,, ${scfile_mm}
ncatted -a long_name,ivolgr,o,c,"grounded ice volume" ${scfile_mm}
ncatted -a units,ivolgr,o,c,"m3" ${scfile_mm}
/bin/rm ${tmp_af} ${tmp_sc} 

# Floating ice vol model
# sftflf
/bin/cp scalars_template.nc ${tmp_af}
ncap2 -O -s 'af=lithk*sftflf*maxmask1*af2; dx=dx' -v ${procfile} ${tmp_af}
ncap2 -O -s 'ivolfl=af.total($x,$y)*dx^2' -v ${tmp_af} ${tmp_sc}
ncks -A -v ivolfl ${tmp_sc} ${scfile_mm}
ncatted -a standard_name,ivolfl,d,, ${scfile_mm}
ncatted -a long_name,ivolfl,o,c,"floating ice volume" ${scfile_mm}
ncatted -a units,ivolfl,o,c,"m3" ${scfile_mm}
/bin/rm ${tmp_af} ${tmp_sc} 

# Volume above flotation model
# sftgif
ncks -A scalars_template.nc ${tmp_file}
# thickness at flotation
ncap2 -O -s 'thif=-topg*(rhow/rhoi); where (thif<0) thif=0' ${procfile} ${tmp_file}
# thickness above flotation
ncap2 -O -s 'af=(lithk-thif)*sftgif*maxmask1*af2; where(af<0) af=0; dx=dx' -v ${tmp_file} ${tmp_af}
ncap2 -O -s 'ivaf=af.total($x,$y)*dx^2' -v ${tmp_af} ${tmp_sc}
ncks -A -v ivaf ${tmp_sc} ${scfile_mm}
ncatted -a standard_name,ivaf,d,, ${scfile_mm}
ncatted -a long_name,ivaf,o,c,"ice volume above flotation" ${scfile_mm}
ncatted -a units,ivaf,o,c,"m3" ${scfile_mm}
/bin/rm ${tmp_file} ${tmp_af} ${tmp_sc}

# Ice mass lim
ncap2 -A -s "lim=ivol*rhoi" ${scfile_mm} ${scfile_mm} 
ncatted -a standard_name,lim,d,, ${scfile_mm}
ncatted -a long_name,lim,o,c,"ice mass" ${scfile_mm}
ncatted -a units,lim,o,c,"kg" ${scfile_mm}
ncap2 -A -s "limgr=ivolgr*rhoi" ${scfile_mm} ${scfile_mm} 
ncatted -a standard_name,limgr,d,, ${scfile_mm}
ncatted -a long_name,limgr,o,c,"grounded ice mass" ${scfile_mm}
ncatted -a units,limgr,o,c,"kg" ${scfile_mm}
ncap2 -A -s "limfl=ivolfl*rhoi" ${scfile_mm} ${scfile_mm} 
ncatted -a standard_name,limfl,d,, ${scfile_mm}
ncatted -a long_name,limfl,o,c,"floating ice mass" ${scfile_mm}
ncatted -a units,limfl,o,c,"kg" ${scfile_mm}
# Ice mass above flotation
ncap2 -A -s "limaf=ivaf*rhoi" ${scfile_mm} ${scfile_mm} 
ncatted -a standard_name,limaf,d,, ${scfile_mm}
ncatted -a long_name,limaf,o,c,"ice mass above flotation" ${scfile_mm}
ncatted -a units,limaf,o,c,"kg" ${scfile_mm}

# SL G2020
# Goelzer at al 2020, TC. Brief communication: On calculating the sea-level contribution in marine ice-sheet models
# Uncorrected Vaf; like Equ 2, but not devided by Aoc
ncap2 -A -s "vaf=ivaf*(rhoi/rhow)" ${scfile_mm} ${scfile_mm} 
ncatted -a standard_name,vaf,d,, ${scfile_mm}
ncatted -a long_name,vaf,o,c,"uncorrected volume above floatation" ${scfile_mm}
ncatted -a units,vaf,o,c,"m3" ${scfile_mm}
# Density correction Equ 10.
ncap2 -A -s "vden=ivol*((rhoi/rhof)-(rhoi/rhow))" ${scfile_mm} ${scfile_mm} 
ncatted -a standard_name,vden,d,, ${scfile_mm}
ncatted -a long_name,vden,o,c,"density correction volume" ${scfile_mm}
ncatted -a units,vden,o,c,"m3" ${scfile_mm}
# Potential ocean volume correction Equ 8.
ncap2 -O -s 'af=(-topg)*maxmask1*af2; where(af<0) af=0' ${procfile} ${tmp_af}
ncap2 -O -s 'vpov=af.total($x,$y)*dx^2' ${tmp_af} ${tmp_sc}
ncks -A -v vpov ${tmp_sc} ${scfile_mm}
ncatted -a standard_name,vpov,d,, ${scfile_mm}
ncatted -a long_name,vpov,o,c,"potential ocean volume" ${scfile_mm}
ncatted -a units,ivaf,o,c,"m3" ${scfile_mm}
/bin/rm ${tmp_af} ${tmp_sc}
# SL correction 
ncap2 -A -s "sl_G2020=(vaf+vden+vpov)/oarea" ${scfile_mm} ${scfile_mm} 
ncatted -a long_name,sl_G2020,o,c,"corrected sealevel equivalent ice mass (af+den+pov)" ${scfile_mm}
ncatted -a standard_name,sl_G2020,d,, ${scfile_mm}
ncatted -a units,sl_G2020,o,c,"m" ${scfile_mm}

# SL VAF
ncap2 -A -s "sl_vaf=ivaf*rhoi/oarea/rhof" ${scfile_mm} ${scfile_mm} 
ncatted -a standard_name,sl_vaf,d,, ${scfile_mm}
ncatted -a long_name,sl_vaf,o,c,"sealevel equivalent ice mass" ${scfile_mm}
ncatted -a units,sl_vaf,o,c,"m" ${scfile_mm}

# clean up
ncatted -h -a history,global,d,, ${scfile_mm}
ncatted -h -a history_of_appended_files,global,d,, ${scfile_mm}
ncatted -h -a NCO,global,d,, ${scfile_mm}
ncatted -h -a CDO,global,d,, ${scfile_mm}
ncatted -h -a CDI,global,d,, ${scfile_mm}
ncatted -h -a Description,global,d,, ${scfile_mm}
ncatted -h -a proj4,global,d,, ${scfile_mm}
# Add info
ncatted -h -a Description,global,o,c,"ISMIP7 scalar output. Heiko Goelzer 2026, heig@norceresearch.no" ${scfile_mm}

fi

##################################################################################
# IMBIE3 Mouginot basins 
##################################################################################
if $flg_bm; then

# Make dummy containers for scalar output
ncks -O scalars_template.nc ${scfile_bm}
ncks -A -v rhoi,rhow,rhof,oarea ${paramfile} ${scfile_bm}

# Volume above flotation
# sftgif
ncks -A scalars_template.nc ${tmp_file}
# thickness at flotation
ncap2 -O -s "thif=-topg*(rhow/rhoi); where (thif<0) thif=0" ${procfile} ${tmp_file}

for basin in no ne ce se sw cw nw; do
# thickness above flotation 
ncap2 -O -s "af=(lithk-thif)*sftgif*${basin}*maxmask1*af2; where(af<0) af=0; dx=dx" -v ${tmp_file} ${tmp_af}
ncap2 -O -s "ivaf_${basin}=af.total(\$x,\$y)*dx^2" ${tmp_af} ${tmp_sc}
ncks -A -v ivaf_${basin} ${tmp_sc} ${scfile_bm}
ncatted -a standard_name,ivaf_${basin},d,, ${scfile_bm}
ncatted -a long_name,ivaf_${basin},o,c,"ice volume above flotation" ${scfile_bm}
ncatted -a units,ivaf_${basin},o,c,"m3" ${scfile_bm}
/bin/rm ${tmp_af} ${tmp_sc}

# Ice mass above flotation
ncap2 -A -s "limaf_${basin}=ivaf_${basin}*rhoi" ${scfile_bm} ${scfile_bm} 
ncatted -a standard_name,limaf_${basin},d,, ${scfile_bm}
ncatted -a long_name,limaf_${basin},o,c,"ice mass above flotation" ${scfile_bm}
ncatted -a units,limaf_${basin},o,c,"kg" ${scfile_bm}
# SLE
ncap2 -A -s "sle_${basin}=ivaf_${basin}*rhoi/oarea/rhof" ${scfile_bm} ${scfile_bm} 
ncatted -a standard_name,sle_${basin},d,, ${scfile_bm}
ncatted -a long_name,sle_${basin},o,c,"sealevel equivalent ice mass" ${scfile_bm}
ncatted -a units,sle_${basin},o,c,"m" ${scfile_bm}

# Goelzer at al 2020, TC. Brief communication: On calculating the sea-level contribution in marine ice-sheet models
# Uncorrected Vaf; like Equ 2, but not devided by Aoc
ncap2 -A -s "vaf_${basin}=ivaf_${basin}*(rhoi/rhow)" ${scfile_bm} ${scfile_bm}
ncatted -a standard_name,vaf_${basin},d,, ${scfile_bm}
ncatted -a long_name,vaf_${basin},o,c,"uncorrected volume above floatation" ${scfile_bm}
ncatted -a units,vaf_${basin},o,c,"m3" ${scfile_bm}
# Density correction Equ 10.
ncap2 -O -s "af=lithk*sftgif*${basin}*maxmask1*af2" ${tmp_file} ${tmp_af}
ncap2 -O -s "ivol_${basin}=af.total(\$x,\$y)*dx^2" ${tmp_af} ${tmp_sc}
ncap2 -A -s "vden_${basin}=ivol_${basin}*((rhoi/rhof)-(rhoi/rhow))" ${tmp_sc} ${tmp_sc}
ncks -A -v vden_${basin} ${tmp_sc} ${scfile_bm}
ncatted -a standard_name,vden_${basin},d,, ${scfile_bm}
ncatted -a long_name,vden_${basin},o,c,"density correction volume" ${scfile_bm}
ncatted -a units,vden_${basin},o,c,"m3" ${scfile_bm}
/bin/rm ${tmp_af} ${tmp_sc}
# Potential ocean volume correction Equ 8.
ncap2 -O -s "af=(-topg)*${basin}*maxmask1*af2; where(af<0) af=0" ${tmp_file} ${tmp_af}
ncap2 -O -s "vpov_${basin}=af.total(\$x,\$y)*dx^2" ${tmp_af} ${tmp_sc}
ncks -A -v vpov_${basin} ${tmp_sc} ${scfile_bm}
ncatted -a standard_name,vpov_${basin},d,, ${scfile_bm}
ncatted -a long_name,vpov_${basin},o,c,"potential ocean volume" ${scfile_bm}
ncatted -a units,vpov_${basin},o,c,"m3" ${scfile_bm}
/bin/rm ${tmp_af} ${tmp_sc}
# Corrected SLE
if $flg_pov; then
    ncap2 -A -s "sl_G2020_${basin}=(vaf_${basin}+vden_${basin}+vpov_${basin})/oarea" ${scfile_bm} ${scfile_bm} 
    ncatted -a long_name,sl_G2020_${basin},o,c,"corrected sealevel equivalent ice mass (af+den+pov)" ${scfile_bm}
else
    ncap2 -A -s "sl_G2020_${basin}=(vaf_${basin}+vden_${basin})/oarea" ${scfile_bm} ${scfile_bm} 
    ncatted -a long_name,sl_G2020_${basin},o,c,"corrected sealevel equivalent ice mass (af+den)" ${scfile_bm}
fi
ncatted -a standard_name,sl_G2020_${basin},d,, ${scfile_bm}
ncatted -a units,sl_G2020_${basin},o,c,"m" ${scfile_bm}


done
/bin/rm ${tmp_file}

# clean up
ncatted -h -a history,global,d,, ${scfile_bm}
ncatted -h -a history_of_appended_files,global,d,, ${scfile_bm}
ncatted -h -a NCO,global,d,, ${scfile_bm}
ncatted -h -a CDO,global,d,, ${scfile_bm}
ncatted -h -a CDI,global,d,, ${scfile_bm}
ncatted -h -a Description,global,d,, ${scfile_bm}
ncatted -h -a proj4,global,d,, ${scfile_bm}
# Add info
ncatted -h -a Description,global,o,c,"ISMIP7 scalar output. Heiko Goelzer 2026, heig@norceresearch.no" ${scfile_bm}

fi

##################################################################################


# Clean up
/bin/rm ${procpath}/af2.nc ${procpath}/masksOBS.nc ${procpath}/afGIC.nc
/bin/rm ${procpath}/icemasks.nc ${procpath}/basins.nc ${procpath}/maxmask1.nc 
/bin/rm ${procpath}/model.nc ${procpath}/mainproc.nc ${procpath}/params.nc 
