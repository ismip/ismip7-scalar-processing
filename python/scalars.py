# Calculate scalar variables from ISMIP7 3D model output
# Heiko Goelzer 2026 (heig@norceresearch.no)

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import argparse
import csv
import glob
import netCDF4 as nc
import numpy as np
from types import SimpleNamespace

from slc import slc_vaf
from slc import slc_G2020
from slc import slc_A2020

# Region-specific data file naming
FILE_CONFIG = {
    "AIS": {
        "af2":    "af2_AIS_{res}000m_v1.nc",
        "maxmask":"maxmask1_AIS_{res}000m_v0.nc",
        "gic":    "iaf2_GIC_AIS_{res}000m_v0.nc",
        "basins": "basins_regions_AIS_Rignot_extended_{res}000m_v1.nc",
    },
    "GrIS": {
        "af2":    "af2_GrIS_{res}000m_v1.nc",
        "maxmask":"maxmask1_GrIS_{res}000m_v1.nc",
        "gic":    "iaf2_GIC_GrIS_{res}000m_v0.nc",
        "basins": "basins_GrIS_Mouginot_extended_{res}000m_v1.nc",
    },
}

# Region-specific defaults
DEFAULTS = {
    "AIS":  {"group": "VUW",   "model": "PISM1",             "experiment": "ssp585",
             "modelid": "m001", "esm": "CESM2", "forcingid": "f001", "configid": "E001",
             "exp_group": "ESM"},
    "GrIS": {"group": "NORCE", "model": "CISM16x-MAR312-p50", "experiment": "ssp585",
             "modelid": "m001", "esm": "CESM2-WACCM",  "forcingid": "f001", "configid": "E001",
             "exp_group": "ESM"},
}

# User settings
parser = argparse.ArgumentParser(description="ISMIP7 scalar processing")
parser.add_argument("--region",         required=True, choices=["AIS", "GrIS"],
                                                                        help="Ice sheet region")
parser.add_argument("--group",          default=None,                   help="Submitting group/lab")
parser.add_argument("--model",          default=None,                   help="Ice sheet model name")
parser.add_argument("--experiment",     default=None,                   help="Experiment name (e.g. ssp126, ctrl)")
parser.add_argument("--modelid",        default=None,                   help="ISM member ID (e.g. m001)")
parser.add_argument("--esm",            default=None,                   help="Climate forcing model (e.g. NorESM2-MM)")
parser.add_argument("--forcingid",      default=None,                   help="Forcing realization (e.g. f001)")
parser.add_argument("--configid",       default=None,                   help="Configuration ID (e.g. C001)")
parser.add_argument("--exp-group",      default=None,                   help="Experiment directory name (CORE, ESM, or PPE)")
parser.add_argument("--hist",           default="historical",           help="Historical experiment name")
parser.add_argument("--hist-exp-group", default=None,                   help="History experiment directory (default: same as --exp-group)")
parser.add_argument("--refyear",        type=int, default=None,         help="Year to use as SLC reference (default: last timestep of hist experiment)")
parser.add_argument("--datapath",       default=None,                   help="Path to generic data files (default: ../Data/<region>)")
parser.add_argument("--modelpath",      default=None,                   help="Path to model output (default: ../Models/<region>)")
_script_dir = os.path.dirname(os.path.abspath(__file__))
_default_outpath = os.path.join(_script_dir, "..", "Output")
parser.add_argument("--outpath",        default=_default_outpath,       help="Root path for output (nc/ and csv/ created as subdirectories)")
parser.add_argument("--histout",        type=int, default=-1,
                                                    help="Hist timesteps to prepend to output: 0=none, 1=last only, -1=all (default), N=last N")
parser.add_argument("--basins",         action="store_true",
                                                    help="Compute per-basin and per-region integrals in addition to whole ice sheet")
parser.add_argument("--no-mm",          action="store_true",
                                                    help="Skip whole-ice-sheet (mm) integral (use with --basins to get basins only)")
args = parser.parse_args()

