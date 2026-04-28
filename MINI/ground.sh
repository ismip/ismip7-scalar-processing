#!/bin/bash
# make grounded by increasing the bed

m1path=/Users/heig/Desktop/Output/Models/MINI/ISMIP7/MINI1

exp=expg

# make new dir
mkdir -p ${m1path}/${exp}

# ice thickness unchanged
/bin/cp ${m1path}/exp0/lithk_AIS_ISMIP7_MINI1_exp0.nc ${m1path}/${exp}/lithk_AIS_ISMIP7_MINI1_${exp}.nc

# update bed and masks
ncap2 -O -s "topg=topg+10000." -v ${m1path}/exp0/topg_AIS_ISMIP7_MINI1_exp0.nc ${m1path}/${exp}/topg_AIS_ISMIP7_MINI1_${exp}.nc 

# ice mask unchanged
/bin/cp ${m1path}/exp0/sftgif_AIS_ISMIP7_MINI1_exp0.nc ${m1path}/${exp}/sftgif_AIS_ISMIP7_MINI1_${exp}.nc
# no more floating ice
ncap2 -O -s "sftflf=sftflf*0." -v ${m1path}/exp0/sftflf_AIS_ISMIP7_MINI1_exp0.nc ${m1path}/${exp}/sftflf_AIS_ISMIP7_MINI1_${exp}.nc 
# grounded mask same as full ice mask
ncap2 -O -s "sftgrf=sftgif" -v ${m1path}/exp0/sftgif_AIS_ISMIP7_MINI1_exp0.nc ${m1path}/${exp}/sftgrf_AIS_ISMIP7_MINI1_${exp}.nc 

