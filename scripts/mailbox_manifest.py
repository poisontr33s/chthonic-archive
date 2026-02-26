#!/usr/bin/env python3
#-*- coding: utf-8 -*-
"""
Mailbox Manifest Tracker.

Scans all mailbox directories (claude/mailbox, codex/mailbox, gemini/mailbox,
.claude/mailbox, .codex/mailbox, claude-codex-gemini/) and produces a single
JSON manifest that can be committed to git — giving full inventory visibility
without requiring git to track individual mailbox files.

@SID:           TOOL_MAILBOX_MANIFEST_V1
@Type:          Utility
@Context:       Infrastructure / Cross-Agent Tracking
@Implements:    NUKE-RESILIENCE mailbox tracking without git pollution

Usage:
    uv run scripts/mailbox_manifest.py                  # scan + write manifest
    uv run scripts/mailbox_manifest.py --diff            # show changes since last manifest
    uv run scripts/mailbox_manifest.py --check           # exit 1 if manifest is stale
    uv run scripts/mailbox_manifest.py --prune           # remove manifest entries for deleted files
    uv run scripts/mailbox_manifest.py --verbose         # debug logging
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from scripts.lib.shared import configure_utf8_output, find_repo_root, setup_logging

# =============================================================================
# Constants
# =============================================================================

MANIFEST_FILENAME = "MAILBOX_MANIFEST.json"
SCHEMA_VERSION = 1

# Roots to scan (relative to repo root)
MAILBOX_ROOTS: list[str] = [
    "claude/mailbox",
    "codex/mailbox",
    "gemini/mailbox",
    ".claude/mailbox",
    ".codex/mailbox",
    "claude-codex-gemini",
]

# Extensions we care about
TRACKED_EXTENSIONS: set[str] = {".md", ".json", ".txt", ".yaml", ".yml", ".toml"}

# Directories to skip inside mailbox roots
SKIP_DIRS: set[str] = {"__pycache__", ".git", "node_modules"}

# Files to exclude from scanning (self-reference prevention)
SKIP_FILES: set[str] = {MANIFEST_FILENAME}

# Workstream classification rules (prefix → workstream)
WORKSTREAM_RULES: list[tuple[str, str]] = [
    ("SESSION_HANDOFF", "session-handoff"),
    ("SESSION_COMPACT", "session-handoff"),
    ("HANDOFF_AUDIT", "handoff-audit"),
    ("SCM_TRIAGE", "scm-triage"),
    ("PRE_SCM", "scm-triage"),
    ("POE_", "poe-transport"),
    ("GENRE_", "genre-extraction"),
    ("KCP_", "kcp-spectrum"),
    ("WPTG_", "wptg-alignment"),
    ("MAILBOX_HANDOFF", "mailbox-verification"),
    ("GENRE_DAEMON", "genre-daemon"),
]


def classify_workstream(filename: str) -> str:
    """Classify a file into a workstream based on its name prefix."""
    upper = filename.upper()
    for prefix, workstream in WORKSTREAM_RULES:
        if upper.startswith(prefix):
            return workstream
    return "unclassified"


def file_sha256(path: Path) -> str:
    """Compute SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def scan_mailbox_root(repo_root: Path, root_rel: str, log) -> list[dict]:
    """Scan a single mailbox root and return file entries."""
    root = repo_root / root_rel
    if not root.is_dir():
        log.debug("Skipping missing root: %s", root_rel)
        return []

    entries = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in TRACKED_EXTENSIONS:
            continue
        if any(skip in path.parts for skip in SKIP_DIRS):
            continue
        if path.name in SKIP_FILES:
            continue

        rel = path.relative_to(repo_root).as_posix()
        stat = path.stat()
        entries.append({
            "path": rel,
            "root": root_rel,
            "filename": path.name,
            "extension": path.suffix.lower(),
            "size_bytes": stat.st_size,
            "mtime_iso": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            "sha256": file_sha256(path),
            "workstream": classify_workstream(path.stem),
        })
        log.debug("Indexed: %s (%d bytes)", rel, stat.st_size)

    return entries


def build_manifest(repo_root: Path, log) -> dict:
    """Scan all roots and build the full manifest."""
    all_entries = []
    root_stats: dict[str, int] = {}

    for root_rel in MAILBOX_ROOTS:
        entries = scan_mailbox_root(repo_root, root_rel, log)
        all_entries.extend(entries)
        if entries:
            root_stats[root_rel] = len(entries)

    # Workstream summary
    ws_counts: dict[str, int] = {}
    for e in all_entries:
        ws = e["workstream"]
        ws_counts[ws] = ws_counts.get(ws, 0) + 1

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "generator": "scripts/mailbox_manifest.py",
        "total_files": len(all_entries),
        "roots_scanned": MAILBOX_ROOTS,
        "root_file_counts": root_stats,
        "workstream_counts": ws_counts,
        "files": all_entries,
    }


