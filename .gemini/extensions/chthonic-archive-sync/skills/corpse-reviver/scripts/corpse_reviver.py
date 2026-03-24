#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: corpse_reviver.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🔥 THE FOUNDRY
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Corpse Reviver — necromancy pipeline for dead code.

Harvest dead code from git history, stashes, reflog, dead branches, commented
blocks, orphaned files, gitignored treasures, and TODO/FIXME graffiti.
Embalm with provenance metadata, classify by language, vault for reanimation.

@SID:  CORPSE_REVIVER_V2
@Shabti: Utility
@Purpose:       Corpse Reviver — necromancy pipeline for dead code.

Invocation:
  uv run .codex/skills/corpse-reviver/scripts/corpse_reviver.py harvest --since 30d
  uv run .codex/skills/corpse-reviver/scripts/corpse_reviver.py harvest --stashes
  uv run .codex/skills/corpse-reviver/scripts/corpse_reviver.py harvest --comments
  uv run .codex/skills/corpse-reviver/scripts/corpse_reviver.py harvest --reflog
  uv run .codex/skills/corpse-reviver/scripts/corpse_reviver.py harvest --dead-branches
  uv run .codex/skills/corpse-reviver/scripts/corpse_reviver.py harvest --orphans
  uv run .codex/skills/corpse-reviver/scripts/corpse_reviver.py harvest --gitignored
  uv run .codex/skills/corpse-reviver/scripts/corpse_reviver.py harvest --graffiti
  uv run .codex/skills/corpse-reviver/scripts/corpse_reviver.py harvest --all
  uv run .codex/skills/corpse-reviver/scripts/corpse_reviver.py classify
  uv run .codex/skills/corpse-reviver/scripts/corpse_reviver.py reanimate --query "handler"
  uv run .codex/skills/corpse-reviver/scripts/corpse_reviver.py manifest
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence


# ---------------------------------------------------------------------------
# Repo root discovery
# ---------------------------------------------------------------------------

def find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for p in [cur, *cur.parents]:
        if (p / "pyproject.toml").exists() and (p / "AGENTS.md").exists():
            return p
    raise SystemExit(
        "Could not locate repo root (expected pyproject.toml + AGENTS.md)."
    )


REPO_ROOT = find_repo_root(Path(__file__))
VAULT_ROOT = REPO_ROOT / "dumpster-dive" / "corpse-vault"
MANIFEST_PATH = VAULT_ROOT / "manifest.json"


# ---------------------------------------------------------------------------
# Language / extension mapping
# ---------------------------------------------------------------------------

EXT_TO_LANG: dict[str, str] = {
    ".rs": "rust",
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".md": "markdown",
    ".toml": "config",
    ".yaml": "config",
    ".yml": "config",
    ".json": "config",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".scss": "css",
    ".ps1": "shell",
    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",
    ".bat": "shell",
    ".cmd": "shell",
    ".sql": "sql",
    ".lua": "lua",
    ".rb": "ruby",
    ".go": "go",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".zig": "zig",
    ".wgsl": "wgsl",
    ".glsl": "glsl",
    ".hlsl": "hlsl",
}


def lang_for_file(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    return EXT_TO_LANG.get(ext, "unknown")


# ---------------------------------------------------------------------------
# Comment-block detection patterns (per language family)
# ---------------------------------------------------------------------------

COMMENT_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    "line": [
        # 3+ consecutive single-line comments with code-like content
        re.compile(
            r"(?m)^[ \t]*((?://|#|--|;;)[ \t]*\S.*\n){3,}",
        ),
    ],
    "block": [
        # C-style block comments containing code indicators
        re.compile(
            r"/\*[\s\S]*?(?:fn |def |class |let |const |var |return |import )[\s\S]*?\*/",
        ),
        # HTML comments containing code
        re.compile(
            r"<!--[\s\S]*?(?:function|class |def |import )[\s\S]*?-->",
        ),
    ],
}


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Fragment:
    content: str
    source_file: str
    commit: str
    author: str
    date: str
    cause_of_death: str  # deleted_in_commit | stash_abandoned | commented_out
    language: str
    extension: str
    lines_start: int
    lines_end: int
    byte_size: int = 0
    fragment_hash: str = ""
    fragment_file: str = ""

    def __post_init__(self) -> None:
        self.byte_size = len(self.content.encode("utf-8"))
        self.fragment_hash = hashlib.sha256(
            self.content.encode("utf-8")
        ).hexdigest()[:16]


@dataclass
class Manifest:
    fragments: list[dict] = field(default_factory=list)
    harvested_at: str = ""
    total_fragments: int = 0
    total_bytes: int = 0

    def to_dict(self) -> dict:
        return {
            "harvested_at": self.harvested_at,
            "total_fragments": self.total_fragments,
            "total_bytes": self.total_bytes,
            "fragments": self.fragments,
        }


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=check,
    )
    return result.stdout


