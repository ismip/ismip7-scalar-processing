% Calculate scalar variables from ISMIP7 3D model output
% Heiko Goelzer 2026 (heig@norceresearch.no)

addpath('/nird/services/software/betzy/sw_rl9/software/MATLAB/2024a/toolbox/matlab/matlab_sci/netcdf'); % ncread/nccreate/ncwrite/ncwriteatt

% User settings — set any of these in the workspace before run() to override defaults
if ~exist('region',    'var'), region    = 'AIS';       end
if ~exist('ref',       'var'), ref       = 'historical'; end
if ~exist('refyear',   'var'), refyear   = [];           end  % [] = last timestep of ref
if ~exist('res',       'var'), res       = '08';         end
if ~exist('outpath',   'var'), outpath   = './output';   end

% Region-specific defaults
switch region
    case 'AIS'
        def_lab   = 'VUW';   def_model = 'PISM1';             def_exp = 'expAE04';
    case 'GrIS'
        def_lab   = 'NORCE'; def_model = 'CISM08-MAR312-p50'; def_exp = 'historical';
    otherwise
        error('Unknown region: %s. Choose AIS or GrIS.', region);
end
if ~exist('lab',       'var') || isempty(lab),       lab       = def_lab;                end
if ~exist('model',     'var') || isempty(model),     model     = def_model;              end
if ~exist('exp',       'var') || isempty(exp),       exp       = def_exp;                end
if ~exist('datapath',  'var') || isempty(datapath),  datapath  = ['../Data/'   region]; end
if ~exist('modelpath', 'var') || isempty(modelpath), modelpath = ['../Models/' region]; end

% What output to produce
flg_mm = true;  % Integrals on model mask
flg_bm = false;  % IMBIE3 basins

% Description for netcdf global attribute
file_description = 'ISMIP7 scalar output. Heiko Goelzer 2026, heig@norceresearch.no';

% Options
% Remove GIC contribution
flg_GICmask = true; % [Default true!]
% A2020: stepwise cumulative (true, default) vs. all relative to reference (false)
flg_A20_cumul = true;

% More output
verbose = false;

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% File names

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
file_suffix = [region '_' lab '_' model '_' exp '_' res '000m.nc'];

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
if flg_GICmask
    iaf2GIC = double(ncread(gicinput, 'iaf2')); % (nx, ny)
else
    iaf2GIC = ones(size(af2));
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Prepare model output

exppath = [modelpath '/' lab '/' model '/' exp '_' res];

lithk_file = [exppath '/lithk_' region '_' lab '_' model '_' exp '.nc'];
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

topg = double(ncread([exppath '/topg_' region '_' lab '_' model '_' exp '.nc'], 'topg')); % (nx, ny, nt)

% Reference experiment
refpath        = [modelpath '/' lab '/' model '/' ref '_' res];
ref_lithk_file = [refpath '/lithk_' region '_' lab '_' model '_' ref '.nc'];
lithk_ref_all  = double(ncread(ref_lithk_file, 'lithk'));
topg_ref_all   = double(ncread([refpath '/topg_' region '_' lab '_' model '_' ref '.nc'], 'topg'));
if ~isempty(refyear)
    ref_idx = find_year_idx(ref_lithk_file, 'time', refyear);
else
    ref_idx = size(lithk_ref_all, 3); % last timestep
end
lithk_ref = lithk_ref_all(:,:,ref_idx);
topg_ref  = topg_ref_all(:,:,ref_idx);

% Model density parameters
params_file = [modelpath '/' lab '/' model '/params.nc'];
c.RHOI  = double(ncread(params_file, 'rhoi'));
c.RHOSW = double(ncread(params_file, 'rhow'));
c.RHOFW = double(ncread(params_file, 'rhof'));
c.AO    = oarea;

% Model masks (loaded for completeness; not used in SLC computation)
sftgif = double(ncread([exppath '/sftgif_' region '_' lab '_' model '_' exp '.nc'], 'sftgif'));
sftgrf = double(ncread([exppath '/sftgrf_' region '_' lab '_' model '_' exp '.nc'], 'sftgrf'));
sftflf = double(ncread([exppath '/sftflf_' region '_' lab '_' model '_' exp '.nc'], 'sftflf'));

