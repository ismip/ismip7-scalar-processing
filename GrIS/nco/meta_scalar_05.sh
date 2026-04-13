#!/bin/bash
# Calculate scalar values for a number of models/experiments

set -x
set -e

# location of Archive
#outp=/Volumes/ISMIP6/ISMIP6-Greenland/Archive_05/Data
outp=/nird/projects/NS8085K/PROTECT-GrIS/Results/protect-gris-results-processing/Archive_05/Data

# Destination for scalar files
outpsc=/nird/projects/NS8085K/PROTECT-GrIS/Results/protect-gris-results-processing/Archive_sc/Data

## Settings
# Remove GIC contribution? 
#flg_GICmask=false # [Default true!]
flg_GICmask=true # [Default true!]
# Remove ice outside observed ice mask (can be combined with GIC masking) 
flg_OBSmask=false # [Default false!]

ares=05

## labs/models lists
#declare -a labs=(VUB)
#declare -a models=(GISMSIAv1)
#exps="ACCESS1.3-rcp85_MARv3.12_p25 ACCESS1.3-rcp85_MARv3.12_p50 ACCESS1.3-rcp85_MARv3.12_p75 CESM2-Leo-ssp585_MARv3.12_p25 CESM2-Leo-ssp585_MARv3.12_p50 CESM2-Leo-ssp585_MARv3.12_p75 CNRM-CM6-ssp585_MARv3.12_p25 CNRM-CM6-ssp585_MARv3.12_p50 CNRM-CM6-ssp585_MARv3.12_p75 MPI-ESM1-2-HR-ssp126_MARv3.12_p25 MPI-ESM1-2-HR-ssp126_MARv3.12_p50 MPI-ESM1-2-HR-ssp126_MARv3.12_p75 MPI-ESM1-2-HR-ssp245_MARv3.12_p25 MPI-ESM1-2-HR-ssp245_MARv3.12_p50 MPI-ESM1-2-HR-ssp245_MARv3.12_p75 MPI-ESM1-2-HR-ssp585_MARv3.12_p25 MPI-ESM1-2-HR-ssp585_MARv3.12_p50 MPI-ESM1-2-HR-ssp585_MARv3.12_p75 UKESM1-0-LL-Robin-ssp585_MARv3.12_p25 UKESM1-0-LL-Robin-ssp585_MARv3.12_p50 UKESM1-0-LL-Robin-ssp585_MARv3.12_p75 ctrl-proj historical"

## labs/models lists
#declare -a labs=(VUB)
#declare -a models=(GISMHOMv1)
#exps="ctrl-proj historical"
#exps="ACCESS1.3-rcp85_MARv3.12_high ACCESS1.3-rcp85_MARv3.12_low ACCESS1.3-rcp85_MARv3.12_med ACCESS1.3-rcp85_MARv3.9_high ACCESS1.3-rcp85_MARv3.9_low ACCESS1.3-rcp85_MARv3.9_med CESM2-ssp585_MARv3.12_high CESM2-ssp585_MARv3.12_low CESM2-ssp585_MARv3.12_med CESM2-ssp585_MARv3.9_high CESM2-ssp585_MARv3.9_low CESM2-ssp585_MARv3.9_med CNRM-CM6-ssp126_MARv3.9_high CNRM-CM6-ssp126_MARv3.9_low CNRM-CM6-ssp126_MARv3.9_med CNRM-CM6-ssp585_MARv3.12_high CNRM-CM6-ssp585_MARv3.12_low CNRM-CM6-ssp585_MARv3.12_med CNRM-CM6-ssp585_MARv3.9_high CNRM-CM6-ssp585_MARv3.9_low CNRM-CM6-ssp585_MARv3.9_med CNRM-ESM2-ssp585_MARv3.12_high CNRM-ESM2-ssp585_MARv3.12_low CNRM-ESM2-ssp585_MARv3.12_med CNRM-ESM2-ssp585_MARv3.9_high CNRM-ESM2-ssp585_MARv3.9_low CNRM-ESM2-ssp585_MARv3.9_med CSIRO-Mk3.6-rcp85_MARv3.9_high CSIRO-Mk3.6-rcp85_MARv3.9_low CSIRO-Mk3.6-rcp85_MARv3.9_med HadGEM2-ES-rcp85_MARv3.9_high HadGEM2-ES-rcp85_MARv3.9_low HadGEM2-ES-rcp85_MARv3.9_med IPSL-CM5-MR-rcp85_MARv3.9_high IPSL-CM5-MR-rcp85_MARv3.9_low IPSL-CM5-MR-rcp85_MARv3.9_med MIROC5-rcp26_MARv3.9_high MIROC5-rcp26_MARv3.9_low MIROC5-rcp26_MARv3.9_med MIROC5-rcp85_MARv3.9_high MIROC5-rcp85_MARv3.9_low MIROC5-rcp85_MARv3.9_med MPI-ESM1-2-HR-ssp245_MARv3.12_high MPI-ESM1-2-HR-ssp245_MARv3.12_low MPI-ESM1-2-HR-ssp245_MARv3.12_med MPI-ESM1-2-HR-ssp585_MARv3.12_high MPI-ESM1-2-HR-ssp585_MARv3.12_low MPI-ESM1-2-HR-ssp585_MARv3.12_med NorESM1-rcp85_MARv3.9_high NorESM1-rcp85_MARv3.9_low NorESM1-rcp85_MARv3.9_med UKESM1-0-LL-ssp585_MARv3.12_high UKESM1-0-LL-ssp585_MARv3.12_low UKESM1-0-LL-ssp585_MARv3.12_med UKESM1-CM6-ssp585_MARv3.9_high UKESM1-CM6-ssp585_MARv3.9_low UKESM1-CM6-ssp585_MARv3.9_med"


