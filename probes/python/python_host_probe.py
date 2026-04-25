#!/usr/bin/env python3
#-*- coding: utf-8 -*-
# SID: PROBE-P01-PYTHON-HOST-IDENTITY
# Gate: host/python_identity
# FAF artifact type: probe
# Run: uv run python probes/python/python_host_probe.py
# Output: manifest/python_host.json (written) + stdout (JSON)
import json
import os
import platform
import sys

host = {
    "gate": "host/python_identity",
    "python_version": sys.version,
    "python_implementation": platform.python_implementation(),
    "python_version_info": {
        "major": sys.version_info.major,
        "minor": sys.version_info.minor,
        "micro": sys.version_info.micro,
        "releaselevel": sys.version_info.releaselevel,
    },
    "platform": platform.platform(),
    "system": platform.system(),
    "machine": platform.machine(),
    "processor": platform.processor(),
    "python_path": sys.executable,
    "prefix": sys.prefix,
    "level": "L4_useful",
    "status": "admitted",
}

output = json.dumps(host, indent=2)
print(output)

manifest_dir = os.path.join(os.path.dirname(__file__), "..", "..", "manifest")
os.makedirs(manifest_dir, exist_ok=True)
manifest_path = os.path.join(manifest_dir, "python_host.json")
with open(manifest_path, "w", encoding="utf-8") as f:
    f.write(output + "\n")

print(f"\n[P-01] Written: {os.path.abspath(manifest_path)}", file=sys.stderr)
