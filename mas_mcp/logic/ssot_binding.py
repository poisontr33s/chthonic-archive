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

@SID:           LOGIC_SSOT_BINDING_V3
@Shabti:        Domain Logic (Governance)
@Lineage:       Upcycled from LIB_SSOT_HANDLER_V1 (wet-paper-to-gold)
@Purpose:       Canonical text normalization, SHA-256 fingerprinting,
                semantic vitals fingerprint, persistent hash journal, and
                bookend drift detection. Wired into mas_pulse (session
                integrity), mas_narrative_scan (normalized vocab matching),
                and mas_scan (provenance binding).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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


# ─────────────────────────────────────────────────────────────────────────────
# Semantic Vitals Fingerprint
# ─────────────────────────────────────────────────────────────────────────────

# Entity names shared with narrative.py — single source of truth
KNOWN_ENTITIES = [
    "Orackla", "Umeko", "Lysandra", "Kali", "Vesper", "Seraphine", "Claudine",
]


def compute_ssot_vitals(ssot_path: Path) -> Dict[str, Any]:
    """
    Semantic fingerprint of SSOT state.

    Returns a structured dict that tells you the *shape* of the world:
      - hash: exact SHA-256 (collision-resistant identity)
      - lexicon_cardinality: count of extractable canon terms
      - entity_census: which entities are present
      - section_count: markdown heading count (structural complexity)
      - byte_size: raw file size
      - fingerprint: compact human-readable summary, e.g. "L1504·E7·S42·955K"

    After a submergence, one glance at the fingerprint tells you what world
    you're in without re-reading 955KB of SSOT.
    """
    raw = ssot_path.read_bytes()
    content = canonicalize_text(raw.decode('utf-8', errors='ignore'))
    sha = hashlib.sha256(content.encode('utf-8')).hexdigest()

    # Lexicon cardinality (same extraction as narrative.py)
    bt_terms = set(re.findall(r'`([A-Za-z][A-Za-z0-9\-_\.]{2,})`', content))
    paren_terms = set(re.findall(r'\(`([^`\)]+)`?\)', content))
    lexicon = bt_terms | paren_terms

    # Entity census
    content_lower = content.lower()
    entities_present = [e for e in KNOWN_ENTITIES if e.lower() in content_lower]

    # Section count (markdown headings)
    sections = len(re.findall(r'^#{1,6}\s', content, re.MULTILINE))

    # Byte size
    byte_size = len(raw)

    # Compact fingerprint: L{lexicon}·E{entities}·S{sections}·{size}
    if byte_size >= 1_000_000:
        size_label = f"{byte_size / 1_000_000:.1f}M"
    elif byte_size >= 1_000:
        size_label = f"{byte_size // 1_000}K"
    else:
        size_label = f"{byte_size}B"

    fingerprint = f"L{len(lexicon)}\u00b7E{len(entities_present)}\u00b7S{sections}\u00b7{size_label}"

    return {
        "hash": sha,
        "lexicon_cardinality": len(lexicon),
        "entity_census": entities_present,
        "section_count": sections,
        "byte_size": byte_size,
        "fingerprint": fingerprint,
    }