## labs/models lists
##declare -a labs=(IMAU)
##declare -a models=(IMAUICE1)
#declare -a labs=(IMAU IMAU IMAU IMAU IMAU IMAU )
#declare -a models=(IMAUICE2 IMAUICE3 IMAUICE5 IMAUICE6 IMAUICE7 IMAUICE8)
#exps="ACCESS1.3-rcp85_MARv3.12_p25 ACCESS1.3-rcp85_MARv3.12_p50 ACCESS1.3-rcp85_MARv3.12_p75 ACCESS1.3-rcp85_MARv3.9_p25 ACCESS1.3-rcp85_MARv3.9_p50 ACCESS1.3-rcp85_MARv3.9_p75 CESM2-Leo-ssp585_MARv3.12_p25 CESM2-Leo-ssp585_MARv3.12_p50 CESM2-Leo-ssp585_MARv3.12_p75 CESM2-Leo-ssp585_MARv3.9_p25 CESM2-Leo-ssp585_MARv3.9_p50 CESM2-Leo-ssp585_MARv3.9_p75 CNRM-CM6-ssp126_MARv3.9_p25 CNRM-CM6-ssp126_MARv3.9_p50 CNRM-CM6-ssp126_MARv3.9_p75 CNRM-CM6-ssp585_MARv3.12_p25 CNRM-CM6-ssp585_MARv3.12_p50 CNRM-CM6-ssp585_MARv3.12_p75 CNRM-CM6-ssp585_MARv3.9_p25 CNRM-CM6-ssp585_MARv3.9_p50 CNRM-CM6-ssp585_MARv3.9_p75 CNRM-ESM2-ssp585_MARv3.9_p25 CNRM-ESM2-ssp585_MARv3.9_p50 CNRM-ESM2-ssp585_MARv3.9_p75 CSIRO-Mk3.6-rcp85_MARv3.9_p25 CSIRO-Mk3.6-rcp85_MARv3.9_p50 CSIRO-Mk3.6-rcp85_MARv3.9_p75 HadGEM2-ES-rcp85_MARv3.9_p25 HadGEM2-ES-rcp85_MARv3.9_p50 HadGEM2-ES-rcp85_MARv3.9_p75 IPSL-CM5-MR-rcp85_MARv3.9_p25 IPSL-CM5-MR-rcp85_MARv3.9_p50 IPSL-CM5-MR-rcp85_MARv3.9_p75 MIROC5-rcp26_MARv3.9_p25 MIROC5-rcp26_MARv3.9_p50 MIROC5-rcp26_MARv3.9_p75 MIROC5-rcp85_MARv3.9_p25 MIROC5-rcp85_MARv3.9_p50 MIROC5-rcp85_MARv3.9_p75 MPI-ESM1-2-HR-ssp126_MARv3.12_p25 MPI-ESM1-2-HR-ssp126_MARv3.12_p50 MPI-ESM1-2-HR-ssp126_MARv3.12_p75 MPI-ESM1-2-HR-ssp245_MARv3.12_p25 MPI-ESM1-2-HR-ssp245_MARv3.12_p50 MPI-ESM1-2-HR-ssp245_MARv3.12_p75 MPI-ESM1-2-HR-ssp585_MARv3.12_p25 MPI-ESM1-2-HR-ssp585_MARv3.12_p50 MPI-ESM1-2-HR-ssp585_MARv3.12_p75 NorESM1-rcp85_MARv3.9_p25 NorESM1-rcp85_MARv3.9_p50 NorESM1-rcp85_MARv3.9_p75 UKESM1-0-LL-Robin-ssp585_MARv3.12_p25 UKESM1-0-LL-Robin-ssp585_MARv3.12_p50 UKESM1-0-LL-Robin-ssp585_MARv3.12_p75 UKESM1-0-LL-Robin-ssp585_MARv3.9_p25 UKESM1-0-LL-Robin-ssp585_MARv3.9_p50 UKESM1-0-LL-Robin-ssp585_MARv3.9_p75 ctrl-proj historical"