region    = args.region
group     = args.group      or DEFAULTS[region]["group"]
model     = args.model      or DEFAULTS[region]["model"]
exp       = args.experiment or DEFAULTS[region]["experiment"]
modelid   = args.modelid    or DEFAULTS[region]["modelid"]
esm       = args.esm        or DEFAULTS[region]["esm"]
forcingid = args.forcingid  or DEFAULTS[region]["forcingid"]
configid  = args.configid   or DEFAULTS[region]["configid"]
exp_group = args.exp_group  or DEFAULTS[region]["exp_group"]
hist      = args.hist
hist_exp_group = args.hist_exp_group or exp_group
datapath  = args.datapath  if args.datapath  else os.path.join(_script_dir, "..", "Data",   region)
modelpath = args.modelpath if args.modelpath else os.path.join(_script_dir, "..", "Models", region)

outpath   = args.outpath
ncpath    = os.path.join(outpath, "nc")
csvpath   = os.path.join(outpath, "csv")
histout   = args.histout


def find_model_file(dirpath, var, region, group, model, modelid, esm, forcingid, experiment, configid):
    pattern = os.path.join(dirpath,
        f"{var}_{region}_{group}_{model}_{modelid}_{esm}_{forcingid}_{experiment}_{configid}_*.nc")
    files = glob.glob(pattern)
    if len(files) == 0:
        raise FileNotFoundError(f"No file found:\n  {pattern}")
    if len(files) > 1:
        raise ValueError(f"Multiple files match for {var} — cannot disambiguate:\n  " + "\n  ".join(files))
    return files[0]

def detect_res(modelpath, region, group, model, modelid, esm, forcingid, exp, configid, exp_group):
    """Derive data-file resolution string (e.g. '08') from model grid x-spacing."""
    exppath = os.path.join(modelpath, group, model, exp_group)
    f = find_model_file(exppath, "lithk", region, group, model, modelid, esm, forcingid, exp, configid)
    ds = nc.Dataset(f, 'r')
    dx_m = abs(float(ds.variables["x"][1]) - float(ds.variables["x"][0]))
    ds.close()
    return f"{round(dx_m / 1000):02d}"

def region_display_name(raw, region):
    """Map internal region key to output name: mm → ais/gris, others unchanged."""
    return region.lower() if raw == 'mm' else raw

res = detect_res(modelpath, region, group, model, modelid, esm, forcingid, exp, configid, exp_group)
print(f"Auto-detected resolution: {res} km")

## What output to produce
flg_mm = not args.no_mm  # Integrals on model mask
flg_bm = args.basins     # IMBIE3 basins

# Description for netcdf global
file_description = "ISMIP7 scalar output. Heiko Goelzer 2026, heig@norceresearch.no"

# Options
# A2020: seamless hist+exp cumulative (True, default) vs. relative to reference (False)
flg_A20_cumul = True

# More output
verbose = False

################################################################
# File names and mapping

cfg        = FILE_CONFIG[region]
af2input   = datapath + "/" + cfg["af2"].format(res=res)
mminput    = datapath + "/" + cfg["maxmask"].format(res=res)
gicinput   = datapath + "/" + cfg["gic"].format(res=res)
basininput = datapath + "/" + cfg["basins"].format(res=res)
# file_stem built after time_out is known (year range derived from output time axis)

####################################################
# Prepare generic data file

# Defined ocean area
oarea = 3.625e14  # m2 (Gregory et al., 2019)

# Prepare ice sheet mask
idat = nc.Dataset(mminput, 'r')
maxmask1 = idat.variables["maxmask1"][:,:]
idat.close()
sheet = maxmask1 * 0 + 1  # sheet region covers the entire grid
regions = SimpleNamespace()
regions.mm = sheet

