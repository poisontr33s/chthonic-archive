#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: scan_redundancy.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
scan_redundancy.py — Script logic for scan_redundancy.py.

@SID:           TOOL_SCAN_REDUNDANCY_V1
@Shabti:        CLI Script
@Purpose:       Script logic for scan_redundancy.py.
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import os
import re
from pathlib import Path
import sys
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
from scripts.lib.ssot_paths import resolve_ssot_paths

# Configuration
_SSOT = resolve_ssot_paths(_REPO_ROOT)
SSOT_PATH = _SSOT.pointer
IGNORE_DIRS = {".git", "node_modules", "dist", ".venv", "__pycache__", "target"}
IGNORE_FILES = {"scan_redundancy.py", "package-lock.json", "bun.lock", "uv.lock"}

def extract_ssot_colors(ssot_path):
    """Extracts FA color definitions from the SSOT."""
    if not ssot_path.exists():
        print(f"❌ SSOT not found at {ssot_path}")
        return {}

    content = ssot_path.read_text(encoding="utf-8")
    # Regex to find FA definitions: e.g., FA¹ (Red #FF6B6B)
    # Looks for FA followed by superscript or number, optional text, then hex
    pattern = re.compile(r"FA[¹²³⁴⁵1-5].*?#([A-Fa-f0-9]{6})", re.IGNORECASE)

    # Hardcoded FA colors from theme artifact (reverse-lookup)
    colors = {
        "#FF6B6B", # FA1 (Red)
        "#FFB84D", # FA2 (Orange)
        "#FFD700", # FA3 (Gold)
        "#4ECDC4", # FA4 (Blue)
        "#B8B8CC", # FA5 (White)
    }
    return colors

def scan_codebase(root_path, target_colors):
    """Scans the codebase for the target colors."""
    matches = {color: [] for color in target_colors}

    for root, dirs, files in os.walk(root_path):
        # Filter directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in files:
            if file in IGNORE_FILES:
                continue

            file_path = Path(root) / file

            # Skip the SSOT itself to find *redundancy*
            if file_path.resolve() == SSOT_PATH.resolve():
                continue

            try:
                # Read as text, ignore binary errors
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                for color in target_colors:
                    if color in content or color.lower() in content:
                        matches[color].append(str(file_path))
            except Exception:
                continue # Skip binary/unreadable files

    return matches

def main():
    print(f"🔍 Scanning for redundancy based on SSOT: {SSOT_PATH}")

    colors = extract_ssot_colors(SSOT_PATH)
    if not colors:
        print("⚠️  No FA color definitions found in SSOT regex scan.")
        return

    print(f"🎨 Found {len(colors)} Axiomatic Colors in SSOT: {', '.join(colors)}")
    print("🚀 Scanning codebase for redundant artifacts...\n")

    redundancy_map = scan_codebase(".", colors)

    total_redundant_files = set()

    for color, files in redundancy_map.items():
        if files:
            print(f"🔴 Color {color} found in {len(files)} files:")
            for f in files:
                print(f"   - {f}")
                total_redundant_files.add(f)
        else:
            print(f"⚪ Color {color} is UNIQUE to SSOT (No redundancy found).")

    print("\n📊 Summary:")
    print(f"   Total Unique Axiomatic Colors: {len(colors)}")
    print(f"   Files containing Redundant Definitions: {len(total_redundant_files)}")

    if len(total_redundant_files) > 0:
        print("\n✅ REDUNDANCY CONFIRMED. These files are downstream artifacts.")
        print("   They are candidates for auto-generation from SSOT.")
    else:
        print("\n❓ NO REDUNDANCY FOUND. The SSOT colors are not propagating.")

if __name__ == "__main__":
    main()
