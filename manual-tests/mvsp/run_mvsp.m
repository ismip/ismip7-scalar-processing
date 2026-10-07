% Driver for the MATLAB-vs-Python scalar comparison on NIRD.
%
% Runs matlab/scalars.m for one ISMIP7 run.  Every setting is a char row
% (single quotes): scalars.m concatenates them with [], and a string array
% would make dir() fail with "Name must be a text scalar".
%
% Usage:
%   matlab -nodisplay -nosplash -nojvm -singleCompThread \
%     -r "run('/abs/path/run_mvsp.m'); exit"

% --- settings ---------------------------------------------------------
region        = 'AIS';
group         = 'NORCE';
model         = 'CISM';
exp           = 'ssp370';
configid      = 'C003';
hist_configid = 'C001';

root      = '/nird/datalake/NS8002K/heig/ISMIP7';
modelpath = [root '/Models/' region];
datapath  = [root '/Data/' region];
outpath   = [root '/Scalars_mvsp/mat'];

% --- run --------------------------------------------------------------
script = [root '/ismip7-scalar-processing/matlab/scalars.m'];
run(script);