# Prepare basin masks
if flg_bm:
    idat = nc.Dataset(basininput, 'r')
    if region == "AIS":
        # IMBIE3 regions: 1 West Antarctica, 2 East Antarctica, 3 Peninsula
        basinid = idat.variables["regions"][:,:]
        regions.wais = (basinid==1).astype(float)
        regions.eais = (basinid==2).astype(float)
        regions.pina = (basinid==3).astype(float)
        # IMBIE3 basins 1 to 18
        basinid = idat.variables["basins"][:,:]
        regions.r01 = (basinid== 1).astype(float)
        regions.r02 = (basinid== 2).astype(float)
        regions.r03 = (basinid== 3).astype(float)
        regions.r04 = (basinid== 4).astype(float)
        regions.r05 = (basinid== 5).astype(float)
        regions.r06 = (basinid== 6).astype(float)
        regions.r07 = (basinid== 7).astype(float)
        regions.r08 = (basinid== 8).astype(float)
        regions.r09 = (basinid== 9).astype(float)
        regions.r10 = (basinid==10).astype(float)
        regions.r11 = (basinid==11).astype(float)
        regions.r12 = (basinid==12).astype(float)
        regions.r13 = (basinid==13).astype(float)
        regions.r14 = (basinid==14).astype(float)
        regions.r15 = (basinid==15).astype(float)
        regions.r16 = (basinid==16).astype(float)
        regions.r17 = (basinid==17).astype(float)
        regions.r18 = (basinid==18).astype(float)
        idat.close()
        # Test no gaps
        sheettest = regions.wais + regions.eais + regions.pina
        nx, ny = regions.wais.shape
        if verbose:
            print(np.sum(sheet), np.sum(sheettest), nx*ny)
    elif region == "GrIS":
        # IMBIE3 Mouginot basins: From NO clockwise
        basinid = idat.variables["basins"][:,:]
        regions.no = (basinid==1).astype(float)
        regions.ne = (basinid==2).astype(float)
        regions.ce = (basinid==3).astype(float)
        regions.se = (basinid==4).astype(float)
        regions.sw = (basinid==5).astype(float)
        regions.cw = (basinid==6).astype(float)
        regions.nw = (basinid==7).astype(float)
        idat.close()
        # Test no gaps
        sheettest = regions.no + regions.ne + regions.ce + regions.se + regions.sw + regions.cw + regions.nw
        nx, ny = regions.no.shape
        if verbose:
            print(np.sum(sheet), np.sum(sheettest), nx*ny)

# Prepare area factors
idat = nc.Dataset(af2input, 'r')
af2  = idat.variables["af2"][:,:]
idat.close()
# GIC mask: always loaded
idat = nc.Dataset(gicinput, 'r')
iaf2GIC = idat.variables["iaf2"][:,:]
idat.close()

###########################################################
# Prepare model output

# Main experiment
exppath = modelpath + "/" + group + "/" + model + "/" + exp_group
# Model geometry
idat = nc.Dataset(find_model_file(exppath, "lithk", region, group, model, modelid, esm, forcingid, exp, configid), 'r')
lithk = idat.variables["lithk"][:,:,:]
# Pick up time axis
time_model     = idat.variables["time"][:]
time_units     = idat.variables["time"].units
time_long_name = idat.variables["time"].long_name
time_calendar  = idat.variables["time"].calendar
idat.close()
idat = nc.Dataset(find_model_file(exppath, "topg", region, group, model, modelid, esm, forcingid, exp, configid), 'r')
topg = idat.variables["topg"][:,:,:]
idat.close()

# Historical experiment
histpath = modelpath + "/" + group + "/" + model + "/" + hist_exp_group
# Model geometry
idat = nc.Dataset(find_model_file(histpath, "lithk", region, group, model, modelid, esm, forcingid, hist, configid), 'r')
time_ref_var = idat.variables["time"]
n_hist = len(time_ref_var)
time_hist = time_ref_var[:]
ref_in_exp = False
ref_idx_exp = None
if args.refyear is not None:
    dates = nc.num2date(time_ref_var[:], time_ref_var.units, calendar=time_ref_var.calendar)
    idx_arr = np.where(np.array([d.year for d in dates]) == args.refyear)[0]
    if len(idx_arr) > 0:
        ref_idx = int(idx_arr[-1])
    else:
        ref_idx = n_hist - 1  # refyear not in hist; will search exp after loading
        ref_in_exp = True
