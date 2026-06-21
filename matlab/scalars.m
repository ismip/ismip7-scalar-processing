% Calculate scalar variables from ISMIP7 3D model output
% Heiko Goelzer 2026 (heig@norceresearch.no)

addpath('/nird/services/software/betzy/sw_rl9/software/MATLAB/2024a/toolbox/matlab/matlab_sci/netcdf'); % ncread/nccreate/ncwrite/ncwriteatt

% User settings — set any of these in the workspace before run() to override defaults
if ~exist('region',        'var'), region        = 'AIS';       end
if ~exist('hist',          'var'), hist          = 'historical'; end
if ~exist('refyear',       'var'), refyear       = [];           end  % [] = last timestep of hist
if ~exist('outpath',       'var'), outpath       = '../Output';  end
if ~exist('histout',       'var'), histout       = -1;           end  % -1 = all hist timesteps
if ~exist('flg_mm',        'var'), flg_mm        = true;         end  % whole ice sheet integral
if ~exist('flg_bm',        'var'), flg_bm        = false;        end  % IMBIE3 basins

% Region-specific defaults
switch region
    case 'AIS'
        def_group     = 'VUW';   def_model = 'PISM1';             def_exp = 'expAE04';
        def_modelid   = 'm001';  def_esm   = 'CESM2-WACCM';
        def_forcingid = 'f001';  def_configid = 'E001';           def_exp_group = 'ESM';
    case 'GrIS'
        def_group     = 'NORCE'; def_model = 'CISM16x-MAR312-p50'; def_exp = 'ssp585';
        def_modelid   = 'm001';  def_esm   = 'CESM2-WACCM';
        def_forcingid = 'f001';  def_configid = 'E001';            def_exp_group = 'ESM';
    otherwise
        error('Unknown region: %s. Choose AIS or GrIS.', region);
end
if ~exist('group',         'var') || isempty(group),         group         = def_group;                end
if ~exist('model',         'var') || isempty(model),         model         = def_model;                end
if ~exist('exp',           'var') || isempty(exp),           exp           = def_exp;                  end
if ~exist('modelid',       'var') || isempty(modelid),       modelid       = def_modelid;              end
if ~exist('esm',           'var') || isempty(esm),           esm           = def_esm;                  end
if ~exist('forcingid',     'var') || isempty(forcingid),     forcingid     = def_forcingid;            end
if ~exist('configid',      'var') || isempty(configid),      configid      = def_configid;             end
if ~exist('exp_group',     'var') || isempty(exp_group),     exp_group     = def_exp_group;            end
if ~exist('hist_exp_group','var') || isempty(hist_exp_group),hist_exp_group = exp_group;               end
if ~exist('datapath',      'var') || isempty(datapath),      datapath      = ['../Data/'   region];   end
if ~exist('modelpath',     'var') || isempty(modelpath),     modelpath     = ['../Models/' region];   end

% Description for netcdf global attribute
file_description = 'ISMIP7 scalar output. Heiko Goelzer 2026, heig@norceresearch.no';

% Options
% A2020: seamless hist+exp cumulative (true, default) vs. relative to reference (false)
flg_A20_cumul = true;

% More output
verbose = false;

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% File names

% Auto-detect resolution from model grid x-spacing
exppath_tmp = fullfile(modelpath, group, model, exp_group);
lithk_tmp   = find_model_file(exppath_tmp, 'lithk', region, group, model, modelid, esm, forcingid, exp, configid);
x_tmp       = double(ncread(lithk_tmp, 'x'));
dx_km       = round(abs(x_tmp(2) - x_tmp(1)) / 1000);
res         = sprintf('%02d', dx_km);
fprintf('Auto-detected resolution: %s km\n', res);

