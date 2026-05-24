#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: ssot_immunity.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
🔐 SSOT HASH IMMUNITY PROTOCOL
═══════════════════════════════════════════════════════════════════════════════

Memory Immunity System for Single Source of Truth (SSOT) Files
Detects unauthorized mutations, provides drift alerts, maintains baseline.

Workflow:
  1. First run: Initialize baseline hashes for SSOT files
  2. Subsequent runs: Compare current hashes to baseline
  3. Drift detected: Log event + return alert payload
  4. No drift: Update baseline, return None

Usage:
    from ssot_immunity import check_ssot_drift
    drift = check_ssot_drift()
    if drift:
        print(f"DRIFT: {drift}")

State Files:
  - .dcrp_state.json: Baseline hash storage
  - logs/ssot_drift.log: Append-only drift event log

═══════════════════════════════════════════════════════════════════════════════

@SID:           TOOL_SSOT_IMMUNITY_V1
@Shabti:        CLI Script
@Purpose:       🔐 SSOT HASH IMMUNITY PROTOCOL
"""

from __future__ import annotations


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import hashlib
import json
import datetime
from typing import Dict, Optional, List

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))
from scripts.lib.ssot_paths import SSOT_POINTER

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

PROJECT_ROOT = _REPO_ROOT
STATE_PATH = Path(__file__).resolve().parent / ".dcrp_state.json"
LOG_PATH = Path(__file__).resolve().parent / "logs" / "ssot_drift.log"

# SSOT files to monitor
SSOT_FILES = [
    SSOT_POINTER,
    "ankh.md",
    "ANKHOLOGY.md",
    "ANKH_README.md",
    # Add additional SSOT files as needed
]

# ═══════════════════════════════════════════════════════════════════════════════
# HASH COMPUTATION
# ═══════════════════════════════════════════════════════════════════════════════

def compute_hash(path: Path) -> str:
    """
    Compute SHA-256 hash of file content.
    Uses raw bytes (no canonicalization) for simplicity.
    For production: add canonicalization (line endings, trailing whitespace, Unicode normalization).
    """
    if not path.exists():
        return "FILE_NOT_FOUND"

    try:
        h = hashlib.sha256()
        h.update(path.read_bytes())
        return h.hexdigest()
    except Exception as e:
        return f"ERROR:{str(e)[:50]}"

# ═══════════════════════════════════════════════════════════════════════════════
# STATE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def load_state() -> Dict:
    """Load state from .dcrp_state.json."""
    if not STATE_PATH.exists():
        return {"ssot_hashes": {}, "last_verified": None}

    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"ssot_hashes": {}, "last_verified": None}

def save_state(state: Dict) -> None:
    """Save state to .dcrp_state.json."""
    state["last_verified"] = datetime.datetime.now(datetime.UTC).isoformat()
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")

# ═══════════════════════════════════════════════════════════════════════════════
# DRIFT DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

def check_ssot_drift() -> Optional[Dict]:
    """
    Main drift detection function.

    Returns:
      - None if no drift detected
      - Dict with drift event details if drift found
    """
    state = load_state()
    baseline = state.get("ssot_hashes", {})
    drift_events: List[Dict] = []

    for rel_path in SSOT_FILES:
        abs_path = PROJECT_ROOT / rel_path
        current_hash = compute_hash(abs_path)
        expected_hash = baseline.get(rel_path)

        if expected_hash is None:
            # First-time initialization: record baseline
            baseline[rel_path] = current_hash
            print(f"🔐 SSOT Baseline initialized: {rel_path} → {current_hash[:16]}...")
        elif expected_hash != current_hash:
            # Drift detected
            drift_events.append({
                "file": rel_path,
                "expected": expected_hash,
                "actual": current_hash,
                "timestamp": datetime.datetime.now(datetime.UTC).isoformat()
            })
            print(f"⚠️  SSOT Drift detected: {rel_path}")
            print(f"   Expected: {expected_hash[:16]}...")
            print(f"   Actual:   {current_hash[:16]}...")

            # Update baseline to current (accept drift but log it)
            baseline[rel_path] = current_hash

    # Save updated baseline
    state["ssot_hashes"] = baseline
    save_state(state)

    if not drift_events:
        return None

    # Log drift events
    alert = {
        "severity": "HIGH",
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        "events": drift_events
    }

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(alert) + "\n")

    return alert

# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    """Standalone CLI for manual SSOT verification."""
    print("🔐 SSOT Hash Immunity Protocol")
    print("=" * 60)
    print("")

    drift = check_ssot_drift()

    if drift is None:
        print("")
        print("✅ No drift detected - all SSOT files match baseline")
    else:
        print("")
        print(f"⚠️  Drift detected in {len(drift['events'])} file(s)")
        print("")
        print("Drift events logged to:", LOG_PATH)
        print("")
        print("Details:")
        for event in drift["events"]:
            print(f"  - {event['file']}")
            print(f"    Expected: {event['expected'][:16]}...")
            print(f"    Actual:   {event['actual'][:16]}...")

if __name__ == "__main__":
    main()
