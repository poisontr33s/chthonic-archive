#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: code_scent.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
code_scent.py — Olfactory Analysis: Code Smell Detection via Cyclomatic Complexity

@SID:           TOOL_CODE_SCENT_V1
@Shabti:        CLI Script
@Purpose:       Analyzes code complexity using radon and maps cyclomatic
                complexity scores to olfactory (scent) descriptors.
                Usage: uv run scripts/code_scent.py <file_path>
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


from __future__ import annotations
import sys
from pathlib import Path
from radon.complexity import cc_visit
from radon.raw import analyze

def analyze_scent(file_path: str) -> tuple[str, float]:
    """Analyze code complexity and map to scent descriptors"""
    try:
        code = Path(file_path).read_text(encoding='utf-8')
        complexity_results = cc_visit(code)

        if not complexity_results:
            return "NEUTRAL", 0.0

        # Average complexity across all functions/classes
        avg_complexity = sum(item.complexity for item in complexity_results) / len(complexity_results)

        # Map complexity to scent
        if avg_complexity < 5:
            scent = "🌸 FLORAL"
        elif avg_complexity < 10:
            scent = "🌲 FRESH"
        elif avg_complexity < 15:
            scent = "🌿 EARTHY"
        elif avg_complexity < 20:
            scent = "⚠️ PUNGENT"
        else:
            scent = "💀 ROTTEN"

        return scent, avg_complexity
    except Exception as e:
        return f"ERROR: {e}", 0.0

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = "autonomous_coordinator.py"

    print(f"👃 [OLFACTORY] Analyzing code scent...")

    # Scan Python files
    files_to_scan = [
        "autonomous_coordinator.py",
        "unified_topology.py",
        "scripts/mandala_topology.py",
        "scripts/cycle_detector.py"
    ]

    print("   📊 Scent Profile:")
    for file in files_to_scan:
        if Path(file).exists():
            scent, complexity = analyze_scent(file)
            print(f"      - {file}: {scent} (Complexity: {complexity:.1f})")