switch region
    case 'AIS'
        af2input   = [datapath '/af2_AIS_'                            res '000m_v1.nc'];
        mminput    = [datapath '/maxmask1_AIS_'                       res '000m_v0.nc'];
        basininput = [datapath '/basins_regions_AIS_Rignot_extended_' res '000m_v1.nc'];
        gicinput   = [datapath '/iaf2_GIC_AIS_'                       res '000m_v0.nc'];
    case 'GrIS'
        af2input   = [datapath '/af2_GrIS_'                           res '000m_v1.nc'];
        mminput    = [datapath '/maxmask1_GrIS_'                      res '000m_v1.nc'];
        basininput = [datapath '/basins_GrIS_Mouginot_extended_'      res '000m_v1.nc'];
        gicinput   = [datapath '/iaf2_GIC_GrIS_'                      res '000m_v0.nc'];
end
ncpath  = fullfile(outpath, 'nc');
csvpath = fullfile(outpath, 'csv');

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Prepare generic data

% Defined ocean area
oarea = 3.625e14; % m2 (Gregory et al., 2019)

% Ice sheet mask
maxmask1 = double(ncread(mminput, 'maxmask1')); % (nx, ny)
sheet = maxmask1 * 0 + 1; % full grid
regions = struct('mm', sheet);

% Basin masks
if flg_bm
    switch region
        case 'AIS'
            % IMBIE3 regions: 1=WAIS, 2=EAIS, 3=PINA
            regionid     = double(ncread(basininput, 'regions'));
            regions.wais = double(regionid == 1);
            regions.eais = double(regionid == 2);
            regions.pina = double(regionid == 3);
            % IMBIE3 basins 1-18
            basinid      = double(ncread(basininput, 'basins'));
            regions.r01  = double(basinid ==  1);
            regions.r02  = double(basinid ==  2);
            regions.r03  = double(basinid ==  3);
            regions.r04  = double(basinid ==  4);
            regions.r05  = double(basinid ==  5);
            regions.r06  = double(basinid ==  6);
            regions.r07  = double(basinid ==  7);
            regions.r08  = double(basinid ==  8);
            regions.r09  = double(basinid ==  9);
            regions.r10  = double(basinid == 10);
            regions.r11  = double(basinid == 11);
            regions.r12  = double(basinid == 12);
            regions.r13  = double(basinid == 13);
            regions.r14  = double(basinid == 14);
            regions.r15  = double(basinid == 15);
            regions.r16  = double(basinid == 16);
            regions.r17  = double(basinid == 17);
            regions.r18  = double(basinid == 18);
            if verbose
                sheettest = regions.wais + regions.eais + regions.pina;
                fprintf('sheet sum=%g  region sum=%g  nx*ny=%d\n', ...
                        sum(sheet(:)), sum(sheettest(:)), numel(sheet));
            end
        case 'GrIS'
            % IMBIE3 Mouginot basins: 1-NO 2-NE 3-CE 4-SE 5-SW 6-CW 7-NW
            basinid    = double(ncread(basininput, 'basins'));
            regions.no = double(basinid == 1);
            regions.ne = double(basinid == 2);
            regions.ce = double(basinid == 3);
            regions.se = double(basinid == 4);
            regions.sw = double(basinid == 5);
            regions.cw = double(basinid == 6);
            regions.nw = double(basinid == 7);
            if verbose
                sheettest = regions.no + regions.ne + regions.ce + regions.se + ...
                            regions.sw + regions.cw + regions.nw;
                fprintf('sheet sum=%g  basin sum=%g  nx*ny=%d\n', ...
                        sum(sheet(:)), sum(sheettest(:)), numel(sheet));
            end
    end
end

% Area factors
af2 = double(ncread(af2input, 'af2')); % (nx, ny)
% GIC mask: always loaded
iaf2GIC = double(ncread(gicinput, 'iaf2')); % (nx, ny)

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Prepare model output

exppath  = [modelpath '/' group '/' model '/' exp_group];
histpath = [modelpath '/' group '/' model '/' hist_exp_group];

lithk_file = find_model_file(exppath, 'lithk', region, group, model, modelid, esm, forcingid, exp, configid);
lithk      = double(ncread(lithk_file, 'lithk')); % (nx, ny, nt)
time_model = double(ncread(lithk_file, 'time'));

