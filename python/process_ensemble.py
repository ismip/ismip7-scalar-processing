# Batch-run scalars.py over an ISMIP7 submission ensemble.
#
# Walks a submissions root laid out as
#     {modelpath}/{group}/{model}/{exp_group}/{configid}/
# (i.e. point --modelpath at .../ISMIP7_submissions/{REGION}), classifies each
# unit via conventions/ISMIP7_experiments_CORE.csv, auto-pairs each projection to
# its historical configid by ESM, and runs scalars.py once per unit.
#
# Non-standard directories and files that do not follow the strict ISMIP7 naming
# rules are logged and skipped — the batch never stops on one bad unit.
#
# Heiko Goelzer 2026 (heig@norceresearch.no)

import argparse
import csv
import datetime as dt
import glob
import os
import re
import subprocess
import sys

_script_dir = os.path.dirname(os.path.abspath(__file__))
_repo_root = os.path.dirname(_script_dir)
_core_csv = os.path.join(_repo_root, "conventions", "ISMIP7_experiments_CORE.csv")

EXP_GROUP_RE = re.compile(r"^(CORE|ESM|PPE)$")
CONFIGID_RE = re.compile(r"^[CEP]\d{3}$")
SELF_PAIRED_SCENARIOS = {"historical", "ctrl"}


def load_core_csv(path):
    """configid -> {'scenario': str, 'esm': str}; empty dict if the CSV is absent."""
    table = {}
    if not os.path.exists(path):
        print(f"WARNING: {path} not found — hist pairing falls back to C001/C002 by parity")
        return table
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            cid = (row.get("Core Exp") or "").strip()
            if cid:
                table[cid] = {
                    "scenario": (row.get("Scenario") or "").strip(),
                    "esm": (row.get("ESM") or "").strip(),
                }
    return table


def parse_ismip7_name(fname):
    """Parse a strict ISMIP7 filename; return dict or None.

    {var}_{region}_{group}_{model}_{modelid}_{esm}_{forcingid}_{experiment}_{configid}_{years}[...]
    Anything after {configid} (year range, optional _c) is ignored — scalars.py
    globs it. Fewer than 10 fields, or a name whose 9th field is not the expected
    configid, is treated as non-strict.
    """
    parts = fname[:-3].split("_") if fname.endswith(".nc") else fname.split("_")
    if len(parts) < 10:
        return None
    return {
        "var": parts[0],
        "region": parts[1],
        "group": parts[2],
        "model": parts[3],
        "modelid": parts[4],
        "esm": parts[5],
        "forcingid": parts[6],
        "experiment": parts[7],
        "configid": parts[8],
    }


def hist_configid_for(cid, core):
    """Historical configid a projection should reference (CSV ESM, else parity)."""
    esm = core.get(cid, {}).get("esm", "")
    if "MRI" in esm:
        return "C002"
    if "CESM" in esm:
        return "C001"
    # Not in the CSV (future ESM/PPE) — fall back on numeric parity.
    try:
        n = int(cid[1:])
        return f"{cid[0]}{n - 1:03d}" if n % 2 == 0 else cid
    except ValueError:
        return "C001"


def discover_units(root):
    """Yield (group, model, exp_group, configid, path) plus a list of skip notes."""
    units, skips = [], []
    for path in sorted(glob.glob(os.path.join(root, "*", "*", "*", "*"))):
        if not os.path.isdir(path):
            continue
        rel = os.path.relpath(path, root).split(os.sep)
        if len(rel) != 4:
            continue
        group, model, exp_group, configid = rel
        key = f"{group}/{model}/{exp_group}/{configid}"
        if any(("*" in c) or c.startswith(".") for c in rel):
            skips.append((key, "non-standard dir (glob/hidden artifact)"))
            continue
        if not EXP_GROUP_RE.match(exp_group) or not CONFIGID_RE.match(configid):
            skips.append((key, "non-standard dir"))
            continue
        units.append((group, model, exp_group, configid, path))
    return units, skips


def build_command(args, unit, core):
    """Return (cmd list, note) or (None, skip-reason)."""
    group, model, exp_group, configid, path = unit

    lithks = sorted(glob.glob(os.path.join(path, "lithk_*.nc")))
    if not lithks:
        return None, "no lithk file"
    fname = os.path.basename(lithks[0])
    meta = parse_ismip7_name(fname)
    if meta is None or meta["configid"] != configid or meta["region"] != args.region:
        return None, f"non-strict filename ({fname})"
    if meta["group"] != group or meta["model"] != model:
        return None, (f"filename group/model field != directory "
                      f"({meta['group']}/{meta['model']} vs {group}/{model})")

    scenario = core.get(configid, {}).get("scenario", meta["experiment"])

    cmd = [
        args.python, args.scalars_script,
        "--region", args.region,
        "--group", meta["group"], "--model", meta["model"],
        "--modelid", meta["modelid"], "--esm", meta["esm"],
        "--forcingid", meta["forcingid"],
        "--experiment", meta["experiment"],
        "--configid", configid, "--exp-group", exp_group,
        "--modelpath", args.modelpath,
    ]

    if scenario in SELF_PAIRED_SCENARIOS:
        cmd += ["--hist", meta["experiment"],
                "--hist-configid", configid, "--hist-exp-group", exp_group]
        note = f"self-paired ({scenario})"
    else:
        hcid = hist_configid_for(configid, core)
        hpath = os.path.join(args.modelpath, meta["group"], meta["model"], exp_group, hcid)
        hlithks = sorted(glob.glob(os.path.join(hpath, "lithk_*.nc")))
        if not hlithks:
            return None, f"no historical {hcid}"
        hmeta = parse_ismip7_name(os.path.basename(hlithks[0]))
        hist_exp = hmeta["experiment"] if hmeta else "historical"
        cmd += ["--hist", hist_exp,
                "--hist-configid", hcid, "--hist-exp-group", exp_group]
        note = f"{scenario} -> hist {hcid}"

    if args.params_path:
        cmd += ["--params-path", args.params_path]
    if args.outpath:
        cmd += ["--outpath", args.outpath]
    if args.histout is not None:
        cmd += ["--histout", str(args.histout)]
    if args.basins:
        cmd += ["--basins"]
    return cmd, note