def parse_since(since: str) -> str:
    """Convert '30d' / '7d' / '90d' to git --since format."""
    m = re.match(r"^(\d+)([dhm])$", since)
    if not m:
        return since  # pass through as-is for git to interpret
    num, unit = m.group(1), m.group(2)
    unit_map = {"d": "days", "h": "hours", "m": "months"}
    return f"{num}.{unit_map[unit]}.ago"


# ---------------------------------------------------------------------------
# Harvest: deleted lines from git log
# ---------------------------------------------------------------------------

def harvest_deleted_from_commits(since: str, max_commits: int = 200) -> list[Fragment]:
    """Extract deleted lines (the '-' lines in diffs) from recent commits."""
    since_arg = parse_since(since)
    # Get commits with file-level info
    log_output = git(
        "log", f"--since={since_arg}", "--pretty=format:%H|%an|%aI",
        f"--max-count={max_commits}", "--diff-filter=MD",
        "--name-only",
    )
    if not log_output.strip():
        return []

    fragments: list[Fragment] = []
    commits_seen: set[str] = set()

    # Parse commits
    for block in log_output.strip().split("\n\n"):
        lines = block.strip().split("\n")
        if not lines or "|" not in lines[0]:
            continue
        header_parts = lines[0].split("|", 2)
        if len(header_parts) < 3:
            continue
        commit_hash, author, date = header_parts
        if commit_hash in commits_seen:
            continue
        commits_seen.add(commit_hash)

        # Get the actual diff for this commit (deleted lines only)
        diff = git("diff", f"{commit_hash}~1..{commit_hash}", "--unified=0", check=False)
        if not diff.strip():
            continue

        current_file = ""
        deleted_lines: list[str] = []
        line_start = 0

        for dline in diff.split("\n"):
            if dline.startswith("diff --git"):
                # Flush previous file's deletions
                if deleted_lines and current_file:
                    content = "\n".join(deleted_lines)
                    if len(content.strip()) > 20:  # skip trivial deletions
                        fragments.append(Fragment(
                            content=content,
                            source_file=current_file,
                            commit=commit_hash[:8],
                            author=author,
                            date=date,
                            cause_of_death="deleted_in_commit",
                            language=lang_for_file(current_file),
                            extension=Path(current_file).suffix,
                            lines_start=line_start,
                            lines_end=line_start + len(deleted_lines),
                        ))
                deleted_lines = []
                line_start = 0
                # Extract filename from diff header
                parts = dline.split(" b/", 1)
                current_file = parts[1] if len(parts) > 1 else ""
            elif dline.startswith("@@ "):
                # Parse hunk header for line numbers
                m = re.search(r"-(\d+)", dline)
                if m:
                    line_start = int(m.group(1))
            elif dline.startswith("-") and not dline.startswith("---"):
                deleted_lines.append(dline[1:])  # strip the '-' prefix
            elif dline.startswith("+") or dline.startswith(" "):
                # Flush on context/addition boundary
                if deleted_lines and current_file:
                    content = "\n".join(deleted_lines)
                    if len(content.strip()) > 20:
                        fragments.append(Fragment(
                            content=content,
                            source_file=current_file,
                            commit=commit_hash[:8],
                            author=author,
                            date=date,
                            cause_of_death="deleted_in_commit",
                            language=lang_for_file(current_file),
                            extension=Path(current_file).suffix,
                            lines_start=line_start,
                            lines_end=line_start + len(deleted_lines),
                        ))
                deleted_lines = []

        # Flush last file
        if deleted_lines and current_file:
            content = "\n".join(deleted_lines)
            if len(content.strip()) > 20:
                fragments.append(Fragment(
                    content=content,
                    source_file=current_file,
                    commit=commit_hash[:8],
                    author=author,
                    date=date,
                    cause_of_death="deleted_in_commit",
                    language=lang_for_file(current_file),
                    extension=Path(current_file).suffix,
                    lines_start=line_start,
                    lines_end=line_start + len(deleted_lines),
                ))

    return fragments


# ---------------------------------------------------------------------------
# Harvest: stashes
# ---------------------------------------------------------------------------