% Time axis attributes needed for output
time_info      = ncinfo(lithk_file, 'time');
time_units     = '';
time_long_name = '';
time_calendar  = '';
for i = 1:length(time_info.Attributes)
    switch time_info.Attributes(i).Name
        case 'units',     time_units     = time_info.Attributes(i).Value;
        case 'long_name', time_long_name = time_info.Attributes(i).Value;
        case 'calendar',  time_calendar  = time_info.Attributes(i).Value;
    end
end

topg = double(ncread(find_model_file(exppath, 'topg', region, group, model, modelid, esm, forcingid, exp, configid), 'topg')); % (nx, ny, nt)

% Historical experiment
hist_lithk_file = find_model_file(histpath, 'lithk', region, group, model, modelid, esm, forcingid, hist, configid);
lithk_hist_all  = double(ncread(hist_lithk_file, 'lithk'));
topg_hist_all   = double(ncread(find_model_file(histpath, 'topg', region, group, model, modelid, esm, forcingid, hist, configid), 'topg'));
time_hist       = double(ncread(hist_lithk_file, 'time'));
n_hist          = size(lithk_hist_all, 3);

% Number of hist timesteps to prepend to output
if strcmp(exp, hist)
    hist_n_out = 0;
elseif histout == 0
    hist_n_out = 0;
elseif histout == -1
    hist_n_out = n_hist;
else
    if histout > n_hist
        fprintf('Warning: histout %d exceeds hist length %d; using all %d timesteps\n', histout, n_hist, n_hist);
        hist_n_out = n_hist;
    else
        hist_n_out = histout;
    end
end
hist_start = n_hist - hist_n_out;  % 0-based start index into hist arrays

ref_in_exp  = false;
ref_idx_exp = [];
if ~isempty(refyear)
    [ref_idx, found] = find_year_idx_safe(hist_lithk_file, 'time', refyear);
    if ~found
        fprintf('Warning: refyear %d not found in hist experiment ''%s''; searching exp ''%s''\n', refyear, hist, exp);
        ref_in_exp = true;
        ref_idx    = n_hist;
    end
else
    ref_idx = n_hist;  % last timestep (1-based absolute index)
end
lithk_ref = lithk_hist_all(:,:,ref_idx);
topg_ref  = topg_hist_all(:,:,ref_idx);

% If refyear not found in hist, search exp
if ref_in_exp
    [ref_idx_exp, found] = find_year_idx_safe(lithk_file, 'time', refyear);
    if ~found
        error('refyear %d not found in hist experiment ''%s'' or exp ''%s''', refyear, hist, exp);
    end
    lithk_ref = lithk(:,:,ref_idx_exp);
    topg_ref  = topg(:,:,ref_idx_exp);
end

% Model density parameters
params_file = [modelpath '/' group '/' model '/params.nc'];
if ~isfile(params_file)
    error('Missing params.nc for %s/%s.\n  Expected: %s\n  Generate it with: bash tools/set_params.sh', ...
          group, model, params_file);
end
c.RHOI  = double(ncread(params_file, 'rhoi'));
c.RHOSW = double(ncread(params_file, 'rhow'));
c.RHOFW = double(ncread(params_file, 'rhof'));
c.AO    = oarea;

% Model masks (loaded for completeness; not used in SLC computation)
sftgif = double(ncread(find_model_file(exppath, 'sftgif', region, group, model, modelid, esm, forcingid, exp, configid), 'sftgif'));
sftgrf = double(ncread(find_model_file(exppath, 'sftgrf', region, group, model, modelid, esm, forcingid, exp, configid), 'sftgrf'));
sftflf = double(ncread(find_model_file(exppath, 'sftflf', region, group, model, modelid, esm, forcingid, exp, configid), 'sftflf'));

