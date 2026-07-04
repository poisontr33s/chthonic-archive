#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""Probe 01 — environment baseline.

Reports the interpreter, build tags, GIL state, and the surface area
that matters for Cython + native deps. No network, no installs.

Run: uv run probes/probe_01_environment.py
"""
from __future__ import annotations

import os
import platform
import sys
import sysconfig


def main() -> int:
    print("=== Probe 01: environment baseline ===")
    print(f"sys.version          : {sys.version.splitlines()[0]}")
    print(f"sys.implementation   : {sys.implementation.name} {sys.implementation.version}")
    print(f"sys.platform         : {sys.platform}")
    print(f"platform.machine     : {platform.machine()}")
    print(f"platform.win32_ver   : {platform.win32_ver()}")
    print(f"sys.executable       : {sys.executable}")
    print(f"sys.prefix           : {sys.prefix}")
    print(f"sys.maxsize          : {sys.maxsize}")
    print(f"GIL disabled         : {getattr(sys, '_is_gil_enabled', lambda: True)() is False}")
    print(f"sysconfig EXT_SUFFIX : {sysconfig.get_config_var('EXT_SUFFIX')}")
    print(f"sysconfig SOABI      : {sysconfig.get_config_var('SOABI')}")
    print(f"sysconfig Py_GIL_DISABLED: {sysconfig.get_config_var('Py_GIL_DISABLED')}")
    print(f"sysconfig CC         : {sysconfig.get_config_var('CC')}")
    print(f"sysconfig prefix     : {sysconfig.get_config_var('prefix')}")
    print()
    print("=== Build context ===")
    for var in ("VCToolsInstallDir", "WindowsSDKVersion", "INCLUDE", "LIB"):
        val = os.environ.get(var)
        if val:
            print(f"  {var}: {val[:140]}")
        else:
            print(f"  {var}: (unset)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
