#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: run_narrative_scan.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
@SID: RUN_NARRATIVE_SCAN_V1
@Shabti: Utility Script
@Context: Standalone Narrative Scan Runner
@Purpose:       Script logic for run_narrative_scan.py.
"""


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import sys
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

# Import logic directly to avoid server overhead
from mas_mcp.logic.tools import mas_narrative_scan_logic
from scripts.lib.ssot_paths import resolve_ssot_paths

_SSOT = resolve_ssot_paths(PROJECT_ROOT)
SSOT_PATH = _SSOT.pointer

def main():
    results = mas_narrative_scan_logic(".", PROJECT_ROOT, SSOT_PATH)
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