## labs/models lists
#declare -a labs=(IGE)
##declare -a models=(ElmerIce2)
#declare -a models=(ElmerIce3)
##exps="ACCESS1.3-rcp85_MARv3.12_p25 ACCESS1.3-rcp85_MARv3.12_p50 ACCESS1.3-rcp85_MARv3.12_p75 CESM2-CMIP6-ssp126_RACMO2.3p2_p25 CESM2-CMIP6-ssp126_RACMO2.3p2_p50 CESM2-CMIP6-ssp126_RACMO2.3p2_p75 CESM2-Leo-ssp585_RACMO2.3p2_p25 CESM2-Leo-ssp585_RACMO2.3p2_p50 CESM2-Leo-ssp585_RACMO2.3p2_p75 MPI-ESM1-2-HR-ssp126_MARv3.12_p25 MPI-ESM1-2-HR-ssp126_MARv3.12_p50 MPI-ESM1-2-HR-ssp126_MARv3.12_p75 UKESM1-0-LL-Robin-ssp585_MARv3.12_p25 UKESM1-0-LL-Robin-ssp585_MARv3.12_p50 UKESM1-0-LL-Robin-ssp585_MARv3.12_p75 ctrl-proj historical"
#exps="CESM2-CMIP6-ssp126_RACMO2.3p2_p50"

# labs/models lists
#declare -a labs=(NORCE NORCE NORCE)
#declare -a models=(CISM04-MAR312-p25 CISM08-MAR312-p25 CISM16-MAR312-p25)
#exps="ACCESS1.3-rcp85_MARv3.12_p25 CESM2-CMIP6-ssp126_MARv3.12_p25 CESM2-CMIP6-ssp245_MARv3.12_p25 CESM2-CMIP6-ssp585_MARv3.12_p25 CESM2-Leo-ssp585_MARv3.12_p25 CNRM-CM6-ssp585_MARv3.12_p25 CNRM-ESM2-ssp585_MARv3.12_p25 IPSL-CM6A-LR-ssp585_MARv3.12_p25 MPI-ESM1-2-HR-ssp126_MARv3.12_p25 MPI-ESM1-2-HR-ssp245_MARv3.12_p25 MPI-ESM1-2-HR-ssp585_MARv3.12_p25 NorESM2-ssp245_MARv3.12_p25 NorESM2-ssp585_MARv3.12_p25 UKESM1-0-LL-CMIP6-ssp245_MARv3.12_p25 UKESM1-0-LL-CMIP6-ssp585_MARv3.12_p25 UKESM1-0-LL-Robin-ssp585_MARv3.12_p25 historical"
#declare -a models=(CISM04-MAR312-p50 CISM08-MAR312-p50 CISM16-MAR312-p50)
#exps="ACCESS1.3-rcp85_MARv3.12_p50 CESM2-CMIP6-ssp126_MARv3.12_p50 CESM2-CMIP6-ssp245_MARv3.12_p50 CESM2-CMIP6-ssp585_MARv3.12_p50 CESM2-Leo-ssp585_MARv3.12_p50 CNRM-CM6-ssp585_MARv3.12_p50 CNRM-ESM2-ssp585_MARv3.12_p50 IPSL-CM6A-LR-ssp585_MARv3.12_p50 MPI-ESM1-2-HR-ssp126_MARv3.12_p50 MPI-ESM1-2-HR-ssp245_MARv3.12_p50 MPI-ESM1-2-HR-ssp585_MARv3.12_p50 NorESM2-ssp245_MARv3.12_p50 NorESM2-ssp585_MARv3.12_p50 UKESM1-0-LL-CMIP6-ssp245_MARv3.12_p50 UKESM1-0-LL-CMIP6-ssp585_MARv3.12_p50 UKESM1-0-LL-Robin-ssp585_MARv3.12_p50 historical"
#declare -a models=(CISM04-MAR312-p75 CISM08-MAR312-p75 CISM16-MAR312-p75)
#exps="ctrl-proj ACCESS1.3-rcp85_MARv3.12_p75 CESM2-CMIP6-ssp126_MARv3.12_p75 CESM2-CMIP6-ssp245_MARv3.12_p75 CESM2-CMIP6-ssp585_MARv3.12_p75 CESM2-Leo-ssp585_MARv3.12_p75 CNRM-CM6-ssp585_MARv3.12_p75 CNRM-ESM2-ssp585_MARv3.12_p75 IPSL-CM6A-LR-ssp585_MARv3.12_p75 MPI-ESM1-2-HR-ssp126_MARv3.12_p75 MPI-ESM1-2-HR-ssp245_MARv3.12_p75 MPI-ESM1-2-HR-ssp585_MARv3.12_p75 NorESM2-ssp245_MARv3.12_p75 NorESM2-ssp585_MARv3.12_p75 UKESM1-0-LL-CMIP6-ssp245_MARv3.12_p75 UKESM1-0-LL-CMIP6-ssp585_MARv3.12_p75 UKESM1-0-LL-Robin-ssp585_MARv3.12_p75 historical"

