#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: embalm_before_edit.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🔥 THE FOUNDRY
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
The Bride's Pre-Mortem Preservation — snapshot files before editing.

Captures provenance snapshots of files prior to modification, enabling
diff/stitch recovery of changes via session-based delta extraction.

@SID:   EMBALM_BEFORE_EDIT_V1
@Shabti: CLI Script
@Purpose: Pre-mortem file preservation with provenance metadata.
"""

from __future__ import annotations


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Repo / vault paths
# ---------------------------------------------------------------------------

def find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for p in [cur, *cur.parents]:
        if (p / "pyproject.toml").exists() and (p / "AGENTS.md").exists():
            return p
    raise SystemExit("Could not locate repo root.")


REPO_ROOT = find_repo_root(Path(__file__))
VAULT_ROOT = REPO_ROOT / "dumpster-dive" / "corpse-vault"
BEFORE_EDIT_DIR = VAULT_ROOT / "before-edit-experiments"


# Extension → language (shared with corpse_reviver.py)
EXT_TO_LANG: dict[str, str] = {
    ".rs": "rust", ".py": "python", ".ts": "typescript", ".tsx": "typescript",
    ".js": "javascript", ".jsx": "javascript", ".md": "markdown",
    ".toml": "config", ".yaml": "config", ".yml": "config", ".json": "config",
    ".html": "html", ".htm": "html", ".css": "css", ".scss": "css",
    ".ps1": "shell", ".sh": "shell", ".bash": "shell", ".bat": "shell",
    ".cmd": "shell", ".sql": "sql", ".lua": "lua", ".rb": "ruby",
    ".go": "go", ".c": "c", ".h": "c", ".cpp": "cpp", ".hpp": "cpp",
    ".zig": "zig", ".wgsl": "wgsl", ".glsl": "glsl", ".hlsl": "hlsl",
}


def lang_for_file(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    return EXT_TO_LANG.get(ext, "unknown")


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        capture_output=True, text=True,
        cwd=str(REPO_ROOT),
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Snapshot creation
# ---------------------------------------------------------------------------

def snapshot_file(filepath: Path, session_dir: Path) -> dict | None:
    """Snapshot a single file into the session directory. Returns provenance dict."""
    if not filepath.exists():
        print(f"  SKIP (not found): {filepath}")
        return None

    content = filepath.read_bytes()
    if len(content) == 0:
        print(f"  SKIP (empty): {filepath}")
        return None

    rel = filepath.resolve().relative_to(REPO_ROOT.resolve())
    lang = lang_for_file(filepath.name)
    h = file_hash(content)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    # Organize: session_dir / language / hash_filename.snapshot
    lang_dir = session_dir / lang
    lang_dir.mkdir(parents=True, exist_ok=True)

    safe_name = filepath.name.replace(" ", "_")
    snapshot_name = f"{h}_{safe_name}.snapshot"
    provenance_name = f"{h}_{safe_name}.provenance.json"

    snapshot_path = lang_dir / snapshot_name
    provenance_path = lang_dir / provenance_name

    # Don't re-snapshot identical content in same session
    if snapshot_path.exists():
        print(f"  SKIP (already snapshotted): {rel}")
        return None

    # Write snapshot
    shutil.copy2(filepath, snapshot_path)

    # Get git metadata
    try:
        head_sha = git("rev-parse", "HEAD")
    except RuntimeError:
        head_sha = "unknown"

    try:
        status = git("status", "--porcelain", str(rel))
    except RuntimeError:
        status = "unknown"

    # Line count, structural landmarks
    text_content = content.decode("utf-8", errors="replace")
    lines = text_content.splitlines()
    line_count = len(lines)

    # Extract structural landmarks (functions, classes, headers)
    landmarks = extract_landmarks(text_content, lang)

    provenance = {
        "hash": h,
        "source_file": str(rel),
        "language": lang,
        "byte_size": len(content),
        "line_count": line_count,
        "snapshot_at": ts,
        "head_commit": head_sha,
        "git_status": status or "clean",
        "landmarks": landmarks,
        "snapshot_path": str(snapshot_path.relative_to(BEFORE_EDIT_DIR)),
    }

    provenance_path.write_text(
        json.dumps(provenance, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"  EMBALMED: {rel} → {lang}/{snapshot_name} ({line_count} lines, {len(content):,} bytes)")
    return provenance


def extract_landmarks(content: str, lang: str) -> list[dict]:
    """Extract structural landmarks from file content for indexing."""
    import re

    landmarks: list[dict] = []
    lines = content.splitlines()

    # Language-specific patterns
    patterns: dict[str, list[tuple[str, str]]] = {
        "python": [
            (r"^\s*(def\s+\w+)", "function"),
            (r"^\s*(class\s+\w+)", "class"),
        ],
        "rust": [
            (r"^\s*(pub\s+)?(fn\s+\w+)", "function"),
            (r"^\s*(pub\s+)?(struct\s+\w+)", "struct"),
            (r"^\s*(pub\s+)?(enum\s+\w+)", "enum"),
            (r"^\s*(pub\s+)?(impl\s+\w+)", "impl"),
            (r"^\s*(pub\s+)?(mod\s+\w+)", "module"),
        ],
        "typescript": [
            (r"^\s*(export\s+)?(function\s+\w+|const\s+\w+\s*=\s*(?:async\s+)?\()", "function"),
            (r"^\s*(export\s+)?(class\s+\w+)", "class"),
            (r"^\s*(export\s+)?(interface\s+\w+)", "interface"),
            (r"^\s*(export\s+)?(type\s+\w+)", "type"),
        ],
        "javascript": [
            (r"^\s*(export\s+)?(function\s+\w+|const\s+\w+\s*=\s*(?:async\s+)?\()", "function"),
            (r"^\s*(export\s+)?(class\s+\w+)", "class"),
        ],
        "markdown": [
            (r"^(#{1,6}\s+.+)", "heading"),
        ],
        "shell": [
            (r"^\s*(function\s+\w+|\w+\s*\(\)\s*\{)", "function"),
        ],
    }

    # Use language patterns or fall back to markdown headings
    active_patterns = patterns.get(lang, patterns.get("markdown", []))

    for i, line in enumerate(lines, 1):
        for pattern, kind in active_patterns:
            m = re.match(pattern, line)
            if m:
                landmarks.append({
                    "line": i,
                    "kind": kind,
                    "text": m.group(0).strip()[:120],
                })
                break

    return landmarks


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------

def create_session_dir(label: str | None = None) -> Path:
    """Create a timestamped session directory under before-edit-experiments."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    name = f"{ts}"
    if label:
        # Sanitize label for filesystem
        safe_label = "".join(c if c.isalnum() or c in "-_" else "_" for c in label)
        name = f"{ts}_{safe_label[:40]}"

    session_dir = BEFORE_EDIT_DIR / name
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


