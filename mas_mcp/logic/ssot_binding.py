#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: ssot_binding.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 📜 THE SCRIPTORIUM
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ .github/copilot-instructions.md
# ║   └─◄ .github/copilot-instructions.archive.md
# ╚════════════════════════════════════════════════════════════════════════════

"""
ssot_binding.py — Cryptographic SSOT Binding for MAS Pipeline.

@SID:           LOGIC_SSOT_BINDING_V2
@Shabti:        Domain Logic (Governance)
@Lineage:       Upcycled from LIB_SSOT_HANDLER_V1 (wet-paper-to-gold)
@Purpose:       Canonical text normalization, SHA-256 fingerprinting, and
                bookend drift detection. Wired into mas_pulse (session
                integrity), mas_narrative_scan (normalized vocab matching),
                and mas_scan (provenance binding).
"""

from __future__ import annotations

import hashlib
import os
import unicodedata
from pathlib import Path
from typing import Tuple

# Default SSOT paths relative to repository root
SSOT_POINTER = ".github/copilot-instructions.md"
SSOT_ARCHIVE = ".github/copilot-instructions.archive.md"


def _detect_git_root(project_root: Path) -> Path:
    """Walk upward until a git root is found, else fall back to project_root."""
    current = project_root.resolve()
    if current.is_file():
        current = current.parent

    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate

    return current


def _resolve_from_root(root: Path, env_value: str | None, fallback: str) -> Path:
    """Resolve env overrides relative to the detected repository root."""
    if env_value:
        candidate = Path(env_value).expanduser()
        return candidate if candidate.is_absolute() else root / candidate
    return root / fallback


def resolve_ssot(project_root: Path) -> Tuple[Path, Path]:
    """
    Resolve SSOT pointer and archive paths.

    Priority for each:
    1. SSOT_PATH / SSOT_ARCHIVE_PATH environment variables
    2. Standard paths relative to the detected git root

    Returns:
        (pointer_path, archive_path) — archive may not exist
    """
    root = _detect_git_root(project_root)
    env_pointer = os.environ.get("SSOT_PATH")
    pointer = _resolve_from_root(root, env_pointer, SSOT_POINTER)

    env_archive = os.environ.get("SSOT_ARCHIVE_PATH")
    archive = _resolve_from_root(root, env_archive, SSOT_ARCHIVE)

    return pointer, archive


def resolve_ssot_for_lexicon(project_root: Path) -> Path:
    """
    Resolve the richest available SSOT for lexicon extraction.
    Prefers archive (955KB, 1500+ terms) over pointer (4KB, 1 term).
    """
    pointer, archive = resolve_ssot(project_root)
    if archive.exists():
        return archive
    return pointer


def canonicalize_text(text: str) -> str:
    """
    Canonicalize text for consistent hashing and vocabulary matching.

    1. CRLF/CR → LF (line endings)
    2. Strip trailing whitespace per line
    3. Unicode NFC normalization
    4. Strip document-level whitespace

    Cross-platform identical output for identical semantic content.
    """
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = [line.rstrip() for line in text.split('\n')]
    text = '\n'.join(lines)
    text = unicodedata.normalize('NFC', text)
    text = text.strip()
    return text


def compute_ssot_hash(ssot_path: Path) -> str:
    """
    SHA-256 of canonical SSOT content. 64-char lowercase hex digest.
    """
    content = ssot_path.read_text(encoding='utf-8')
    canonical = canonicalize_text(content)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def verify_bookend(hash_start: str, ssot_path: Path) -> Tuple[bool, str]:
    """
    Bookend drift detection: compare session-start hash against current.

    Returns:
        (is_consistent, hash_now)
    """
    hash_now = compute_ssot_hash(ssot_path)
    return hash_start == hash_now, hash_now


# ─────────────────────────────────────────────────────────────────────────────
# Session-level bookend state (module-scoped singleton)
# ─────────────────────────────────────────────────────────────────────────────

_session_hash: str | None = None
_session_ssot_path: Path | None = None


def init_session_bookend(ssot_path: Path) -> str:
    """
    Stamp the session-start SSOT hash. Called once at server init.
    Returns the starting hash.
    """
    global _session_hash, _session_ssot_path
    _session_hash = compute_ssot_hash(ssot_path)
    _session_ssot_path = ssot_path
    return _session_hash


def check_session_bookend() -> dict:
    """
    Check whether the SSOT has drifted since session start.

    Returns:
        {
            "ssot_file": str,
            "hash_start": str (short),
            "hash_now": str (short),
            "drifted": bool
        }
    """
    if _session_hash is None or _session_ssot_path is None:
        return {"ssot_file": None, "hash_start": None, "hash_now": None, "drifted": None}

    is_ok, hash_now = verify_bookend(_session_hash, _session_ssot_path)
    return {
        "ssot_file": _session_ssot_path.name,
        "hash_start": _session_hash[:16],
        "hash_now": hash_now[:16],
        "drifted": not is_ok,
    }