def harvest_stashes() -> list[Fragment]:
    """Extract content from git stashes."""
    stash_list = git("stash", "list", check=False).strip()
    if not stash_list:
        return []

    fragments: list[Fragment] = []
    for line in stash_list.split("\n"):
        if not line.strip():
            continue
        # stash@{0}: WIP on main: abc1234 message
        m = re.match(r"(stash@\{\d+\})", line)
        if not m:
            continue
        stash_ref = m.group(1)

        # Get diff of stash against its parent
        diff = git("stash", "show", "-p", stash_ref, check=False)
        if not diff.strip():
            continue

        current_file = ""
        added_lines: list[str] = []
        line_start = 0

        for dline in diff.split("\n"):
            if dline.startswith("diff --git"):
                if added_lines and current_file:
                    content = "\n".join(added_lines)
                    if len(content.strip()) > 20:
                        fragments.append(Fragment(
                            content=content,
                            source_file=current_file,
                            commit=stash_ref,
                            author="(stash)",
                            date=datetime.now(timezone.utc).isoformat(),
                            cause_of_death="stash_abandoned",
                            language=lang_for_file(current_file),
                            extension=Path(current_file).suffix,
                            lines_start=line_start,
                            lines_end=line_start + len(added_lines),
                        ))
                added_lines = []
                line_start = 0
                parts = dline.split(" b/", 1)
                current_file = parts[1] if len(parts) > 1 else ""
            elif dline.startswith("@@ "):
                m2 = re.search(r"\+(\d+)", dline)
                if m2:
                    line_start = int(m2.group(1))
            elif dline.startswith("+") and not dline.startswith("+++"):
                added_lines.append(dline[1:])

        if added_lines and current_file:
            content = "\n".join(added_lines)
            if len(content.strip()) > 20:
                fragments.append(Fragment(
                    content=content,
                    source_file=current_file,
                    commit=stash_ref,
                    author="(stash)",
                    date=datetime.now(timezone.utc).isoformat(),
                    cause_of_death="stash_abandoned",
                    language=lang_for_file(current_file),
                    extension=Path(current_file).suffix,
                    lines_start=line_start,
                    lines_end=line_start + len(added_lines),
                ))

    return fragments


# ---------------------------------------------------------------------------
# Harvest: commented-out code in tracked files
# ---------------------------------------------------------------------------

CODE_INDICATORS = re.compile(
    r"(?:fn |def |class |let |const |var |return |import |from |use |pub |"
    r"async |await |struct |enum |impl |match |if |for |while |loop )"
)


def harvest_commented_code() -> list[Fragment]:
    """Scan tracked files for commented-out code blocks."""
    tracked = git("ls-files").strip().split("\n")
    fragments: list[Fragment] = []

    for filepath_str in tracked:
        filepath = REPO_ROOT / filepath_str
        if not filepath.is_file():
            continue
        # Only scan code files
        lang = lang_for_file(filepath_str)
        if lang in ("unknown", "markdown", "config"):
            continue
        try:
            text = filepath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # Check line-comment blocks (3+ consecutive comment lines with code-like content)
        lines = text.split("\n")
        block: list[str] = []
        block_start = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            is_comment = (
                stripped.startswith("//")
                or stripped.startswith("#")
                and not stripped.startswith("#!")
                and not stripped.startswith("# -*-")
            )
            if is_comment and len(stripped) > 3:
                if not block:
                    block_start = i + 1
                # Strip comment prefix for content check
                content_part = re.sub(r"^(//|#)\s?", "", stripped)
                block.append(content_part)
            else:
                if len(block) >= 3:
                    joined = "\n".join(block)
                    if CODE_INDICATORS.search(joined):
                        fragments.append(Fragment(
                            content=joined,
                            source_file=filepath_str,
                            commit="(working-tree)",
                            author="(commented)",
                            date=datetime.now(timezone.utc).isoformat(),
                            cause_of_death="commented_out",
                            language=lang,
                            extension=filepath.suffix,
                            lines_start=block_start,
                            lines_end=block_start + len(block),
                        ))
                block = []

        # Flush trailing block
        if len(block) >= 3:
            joined = "\n".join(block)
            if CODE_INDICATORS.search(joined):
                fragments.append(Fragment(
                    content=joined,
                    source_file=filepath_str,
                    commit="(working-tree)",
                    author="(commented)",
                    date=datetime.now(timezone.utc).isoformat(),
                    cause_of_death="commented_out",
                    language=lang,
                    extension=filepath.suffix,
                    lines_start=block_start,
                    lines_end=block_start + len(block),
                ))

    return fragments


# ---------------------------------------------------------------------------
# Harvest: reflog casualties (force-push, reset --hard, amend)
# ---------------------------------------------------------------------------

def harvest_reflog(max_entries: int = 100) -> list[Fragment]:
    """Extract code from orphaned reflog entries not reachable from HEAD."""
    reflog = git("reflog", "--pretty=format:%H|%an|%aI|%gs", f"-n{max_entries}", check=False)
    if not reflog.strip():
        return []

    fragments: list[Fragment] = []
    reachable = set(git("rev-list", "HEAD", f"--max-count={max_entries}", check=False).strip().split("\n"))

    for line in reflog.strip().split("\n"):
        parts = line.split("|", 3)
        if len(parts) < 4:
            continue
        commit_hash, author, date, subject = parts
        if commit_hash in reachable:
            continue  # still reachable — not a casualty

        diff = git("diff", f"{commit_hash}~1..{commit_hash}", "--unified=0", check=False)
        if not diff.strip():
            continue

        current_file = ""
        deleted_lines: list[str] = []
        line_start = 0

        for dline in diff.split("\n"):
            if dline.startswith("diff --git"):
                if deleted_lines and current_file:
                    content = "\n".join(deleted_lines)
                    if len(content.strip()) > 20:
                        fragments.append(Fragment(
                            content=content,
                            source_file=current_file,
                            commit=commit_hash[:8],
                            author=author,
                            date=date,
                            cause_of_death="reflog_casualty",
                            language=lang_for_file(current_file),
                            extension=Path(current_file).suffix,
                            lines_start=line_start,
                            lines_end=line_start + len(deleted_lines),
                        ))
                deleted_lines = []
                line_start = 0
                file_parts = dline.split(" b/", 1)
                current_file = file_parts[1] if len(file_parts) > 1 else ""
            elif dline.startswith("@@ "):
                m = re.search(r"-(\d+)", dline)
                if m:
                    line_start = int(m.group(1))
            elif dline.startswith("-") and not dline.startswith("---"):
                deleted_lines.append(dline[1:])

        if deleted_lines and current_file:
            content = "\n".join(deleted_lines)
            if len(content.strip()) > 20:
                fragments.append(Fragment(
                    content=content,
                    source_file=current_file,
                    commit=commit_hash[:8],
                    author=author,
                    date=date,
                    cause_of_death="reflog_casualty",
                    language=lang_for_file(current_file),
                    extension=Path(current_file).suffix,
                    lines_start=line_start,
                    lines_end=line_start + len(deleted_lines),
                ))

    return fragments


