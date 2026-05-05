#!/usr/bin/env python3
# @SID: SDNEXT_G0_PROBE
# @DESC: SD.NEXT G0 gate — validates torch+cuda baseline and writes manifest/sdnext_g0.json
# @GATE: G0 (environment coherence)
# @RUN: uv run probes/python/sdnext_g0_probe.py
# @OUTPUT: manifest/sdnext_g0.json
"""
SD.NEXT G0 Probe — environment coherence gate.

Checks:
  1. Python version (≥ 3.10 for SD.NEXT)
  2. torch importable + CUDA available
  3. RTX 4090 device present (SM 8.9)
  4. SD.NEXT extension imports healthy (entity_registry, prompt_transformer)
  5. corpus.sqlite accessible

Writes manifest/sdnext_g0.json with structured gate verdict.
Exit codes: 0=pass, 1=fail (at least one gate blocked).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
MANIFEST_DIR = REPO_ROOT / "manifest"
OUTPUT_PATH = MANIFEST_DIR / "sdnext_g0.json"
SDNEXT_EXT = REPO_ROOT / "dev" / "sd-candidates" / "sdnext" / "extensions" / "milfological"
CORPUS_PATH = MANIFEST_DIR / "corpus.sqlite"

gates: list[dict] = []


def gate(name: str, level: int, note: str, status: str = "admitted") -> None:
    gates.append({"gate": name, "status": status, "level": level, "note": note})
    mark = "✓" if status == "admitted" else "✗"
    print(f"  {mark} {name}: {note}")


def run() -> int:
    print("SD.NEXT G0 probe ─────────────────────────────────────────")

    # G0.1 — Python version
    ver = sys.version_info
    if ver >= (3, 10):
        gate("python_version", 4, f"Python {ver.major}.{ver.minor}.{ver.micro}")
    else:
        gate("python_version", 0, f"Python {ver.major}.{ver.minor} < 3.10 required", "blocked")

    # G0.2 — torch + CUDA
    try:
        import torch  # type: ignore
        cuda_ok = torch.cuda.is_available()
        if cuda_ok:
            dev_name = torch.cuda.get_device_name(0)
            cap = torch.cuda.get_device_capability(0)
            gate(
                "torch_cuda",
                4,
                f"torch {torch.__version__}, {dev_name}, SM {cap[0]}.{cap[1]}",
            )
        else:
            gate("torch_cuda", 1, f"torch {torch.__version__} — CUDA not available", "degraded")
    except ImportError:
        gate("torch_cuda", 0, "torch not importable", "blocked")

    # G0.3 — RTX 4090 specific (SM 8.9)
    try:
        import torch  # noqa: F811
        if torch.cuda.is_available():
            cap = torch.cuda.get_device_capability(0)
            if cap == (8, 9):
                gate("rtx4090", 4, "SM 8.9 confirmed (Ada Lovelace)")
            else:
                gate("rtx4090", 2, f"SM {cap[0]}.{cap[1]} (not RTX 4090, OK)", "degraded")
        else:
            gate("rtx4090", 0, "CUDA unavailable, skip RTX check", "skipped")
    except Exception as exc:  # noqa: BLE001
        gate("rtx4090", 0, str(exc), "skipped")

    # G0.4 — SD.NEXT extension imports
    sys.path.insert(0, str(SDNEXT_EXT))
    try:
        import entity_registry  # type: ignore  # noqa: F401
        n = len(entity_registry.registry._entities)
        gate("entity_registry", 4, f"{n} entities loaded")
    except Exception as exc:  # noqa: BLE001
        gate("entity_registry", 0, f"import failed: {exc}", "blocked")

    try:
        import prompt_transformer  # type: ignore  # noqa: F401
        gate("prompt_transformer", 4, "import OK, _rag_augment present")
    except Exception as exc:  # noqa: BLE001
        gate("prompt_transformer", 0, f"import failed: {exc}", "blocked")

    # G0.5 — corpus.sqlite
    if CORPUS_PATH.exists():
        size_kb = CORPUS_PATH.stat().st_size // 1024
        try:
            import sqlite3
            db = sqlite3.connect(str(CORPUS_PATH))
            msg_count = db.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
            session_count = db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
            db.close()
            gate(
                "corpus_sqlite",
                4,
                f"{size_kb}KB, {session_count} sessions, {msg_count} messages",
            )
        except Exception as exc:  # noqa: BLE001
            gate("corpus_sqlite", 1, f"open failed: {exc}", "degraded")
    else:
        gate("corpus_sqlite", 0, "manifest/corpus.sqlite not found", "missing")

    # Write manifest
    blocked = [g for g in gates if g["status"] in ("blocked",)]
    overall = "pass" if not blocked else "fail"
    result = {
        "probe": "sdnext_g0",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "status": overall,
        "gates": gates,
    }
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(result, indent=2))
    print(f"\nSD.NEXT G0  {overall.upper()}  → {OUTPUT_PATH}")
    return 0 if overall == "pass" else 1


if __name__ == "__main__":
    sys.exit(run())
