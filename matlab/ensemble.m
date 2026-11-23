% Batch-run the scalar processing over an ISMIP7 submission ensemble.
% Heiko Goelzer 2026 (heig@norceresearch.no)
%
% MATLAB mirror of ismip7_scalars/ensemble.py.  Walks a submissions root
% {modelpath}/{group}/{model}/{exp_group}/{configid}/, pairs each projection
% with its historical run (CORE table by ESM, or a user-declared links CSV
% for ESM/PPE configids), and runs scalars.m once per unit.  Units that
% error are caught and reported: one bad submission cannot take the batch
% down.

% User settings — set any of these in the workspace before run() to override
if ~exist('region',    'var'), region    = 'AIS';                 end
if ~exist('modelpath', 'var'), modelpath = ['../Models/' region];  end
if ~exist('datapath',  'var'), datapath  = ['../Data/' region];    end
if ~exist('params_path', 'var'), params_path = '';  end  % unset = modelpath
if ~exist('outpath',   'var'), outpath = '';  end  % unset = scalars default
if ~exist('exp_group', 'var'), exp_group = '';  end  % unset = all
if ~exist('groups',    'var'), groups    = '';  end  % comma-separated
if ~exist('models',    'var'), models    = '';  end  % comma-separated
if ~exist('configids', 'var'), configids = '';  end  % comma-separated
if ~exist('histout',   'var'), histout   = [];  end  % [] = scalars default
if ~exist('flg_mm',    'var'), flg_mm    = true;   end
if ~exist('flg_bm',    'var'), flg_bm    = false;  end
if ~exist('flg_base',  'var'), flg_base  = false;  end
if ~exist('dry_run',   'var'), dry_run   = false;  end
if ~exist('log_dir',   'var'), log_dir   = ['../Output/logs']; end
if ~exist('hist_links','var'), hist_links = '';  end  % unset = none
if ~exist('core_csv',  'var')
    core_csv = fullfile('..', 'ismip7_scalars', 'data', ...
                        'ISMIP7_experiments_CORE.csv');
end

% Pairing tables
core  = load_core_csv(core_csv);
links = struct();
if ~isempty(hist_links)
    links = load_hist_links(hist_links);
    if isempty(fieldnames(links))
        error(['no usable links in %s -- the file is missing or has no ' ...
               'configid,hist_configid rows'], hist_links);
    end
end

% Discover units
[units, results] = discover_units(modelpath);  % results starts as skips
units = keep_units(units, exp_group, groups, models, configids);

if ~exist(log_dir, 'dir'), mkdir(log_dir); end
d = datetime('now');
stamp = char(datetime(d, 'Format', 'yyyyMMdd''T''HHmmss'));

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Plan and run each unit

for k = 1:numel(units)
    unit = units{k};
    key = [unit.group '/' unit.model '/' unit.exp_group '/' unit.configid];
    [s, note] = plan_unit(unit, core, links, region, modelpath, ...
                          datapath, params_path, outpath, histout, ...
                          flg_mm, flg_bm, flg_base);
    if isempty(s)
        results(end+1, :) = {key, ['SKIP: ' note], ''}; %#ok<*AGROW>
        fprintf('[SKIP] %s -- %s\n', key, note);
        continue
    end
    if dry_run
        results(end+1, :) = {key, 'DRY-RUN', note};
        fprintf('[PLAN] %s -- %s\n', key, note);
        disp(s);
        continue
    end
    log_path = fullfile(log_dir, sprintf('%s_%s_%s_%s_%s.log', ...
                        region, unit.group, unit.model, unit.exp_group, ...
                        unit.configid));
    fprintf('[RUN ] %s -- %s\n', key, note);
    diary(log_path);
    try
        run_unit(s);
        results(end+1, :) = {key, 'OK', log_path};
    catch ME
        results(end+1, :) = {key, ['FAIL: ' ME.message], log_path};
    end
    diary off
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Summary

n_ok   = sum(strcmp('OK',        results(:, 2)));
n_skip = sum(startsWith(results(:, 2), 'SKIP') | ...
             strcmp('DRY-RUN',   results(:, 2)));
n_fail = sum(startsWith(results(:, 2), 'FAIL'));
lines = {sprintf('ISMIP7 ensemble run -- %s -- %s', region, stamp); ...
         sprintf('modelpath: %s', modelpath); ...
         sprintf('units: %d   ok: %d   skipped: %d   failed: %d', ...
                 size(results, 1), n_ok, n_skip, n_fail); ''};
for k = 1:size(results, 1)
    entry = sprintf('  %-55s  %s', results{k, 1}, results{k, 2});
    if ~isempty(results{k, 3})
        entry = [entry '   [' results{k, 3} ']'];
    end
    lines{end+1} = entry; %#ok<AGROW>
end
report = strjoin(lines, sprintf('\n'));
master_path = fullfile(log_dir, ['ensemble_' region '_' stamp '.log']);
fid = fopen(master_path, 'w');
fprintf(fid, '%s\n', report);
fclose(fid);
fprintf('\n%s\n', report);
fprintf('\nSummary written to %s\n', master_path);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Local functions

