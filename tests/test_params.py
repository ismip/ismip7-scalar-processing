"""Tests for the ``params.nc`` writer."""

from __future__ import annotations

import os

import netCDF4 as nc
import pytest

from ismip7_scalars.params import main, write_params
from ismip7_scalars.scalars import OCEAN_AREA


class TestWriteParams:
    def test_defaults(self, tmp_path):
        path = write_params(str(tmp_path / 'params.nc'))
        with nc.Dataset(path) as ds:
            assert float(ds.variables['rhoi'][()]) == 917.0
            assert float(ds.variables['rhow'][()]) == 1027.0
            assert float(ds.variables['rhof'][()]) == 1000.0
            assert float(ds.variables['oarea'][()]) == OCEAN_AREA

    def test_overrides(self, tmp_path):
        path = write_params(str(tmp_path / 'params.nc'), rhoi=910.0,
                            rhow=1028.0, rhof=1000.0)
        with nc.Dataset(path) as ds:
            assert float(ds.variables['rhoi'][()]) == 910.0
            assert float(ds.variables['rhow'][()]) == 1028.0

    def test_written_as_double(self, tmp_path):
        """The old NCO-written file stored float32, losing digits of a density.

        The processing multiplies every cell by these, so the file that
        carries them should not be the place precision is thrown away.
        """
        path = write_params(str(tmp_path / 'params.nc'), rhoi=917.35)
        with nc.Dataset(path) as ds:
            assert ds.variables['rhoi'].dtype.kind == 'f'
            assert float(ds.variables['rhoi'][()]) == 917.35

    def test_creates_missing_directories(self, tmp_path):
        path = write_params(str(tmp_path / 'a' / 'b' / 'params.nc'))
        assert os.path.exists(path)

    def test_variables_carry_units(self, tmp_path):
        path = write_params(str(tmp_path / 'params.nc'))
        with nc.Dataset(path) as ds:
            for name in ('rhoi', 'rhow', 'rhof'):
                assert ds.variables[name].units == 'kg m-3'


class TestMain:
    def test_writes_into_the_model_tree(self, tmp_path):
        rc = main(['--region', 'AIS', '--group', 'VUW', '--model', 'PISM1',
                   '--rhoi', '910', '--modelpath', str(tmp_path)])
        assert rc == 0
        path = tmp_path / 'VUW' / 'PISM1' / 'params.nc'
        assert path.exists()
        with nc.Dataset(str(path)) as ds:
            assert float(ds.variables['rhoi'][()]) == 910.0

    def test_region_is_required(self):
        with pytest.raises(SystemExit):
            main(['--group', 'VUW', '--model', 'PISM1'])
