#!/bin/bash
# Interpolate to new grid0

SETUP_DIR=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$SETUP_DIR/../../.." && pwd)

m1path=$ROOT/Models/MINI/ISMIP7/MINI1
m0path=$ROOT/Models/MINI/ISMIP7/MINI0
gdfpath=$SETUP_DIR

#exp=exp0
exp=expg

mkdir -p ${m0path}/${exp}

for avar in lithk topg sftgif sftgrf sftflf; do

    "$SETUP_DIR/remapCDO.sh" ${m1path}/${exp}/${avar}_AIS_ISMIP7_MINI1_${exp}.nc ${m0path}/${exp}/${avar}_AIS_ISMIP7_MINI0_${exp}.nc ${gdfpath}/gdf_ISMIP7_MINI1.txt ${gdfpath}/gdf_ISMIP7_MINI0.txt ycon

done