if verbose
    fprintf('# Generic\n');
    fprintf('af2:       %s\n', mat2str(size(af2)));
    fprintf('maxmask1:  %s\n', mat2str(size(maxmask1)));
    fprintf('iaf2GIC:   %s\n', mat2str(size(iaf2GIC)));
    fprintf('# Model\n');
    fprintf('lithk_ref: %s\n', mat2str(size(lithk_ref)));
    fprintf('topg_ref:  %s\n', mat2str(size(topg_ref)));
    fprintf('lithk:     %s\n', mat2str(size(lithk)));
    fprintf('topg:      %s\n', mat2str(size(topg)));
    fprintf('rhoi=%g  rhow=%g  rhof=%g\n', c.RHOI, c.RHOSW, c.RHOFW);
    fprintf('sftgif:    %s\n', mat2str(size(sftgif)));
    fprintf('sftgrf:    %s\n', mat2str(size(sftgrf)));
    fprintf('sftflf:    %s\n', mat2str(size(sftflf)));
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Ice sheet and basin wide integrals

regionNames = fieldnames(regions);
nt = size(lithk, 3);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Pre-compute shared time axis and file stem (same for all regions)

if hist_n_out > 0
    time_out = [time_hist(hist_start+1 : end); time_model(:)];
else
    time_out = time_model(:);
end
nominal_yrs = decode_years(time_out, time_units) - 1;
year_start  = nominal_yrs(1);
year_end    = nominal_yrs(end);
file_stem   = sprintf('%s_%s_%s_%s_%s_%s_%s_%s_%d-%d', ...
                      region, group, model, modelid, esm, forcingid, ...
                      exp, configid, year_start, year_end);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% SLC integrals — two passes: with GIC masking (-gic suffix) and without

gic_masks   = {iaf2GIC,             ones(size(iaf2GIC))};
gic_suffixes = {'-gic', ''};