## labs/models lists
#declare -a labs=(NORCE)
#declare -a models=(CISM16t-MAR39-p50)
#exps="historical"
#exps="CESM2-CMIP6-ssp126-r2300_RACMO2.3p2_p05 CESM2-CMIP6-ssp126-r2300_RACMO2.3p2_p25 CESM2-CMIP6-ssp126-r2300_RACMO2.3p2_p50 CESM2-CMIP6-ssp126-r2300_RACMO2.3p2_p75 CESM2-CMIP6-ssp126-r2300_RACMO2.3p2_p95 CESM2-CMIP6-ssp245-r2300_MARv3.12_p05 CESM2-CMIP6-ssp245-r2300_MARv3.12_p25 CESM2-CMIP6-ssp245-r2300_MARv3.12_p50 CESM2-CMIP6-ssp245-r2300_MARv3.12_p75 CESM2-CMIP6-ssp245-r2300_MARv3.12_p95 CESM2-CMIP6-ssp245-r2300_RACMO2.3p2_p05 CESM2-CMIP6-ssp245-r2300_RACMO2.3p2_p25 CESM2-CMIP6-ssp245-r2300_RACMO2.3p2_p50 CESM2-CMIP6-ssp245-r2300_RACMO2.3p2_p75 CESM2-CMIP6-ssp245-r2300_RACMO2.3p2_p95 IPSL-CM6A-LR_ssp585-r2300_MARv3.12_p05 IPSL-CM6A-LR_ssp585-r2300_MARv3.12_p25 IPSL-CM6A-LR_ssp585-r2300_MARv3.12_p50 IPSL-CM6A-LR_ssp585-r2300_MARv3.12_p75 IPSL-CM6A-LR_ssp585-r2300_MARv3.12_p95"

#exps="ACCESS1.3-rcp85_MARv3.12_p05_r2300 CESM2-Leo-ssp585_MARv3.12_p05_r2300 CESM2-Leo-ssp585_RACMO2.3p2_p05_r2300 CNRM-ESM2-ssp585_MARv3.12_p05_r2300 IPSL-CM6A-LR-ssp126_RACMO2.3p2_p05_r2300 IPSL-CM6A-LR-ssp245_MARv3.12_p05_r2300 IPSL-CM6A-LR-ssp245_RACMO2.3p2_p05_r2300 MPI-ESM1-2-HR-ssp126_MARv3.12_p05_r2300 MPI-ESM1-2-HR-ssp245_MARv3.12_p05_r2300 MPI-ESM1-2-HR-ssp585_MARv3.12_p05_r2300 UKESM1-0-LL-CMIP6-ssp585_MARv3.12_p05_r2300 UKESM1-0-LL-Robin-ssp585_MARv3.12_p05_r2300 UKESM1-0-LL-Robin-ssp585_MARv3.9_p05_r2300 ACCESS1.3-rcp85_MARv3.12_p25_r2300 CESM2-Leo-ssp585_MARv3.12_p25_r2300 CESM2-Leo-ssp585_RACMO2.3p2_p25_r2300 CNRM-ESM2-ssp585_MARv3.12_p25_r2300 IPSL-CM6A-LR-ssp126_RACMO2.3p2_p25_r2300 IPSL-CM6A-LR-ssp245_MARv3.12_p25_r2300 IPSL-CM6A-LR-ssp245_RACMO2.3p2_p25_r2300 MPI-ESM1-2-HR-ssp126_MARv3.12_p25_r2300 MPI-ESM1-2-HR-ssp245_MARv3.12_p25_r2300 MPI-ESM1-2-HR-ssp585_MARv3.12_p25_r2300 UKESM1-0-LL-CMIP6-ssp585_MARv3.12_p25_r2300 UKESM1-0-LL-Robin-ssp585_MARv3.12_p25_r2300 UKESM1-0-LL-Robin-ssp585_MARv3.9_p25_r2300 ACCESS1.3-rcp85_MARv3.12_p50_r2300 CESM2-Leo-ssp585_MARv3.12_p50_r2300 CESM2-Leo-ssp585_RACMO2.3p2_p50_r2300 CNRM-ESM2-ssp585_MARv3.12_p50_r2300 IPSL-CM6A-LR-ssp126_RACMO2.3p2_p50_r2300 IPSL-CM6A-LR-ssp245_MARv3.12_p50_r2300 IPSL-CM6A-LR-ssp245_RACMO2.3p2_p50_r2300 MPI-ESM1-2-HR-ssp126_MARv3.12_p50_r2300 MPI-ESM1-2-HR-ssp245_MARv3.12_p50_r2300 MPI-ESM1-2-HR-ssp585_MARv3.12_p50_r2300 UKESM1-0-LL-CMIP6-ssp585_MARv3.12_p50_r2300 UKESM1-0-LL-Robin-ssp585_MARv3.12_p50_r2300 UKESM1-0-LL-Robin-ssp585_MARv3.9_p50_r2300 ACCESS1.3-rcp85_MARv3.12_p75_r2300 CESM2-Leo-ssp585_MARv3.12_p75_r2300 CESM2-Leo-ssp585_RACMO2.3p2_p75_r2300 CNRM-ESM2-ssp585_MARv3.12_p75_r2300 IPSL-CM6A-LR-ssp126_RACMO2.3p2_p75_r2300 IPSL-CM6A-LR-ssp245_MARv3.12_p75_r2300 IPSL-CM6A-LR-ssp245_RACMO2.3p2_p75_r2300 MPI-ESM1-2-HR-ssp126_MARv3.12_p75_r2300 MPI-ESM1-2-HR-ssp245_MARv3.12_p75_r2300 MPI-ESM1-2-HR-ssp585_MARv3.12_p75_r2300 UKESM1-0-LL-CMIP6-ssp585_MARv3.12_p75_r2300 UKESM1-0-LL-Robin-ssp585_MARv3.12_p75_r2300 UKESM1-0-LL-Robin-ssp585_MARv3.9_p75_r2300 ACCESS1.3-rcp85_MARv3.12_p95_r2300 CESM2-Leo-ssp585_MARv3.12_p95_r2300 CESM2-Leo-ssp585_RACMO2.3p2_p95_r2300 CNRM-ESM2-ssp585_MARv3.12_p95_r2300 IPSL-CM6A-LR-ssp126_RACMO2.3p2_p95_r2300 IPSL-CM6A-LR-ssp245_MARv3.12_p95_r2300 IPSL-CM6A-LR-ssp245_RACMO2.3p2_p95_r2300 MPI-ESM1-2-HR-ssp126_MARv3.12_p95_r2300 MPI-ESM1-2-HR-ssp245_MARv3.12_p95_r2300 MPI-ESM1-2-HR-ssp585_MARv3.12_p95_r2300 UKESM1-0-LL-CMIP6-ssp585_MARv3.12_p95_r2300 UKESM1-0-LL-Robin-ssp585_MARv3.12_p95_r2300 UKESM1-0-LL-Robin-ssp585_MARv3.9_p95_r2300"

