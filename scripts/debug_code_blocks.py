#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: debug_code_blocks.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""Debug Code Blocks - Utility to check for balanced code block delimiters in markdown files

@SID:           TOOL_DEBUG_CODE_BLOCKS_V1
@Shabti:        CLI Script
@Purpose:       Debug Code Blocks - Utility to check for balanced code block delimiters in markdown files
"""


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))
from scripts.lib.ssot_paths import resolve_ssot_paths

_SSOT = resolve_ssot_paths(_REPO_ROOT)
path = _SSOT.pointer
lines = path.read_text(encoding='utf-8').split('\n')

count = 0
for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped.startswith('```') or stripped.startswith('~~~'):
        count += 1
        print(f"Line {i+1}: {stripped} (Count: {count})")

if count % 2 != 0:
    print(f"WARNING: Odd number of code block delimiters found: {count}")
else:
    print(f"Total delimiters: {count} (Even)")
