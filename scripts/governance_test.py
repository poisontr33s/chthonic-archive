#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: governance_test.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
governance_test.py — Script logic for governance_test.py.

@SID:           TOOL_GOVERNANCE_TEST_V1
@Shabti:        CLI Script
@Purpose:       Script logic for governance_test.py.
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import sqlite3

db = sqlite3.connect(r"C:\Users\erdno\chthonic-archive\scripts\test_epistemograph.sqlite")
cur = db.cursor()

print("=" * 80)
print("CRITICAL QUERY: SSOT Hierarchy Validation")
print("=" * 80)
print("\nExpected: .github/copilot-instructions.md should have:")
print("  - Highest export count (most referenced)")
print("  - GOLD spectral frequency")
print("  - DOCUMENTATION role")
print("  - 'Single Source of Truth' in essence")
print()

result = cur.execute("""
SELECT
    path,
    dcrp_spectral_freq,
    dcrp_role,
    dcrp_exports_count,
    dcrp_essence
FROM files
WHERE path LIKE '%copilot-instructions.md'
ORDER BY dcrp_exports_count DESC
""").fetchall()

print("Actual results:")
for path, freq, role, exports, essence in result:
    status = "✓ PASS" if all([
        freq == "GOLD",
        "DOCUMENTATION" in role,
        exports > 50,
        "Single Source of Truth" in essence or "Codex Brahmanica" in essence
    ]) else "✗ FAIL"

    print(f"\n{status} | {path}")
    print(f"  Frequency: {freq} (expected: GOLD)")
    print(f"  Role: {role} (expected: DOCUMENTATION)")
    print(f"  Exports: {exports} (expected: >50)")
    print(f"  Essence: {essence[:80]}...")

print("\n" + "=" * 80)
print("DISTRIBUTION SANITY CHECK")
print("=" * 80)
print("\nExpected distribution based on tri-modal architecture:")
print("  GOLD (DOCUMENTATION): ~50-60 files (session logs, governance)")
print("  WHITE (GARDEN/Python): ~15-20 files (MCP, GPU, MILF systems)")
print("  RED (FORTRESS/Rust): ~1-5 files (Vulkan rendering)")
print("  BLUE (CONFIGURATION): ~20-30 files (JSON, TOML, YAML)")
print()

result = cur.execute("""
SELECT dcrp_spectral_freq, COUNT(*) as count
FROM files
GROUP BY dcrp_spectral_freq
ORDER BY count DESC
""").fetchall()

print("Actual distribution:")
for freq, count in result:
    print(f"  {freq:12s}: {count:3d} files")

db.close()
