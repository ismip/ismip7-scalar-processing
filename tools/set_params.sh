#!/bin/bash
# Create model-specific parameter file (params.nc) for a given group/model.
#
# Usage:
#   bash tools/set_params.sh <region> <group> <model> [rhoi] [rhow] [rhof]
#   bash tools/set_params.sh <region> <group> <model> [rhoi] [rhow] [rhof] \
#       --modelpath /path/to/models/{region}
#
# Arguments:
#   region        AIS or GrIS
#   group         Submitting group/lab (e.g. NORCE, VUW)
#   model         Ice sheet model name (e.g. CISM16x-MAR312-p50, PISM1)
#   rhoi          Ice density in kg/m³       (default: 917)
#   rhow          Ocean water density kg/m³  (default: 1027)
#   rhof          Freshwater density kg/m³   (default: 1000)
#   --modelpath   Root for model output of one region (default: Models/<region>
#                 relative to the repo root). params.nc is written to
#                 <modelpath>/<group>/<model>/params.nc.
#
# Examples:
#   bash tools/set_params.sh GrIS NORCE CISM16x-MAR312-p50
#   bash tools/set_params.sh AIS  VUW   PISM1 910 1028 1000
#   bash tools/set_params.sh AIS  ISMIP7 SYNTH1 \
#       --modelpath /nird/.../ISM_SimulationChecker/Models/AIS

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TEMPLATE="${SCRIPT_DIR}/params_template.nc"

if [ "$#" -lt 3 ]; then
    echo "Usage: bash tools/set_params.sh <region> <group> <model>" \
         "[rhoi] [rhow] [rhof] [--modelpath <path>]"
    exit 1
fi

region=$1; group=$2; model=$3
shift 3

# Defaults
rhoi=917; rhow=1027; rhof=1000
modelpath="${REPO_ROOT}/Models/${region}"

# Parse remaining: bare numbers fill rhoi/rhow/rhof in order; --modelpath is named
density_idx=0
while [ "$#" -gt 0 ]; do
    case "$1" in
        --modelpath) modelpath="$2"; shift 2 ;;
        --*) echo "Unknown option: $1"; exit 1 ;;
        *)
            case $density_idx in
                0) rhoi="$1" ;;
                1) rhow="$1" ;;
                2) rhof="$1" ;;
            esac
            density_idx=$((density_idx + 1))
            shift ;;
    esac
done

apar="${modelpath}/${group}/${model}/params.nc"

mkdir -p "$(dirname "$apar")"
ncap2 -3 -O -s "rhoi=${rhoi}.; rhow=${rhow}.; rhof=${rhof}." "${apar}"
ncks -A "${TEMPLATE}" "${apar}"

echo "Written: ${apar}  (rhoi=${rhoi}, rhow=${rhow}, rhof=${rhof})"
