#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: __main__.py
# ║ Python module: get_commit_hash, make_relative_path, build_index
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: 🌿 THE GARDEN
# ║ Purpose: Main execution - coordinate system over semantic field.
# ║         This tool answers "where" & "how often."
# ║         It must never answer "what" or "why."
# ║ Exports: get_commit_hash, make_relative_path, build_index, main
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Cross-References (Bidirectional):
# ║ Dependents (Rely on me):
# ║  └─◄ ankh_atlas\ankh_atlas\index.py
# ║  └─◄ ankh_atlas\ankh_atlas\detectors.py
# ║  └─◄ ankh_atlas\ankh_atlas\scan.py
# ║  └─◄ ankh_atlas\ankh_atlas\models.py
# ╚════════════════════════════════════════════════════════════════════════════
# @sid:chthonic-archive/ankh_atlas/ankh_atlas/__main__.py
# @id:6f4e2f90-3e2e-11ee-9726-0242ac120003
# @CopilotVersion: COPILOT_PRO_VSCODE_SETUP_REPORT.md:2026-01-29
# ════════════════════════════════════════════════════════════════════════════

"""
Main execution - coordinate system over semantic field.
This tool answers "where" & "how often."
It must never answer "what" or "why."
"""

import subprocess
from pathlib import Path

from .detectors import (
    TIER_1_DETECTORS,
    detect_abbrev_def,
    detect_abbrev_use,
)
from .index import serialize_index, write_index
from .models import Signal
from .scan import iter_md, scan_file


def get_commit_hash() -> str | None:
    """Get current git commit hash (if in git repo)."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def make_relative_path(path: Path, repo_root: Path) -> str:
    """Convert absolute path to relative path from repo root."""
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        # If path is not relative to repo_root, return as-is
        return str(path)


def build_index(repo_root: Path) -> list[Signal]:
    """Scan all markdown files and build signal index.

    This is the core pipeline:
    1. Walk files deterministically
    2. Apply Tier 1 detectors
    3. Track abbreviation state for def/use distinction
    4. Return flat list of signals
    """
    signals: list[Signal] = []
    known_abbrevs: set[str] = set()

    for md_path in iter_md(repo_root):
        relative_path = make_relative_path(md_path, repo_root)

        for line_no, line in scan_file(md_path):
            # Apply stateless detectors
            for detector in TIER_1_DETECTORS:
                result = detector(line, line_no, Path(relative_path))
                if result:
                    if isinstance(result, list):
                        signals.extend(result)
                    else:
                        signals.append(result)

            # Apply abbreviation detectors (stateful)
            abbrev_def = detect_abbrev_def(line, line_no, Path(relative_path), known_abbrevs)
            if abbrev_def:
                signals.append(abbrev_def)

            abbrev_uses = detect_abbrev_use(line, line_no, Path(relative_path), known_abbrevs)
            signals.extend(abbrev_uses)

    return signals


def main() -> None:
    """Generate ankh_index.json at repo root."""
    # Assume we're in ankh_atlas/ directory, repo root is parent
    repo_root = Path(__file__).parent.parent.parent
    output_path = repo_root / "ankh_index.json"

    print(f"Scanning {repo_root}...")
    signals = build_index(repo_root)
    print(f"Detected {len(signals)} signals")

    commit_hash = get_commit_hash()
    print(f"Current commit: {commit_hash or 'unknown'}")

    index_data = serialize_index(signals, repo_root, commit_hash)
    write_index(index_data, output_path)

    print(f"Index written to {output_path}")
    print(f"Signal breakdown:")

    # Count by type (purely informational, no interpretation)
    signal_types: dict[str, int] = {}
    for sig in signals:
        signal_types[sig.signal_type] = signal_types.get(sig.signal_type, 0) + 1

    for sig_type in sorted(signal_types.keys()):
        count = signal_types[sig_type]
        print(f"  {sig_type}: {count}")


if __name__ == "__main__":
    main()