function [units, skips] = discover_units(root)
    % Find every processable unit under a submissions root.  A unit is a
    % struct (group, model, exp_group, configid, path); a skip is {key,
    % reason, ''}.  Like Python's glob, a leading-dot directory beside a
    % real unit is invisible rather than skipped; MATLAB's dir does list
    % '.' and '..' entries, which are skipped here.
    units = {}; skips = {};
    listing = dir(fullfile(root, '*', '*', '*', '*'));
    for k = 1:numel(listing)
        if ~listing(k).isdir, continue; end
        if any(strcmp(listing(k).name, {'.', '..'})), continue; end
        path = fullfile(listing(k).folder, listing(k).name);
        parts = strsplit(path, filesep);
        group = parts{end-3}; model = parts{end-2};
        exp_group = parts{end-1}; configid = parts{end};
        key = [group '/' model '/' exp_group '/' configid];
        if isempty(regexp(exp_group, '^(CORE|ESM|PPE)$', 'once')) || ...
           isempty(regexp(configid, '^[CEP]\d{3}$', 'once'))
            skips(end+1, :) = {key, 'non-standard dir', ''};
            continue
        end
        units(end+1, :) = {struct('group', group, 'model', model, ...
                                  'exp_group', exp_group, ...
                                  'configid', configid, 'path', path)};
    end
end

function units = keep_units(units, exp_group, groups, models, configids)
    % Keep the units that pass the comma-separated filters; an empty
    % filter keeps everything.
    keep = true(size(units));
    for k = 1:numel(units)
        if ~isempty(exp_group) && ~strcmp(units{k}.exp_group, exp_group)
            keep(k) = false;
        end
        if ~isempty(groups) && ...
           ~any(strcmp(units{k}.group, strsplit(groups, ',')))
            keep(k) = false;
        end
        if ~isempty(models) && ...
           ~any(strcmp(units{k}.model, strsplit(models, ',')))
            keep(k) = false;
        end
        if ~isempty(configids) && ...
           ~any(strcmp(units{k}.configid, strsplit(configids, ',')))
            keep(k) = false;
        end
    end
    units = units(keep);
end

function [s, note] = plan_unit(unit, core, links, region, modelpath, ...
                               datapath, params_path, outpath, histout, ...
                               flg_mm, flg_bm, flg_base)
    % Plan one unit: returns the scalars.m settings struct and a note, or
    % an empty s and a skip reason.
    s = [];
    lithks = dir(fullfile(unit.path, 'lithk_*.nc'));
    if isempty(lithks)
        note = 'no lithk file';
        return
    end
    fname = lithks(1).name;
    parts = parse_ismip7_name(fname);
    if isempty(parts) || ~strcmp(parts{9}, unit.configid) || ...
       ~strcmp(parts{2}, region)
        note = ['non-strict filename (' fname ')'];
        return
    end
    if ~strcmp(parts{3}, unit.group) || ~strcmp(parts{4}, unit.model)
        note = ['filename group/model field != directory (' parts{3} ...
                '/' parts{4} ' vs ' unit.group '/' unit.model ')'];
        return
    end

    % Scenario: the CORE table's, or the filename's when unknown to it.
    if isfield(core, unit.configid)
        scenario = core.(unit.configid).scenario;
    else
        scenario = parts{8};
    end

    s = struct('region', region, 'group', parts{3}, 'model', parts{4}, ...
               'modelid', parts{5}, 'esm', parts{6}, 'forcingid', parts{7}, ...
               'experiment', parts{8}, 'configid', unit.configid, ...
               'exp_group', unit.exp_group, 'modelpath', modelpath, ...
               'datapath', datapath, 'flg_mm', flg_mm, 'flg_bm', flg_bm, ...
               'flg_base', flg_base);
    if ~isempty(params_path), s.params_path = params_path; end
    if ~isempty(outpath),     s.outpath = outpath;         end
    if ~isempty(histout),     s.histout = histout;         end

    if any(strcmp(scenario, {'historical', 'ocx'}))
        % Self-paired: the reference comes from within the run itself.
        s.hist = parts{8};
        s.hist_configid = unit.configid;
        s.hist_exp_group = unit.exp_group;
        note = ['self-paired (' scenario ')'];
        return
    end

    hcid = hist_configid_for(unit.configid, core);
    hist_exp_group = '';
    if isempty(hcid)
        if ~isfield(links, unit.configid)
            note = sprintf(['no historical run is defined for %s (''%s''); ' ...
                            'declare one with hist_links or run it by hand ' ...
                            'with hist_configid'], unit.configid, scenario);
            s = [];
            return
        end
        hcid = links.(unit.configid).hist_configid;
        hist_exp_group = links.(unit.configid).hist_exp_group;
    end
    if strcmp(hcid, unit.configid)
        note = [unit.configid ' would be paired against itself; ' ...
                'a projection needs a separate historical run'];
        s = [];
        return
    end
    if isempty(hist_exp_group), hist_exp_group = unit.exp_group; end
    hpath = fullfile(modelpath, unit.group, unit.model, ...
                     hist_exp_group, hcid);
    hlithks = dir(fullfile(hpath, 'lithk_*.nc'));
    if isempty(hlithks)
        note = ['no historical ' hcid];
        s = [];
        return
    end
    hparts = parse_ismip7_name(hlithks(1).name);
    if isempty(hparts)
        hist_exp = 'historical';
    else
        hist_exp = hparts{8};
    end
    s.hist = hist_exp;
    s.hist_configid = hcid;
    s.hist_exp_group = hist_exp_group;
    note = [scenario ' -> hist ' hcid];
