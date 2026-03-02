#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: patch_utf8.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
patch_utf8.py — Script logic for patch_utf8.py.

@SID:           TOOL_PATCH_UTF8_V1
@Shabti:        CLI Script
@Purpose:       Script logic for patch_utf8.py.
"""

import os
import re
from pathlib import Path

UTF8_FIX = """import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
"""

def patch_python_file(path):
    content = path.read_text(encoding='utf-8')
    if "sys.stdout = io.TextIOWrapper" in content:
        return

    # Find where to insert. After imports or at top.
    # If shebang exists, insert after shebang and docstring.
    if "import sys" not in content:
        # Patch at top or after shebang
        lines = content.split('\n')
        insert_idx = 0
        if lines[0].startswith('#!'):
            insert_idx = 1

        # If there's a docstring at the top, insert after it
        match = re.search(r'"""(.*?)"""', content, re.DOTALL)
        if match and match.start() < 100: # docstring near top
            insert_idx = content.find('"""', match.start() + 3) + 3
            # We want to insert after the newline following the docstring
            newline_idx = content.find('\n', insert_idx)
            if newline_idx != -1:
                insert_idx = newline_idx + 1

        new_content = content[:insert_idx] + "\n" + UTF8_FIX + "\n" + content[insert_idx:]
        path.write_text(new_content, encoding='utf-8')
        print(f"Patched {path}")

def main():
    for f in Path('scripts').rglob('*.py'):
        try:
            patch_python_file(f)
        except Exception as e:
            print(f"Error patching {f}: {e}")

if __name__ == "__main__":
    main()
