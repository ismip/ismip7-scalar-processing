"""Write the ``params.nc`` file that carries a model's density parameters.

Every model directory needs one, because the sea-level methods convert ice
volume to a water-equivalent depth and the answer depends on which densities
the model itself used.  Guessing them would put a systematic error into the
comparison, so the file is required rather than defaulted.

This replaces the ``tools/set_params.sh`` script of earlier versions, which
needed NCO on the path; nothing here needs anything the package does not
already depend on.
"""

from __future__ import annotations

import argparse
import os

import netCDF4 as nc

from ismip7_scalars import __version__
from ismip7_scalars.scalars import OCEAN_AREA

#: Densities assumed when a model does not state its own, in kg/m3.
DEFAULT_RHOI = 917.0   # ice
DEFAULT_RHOW = 1027.0  # ocean water
DEFAULT_RHOF = 1000.0  # fresh water

PARAM_ATTRS = {
    'rhoi': ('ice density', 'kg m-3'),
    'rhow': ('ocean water density', 'kg m-3'),
    'rhof': ('fresh water density', 'kg m-3'),
    'oarea': ('ocean area used for sea-level equivalent', 'm2'),
}


def write_params(path, rhoi=DEFAULT_RHOI, rhow=DEFAULT_RHOW,
                 rhof=DEFAULT_RHOF, oarea=OCEAN_AREA):
    """Write one ``params.nc``, creating its directory.  Returns the path.

    ``oarea`` is recorded for reference only: the processing normalises every
    submission by the same ocean area so that results stay comparable, and
    does not read this value back.
    """
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    values = {'rhoi': rhoi, 'rhow': rhow, 'rhof': rhof, 'oarea': oarea}
    with nc.Dataset(path, 'w', format='NETCDF4') as ds:
        ds.description = ('ISMIP7 model parameters, written by '
                          f'ismip7-scalars-set-params {__version__}')
        for name, value in values.items():
            var = ds.createVariable(name, 'f8')
            long_name, units = PARAM_ATTRS[name]
            var.long_name = long_name
            var.units = units
            var[()] = float(value)
    return path


def build_parser():
    """The ``ismip7-scalars-set-params`` command line."""
    parser = argparse.ArgumentParser(
        prog='ismip7-scalars-set-params',
        description='Create the params.nc file for one ISMIP7 model')
    parser.add_argument('--version', action='version',
                        version=f'ismip7-scalars-set-params {__version__}')
    parser.add_argument('--region', required=True, choices=['AIS', 'GrIS'],
                        help='Ice sheet region')
    parser.add_argument('--group', required=True,
                        help='Submitting group/lab (e.g. NORCE)')
    parser.add_argument('--model', required=True,
                        help='Ice sheet model name (e.g. PISM1)')
    parser.add_argument('--rhoi', type=float, default=DEFAULT_RHOI,
                        help=f'Ice density in kg/m3 (default: {DEFAULT_RHOI})')
    parser.add_argument('--rhow', type=float, default=DEFAULT_RHOW,
                        help=f'Ocean water density in kg/m3 '
                             f'(default: {DEFAULT_RHOW})')
    parser.add_argument('--rhof', type=float, default=DEFAULT_RHOF,
                        help=f'Fresh water density in kg/m3 '
                             f'(default: {DEFAULT_RHOF})')
    parser.add_argument('--modelpath', default=None,
                        help='Root for model output of one region; params.nc '
                             'is written to <modelpath>/<group>/<model>/ '
                             '(default: ./Models/<region>)')
    return parser


def main(argv=None):
    """``ismip7-scalars-set-params`` entry point."""
    args = build_parser().parse_args(argv)
    modelpath = args.modelpath or os.path.join(os.getcwd(), 'Models',
                                               args.region)
    path = os.path.join(modelpath, args.group, args.model, 'params.nc')
    write_params(path, rhoi=args.rhoi, rhow=args.rhow, rhof=args.rhof)
    print(f'Written: {path}  '
          f'(rhoi={args.rhoi}, rhow={args.rhow}, rhof={args.rhof})')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