else:
    ref_idx = n_hist - 1  # last timestep (absolute index)

# Number of hist timesteps to prepend to output
if exp == hist:
    hist_n_out = 0  # full run already output via exp
elif histout == 0:
    hist_n_out = 0
elif histout == -1:
    hist_n_out = n_hist
else:
    if histout > n_hist:
        print(f"Warning: --histout {histout} exceeds hist length {n_hist}; using all {n_hist} timesteps")
        hist_n_out = n_hist
    else:
        hist_n_out = histout
hist_start = n_hist - hist_n_out

lithk_ref = idat.variables["lithk"][ref_idx,:,:]
need_hist = (exp != hist) and flg_A20_cumul
need_hist_arrays = need_hist or (hist_n_out > 0)
if need_hist_arrays:
    lithk_hist = idat.variables["lithk"][:,:,:]
idat.close()
idat = nc.Dataset(find_model_file(histpath, "topg", region, group, model, modelid, esm, forcingid, hist, configid), 'r')
topg_ref = idat.variables["topg"][ref_idx,:,:]
if need_hist_arrays:
    topg_hist = idat.variables["topg"][:,:,:]
idat.close()

# For exp==hist, hist arrays are the same as exp arrays
if exp == hist and flg_A20_cumul:
    lithk_hist = lithk
    topg_hist = topg


# If refyear was not found in the hist file, search the exp file
if ref_in_exp:
    print(f"Warning: --refyear {args.refyear} not found in hist experiment '{hist}'; searching exp '{exp}'")
    dates_exp = nc.num2date(time_model, time_units, calendar=time_calendar)
    idx_arr = np.where(np.array([d.year for d in dates_exp]) == args.refyear)[0]
    if len(idx_arr) == 0:
        raise ValueError(f"--refyear {args.refyear} not found in hist experiment '{hist}' or exp '{exp}'")
    ref_idx_exp = int(idx_arr[-1])
    lithk_ref = lithk[ref_idx_exp,:,:]
    topg_ref  = topg[ref_idx_exp,:,:]

# Add model params
params_file = modelpath + "/" + group + "/" + model + "/params.nc"
if not os.path.exists(params_file):
    raise FileNotFoundError(
        f"Missing params.nc for {group}/{model}.\n"
        f"  Expected: {params_file}\n"
        f"  Generate it with: bash tools/set_params.sh"
    )
idat = nc.Dataset(params_file, 'r')
scalar = idat.variables["rhoi"]; rhoi = scalar[()]
scalar = idat.variables["rhow"]; rhow = scalar[()]
scalar = idat.variables["rhof"]; rhof = scalar[()]
idat.close()
c = SimpleNamespace()
c.RHOI  = rhoi  # kg/m3
c.RHOSW = rhow  # kg/m3
c.RHOFW = rhof  # kg/m3
c.AO    = oarea  # m2

# Model masks
idat = nc.Dataset(find_model_file(exppath, "sftgif", region, group, model, modelid, esm, forcingid, exp, configid), 'r')
sftgif = idat.variables["sftgif"][:,:,:]
idat.close()
idat = nc.Dataset(find_model_file(exppath, "sftgrf", region, group, model, modelid, esm, forcingid, exp, configid), 'r')
sftgrf = idat.variables["sftgrf"][:,:,:]
idat.close()
idat = nc.Dataset(find_model_file(exppath, "sftflf", region, group, model, modelid, esm, forcingid, exp, configid), 'r')
sftflf = idat.variables["sftflf"][:,:,:]
idat.close()

# Load hist mask fields needed for ST scalars (iareagr, iareafl)
sftgrf_hist = sftgrf
sftflf_hist = sftflf
if hist_n_out > 0 and exp != hist:
    idat = nc.Dataset(find_model_file(histpath, "sftgrf", region, group, model, modelid, esm, forcingid, hist, configid), 'r')
    sftgrf_hist = idat.variables["sftgrf"][:,:,:]
    idat.close()
    idat = nc.Dataset(find_model_file(histpath, "sftflf", region, group, model, modelid, esm, forcingid, hist, configid), 'r')
    sftflf_hist = idat.variables["sftflf"][:,:,:]
    idat.close()