def write_session_manifest(session_dir: Path, snapshots: list[dict]) -> None:
    """Write a session-level manifest indexing all snapshots."""
    manifest = {
        "session": session_dir.name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "snapshot_count": len(snapshots),
        "total_bytes": sum(s.get("byte_size", 0) for s in snapshots),
        "total_lines": sum(s.get("line_count", 0) for s in snapshots),
        "languages": sorted(set(s.get("language", "unknown") for s in snapshots)),
        "files": [s.get("source_file", "?") for s in snapshots],
        "snapshots": snapshots,
    }
    manifest_path = session_dir / "session_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\nSession manifest: {manifest_path.relative_to(REPO_ROOT)}")


# ---------------------------------------------------------------------------
# Diff mode — compare snapshot to current state
# ---------------------------------------------------------------------------

def cmd_diff(session_name: str) -> None:
    """Compare current file state against a prior snapshot session."""
    session_dir = BEFORE_EDIT_DIR / session_name
    if not session_dir.exists():
        # Try partial match
        candidates = sorted(BEFORE_EDIT_DIR.iterdir()) if BEFORE_EDIT_DIR.exists() else []
        matches = [c for c in candidates if c.is_dir() and session_name in c.name]
        if len(matches) == 1:
            session_dir = matches[0]
        elif matches:
            print(f"Ambiguous session name. Matches: {[m.name for m in matches]}")
            return
        else:
            print(f"Session not found: {session_name}")
            if candidates:
                print(f"Available sessions: {[c.name for c in candidates if c.is_dir()]}")
            return

    manifest_path = session_dir / "session_manifest.json"
    if not manifest_path.exists():
        print(f"No manifest in session: {session_dir.name}")
        return

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    snapshots = manifest.get("snapshots", [])

    print(f"Comparing session '{session_dir.name}' ({len(snapshots)} files) against current state:\n")

    for snap in snapshots:
        source = REPO_ROOT / snap["source_file"]
        snapshot_path = BEFORE_EDIT_DIR / snap["snapshot_path"]

        if not source.exists():
            print(f"  DELETED: {snap['source_file']} (was {snap['line_count']} lines)")
            continue

        if not snapshot_path.exists():
            print(f"  MISSING SNAPSHOT: {snap['snapshot_path']}")
            continue

        current_content = source.read_bytes()
        snapshot_content = snapshot_path.read_bytes()

        if current_content == snapshot_content:
            print(f"  UNCHANGED: {snap['source_file']}")
        else:
            current_lines = len(current_content.decode("utf-8", errors="replace").splitlines())
            delta = current_lines - snap["line_count"]
            sign = "+" if delta > 0 else ""
            print(f"  CHANGED: {snap['source_file']} ({snap['line_count']} → {current_lines} lines, {sign}{delta})")