# ---------------------------------------------------------------------------
# Harvest: dead branches (merged/deleted with unique code)
# ---------------------------------------------------------------------------

def harvest_dead_branches() -> list[Fragment]:
    """Harvest unique code from branches already merged into HEAD."""
    merged = git("branch", "--merged", "HEAD", check=False).strip()
    if not merged:
        return []

    fragments: list[Fragment] = []
    current_branch = git("rev-parse", "--abbrev-ref", "HEAD", check=False).strip()

    for line in merged.split("\n"):
        branch = line.strip().lstrip("* ")
        if not branch or branch == current_branch or branch == "main":
            continue

        # Diff branch tip against merge-base to find unique code
        merge_base = git("merge-base", "HEAD", branch, check=False).strip()
        if not merge_base:
            continue
        diff = git("diff", f"{merge_base}..{branch}", "--unified=0", check=False)
        if not diff.strip():
            continue

        current_file = ""
        added_lines: list[str] = []
        line_start = 0

        for dline in diff.split("\n"):
            if dline.startswith("diff --git"):
                if added_lines and current_file:
                    content = "\n".join(added_lines)
                    if len(content.strip()) > 20:
                        fragments.append(Fragment(
                            content=content,
                            source_file=current_file,
                            commit=f"branch:{branch}",
                            author="(branch)",
                            date=datetime.now(timezone.utc).isoformat(),
                            cause_of_death="dead_branch",
                            language=lang_for_file(current_file),
                            extension=Path(current_file).suffix,
                            lines_start=line_start,
                            lines_end=line_start + len(added_lines),
                        ))
                added_lines = []
                line_start = 0
                file_parts = dline.split(" b/", 1)
                current_file = file_parts[1] if len(file_parts) > 1 else ""
            elif dline.startswith("@@ "):
                m = re.search(r"\+(\d+)", dline)
                if m:
                    line_start = int(m.group(1))
            elif dline.startswith("+") and not dline.startswith("+++"):
                added_lines.append(dline[1:])

        if added_lines and current_file:
            content = "\n".join(added_lines)
            if len(content.strip()) > 20:
                fragments.append(Fragment(
                    content=content,
                    source_file=current_file,
                    commit=f"branch:{branch}",
                    author="(branch)",
                    date=datetime.now(timezone.utc).isoformat(),
                    cause_of_death="dead_branch",
                    language=lang_for_file(current_file),
                    extension=Path(current_file).suffix,
                    lines_start=line_start,
                    lines_end=line_start + len(added_lines),
                ))

    return fragments


# ---------------------------------------------------------------------------
# Harvest: orphaned files (untracked, not gitignored)
# ---------------------------------------------------------------------------

def harvest_orphans() -> list[Fragment]:
    """Harvest untracked files that git doesn't know about."""
    untracked = git("ls-files", "--others", "--exclude-standard", check=False).strip()
    if not untracked:
        return []

    fragments: list[Fragment] = []
    for filepath_str in untracked.split("\n"):
        filepath_str = filepath_str.strip()
        if not filepath_str:
            continue
        filepath = REPO_ROOT / filepath_str
        if not filepath.is_file() or filepath.stat().st_size > 500_000:
            continue  # skip dirs and huge files
        lang = lang_for_file(filepath_str)
        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if len(content.strip()) < 20:
            continue
        fragments.append(Fragment(
            content=content,
            source_file=filepath_str,
            commit="(untracked)",
            author="(orphan)",
            date=datetime.now(timezone.utc).isoformat(),
            cause_of_death="orphaned",
            language=lang,
            extension=filepath.suffix,
            lines_start=1,
            lines_end=content.count("\n") + 1,
        ))

    return fragments


# ---------------------------------------------------------------------------
# Harvest: gitignored treasures
# ---------------------------------------------------------------------------

