#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: uv_autofix.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
uv_autofix.py

Tiny helper to auto-install missing Python deps using uv *when explicitly enabled*.

Rationale:
  - We want "it just works" for lanes that touch APIs/MCP.
  - But we also do NOT want surprise installs by default.

Enablement:
  - Environment variable: CHTHONIC_UV_AUTOFIX=1

Usage (inside other scripts):
  from scripts.uv_autofix import ensure_deps
  ensure_deps(["mcp", "pydantic-settings"], reason="MCPClient lane")

@SID:           TOOL_UV_AUTOFIX_V1
@Shabti:        CLI Script
@Purpose:       Script logic for uv_autofix.py.
"""

from __future__ import annotations

import os
import subprocess
from importlib import metadata


def _enabled() -> bool:
    return (os.getenv("CHTHONIC_UV_AUTOFIX") or "").strip() in {"1", "true", "TRUE", "yes", "YES"}


def _installed(dist: str) -> bool:
    try:
        metadata.version(dist)
        return True
    except Exception:
        return False


def ensure_deps(dists: list[str], *, reason: str) -> None:
    """
    Ensure the given distribution names are installed.
    If missing and autofix is enabled, install via `uv pip install <dist>`.
    """
    missing = [d for d in dists if not _installed(d)]
    if not missing:
        return
    if not _enabled():
        raise RuntimeError(
            f"Missing deps: {', '.join(missing)}. Set CHTHONIC_UV_AUTOFIX=1 to auto-install via uv. Reason: {reason}"
        )
    for d in missing:
        subprocess.run(["uv", "pip", "install", d], check=True)