# ---------------------------------------------------------------------------
# List sessions
# ---------------------------------------------------------------------------

def cmd_list_sessions() -> None:
    """List all before-edit snapshot sessions."""
    if not BEFORE_EDIT_DIR.exists():
        print("No before-edit sessions found.")
        return

    sessions = sorted(
        (d for d in BEFORE_EDIT_DIR.iterdir() if d.is_dir()),
        key=lambda d: d.name,
        reverse=True,
    )

    if not sessions:
        print("No before-edit sessions found.")
        return

    print(f"Before-edit sessions ({len(sessions)}):\n")
    for s in sessions:
        manifest_path = s / "session_manifest.json"
        if manifest_path.exists():
            m = json.loads(manifest_path.read_text(encoding="utf-8"))
            count = m.get("snapshot_count", 0)
            total = m.get("total_bytes", 0)
            langs = ", ".join(m.get("languages", []))
            print(f"  {s.name}  ({count} files, {total:,} bytes) [{langs}]")
        else:
            print(f"  {s.name}  (no manifest)")


# ---------------------------------------------------------------------------
# Stitch mode — extract delta fragments from snapshot vs current state
# ---------------------------------------------------------------------------

def cmd_stitch(session_name: str, output_dir: Path | None = None) -> None:
    """Extract changed regions between a snapshot session and current file state.

    Produces .delta files containing only the lines that differ — candidate
    data for ankhological emigration injection or suture composites.
    """
    session_dir = BEFORE_EDIT_DIR / session_name
    if not session_dir.exists():
        candidates = sorted(BEFORE_EDIT_DIR.iterdir()) if BEFORE_EDIT_DIR.exists() else []
        matches = [c for c in candidates if c.is_dir() and session_name in c.name]
        if len(matches) == 1:
            session_dir = matches[0]
        elif matches:
            print(f"Ambiguous session name. Matches: {[m.name for m in matches]}")
            return
        else:
            print(f"Session not found: {session_name}")
            return

    manifest_path = session_dir / "session_manifest.json"
    if not manifest_path.exists():
        print(f"No manifest in session: {session_dir.name}")
        return

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    snapshots = manifest.get("snapshots", [])

    # Output goes into session_dir/deltas/ by default
    delta_dir = output_dir or (session_dir / "deltas")
    delta_dir.mkdir(parents=True, exist_ok=True)

    print(f"Stitching deltas from session '{session_dir.name}':\n")
    delta_count = 0

    for snap in snapshots:
        source = REPO_ROOT / snap["source_file"]
        snapshot_path = BEFORE_EDIT_DIR / snap["snapshot_path"]

        if not source.exists() or not snapshot_path.exists():
            continue

        old_lines = snapshot_path.read_text(encoding="utf-8", errors="replace").splitlines()
        new_lines = source.read_text(encoding="utf-8", errors="replace").splitlines()

        if old_lines == new_lines:
            continue

        # Extract added/changed line ranges
        import difflib
        differ = difflib.unified_diff(
            old_lines, new_lines,
            fromfile=f"before/{snap['source_file']}",
            tofile=f"after/{snap['source_file']}",
            lineterm="",
        )
        diff_text = "\n".join(differ)

        if not diff_text.strip():
            continue

        lang = snap.get("language", "unknown")
        lang_dir = delta_dir / lang
        lang_dir.mkdir(parents=True, exist_ok=True)

        safe_name = Path(snap["source_file"]).name.replace(" ", "_")
        delta_name = f"{snap['hash']}_{safe_name}.delta"
        delta_path = lang_dir / delta_name

        # Write the unified diff
        delta_path.write_text(diff_text, encoding="utf-8")

        added = sum(1 for l in diff_text.splitlines() if l.startswith("+") and not l.startswith("+++"))
        removed = sum(1 for l in diff_text.splitlines() if l.startswith("-") and not l.startswith("---"))
        print(f"  DELTA: {snap['source_file']} (+{added}/-{removed} lines) → {lang}/{delta_name}")
        delta_count += 1

    if delta_count:
        print(f"\nStitched {delta_count} delta(s) into {delta_dir.relative_to(REPO_ROOT)}")
    else:
        print("\nNo deltas found (all files unchanged).")


