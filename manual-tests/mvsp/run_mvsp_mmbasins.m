% Driver for the MATLAB-vs-Python scalar comparison on NIRD: mm + basins.
%
% Same as run_mvsp.m but with flg_mm = true AND flg_bm = true, i.e. the
% Python default "--basins" (no --no-mm).  The output CSV must be named
% sl_..._mm-basins.csv.
%
% Usage:
%   matlab -nodisplay -nosplash -nojvm -singleCompThread \
%     -r "run('/abs/path/run_mvsp_mmbasins.m'); exit"

% --- settings ---------------------------------------------------------
region        = 'AIS';
group         = 'NORCE';
model         = 'CISM';
exp           = 'ssp370';
configid      = 'C003';
hist_configid = 'C001';

flg_mm        = true;
flg_bm        = true;

root      = '/nird/datalake/NS8002K/heig/ISMIP7';
modelpath = [root '/Models/' region];
datapath  = [root '/Data/' region];
outpath   = [root '/Scalars_mvsp/mat_mmbasins'];

% --- run --------------------------------------------------------------
script = [root '/ismip7-scalar-processing/matlab/scalars.m'];
run(script);