# check problems with
#exps="UKESM1-0-LL-CMIP6-ssp585_MARv3.12_p50_r2300"

#exps="UKESM1-0-LL-Robin-ssp585_MARv3.12_p50_r2300 UKESM1-0-LL-Robin-ssp585_MARv3.9_p50_r2300 ACCESS1.3-rcp85_MARv3.12_p75_r2300 CESM2-Leo-ssp585_MARv3.12_p75_r2300 CESM2-Leo-ssp585_RACMO2.3p2_p75_r2300 CNRM-ESM2-ssp585_MARv3.12_p75_r2300 IPSL-CM6A-LR-ssp126_RACMO2.3p2_p75_r2300 IPSL-CM6A-LR-ssp245_MARv3.12_p75_r2300 IPSL-CM6A-LR-ssp245_RACMO2.3p2_p75_r2300 MPI-ESM1-2-HR-ssp126_MARv3.12_p75_r2300 MPI-ESM1-2-HR-ssp245_MARv3.12_p75_r2300 MPI-ESM1-2-HR-ssp585_MARv3.12_p75_r2300 UKESM1-0-LL-CMIP6-ssp585_MARv3.12_p75_r2300 UKESM1-0-LL-Robin-ssp585_MARv3.12_p75_r2300 UKESM1-0-LL-Robin-ssp585_MARv3.9_p75_r2300 ACCESS1.3-rcp85_MARv3.12_p95_r2300 CESM2-Leo-ssp585_MARv3.12_p95_r2300 CESM2-Leo-ssp585_RACMO2.3p2_p95_r2300 CNRM-ESM2-ssp585_MARv3.12_p95_r2300 IPSL-CM6A-LR-ssp126_RACMO2.3p2_p95_r2300 IPSL-CM6A-LR-ssp245_MARv3.12_p95_r2300 IPSL-CM6A-LR-ssp245_RACMO2.3p2_p95_r2300 MPI-ESM1-2-HR-ssp126_MARv3.12_p95_r2300 MPI-ESM1-2-HR-ssp245_MARv3.12_p95_r2300 MPI-ESM1-2-HR-ssp585_MARv3.12_p95_r2300 UKESM1-0-LL-CMIP6-ssp585_MARv3.12_p95_r2300 UKESM1-0-LL-Robin-ssp585_MARv3.12_p95_r2300 UKESM1-0-LL-Robin-ssp585_MARv3.9_p95_r2300"

#exps="ctrl-proj_r2300"

#declare -a labs=(NORCE)
#declare -a models=(CISM16-MAR312-p25)
#exps="CESM2-Leo-ssp585_MARv3.12_p25"


## labs/models lists
#declare -a labs=(NORCE)
#declare -a models=(CISM16c-MAR312-p50)
##exps="ACCESS1.3-rcp85_MARv3.12_p50 CESM2-CMIP6-ssp126_MARv3.12_p50 CESM2-CMIP6-ssp126_RACMO2.3p2_p50 CESM2-CMIP6-ssp245_MARv3.12_p50 CESM2-CMIP6-ssp245_RACMO2.3p2_p50 CESM2-CMIP6-ssp585_MARv3.12_p50 CESM2-Leo-ssp585_MARv3.12_p50 CESM2-Leo-ssp585_RACMO2.3p2_p50 CNRM-CM6-ssp585_MARv3.12_p50 CNRM-ESM2-ssp585_MARv3.12_p50 IPSL-CM6A-LR-ssp585_MARv3.12_p50 MPI-ESM1-2-HR-ssp126_MARv3.12_p50 MPI-ESM1-2-HR-ssp245_MARv3.12_p50 MPI-ESM1-2-HR-ssp585_MARv3.12_p50 NorESM2-ssp245_MARv3.12_p50 NorESM2-ssp585_MARv3.12_p50 UKESM1-0-LL-CMIP6-ssp245_MARv3.12_p50 UKESM1-0-LL-CMIP6-ssp585_MARv3.12_p50 UKESM1-0-LL-Robin-ssp585_MARv3.12_p50 ctrl-proj historical"
#exps="CESM2-Leo_ssp585_HIRHAM5_p50 EC-Earth3_ssp126_HIRHAM5_p50 EC-Earth3_ssp585_HIRHAM5_p50"

