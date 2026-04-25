"""
P-05 — flash_attn source build probe
Records the Gate 6 source build attempt result for the FAF ledger.
Executed: 2026-04-25 via:
  $env:CUDA_HOME = 'C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v12.8'
  uv pip install --python dev/tabbyAPI/.venv/Scripts/python.exe flash-attn==2.8.3 --no-build-isolation
"""
import json
import sys
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

MANIFEST = Path(__file__).parent.parent.parent / "manifest" / "flash_attn_build_probe.json"
MANIFEST.parent.mkdir(parents=True, exist_ok=True)

# Verify MSVC version present in environment
msvc_root = r"C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Tools\MSVC"
msvc_versions = []
if os.path.isdir(msvc_root):
    msvc_versions = sorted(os.listdir(msvc_root))

cuda_home = os.environ.get("CUDA_HOME", "not_set")

result = {
    "gate": "flash_attn/source_build_attempt",
    "artifact_type": "probe",
    "probe_id": "P-05",
    "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "python_version": sys.version,
    "target_package": "flash-attn==2.8.3",
    "build_mode": "--no-build-isolation",
    "cuda_home": cuda_home,
    "msvc_versions_found": msvc_versions,
    "nvcc_path": r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\bin\nvcc.exe",
    "failure_mode_1": {
        "location": "crt/host_config.h(170)",
        "error": "fatal error C1189: -- unsupported Microsoft Visual Studio version! Only the versions between 2017 and 2022 (inclusive) are supported!",
        "installed_msvc": msvc_versions[-1] if msvc_versions else "unknown",
        "cuda_12_8_max_msvc": "14.40.x (VS 2022)",
        "installed_msvc_series": "14.51.x (VS BuildTools 2027 / MSVC 19.51)",
        "verdict": "MSVC 14.51 exceeds CUDA 12.8 host_config.h ceiling of 14.40"
    },
    "failure_mode_2": {
        "location": "cutlass/exmy_base.h(404)",
        "error": "error C2039: 'is_unsigned_v': is not a member of 'cutlass::platform'",
        "verdict": "flash_attn 2.8.3 bundled CUTLASS headers incompatible with MSVC 18 STL port"
    },
    "build_result": "FAILED",
    "level": "L0_blocked",
    "status": "source_build_blocked_msvc_ceiling",
    "remediation_paths": [
        "Install VS 2022 BuildTools (MSVC 14.4x) alongside VS 2027; set VCToolsVersion/VCToolsInstallDir to target 14.4x for nvcc",
        "Wait for kingbri1/flash-attention cp314-cp314-win_amd64 pre-built wheel",
        "Wait for flash_attn maintainer to support MSVC 18 / update CUTLASS headers"
    ]
}

MANIFEST.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
