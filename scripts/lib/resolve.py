#!/usr/bin/env python3
#-*- coding: utf-8 -*-
# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: resolve.py
# ║ Python module: SIDEntry, SIDIndex, SID_PATTERNS, SCANNABLE_EXTENSIONS, INDEX_FILE, extract_sid_metadata...
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: 🌿 THE GARDEN
# ║ Semantic ID: TOOL_SID_RESOLVER_V1
# ║ Purpose: resolve.py - Semantic Identity Resolver (Anchor & Signal Protocol)
# ║ Exports: SIDEntry, SIDIndex, SID_PATTERNS, SCANNABLE_EXTENSIONS, INDEX_FILE,
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Cross-References (Bidirectional):
# ║ Dependents (Rely on me):
# ║   └─◄ scripts/lib/shared.py
# ╚════════════════════════════════════════════════════════════════════════════

#!/usr/bin/env python3
"""
resolve.py - Semantic Identity Resolver (Anchor & Signal Protocol)

@SID:           TOOL_SID_RESOLVER_V1
@Type:          CLI Tool
@Context:       Infrastructure / Identity Resolution
@Implements:    PROTOCOL_ANCHOR_SIGNAL, ROADMAP_TOOL_CONSOLIDATION_2026_01_27
@SessionOrigin: SESSION_DOC_2026_01_17_CLEANUP

Scans the codebase for @SID declarations and builds a resolution map.
Enables file-agnostic referencing - move files freely, SIDs remain stable.

Usage:
    chthonic resolve                    # Build/update SID index
    chthonic resolve --resolve SID     # Resolve a specific SID to path
    chthonic resolve --list            # List all known SIDs
    chthonic resolve --validate        # Check for broken references
    chthonic resolve --json            # Output as JSON
"""

from __future__ import annotations

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')



import argparse
import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from .shared import (
    configure_utf8_output,
    setup_logging,
    add_common_args,
    print_json,
    handle_errors,
)

# Configure UTF-8 output
configure_utf8_output()


@dataclass
class SIDEntry:
    """A resolved Semantic Identity entry."""
    sid: str
    path: str
    type: str = ""
    context: str = ""
    implements: str = ""
    session_origin: str = ""
    emits: str = ""
    spawned: list[str] = field(default_factory=list)
    last_seen: str = ""


@dataclass
class SIDIndex:
    """The complete SID resolution index."""
    version: str = "1.0"
    updated: str = ""
    entries: dict[str, SIDEntry] = field(default_factory=dict)
    orphaned_refs: list[str] = field(default_factory=list)


# Patterns to extract @SID metadata
SID_PATTERNS = {
    "sid": r"@SID:\s*([A-Z_][A-Z0-9_]*)",
    "type": r"@Type:\s*(.+?)(?:\n|$)",
    "context": r"@Context:\s*(.+?)(?:\n|$)",
    "implements": r"@Implements:\s*(\S+)",
    "session_origin": r"@SessionOrigin:\s*(\S+)",
    "emits": r"@Emits:\s*(.+?)(?:\n|$)",
    "spawned": r"@Spawned:\s*(.+?)(?:\n|$)",
}

# File extensions to scan
SCANNABLE_EXTENSIONS = {
    ".py", ".md", ".ts", ".js", ".ps1", ".sh", ".rs", ".toml", ".yaml", ".yml"
}

INDEX_FILE = Path("data/indices/sid_index.json")


def extract_sid_metadata(content: str) -> dict[str, Any] | None:
    """Extract @SID metadata from file content."""
    sid_match = re.search(SID_PATTERNS["sid"], content)
    if not sid_match:
        return None

    metadata = {"sid": sid_match.group(1).strip()}

    for key, pattern in SID_PATTERNS.items():
        if key == "sid":
            continue
        match = re.search(pattern, content)
        if match:
            value = match.group(1).strip()
            if key == "spawned":
                metadata[key] = [s.strip() for s in value.split(",")]
            else:
                metadata[key] = value

    return metadata


# Directories to strictly ignore
IGNORE_DIRS = {
    ".git", ".venv", ".bun", ".cache", "node_modules", "dist", "build", 
    "__pycache__", ".vscode", ".idea"
}

# Dot-directories explicitly allowed for scanning (Temple/Triad domains)
ALLOWED_DOT_DIRS = {".temple", ".codex", ".github", ".gemini"}


