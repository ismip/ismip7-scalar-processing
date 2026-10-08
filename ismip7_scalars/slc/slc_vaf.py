# Calculate sea-level contribution using volume above floatation
# Following ISMIP6: https://doi.org/10.5194/tc-14-3071-2020; https://doi.org/10.1029/2024EF004561; https://zenodo.org/records/10528582
# Converting Vaf directly to freshwater
# Suffix 0 refers to reference state.

import numpy as np

# Pass constants c as arguments to functions c.RHOI, c.RHOSW, c.RHOFW, c.AO
# typical values
# c.RHOI  = 917.0 #kg/m3
# c.RHOSW = 1027.0 #kg/m3
# c.RHOFW = 1.0e3 #kg/m3
# c.AO = 3.625e14 # m2 (Gregory et al., 2019)

# Vaf assuming B (and S) in an absolute reference frame like in A2020
#
# B may be the bed or the ice base.  At a point the two give the same Vaf:
# they are equal under grounded ice, and Vaf is zero under floating ice and
# open water either way.  They differ once H and B are cell means.  With the
# bed, a cell that is part grounded and part floating counts the water under
# its shelf against its grounded ice, so Vaf falls as the shelf thins.  With
# the ice base (sea level over open water), Vaf is H + B*RHOSW/RHOI wherever
# B is below sea level, which is linear, so its cell mean is exact.  The
# processing therefore passes the ice base.
def get_vaf(H,B,S,A,c):
  hf  = np.maximum(S-B,0.0)*c.RHOSW/c.RHOI
  hall= np.maximum(H-hf,0.0)
  vol = np.sum(hall*A)
  return vol

def get_slc_vaf(H0,H,B0,B,S0,S,A,c):
  # ISMIP6: Converting Vaf directly to freshwater
  sle_af_ref = get_vaf(H0,B0,S0,A,c) / c.AO * c.RHOI/c.RHOFW
  sle_af = get_vaf(H,B,S,A,c) / c.AO * c.RHOI/c.RHOFW
  slc_af = -(sle_af - sle_af_ref)
  return slc_af 


# Vaf assuming B is given relative to sea level at that time or S=0 
def get_vaf_HBA(H,B,A,c):
  hf  = np.maximum(-B,0.0)*c.RHOSW/c.RHOI
  hall= np.maximum(H-hf,0.0)
  vol = np.sum(hall*A)
  return vol

def get_slc_vaf_HBA(H0,H,B0,B,A,c):
  # ISMIP6: Converting Vaf directly to freshwater
  sle_af_ref = get_vaf_HBA(H0,B0,A,c) / c.AO * c.RHOI/c.RHOFW
  sle_af = get_vaf_HBA(H,B,A,c) / c.AO * c.RHOI/c.RHOFW
  slc_af = -(sle_af - sle_af_ref)
  return slc_af 


# Grounded ice volume change 
def get_vgr(H,B,S,A,c):
    mask_gr = H > (S-B)*c.RHOSW/c.RHOI
    vol = np.sum((H*A)[ mask_gr ])
    return vol

def get_slc_vgr(H0,H,B0,B,S0,S,A,c):
  sle_gr_ref = get_vgr(H0,B0,S0,A,c) / c.AO * c.RHOI/c.RHOFW
  sle_gr = get_vgr(H,B,S,A,c) / c.AO * c.RHOI/c.RHOFW
  slc_gr = -(sle_gr - sle_gr_ref)
  return slc_gr

# Floating ice volume change 
def get_vfl(H,B,S,A,c):
    mask_fl = H <= (S-B)*c.RHOSW/c.RHOI
    vol = np.sum((H*A)[ mask_fl ])
    return vol

def get_slc_vfl(H0,H,B0,B,S0,S,A,c):
  sle_fl_ref = get_vfl(H0,B0,S0,A,c) / c.AO * c.RHOI/c.RHOFW
  sle_fl = get_vfl(H,B,S,A,c) / c.AO * c.RHOI/c.RHOFW
  slc_fl = -(sle_fl - sle_fl_ref)
  return slc_fl


# Total ice volume change 
def get_vtot(H,A):
    vol = np.sum(H*A)
    return vol

def get_slc_vtot(H0,H,A,c):
  sle_tot_ref = get_vtot(H0,A) / c.AO * c.RHOI/c.RHOFW
  sle_tot = get_vtot(H,A) / c.AO * c.RHOI/c.RHOFW
  slc_tot = -(sle_tot - sle_tot_ref) 
  return slc_tot


# For global mean sea-level calculations 
def get_mean(R,A):
    mean = np.sum(R*A)
    return mean

def get_mean_diff(R0,R,A,Atot):
  mean_ref = get_mean(R0,A) / Atot 
  mean = get_mean(R,A) / Atot
  mean_diff = mean - mean_ref
  return mean_diff