# ---------------------------------------------------------------------------
# Quick embalm — programmatic API for agent integration
# ---------------------------------------------------------------------------

def quick_embalm(filepaths: list[str | Path], label: str = "auto") -> Path | None:
    """Programmatic entry point: snapshot files and return session dir.

    Called by agents/scripts to embalm files before editing them,
    without going through CLI parsing. Returns the session directory
    path, or None if nothing was snapshotted.
    """
    session_dir = create_session_dir(label)
    snapshots: list[dict] = []
    for f in filepaths:
        fp = Path(f)
        if not fp.is_absolute():
            fp = REPO_ROOT / fp
        result = snapshot_file(fp, session_dir)
        if result:
            snapshots.append(result)
    if snapshots:
        write_session_manifest(session_dir, snapshots)
        return session_dir
    # Clean up empty session
    if not any(session_dir.iterdir()):
        session_dir.rmdir()
    return None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="embalm_before_edit",
        description="The Bride's Pre-Mortem Preservation — snapshot files before editing.",
    )
    sub = p.add_subparsers(dest="command")

    # snapshot (default when positional args given)
    snap = sub.add_parser("snapshot", help="Snapshot specific files before editing.")
    snap.add_argument("files", nargs="+", help="Files to snapshot.")
    snap.add_argument("--label", "-l", help="Label for this snapshot session.")

    # staged
    stg = sub.add_parser("staged", help="Snapshot all files currently staged in git.")
    stg.add_argument("--label", "-l", help="Label for this snapshot session.")

    # diff
    d = sub.add_parser("diff", help="Compare current state against a prior snapshot.")
    d.add_argument("session", help="Session directory name (or partial match).")

    # list
    sub.add_parser("list", help="List all before-edit snapshot sessions.")

    # stitch
    st = sub.add_parser("stitch", help="Extract delta fragments between snapshot and current state.")
    st.add_argument("session", help="Session directory name (or partial match).")
    st.add_argument("--output", "-o", help="Output directory for delta files (default: session/deltas/).")

    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        raise SystemExit(1)
    if args.command == "snapshot":
        result = quick_embalm(args.files, label=args.label or "manual")
        if result:
            print(f"\nSession: {result.relative_to(REPO_ROOT)}")
        else:
            print("No files snapshotted.")
    elif args.command == "staged":
        staged_output = git("diff", "--cached", "--name-only")
        if not staged_output.strip():
            print("No staged files.")
            return
        files = [f.strip() for f in staged_output.splitlines() if f.strip()]
        result = quick_embalm(files, label=args.label or "staged")
        if result:
            print(f"\nSession: {result.relative_to(REPO_ROOT)}")
        else:
            print("No staged files snapshotted.")
    elif args.command == "diff":
        cmd_diff(args.session)
    elif args.command == "list":
        cmd_list_sessions()
    elif args.command == "stitch":
        output = Path(args.output) if args.output else None
        cmd_stitch(args.session, output_dir=output)


if __name__ == "__main__":
    main()