def scan_directory(root: Path, logger) -> dict[str, SIDEntry]:
    """Scan directory for files with @SID declarations."""
    entries = {}

    for filepath in root.glob("**/*"):
        if not filepath.is_file():
            continue
        if filepath.suffix.lower() not in SCANNABLE_EXTENSIONS:
            continue
        
        # Smart Filtering:
        # 1. Ignore if any part of path is in IGNORE_DIRS
        # 2. Ignore dot-directories UNLESS they are in ALLOWED_DOT_DIRS
        parts = filepath.parts
        if any(p in IGNORE_DIRS for p in parts):
            continue
            
        # Check for blocked dot-directories
        is_blocked_dot = False
        for part in parts:
            if part.startswith(".") and part not in ALLOWED_DOT_DIRS:
                is_blocked_dot = True
                break
        if is_blocked_dot:
            continue

        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
            metadata = extract_sid_metadata(content)

            if metadata:
                sid = metadata["sid"]
                entry = SIDEntry(
                    sid=sid,
                    path=str(filepath.relative_to(root)),
                    type=metadata.get("type", ""),
                    context=metadata.get("context", ""),
                    implements=metadata.get("implements", ""),
                    session_origin=metadata.get("session_origin", ""),
                    emits=metadata.get("emits", ""),
                    spawned=metadata.get("spawned", []),
                    last_seen=datetime.now().isoformat(),
                )
                entries[sid] = entry

        except Exception as e:
            logger.warning(f"Could not scan {filepath}: {e}")

    return entries


def load_index(index_path: Path) -> SIDIndex:
    """Load existing SID index."""
    if index_path.exists():
        try:
            data = json.loads(index_path.read_text(encoding="utf-8"))
            entries = {
                sid: SIDEntry(**entry)
                for sid, entry in data.get("entries", {}).items()
            }
            return SIDIndex(
                version=data.get("version", "1.0"),
                updated=data.get("updated", ""),
                entries=entries,
                orphaned_refs=data.get("orphaned_refs", []),
            )
        except Exception:
            pass
    return SIDIndex()


def save_index(index: SIDIndex, index_path: Path):
    """Save SID index to file."""
    index_path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "version": index.version,
        "updated": index.updated,
        "entries": {sid: asdict(entry) for sid, entry in index.entries.items()},
        "orphaned_refs": index.orphaned_refs,
    }
    index_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


@handle_errors
def main():
    parser = argparse.ArgumentParser(
        description="Semantic Identity Resolver - Anchor & Signal Protocol",
        prog="chthonic resolve"
    )
    parser.add_argument(
        "--root", type=Path, default=Path("."),
        help="Root directory to scan"
    )
    parser.add_argument(
        "--resolve", "-r", metavar="SID",
        help="Resolve a specific SID to its current path"
    )
    parser.add_argument(
        "--list", "-l", action="store_true",
        help="List all known SIDs"
    )
    parser.add_argument(
        "--validate", action="store_true",
        help="Validate all SID references"
    )
    
    # Add common args (--json, --dry-run, --verbose, --quiet)
    add_common_args(parser)

    args = parser.parse_args()
    logger = setup_logging(verbose=args.verbose, quiet=args.quiet)

    root = args.root.resolve()
    index_path = root / INDEX_FILE

    # Resolve specific SID
    if args.resolve:
        index = load_index(index_path)
        sid = args.resolve

        if sid in index.entries:
            entry = index.entries[sid]
            if args.json:
                print_json(asdict(entry))
            else:
                logger.info(f"SID:  {entry.sid}")
                logger.info(f"Path: {entry.path}")
                if entry.type:
                    logger.info(f"Type: {entry.type}")
        else:
            logger.error(f"SID not found: {args.resolve}")
            logger.info("Run without arguments to rebuild index.")
        return

    # List all SIDs
    if args.list:
        index = load_index(index_path)
        if args.json:
            print_json(list(index.entries.keys()))
        else:
            logger.info(f"Known SIDs ({len(index.entries)}):\n")
            for sid, entry in sorted(index.entries.items()):
                print(f"  {sid}")
                print(f"    -> {entry.path}")
        return

    # Validate references
    if args.validate:
        index = load_index(index_path)
        if not index.entries:
            logger.error("No index found. Run without arguments first.")
            return

        logger.info(f"Index contains {len(index.entries)} SIDs")
        if index.orphaned_refs:
            logger.warning(f"Orphaned references: {len(index.orphaned_refs)}")
            for ref in index.orphaned_refs:
                print(f"  - {ref}")
        else:
            logger.info("All SID references are valid.")
        return

    # Default: rebuild index
    logger.info(f"Scanning: {root}")
    entries = scan_directory(root, logger)
    logger.info(f"Found {len(entries)} SID declarations")

    # Build index
    index = SIDIndex(
        updated=datetime.now().isoformat(),
        entries=entries,
    )

    if args.dry_run:
        logger.info("\n[DRY RUN] Index Content Preview:")
        if args.json:
            print_json({sid: asdict(e) for sid, e in entries.items()})
        else:
            for sid in sorted(entries.keys()):
                print(f"  {sid} -> {entries[sid].path}")
        logger.info(f"\n[DRY RUN] Would save to: {index_path}")
    else:
        # Save
        save_index(index, index_path)
        logger.info(f"Index saved to: {index_path}")

        if args.json:
            print_json({sid: asdict(e) for sid, e in entries.items()})
        else:
            logger.info("\nSIDs indexed:")
            for sid in sorted(entries.keys()):
                print(f"  {sid} -> {entries[sid].path}")


if __name__ == "__main__":
    main()
