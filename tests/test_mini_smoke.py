"""
Smoke test for the MINI test suite.

Runs scalars_MINI.py for all four combinations (MINI0/MINI1 × exp0/expg) and
checks that output files are created with non-trivial SLC values.

MINI input files are tracked in test-data/ so this test runs without any
external data or symlinks.

Run with:  pytest tests/
"""
import subprocess
import sys
import os
import pytest
import netCDF4 as nc
import numpy as np

REPO_ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MINI_DIR    = os.path.join(REPO_ROOT, 'manual-tests', 'MINI')
TEST_DATA   = os.path.join(REPO_ROOT, 'test-data')


@pytest.mark.parametrize("model,exp", [
    ("MINI1", "exp0"),
    ("MINI1", "expg"),
    ("MINI0", "exp0"),
    ("MINI0", "expg"),
])
def test_mini_run(model, exp, tmp_path):
    """Run scalars_MINI.py and verify output file is created with non-zero VAF."""
    outpath   = str(tmp_path)
    datapath  = os.path.join(TEST_DATA, 'Data',   model)
    modelpath = os.path.join(TEST_DATA, 'Models', 'MINI', 'ISMIP7', model)
    result = subprocess.run(
        [sys.executable, 'scalars_MINI.py', '--model', model, '--exp', exp,
         '--outpath',   outpath,
         '--datapath',  datapath,
         '--modelpath', modelpath],
        capture_output=True, text=True, cwd=MINI_DIR
    )
    assert result.returncode == 0, (
        f"scalars_MINI.py {model}/{exp} failed:\n{result.stderr}"
    )

    outfile = os.path.join(outpath, f'scalars_mm_AIS_ISMIP7_{model}_{exp}.nc')
    assert os.path.exists(outfile), f"Output file not created: {outfile}"

    ds  = nc.Dataset(outfile, 'r')
    vaf = np.array(ds.variables['slc_VAF'][:])
    g20 = np.array(ds.variables['slc_G2020'][:])
    a20 = np.array(ds.variables['slc_A2020'][:])
    ds.close()

    assert len(vaf) > 0, "slc_VAF is empty"
    # First timestep == reference → VAF[0] must be 0
    assert abs(float(vaf[0])) < 1e-12, f"VAF[0] not zero: {vaf[0]}"
    # Final timestep non-trivially different from zero (ice changes over the run)
    assert abs(float(vaf[-1])) > 1e-9, f"VAF[-1] unexpectedly zero: {vaf[-1]}"
    # All three methods should agree in sign at the last timestep
    if abs(float(vaf[-1])) > 1e-9:
        sign_vaf = np.sign(vaf[-1])
        assert np.sign(g20[-1]) == sign_vaf, "G2020 sign differs from VAF at last timestep"
        assert np.sign(a20[-1]) == sign_vaf, "A2020 sign differs from VAF at last timestep"
