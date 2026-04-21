#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""
ssot_paths.py — SSOT Path Bridge for scripts/.

Thin re-export from mas_mcp.logic.ssot_manifest so that scripts/ modules
never hardcode SSOT filenames. If a filename changes, ssot_manifest.py
changes first, and this bridge propagates it everywhere.

Usage in any script:
    from scripts.lib.ssot_paths import SSOT_POINTER, SSOT_HOLDER, resolve_ssot_paths

    root = find_repo_root()
    paths = resolve_ssot_paths(root)
    ssot_content = paths.pointer.read_text(encoding="utf-8")
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

# Ensure repo root is importable (scripts may be run from anywhere)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    from mas_mcp.logic.ssot_manifest import (  # noqa: E402
        SSOT_HOLDER_RELPATH,
        SSOT_POINTER_RELPATH,
        SSOT_PROTO_RELPATH,
    )
except ImportError:
    import warnings
    warnings.warn(
        "mas_mcp.logic.ssot_manifest not importable — using hardcoded fallback paths. "
        "Install the package or run from the repo root.",
        DeprecationWarning,
        stacklevel=2,
    )
    SSOT_HOLDER_RELPATH = ".github/copilot-instructions.archive.md"
    SSOT_POINTER_RELPATH = ".github/copilot-instructions.md"
    SSOT_PROTO_RELPATH = ".github/copilot-instructions-copy.md"

# ─── Re-exported constants (relative paths as strings) ──────────────────────
SSOT_HOLDER = SSOT_HOLDER_RELPATH
SSOT_POINTER = SSOT_POINTER_RELPATH
SSOT_PROTO = SSOT_PROTO_RELPATH


@dataclass(frozen=True)
class SSOTPaths:
    """Resolved absolute SSOT paths for a given repo root."""
    holder: Path
    pointer: Path
    proto: Path


def resolve_ssot_paths(repo_root: Path) -> SSOTPaths:
    """Resolve canonical SSOT paths from a repo root."""
    return SSOTPaths(
        holder=repo_root / SSOT_HOLDER_RELPATH,
        pointer=repo_root / SSOT_POINTER_RELPATH,
        proto=repo_root / SSOT_PROTO_RELPATH,
    )