def harvest_gitignored() -> list[Fragment]:
    """Harvest gitignored files that exist on disk but are invisible to git."""
    ignored = git("ls-files", "--others", "--ignored", "--exclude-standard", check=False).strip()
    if not ignored:
        return []

    fragments: list[Fragment] = []
    for filepath_str in ignored.split("\n"):
        filepath_str = filepath_str.strip()
        if not filepath_str:
            continue
        filepath = REPO_ROOT / filepath_str
        if not filepath.is_file() or filepath.stat().st_size > 200_000:
            continue
        lang = lang_for_file(filepath_str)
        if lang == "unknown":
            continue  # skip binary/unrecognized
        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if len(content.strip()) < 20:
            continue
        fragments.append(Fragment(
            content=content,
            source_file=filepath_str,
            commit="(gitignored)",
            author="(ignored)",
            date=datetime.now(timezone.utc).isoformat(),
            cause_of_death="gitignored",
            language=lang,
            extension=filepath.suffix,
            lines_start=1,
            lines_end=content.count("\n") + 1,
        ))

    return fragments


# ---------------------------------------------------------------------------
# Harvest: TODO/FIXME/HACK graffiti — marked for death
# ---------------------------------------------------------------------------

GRAFFITI_PATTERN = re.compile(
    r"(?m)^[ \t]*(?://|#|--|;;|/\*+|\*)?[ \t]*"
    r"(TODO|FIXME|HACK|XXX|DEPRECATED|TEMP|REMOVEME|CLEANUP)"
    r"[:\s](.+?)$"
)


def harvest_graffiti() -> list[Fragment]:
    """Scan tracked files for TODO/FIXME/HACK markers with context."""
    tracked = git("ls-files").strip().split("\n")
    fragments: list[Fragment] = []

    for filepath_str in tracked:
        filepath = REPO_ROOT / filepath_str
        if not filepath.is_file():
            continue
        lang = lang_for_file(filepath_str)
        if lang in ("unknown",):
            continue
        try:
            text = filepath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        lines = text.split("\n")
        for i, line in enumerate(lines):
            m = GRAFFITI_PATTERN.match(line)
            if not m:
                continue
            tag, comment = m.group(1), m.group(2).strip()
            # Grab 2 lines of context after the graffiti
            context_end = min(i + 3, len(lines))
            context = "\n".join(lines[i:context_end])
            if len(context.strip()) < 10:
                continue
            fragments.append(Fragment(
                content=context,
                source_file=filepath_str,
                commit="(working-tree)",
                author=f"(graffiti:{tag})",
                date=datetime.now(timezone.utc).isoformat(),
                cause_of_death="graffiti_marked",
                language=lang,
                extension=filepath.suffix,
                lines_start=i + 1,
                lines_end=context_end,
            ))

    return fragments


# ---------------------------------------------------------------------------
# Prowl: intercept code about to die (staged deletions)
# ---------------------------------------------------------------------------

def cmd_prowl() -> None:
    """Show code that is staged for deletion — the pre-mortem intercept."""
    diff = git("diff", "--cached", "--unified=0", check=False)
    if not diff.strip():
        print("Nothing staged. The wasteland is quiet.")
        return

    current_file = ""
    deleted_lines: list[str] = []
    dying_count = 0

    for dline in diff.split("\n"):
        if dline.startswith("diff --git"):
            if deleted_lines and current_file:
                dying_count += 1
                print(f"\n  [{lang_for_file(current_file)}] {current_file} — {len(deleted_lines)} line(s) about to die:")
                for dl in deleted_lines[:10]:
                    print(f"    - {dl}")
                if len(deleted_lines) > 10:
                    print(f"    ... and {len(deleted_lines) - 10} more.")
            deleted_lines = []
            file_parts = dline.split(" b/", 1)
            current_file = file_parts[1] if len(file_parts) > 1 else ""
        elif dline.startswith("-") and not dline.startswith("---"):
            deleted_lines.append(dline[1:])

    if deleted_lines and current_file:
        dying_count += 1
        print(f"\n  [{lang_for_file(current_file)}] {current_file} — {len(deleted_lines)} line(s) about to die:")
        for dl in deleted_lines[:10]:
            print(f"    - {dl}")
        if len(deleted_lines) > 10:
            print(f"    ... and {len(deleted_lines) - 10} more.")

    if dying_count:
        print(f"\n{dying_count} file(s) with staged deletions. Use 'harvest' to embalm before committing.")
    else:
        print("Staged changes contain no deletions. Nothing dying.")


# ---------------------------------------------------------------------------
# Suture: stitch fragments into composites
# ---------------------------------------------------------------------------

SUTURE_DIR = VAULT_ROOT / "sutures"


