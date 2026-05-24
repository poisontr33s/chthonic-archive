#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: strip_broken_headers.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
strip_broken_headers.py — Script logic for strip_broken_headers.py.

@SID:           TOOL_STRIP_BROKEN_HEADERS_V1
@Shabti:        CLI Script
@Purpose:       Script logic for strip_broken_headers.py.
"""


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import re
from pathlib import Path

def strip_blessing(path):
    content = path.read_text(encoding='utf-8')
    # Match the entire header block including the broken parts
    # We look for the start and end of the box
    pattern = re.compile(r'# ╔═+╗\n.*?# ╚═+╝\n\n', re.DOTALL)
    new_content = pattern.sub('', content)
    if new_content != content:
        print(f"Stripped header from {path}")
        path.write_text(new_content, encoding='utf-8')

def main():
    root = Path('.')
    for path in root.rglob('*.py'):
        if 'node_modules' in path.parts or '.venv' in path.parts:
            continue
        strip_blessing(path)

if __name__ == "__main__":
    main()
