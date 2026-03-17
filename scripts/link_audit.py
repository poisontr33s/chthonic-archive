#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: link_audit.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Link Audit — Validate and fix markdown [label](path) references in files.

Scans markdown files for broken or ambiguous internal links, detects basename
collisions, and optionally rewrites fixable references in-place.

@SID:           TOOL_LINK_AUDIT_V1
@Shabti:        Guardian
@Context:       Infrastructure / Markdown Quality Gate
@Implements:    Path-Link Disambiguation Canon (SESSION_HANDOFF_2026_02_27)
@Purpose:       Link Audit — Validate and fix markdown [label](path) references in files.

Usage:
    uv run scripts/link_audit.py check <file>              # audit one file
    uv run scripts/link_audit.py check <file> --fix        # audit + rewrite fixes
    uv run scripts/link_audit.py check <file> --dry-run    # show fixes without writing
    uv run scripts/link_audit.py scan                       # audit ALL markdown files in repo
    uv run scripts/link_audit.py scan --dry-run             # preview repo-wide fixes
    uv run scripts/link_audit.py scan --fix                 # apply repo-wide fixes
    uv run scripts/link_audit.py backticks <file>           # scan for inert backtick file/path refs
    uv run scripts/link_audit.py backticks <file> --dry-run # preview inert backtick upgrades
    uv run scripts/link_audit.py backticks <file> --fix     # rewrite fixable backticks as links
    uv run scripts/link_audit.py renames --staged          # audit markdown links against staged renames
    uv run scripts/link_audit.py renames --staged --dry-run
    uv run scripts/link_audit.py renames --staged --fix
    uv run scripts/link_audit.py collisions                 # list all basename collisions in repo
    uv run scripts/link_audit.py collisions --json          # JSON output
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from scripts.lib.shared import configure_utf8_output, find_repo_root, setup_logging

# =============================================================================
# Constants
# =============================================================================

# Matches markdown links: [label](target)
# Captures: group(1)=full match, group(2)=label, group(3)=target
RE_MD_LINK = re.compile(r"(\[([^\]]*)\]\(([^)]+)\))")

# Paths that are never internal file references
EXTERNAL_PREFIXES = (
    "http://", "https://", "mailto:", "tel:", "ftp://",
    "file:///",  # absolute filesystem URIs from VS Code session dumps
)

# Directories to skip during scanning and collision indexing.
# Includes build artifacts, vendored third-party content, and directories
# whose markdown links are not repo-internal (Hugo templates, session dumps).
SKIP_DIRS = {
    ".git", "node_modules", "target", "__pycache__", ".venv",
    "build", "dist", ".mypy_cache", ".ruff_cache",
    # Third-party / vendored — links reference their own ecosystems
    "meta-ide", "extensions",
    # Session dumps / debugging artifacts — stale file:/// URIs, old usernames
    "debugging_data",
}

# Basenames to skip during scanning (third-party docs whose links are ecosystem-internal)
RE_SKIP_BASENAME = re.compile(r"^(license|readme|changelog|contributing)\b", re.IGNORECASE)

# Backtick-wrapped content: matches `...` outside of [`...`](...) link labels
RE_BACKTICK = re.compile(r"`([^`]+)`")
RE_FILEISH_EXT = re.compile(r"\.(md|py|svg|json|ts|js|toml|yaml|yml|ps1|sh)$")
RE_WINDOWS_ABS = re.compile(r"^[A-Za-z]:[\\/]")
RE_GENERIC_DOTTED_NAME = re.compile(r"^[^`\s\\/]+(?:\.[A-Za-z0-9_-]{1,24})+$")
RE_MD_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


# =============================================================================
# Heading Slug Utilities
# =============================================================================

def markdown_to_slug(heading_text: str) -> str:
    """Convert a markdown heading to a GitHub-compatible anchor slug.

    Rules (matching GitHub/VS Code behaviour):
    - Strip leading/trailing whitespace
    - Downcase
    - Strip characters that are not alphanumeric, space, or hyphen
    - Replace spaces with hyphens
    - Do NOT collapse consecutive hyphens (GitHub preserves them)
    """
    slug = heading_text.strip().lower()
    # Remove inline formatting markers (bold, italic, code, links)
    slug = re.sub(r"[`*_~\[\]()]", "", slug)
    # Remove HTML tags
    slug = re.sub(r"<[^>]+>", "", slug)
    # Keep only alphanumeric, spaces, hyphens, and unicode letters
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = slug.replace(" ", "-")
    slug = slug.strip("-")
    return slug