## labs/models lists
#declare -a labs=(NORCE)
#declare -a models=(CISM16c-MAR312-p25)
##exps="ACCESS1.3-rcp85_MARv3.12_p25 CESM2-CMIP6-ssp126_MARv3.12_p25 CESM2-CMIP6-ssp126_RACMO2.3p2_p25 CESM2-CMIP6-ssp245_MARv3.12_p25 CESM2-CMIP6-ssp245_RACMO2.3p2_p25 CESM2-CMIP6-ssp585_MARv3.12_p25 CESM2-Leo-ssp585_MARv3.12_p25 CESM2-Leo-ssp585_RACMO2.3p2_p25 CNRM-CM6-ssp585_MARv3.12_p25 CNRM-ESM2-ssp585_MARv3.12_p25 IPSL-CM6A-LR-ssp585_MARv3.12_p25 MPI-ESM1-2-HR-ssp126_MARv3.12_p25 MPI-ESM1-2-HR-ssp245_MARv3.12_p25 MPI-ESM1-2-HR-ssp585_MARv3.12_p25 NorESM2-ssp245_MARv3.12_p25 NorESM2-ssp585_MARv3.12_p25 UKESM1-0-LL-CMIP6-ssp245_MARv3.12_p25 UKESM1-0-LL-CMIP6-ssp585_MARv3.12_p25 UKESM1-0-LL-Robin-ssp585_MARv3.12_p25 ctrl-proj historical"
#exps="CESM2-Leo_ssp585_HIRHAM5_p25 EC-Earth3_ssp126_HIRHAM5_p25 EC-Earth3_ssp585_HIRHAM5_p25"

## labs/models lists
#declare -a labs=(NORCE)
#declare -a models=(CISM16c-MAR312-p75)
##exps="ACCESS1.3-rcp85_MARv3.12_p75 CESM2-CMIP6-ssp126_MARv3.12_p75 CESM2-CMIP6-ssp126_RACMO2.3p2_p75 CESM2-CMIP6-ssp245_MARv3.12_p75 CESM2-CMIP6-ssp245_RACMO2.3p2_p75 CESM2-CMIP6-ssp585_MARv3.12_p75 CESM2-Leo-ssp585_MARv3.12_p75 CESM2-Leo-ssp585_RACMO2.3p2_p75 CNRM-CM6-ssp585_MARv3.12_p75 CNRM-ESM2-ssp585_MARv3.12_p75 IPSL-CM6A-LR-ssp585_MARv3.12_p75 MPI-ESM1-2-HR-ssp126_MARv3.12_p75 MPI-ESM1-2-HR-ssp245_MARv3.12_p75 MPI-ESM1-2-HR-ssp585_MARv3.12_p75 NorESM2-ssp245_MARv3.12_p75 NorESM2-ssp585_MARv3.12_p75 UKESM1-0-LL-CMIP6-ssp245_MARv3.12_p75 UKESM1-0-LL-CMIP6-ssp585_MARv3.12_p75 UKESM1-0-LL-Robin-ssp585_MARv3.12_p75 ctrl-proj historical"
#exps="CESM2-Leo_ssp585_HIRHAM5_p75 EC-Earth3_ssp126_HIRHAM5_p75 EC-Earth3_ssp585_HIRHAM5_p75"

## labs/models lists
#declare -a labs=(NORCE)
#declare -a models=(CISM16c-MAR312-p05)
##exps="ACCESS1.3-rcp85_MARv3.12_p05 CESM2-CMIP6-ssp126_MARv3.12_p05 CESM2-CMIP6-ssp126_RACMO2.3p2_p05 CESM2-CMIP6-ssp245_MARv3.12_p05 CESM2-CMIP6-ssp245_RACMO2.3p2_p05 CESM2-CMIP6-ssp585_MARv3.12_p05 CESM2-Leo-ssp585_MARv3.12_p05 CESM2-Leo-ssp585_RACMO2.3p2_p05 CNRM-CM6-ssp585_MARv3.12_p05 CNRM-ESM2-ssp585_MARv3.12_p05 IPSL-CM6A-LR-ssp585_MARv3.12_p05 MPI-ESM1-2-HR-ssp126_MARv3.12_p05 MPI-ESM1-2-HR-ssp245_MARv3.12_p05 MPI-ESM1-2-HR-ssp585_MARv3.12_p05 NorESM2-ssp245_MARv3.12_p05 NorESM2-ssp585_MARv3.12_p05 UKESM1-0-LL-CMIP6-ssp245_MARv3.12_p05 UKESM1-0-LL-CMIP6-ssp585_MARv3.12_p05 UKESM1-0-LL-Robin-ssp585_MARv3.12_p05 ctrl-proj historical"
#exps="CESM2-Leo_ssp585_HIRHAM5_p05 EC-Earth3_ssp126_HIRHAM5_p05 EC-Earth3_ssp585_HIRHAM5_p05"

