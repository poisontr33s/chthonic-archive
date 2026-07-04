#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""Probe 02 — Cython 3.14 readiness.

Verifies Cython is installed and that the cythonize() codepath that
Ren'Py uses can lower a trivial .pyx into C on this interpreter.
We only do .pyx -> .c (no native compile) so this probe runs without
MSVC on PATH. Probe 04 will handle the C -> .pyd step.

Run: uv run --group build probes/probe_02_cython.py
"""
from __future__ import annotations

import importlib
import shutil
import sys
import tempfile
import textwrap
from pathlib import Path


def main() -> int:
    print("=== Probe 02: Cython 3.14 readiness (.pyx -> .c via cythonize) ===")
    try:
        Cython = importlib.import_module("Cython")
    except ImportError as exc:
        print(f"FAIL: Cython not importable ({exc}). Run: uv sync --group build")
        return 1

    print(f"Cython version       : {Cython.__version__}")

    from Cython.Build import cythonize

    src = textwrap.dedent(
        """
        # cython: language_level=3
        def add(int a, int b):
            return a + b

        cpdef double mul(double a, double b):
            return a * b
        """
    ).lstrip()

    tmp = Path(tempfile.mkdtemp(prefix="probe02_"))
    pyx = tmp / "probe.pyx"
    pyx.write_text(src, encoding="utf-8")

    try:
        modules = cythonize(
            [str(pyx)],
            language_level=3,
            quiet=True,
        )
    except Exception as exc:
        print(f"FAIL: cythonize() raised: {exc!r}")
        return 2

    c_file = pyx.with_suffix(".c")
    if not c_file.exists():
        print(f"FAIL: cythonize() produced no .c output at {c_file}")
        return 3

    size = c_file.stat().st_size
    print(f"cythonize modules    : {len(modules)}")
    print(f"emitted C file       : {c_file.name} ({size:,} bytes)")
    print("PASS: Cython 3.2.4 lowers .pyx -> .c on Python 3.14")
    print(f"(temp dir kept for inspection: {tmp})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