def main():
    p = argparse.ArgumentParser(description="Batch scalar processing over an ISMIP7 ensemble")
    p.add_argument("--region", required=True, choices=["AIS", "GrIS"])
    p.add_argument("--modelpath", required=True,
                   help="Submissions root, e.g. .../ISMIP7_submissions/GrIS")
    p.add_argument("--params-path", default=None,
                   help="Root for params.nc (<params-path>/<group>/<model>/params.nc)")
    p.add_argument("--outpath", default=None, help="Passed through to scalars.py")
    p.add_argument("--exp-group", default=None, help="Only this exp_group (CORE/ESM/PPE)")
    p.add_argument("--groups", default=None, help="Comma-separated group filter")
    p.add_argument("--models", default=None, help="Comma-separated model filter")
    p.add_argument("--configids", default=None, help="Comma-separated configid filter")
    p.add_argument("--histout", type=int, default=None, help="Passed through to scalars.py")
    p.add_argument("--basins", action="store_true", help="Passed through to scalars.py")
    p.add_argument("--dry-run", action="store_true", help="Print planned commands, run nothing")
    p.add_argument("--scalars-script", default=os.path.join(_script_dir, "scalars.py"))
    p.add_argument("--python", default=sys.executable)
    p.add_argument("--log-dir", default=os.path.join(_repo_root, "Output", "logs"))
    args = p.parse_args()

    core = load_core_csv(_core_csv)
    units, skips = discover_units(args.modelpath)

    def keep(unit):
        group, model, exp_group, configid, _ = unit
        if args.exp_group and exp_group != args.exp_group:
            return False
        if args.groups and group not in args.groups.split(","):
            return False
        if args.models and model not in args.models.split(","):
            return False
        if args.configids and configid not in args.configids.split(","):
            return False
        return True

    units = [u for u in units if keep(u)]

    os.makedirs(args.log_dir, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    master_path = os.path.join(args.log_dir, f"ensemble_{args.region}_{stamp}.log")
    results = []

    for note_key, reason in skips:
        results.append((note_key, f"SKIP: {reason}", ""))

    for unit in units:
        group, model, exp_group, configid, _ = unit
        key = f"{group}/{model}/{exp_group}/{configid}"
        cmd, note = build_command(args, unit, core)
        if cmd is None:
            results.append((key, f"SKIP: {note}", ""))
            print(f"[SKIP] {key} — {note}")
            continue
        if args.dry_run:
            results.append((key, "DRY-RUN", note))
            print(f"[PLAN] {key} — {note}\n       {' '.join(cmd)}")
            continue

        log_path = os.path.join(
            args.log_dir, f"{args.region}_{group}_{model}_{exp_group}_{configid}.log")
        print(f"[RUN ] {key} — {note}", flush=True)
        with open(log_path, "w") as lf:
            lf.write(" ".join(cmd) + "\n\n")
            lf.flush()
            proc = subprocess.run(cmd, stdout=lf, stderr=subprocess.STDOUT)
        tail = ""
        try:
            with open(log_path) as lf:
                lines = [ln for ln in lf if ln.startswith("SKIP:")]
                tail = lines[-1].strip() if lines else ""
        except OSError:
            pass
        if proc.returncode == 0:
            status = "OK"
        elif proc.returncode == 2:
            status = tail or "SKIP: (see log)"
        else:
            status = f"FAIL: exit {proc.returncode}"
        results.append((key, status, os.path.basename(log_path)))
        print(f"       {status}")

    # ---- Summary ----
    n_ok = sum(1 for _, s, _ in results if s == "OK")
    n_skip = sum(1 for _, s, _ in results if s.startswith("SKIP") or s == "DRY-RUN")
    n_fail = sum(1 for _, s, _ in results if s.startswith("FAIL"))
    lines = [f"ISMIP7 ensemble run — {args.region} — {stamp}",
             f"modelpath: {args.modelpath}",
             f"units: {len(results)}   ok: {n_ok}   skipped: {n_skip}   failed: {n_fail}",
             ""]
    for key, status, log in sorted(results):
        lines.append(f"  {key:<55}  {status}" + (f"   [{log}]" if log else ""))
    report = "\n".join(lines)
    with open(master_path, "w") as f:
        f.write(report + "\n")
    print("\n" + report)
    print(f"\nSummary written to {master_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