# labs/models lists
declare -a labs=(NORCE)
declare -a models=(CISM16c-MAR312-p95)
#exps="ACCESS1.3-rcp85_MARv3.12_p95 CESM2-CMIP6-ssp126_MARv3.12_p95 CESM2-CMIP6-ssp126_RACMO2.3p2_p95 CESM2-CMIP6-ssp245_MARv3.12_p95 CESM2-CMIP6-ssp245_RACMO2.3p2_p95 CESM2-CMIP6-ssp585_MARv3.12_p95 CESM2-Leo-ssp585_MARv3.12_p95 CESM2-Leo-ssp585_RACMO2.3p2_p95 CNRM-CM6-ssp585_MARv3.12_p95 CNRM-ESM2-ssp585_MARv3.12_p95 IPSL-CM6A-LR-ssp585_MARv3.12_p95 MPI-ESM1-2-HR-ssp126_MARv3.12_p95 MPI-ESM1-2-HR-ssp245_MARv3.12_p95 MPI-ESM1-2-HR-ssp585_MARv3.12_p95 NorESM2-ssp245_MARv3.12_p95 NorESM2-ssp585_MARv3.12_p95 UKESM1-0-LL-CMIP6-ssp245_MARv3.12_p95 UKESM1-0-LL-CMIP6-ssp585_MARv3.12_p95 UKESM1-0-LL-Robin-ssp585_MARv3.12_p95 ctrl-proj historical"
exps="CESM2-Leo_ssp585_HIRHAM5_p95 EC-Earth3_ssp126_HIRHAM5_p95 EC-Earth3_ssp585_HIRHAM5_p95"

## labs/models lists
#declare -a labs=(NORCE)
#declare -a models=(CISM16x-MAR312-p50)
#exps=`ls /projects/NS8085K/PROTECT/Results/protect-gris-results-processing/Archive_05/Data/NORCE/CISM16x-MAR312-p50 | grep IPSL`
##exps="historical"

## labs/models lists
#declare -a labs=(NORCE)
#declare -a models=(CISM16x-MAR312-p25)
#exps=`ls /projects/NS8085K/PROTECT/Results/protect-gris-results-processing/Archive_05/Data/NORCE/CISM16x-MAR312-p25 | grep IPSL`
##exps="historical"

## labs/models lists
#declare -a labs=(NORCE)
#declare -a models=(CISM16x-MAR312-p75)
#exps=`ls /projects/NS8085K/PROTECT/Results/protect-gris-results-processing/Archive_05/Data/NORCE/CISM16x-MAR312-p75 | grep IPSL`
##exps="historical"

## labs/models lists
#declare -a labs=(NORCE)
#declare -a models=(CISM16x-MAR312-p05)
#exps=`ls /projects/NS8085K/PROTECT/Results/protect-gris-results-processing/Archive_05/Data/NORCE/CISM16x-MAR312-p05  | grep IPSL`
##exps="historical"

## labs/models lists
#declare -a labs=(NORCE)
#declare -a models=(CISM16x-MAR312-p95)
#exps=`ls /projects/NS8085K/PROTECT/Results/protect-gris-results-processing/Archive_05/Data/NORCE/CISM16x-MAR312-p95 | grep IPSL`
#exps="historical"

######### Charlotte ext e2200
### labs/models lists
#declare -a labs=(NORCE)
#declare -a models=(CISM04e-MAR312-p50)
##exps="IPSL-CM6A-LR_ssp585-e2200_MARv3.12_p50"
#exps="historical"

### labs/models lists
#declare -a labs=(NORCE)
#declare -a models=(CISM04e-MAR312-p25)
##exps="IPSL-CM6A-LR_ssp585-e2200_MARv3.12_p25"
#exps="historical"

### labs/models lists
#declare -a labs=(NORCE)
#declare -a models=(CISM04e-MAR312-p75)
##exps="IPSL-CM6A-LR_ssp585-e2200_MARv3.12_p75"
#exps="historical"

### labs/models lists
#declare -a labs=(NORCE)
#declare -a models=(CISM04e-MAR312-p05)
##exps="IPSL-CM6A-LR_ssp585-e2200_MARv3.12_p05"
#exps="historical"

### labs/models lists
#declare -a labs=(NORCE)
#declare -a models=(CISM04e-MAR312-p95)
##exps="IPSL-CM6A-LR_ssp585-e2200_MARv3.12_p95"
#exps="historical"