def extract_heading_slugs(text: str) -> set[str]:
    """Extract all heading anchor slugs from markdown text.

    Handles duplicate headings by appending -1, -2, etc. (GitHub convention).
    """
    slugs: set[str] = set()
    slug_counts: dict[str, int] = {}
    in_fence = False
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = RE_MD_HEADING.match(stripped)
        if not m:
            continue
        base_slug = markdown_to_slug(m.group(2))
        if not base_slug:
            continue
        count = slug_counts.get(base_slug, 0)
        if count == 0:
            slugs.add(base_slug)
        else:
            slugs.add(f"{base_slug}-{count}")
        slug_counts[base_slug] = count + 1
    return slugs


# =============================================================================
# Collision Index
# =============================================================================

def build_collision_index(repo_root: Path) -> dict[str, list[Path]]:
    """Build a map of basename -> [paths] for all files in the repo.

    Uses os.walk with directory pruning to skip heavy dirs early.
    """
    index: dict[str, list[Path]] = {}
    root_str = str(repo_root)
    for dirpath, dirnames, filenames in os.walk(root_str):
        # Prune skip dirs in-place so os.walk won't descend
        dirnames[:] = [
            d for d in dirnames
            if d not in SKIP_DIRS and not d.startswith(".venv")
        ]
        for fname in filenames:
            if RE_SKIP_BASENAME.match(fname):
                continue
            full = Path(dirpath) / fname
            if fname not in index:
                index[fname] = []
            index[fname].append(full)
    return index


def get_collisions(index: dict[str, list[Path]]) -> dict[str, list[Path]]:
    """Filter the index to only basenames with >1 path."""
    return {k: v for k, v in sorted(index.items()) if len(v) > 1}


# =============================================================================
# Link Extraction & Resolution
# =============================================================================