#######################################
# See what we have

if verbose:
    print("# Generic")
    print("af2:", af2.shape)
    print("maxmask1:", maxmask1.shape)
    print("iaf2GIC:", iaf2GIC.shape)
    print("# Model")
    print("lithk_ref:", lithk_ref.shape)
    print("topg_ref:", topg_ref.shape)
    print("lithk:", lithk.shape)
    print("topg:", topg.shape)
    print(rhoi, rhow, rhof)
    print("sftgif:", sftgif.shape)
    print("sftgrf:", sftgrf.shape)
    print("sftflf:", sftflf.shape)

FL_SCALAR_SPECS = [
    ("tendacabf",       "acabf",       "tendency_of_land_ice_mass_due_to_surface_mass_balance",        "kg s-1"),
    ("tendlibmassbfgr", "libmassbfgr", "tendency_of_land_ice_mass_due_to_basal_mass_balance_grounded", "kg s-1"),
    ("tendlibmassbffl", "libmassbffl", "tendency_of_land_ice_mass_due_to_basal_mass_balance_floating", "kg s-1"),
    ("tendlicalvf",     "licalvf",     "tendency_of_land_ice_mass_due_to_calving",                     "kg s-1"),
    ("tendlifmassbf",   "lifmassbf",   "tendency_of_land_ice_mass_due_to_ice_front_melting",            "kg s-1"),
]
skipped_scalars = []

#############################################################
# Pre-compute shared time axis and file stem (same for all regions)

nt = len(lithk)
time_out = np.concatenate([time_hist[hist_start:], time_model]) if hist_n_out > 0 else time_model
dates_out  = nc.num2date(time_out, time_units, calendar=time_calendar)
year_start = dates_out[0].year  - 1
year_end   = dates_out[-1].year - 1
file_stem  = (f"{region}_{group}_{model}_{modelid}_{esm}_{forcingid}"
              f"_{exp}_{configid}_{year_start}-{year_end}")
nominal_yrs = [d.year - 1 for d in dates_out]

#############################################################
# SLC integrals — two passes: with GIC masking (-gic suffix) and without

