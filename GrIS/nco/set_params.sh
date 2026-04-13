#!/bin/bash
# Create model specific parameter file

set -x 
set -e

# User settings
lab=NORCE
model=CISM08-MAR312-p50

# Path to model output
modelpath=../../../Models/GrIS

apar=${modelpath}/${lab}/${model}/params.nc
ncap2 -3 -O -s 'rhoi=917.; rhow=1026.; rhof=1000.' ${apar}
ncks -A params_template.nc ${apar}
