#!/bin/bash
# Interpolate to new grid0

m1path=/Users/heig/Desktop/Output/Models/MINI/ISMIP7/MINI1
m0path=/Users/heig/Desktop/Output/Models/MINI/ISMIP7/MINI0
gdfpath=./

#exp=exp0
exp=expg

mkdir -p ${m0path}/${exp}

for avar in lithk topg sftgif sftgrf sftflf; do

    ./remapCDO.sh ${m1path}/${exp}/${avar}_AIS_ISMIP7_MINI1_${exp}.nc ${m0path}/${exp}/${avar}_AIS_ISMIP7_MINI0_${exp}.nc ${gdfpath}/gdf_ISMIP7_MINI1.txt ${gdfpath}/gdf_ISMIP7_MINI0.txt ycon

done