if verbose
    fprintf('# Generic\n');
    fprintf('af2:       %s\n', mat2str(size(af2)));
    fprintf('maxmask1:  %s\n', mat2str(size(maxmask1)));
    if flg_GICmask
        fprintf('iaf2GIC:   %s\n', mat2str(size(iaf2GIC)));
    end
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

for ireg = 1:length(regionNames)
    regionName  = regionNames{ireg};
    region_mask = regions.(regionName);
    fprintf('%s\n', regionName);

    % Reference state
    H0 = lithk_ref .* maxmask1 .* iaf2GIC;
    B0 = topg_ref;
    % TODO clarify if S0=0 is correct for all models
    S0 = topg_ref * 0.0; % sea level fixed at 0

    % Area weighting and basin masking
    A = region_mask .* af2 .* (str2double(res) * 1000.0)^2;

    sl_VAF = zeros(nt, 1);
    sl_G20 = zeros(nt, 1);
    sl_A20 = zeros(nt, 1);

    if flg_A20_cumul
        H_prev     = H0;
        B_prev     = B0;
        S_prev     = S0;
        A20_cumsum = 0.0;
    end

    for n = 1:nt
        H = lithk(:,:,n) .* maxmask1 .* iaf2GIC;
        B = topg(:,:,n);

        % TODO check potential issues with partial masks
        sl_VAF(n) = get_slc_vaf(H0, H, B0, B, S0, S0, A, c);
        sl_G20(n) = get_slc_G2020(H0, H, B0, B, A, c);

        if flg_A20_cumul
            % Stepwise: increment from previous to current timestep
            A20_cumsum = A20_cumsum + get_slc_A2020(H_prev, H, B_prev, B, S_prev, S_prev, A, c);
            sl_A20(n)  = A20_cumsum;
            H_prev = H; % MATLAB assignment copies values
            B_prev = B;
            % S_prev stays at S0 (zeros) — never updated, same as Python
        else
            sl_A20(n) = get_slc_A2020(H0, H, B0, B, S0, S0, A, c);
        end
    end

    if verbose
        disp(sl_VAF');
        disp(sl_G20');
        disp(sl_A20');
    end

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % Write NetCDF output

    scfile = [outpath '/scalars_' regionName '_' file_suffix];
    if exist(scfile, 'file')
        delete(scfile);
    end

    nccreate(scfile, 'time',      'Dimensions', {'time', Inf}, 'Format', 'netcdf4');
    nccreate(scfile, 'slc_VAF',   'Dimensions', {'time', Inf});
    nccreate(scfile, 'slc_G2020', 'Dimensions', {'time', Inf});
    nccreate(scfile, 'slc_A2020', 'Dimensions', {'time', Inf});

    ncwrite(scfile, 'time',      time_model(:));
    ncwrite(scfile, 'slc_VAF',   sl_VAF(:));
    ncwrite(scfile, 'slc_G2020', sl_G20(:));
    ncwrite(scfile, 'slc_A2020', sl_A20(:));

    ncwriteatt(scfile, '/',         'description', file_description);
    ncwriteatt(scfile, 'time',      'units',        time_units);
    ncwriteatt(scfile, 'time',      'long_name',    time_long_name);
    ncwriteatt(scfile, 'time',      'calendar',     time_calendar);
    ncwriteatt(scfile, 'slc_VAF',   'long_name',    'Sea level contribution based on Vaf');
    ncwriteatt(scfile, 'slc_VAF',   'units',        'm');
    ncwriteatt(scfile, 'slc_G2020', 'long_name',    'Sea level contribution based on G2020');
    ncwriteatt(scfile, 'slc_G2020', 'units',        'm');
    ncwriteatt(scfile, 'slc_A2020', 'long_name',    'Sea level contribution based on A2020');
    ncwriteatt(scfile, 'slc_A2020', 'units',        'm');

    fprintf('Created file %s\n', scfile);
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
% Return the last index whose calendar year equals target_year.
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
    tok = regexp(units, 'since\s+(\d{4})', 'tokens');
    if isempty(tok)
        error('Cannot parse origin year from time units: %s', units);
    end
    origin_year = str2double(tok{1}{1});
    if contains(units, 'day')
        yr = floor(origin_year + t / 365.25);
    elseif contains(units, 'year')
        yr = floor(origin_year + t);
    else
        error('Unsupported time unit: %s', units);
    end
    hits = find(yr == target_year);
    if isempty(hits)
        error('Year %d not found in %s:%s', target_year, ncfile, varname);
    end
    idx = hits(end);
end