def extract_links(text: str) -> list[dict]:
    """Extract all markdown links from text with line numbers.

    Skips links inside fenced code blocks (``` ... ```).
    """
    results = []
    in_fence = False
    for lineno, line in enumerate(text.split("\n"), start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        # Strip inline code spans before scanning for links, but preserve
        # backticks that are part of a markdown link label: [`file`](path)
        scanline = re.sub(r"(?<!\[)`[^`]+`(?!\]\()", "", line)
        for match in RE_MD_LINK.finditer(scanline):
            full, label, target = match.group(1), match.group(2), match.group(3)
            # Skip external links and Windows absolute paths
            if any(target.startswith(p) for p in EXTERNAL_PREFIXES):
                continue
            if RE_WINDOWS_ABS.match(target):
                continue
            # Split target into path and fragment parts
            if "#" in target:
                path_part, fragment = target.split("#", 1)
            else:
                path_part, fragment = target, None
            # Pure anchor links ([foo](#bar)) — path_part is empty, fragment is set
            results.append({
                "line": lineno,
                "full_match": full,
                "label": label,
                "target": target,
                "path_part": path_part if path_part else None,
                "fragment": fragment,
            })
    return results


_heading_slug_cache: dict[str, set[str]] = {}


def _get_heading_slugs(target_path: Path) -> set[str]:
    """Get heading slugs for a file, with caching."""
    key = str(target_path)
    if key not in _heading_slug_cache:
        try:
            text = target_path.read_text(encoding="utf-8", errors="replace")
            _heading_slug_cache[key] = extract_heading_slugs(text)
        except OSError:
            _heading_slug_cache[key] = set()
    return _heading_slug_cache[key]


def _validate_fragment(
    fragment: str | None,
    resolved_path: Path | None,
    file_path: Path,
    link: dict,
) -> dict | None:
    """Check a #fragment against heading slugs. Returns issue dict or None if ok.

    Works for both same-file anchors (resolved_path=file_path) and cross-file.
    Only validates .md files (fragment anchors in non-md files are ignored).
    """
    if not fragment:
        return None
    # Determine which file contains the headings
    target = resolved_path if resolved_path is not None else file_path
    if not str(target).lower().endswith(".md"):
        return None  # can't validate headers in non-markdown files
    if not target.is_file():
        return None  # file doesn't exist — already handled by path resolution
    slugs = _get_heading_slugs(target)
    # Skip line-reference fragments: #1-1, #45-45, #L6812, #L1 (VS Code / GitHub editor refs)
    if re.match(r"^L?\d+(-L?\d+)?$", fragment):
        return None  # numeric line ref, not a heading anchor
    # Case-insensitive comparison (GitHub renders anchors lowercase,
    # but browsers resolve them case-insensitively)
    fragment_lower = fragment.lower()
    if fragment_lower in slugs:
        return None  # anchor exists, all good
    return {
        "status": "broken_anchor",
        "resolved_path": resolved_path,
        "fix": None,
        "reason": f"No header found: '{fragment}' in {target.name}",
    }


def resolve_link(
    link: dict,
    file_path: Path,
    repo_root: Path,
    collision_index: dict[str, list[Path]],
) -> dict:
    """Resolve a single link and return a diagnostic record.

    Returns a dict with:
        status: "ok" | "broken" | "ambiguous" | "collision_unlabeled" | "broken_anchor"
        resolved_path: the resolved Path (or None)
        fix: suggested replacement string (or None)
        reason: human-readable explanation
    """
    fragment = link.get("fragment")

    # --- Pure same-file anchor: [text](#slug) ---
    if link["path_part"] is None:
        issue = _validate_fragment(fragment, file_path, file_path, link)
        if issue is not None:
            return issue
        return {"status": "ok", "resolved_path": file_path, "fix": None, "reason": None}

    target_str = link["path_part"]
    file_dir = file_path.parent

    # Normalize: strip leading ./ prefix (not lstrip which eats chars individually)
    clean = target_str
    if clean.startswith("./"):
        clean = clean[2:]

    # Try resolve relative to the file's directory
    candidate_rel = (file_dir / clean).resolve()
    # Try resolve relative to repo root
    candidate_root = (repo_root / clean).resolve()

    resolved = None
    needs_path_fix = False
    if candidate_rel.is_file() or candidate_rel.is_dir():
        resolved = candidate_rel
    elif candidate_root.is_file() or candidate_root.is_dir():
        resolved = candidate_root
        # The link text resolves from repo root but NOT from the file's directory.
        # Markdown renderers resolve relative to the file — this link is effectively broken.
        needs_path_fix = True

    basename = Path(clean).name

    # Case 1: target resolves to a real file → OK, but check collision labeling
    if resolved is not None:
        # If the resolved path is outside the repo, it's still valid but skip
        # collision labeling (we can't compute a relative path).
        try:
            rel_path = resolved.relative_to(repo_root)
        except ValueError:
            return {"status": "ok", "resolved_path": resolved, "fix": None, "reason": None}

        # Case 1a: Link resolves from repo root but not from the file's directory.
        # Markdown renderers resolve relative to the file — generate corrected path.
        if needs_path_fix:
            correct_rel = os.path.relpath(resolved, file_dir).replace("\\", "/")
            # Preserve fragment if present
            frag = ""
            if "#" in link["target"]:
                frag = "#" + link["target"].split("#", 1)[1]
            fix = f"[{link['label']}]({correct_rel}{frag})"
            return {
                "status": "broken",
                "resolved_path": resolved,
                "fix": fix,
                "reason": (
                    f"Path '{target_str}' resolves from repo root but not from "
                    f"file directory '{file_dir.relative_to(repo_root)}'; "
                    f"correct relative path is '{correct_rel}'"
                ),
            }

        # Check if the basename has collisions
        siblings = collision_index.get(basename, [])
        if len(siblings) > 1:
            # The link works, but the basename is ambiguous in the repo.
            # Check if the label includes a directory qualifier
            label = link["label"]
            if basename in label and "(" not in label and "/" not in label:
                # Label is just the basename — recommend disambiguation
                parent_hint = rel_path.parent.name or str(rel_path.parent)
                if parent_hint == ".":
                    parent_hint = "repo-root"
                suggested_label = f"{basename} ({parent_hint})"
                fix = f"[{suggested_label}]({link['target']})"
                return {
                    "status": "collision_unlabeled",
                    "resolved_path": resolved,
                    "fix": fix,
                    "reason": (
                        f"'{basename}' exists in {len(siblings)} locations; "
                        f"label should disambiguate with directory qualifier"
                    ),
                }
        # File resolves — now validate fragment if present
        anchor_issue = _validate_fragment(fragment, resolved, file_path, link)
        if anchor_issue is not None:
            return anchor_issue
        return {"status": "ok", "resolved_path": resolved, "fix": None, "reason": None}

    # Case 2: target doesn't resolve — can we find a unique match?
    candidates = collision_index.get(basename, [])

    if len(candidates) == 1:
        # Unique match — the path was just wrong. Suggest fix.
        correct = candidates[0]
        correct_rel = correct.relative_to(repo_root).as_posix()
        # Preserve fragment if present
        fragment = ""
        if "#" in link["target"]:
            fragment = "#" + link["target"].split("#", 1)[1]
        fix = f"[{link['label']}]({correct_rel}{fragment})"
        return {
            "status": "broken",
            "resolved_path": correct,
            "fix": fix,
            "reason": f"Path '{target_str}' not found; unique match at '{correct_rel}'",
        }

    if len(candidates) > 1:
        # Multiple candidates — ambiguous, can't auto-fix
        locs = [str(c.relative_to(repo_root)) for c in candidates]
        return {
            "status": "ambiguous",
            "resolved_path": None,
            "fix": None,
            "reason": (
                f"Path '{target_str}' not found; basename '{basename}' exists in "
                f"{len(candidates)} locations: {', '.join(locs[:5])}"
            ),
        }

    # Case 3: no match at all — file is genuinely deleted.
    # Delink: replace [label](path) with just the label text.
    label = link["label"]
    delink = label if label else ""
    return {
        "status": "broken",
        "resolved_path": None,
        "fix": delink,
        "reason": f"Path '{target_str}' not found and no file named '{basename}' exists in repo — delinked",
    }


# =============================================================================
# Audit Engine
# =============================================================================

def audit_file(
    file_path: Path,
    repo_root: Path,
    collision_index: dict[str, list[Path]],
) -> dict:
    """Audit all internal markdown links in a file.

    Returns a summary dict with diagnostics per link.
    """
    text = file_path.read_text(encoding="utf-8", errors="replace")
    links = extract_links(text)
    results = []

    for link in links:
        diag = resolve_link(link, file_path, repo_root, collision_index)
        results.append({
            "line": link["line"],
            "original": link["full_match"],
            "label": link["label"],
            "target": link["target"],
            **diag,
        })

    ok = [r for r in results if r["status"] == "ok"]
    broken = [r for r in results if r["status"] in ("broken", "broken_anchor")]
    ambiguous = [r for r in results if r["status"] == "ambiguous"]
    unlabeled = [r for r in results if r["status"] == "collision_unlabeled"]
    fixable = [r for r in results if r["fix"] is not None]

    return {
        "file": str(file_path.relative_to(repo_root)),
        "total_links": len(results),
        "ok": len(ok),
        "broken": len(broken),
        "ambiguous": len(ambiguous),
        "collision_unlabeled": len(unlabeled),
        "fixable": len(fixable),
        "issues": [r for r in results if r["status"] != "ok"],
        "all": results,
    }


def load_staged_renames(repo_root: Path) -> list[dict]:
    """Load staged rename pairs from git index."""
    proc = subprocess.run(
        ["git", "diff", "--cached", "--name-status", "--diff-filter=R"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git diff --cached failed")

    renames: list[dict] = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        status, old_path, new_path = parts[0], parts[1], parts[2]
        renames.append({
            "status": status,
            "old_rel": old_path.replace("\\", "/"),
            "new_rel": new_path.replace("\\", "/"),
            "old_abs": (repo_root / old_path).resolve(),
            "new_abs": (repo_root / new_path).resolve(),
        })
    return renames


def scan_repo_markdown(repo_root: Path) -> list[Path]:
    """Collect markdown files in the repo, skipping generated/heavy dirs."""
    files: list[Path] = []
    root_str = str(repo_root)
    for dirpath, dirnames, filenames in os.walk(root_str):
        dirnames[:] = [
            d for d in dirnames
            if d not in SKIP_DIRS and not d.startswith(".venv")
        ]
        for fname in filenames:
            if fname.lower().endswith(".md") and not RE_SKIP_BASENAME.match(fname):
                files.append(Path(dirpath) / fname)
    return sorted(files)


def resolve_staged_rename_fix(link: dict, file_path: Path, repo_root: Path, renames: list[dict]) -> dict | None:
    """Resolve a markdown link against staged rename pairs."""
    target = link["target"]
    path_part = link["path_part"]
    fragment = ""
    if "#" in target:
        fragment = "#" + target.split("#", 1)[1]

    file_dir = file_path.parent
    clean = path_part[2:] if path_part.startswith("./") else path_part
    candidate_rel = (file_dir / clean).resolve()
    candidate_root = (repo_root / clean).resolve()

    for rename in renames:
        if candidate_rel == rename["old_abs"] or candidate_root == rename["old_abs"]:
            replacement_rel = os.path.relpath(rename["new_abs"], file_dir).replace("\\", "/")
            if not replacement_rel.startswith(".") and "/" not in replacement_rel:
                replacement_rel = f"./{replacement_rel}"
            return {
                "status": "staged_rename",
                "resolved_path": str(rename["new_abs"].relative_to(repo_root)),
                "fix": f"[{link['label']}]({replacement_rel}{fragment})",
                "reason": (
                    f"Path '{path_part}' points to staged rename "
                    f"'{rename['old_rel']}' -> '{rename['new_rel']}'"
                ),
            }
    return None


def audit_file_against_staged_renames(file_path: Path, repo_root: Path, renames: list[dict]) -> dict:
    """Audit one markdown file against the staged rename set."""
    text = file_path.read_text(encoding="utf-8", errors="replace")
    links = extract_links(text)
    issues = []

    for link in links:
        diag = resolve_staged_rename_fix(link, file_path, repo_root, renames)
        if diag is None:
            continue
        issues.append({
            "line": link["line"],
            "original": link["full_match"],
            "label": link["label"],
            "target": link["target"],
            **diag,
        })

    return {
        "file": str(file_path.relative_to(repo_root)),
        "total_links": len(links),
        "fixable": len(issues),
        "issues": issues,
    }


def apply_fixes(file_path: Path, issues: list[dict]) -> int:
    """Apply fixable replacements to a file. Returns count of fixes applied."""
    fixable = [i for i in issues if i["fix"] is not None]
    if not fixable:
        return 0

    text = file_path.read_text(encoding="utf-8", errors="replace")
    count = 0
    for issue in fixable:
        old = issue["original"]
        new = issue["fix"]
        if old in text:
            text = text.replace(old, new, 1)
            count += 1

    file_path.write_text(text, encoding="utf-8")
    return count


# =============================================================================
# Inert Backtick Scanner
# =============================================================================

def looks_like_path_literal(text: str) -> bool:
    """Heuristic guard for inert backtick refs.

    Conservative by default:
    - always accept slash-based paths and known extensions
    - accept hidden dot-paths/dotfiles
    - accept generic dotted filenames so new filetypes are discoverable
    """
    candidate = text.strip()
    if not candidate:
        return False
    if "/" in candidate or "\\" in candidate:
        return True
    if RE_FILEISH_EXT.search(candidate):
        return True
    if candidate.startswith("."):
        return True
    return RE_GENERIC_DOTTED_NAME.match(candidate) is not None

def scan_inert_backticks(file_path: Path) -> list[dict]:
    """Find backtick-wrapped file/path-like literals outside code blocks.

    Returns a list of dicts with keys: line, text.
    Skips backticks that are part of markdown link labels ([`x`](url)).
    """
    text = file_path.read_text(encoding="utf-8")
    hits: list[dict] = []
    in_fence = False
    for lineno, line in enumerate(text.split("\n"), start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for m in RE_BACKTICK.finditer(line):
            txt = m.group(1)
            if not looks_like_path_literal(txt):
                continue
            # Skip if part of markdown link label: [`text`](url)
            s = m.start()
            if s > 0 and line[s - 1] == "[":
                continue
            hits.append({"line": lineno, "text": txt, "original": m.group(0)})
    return hits


def format_backtick_target(file_dir: Path, resolved: Path) -> str:
    """Format a resolved path as a markdown target relative to the source file."""
    rel = Path(os.path.relpath(resolved, start=file_dir)).as_posix()
    if rel == ".":
        rel = "./"
    if resolved.is_dir() and not rel.endswith("/"):
        rel += "/"
    return rel


def resolve_backtick_ref(
    hit: dict,
    file_path: Path,
    repo_root: Path,
    collision_index: dict[str, list[Path]],
) -> dict:
    """Resolve an inert backtick ref and suggest a markdown-link replacement when safe."""
    raw = hit["text"].strip()
    clean = raw.replace("\\", "/")
    file_dir = file_path.parent

    if any(ch in raw for ch in ("*", "?", "[", "]", "{", "}")):
        return {
            "status": "skipped_pattern",
            "resolved_path": None,
            "fix": None,
            "reason": "contains wildcard or pattern syntax; keep as illustrative literal",
        }

    resolved: Path | None = None

    if RE_WINDOWS_ABS.match(raw):
        candidate = Path(raw)
        if candidate.exists():
            try:
                candidate.relative_to(repo_root)
            except ValueError:
                return {
                    "status": "skipped_external",
                    "resolved_path": None,
                    "fix": None,
                    "reason": "absolute path points outside repo; keep as literal",
                }
            resolved = candidate.resolve()
    else:
        candidates: list[Path] = []
        if clean.startswith("/"):
            candidates.append((repo_root / clean.lstrip("/")).resolve())
        else:
            candidates.append((file_dir / clean).resolve())
            candidates.append((repo_root / clean).resolve())

        for candidate in candidates:
            if candidate.is_file() or candidate.is_dir():
                resolved = candidate
                break

    if resolved is not None:
        target = format_backtick_target(file_dir, resolved)
        return {
            "status": "fixable",
            "resolved_path": resolved,
            "fix": f"[`{raw}`]({target})",
            "reason": f"resolved to '{target}'",
        }

    basename = Path(clean.rstrip("/")).name
    if not basename:
        return {
            "status": "unresolved",
            "resolved_path": None,
            "fix": None,
            "reason": "empty path component after normalization",
        }

    matches = collision_index.get(basename, [])
    if len(matches) == 1:
        resolved = matches[0]
        target = format_backtick_target(file_dir, resolved)
        return {
            "status": "fixable",
            "resolved_path": resolved,
            "fix": f"[`{raw}`]({target})",
            "reason": f"unique basename match at '{target}'",
        }
    if len(matches) > 1:
        return {
            "status": "ambiguous",
            "resolved_path": None,
            "fix": None,
            "reason": f"basename '{basename}' exists in {len(matches)} repo locations",
        }
    return {
        "status": "unresolved",
        "resolved_path": None,
        "fix": None,
        "reason": f"no repo path resolves for '{raw}'",
    }


def audit_inert_backticks(
    file_path: Path,
    repo_root: Path,
    collision_index: dict[str, list[Path]],
) -> dict:
    """Audit inert backtick refs and classify which can be upgraded into links."""
    hits = scan_inert_backticks(file_path)
    results = []
    for hit in hits:
        diag = resolve_backtick_ref(hit, file_path, repo_root, collision_index)
        results.append(
            {
                "line": hit["line"],
                "text": hit["text"],
                "original": hit["original"],
                **diag,
            }
        )

    counts = {
        "fixable": sum(1 for item in results if item["status"] == "fixable"),
        "ambiguous": sum(1 for item in results if item["status"] == "ambiguous"),
        "unresolved": sum(1 for item in results if item["status"] == "unresolved"),
        "skipped_pattern": sum(1 for item in results if item["status"] == "skipped_pattern"),
        "skipped_external": sum(1 for item in results if item["status"] == "skipped_external"),
    }

    return {
        "file": str(file_path.relative_to(repo_root)),
        "inert_backtick_refs": len(results),
        **counts,
        "hits": results,
    }


def apply_backtick_fixes(file_path: Path, hits: list[dict]) -> int:
    """Apply fixable inert-backtick rewrites to a file."""
    fixable = [item for item in hits if item["fix"] is not None]
    if not fixable:
        return 0

    text = file_path.read_text(encoding="utf-8", errors="replace")
    applied = 0
    for item in fixable:
        old = item["original"]
        new = item["fix"]
        if old in text:
            text = text.replace(old, new, 1)
            applied += 1

    file_path.write_text(text, encoding="utf-8")
    return applied


# =============================================================================
# CLI
# =============================================================================

def main() -> int:
    configure_utf8_output()

    parser = argparse.ArgumentParser(
        description="Audit and fix markdown [label](path) references."
    )
    sub = parser.add_subparsers(dest="command")

    # check
    p_check = sub.add_parser("check", help="Audit links in a markdown file")
    p_check.add_argument("file", type=Path, help="File to audit")
    p_check.add_argument("--fix", action="store_true",
                         help="Apply fixes to the file in-place")
    p_check.add_argument("--dry-run", action="store_true",
                         help="Show what --fix would do without writing")

    # collisions
    p_coll = sub.add_parser("collisions", help="List all basename collisions in the repo")
    p_coll.add_argument("--min-count", type=int, default=2,
                        help="Minimum collision count to report (default: 2)")
    p_coll.add_argument("--filter", type=str, default=None,
                        help="Filter by extension (e.g., .md)")

    # backticks
    p_bt = sub.add_parser("backticks", help="Scan for inert backtick file/path refs outside code blocks")
    p_bt.add_argument("file", type=Path, help="File to scan")
    p_bt.add_argument("--fix", action="store_true", help="Upgrade fixable inert backticks to markdown links")
    p_bt.add_argument("--dry-run", action="store_true", help="Show what --fix would rewrite without writing")
    p_bt.add_argument("--json", dest="bt_json", action="store_true", help="JSON output")

    # scan
    p_scan = sub.add_parser("scan", help="Audit all markdown files in the repo")
    p_scan.add_argument("--fix", action="store_true",
                        help="Apply fixes to all files in-place")
    p_scan.add_argument("--dry-run", action="store_true",
                        help="Show what --fix would do without writing")

    # renames
    p_renames = sub.add_parser("renames", help="Audit markdown links against staged renames")
    p_renames.add_argument("--staged", action="store_true",
                           help="Use staged git renames as the source set")
    p_renames.add_argument("--fix", action="store_true",
                           help="Apply fixable replacements to affected markdown files")
    p_renames.add_argument("--dry-run", action="store_true",
                           help="Show what --fix would do without writing")

    # Common options
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--quiet", "-q", action="store_true")

    args = parser.parse_args()
    log = setup_logging(verbose=args.verbose, quiet=args.quiet)
    repo_root = find_repo_root()

    if not args.command:
        parser.print_help()
        return 0

    # --- backticks ---
    if args.command == "backticks":
        file_path = args.file.resolve()
        if not file_path.is_file():
            log.error("File not found: %s", file_path)
            return 1
        index = build_collision_index(repo_root)
        result = audit_inert_backticks(file_path, repo_root, index)
        use_json = getattr(args, "bt_json", False) or getattr(args, "json", False)
        if use_json:
            payload = dict(result)
            for item in payload["hits"]:
                if item.get("resolved_path"):
                    item["resolved_path"] = str(item["resolved_path"].relative_to(repo_root))
            print(json.dumps(payload, indent=2))
        else:
            if not result["hits"]:
                print(f"OK: {result['file']} — 0 inert backtick file/path refs")
            else:
                print(f"AUDIT: {result['file']}")
                print(
                    f"  Inert refs: {result['inert_backtick_refs']} total, "
                    f"{result['fixable']} fixable, {result['ambiguous']} ambiguous, "
                    f"{result['unresolved']} unresolved, "
                    f"{result['skipped_pattern'] + result['skipped_external']} skipped"
                )
                for hit in result["hits"]:
                    tag = {
                        "fixable": "FIXABLE",
                        "ambiguous": "AMBIG",
                        "unresolved": "UNRESOLVED",
                        "skipped_pattern": "SKIP",
                        "skipped_external": "SKIP",
                    }.get(hit["status"], hit["status"].upper())
                    print(f"\n  L{hit['line']} [{tag}] {hit['original']}")
                    print(f"    Reason: {hit['reason']}")
                    if hit["fix"]:
                        print(f"    Fix:    {hit['fix']}")

        if args.dry_run:
            print(f"\n--dry-run: {result['fixable']} fixes would be applied (no changes written)")
            return 0 if result["inert_backtick_refs"] == 0 else 1

        if args.fix and result["fixable"]:
            applied = apply_backtick_fixes(file_path, result["hits"])
            rerun = audit_inert_backticks(file_path, repo_root, index)
            print(f"\nApplied {applied} fix(es)")
            return 0 if rerun["inert_backtick_refs"] == 0 else 1

        return 1 if result["hits"] else 0

    # --- collisions ---
    if args.command == "collisions":
        log.info("Building file index from %s ...", repo_root)
        index = build_collision_index(repo_root)
        collisions = get_collisions(index)

        if args.filter:
            collisions = {
                k: v for k, v in collisions.items()
                if k.endswith(args.filter)
            }

        collisions = {
            k: v for k, v in collisions.items()
            if len(v) >= args.min_count
        }

        if args.json:
            out = {
                name: [str(p.relative_to(repo_root)) for p in paths]
                for name, paths in sorted(collisions.items(), key=lambda x: -len(x[1]))
            }
            print(json.dumps(out, indent=2))
        else:
            print(f"Basename collisions ({len(collisions)} names):\n")
            for name, paths in sorted(collisions.items(), key=lambda x: -len(x[1])):
                print(f"  {name} ({len(paths)} copies):")
                for p in sorted(paths):
                    print(f"    {p.relative_to(repo_root)}")
        return 0

    # --- renames ---
    if args.command == "renames":
        if not args.staged:
            log.error("renames currently requires --staged")
            return 1

        renames = load_staged_renames(repo_root)
        if not renames:
            print("No staged renames found.")
            return 0

        markdown_files = scan_repo_markdown(repo_root)
        results = []
        for file_path in markdown_files:
            result = audit_file_against_staged_renames(file_path, repo_root, renames)
            if result["issues"]:
                results.append(result)

        impacted_files = len(results)
        impacted_issues = sum(len(result["issues"]) for result in results)

        if args.json and not args.fix and not args.dry_run:
            print(json.dumps({
                "staged_renames": [
                    {
                        "status": rename["status"],
                        "old_rel": rename["old_rel"],
                        "new_rel": rename["new_rel"],
                    }
                    for rename in renames
                ],
                "impacted_files": impacted_files,
                "impacted_issues": impacted_issues,
                "results": results,
            }, indent=2))
            return 0 if impacted_issues == 0 else 1

        print(f"STAGED RENAMES: {len(renames)}")
        print(f"IMPACTED FILES: {impacted_files}")
        print(f"FIXABLE LINKS: {impacted_issues}")

        for result in results:
            print(f"\nAUDIT: {result['file']}")
            for issue in result["issues"]:
                print(f"  L{issue['line']} [STAGED] {issue['original']}")
                print(f"    Reason: {issue['reason']}")
                print(f"    Fix:    {issue['fix']}")

        if args.dry_run:
            print(f"\n--dry-run: {impacted_issues} fixes would be applied across {impacted_files} files")
            return 0 if impacted_issues == 0 else 1

        if args.fix and impacted_issues:
            applied = 0
            touched = 0
            for result in results:
                file_path = repo_root / result["file"]
                count = apply_fixes(file_path, result["issues"])
                if count:
                    touched += 1
                    applied += count
            print(f"\nApplied {applied} fix(es) across {touched} file(s)")
            return 0 if applied == impacted_issues else 1

        return 0 if impacted_issues == 0 else 1

    # --- scan ---
    if args.command == "scan":
        log.info("Building file index ...")
        index = build_collision_index(repo_root)
        md_files = scan_repo_markdown(repo_root)
        log.info("Scanning %d markdown files ...", len(md_files))

        all_results = []
        for md_file in md_files:
            result = audit_file(md_file, repo_root, index)
            if result["issues"]:
                all_results.append(result)

        total_files = len(md_files)
        impacted_files = len(all_results)
        total_issues = sum(len(r["issues"]) for r in all_results)
        total_fixable = sum(r["fixable"] for r in all_results)
        total_broken = sum(r["broken"] for r in all_results)
        total_ambiguous = sum(r["ambiguous"] for r in all_results)

        if args.json and not args.fix and not args.dry_run:
            for result in all_results:
                for item in result.get("all", []):
                    if item.get("resolved_path"):
                        item["resolved_path"] = str(item["resolved_path"].relative_to(repo_root))
                for item in result.get("issues", []):
                    if item.get("resolved_path"):
                        item["resolved_path"] = str(item["resolved_path"].relative_to(repo_root))
            print(json.dumps({
                "total_files": total_files,
                "impacted_files": impacted_files,
                "total_issues": total_issues,
                "total_fixable": total_fixable,
                "total_broken": total_broken,
                "total_ambiguous": total_ambiguous,
                "results": all_results,
            }, indent=2))
            return 0 if total_issues == 0 else 1

        if not all_results:
            print(f"OK: {total_files} files scanned, all links valid")
            return 0

        print(f"SCAN: {total_files} files, {impacted_files} with issues")
        print(f"  Issues: {total_issues} total — {total_broken} broken, "
              f"{total_ambiguous} ambiguous, {total_fixable} fixable")

        for result in all_results:
            print(f"\n  {result['file']}:")
            for issue in result["issues"]:
                tag = {
                    "broken": "BROKEN",
                    "broken_anchor": "ANCHOR",
                    "ambiguous": "AMBIG",
                    "collision_unlabeled": "LABEL",
                }.get(issue["status"], issue["status"].upper())
                fix_hint = f" -> {issue['fix']!r}" if issue["fix"] is not None else ""
                print(f"    L{issue['line']} [{tag}] {issue['original']}{fix_hint}")

        if args.dry_run:
            print(f"\n--dry-run: {total_fixable} fixes would be applied "
                  f"across {impacted_files} file(s) (no changes written)")
            return 0 if total_issues == 0 else 1

        if args.fix and total_fixable:
            applied = 0
            touched = 0
            for result in all_results:
                file_path = repo_root / result["file"]
                count = apply_fixes(file_path, result["issues"])
                if count:
                    touched += 1
                    applied += count
            print(f"\nApplied {applied} fix(es) across {touched} file(s)")
            return 0 if applied == total_fixable else 1

        if total_fixable and not args.fix:
            print(f"\n{total_fixable} fixable issue(s). "
                  f"Run with --fix to apply or --dry-run to preview.")

        return 1 if total_issues else 0

    # --- check ---
    if args.command == "check":
        file_path = args.file.resolve()
        if not file_path.is_file():
            log.error("File not found: %s", file_path)
            return 1

        log.info("Building file index ...")
        index = build_collision_index(repo_root)

        result = audit_file(file_path, repo_root, index)

        if args.json and not args.dry_run and not args.fix:
            # Strip non-serializable Path objects
            for item in result.get("all", []):
                if item.get("resolved_path"):
                    item["resolved_path"] = str(item["resolved_path"].relative_to(repo_root))
            for item in result.get("issues", []):
                if item.get("resolved_path"):
                    item["resolved_path"] = str(item["resolved_path"].relative_to(repo_root))
            print(json.dumps(result, indent=2))
            return 0 if not result["issues"] else 1

        # Human output
        issues = result["issues"]
        fixable = [i for i in issues if i["fix"] is not None]

        if not issues:
            print(f"OK: {result['file']} — {result['total_links']} links, all valid")
            return 0

        print(f"AUDIT: {result['file']}")
        print(f"  Links: {result['total_links']} total, {result['ok']} ok, "
              f"{result['broken']} broken, {result['ambiguous']} ambiguous, "
              f"{result['collision_unlabeled']} unlabeled collisions")

        for issue in issues:
            status_icon = {
                "broken": "BROKEN",
                "broken_anchor": "ANCHOR",
                "ambiguous": "AMBIG",
                "collision_unlabeled": "LABEL",
            }.get(issue["status"], issue["status"].upper())
            print(f"\n  L{issue['line']} [{status_icon}] {issue['original']}")
            print(f"    Reason: {issue['reason']}")
            if issue["fix"] is not None:
                print(f"    Fix:    {issue['fix']!r}")

        if args.dry_run:
            print(f"\n--dry-run: {len(fixable)} fixes would be applied (no changes written)")
            return 1 if issues else 0

        if args.fix and fixable:
            applied = apply_fixes(file_path, issues)
            print(f"\nApplied {applied} fix(es) to {result['file']}")
            return 0 if applied == len(fixable) else 1

        if fixable and not args.fix:
            print(f"\n{len(fixable)} fixable issue(s). Run with --fix to apply or --dry-run to preview.")

        return 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