end

function run_unit(s)
    % Run scalars.m for one unit.  The struct fields become workspace
    % variables inside this function, which the script's exist() checks
    % pick up; anything unset keeps the scalars.m default.
    mdir = fileparts(mfilename('fullpath'));
    fn = fieldnames(s);
    for k = 1:numel(fn)
        eval([fn{k} ' = s.(fn{k});']); %#ok<NOSEL>
    end
    run(fullfile(mdir, 'scalars.m'));
end

function parts = parse_ismip7_name(fname)
    % Split a strict ISMIP7 filename into its fields, or return [].
    % {var region group model modelid esm forcingid experiment configid ...
    %  years ...}; fewer than ten fields is not a strict name.
    parts = {};
    if ~endsWith(fname, '.nc')
        return
    end
    parts = strsplit(fname(1:end-3), '_');
    if numel(parts) < 10
        parts = {};
    end
end

function hcid = hist_configid_for(cid, core)
    % Historical configid a CORE projection should reference: the table
    % pairs each projection with the historical run driven by the same
    % ESM.  Anything the table does not list -- an ESM or PPE experiment,
    % or a CORE configid yet to be added -- gets '' here: ESM/PPE
    % numbering carries no hist/projection order to read a pairing out
    % of.  Callers fall back on the links table instead, or report an
    % honest skip rather than pairing a projection against itself.
    hcid = '';
    if isfield(core, cid)
        esm = core.(cid).esm;
        if contains(esm, 'MRI')
            hcid = 'C002';
        elseif contains(esm, 'CESM')
            hcid = 'C001';
        end
    end
end

function core = load_core_csv(path)
    % configid -> {scenario, esm} from the CORE experiment table.  Empty
    % (with a warning) when the file is missing, in which case every
    % projection falls back on hist_links or is skipped.
    core = struct();
    if ~exist(path, 'file')
        fprintf(['WARNING: %s not found -- CORE pairing is disabled; ' ...
                 'declare historical runs with hist_links or they will ' ...
                 'be skipped\n'], path);
        return
    end
    [header, rows] = read_csv_rows(path);
    i_cid = find(strcmp(header, 'Core Exp'));
    i_scn = find(strcmp(header, 'Scenario'));
    i_esm = find(strcmp(header, 'ESM'));
    for k = 1:numel(rows)
        row = rows{k};
        cid = csv_cell(row, i_cid);
        if isempty(cid), continue; end
        core.(cid) = struct('scenario', csv_cell(row, i_scn), ...
                            'esm', csv_cell(row, i_esm));
    end
end

function links = load_hist_links(path)
    % configid -> {hist_configid, hist_exp_group} from a user-supplied
    % links CSV.  Columns: configid, hist_configid and an optional
    % hist_exp_group (empty = the projection's own experiment group).
    % Malformed rows are warned about and skipped.
    links = struct();
    if ~exist(path, 'file')
        return
    end
    [header, rows] = read_csv_rows(path);
    i_cid = find(strcmp(header, 'configid'));
    i_hcid = find(strcmp(header, 'hist_configid'));
    i_grp = find(strcmp(header, 'hist_exp_group'));
    for k = 1:numel(rows)
        row = rows{k};
        cid = csv_cell(row, i_cid);
        hcid = csv_cell(row, i_hcid);
        if isempty(cid) || isempty(hcid)
            fprintf('WARNING: %s: malformed row\n', path);
            continue
        end
        links.(cid) = struct('hist_configid', hcid, ...
                             'hist_exp_group', csv_cell(row, i_grp));
    end
end

function [header, rows] = read_csv_rows(path)
    % The header cells and one cell array of rows per data line, with the
    % UTF-8 BOM and CRLF endings the bundled table carries stripped.
    txt = fileread(path);
    txt = strrep(txt, sprintf('\r\n'), sprintf('\n'));
    txt = strrep(txt, char([239 187 191]), '');
    lines = strsplit(strtrim(txt), sprintf('\n'));
    header = strsplit(lines{1}, ',');
    rows = cell(numel(lines) - 1, 1);
    for k = 2:numel(lines)
        rows{k-1} = strsplit(lines{k}, ',');
    end
end

function out = csv_cell(row, i)
    % The trimmed cell at 1-based position i, or '' when absent.
    out = '';
    if ~isempty(i) && i <= numel(row)
        out = strtrim(row{i});
    end
end