def cmd_suture(
    fragment_hashes: list[str] | None,
    lang: str | None,
    query: str | None,
    output: str | None,
) -> None:
    """Stitch fragments together into a composite file — the Bride's act."""
    if not MANIFEST_PATH.exists():
        print("No manifest found. Run 'harvest' first.")
        return

    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    all_frags = data.get("fragments", [])

    # Select fragments
    selected: list[dict] = []
    if fragment_hashes:
        hash_set = set(fragment_hashes)
        selected = [f for f in all_frags if f["hash"] in hash_set]
    else:
        for entry in all_frags:
            if lang and entry.get("language") != lang:
                continue
            if query:
                frag_path = VAULT_ROOT / entry["fragment_file"]
                if frag_path.exists():
                    content = frag_path.read_text(encoding="utf-8", errors="replace")
                    if query.lower() not in content.lower():
                        continue
                else:
                    continue
            selected.append(entry)

    if not selected:
        print("No fragments matched. Nothing to suture.")
        return

    # Read and stitch
    parts: list[str] = []
    for entry in selected[:50]:  # cap at 50 to avoid monsters
        frag_path = VAULT_ROOT / entry["fragment_file"]
        if not frag_path.exists():
            continue
        content = frag_path.read_text(encoding="utf-8", errors="replace")
        header = (
            f"# --- [{entry['language']}] from {entry['source_file']} "
            f"(L{entry['lines_start']}-{entry['lines_end']}, {entry['cause_of_death']}) ---"
        )
        parts.append(f"{header}\n{content}")

    composite = "\n\n".join(parts)

    # Write output
    SUTURE_DIR.mkdir(parents=True, exist_ok=True)
    if output:
        out_path = Path(output) if Path(output).is_absolute() else SUTURE_DIR / output
    else:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = SUTURE_DIR / f"bride_{ts}.txt"

    out_path.write_text(composite, encoding="utf-8")
    print(f"Sutured {len(parts)} fragment(s) into {out_path}")
    print(f"  Total size: {len(composite):,} bytes")

