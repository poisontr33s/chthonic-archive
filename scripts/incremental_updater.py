#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: incremental_updater.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
@SID:           TOOL_INCREMENTAL_UPDATER_PYTHON
@Shabti:          Utility Script
@Context:       Development Workflow Optimization / Incremental Scanning
@Implements:    CONCEPT_INCREMENTAL_UPDATER
@Purpose:       Script logic for incremental_updater.py.
Purpose: Detect changed files and trigger partial scans in DCRP for;
faster feedback loops.
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


from __future__ import annotations
import subprocess
import sys

def get_changed_files():
    # Get status of files: Added (A), Modified (M), Renamed (R)
    result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True, encoding='utf-8')
    files = []
    for line in result.stdout.splitlines():
        status, path = line[:2], line[3:]
        if any(s in status for s in ['M', 'A', 'R']):
            files.append(path)
    return files

def trigger_partial_scan(files):
    if not files:
        print('💤 No topology changes detected. Skipping scan.')
        return

    print(f'⚡ Incremental Scan Triggered for {len(files)} files...')
    # Here we would call the DCRP specifically for these files
    # For Phase 4 Prototype, we simply log the intent
    print(f'   Targeting: {files[:3]}...')

if __name__ == '__main__':
    changed = get_changed_files()
    trigger_partial_scan(changed)
