#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Compatibility entrypoint.

This repository was refactored into a package under the `rewifi/` folder.
Keep `python rewifi.py ...` working by delegating to `rewifi.cli.main`.
"""

from __future__ import annotations

import sys

from rewifi.cli import main


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
