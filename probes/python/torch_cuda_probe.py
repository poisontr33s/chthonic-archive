#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SID: PROBE-P02-TORCH-CUDA-GATE
# Gate: torch/cuda_discovery
# FAF artifact type: probe
# Run: uv run --extra cu12 python probes/python/torch_cuda_probe.py
# Output: manifest/cuda_gate.jsonl (appended) + stdout (JSON)
import json
import os
import sys
import time

result = {
    "gate": "torch/cuda_discovery",
    "artifact_type": "probe",
    "python_version": sys.version,
    "python_version_info": {
        "major": sys.version_info.major,
        "minor": sys.version_info.minor,
        "micro": sys.version_info.micro,
    },
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}

try:
    import torch  # noqa: PLC0415

    result["torch_version"] = torch.__version__
    result["cuda_version"] = torch.version.cuda
    result["cuda_available"] = torch.cuda.is_available()
    result["device_count"] = torch.cuda.device_count() if torch.cuda.is_available() else 0

    if torch.cuda.is_available() and torch.cuda.device_count() > 0:
        result["device_name"] = torch.cuda.get_device_name(0)
        result["device_capability"] = list(torch.cuda.get_device_capability(0))
        result["level"] = "L4_useful"
        result["status"] = "admitted"
    elif torch.cuda.is_available():
        result["level"] = "L2_interrogable_no_device"
        result["status"] = "probe_incomplete"
        result["note"] = "CUDA available but device_count=0"
    else:
        result["level"] = "L1_loadable_cuda_absent"
        result["status"] = "probe_incomplete"
        result["note"] = "torch loaded; CUDA not available (driver/runtime gate)"
        result["next_gate"] = "cuda_driver_runtime_compatibility"

except ImportError as exc:
    result["level"] = "L0_or_L1_blocked"
    result["status"] = "blocked_not_closed"
    result["error"] = str(exc)
    result["minimum_condition_to_reopen"] = "cp314 torch wheel present in pytorch-cu128 index"
    result["upstream_dependency"] = "pytorch/pytorch release with cp314 wheel"
    result["next_probe"] = "torch_cuda_device_interrogation_probe"

output = json.dumps(result, indent=2)
print(output)

manifest_dir = os.path.join(os.path.dirname(__file__), "..", "..", "manifest")
os.makedirs(manifest_dir, exist_ok=True)
ledger_path = os.path.join(manifest_dir, "cuda_gate.jsonl")
with open(ledger_path, "a", encoding="utf-8") as f:
    f.write(json.dumps(result) + "\n")

print(f"\n[P-02] Appended: {os.path.abspath(ledger_path)}", file=sys.stderr)