def embalm(fragments: list[Fragment]) -> Manifest:
    """Write fragments to the vault with provenance sidecars."""
    manifest = Manifest(
        harvested_at=datetime.now(timezone.utc).isoformat(),
    )

    seen_hashes: set[str] = set()

    # Load existing manifest to avoid duplicates
    if MANIFEST_PATH.exists():
        try:
            existing = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
            manifest.fragments = existing.get("fragments", [])
            seen_hashes = {f["hash"] for f in manifest.fragments}
        except (json.JSONDecodeError, KeyError):
            pass

    new_count = 0
    for frag in fragments:
        if frag.fragment_hash in seen_hashes:
            continue
        seen_hashes.add(frag.fragment_hash)

        # Determine vault subdirectory
        lang_dir = VAULT_ROOT / frag.language
        lang_dir.mkdir(parents=True, exist_ok=True)

        # Write fragment
        safe_name = re.sub(r"[^\w.\-]", "_", Path(frag.source_file).name)
        frag_filename = f"{frag.fragment_hash}_{safe_name}.fragment"
        frag_path = lang_dir / frag_filename
        frag_path.write_text(frag.content, encoding="utf-8")

        # Write provenance sidecar
        frag.fragment_file = f"{frag.language}/{frag_filename}"
        prov_path = lang_dir / f"{frag.fragment_hash}_{safe_name}.provenance.json"
        prov_data = {
            "hash": frag.fragment_hash,
            "source_file": frag.source_file,
            "commit": frag.commit,
            "author": frag.author,
            "date": frag.date,
            "cause_of_death": frag.cause_of_death,
            "language": frag.language,
            "extension": frag.extension,
            "lines_start": frag.lines_start,
            "lines_end": frag.lines_end,
            "byte_size": frag.byte_size,
            "fragment_file": frag.fragment_file,
        }
        prov_path.write_text(
            json.dumps(prov_data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        manifest.fragments.append(prov_data)
        new_count += 1

    manifest.total_fragments = len(manifest.fragments)
    manifest.total_bytes = sum(f.get("byte_size", 0) for f in manifest.fragments)

    # Write manifest
    VAULT_ROOT.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(
        json.dumps(manifest.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return manifest, new_count


# ---------------------------------------------------------------------------
# Classify: sort existing unsorted fragments into vault subdirs
# ---------------------------------------------------------------------------

def cmd_classify() -> None:
    """Re-classify fragments in the vault (move to correct language dir)."""
    if not MANIFEST_PATH.exists():
        print("No manifest found. Run 'harvest' first.")
        return

    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    moved = 0
    for entry in data.get("fragments", []):
        frag_path = VAULT_ROOT / entry["fragment_file"]
        if not frag_path.exists():
            continue
        expected_lang = lang_for_file(entry.get("source_file", ""))
        if expected_lang != entry.get("language"):
            new_dir = VAULT_ROOT / expected_lang
            new_dir.mkdir(parents=True, exist_ok=True)
            new_name = frag_path.name
            new_path = new_dir / new_name
            frag_path.rename(new_path)
            # Move provenance sidecar too
            prov_old = frag_path.with_suffix(".provenance.json")
            if prov_old.exists():
                prov_old.rename(new_dir / prov_old.name)
            entry["language"] = expected_lang
            entry["fragment_file"] = f"{expected_lang}/{new_name}"
            moved += 1

    MANIFEST_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Reclassified {moved} fragments.")


# ---------------------------------------------------------------------------
# Reanimate: search the vault
# ---------------------------------------------------------------------------

def cmd_reanimate(query: str | None, lang: str | None, ext: str | None) -> None:
    """Search the vault and print matching fragments."""
    if not MANIFEST_PATH.exists():
        print("No manifest found. Run 'harvest' first.")
        return

    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    matches = []

    for entry in data.get("fragments", []):
        if lang and entry.get("language") != lang:
            continue
        if ext and entry.get("extension") != ext:
            continue
        if query:
            frag_path = VAULT_ROOT / entry["fragment_file"]
            if frag_path.exists():
                content = frag_path.read_text(encoding="utf-8", errors="replace")
                if query.lower() not in content.lower():
                    continue
            else:
                continue
        matches.append(entry)

    if not matches:
        print("No matching fragments found.")
        return

    print(f"Found {len(matches)} fragment(s):\n")
    for m in matches[:25]:  # cap output
        cause = m.get("cause_of_death", "?")
        print(
            f"  [{m['language']}] {m['source_file']}  "
            f"L{m['lines_start']}-{m['lines_end']}  "
            f"({m['byte_size']}B, {cause})"
        )
        print(f"    → {m['fragment_file']}")
    if len(matches) > 25:
        print(f"\n  ... and {len(matches) - 25} more.")


# ---------------------------------------------------------------------------
# Manifest: print vault summary
# ---------------------------------------------------------------------------

def cmd_manifest() -> None:
    """Print vault summary."""
    if not MANIFEST_PATH.exists():
        print("No manifest found. Run 'harvest' first.")
        return

    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    frags = data.get("fragments", [])
    total = len(frags)
    total_bytes = sum(f.get("byte_size", 0) for f in frags)

    # Count by language
    by_lang: dict[str, int] = {}
    by_cause: dict[str, int] = {}
    for f in frags:
        lang = f.get("language", "unknown")
        cause = f.get("cause_of_death", "unknown")
        by_lang[lang] = by_lang.get(lang, 0) + 1
        by_cause[cause] = by_cause.get(cause, 0) + 1

    print(f"Corpse Vault: {total} fragments, {total_bytes:,} bytes")
    print(f"Harvested: {data.get('harvested_at', '?')}\n")

    if by_lang:
        print("By language:")
        for lang, count in sorted(by_lang.items(), key=lambda x: -x[1]):
            print(f"  {lang:16s} {count:4d}")

    if by_cause:
        print("\nBy cause of death:")
        for cause, count in sorted(by_cause.items(), key=lambda x: -x[1]):
            print(f"  {cause:24s} {count:4d}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="corpse_reviver",
        description="The White-dressed Bride — necromancy pipeline for dead code.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    # prowl
    sub.add_parser("prowl", help="Intercept code staged for deletion (pre-mortem scan).")

    # harvest
    h = sub.add_parser("harvest", help="Harvest dead code from specific graveyards.")
    h.add_argument("--since", default="30d", help="How far back to scan git log (e.g. 30d, 7d, 90d, 6m). Default: 30d")
    h.add_argument("--stashes", action="store_true", help="Harvest from git stashes.")
    h.add_argument("--comments", action="store_true", help="Harvest commented-out code from tracked files.")
    h.add_argument("--reflog", action="store_true", help="Harvest from reflog (force-push/reset casualties).")
    h.add_argument("--dead-branches", action="store_true", help="Harvest from merged/dead branches.")
    h.add_argument("--orphans", action="store_true", help="Harvest untracked orphaned files.")
    h.add_argument("--gitignored", action="store_true", help="Harvest gitignored files on disk.")
    h.add_argument("--graffiti", action="store_true", help="Harvest TODO/FIXME/HACK markers.")
    h.add_argument("--all", action="store_true", help="Harvest from ALL sources (the kleptomaniac).")
    h.add_argument("--max-commits", type=int, default=200, help="Max commits to scan. Default: 200")

    # hoard (blind-faithed total sweep)
    ho = sub.add_parser("hoard", help="Blind-faithed total sweep — every graveyard, no discrimination.")
    ho.add_argument("--since", default="30d", help="How far back for commit history. Default: 30d")
    ho.add_argument("--max-commits", type=int, default=200, help="Max commits to scan. Default: 200")

    # classify
    sub.add_parser("classify", help="Re-classify vault fragments by language.")

    # reanimate
    r = sub.add_parser("reanimate", help="Search the vault for fragments.")
    r.add_argument("--query", "-q", help="Text to search for in fragment content.")
    r.add_argument("--lang", help="Filter by language (e.g. rust, python, typescript).")
    r.add_argument("--ext", help="Filter by extension (e.g. .rs, .py, .ts).")

    # suture
    s = sub.add_parser("suture", help="Stitch fragments into a composite — the Bride's act.")
    s.add_argument("--fragments", nargs="+", help="Fragment hashes to stitch together.")
    s.add_argument("--lang", help="Select fragments by language.")
    s.add_argument("--query", "-q", help="Select fragments matching text.")
    s.add_argument("--output", "-o", help="Output filename (default: auto-timestamped in sutures/).")

    # manifest
    sub.add_parser("manifest", help="Print vault summary — the morgue ledger.")

    # embalm-before-edit
    ebe = sub.add_parser(
        "embalm-before-edit",
        help="DO-NOT-USE-UNFINISHED-DEV--WIP: embalm-before-edit is disabled until finished.",
    )
    ebe.add_argument("files", nargs="*", help="Disabled WIP lane.")
    ebe.add_argument("--label", "-l", help="Disabled WIP lane.")
    ebe.add_argument("--staged", action="store_true", help="Disabled WIP lane.")
    ebe.add_argument("--diff", metavar="SESSION", help="Disabled WIP lane.")
    ebe.add_argument("--stitch", metavar="SESSION", help="Disabled WIP lane.")
    ebe.add_argument("--list", action="store_true", dest="list_sessions", help="Disabled WIP lane.")

    return p


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)

    if args.command == "prowl":
        cmd_prowl()

    elif args.command in ("harvest", "hoard"):
        all_fragments: list[Fragment] = []
        is_hoard = args.command == "hoard"

        # Determine what to harvest
        any_specific = getattr(args, "stashes", False) or getattr(args, "comments", False) or \
            getattr(args, "reflog", False) or getattr(args, "dead_branches", False) or \
            getattr(args, "orphans", False) or getattr(args, "gitignored", False) or \
            getattr(args, "graffiti", False)

        do_all = is_hoard or getattr(args, "all", False)
        do_commits = do_all or not any_specific
        do_stashes = do_all or getattr(args, "stashes", False)
        do_comments = do_all or getattr(args, "comments", False)
        do_reflog = do_all or getattr(args, "reflog", False)
        do_dead_branches = do_all or getattr(args, "dead_branches", False)
        do_orphans = do_all or getattr(args, "orphans", False)
        do_gitignored = do_all or getattr(args, "gitignored", False)
        do_graffiti = do_all or getattr(args, "graffiti", False)

        if is_hoard:
            print("The Bride walks the wasteland. Hoarding everything.\n")

        if do_commits:
            print(f"Harvesting deleted code from commits (--since {args.since})...")
            frags = harvest_deleted_from_commits(args.since, args.max_commits)
            print(f"  Found {len(frags)} fragment(s) from commits.")
            all_fragments.extend(frags)

        if do_stashes:
            print("Harvesting from stashes...")
            frags = harvest_stashes()
            print(f"  Found {len(frags)} fragment(s) from stashes.")
            all_fragments.extend(frags)

        if do_comments:
            print("Harvesting commented-out code from tracked files...")
            frags = harvest_commented_code()
            print(f"  Found {len(frags)} fragment(s) from comments.")
            all_fragments.extend(frags)

        if do_reflog:
            print("Harvesting from reflog (force-push/reset casualties)...")
            frags = harvest_reflog()
            print(f"  Found {len(frags)} fragment(s) from reflog.")
            all_fragments.extend(frags)

        if do_dead_branches:
            print("Harvesting from dead/merged branches...")
            frags = harvest_dead_branches()
            print(f"  Found {len(frags)} fragment(s) from dead branches.")
            all_fragments.extend(frags)

        if do_orphans:
            print("Harvesting orphaned (untracked) files...")
            frags = harvest_orphans()
            print(f"  Found {len(frags)} fragment(s) from orphans.")
            all_fragments.extend(frags)

        if do_gitignored:
            print("Harvesting gitignored treasures...")
            frags = harvest_gitignored()
            print(f"  Found {len(frags)} fragment(s) from gitignored files.")
            all_fragments.extend(frags)

        if do_graffiti:
            print("Harvesting TODO/FIXME/HACK graffiti...")
            frags = harvest_graffiti()
            print(f"  Found {len(frags)} fragment(s) from graffiti.")
            all_fragments.extend(frags)

        if all_fragments:
            manifest, new_count = embalm(all_fragments)
            print(
                f"\nEmbalmed {new_count} new fragment(s) "
                f"(vault total: {manifest.total_fragments}, "
                f"{manifest.total_bytes:,} bytes)."
            )
        else:
            print("\nNo fragments harvested.")

    elif args.command == "classify":
        cmd_classify()

    elif args.command == "reanimate":
        cmd_reanimate(args.query, args.lang, args.ext)

    elif args.command == "suture":
        cmd_suture(args.fragments, args.lang, args.query, args.output)

    elif args.command == "manifest":
        cmd_manifest()

    elif args.command == "embalm-before-edit":
        raise SystemExit(
            "DO-NOT-USE-UNFINISHED-DEV--WIP: embalm-before-edit is unfinished and disabled."
        )


if __name__ == "__main__":
    main()
