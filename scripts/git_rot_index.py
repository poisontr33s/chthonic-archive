#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: git_rot_index.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
scripts/git_rot_index.py - Git-aware rot accumulator.

Reads every tracked markdown file plus git rename history, classifies each
link as resolves/broken/ambig, attaches git signals (when source was last
touched, who, whether target was renamed historically), and emits:

  manifest/git_rot_index.json   - machine-readable snapshot
  manifest/git_rot_index.md     - human-readable digest (top 30 by priority)

Re-run anytime to refresh. The JSON is cache, not truth. Truth is git.

Usage:
  uv run scripts/git_rot_index.py             # full index
  uv run scripts/git_rot_index.py --top 50    # bump digest size
  uv run scripts/git_rot_index.py --no-md     # skip markdown digest

@SID:           GIT_ROT_INDEX_V1
@Shabti:        CLI Script
@Purpose:       scripts/git_rot_index.py - Git-aware rot accumulator.
"""

from __future__ import annotations

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


# @SID: GIT_ROT_INDEX_V1

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\n]+)\)")  # simple, non-backtracking
# Note: the simple regex stops the URL at the first `)`. This misses links
# whose path contains literal parens (e.g. `(SSOT)` in IronMaiden's target).
# The trade was made on 2026-05-13 after a balanced-paren regex caused
# catastrophic backtracking on adversarial input from agent-generated docs,
# hanging the indexer on the first file. scripts/link_audit.py handles
# parens-in-URL via different machinery; we accept the gap here.

# Error code taxonomy. Stable identifiers so future tooling can dispatch on code.
ROT_CODES: dict[str, str] = {
    "ROT-001": "target_missing — no candidate file exists anywhere",
    "ROT-002": "target_ambig_broken — basename matches multiple, link broken",
    "ROT-003": "target_ambig_resolves — basename ambiguous but link resolves (false positive)",
    "ROT-004": "target_renamed — auto-fixable via rename history",
    "ROT-005": "empty_label — [](target) with no link text",
    "ROT-006": "anchor_missing — file exists, #anchor doesn't",
    "ROT-007": "line_anchor_stale — #LNNN out of range for current file",
    "ROT-008": "placeholder_literal — target is literal 'path'/'url'/template residue",
    "ROT-009": "external_unreached — http(s) link failed live check (opt-in, not run by default)",
}
CLUSTER_CODES: dict[str, str] = {
    "CLUSTER-001": "source_hotspot — one file holds >50 rot entries (agent dump candidate)",
    "CLUSTER-002": "orphan_target — one missing target referenced from >=3 sources",
    "ROOT-001": "mass_rename_legacy — N rot entries trace to single historical commit",
}

CATEGORY_TO_CODE = {
    "broken_no_known_target": "ROT-001",
    "ambig_truly_ambiguous": "ROT-002",
    "ambig_resolves_fine": "ROT-003",
    "broken_fixable_via_rename": "ROT-004",
}

# Gitological Taxonomy Ladder — depth model the user named on 2026-05-13.
# Codes describe symptoms at different depths of git's reality. Each level
# represents a kind of question being asked about the artifact:
#   L1 SURFACE  — does this link work right now? (raw symptoms)
#   L2 VIRTUAL  — is the namespace clean? (resolution-layer concerns)
#   L3 ANCHOR   — does the positional reference still align? (semantic)
#   L4 LINEAGE  — what historical structure created this state? (causational)
# Tombstone lifecycle marker is orthogonal — it cuts across all levels.
LEVELS: dict[str, str] = {
    "L1": "SURFACE  — raw symptoms visible at the link site",
    "L2": "VIRTUAL  — namespace and resolution-layer concerns",
    "L3": "ANCHOR   — positional / semantic reference alignment",
    "L4": "LINEAGE  — structural / causational, derived from git history",
}
CODE_TO_LEVEL: dict[str, str] = {
    "ROT-001": "L1",  # target_missing
    "ROT-002": "L1",  # target_ambig_broken
    "ROT-005": "L1",  # empty_label
    "ROT-008": "L1",  # placeholder_literal
    "ROT-003": "L2",  # target_ambig_resolves (suppressed by default)
    "ROT-004": "L2",  # target_renamed (auto-fixable)
    "ROT-006": "L3",  # anchor_missing (detector pending)
    "ROT-007": "L3",  # line_anchor_stale (detector pending)
    "ROOT-001": "L4",  # mass_rename_legacy (detector pending)
    "CLUSTER-001": "L4",  # source_hotspot
    "CLUSTER-002": "L4",  # orphan_target
}

PLACEHOLDER_LITERALS = {"path", "url", "link", "target", "file", "TODO", "FIXME"}
SKIP_DIRS = {
    ".git", "node_modules", "target", "__pycache__", ".venv",
    "build", "dist", ".mypy_cache", ".ruff_cache",
    "pnk-live", "rmco-live", "csb-live", "git-dump-live", "pnk-lfh-live",
}
REPO_ROOT = Path(__file__).resolve().parent.parent


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"git {args} failed: {result.stderr}")
    return result.stdout


def build_rename_map() -> dict[str, str]:
    """
    Build old_path -> current_path map from git rename history.
    Walks renames forward through history so chains resolve to the latest path.
    """
    out = git("log", "--all", "--diff-filter=R", "--name-status",
              "--format=__C__%H", check=False)
    rename_chain: dict[str, str] = {}
    for line in out.splitlines():
        if line.startswith("__C__") or not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 3 or not parts[0].startswith("R"):
            continue
        _, old, new = parts[0], parts[1], parts[2]
        rename_chain[old] = new

    # Collapse chains: if A -> B and B -> C, then A -> C
    resolved: dict[str, str] = {}
    for old in rename_chain:
        current = old
        seen = {current}
        while current in rename_chain and rename_chain[current] not in seen:
            current = rename_chain[current]
            seen.add(current)
        if current != old:
            resolved[old] = current
    return resolved


# Lifecycle values that exclude a file from active rot scanning.
# - tombstone: file is dead, preserved for history
# - ssot-canon: file is the macro-prompt-world / unabridged source from
#   which downstream slimmed references are derived. Scanning broken refs
#   on the SSOT itself inverts the dependency direction (downstream files
#   inherit from here; the SSOT does not depend on them).
EXCLUDED_LIFECYCLES = {"tombstone", "ssot-canon"}


def is_tombstone(path: Path) -> bool:
    """
    A file is excluded from active rot scanning if its frontmatter declares
    a lifecycle in EXCLUDED_LIFECYCLES. Name kept for backwards compatibility;
    the predicate covers both tombstones (dead) and ssot-canon (frozen
    macro-prompt source).
    """
    try:
        head = path.read_text(encoding="utf-8", errors="replace").splitlines()[:20]
    except OSError:
        return False
    in_fm = False
    for line in head:
        # Strip UTF-8 BOM if present (some files are saved with BOM by editors).
        clean = line.lstrip("﻿").strip()
        if clean == "---":
            if in_fm:
                return False
            in_fm = True
            continue
        if in_fm:
            m = re.match(r"^\s*lifecycle\s*:\s*([\w-]+)", line.lstrip("﻿"))
            if m and m.group(1) in EXCLUDED_LIFECYCLES:
                return True
    return False


# Memoized target-side lifecycle check. Same canon target is linked from
# many sources (the SSOT alone receives 14 inbound refs in current state);
# reading its frontmatter once per scan beats once per link.
_TARGET_LIFECYCLE_CACHE: dict[Path, bool] = {}


def _target_excluded(path: Path) -> bool:
    cached = _TARGET_LIFECYCLE_CACHE.get(path)
    if cached is not None:
        return cached
    excluded = is_tombstone(path)
    _TARGET_LIFECYCLE_CACHE[path] = excluded
    return excluded


def tracked_markdown() -> tuple[list[Path], list[str]]:
    out = git("ls-files", "*.md", "*.MD", "*.markdown")
    paths: list[Path] = []
    tombstones: list[str] = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        if any(seg in SKIP_DIRS for seg in line.split("/")):
            continue
        p = REPO_ROOT / line
        if not p.exists():
            continue
        if is_tombstone(p):
            tombstones.append(line)
            continue
        paths.append(p)
    return paths, tombstones


def file_signals_batch(paths: list[Path]) -> dict[str, dict]:
    """
    Single git invocation that returns: per path, last-commit ISO date + author email.
    """
    # Walk one log run with --name-only and __COMMIT__ markers.
    out = git("log", "--all", "--name-only",
              "--format=__C__%H%n%aI%n%ae", check=False)
    file_first_seen: dict[str, str] = {}
    file_last_touched: dict[str, dict] = {}
    current_iso = None
    current_email = None
    expecting = "hash"
    for line in out.splitlines():
        if line.startswith("__C__"):
            expecting = "iso"
            continue
        if expecting == "iso":
            current_iso = line.strip()
            expecting = "email"
            continue
        if expecting == "email":
            current_email = line.strip()
            expecting = "files"
            continue
        if not line.strip():
            continue
        # file path
        rel = line.strip()
        if rel not in file_last_touched:
            file_last_touched[rel] = {"iso": current_iso, "email": current_email}
        file_first_seen[rel] = current_iso  # overwritten until oldest wins
    return {
        rel: {
            "last_touched": file_last_touched.get(rel, {}).get("iso"),
            "last_author": file_last_touched.get(rel, {}).get("email"),
            "first_seen": file_first_seen.get(rel),
        }
        for rel in {*file_last_touched, *file_first_seen}
    }


def resolve_link(src: Path, raw_target: str) -> tuple[str, Optional[Path], Optional[str], Optional[str]]:
    """
    Return (cleaned_target_str, resolved_path_or_None, would_be_repo_relpath, fragment).
    The fragment is everything after `#` if present (e.g. `section-name` or `L42`).
    Used by L3 ANCHOR detection (ROT-006/007).
    """
    tgt = raw_target.strip()
    if tgt.startswith(("http://", "https://", "mailto:", "#")):
        return ("external", None, None, None)
    if re.match(r"^[A-Za-z]:[/\\]", tgt):
        return ("absolute_winpath", None, None, None)
    fragment = None
    if "#" in tgt:
        tgt, fragment = tgt.split("#", 1)
        fragment = fragment.split("?")[0]
    tgt_clean = tgt.split("?")[0].strip()
    if not tgt_clean:
        return ("empty", None, None, fragment)
    if tgt_clean.startswith("/"):
        resolved = REPO_ROOT / tgt_clean[1:]
    else:
        resolved = (src.parent / tgt_clean).resolve()
    try:
        would_be = resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        would_be = None
    return (tgt_clean, resolved if resolved.exists() else None, would_be, fragment)


# Unified target-structure lookaside cache: one entry per target file,
# carries everything L3 detection needs in a single read.
#   structure_cache[Path] = {"total_lines": int, "valid_slugs": set[str]}
# Built lazily — populated only when a link actually resolves to that target.
_STRUCTURE_CACHE: dict[Path, dict] = {}


def _gfm_anchor(text: str) -> str:
    """
    GitHub Flavored Markdown anchor normalization.
    Sequence (matches user 2026-05-13 spec):
      1. Strip leading/trailing whitespace.
      2. Lowercase entire string.
      3. Strip leading `#` markers (heading sigils).
      4. Remove punctuation (everything not alphanumeric / underscore / whitespace / hyphen).
      5. Replace whitespace runs with single hyphen.
      6. Strip leading/trailing hyphens.

    Duplicate-suffix logic (heading collisions like two `## Introduction`)
    is applied at the file level in _build_structure, NOT here — this
    function returns the base slug only.
    """
    text = text.strip().lower()
    text = re.sub(r"^#+\s*", "", text)
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    return text.strip("-")


def _build_structure(path: Path) -> dict:
    """Read a target file once, return everything L3 needs."""
    valid_slugs: set[str] = set()
    total_lines = 0
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        total_lines = text.count("\n") + 1
        seen_counts: dict[str, int] = {}
        in_fence = False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            m = re.match(r"^(#{1,6})\s+(.+)$", stripped)
            if not m:
                continue
            base = _gfm_anchor(m.group(2))
            if not base:
                continue
            # GFM duplicate-suffix rule: first occurrence is bare, subsequent
            # ones get -1, -2, -3 appended.
            n = seen_counts.get(base, 0)
            slug = base if n == 0 else f"{base}-{n}"
            valid_slugs.add(slug)
            seen_counts[base] = n + 1
    except OSError:
        pass
    return {"total_lines": total_lines, "valid_slugs": valid_slugs}


def _structure(path: Path) -> dict:
    cached = _STRUCTURE_CACHE.get(path)
    if cached is not None:
        return cached
    built = _build_structure(path)
    _STRUCTURE_CACHE[path] = built
    return built


LINE_ANCHOR_RE = re.compile(r"^[Ll]?(\d+)(?:-[Ll]?(\d+))?$")


# ============================================================================
# L4 LINEAGE: ROOT-001 mass-rename / mass-delete ancestry attribution.
#
# For each ROT-001 entry (truly-missing target), ask git when its
# would_be_path stopped existing. Groups by parent directory first so we
# can ask git about many paths in one subprocess call. The sentinel-format
# parser matches the build_rename_map / file_signals_batch patterns
# already used in this file (deterministic core-state sync).
# ============================================================================

def parse_root_stream(stdout: str) -> list[dict]:
    """
    Parse output of:
      git log --diff-filter=D --name-only --format=__C__%H%n%aI%n%s -- <paths>

    Each `__C__<sha>` line starts a commit block. Following two lines are
    ISO date and subject. Subsequent non-empty lines are deleted paths
    until the next sentinel.
    """
    commits: list[dict] = []
    cur: Optional[dict] = None
    phase = "sentinel"  # sentinel | date | subject | paths
    for line in stdout.splitlines():
        if line.startswith("__C__"):
            if cur is not None:
                commits.append(cur)
            cur = {"sha": line[5:].strip(), "date": "", "subject": "", "deleted_paths": []}
            phase = "date"
            continue
        if cur is None:
            continue
        if phase == "date":
            cur["date"] = line.strip()
            phase = "subject"
            continue
        if phase == "subject":
            cur["subject"] = line.strip()
            phase = "paths"
            continue
        if line.strip():
            cur["deleted_paths"].append(line.strip())
    if cur is not None:
        commits.append(cur)
    return commits


def compute_root_attribution(entries: list[dict]) -> list[dict]:
    """
    For ROT-001 entries (broken_no_known_target with would_be_path),
    group by parent directory, then run one `git log` per group to find
    the deletion commit(s). Attach `root_commit` / `root_subject` /
    `root_date` to each matched entry IN PLACE, and return a list of
    ROOT-001 cluster summaries (one per breaking commit).

    The git_truth=='existed_once' entries are the prime candidates;
    'never_existed' targets won't be found in deletion history.
    """
    rot001 = [
        e for e in entries
        if e.get("code") == "ROT-001"
        and e.get("would_be_path")
        and e.get("git_truth") == "existed_once"
    ]
    if not rot001:
        return []

    # Group by parent directory of would_be_path.
    by_parent: dict[str, list[dict]] = defaultdict(list)
    for e in rot001:
        parent = str(Path(e["would_be_path"]).parent.as_posix())
        by_parent[parent].append(e)

    # For each parent group, query git for deletion events affecting any of
    # the would_be_paths in that group. One subprocess per parent.
    by_commit: dict[str, dict] = {}  # sha -> {sha, subject, date, broken_paths: set, entry_ids: set}

    for parent, group_entries in by_parent.items():
        paths_in_group = list({e["would_be_path"] for e in group_entries})
        if not paths_in_group:
            continue
        try:
            out = git(
                "log", "--diff-filter=D", "--name-only",
                "--format=__C__%H%n%aI%n%s", "--all", "--",
                *paths_in_group, check=False,
            )
        except (RuntimeError, OSError):
            continue
        commits = parse_root_stream(out)
        # For each entry in this group, find the most recent commit that
        # deleted its would_be_path.
        deleted_at: dict[str, dict] = {}  # path -> commit dict
        for c in commits:
            for p in c["deleted_paths"]:
                if p in deleted_at:
                    continue  # we walk newest-first, keep the first hit
                deleted_at[p] = c

        for e in group_entries:
            wbp = e["would_be_path"]
            hit = deleted_at.get(wbp)
            if not hit:
                continue
            e["root_commit"] = hit["sha"]
            e["root_subject"] = hit["subject"]
            e["root_date"] = hit["date"]
            sha = hit["sha"]
            if sha not in by_commit:
                by_commit[sha] = {
                    "code": "ROOT-001",
                    "level": "L4",
                    "kind": "mass_delete_ancestry",
                    "sha": sha,
                    "subject": hit["subject"],
                    "date": hit["date"],
                    "broken_paths": set(),
                    "entry_ids": set(),
                    "parent_dirs": set(),
                }
            by_commit[sha]["broken_paths"].add(wbp)
            by_commit[sha]["entry_ids"].add(e["id"])
            by_commit[sha]["parent_dirs"].add(parent)

    # Materialize sets to sorted lists for JSON.
    roots: list[dict] = []
    for sha, info in by_commit.items():
        roots.append({
            "code": info["code"],
            "level": info["level"],
            "kind": info["kind"],
            "sha": sha,
            "subject": info["subject"],
            "date": info["date"],
            "broken_path_count": len(info["broken_paths"]),
            "affected_entry_count": len(info["entry_ids"]),
            "parent_dirs": sorted(info["parent_dirs"])[:5],
            "broken_paths_sample": sorted(info["broken_paths"])[:5],
            "verdict": (
                "single historical commit broke N L1 entries — "
                "decide: revert restore, accept deletion + prune referrers, "
                "or stub-create the deleted targets."
            ),
        })
    # Sort by impact (most-broken first).
    roots.sort(key=lambda r: -r["broken_path_count"])
    return roots


def basename_index(all_md: list[Path]) -> dict[str, list[str]]:
    idx: dict[str, list[str]] = defaultdict(list)
    for p in all_md:
        rel = p.relative_to(REPO_ROOT).as_posix()
        idx[p.name].append(rel)
    return idx


def find_via_rename(target_rel: str, rename_map: dict[str, str]) -> Optional[str]:
    """If target_rel was renamed historically, return current path."""
    return rename_map.get(target_rel)


def relpath_from(src: Path, dest_rel: str) -> str:
    """Compute markdown-friendly relative path from src to dest_rel."""
    src_rel = src.relative_to(REPO_ROOT)
    src_parts = src_rel.parts[:-1]
    dest_parts = Path(dest_rel).parts
    ups = "../" * len(src_parts)
    return ups + "/".join(dest_parts) if src_parts else "/".join(dest_parts)


def score_priority(category: str, signals: dict, repo_path: str) -> str:
    """Heuristic priority. Tweakable."""
    if category == "broken_fixable_via_rename":
        return "high"
    if category == "broken_no_known_target":
        # Archived paths get demoted
        if "archive" in repo_path or "dumpster-dive" in repo_path:
            return "low"
        return "medium"
    if category == "ambig_resolves_fine":
        return "background"
    if category == "ambig_truly_ambiguous":
        return "medium"
    return "low"


def classify_link(
    src: Path, raw_target: str, line_no: int,
    rename_map: dict[str, str], basenames: dict[str, list[str]],
    file_sig: dict, ever_existed: set[str],
) -> Optional[dict]:
    cleaned, resolved, would_be, fragment = resolve_link(src, raw_target)
    if cleaned in ("external", "absolute_winpath", "empty"):
        return None

    src_rel = src.relative_to(REPO_ROOT).as_posix()
    base_entry = {
        "source": src_rel,
        "line": line_no,
        "raw_target": raw_target,
        "git": {
            "source_last_touched": file_sig.get(src_rel, {}).get("last_touched"),
            "source_author": file_sig.get(src_rel, {}).get("last_author"),
        },
    }

    # Detect placeholder literals first (ROT-008) — target is literally "path", "url", etc.
    if cleaned.strip() in PLACEHOLDER_LITERALS:
        return {
            **base_entry,
            "category": "placeholder_literal",
            "code": "ROT-008",
            "priority": "low",
        }

    if resolved is not None:
        # File resolves. Check fragment if present (L3 ANCHOR detection).
        if fragment:
            # Target-side lifecycle guard: skip L3 ANCHOR detection when the
            # resolved target carries an EXCLUDED_LIFECYCLES marker.
            #   tombstone   = dead-and-preserved (no positional contract)
            #   ssot-canon  = alive-and-frozen macro-prompt source; line/
            #                 anchor refs into it are GitHub-style markers,
            #                 not load-bearing structural contracts.
            # Same predicate that excludes tombstoned sources at the walk
            # layer, now propagated to the target side at classification.
            if _target_excluded(resolved):
                return None
            line_m = LINE_ANCHOR_RE.match(fragment)
            if line_m:
                # Line anchor: #L42 or #L42-L51 or #42
                start = int(line_m.group(1))
                end = int(line_m.group(2)) if line_m.group(2) else start
                struct = _structure(resolved)
                file_lines = struct["total_lines"]
                if file_lines and (start > file_lines or end > file_lines):
                    return {
                        **base_entry,
                        "category": "line_anchor_stale",
                        "code": "ROT-007",
                        "resolved_to": str(resolved.relative_to(REPO_ROOT).as_posix()),
                        "fragment": fragment,
                        "file_lines": file_lines,
                        "priority": "medium",
                    }
            else:
                # Heading anchor: fragment may itself include a duplicate
                # suffix (e.g. `#introduction-1`). _structure carries the
                # full set of canonicalized slugs including those suffixes.
                want = _gfm_anchor(fragment)
                struct = _structure(resolved)
                if want and want not in struct["valid_slugs"]:
                    return {
                        **base_entry,
                        "category": "anchor_missing",
                        "code": "ROT-006",
                        "resolved_to": str(resolved.relative_to(REPO_ROOT).as_posix()),
                        "fragment": fragment,
                        "want_anchor": want,
                        "priority": "medium",
                    }

        # No fragment problem. Check basename ambiguity (existing L2 logic).
        bname = Path(cleaned).name
        candidates = basenames.get(bname, [])
        if len(candidates) > 1:
            return {
                **base_entry,
                "category": "ambig_resolves_fine",
                "code": "ROT-003",
                "candidate_count": len(candidates),
                "resolved_to": str(resolved.relative_to(REPO_ROOT).as_posix()),
                "priority": score_priority("ambig_resolves_fine", base_entry["git"], src_rel),
            }
        return None  # plain healthy link

    # Resolved is None: broken
    # Try rename history match
    target_rel = cleaned.lstrip("/")
    rename_target = find_via_rename(target_rel, rename_map)

    if rename_target:
        suggested = relpath_from(src, rename_target)
        return {
            **base_entry,
            "category": "broken_fixable_via_rename",
            "code": "ROT-004",
            "renamed_from": target_rel,
            "renamed_to": rename_target,
            "suggested_fix": suggested,
            "priority": score_priority("broken_fixable_via_rename", base_entry["git"], src_rel),
        }

    # No rename match. Check if basename matches something elsewhere.
    bname = Path(cleaned).name
    candidates = basenames.get(bname, [])
    if candidates:
        return {
            **base_entry,
            "category": "ambig_truly_ambiguous",
            "code": "ROT-002",
            "candidates": candidates[:5],
            "priority": score_priority("ambig_truly_ambiguous", base_entry["git"], src_rel),
        }

    # ROT-001 enrichment: ask git what it knows about this target.
    # ever_existed is the set of every path that appeared in any commit on
    # any ref. If the would-be path is in there, the file existed once and
    # was deleted (or git's rename heuristic missed a move). If not, the
    # target was never in this repo — typo or hallucinated reference.
    git_truth = "unknown"
    if would_be:
        if would_be in ever_existed:
            git_truth = "existed_once"  # was committed, then deleted
        else:
            git_truth = "never_existed"  # typo or fictional reference
    return {
        **base_entry,
        "category": "broken_no_known_target",
        "code": "ROT-001",
        "would_be_path": would_be,
        "git_truth": git_truth,
        "priority": score_priority("broken_no_known_target", base_entry["git"], src_rel),
    }


def build_index(args) -> dict:
    print("[git_rot_index] building rename map ...", file=sys.stderr)
    rename_map = build_rename_map()
    print(f"[git_rot_index] {len(rename_map)} historical renames", file=sys.stderr)

    print("[git_rot_index] enumerating tracked markdown ...", file=sys.stderr)
    md_files, tombstones = tracked_markdown()
    print(f"[git_rot_index] {len(md_files)} living markdown files in scope", file=sys.stderr)
    if tombstones:
        print(f"[git_rot_index] {len(tombstones)} files excluded (lifecycle: tombstone or ssot-canon)", file=sys.stderr)

    print("[git_rot_index] collecting per-file git signals ...", file=sys.stderr)
    file_sig = file_signals_batch(md_files)

    print("[git_rot_index] indexing basenames ...", file=sys.stderr)
    basenames = basename_index(md_files)

    # ever_existed = every path that ever appeared in any commit on any ref.
    # This is the "git knows" set — broken ROT-001 entries get checked against
    # it to distinguish "deleted file" from "never existed" (typo).
    ever_existed: set[str] = set(file_sig.keys())

    entries: list[dict] = []
    for src in md_files:
        try:
            text = src.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        # Skip fenced code blocks. Inside ``` or ~~~ blocks, lines that look
        # like [label](target) are actually code (PowerShell conditionals,
        # regex patterns like [^"']+, etc.) — not markdown links.
        in_fence = False
        for line_no, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for m in LINK_RE.finditer(line):
                entry = classify_link(
                    src, m.group(2), line_no, rename_map, basenames, file_sig,
                    ever_existed,
                )
                if entry is not None:
                    entry["id"] = hashlib.sha1(
                        f"{entry['source']}:{entry['line']}:{entry['raw_target']}".encode()
                    ).hexdigest()[:12]
                    entry["level"] = CODE_TO_LEVEL.get(entry.get("code", ""), "L1")
                    entries.append(entry)

    summary = Counter(e["category"] for e in entries)
    priority = Counter(e["priority"] for e in entries)
    code_counts = Counter(e.get("code", "UNCODED") for e in entries)

    # Compute clusters from entries.
    source_counts = Counter(e["source"] for e in entries)
    target_counts: Counter[str] = Counter()
    for e in entries:
        if e.get("category") in ("broken_no_known_target", "ambig_truly_ambiguous"):
            target_counts[e["raw_target"]] += 1

    clusters = []
    for src, n in source_counts.most_common():
        if n > 50:
            clusters.append({
                "code": "CLUSTER-001",
                "level": "L4",
                "kind": "source_hotspot",
                "source": src,
                "rot_count": n,
                "verdict": "agent dump candidate — consider archive or delint exclusion",
            })
    for tgt, n in target_counts.most_common():
        if n >= 3:
            sources = [e["source"] for e in entries if e["raw_target"] == tgt][:5]
            clusters.append({
                "code": "CLUSTER-002",
                "level": "L4",
                "kind": "orphan_target",
                "target": tgt,
                "ref_count": n,
                "referenced_from_sample": sources,
                "verdict": "missing file referenced widely — confirm intent (typo? deleted?)",
            })

    # L4 ROOT-001: trace ROT-001 entries to historical commits that deleted
    # their would_be_path. Groups by parent directory first (cheap clustering),
    # then a single `git log --diff-filter=D` per cluster identifies the
    # deletion commit(s). Each L1 ROT-001 entry whose path was deleted in a
    # discoverable commit gets a `root_commit` annotation. Each unique commit
    # that broke multiple paths becomes a ROOT-001 cluster summary.
    roots = compute_root_attribution(entries)

    hotspots = source_counts.most_common(10)

    return {
        "schema_version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(REPO_ROOT),
        "code_taxonomy": {
            "rot": ROT_CODES,
            "cluster": CLUSTER_CODES,
            "levels": LEVELS,
            "code_to_level": CODE_TO_LEVEL,
        },
        "summary": {
            "tracked_md_files": len(md_files),
            "tombstone_files_excluded": len(tombstones),
            "rot_entries": len(entries),
            "categories": dict(summary),
            "codes": dict(code_counts),
            "priorities": dict(priority),
            "rename_history_size": len(rename_map),
            "cluster_count": len(clusters),
        },
        "tombstones": tombstones,
        "hotspots_top10": [{"source": s, "rot_count": n} for s, n in hotspots],
        "clusters": clusters,
        "roots": roots,
        "entries": sorted(
            entries,
            key=lambda e: (
                {"high": 0, "medium": 1, "background": 2, "low": 3}.get(e["priority"], 4),
                e["source"],
                e["line"],
            ),
        ),
    }


def write_md_digest(index: dict, top_n: int = 30) -> str:
    s = index["summary"]
    lines = [
        f"# Git rot index digest",
        "",
        f"Generated: {index['generated_at']}",
        f"Source: `manifest/git_rot_index.json` (regenerate via `uv run scripts/git_rot_index.py`)",
        "",
        f"## Summary",
        "",
        f"- Tracked markdown files: {s['tracked_md_files']}",
        f"- Rot entries: {s['rot_entries']}",
        f"- Historical renames in repo: {s['rename_history_size']}",
        "",
        f"### By category",
        "",
    ]
    for cat, n in sorted(s["categories"].items(), key=lambda kv: -kv[1]):
        lines.append(f"- `{cat}`: {n}")
    lines += ["", "### By priority", ""]
    for pri, n in sorted(s["priorities"].items(), key=lambda kv: -kv[1]):
        lines.append(f"- `{pri}`: {n}")

    lines += ["", "### By code (grouped by gitological level)", ""]
    code_counts = s.get("codes", {})
    # Bucket counts by level
    by_level: dict[str, list[tuple[str, int]]] = {"L1": [], "L2": [], "L3": [], "L4": []}
    for code, n in sorted(code_counts.items(), key=lambda kv: -kv[1]):
        lvl = CODE_TO_LEVEL.get(code, "L1")
        by_level.setdefault(lvl, []).append((code, n))
    for lvl in ("L1", "L2", "L3", "L4"):
        if not by_level.get(lvl):
            continue
        lines.append(f"**{lvl} — {LEVELS[lvl]}**")
        lines.append("")
        for code, n in by_level[lvl]:
            desc = index.get("code_taxonomy", {}).get("rot", {}).get(code, "")
            lines.append(f"- `{code}` ({n}): {desc}")
        lines.append("")

    lines += ["", "## Hotspots (top 10 files by rot count)", ""]
    for h in index["hotspots_top10"]:
        lines.append(f"- `{h['source']}` — {h['rot_count']} entries")

    clusters = index.get("clusters", [])
    if clusters:
        lines += ["", "## Clusters (derived patterns)", ""]
        for c in clusters[:15]:
            if c["kind"] == "source_hotspot":
                lines.append(f"- `{c['code']}` `{c['source']}` — {c['rot_count']} entries. {c['verdict']}")
            elif c["kind"] == "orphan_target":
                lines.append(f"- `{c['code']}` target `{c['target']}` — {c['ref_count']} refs. {c['verdict']}")
                lines.append(f"  sample: {', '.join(f'`{s}`' for s in c['referenced_from_sample'])}")

    lines += ["", f"## Top {top_n} entries by priority", ""]
    for e in index["entries"][:top_n]:
        loc = f"`{e['source']}:L{e['line']}`"
        code = e.get("code", "?")
        head = f"### [{e['priority'].upper()} / {code} / {e['category']}] {loc}"
        lines.append(head)
        lines.append("")
        lines.append(f"- Target: `{e['raw_target']}`")
        if e.get("suggested_fix"):
            lines.append(f"- Suggested fix: `{e['suggested_fix']}`")
        if e.get("renamed_from"):
            lines.append(f"- Rename: `{e['renamed_from']}` -> `{e['renamed_to']}`")
        if e.get("candidates"):
            cands = ", ".join(f"`{c}`" for c in e["candidates"])
            lines.append(f"- Candidate matches: {cands}")
        if e.get("resolved_to"):
            # For ROT-006/007, the file resolves but the anchor doesn't —
            # that's why the entry fires. The old "(false positive — link
            # works)" annotation was misleading (the *file* part works; the
            # *anchor* part is the genuine miss). State it correctly.
            note = "file resolves; anchor missing/stale" if e.get("code") in ("ROT-006", "ROT-007") else "file resolves"
            lines.append(f"- Resolves to: `{e['resolved_to']}` ({note})")
        sig = e.get("git", {})
        if sig.get("source_last_touched"):
            lines.append(f"- Source last touched: {sig['source_last_touched']} by {sig.get('source_author', '?')}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(prog="git_rot_index")
    p.add_argument("--top", type=int, default=30, help="entries in markdown digest")
    p.add_argument("--no-md", action="store_true", help="skip markdown digest")
    p.add_argument("--out-json", default="manifest/git_rot_index.json")
    p.add_argument("--out-md", default="manifest/git_rot_index.md")
    p.add_argument("--include-false-positives", action="store_true",
                   help="Include ROT-003 (ambig_resolves_fine) in output. "
                   "Off by default — these are known false positives where "
                   "the basename is ambiguous but the link resolves correctly. "
                   "Set this flag for diagnostic dives.")
    args = p.parse_args()

    index = build_index(args)

    # Default: drop ROT-003 and ROT-008 false positives from the persisted
    # output. ROT-003 is basename ambiguity that resolves fine in practice;
    # ROT-008 fires on `[label](path)` documentation showing markdown link
    # syntax — universally a placeholder, not real rot. Both are noise the
    # index now structurizes silently. Use --include-false-positives for
    # diagnostic dives.
    if not args.include_false_positives:
        SUPPRESSED_CODES = {"ROT-003", "ROT-008"}
        before = len(index["entries"])
        index["entries"] = [e for e in index["entries"] if e.get("code") not in SUPPRESSED_CODES]
        dropped = before - len(index["entries"])
        if dropped:
            index["summary"]["false_positives_suppressed"] = dropped
            index["summary"]["rot_entries"] = len(index["entries"])
            # Rebuild category/code counts to match the filtered set.
            from collections import Counter as _C
            cats = _C(e["category"] for e in index["entries"])
            codes = _C(e.get("code", "UNCODED") for e in index["entries"])
            pris = _C(e["priority"] for e in index["entries"])
            index["summary"]["categories"] = dict(cats)
            index["summary"]["codes"] = dict(codes)
            index["summary"]["priorities"] = dict(pris)
            print(f"[git_rot_index] suppressed {dropped} false positives "
                  f"(ROT-003 ambig-resolves, ROT-008 placeholder-literal; "
                  f"use --include-false-positives to keep them)", file=sys.stderr)

    out_json = REPO_ROOT / args.out_json
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[git_rot_index] wrote {out_json}")

    if not args.no_md:
        out_md = REPO_ROOT / args.out_md
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_md.write_text(write_md_digest(index, top_n=args.top), encoding="utf-8")
        print(f"[git_rot_index] wrote {out_md}")

    s = index["summary"]
    print(f"[git_rot_index] {s['rot_entries']} rot entries across {s['tracked_md_files']} files; "
          f"categories: {s['categories']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
