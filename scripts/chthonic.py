#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: chthonic.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
@SID:           TOOL_CHTHONIC_ROUTER_PYTHON
@Shabti:          Router Script
@Context:       Infrastructure / CLI Entry Point
@Implements:    ROADMAP_TOOL_CONSOLIDATION_2026_01_27
@Purpose:       Script logic for chthonic.py.
Python-based router for platforms without Bash/PowerShell. Dispatches to lib/ modules.
Usage:
    python scripts/chthonic.py <command> [<args>]
Commands:
    audit       Analyze root directory health and recommend cleanups
    compact     Condense markdown files using noise pattern matching
    extract     Extract valuable content from session JSONL files
    resolve     Resolve Semantic IDs (@SID) to file paths
    map         Generate codebase inventory and dependency graph
    analyze     Frequency analysis of line patterns (diagnostic)
Options:
    --version   Show version and exit
    --help      Show this help message and exit
Notes:
    - This script serves as a fallback for environments where the primary chthonic CLI (Bash/PowerShell) may not be available.
    - For optimal performance and compatibility, use the primary chthonic CLI when possible.
    - The script exits with code 0 on success, or 1 on error (e.g., unknown command).
"""

from __future__ import annotations
import subprocess
import sys
from pathlib import Path

VERSION = "1.0.0"

SCRIPT_DIR = Path(__file__).parent
LIB_DIR = SCRIPT_DIR / "lib"

COMMANDS = {
    "audit": "audit.py",
    "compact": "compact.py",
    "extract": "extract.py",
    "resolve": "resolve.py",
    "map": "map.py",
    "analyze": "analyze.py",
}

HELP_TEXT = f"""chthonic v{VERSION} - CLI tooling for chthonic-archive

Usage: chthonic [--version] [--help] <command> [<args>]

Commands:
  audit       Analyze root directory health and recommend cleanups
  compact     Condense markdown files using noise pattern matching
  extract     Extract valuable content from session JSONL files
  resolve     Resolve Semantic IDs (@SID) to file paths
  map         Generate codebase inventory and dependency graph
  analyze     Frequency analysis of line patterns (diagnostic)

Options:
  --version   Show version
  --help      Show this help

Run 'chthonic <command> --help' for command-specific help.
"""

def main():
    if len(sys.argv) < 2:
        print(HELP_TEXT)
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command in ("--version", "-v"):
        print(f"chthonic v{VERSION}")
        sys.exit(0)

    if command in ("--help", "-h", "help"):
        print(HELP_TEXT)
        sys.exit(0)

    if command not in COMMANDS:
        print(f"Error: Unknown command '{command}'", file=sys.stderr)
        print("Run 'chthonic --help' for usage.", file=sys.stderr)
        sys.exit(1)

    # Dispatch to lib module
    script_path = LIB_DIR / COMMANDS[command]
    result = subprocess.run(
        ["uv", "run", "python", "-m", f"lib.{command}"] + args,
        cwd=SCRIPT_DIR
    )
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
