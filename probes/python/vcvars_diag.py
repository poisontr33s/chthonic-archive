#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# @SID: P-XX_VCVARS_DIAG
# @Ankh: vcvars_diag # Diagnostic: verify vcvarsall env capture sets correct INCLUDE and PATH. Windows SDK 10.0.22621.0, MSVC v14.44.35207
# @GATE: C-GX — Diagnostic: verify vcvarsall env capture sets correct INCLUDE and PATH.
# @MANIFEST: manifest/vcvars_diag.json

"""Diagnostic: verify vcvarsall env capture sets correct INCLUDE and PATH."""

import subprocess, os, tempfile

VCVARSALL = r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat"
VCTOOLS_VER = "14.44.35207"

# Use temp batch file — avoids cmd.exe inner-quote nesting bug
bat_fd, bat_path = tempfile.mkstemp(suffix=".bat", prefix="vcvars_diag_")
try:
    with os.fdopen(bat_fd, "w") as f:
        f.write("@echo off\r\n")
        f.write(f"set VCToolsVersion={VCTOOLS_VER}\r\n")
        f.write(f'call "{VCVARSALL}" amd64 > NUL 2>&1\r\n')
        f.write("set\r\n")
    r = subprocess.run(["cmd.exe", "/c", bat_path], capture_output=True, text=True)
finally:
    try: os.unlink(bat_path)
    except OSError: pass

print("returncode:", r.returncode)
env = {}
for line in r.stdout.splitlines():
    if "=" in line:
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip()

print(f"vars captured: {len(env)}")
inc = env.get("INCLUDE", "NOT SET")
print(f"INCLUDE[:300]: {inc[:300]}")
path_entries = [p for p in env.get("PATH", "").split(";") if "MSVC" in p or "msvc" in p.lower()]
print("MSVC entries in PATH:")
for e in path_entries[:8]:
    print(" ", e)

# Also show first few PATH entries
first_path = env.get("PATH", "").split(";")[:6]
print("First PATH entries:")
for e in first_path:
    print(" ", e)

# Check case of PATH key
path_key = next((k for k in env if k.lower() == "path"), None)
print(f"PATH key in env: {path_key!r}")
if path_key:
    first_p = env[path_key].split(";")[:6]
    print("First PATH entries (via key):")
    for e in first_p:
        print(" ", e)
