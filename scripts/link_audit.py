#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""
Link Audit — Validate and fix markdown [label](path) references in files.

Scans markdown files for broken or ambiguous internal links, detects basename
collisions, and optionally rewrites fixable references in-place.

@SID:           TOOL_LINK_AUDIT_V1
@Type:          Guardian
@Context:       Infrastructure / Markdown Quality Gate
@Implements:    Path-Link Disambiguation Canon (SESSION_HANDOFF_2026_02_27)

Usage:
    uv run scripts/link_audit.py check <file>              # audit one file
    uv run scripts/link_audit.py check <file> --fix        # audit + rewrite fixes
    uv run scripts/link_audit.py check <file> --dry-run    # show fixes without writing
    uv run scripts/link_audit.py collisions                 # list all basename collisions in repo
    uv run scripts/link_audit.py collisions --json          # JSON output
"""

from __future__ import annotations

import argparse
import json
import os
import re
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
EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "tel:", "#", "ftp://")

# Directories to skip during collision scanning
SKIP_DIRS = {
    ".git", "node_modules", "target", "__pycache__", ".venv",
    "build", "dist", ".mypy_cache", ".ruff_cache",
}

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
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
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
        # Strip inline code spans before scanning for links
        scanline = re.sub(r"`[^`]+`", "", line)
        for match in RE_MD_LINK.finditer(scanline):
            full, label, target = match.group(1), match.group(2), match.group(3)
            # Skip external links
            if any(target.startswith(p) for p in EXTERNAL_PREFIXES):
                continue
            # Strip fragment anchors for path resolution
            path_part = target.split("#")[0] if "#" in target else target
            if not path_part:
                continue  # pure anchor link like [foo](#bar)
            results.append({
                "line": lineno,
                "full_match": full,
                "label": label,
                "target": target,
                "path_part": path_part,
            })
    return results


def resolve_link(
    link: dict,
    file_path: Path,
    repo_root: Path,
    collision_index: dict[str, list[Path]],
) -> dict:
    """Resolve a single link and return a diagnostic record.

    Returns a dict with:
        status: "ok" | "broken" | "ambiguous" | "collision_unlabeled"
        resolved_path: the resolved Path (or None)
        fix: suggested replacement string (or None)
        reason: human-readable explanation
    """
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
    if candidate_rel.is_file():
        resolved = candidate_rel
    elif candidate_root.is_file():
        resolved = candidate_root

    basename = Path(clean).name

    # Case 1: target resolves to a real file → OK, but check collision labeling
    if resolved is not None:
        # Check if the basename has collisions
        siblings = collision_index.get(basename, [])
        if len(siblings) > 1:
            # The link works, but the basename is ambiguous in the repo.
            # Check if the label includes a directory qualifier
            label = link["label"]
            if basename in label and "(" not in label and "/" not in label:
                # Label is just the basename — recommend disambiguation
                rel_path = resolved.relative_to(repo_root)
                parent_hint = rel_path.parent.name or str(rel_path.parent)
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

    # Case 3: no match at all
    return {
        "status": "broken",
        "resolved_path": None,
        "fix": None,
        "reason": f"Path '{target_str}' not found and no file named '{basename}' exists in repo",
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
    broken = [r for r in results if r["status"] == "broken"]
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
                "ambiguous": "AMBIG",
                "collision_unlabeled": "LABEL",
            }.get(issue["status"], issue["status"].upper())
            print(f"\n  L{issue['line']} [{status_icon}] {issue['original']}")
            print(f"    Reason: {issue['reason']}")
            if issue["fix"]:
                print(f"    Fix:    {issue['fix']}")

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
