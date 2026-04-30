#!/bin/bash
# Provied in- and output file names with .nc suffix !
# Specify GDFs with full path
# Note: use -setmisstoc to remove NaN only where it makes sense (masks, lithk, orog) 

set -x
set -e

# input/output files
infile=$1
outfile=$2

# input/output grid description files
ingdf=$3
outgdf=$4

# regridding type: nn, bil, ycon
rtype=$5

##################

# check parameters
# TODo

#################

if [[ "$rtype" == "nn" ]]; then
    # Nearest neighbor
    cdo remapnn,${outgdf} -setgrid,${ingdf} ${infile} ${outfile}

elif [[ "$rtype" == "bil" ]]; then
    # Bilinear
    cdo remapbil,${outgdf} -setgrid,${ingdf} ${infile} ${outfile}
    
elif [[ "$rtype" == "ycon" ]]; then
    # Conservative
    cdo remapycon,${outgdf} -setgrid,${ingdf} ${infile} ${outfile}

else 
    echo "Remapping method unknown; choices are nn, bil, ycon"
fi