for gic_mask, gic_suffix in [(iaf2GIC, '-gic'), (np.ones_like(iaf2GIC), '')]:

    # Reference state for this GIC mode
    H0 = lithk_ref * maxmask1 * gic_mask
    B0 = topg_ref
    # TODO clarify if S0=0 is correct for all models
    S0 = topg_ref * 0.0  # Fix sea level to 0

    for regionName_raw, region_mask in vars(regions).items():
        regionName = region_display_name(regionName_raw, region) + gic_suffix
        print(f"{regionName}")

        VAF_list = []
        G20_list = []
        A20_list = []
        VAF_hist, G20_hist, A20_hist = [], [], []

        # Area weighting and basin masking
        A = region_mask * af2 * (float(res)*1000.0)**2

        # ---- Hist portion (VAF, G2020, and non-cumulative A2020) ----
        if hist_n_out > 0:
            for n in range(hist_start, n_hist):
                H = lithk_hist[n,:,:] * maxmask1 * gic_mask
                B = topg_hist[n,:,:]
                VAF_hist.append(slc_vaf.get_slc_vaf(H0, H, B0, B, S0, S0, A, c))
                G20_hist.append(slc_G2020.get_slc_G2020(H0, H, B0, B, A, c))
                if not flg_A20_cumul:
                    A20_hist.append(slc_A2020.get_slc_A2020(H0, H, B0, B, S0, S0, A, c))

        # ---- VAF and G2020 (always relative to reference state) ----
        for n in range(nt):
            H = lithk[n,:,:] * maxmask1 * gic_mask
            B = topg[n,:,:]
            VAF_list.append(slc_vaf.get_slc_vaf(H0, H, B0, B, S0, S0, A, c))
            G20_list.append(slc_G2020.get_slc_G2020(H0, H, B0, B, A, c))

        # ---- A2020 (method-dependent) ----
        if not flg_A20_cumul:
            # Relative to reference state at every timestep
            for n in range(nt):
                H = lithk[n,:,:] * maxmask1 * gic_mask
                B = topg[n,:,:]
                A20_list.append(slc_A2020.get_slc_A2020(H0, H, B0, B, S0, S0, A, c))

        else:
            # Mode 1: seamless hist+exp cumulative, offset to zero at t_ref
            lh = lithk if exp == hist else lithk_hist
            th = topg if exp == hist else topg_hist
            n_lh = nt if exp == hist else n_hist

            # Hist pre-pass: cumulate from hist[0] forward
            H_prev = lh[0,:,:] * maxmask1 * gic_mask
            B_prev = th[0,:,:]
            acc = 0.0
            hist_cumul = [0.0]
            for n_h in range(1, n_lh):
                H_h = lh[n_h,:,:] * maxmask1 * gic_mask
                B_h = th[n_h,:,:]
                acc += slc_A2020.get_slc_A2020(H_prev, H_h, B_prev, B_h, S0, S0, A, c)
                hist_cumul.append(acc)
                H_prev = H_h.copy()
                B_prev = B_h.copy()
            offset = hist_cumul[ref_idx]

            if exp == hist:
                A20_list = [v - offset for v in hist_cumul]
            else:
                # H_prev/B_prev are at hist[-1]; continue into exp
                raw_exp = []
                for n in range(nt):
                    H = lithk[n,:,:] * maxmask1 * gic_mask
                    B = topg[n,:,:]
                    acc += slc_A2020.get_slc_A2020(H_prev, H, B_prev, B, S0, S0, A, c)
                    raw_exp.append(acc)
                    H_prev = H.copy()
                    B_prev = B.copy()
                if ref_in_exp:
                    offset = raw_exp[ref_idx_exp]
                A20_list = [v - offset for v in raw_exp]
                if hist_n_out > 0:
                    A20_hist = [v - offset for v in hist_cumul[hist_start:]]

        sl_VAF = np.concatenate([VAF_hist, VAF_list])
        sl_G20 = np.concatenate([G20_hist, G20_list])
        sl_A20 = np.concatenate([A20_hist, A20_list])

        if verbose:
            print(sl_VAF)
            print(sl_G20)
            print(sl_A20)

        ###############################################
        # Write SLC NetCDF files

        for varname, long_name, sl_array in [
            ("slvaf", "Sea level contribution based on Vaf",   sl_VAF),
            ("slg20", "Sea level contribution based on G2020", sl_G20),
            ("sla20", "Sea level contribution based on A2020", sl_A20),
        ]:
            os.makedirs(ncpath, exist_ok=True)
            scfile = ncpath + "/" + varname + "_" + regionName + "_" + file_stem + ".nc"
            ds = nc.Dataset(scfile, 'w', format='NETCDF4')
            ds.createDimension('time', None)
            ds.description = file_description
            var_time = ds.createVariable('time',   'f8', ('time',), zlib=True)
            var_slc  = ds.createVariable(varname,  'f8', ('time',), zlib=True)
            var_time.units     = time_units
            var_time.long_name = time_long_name
            var_time.calendar  = time_calendar
            var_slc.long_name  = long_name
            var_slc.units      = 'm'
            var_time[:]  = time_out
            var_slc[:]   = sl_array[:]
            ds.close()
            print("Created file ", scfile)

        ###############################################
        # Write SLC CSV files (one per SLC method)

        csv_years = range(1850, 2301)
        meta = {
            "ice_source":    region,
            "region":        regionName,
            "group":         group,
            "model":         model,
            "model_variant": modelid,
            "scenario":      exp,
            "GCM":           esm,
            "forcingid":     forcingid,
            "configid":      configid,
        }
        meta_keys = list(meta.keys())
        header = meta_keys + [f"y{y}" for y in csv_years]

        os.makedirs(csvpath, exist_ok=True)
        out_of_range = [y for y in nominal_yrs if y not in csv_years]
        if out_of_range:
            print(f"Warning: {len(out_of_range)} year(s) outside CSV window {csv_years[0]}–{csv_years[-1]+1} "
                  f"will be dropped: {out_of_range[:5]}{'...' if len(out_of_range)>5 else ''}")
        for varname, sl_array in [("slvaf", sl_VAF), ("slg20", sl_G20), ("sla20", sl_A20)]:
            year_to_slc = dict(zip(nominal_yrs, sl_array))
            row = [meta[k] for k in meta_keys] + [
                year_to_slc[y] if y in year_to_slc else "NA" for y in csv_years
            ]
            csvfile = csvpath + "/" + varname + "_" + regionName + "_" + file_stem + ".csv"
            with open(csvfile, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(header)
                writer.writerow(row)
            print("Created file ", csvfile)

#############################################################
# ST scalar variables (no GIC masking, plain display name)

for regionName_raw, region_mask in vars(regions).items():
    regionName = region_display_name(regionName_raw, region)

    A = region_mask * af2 * (float(res)*1000.0)**2

    lim_hist, limnsw_hist, iareagr_hist, iareafl_hist = [], [], [], []
    lim_list, limnsw_list, iareagr_list, iareafl_list = [], [], [], []

    if hist_n_out > 0:
        for n in range(hist_start, n_hist):
            H = lithk_hist[n,:,:] * maxmask1
            B = topg_hist[n,:,:]
            hf = np.maximum(-B, 0) * c.RHOSW / c.RHOI
            lim_hist.append(np.sum(H * A) * c.RHOI)
            limnsw_hist.append(np.sum(np.maximum(H - hf, 0) * A) * c.RHOI)
            iareagr_hist.append(np.sum(sftgrf_hist[n,:,:] * A))
            iareafl_hist.append(np.sum(sftflf_hist[n,:,:] * A))

    for n in range(nt):
        H = lithk[n,:,:] * maxmask1
        B = topg[n,:,:]
        hf = np.maximum(-B, 0) * c.RHOSW / c.RHOI
        lim_list.append(np.sum(H * A) * c.RHOI)
        limnsw_list.append(np.sum(np.maximum(H - hf, 0) * A) * c.RHOI)
        iareagr_list.append(np.sum(sftgrf[n,:,:] * A))
        iareafl_list.append(np.sum(sftflf[n,:,:] * A))

    ST_SCALAR_SPECS = [
        ("lim",     "land_ice_mass",                          "kg", lim_hist,     lim_list),
        ("limnsw",  "land_ice_mass_not_displacing_sea_water", "kg", limnsw_hist,  limnsw_list),
        ("iareagr", "grounded_ice_sheet_area",                "m2", iareagr_hist, iareagr_list),
        ("iareafl", "floating_ice_shelf_area",                "m2", iareafl_hist, iareafl_list),
    ]
    for varname, long_name, units, hist_vals, exp_vals in ST_SCALAR_SPECS:
        data_out = np.concatenate([hist_vals, exp_vals])
        scfile = ncpath + "/" + varname + "_" + regionName + "_" + file_stem + ".nc"
        ds = nc.Dataset(scfile, 'w', format='NETCDF4')
        ds.createDimension('time', None)
        ds.description = file_description
        var_time = ds.createVariable('time',   'f8', ('time',), zlib=True)
        var_data = ds.createVariable(varname,  'f8', ('time',), zlib=True)
        var_time.units     = time_units
        var_time.long_name = time_long_name
        var_time.calendar  = time_calendar
        var_data.long_name = long_name
        var_data.units     = units
        var_time[:] = time_out
        var_data[:] = data_out
        ds.close()
        print("Created file ", scfile)

#############################################################
# FL scalar variables (one NC file per variable per region, no GIC masking)

for tendvarname, input_var, long_name, units in FL_SCALAR_SPECS:
    # Find exp FL file; skip variable if not found
    try:
        fl_exp_file = find_model_file(exppath, input_var, region, group, model, modelid, esm, forcingid, exp, configid)
    except FileNotFoundError:
        skipped_scalars.append(tendvarname)
        continue

    # Load exp FL data + time axis
    idat = nc.Dataset(fl_exp_file, 'r')
    fl_exp = idat.variables[input_var][:,:,:]
    fl_tv  = idat.variables['time']
    fl_time_exp       = fl_tv[:]
    fl_time_units     = fl_tv.units
    fl_time_calendar  = fl_tv.calendar
    fl_time_long_name = fl_tv.long_name
    idat.close()

    # Optionally load hist FL data for histout prepending
    fl_hist, fl_time_hist = None, None
    if hist_n_out > 0 and exp != hist:
        try:
            fl_hist_file = find_model_file(histpath, input_var, region, group, model, modelid, esm, forcingid, hist, configid)
            idat = nc.Dataset(fl_hist_file, 'r')
            fl_hist      = idat.variables[input_var][:,:,:]
            fl_time_hist = idat.variables['time'][:]
            idat.close()
        except FileNotFoundError:
            pass  # hist FL file missing; output exp period only

    # Build concatenated FL time axis (same histout logic as ST)
    n_fl_hist = len(fl_time_hist) if fl_time_hist is not None else 0
    if fl_hist is not None and hist_n_out > 0:
        fl_n_out = n_fl_hist if histout == -1 else min(hist_n_out, n_fl_hist)
        if fl_n_out < hist_n_out and histout != -1:
            print(f"Warning: FL hist file for {tendvarname} has {n_fl_hist} steps; "
                  f"requested {hist_n_out} via --histout — using {fl_n_out}")
        fl_hist_start = n_fl_hist - fl_n_out
        fl_time_out = np.concatenate([fl_time_hist[fl_hist_start:], fl_time_exp])
    else:
        fl_hist_start = n_fl_hist
        fl_time_out = fl_time_exp

    # FL nominal year (Jul 1 of year N → nominal year N; no -1 offset unlike ST)
    fl_dates = nc.num2date(fl_time_out, fl_time_units, calendar=fl_time_calendar)
    fl_y0 = fl_dates[0].year
    fl_y1 = fl_dates[-1].year
    fl_file_stem = (f"{region}_{group}_{model}_{modelid}_{esm}_{forcingid}"
                    f"_{exp}_{configid}_{fl_y0}-{fl_y1}")

    # Base area weight without GIC masking
    weight_base = af2 * (float(res) * 1000.0) ** 2

    for regionName_raw, region_mask in vars(regions).items():
        regionName = region_display_name(regionName_raw, region)
        W = region_mask * weight_base  # (ny, nx)
        exp_integral = np.einsum('nyx,yx->n', fl_exp, W)
        if fl_hist is not None and hist_n_out > 0:
            hist_integral = np.einsum('nyx,yx->n', fl_hist[fl_hist_start:], W)
            fl_integral = np.concatenate([hist_integral, exp_integral])
        else:
            fl_integral = exp_integral

        os.makedirs(ncpath, exist_ok=True)
        scfile = ncpath + "/" + tendvarname + "_" + regionName + "_" + fl_file_stem + ".nc"
        ds = nc.Dataset(scfile, 'w', format='NETCDF4')
        ds.createDimension('time', None)
        ds.description = file_description
        vt = ds.createVariable('time',      'f8', ('time',), zlib=True)
        vd = ds.createVariable(tendvarname, 'f8', ('time',), zlib=True)
        vt.units     = fl_time_units
        vt.long_name = fl_time_long_name
        vt.calendar  = fl_time_calendar
        vd.long_name = long_name
        vd.units     = units
        vt[:] = fl_time_out
        vd[:] = fl_integral
        ds.close()
        print("Created file ", scfile)

if skipped_scalars:
    print("\nSkipped scalars (input files not found):")
    for s in skipped_scalars:
        print(f"  {s}")
