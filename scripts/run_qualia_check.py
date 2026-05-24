#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: run_qualia_check.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
@SID: RUN_QUALIA_CHECK_V1
@Shabti: Utility Script
@Context: Standalone Qualia Check Runner
@Purpose:       Script logic for run_qualia_check.py.
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

# Import logic directly
from mas_mcp.logic.tools import mas_qualia_check_logic

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "mas_mcp"
    results = mas_qualia_check_logic(target, PROJECT_ROOT)
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
