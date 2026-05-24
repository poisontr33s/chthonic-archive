#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: check_mailbox_layout.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Check that the mailbox layout adheres to the canonical structure. This script ensures that:
- The canonical mailbox directories (e.g., "codex/mailbox", "claude/mailbox") exist.
- No files (except for ".gitkeep") are present in non-canonical mailbox directories (e.g., ".codex/mailbox", ".claude/mailbox").
- Any violations are reported with details for remediation.

Usage:
  uv run scripts/check_mailbox_layout.py --repo-root <path_to_repo_root>
Notes:
- The script exits with code 0 if the layout is valid, or 1 if any violations are found.

@SID:           TOOL_CHECK_MAILBOX_LAYOUT_V1
@Shabti:          Validation Script
@Context:       Repository Hygiene / Structural Validation
@Implements:    CONCEPT_CHECK_MAILBOX_LAYOUT
@Purpose:       Check that the mailbox layout adheres to the canonical structure. This script ensures that:
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


from __future__ import annotations

import argparse
from pathlib import Path

CANONICAL_DIRS = ("codex/mailbox", "claude/mailbox")
NON_CANONICAL_DIRS = (".codex/mailbox", ".claude/mailbox")


def list_files(path: Path) -> list[Path]:
    if not path.exists() or not path.is_dir():
        return []
    return sorted([p for p in path.iterdir() if p.is_file()])


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate canonical mailbox layout.")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    errors: list[str] = []

    for rel in CANONICAL_DIRS:
        p = root / rel
        if not p.exists() or not p.is_dir():
            errors.append(f"missing_canonical_dir: {rel}")

    for rel in NON_CANONICAL_DIRS:
        p = root / rel
        files = list_files(p)
        for f in files:
            if f.name == ".gitkeep":
                continue
            errors.append(f"noncanonical_mailbox_file: {f.relative_to(root).as_posix()}")

    print(f"Canonical dirs checked: {len(CANONICAL_DIRS)}")
    print(f"Layout violations: {len(errors)}")
    for err in errors:
        print(err)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
