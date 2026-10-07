% Driver for the MATLAB-vs-Python scalar comparison on NIRD: basins only.
%
% Same as run_mvsp.m but with flg_mm = false, flg_bm = true, i.e. the
% Python "--basins --no-mm" case.  The output CSV must be named
% sl_..._basins.csv, not sl_..._mm-basins.csv.
%
% Usage:
%   matlab -nodisplay -nosplash -nojvm -singleCompThread \
%     -r "run('/abs/path/run_mvsp_basins.m'); exit"

% --- settings ---------------------------------------------------------
region        = 'AIS';
group         = 'NORCE';
model         = 'CISM';
exp           = 'ssp370';
configid      = 'C003';
hist_configid = 'C001';

flg_mm        = false;
flg_bm        = true;

root      = '/nird/datalake/NS8002K/heig/ISMIP7';
modelpath = [root '/Models/' region];
datapath  = [root '/Data/' region];
outpath   = [root '/Scalars_mvsp/mat_basins'];

% --- run --------------------------------------------------------------
script = [root '/ismip7-scalar-processing/matlab/scalars.m'];
run(script);
