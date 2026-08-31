"""Batch-run the scalar processing over an ISMIP7 submission ensemble.

Walks a submissions root laid out as
``{modelpath}/{group}/{model}/{exp_group}/{configid}/`` -- point ``--modelpath``
at ``.../ISMIP7_submissions/{REGION}`` -- classifies each unit against the
bundled CORE experiment table, pairs each projection with its historical
configid by ESM, and processes each unit in a subprocess of its own.

Directories and files that do not follow the strict ISMIP7 naming rules are
logged and skipped: the batch never stops on one bad unit.

Originally written as a script by Heiko Goelzer 2026 (heig@norceresearch.no).
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import glob
import os
import re
import subprocess
import sys

from ismip7_scalars import __version__
from ismip7_scalars.naming import parse_ismip7_name
from ismip7_scalars.paths import core_experiments_path

EXP_GROUP_RE = re.compile(r'^(CORE|ESM|PPE)$')
CONFIGID_RE = re.compile(r'^[CEP]\d{3}$')

#: Scenarios that are their own reference: there is no earlier run to pair
#: them with, so the reference state comes from within the run itself.
SELF_PAIRED_SCENARIOS = {'historical', 'ctrl'}


def load_core_csv(path=None):
    """``configid -> {'scenario': str, 'esm': str}`` from the CORE table.

    The table is this package's own data rather than the project's: it records
    which historical run each projection is paired with, which is a decision
    the driver makes.  The ISMIP7 data request, which *is* the project's, comes
    from isschecker instead -- see :mod:`ismip7_scalars.paths`.

    Returns an empty table if the file is missing, in which case pairing falls
    back on the configid numbering.
    """
    if path is None:
        path = str(core_experiments_path())
    table = {}
    if not os.path.exists(path):
        print(f'WARNING: {path} not found -- hist pairing falls back to '
              f'configid parity')
        return table
    with open(path, newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            cid = (row.get('Core Exp') or '').strip()
            if cid:
                table[cid] = {
                    'scenario': (row.get('Scenario') or '').strip(),
                    'esm': (row.get('ESM') or '').strip(),
                }
    return table


def hist_configid_for(cid, core):
    """Historical configid a projection should reference.

    The CORE table pairs each projection with the historical run driven by the
    same ESM.  For a configid the table does not list -- a future ESM or PPE
    experiment -- fall back on the numbering convention that pairs an even
    configid with the odd one below it, and return ``None`` when even that
    gives no candidate, so that the caller reports an honest skip instead of
    pairing a projection against itself.
    """
    esm = core.get(cid, {}).get('esm', '')
    if 'MRI' in esm:
        return 'C002'
    if 'CESM' in esm:
        return 'C001'
    try:
        n = int(cid[1:])
    except ValueError:
        return None
    if n % 2 == 0:
        return f'{cid[0]}{n - 1:03d}'
    return None


def discover_units(root):
    """Find every processable unit under a submissions root.

    Returns ``(units, skips)``, where a unit is
    ``(group, model, exp_group, configid, path)`` and a skip is
    ``(key, reason)``.
    """
    units, skips = [], []
    for path in sorted(glob.glob(os.path.join(root, '*', '*', '*', '*'))):
        if not os.path.isdir(path):
            continue
        rel = os.path.relpath(path, root).split(os.sep)
        if len(rel) != 4:
            continue
        group, model, exp_group, configid = rel
        key = f'{group}/{model}/{exp_group}/{configid}'
        # Hidden directories never reach here: `glob` does not match a
        # leading dot, so a `.snapshot` or `.ipynb_checkpoints` alongside a
        # real unit is invisible rather than skipped.
        if not EXP_GROUP_RE.match(exp_group) or not CONFIGID_RE.match(
                configid):
            skips.append((key, 'non-standard dir'))
            continue
        units.append((group, model, exp_group, configid, path))
    return units, skips


def build_command(args, unit, core):
    """Plan one unit.  Returns ``(cmd, note)``, or ``(None, reason)`` to skip."""
    group, model, exp_group, configid, path = unit

    lithks = sorted(glob.glob(os.path.join(path, 'lithk_*.nc')))
    if not lithks:
        return None, 'no lithk file'
    fname = os.path.basename(lithks[0])
    meta = parse_ismip7_name(fname)
    if (meta is None or meta['configid'] != configid
            or meta['region'] != args.region):
        return None, f'non-strict filename ({fname})'
    if meta['group'] != group or meta['model'] != model:
        return None, (f'filename group/model field != directory '
                      f"({meta['group']}/{meta['model']} vs {group}/{model})")

    scenario = core.get(configid, {}).get('scenario', meta['experiment'])

    cmd = [
        args.python, '-m', 'ismip7_scalars',
        '--region', args.region,
        '--group', meta['group'], '--model', meta['model'],
        '--modelid', meta['modelid'], '--esm', meta['esm'],
        '--forcingid', meta['forcingid'],
        '--experiment', meta['experiment'],
        '--configid', configid, '--exp-group', exp_group,
        '--modelpath', args.modelpath,
    ]

    if scenario in SELF_PAIRED_SCENARIOS:
        cmd += ['--hist', meta['experiment'],
                '--hist-configid', configid, '--hist-exp-group', exp_group]
        note = f'self-paired ({scenario})'
    else:
        hcid = hist_configid_for(configid, core)
        if hcid is None:
            return None, (
                f"no historical run is defined for {configid} "
                f"('{scenario}'); pair it by hand with --hist-configid")
        if hcid == configid:
            return None, (f'{configid} would be paired against itself; '
                          f'a projection needs a separate historical run')
        hpath = os.path.join(args.modelpath, meta['group'], meta['model'],
                             exp_group, hcid)
        hlithks = sorted(glob.glob(os.path.join(hpath, 'lithk_*.nc')))
        if not hlithks:
            return None, f'no historical {hcid}'
        hmeta = parse_ismip7_name(os.path.basename(hlithks[0]))
        hist_exp = hmeta['experiment'] if hmeta else 'historical'
        cmd += ['--hist', hist_exp,
                '--hist-configid', hcid, '--hist-exp-group', exp_group]
        note = f'{scenario} -> hist {hcid}'

    if args.params_path:
        cmd += ['--params-path', args.params_path]
    if args.datapath:
        cmd += ['--datapath', args.datapath]
    if args.outpath:
        cmd += ['--outpath', args.outpath]
    if args.histout is not None:
        cmd += ['--histout', str(args.histout)]
    if args.basins:
        cmd += ['--basins']
    return cmd, note


def build_parser():
    """The ``ismip7-scalars-ensemble`` command line."""
    parser = argparse.ArgumentParser(
        prog='ismip7-scalars-ensemble',
        description='Batch scalar processing over an ISMIP7 ensemble')
    parser.add_argument('--version', action='version',
                        version=f'ismip7-scalars-ensemble {__version__}')
    parser.add_argument('--region', required=True, choices=['AIS', 'GrIS'])
    parser.add_argument('--modelpath', required=True,
                        help='Submissions root, e.g. '
                             '.../ISMIP7_submissions/GrIS')
    parser.add_argument('--datapath', default=None,
                        help='Passed through: path to the generic data files')
    parser.add_argument('--params-path', default=None,
                        help='Root for params.nc '
                             '(<params-path>/<group>/<model>/params.nc)')
    parser.add_argument('--outpath', default=None, help='Passed through')
    parser.add_argument('--exp-group', default=None,
                        help='Only this exp_group (CORE/ESM/PPE)')
    parser.add_argument('--groups', default=None,
                        help='Comma-separated group filter')
    parser.add_argument('--models', default=None,
                        help='Comma-separated model filter')
    parser.add_argument('--configids', default=None,
                        help='Comma-separated configid filter')
    parser.add_argument('--histout', type=int, default=None,
                        help='Passed through')
    parser.add_argument('--basins', action='store_true',
                        help='Passed through')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print planned commands, run nothing')
    parser.add_argument('--core-csv', default=None,
                        help='Override the bundled CORE experiment table')
    parser.add_argument('--python', default=sys.executable,
                        help='Interpreter used to run each unit')
    parser.add_argument('--log-dir', default=None,
                        help='Where per-unit logs and the run summary go '
                             '(default: ./Output/logs)')
    return parser


def keep_unit(args, unit):
    """Whether a discovered unit passes the command-line filters."""
    group, model, exp_group, configid, _ = unit
    if args.exp_group and exp_group != args.exp_group:
        return False
    if args.groups and group not in args.groups.split(','):
        return False
    if args.models and model not in args.models.split(','):
        return False
    if args.configids and configid not in args.configids.split(','):
        return False
    return True


def format_report(args, stamp, results):
    """The run summary, as one string."""
    n_ok = sum(1 for _, s, _ in results if s == 'OK')
    n_skip = sum(1 for _, s, _ in results
                 if s.startswith('SKIP') or s == 'DRY-RUN')
    n_fail = sum(1 for _, s, _ in results if s.startswith('FAIL'))
    lines = [f'ISMIP7 ensemble run -- {args.region} -- {stamp}',
             f'modelpath: {args.modelpath}',
             f'units: {len(results)}   ok: {n_ok}   skipped: {n_skip}   '
             f'failed: {n_fail}',
             '']
    for key, status, log in sorted(results):
        lines.append(f'  {key:<55}  {status}'
                     + (f'   [{log}]' if log else ''))
    return '\n'.join(lines)


def main(argv=None):
    """``ismip7-scalars-ensemble`` entry point.

    Always returns 0 unless the driver itself fails: a unit that could not be
    processed is a line in the summary, not a failure of the batch.
    """
    args = build_parser().parse_args(argv)
    log_dir = args.log_dir or os.path.join(os.getcwd(), 'Output', 'logs')

    core = load_core_csv(args.core_csv)
    units, skips = discover_units(args.modelpath)
    units = [u for u in units if keep_unit(args, u)]

    os.makedirs(log_dir, exist_ok=True)
    stamp = dt.datetime.now().strftime('%Y%m%dT%H%M%S')
    master_path = os.path.join(log_dir,
                               f'ensemble_{args.region}_{stamp}.log')
    results = [(key, f'SKIP: {reason}', '') for key, reason in skips]

    for unit in units:
        group, model, exp_group, configid, _ = unit
        key = f'{group}/{model}/{exp_group}/{configid}'
        cmd, note = build_command(args, unit, core)
        if cmd is None:
            results.append((key, f'SKIP: {note}', ''))
            print(f'[SKIP] {key} -- {note}')
            continue
        if args.dry_run:
            results.append((key, 'DRY-RUN', note))
            print(f"[PLAN] {key} -- {note}\n       {' '.join(cmd)}")
            continue

        log_path = os.path.join(
            log_dir,
            f'{args.region}_{group}_{model}_{exp_group}_{configid}.log')
        print(f'[RUN ] {key} -- {note}', flush=True)
        with open(log_path, 'w') as lf:
            lf.write(' '.join(cmd) + '\n\n')
            lf.flush()
            proc = subprocess.run(cmd, stdout=lf, stderr=subprocess.STDOUT)
        results.append((key, unit_status(proc.returncode, log_path),
                        os.path.basename(log_path)))
        print(f'       {results[-1][1]}')

    report = format_report(args, stamp, results)
    with open(master_path, 'w') as f:
        f.write(report + '\n')
    print('\n' + report)
    print(f'\nSummary written to {master_path}')
    return 0


def unit_status(returncode, log_path):
    """Turn one unit's exit code into a summary line.

    Exit 2 means the run skipped itself over a missing input and said why in
    its log, so lift that reason into the summary rather than reporting a
    bare exit code.
    """
    if returncode == 0:
        return 'OK'
    if returncode != 2:
        return f'FAIL: exit {returncode}'
    try:
        with open(log_path) as lf:
            lines = [ln for ln in lf if ln.startswith('SKIP:')]
        if lines:
            return lines[-1].strip()
    except OSError:
        pass
    return 'SKIP: (see log)'


if __name__ == '__main__':
    sys.exit(main())