def compare_vitals(
    before: Dict[str, Any], after: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Human-readable diff between two vitals snapshots.

    Returns structured deltas and a summary sentence. Designed to answer
    "what changed while I was submerged?" in one glance.
    """
    lex_delta = after["lexicon_cardinality"] - before["lexicon_cardinality"]
    sec_delta = after["section_count"] - before["section_count"]
    size_delta = after["byte_size"] - before["byte_size"]

    entities_added = [e for e in after["entity_census"] if e not in before["entity_census"]]
    entities_removed = [e for e in before["entity_census"] if e not in after["entity_census"]]
    hash_changed = before["hash"] != after["hash"]

    # Build summary sentence
    parts: List[str] = []
    if lex_delta > 0:
        parts.append(f"lexicon grew by {lex_delta} terms")
    elif lex_delta < 0:
        parts.append(f"lexicon shrank by {abs(lex_delta)} terms")
    if entities_added:
        parts.append(f"entities added: {', '.join(entities_added)}")
    if entities_removed:
        parts.append(f"entities removed: {', '.join(entities_removed)}")
    if sec_delta > 0:
        parts.append(f"{sec_delta} sections added")
    elif sec_delta < 0:
        parts.append(f"{abs(sec_delta)} sections removed")
    if size_delta:
        sign = "+" if size_delta > 0 else ""
        parts.append(f"size {sign}{size_delta} bytes")
    if not parts:
        parts.append("no structural change detected")

    return {
        "hash_changed": hash_changed,
        "lexicon_delta": lex_delta,
        "section_delta": sec_delta,
        "byte_delta": size_delta,
        "entities_added": entities_added,
        "entities_removed": entities_removed,
        "fingerprint_before": before["fingerprint"],
        "fingerprint_after": after["fingerprint"],
        "summary": "; ".join(parts),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Hash Journal — persistent SSOT state timeline
# ─────────────────────────────────────────────────────────────────────────────

JOURNAL_FILENAME = "ssot_hash_journal.jsonl"


def _journal_path(project_root: Path) -> Path:
    """Journal lives at <repo>/.mas_mcp/ssot_hash_journal.jsonl."""
    journal_dir = project_root / ".mas_mcp"
    journal_dir.mkdir(exist_ok=True)
    return journal_dir / JOURNAL_FILENAME


def stamp_journal(
    project_root: Path,
    vitals: Dict[str, Any],
    event: str = "startup",
) -> Dict[str, Any]:
    """
    Append a vitals snapshot to the hash journal.

    Events: "startup", "drift_detected", "manual"
    Returns the entry that was written.
    """
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "event": event,
        "fingerprint": vitals["fingerprint"],
        "hash": vitals["hash"][:16],
        "lexicon": vitals["lexicon_cardinality"],
        "entities": len(vitals["entity_census"]),
        "sections": vitals["section_count"],
        "bytes": vitals["byte_size"],
    }
    jpath = _journal_path(project_root)
    with jpath.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, separators=(",", ":")) + "\n")
    return entry


def read_journal_tail(
    project_root: Path, n: int = 10
) -> List[Dict[str, Any]]:
    """
    Read the last *n* journal entries. After submergence, this shows
    what the world looked like at each checkpoint you missed.
    """
    jpath = _journal_path(project_root)
    if not jpath.exists():
        return []
    lines = jpath.read_text(encoding="utf-8").strip().splitlines()
    tail = lines[-n:]
    entries: List[Dict[str, Any]] = []
    for line in tail:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


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
_session_vitals: Dict[str, Any] | None = None
_session_project_root: Path | None = None


def init_session_bookend(ssot_path: Path, project_root: Optional[Path] = None) -> str:
    """
    Stamp the session-start SSOT vitals. Called once at server init.
    Journals the startup event if project_root is provided.
    Returns the starting hash.
    """
    global _session_hash, _session_ssot_path, _session_vitals, _session_project_root
    vitals = compute_ssot_vitals(ssot_path)
    _session_hash = vitals["hash"]
    _session_ssot_path = ssot_path
    _session_vitals = vitals
    _session_project_root = project_root
    if project_root is not None:
        stamp_journal(project_root, vitals, event="startup")
    return _session_hash


def check_session_bookend() -> dict:
    """
    Check whether the SSOT has drifted since session start.

    Now vitals-aware: returns fingerprints + a human-readable diff summary
    when drift is detected — not just a boolean. After submergence, this
    tells you *what* changed, not just *that* it changed.

    Returns:
        {
            "ssot_file": str,
            "hash_start": str (short),
            "hash_now": str (short),
            "drifted": bool,
            "fingerprint_start": str,      # compact vitals at session start
            "fingerprint_now": str,         # compact vitals right now
            "drift_summary": str | None,    # human sentence if drifted
        }
    """
    if _session_hash is None or _session_ssot_path is None:
        return {
            "ssot_file": None, "hash_start": None, "hash_now": None,
            "drifted": None, "fingerprint_start": None,
            "fingerprint_now": None, "drift_summary": None,
        }

    vitals_now = compute_ssot_vitals(_session_ssot_path)
    is_ok = _session_hash == vitals_now["hash"]

    drift_summary: str | None = None
    if not is_ok and _session_vitals is not None:
        diff = compare_vitals(_session_vitals, vitals_now)
        drift_summary = diff["summary"]
        # Journal the drift event
        if _session_project_root is not None:
            stamp_journal(_session_project_root, vitals_now, event="drift_detected")

    fp_start = _session_vitals["fingerprint"] if _session_vitals else None

    return {
        "ssot_file": _session_ssot_path.name,
        "hash_start": _session_hash[:16],
        "hash_now": vitals_now["hash"][:16],
        "drifted": not is_ok,
        "fingerprint_start": fp_start,
        "fingerprint_now": vitals_now["fingerprint"],
        "drift_summary": drift_summary,
    }