## labs/models lists
#declare -a labs=(NORCE)
#declare -a models=(CISM04-MAR312-p50)
#exps="CESM2_ssp126_MARv3.12_p50 CESM2_ssp245_MARv3.12_p50 CESM2_ssp585_MARv3.12_p50 MPI-ESM1-2-HR_ssp126_MARv3.12_p50 MPI-ESM1-2-HR_ssp245_MARv3.12_p50 MPI-ESM1-2-HR_ssp585_MARv3.12_p50 NorESM2-MM_ssp245_MARv3.12_p50 NorESM2-MM_ssp585_MARv3.12_p50 historical"

#declare -a labs=(NORCE)
#declare -a models=(CISM16x-MAR312-p05)
#exps="IPSL-CM6A-LR_ssp585-x2300_MARv3.13-e05_p05 IPSL-CM6A-LR_ssp585-x2300_MARv3.13-e05_pno"
#declare -a labs=(NORCE)
#declare -a models=(CISM16x-MAR312-p95)
#exps="IPSL-CM6A-LR_ssp585-x2300_MARv3.13-e05_p95 IPSL-CM6A-LR_ssp585-x2300_MARv3.13-e05_pno"

### Overshoots
#declare -a labs=(NORCE)
#declare -a models=(CISM16oc-MAR39-p25)
#exps=`ls /projects/NS8085K/PROTECT-GrIS/Results/protect-gris-results-processing/Archive_05/Data/NORCE/CISM16oc-MAR39-p25`


# array sizes match
if [ ${#labs[@]} -eq ${#models[@]} ]; then 
    count=${#models[@]}
else
    echo Error: length of labs and models has to match  
    exit 1
fi

##### 
echo "------------------"
echo  netcdf calculations
echo "------------------"

# loop trough labs/models
counter=0
while [ $counter -lt ${count} ]; do

    echo ${labs[$counter]} ${models[$counter]}

    proc=${labs[$counter]}_${models[$counter]}
    mkdir -p ${proc}
    cd ${proc}

    # A. set exps manually above

    # B. find experiments automatically
    #dexps=`find ${outp}/${labs[$counter]}/${models[$counter]}/* -maxdepth 0 -type d`
    #exps=`basename -a ${dexps}`

    echo "###"
    echo ${exps}

    
    # loop trough experiments to calculate scalars
    for exp in ${exps}; do

	apath=${outp}/${labs[$counter]}/${models[$counter]}/${exp}
	# input file name
	anc=${apath}/lithk_GIS_${labs[$counter]}_${models[$counter]}_${exp}.nc
	ncks -3 -O -v lithk ${anc} model_pre.nc
	anc=${apath}/topg_GIS_${labs[$counter]}_${models[$counter]}_${exp}.nc
	ncks -3 -A -v topg ${anc} model_pre.nc

	anc=${apath}/sftflf_GIS_${labs[$counter]}_${models[$counter]}_${exp}.nc
	ncks -3 -A -v sftflf ${anc} model_pre.nc
	anc=${apath}/sftgif_GIS_${labs[$counter]}_${models[$counter]}_${exp}.nc
	ncks -3 -A -v sftgif ${anc} model_pre.nc
	anc=${apath}/sftgrf_GIS_${labs[$counter]}_${models[$counter]}_${exp}.nc
	ncks -3 -A -v sftgrf ${anc} model_pre.nc

	# set missing to zero like during interpolation 
	cdo -setmisstoc,0.0  model_pre.nc model.nc 

	# Add model params
	ncks -3 -A ${outp}/${labs[$counter]}/${models[$counter]}/params.nc model.nc

	### scalar calculations; expect model input in model.nc
	../scalars_basin_slc.sh $flg_GICmask $flg_OBSmask 05

	# Make settings specific output paths
	prefix=SC
	# Remove GIC contribution? 
	if $flg_GICmask; then
	    prefix=${prefix}_GIC1
	else
	    prefix=${prefix}_GIC0
	fi
	# Mask to observed?
	if $flg_OBSmask; then
	    prefix=${prefix}_OBS1
	else
	    prefix=${prefix}_OBS0
	fi
	destpath=${outpsc}/${prefix}/${labs[$counter]}/${models[$counter]}/${exp}
	mkdir -p ${destpath}
	### move output ./scalars_??_05.nc to Archive
	[ -f ./scalars_mm_05.nc ] && /bin/mv ./scalars_mm_05.nc ${destpath}/scalars_mm_GIS_${labs[$counter]}_${models[$counter]}_${exp}.nc
	[ -f ./scalars_rm_05.nc ] && /bin/mv ./scalars_rm_05.nc ${destpath}/scalars_rm_GIS_${labs[$counter]}_${models[$counter]}_${exp}.nc
	[ -f ./scalars_zm_05.nc ] && /bin/mv ./scalars_zm_05.nc ${destpath}/scalars_zm_GIS_${labs[$counter]}_${models[$counter]}_${exp}.nc
	#/bin/rm model.nc
    done
    # end exp loop
    
    counter=$(( counter+1 )) 
    
    # back to top level directory
    cd ../
done
# end lab/model loop