def load_existing_manifest(manifest_path: Path) -> dict | None:
    """Load the previous manifest if it exists."""
    if not manifest_path.is_file():
        return None
    with open(manifest_path, encoding="utf-8") as f:
        return json.load(f)


def compute_diff(old: dict | None, new: dict) -> dict:
    """Compare two manifests and report additions, removals, and modifications."""
    if old is None:
        return {
            "added": [e["path"] for e in new["files"]],
            "removed": [],
            "modified": [],
            "unchanged": 0,
        }

    old_map = {e["path"]: e for e in old.get("files", [])}
    new_map = {e["path"]: e for e in new["files"]}

    added = sorted(set(new_map) - set(old_map))
    removed = sorted(set(old_map) - set(new_map))
    modified = []
    unchanged = 0

    for path in sorted(set(old_map) & set(new_map)):
        if old_map[path]["sha256"] != new_map[path]["sha256"]:
            modified.append(path)
        else:
            unchanged += 1

    return {
        "added": added,
        "removed": removed,
        "modified": modified,
        "unchanged": unchanged,
    }


def prune_manifest(manifest: dict, repo_root: Path, log) -> dict:
    """Remove entries for files that no longer exist on disk."""
    surviving = []
    pruned = []
    for entry in manifest.get("files", []):
        full_path = repo_root / entry["path"]
        if full_path.is_file():
            surviving.append(entry)
        else:
            pruned.append(entry["path"])
            log.info("Pruned: %s (file deleted)", entry["path"])

    manifest["files"] = surviving
    manifest["total_files"] = len(surviving)

    # Recalculate counts
    root_stats: dict[str, int] = {}
    ws_counts: dict[str, int] = {}
    for e in surviving:
        root_stats[e["root"]] = root_stats.get(e["root"], 0) + 1
        ws_counts[e["workstream"]] = ws_counts.get(e["workstream"], 0) + 1
    manifest["root_file_counts"] = root_stats
    manifest["workstream_counts"] = ws_counts
    manifest["pruned_at"] = datetime.now(tz=timezone.utc).isoformat()

    return manifest


def main() -> int:
    configure_utf8_output()

    parser = argparse.ArgumentParser(
        description="Mailbox manifest tracker — inventory mailbox files without git tracking."
    )
    parser.add_argument("--diff", action="store_true", help="Show changes since last manifest")
    parser.add_argument("--check", action="store_true", help="Exit 1 if manifest is stale")
    parser.add_argument("--prune", action="store_true", help="Remove entries for deleted files")
    parser.add_argument("--verbose", "-v", action="store_true", help="Debug logging")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress info output")
    parser.add_argument("--output", "-o", type=Path, help="Override manifest output path")
    args = parser.parse_args()

    log = setup_logging(verbose=args.verbose, quiet=args.quiet)
    repo_root = find_repo_root()
    manifest_path = args.output or (repo_root / "claude-codex-gemini" / MANIFEST_FILENAME)

    # Ensure output directory exists
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    old_manifest = load_existing_manifest(manifest_path)

    if args.prune:
        if old_manifest is None:
            log.error("No existing manifest to prune at %s", manifest_path)
            return 1
        pruned = prune_manifest(old_manifest, repo_root, log)
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(pruned, f, indent=2, ensure_ascii=False)
        log.info("Manifest pruned → %s (%d files remain)", manifest_path, pruned["total_files"])
        return 0

    new_manifest = build_manifest(repo_root, log)
    diff = compute_diff(old_manifest, new_manifest)

    if args.check:
        is_stale = bool(diff["added"] or diff["removed"] or diff["modified"])
        if is_stale:
            print(f"STALE: +{len(diff['added'])} -{len(diff['removed'])} ~{len(diff['modified'])}")
            return 1
        print(f"OK: {new_manifest['total_files']} files tracked, no changes")
        return 0

    if args.diff:
        print(json.dumps(diff, indent=2, ensure_ascii=False))
        if not diff["added"] and not diff["removed"] and not diff["modified"]:
            print(f"\nNo changes ({diff['unchanged']} files unchanged)")
        else:
            for p in diff["added"]:
                print(f"  + {p}")
            for p in diff["removed"]:
                print(f"  - {p}")
            for p in diff["modified"]:
                print(f"  ~ {p}")
        return 0

    # Default: scan and write
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(new_manifest, f, indent=2, ensure_ascii=False)

    # Summary
    print(f"Manifest written → {manifest_path.relative_to(repo_root)}")
    print(f"  Total files: {new_manifest['total_files']}")
    for root, count in sorted(new_manifest["root_file_counts"].items()):
        print(f"  {root}: {count}")
    print(f"  Workstreams: {', '.join(f'{k}({v})' for k, v in sorted(new_manifest['workstream_counts'].items()))}")

    if old_manifest:
        if diff["added"]:
            print(f"  New since last: +{len(diff['added'])}")
        if diff["removed"]:
            print(f"  Removed since last: -{len(diff['removed'])}")
        if diff["modified"]:
            print(f"  Modified since last: ~{len(diff['modified'])}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
