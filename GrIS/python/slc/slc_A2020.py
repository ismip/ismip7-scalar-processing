# Calculate sea-level contribution according to A2020
# Adhikari et al., TC 2020, https://doi.org/10.5194/tc-14-2819-2020
# Symbols are the same as in the paper.
# Suffix 0 refers to reference state.
# H0 in eq 7 is called Hn here to avoid confusion with the reference symbols.
# Absolute reference frame with B and S relative to same reference ellipsoid

import numpy as np

# Pass constants c as arguments to functions c.RHOI, c.RHOSW, c.RHOFW, c.AO
# typical values
# c.RHOI  = 917.0 #kg/m3
# c.RHOSW = 1027.0 #kg/m3
# c.RHOFW = 1.0e3 #kg/m3
# c.AO = 3.625e14 # m2 (Gregory et al., 2019)

def get_masks_A2020(H,B,S,c):
  # Calculate binary ice cover and grounded ice mask

  # eq. 1
  F = H - c.RHOSW/c.RHOI * (S-B) 
  # eq. 5: O = ocean/floating
  O  = np.zeros_like(H)
  O[F<0] = 1 
  # text after eq. 5: L = land/grounded ice
  L = 1-O 
  # eq. 6: I = ice (grounded or floating)
  I = np.zeros_like(H)
  I[H>0] = 1
  # text after eq. 6: G = grounded ice
  G = I*L 
  
  return (I,L,G)


def get_slc_A2020(H0,H,B0,B,S0,S,A,c):

  I0,L0,G0 = get_masks_A2020(H0,B0,S0,c)
  I,L,G = get_masks_A2020(H,B,S,c)

  # eq. 7
  Hn = c.RHOSW/c.RHOI*np.maximum(S-B,0)
  Hn0 = c.RHOSW/c.RHOI*np.maximum(S0-B0,0)
  # eq. 8
  HF = G*(H - Hn)
  HF0 = G0*(H0 - Hn0)
  # eq. 11
  HM = (H-H0)*L0*L + (HF-HF0)*(1-L0*L) 
  # eq. 12
  HV = (1-c.RHOFW/c.RHOSW)*((H-H0)-(HF-HF0))*(1-L0*L) 
  # eq. 10
  HS = HM + HV
  # last paragraph before Sec. 3.3
  slc = -c.RHOI/c.RHOFW * np.sum(HS*A)/c.AO

  return slc


def get_slc_A2020_with_masks(H0,H,B0,B,S0,S,L0,L,G0,G,A,c):

  Hn = c.RHOSW/c.RHOI*np.maximum(S-B,0)
  Hn0 = c.RHOSW/c.RHOI*np.maximum(S0-B0,0)
  # eq. 8
  HF = G*(H - Hn)
  HF0 = G0*(H0 - Hn0)
  # eq. 11
  HM = (H-H0)*L0*L + (HF-HF0)*(1-L0*L) 
  # eq. 12
  HV = (1-c.RHOFW/c.RHOSW)*((H-H0)-(HF-HF0))*(1-L0*L) 
  # eq. 10
  HS = HM + HV
  # last paragraph before Sec. 3.3
  slc = -c.RHOI/c.RHOFW * np.sum(HS*A)/c.AO

  return slc
