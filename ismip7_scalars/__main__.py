"""Entry point for ``python -m ismip7_scalars``."""

from ismip7_scalars.scalars import main

if __name__ == '__main__':
    # The console script gets this for free from setuptools; without it here,
    # `python -m ismip7_scalars` would exit 0 on a skipped run.
    raise SystemExit(main())
