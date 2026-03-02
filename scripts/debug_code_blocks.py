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
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


from pathlib import Path

path = Path(r'C:\Users\erdno\chthonic-archive\.github\copilot-instructions.md')
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
