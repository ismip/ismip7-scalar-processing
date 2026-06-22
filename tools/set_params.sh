#!/bin/bash
# Create model-specific parameter file (params.nc) for a given group/model.
#
# Usage:
#   bash tools/set_params.sh <region> <group> <model> [rhoi] [rhow] [rhof]
#
# Arguments:
#   region   AIS or GrIS
#   group    Submitting group/lab (e.g. NORCE, VUW)
#   model    Ice sheet model name (e.g. CISM16x-MAR312-p50, PISM1)
#   rhoi     Ice density in kg/m³       (default: 917)
#   rhow     Ocean water density kg/m³  (default: 1027)
#   rhof     Freshwater density kg/m³   (default: 1000)
#
# Examples:
#   bash tools/set_params.sh GrIS NORCE CISM16x-MAR312-p50
#   bash tools/set_params.sh AIS  VUW   PISM1 910 1028 1000

set -e

if [ "$#" -lt 3 ]; then
    echo "Usage: bash tools/set_params.sh <region> <group> <model> [rhoi] [rhow] [rhof]"
    exit 1
fi

region=$1
group=$2
model=$3
rhoi=${4:-917}
rhow=${5:-1027}
rhof=${6:-1000}

modelpath="../Models/${region}"
apar="${modelpath}/${group}/${model}/params.nc"

mkdir -p "$(dirname "$apar")"
ncap2 -3 -O -s "rhoi=${rhoi}.; rhow=${rhow}.; rhof=${rhof}." "${apar}"
ncks -A params_template.nc "${apar}"

echo "Written: ${apar}  (rhoi=${rhoi}, rhow=${rhow}, rhof=${rhof})"
