# Scripts for ISMIP7 scalar processing

These scripts are used to be calculate sea-level contributions and other scalar variables based on ISMIP7 submission files for AIS and GrIS. This means that we expect to find model output on the diagnostic ISMIP grid following specific ISMIP7 conventions for filenames and units. 

The different versions of the scripts have slightly different requirements, but a conda environment as follows works for all of them.

conda create -n nc 
conda activate nc
conda install -c conda-forge cdo=2.4.4 nco netCDF4 scipy

Required input data (other than the model output) consists of masks and area factors that can be found on the ISMIP globus server under Output-Processing.

The following directory structure may be used but can be modified changing path definitions in the scripts.

conda create -n nc 
conda activate nc
conda install -c conda-forge cdo=2.4.4 nco netCDF4 scipy

TODO - update Model file and folder names to ISMIP7 style
```
Scalars
   |-ismip7-scalar-processing
   |---AIS
   |-----python
   |-------output
   |-------slc
   |---GrIS
   |-----nco
   |-------output
   |-------proc
   |-----python
   |-------output
   |-------slc

   |-Data
   |---AIS
   |---GrIS
   
   |-Models
   |---AIS
   |-----NORCE
   |-------CISM4-MAR364-ERA-t1
   |---------expAE01_16
   |---------historical_16
   |-----VUW
   |-------PISM1
   |---------expAE04_08
   |---------historical_08
   |---GrIS
   |-----NORCE
   |-------CISM08-MAR312-p50
   |---------historical_08
```