for igic = 1:2
    gic_mask   = gic_masks{igic};
    gic_suffix = gic_suffixes{igic};

    % Reference state for this GIC mode
    H0 = lithk_ref .* maxmask1 .* gic_mask;
    B0 = topg_ref;
    % TODO clarify if S0=0 is correct for all models
    S0 = topg_ref * 0.0; % sea level fixed at 0

    for ireg = 1:length(regionNames)
        regionName_raw = regionNames{ireg};
        region_mask    = regions.(regionName_raw);

        % Display name: mm → ais/gris, others unchanged
        if strcmp(regionName_raw, 'mm')
            dispName = lower(region);
        else
            dispName = regionName_raw;
        end
        regionName = [dispName gic_suffix];
        fprintf('%s\n', regionName);

        % Area weighting and basin masking
        A = region_mask .* af2 .* (str2double(res) * 1000.0)^2;

        sl_VAF = zeros(nt, 1);
        sl_G20 = zeros(nt, 1);
        sl_A20 = zeros(nt, 1);
        VAF_hist = [];
        G20_hist = [];
        A20_hist = [];

        % ---- Hist portion (VAF, G2020, and non-cumulative A2020) ----
        if hist_n_out > 0
            VAF_hist = zeros(hist_n_out, 1);
            G20_hist = zeros(hist_n_out, 1);
            for n = 1:hist_n_out
                H              = lithk_hist_all(:,:, hist_start + n) .* maxmask1 .* gic_mask;
                B              = topg_hist_all(:,:,  hist_start + n);
                VAF_hist(n)    = get_slc_vaf(H0, H, B0, B, S0, S0, A, c);
                G20_hist(n)    = get_slc_G2020(H0, H, B0, B, A, c);
            end
            if ~flg_A20_cumul
                A20_hist = zeros(hist_n_out, 1);
                for n = 1:hist_n_out
                    H           = lithk_hist_all(:,:, hist_start + n) .* maxmask1 .* gic_mask;
                    B           = topg_hist_all(:,:,  hist_start + n);
                    A20_hist(n) = get_slc_A2020(H0, H, B0, B, S0, S0, A, c);
                end
            end
        end

        % ---- VAF and G2020 (always relative to reference state) ----
        for n = 1:nt
            H         = lithk(:,:,n) .* maxmask1 .* gic_mask;
            B         = topg(:,:,n);
            sl_VAF(n) = get_slc_vaf(H0, H, B0, B, S0, S0, A, c);
            sl_G20(n) = get_slc_G2020(H0, H, B0, B, A, c);
        end

        % ---- A2020 (method-dependent) ----
        if ~flg_A20_cumul
            % Relative to reference state at every timestep
            for n = 1:nt
                H         = lithk(:,:,n) .* maxmask1 .* gic_mask;
                B         = topg(:,:,n);
                sl_A20(n) = get_slc_A2020(H0, H, B0, B, S0, S0, A, c);
            end
        else
            % Seamless hist+exp cumulative, offset to zero at t_ref
            if strcmp(exp, hist)
                lh   = lithk;
                th   = topg;
                n_lh = nt;
            else
                lh   = lithk_hist_all;
                th   = topg_hist_all;
                n_lh = n_hist;
            end
            % Hist pre-pass: cumulate from hist[0] forward
            H_prev     = lh(:,:,1) .* maxmask1 .* gic_mask;
            B_prev     = th(:,:,1);
            acc        = 0.0;
            hist_cumul = zeros(n_lh, 1);
            for n_h = 2:n_lh
                H_h             = lh(:,:,n_h) .* maxmask1 .* gic_mask;
                B_h             = th(:,:,n_h);
                acc             = acc + get_slc_A2020(H_prev, H_h, B_prev, B_h, S0, S0, A, c);
                hist_cumul(n_h) = acc;
                H_prev          = H_h;
                B_prev          = B_h;
            end
            offset = hist_cumul(ref_idx);
            if strcmp(exp, hist)
                sl_A20 = hist_cumul - offset;
            else
                raw_exp = zeros(nt, 1);
                for n = 1:nt
                    H          = lithk(:,:,n) .* maxmask1 .* gic_mask;
                    B          = topg(:,:,n);
                    acc        = acc + get_slc_A2020(H_prev, H, B_prev, B, S0, S0, A, c);
                    raw_exp(n) = acc;
                    H_prev     = H;
                    B_prev     = B;
                end
                if ref_in_exp
                    offset = raw_exp(ref_idx_exp);
                end
                sl_A20 = raw_exp - offset;
                if hist_n_out > 0
                    A20_hist = hist_cumul(hist_start+1 : end) - offset;
                end
            end
        end

        % Concatenate hist + exp arrays
        sl_VAF = [VAF_hist; sl_VAF];
        sl_G20 = [G20_hist; sl_G20];
        sl_A20 = [A20_hist; sl_A20];

        if verbose
            disp(sl_VAF');
            disp(sl_G20');
            disp(sl_A20');
        end

        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        % Write SLC NetCDF output — one file per SLC method

        nc_vars = { ...
            'slvaf', 'Sea level contribution based on Vaf',   sl_VAF; ...
            'slg20', 'Sea level contribution based on G2020', sl_G20; ...
            'sla20', 'Sea level contribution based on A2020', sl_A20; ...
        };
        for iv = 1:size(nc_vars, 1)
            varname   = nc_vars{iv,1};
            long_name = nc_vars{iv,2};
            sl_data   = nc_vars{iv,3};
            if ~exist(ncpath, 'dir'), mkdir(ncpath); end
            scfile = fullfile(ncpath, [varname '_' regionName '_' file_stem '.nc']);
            if exist(scfile, 'file'), delete(scfile); end
            nccreate(scfile, 'time',   'Dimensions', {'time', Inf}, 'Format', 'netcdf4');
            nccreate(scfile, varname,  'Dimensions', {'time', Inf});
            ncwrite(scfile,  'time',   time_out(:));
            ncwrite(scfile,  varname,  sl_data(:));
            ncwriteatt(scfile, '/',      'description', file_description);
            ncwriteatt(scfile, 'time',   'units',        time_units);
            ncwriteatt(scfile, 'time',   'long_name',    time_long_name);
            ncwriteatt(scfile, 'time',   'calendar',     time_calendar);
            ncwriteatt(scfile, varname,  'long_name',    long_name);
            ncwriteatt(scfile, varname,  'units',        'm');
            fprintf('Created file %s\n', scfile);
        end

        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        % Write SLC CSV output — one file per SLC method

        if ~exist(csvpath, 'dir'), mkdir(csvpath); end
        meta_keys = {'ice_source','region','group','model','model_variant','scenario','GCM','forcingid','configid'};
        meta_vals = {region, regionName, group, model, modelid, exp, esm, forcingid, configid};
        csv_years = 1850:2300;

        csv_vars = { ...
            'slvaf', sl_VAF; ...
            'slg20', sl_G20; ...
            'sla20', sl_A20; ...
        };
        for iv = 1:size(csv_vars, 1)
            varname  = csv_vars{iv,1};
            sl_data  = csv_vars{iv,2};
            csvfile  = fullfile(csvpath, [varname '_' regionName '_' file_stem '.csv']);
            fid      = fopen(csvfile, 'w');
            % Header
            fprintf(fid, '%s', strjoin([meta_keys, arrayfun(@(y) sprintf('y%d',y), csv_years, 'UniformOutput', false)], ','));
            fprintf(fid, '\n');
            % Data row — metadata
            for k = 1:length(meta_vals)
                fprintf(fid, '%s,', meta_vals{k});
            end
            % Annual values
            year_map = containers.Map(nominal_yrs, num2cell(sl_data(:)));
            for iy = 1:length(csv_years)
                y = csv_years(iy);
                if isKey(year_map, y)
                    val = year_map(y);
                    if iy < length(csv_years)
                        fprintf(fid, '%.10g,', val);
                    else
                        fprintf(fid, '%.10g', val);
                    end
                else
                    if iy < length(csv_years)
                        fprintf(fid, 'NA,');
                    else
                        fprintf(fid, 'NA');
                    end
                end
            end
            fprintf(fid, '\n');
            fclose(fid);
            fprintf('Created file %s\n', csvfile);
        end
    end % region loop
end % GIC mode loop


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Local functions — year decoding

function yrs = decode_years(t, units)
% Decode a time vector to calendar years using MATLAB datetime (calendar-aware).
    tok = regexp(units, 'since\s+(\d{4})-(\d{2})-(\d{2})', 'tokens');
    if ~isempty(tok)
        origin = datetime(str2double(tok{1}{1}), str2double(tok{1}{2}), str2double(tok{1}{3}));
    else
        tok = regexp(units, 'since\s+(\d{4})', 'tokens');
        if isempty(tok)
            error('Cannot parse origin from time units: %s', units);
        end
        origin = datetime(str2double(tok{1}{1}), 1, 1);
    end
    if contains(units, 'day')
        dt = origin + days(t);
    elseif contains(units, 'year')
        dt = origin + years(t);
    else
        error('Unsupported time unit: %s', units);
    end
    yrs = year(dt);
end


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Local functions — file discovery

function fpath = find_model_file(dirpath, var, region, group, model, modelid, esm, forcingid, experiment, configid)
% Find new-format ISMIP7 file by glob, ignoring the timerange field.
    pattern = fullfile(dirpath, [var '_' region '_' group '_' model '_' modelid '_' esm '_' forcingid '_' experiment '_' configid '_*.nc']);
    d = dir(pattern);
    if isempty(d)
        error('No file found:\n  %s', pattern);
    end
    if length(d) > 1
        error('Multiple files match for %s — cannot disambiguate:\n  %s', var, pattern);
    end
    fpath = fullfile(d(1).folder, d(1).name);
end


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Local functions — SLC methods
% Translated from slc/slc_vaf.py, slc/slc_G2020.py, slc/slc_A2020.py

% ---- VAF (Volume Above Flotation, ISMIP6 method) ----

function vol = get_vaf(H, B, S, A, c)
% Volume above flotation; B and S in absolute reference frame
    hf   = max(S - B, 0.0) * c.RHOSW / c.RHOI;
    hall = max(H - hf, 0.0);
    vol  = sum(hall .* A, 'all');
end

function slc = get_slc_vaf(H0, H, B0, B, S0, S, A, c)
% SLC using VAF method — freshwater conversion (ISMIP6)
    sle_ref = get_vaf(H0, B0, S0, A, c) / c.AO * c.RHOI / c.RHOFW;
    sle     = get_vaf(H,  B,  S,  A, c) / c.AO * c.RHOI / c.RHOFW;
    slc     = -(sle - sle_ref);
end


% ---- Goelzer et al. 2020 (G2020) ----
% https://doi.org/10.5194/tc-14-833-2020

function vol = get_vaf_G2020(H, B, A, c)
% eq. 1/13
    hf   = min(B, 0.0) * c.RHOSW / c.RHOI;
    hall = max(H + hf, 0.0);
    vol  = sum(hall .* A, 'all');
end

function vol = get_vpov_G2020(B, A)
% eq. 8/14 — potential ocean volume
    vol = sum(max(-B, 0.0) .* A, 'all');
end

function vol = get_vden_G2020(H, A, c)
% eq. 10 — density correction
    vol = sum(H .* (c.RHOI/c.RHOFW - c.RHOI/c.RHOSW) .* A, 'all');
end

function slc = get_slc_G2020(H0, H, B0, B, A, c)
% eq. 12/15 — total SLC combining three components
    slc_af  = -(get_vaf_G2020(H,  B,  A, c) - get_vaf_G2020(H0, B0, A, c)) / c.AO * c.RHOI/c.RHOSW;
    slc_pov = -(get_vpov_G2020(B,  A)        - get_vpov_G2020(B0, A))        / c.AO;
    slc_den = -(get_vden_G2020(H,  A, c)     - get_vden_G2020(H0, A, c))     / c.AO;
    slc = slc_af + slc_pov + slc_den;
end


% ---- Adhikari et al. 2020 (A2020) ----
% https://doi.org/10.5194/tc-14-2819-2020

function [I, L, G] = get_masks_A2020(H, B, S, c)
% Binary masks: I=ice cover, L=land/grounded, G=grounded ice
    % eq. 1
    F = H - c.RHOSW/c.RHOI * (S - B);
    % eq. 5: O = ocean/floating
    O = zeros(size(H));
    O(F < 0) = 1;
    % text after eq. 5: L = land/grounded
    L = 1 - O;
    % eq. 6: I = ice
    I = zeros(size(H));
    I(H > 0) = 1;
    % text after eq. 6: G = grounded ice
    G = I .* L;
end

function slc = get_slc_A2020(H0, H, B0, B, S0, S, A, c)
% SLC in absolute reference frame with grounding-line migration tracking
    [~, L0, G0] = get_masks_A2020(H0, B0, S0, c);
    [~, L,  G ] = get_masks_A2020(H,  B,  S,  c);

    % eq. 7
    Hn  = c.RHOSW/c.RHOI * max(S  - B,  0);
    Hn0 = c.RHOSW/c.RHOI * max(S0 - B0, 0);
    % eq. 8
    HF  = G  .* (H  - Hn);
    HF0 = G0 .* (H0 - Hn0);
    % eq. 11
    HM = (H - H0) .* L0 .* L + (HF - HF0) .* (1 - L0.*L);
    % eq. 12
    HV = (1 - c.RHOFW/c.RHOSW) .* ((H - H0) - (HF - HF0)) .* (1 - L0.*L);
    % eq. 10
    HS = HM + HV;
    % last paragraph before Sec. 3.3
    slc = -c.RHOI/c.RHOFW * sum(HS .* A, 'all') / c.AO;
end


% ---- Helper: find time index matching a calendar year ----

function idx = find_year_idx(ncfile, varname, target_year)
% Return the last index whose calendar year equals target_year; error if not found.
    [idx, found] = find_year_idx_safe(ncfile, varname, target_year);
    if ~found
        error('Year %d not found in %s:%s', target_year, ncfile, varname);
    end
end

function [idx, found] = find_year_idx_safe(ncfile, varname, target_year)
% Return the last index whose calendar year equals target_year.
% found=false and idx=0 if target_year is not present.
% Handles 'days since' and 'years since' time units.
    t    = double(ncread(ncfile, varname));
    info = ncinfo(ncfile, varname);
    units = '';
    for k = 1:length(info.Attributes)
        if strcmp(info.Attributes(k).Name, 'units')
            units = info.Attributes(k).Value;
            break;
        end
    end
    yr = decode_years(t, units);
    hits = find(yr == target_year);
    if isempty(hits)
        idx   = 0;
        found = false;
    else
        idx   = hits(end);
        found = true;
    end
end
