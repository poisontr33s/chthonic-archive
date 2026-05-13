#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: link_audit_author.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Wraps: link_audit.py scan with per-author file filter)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Link Audit (Author Filter) — Run link_audit.py scan against only files
that the configured author(s) actually committed. Honors the "I only want
to validate MY work, not vendored readmes / submodule docs" workflow.

@SID:           TOOL_LINK_AUDIT_AUTHOR_V1
@Shabti:        Guardian
@Context:       Infrastructure / Pathfinder author scoping
@Implements:    Author-filtered pathfinder scan (chthonic-archive #C-landing)
@Purpose:       Build a path -> {authors} map once via `git log --all`, filter
                markdown files to those committed by the requested author(s),
                and hand the narrowed file list to scripts/link_audit.py.

Usage:
    uv run scripts/link_audit_author.py --author-self
    uv run scripts/link_audit_author.py --author eldnordd@gmail.com
    uv run scripts/link_audit_author.py --author a@x --author b@y
    uv run scripts/link_audit_author.py --author-self --changed-only
    uv run scripts/link_audit_author.py --author-self --repo ../PsychoNoir-Kontrapunkt
    uv run scripts/link_audit_author.py --author-self --report manifest/link_audit_author.json

Flags:
    --author EMAIL        Email to filter by (repeatable for multi-identity)
    --author-self         Auto-include `git config user.email` in filter
    --changed-only        Intersect with `git diff --name-only HEAD`
    --repo PATH           Repo root to operate against (default: cwd's git root)
    --report PATH         Write JSON summary to this path
    --dry-run             Don't invoke link_audit.py, just print the file list
    --no-cache            Bypass author-map cache (slower)
    --pass-through ARG    Forward an extra arg to link_audit.py (repeatable)

Cache:
    Author map cached at <repo>/.git/info/author-map.json keyed on HEAD SHA.
    Re-running with the same HEAD is O(1). Bust the cache with --no-cache.

Exit codes:
    0  link_audit.py passed
    1  link_audit.py found issues
    2  no files matched the author filter (treated as success but reported)
    3  invocation error (missing git, bad flags, etc.)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


COMMIT_SENTINEL = "__COMMIT__"


def run_git(repo_root: Path, args: list[str]) -> str:
    """Run git in repo_root, return stdout text. Raises on failure."""
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def find_repo_root(start: Path) -> Path:
    out = subprocess.run(
        ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if out.returncode != 0:
        raise RuntimeError(f"Not a git repo: {start}")
    return Path(out.stdout.strip())


def head_sha(repo_root: Path) -> str:
    return run_git(repo_root, ["rev-parse", "HEAD"]).strip()


def build_author_map(repo_root: Path) -> dict[str, set[str]]:
    """
    Map relative-path-string -> set of author emails who committed (added/modified) that path.
    One git invocation; O(commits + paths) parse.
    """
    output = run_git(
        repo_root,
        ["log", "--all", "--name-only", f"--format={COMMIT_SENTINEL}%ae",
         "--diff-filter=AM"],
    )
    mapping: dict[str, set[str]] = defaultdict(set)
    current_email: str | None = None
    for line in output.splitlines():
        if line.startswith(COMMIT_SENTINEL):
            current_email = line[len(COMMIT_SENTINEL):].strip().lower() or None
            continue
        if not line.strip() or current_email is None:
            continue
        mapping[line.strip()].add(current_email)
    return dict(mapping)


def load_or_build_author_map(repo_root: Path, *, use_cache: bool) -> dict[str, set[str]]:
    if not use_cache:
        return build_author_map(repo_root)

    cache_path = repo_root / ".git" / "info" / "author-map.json"
    sha = head_sha(repo_root)

    if cache_path.exists():
        try:
            blob = json.loads(cache_path.read_text(encoding="utf-8"))
            if blob.get("head") == sha and isinstance(blob.get("map"), dict):
                return {k: set(v) for k, v in blob["map"].items()}
        except (json.JSONDecodeError, OSError):
            pass

    mapping = build_author_map(repo_root)
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps({"head": sha, "map": {k: sorted(v) for k, v in mapping.items()}}),
            encoding="utf-8",
        )
    except OSError:
        pass
    return mapping


def changed_files(repo_root: Path) -> set[str]:
    out = run_git(repo_root, ["diff", "--name-only", "HEAD"])
    return {ln.strip() for ln in out.splitlines() if ln.strip()}


def collect_markdown(repo_root: Path) -> list[str]:
    """List tracked markdown files relative to repo_root."""
    out = run_git(repo_root, ["ls-files", "*.md", "*.MD"])
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def resolve_authors(args: argparse.Namespace, repo_root: Path) -> set[str]:
    authors: set[str] = set()
    if args.author:
        authors.update(a.lower() for a in args.author)
    if args.author_self:
        email = run_git(repo_root, ["config", "user.email"]).strip().lower()
        if email:
            authors.add(email)
    return authors


def filter_by_author(
    files: list[str],
    author_map: dict[str, set[str]],
    target_authors: set[str],
) -> list[str]:
    if not target_authors:
        return files
    kept: list[str] = []
    for f in files:
        commit_authors = author_map.get(f, set())
        if not commit_authors:
            # Newly created uncommitted files — include by default (user-authored locally)
            kept.append(f)
            continue
        if commit_authors & target_authors:
            kept.append(f)
    return kept


def invoke_link_audit(repo_root: Path, files: list[str], extra: list[str]) -> int:
    """
    Call link_audit.py scan with the narrowed file set.

    Windows CreateProcess caps the command line at 32,767 chars; passing ~1000
    paths in one shot overflows it (WinError 206). Batch into chunks that stay
    well under the cap and aggregate the worst exit code.
    """
    if not files:
        return 0

    mode_flag = "--fix" if "--apply-fixes" in extra else "--dry-run"
    cleaned_extra = [a for a in extra if a != "--apply-fixes"]
    base_cmd = ["uv", "run", "scripts/link_audit.py", "scan", mode_flag, "--paths"]
    extra = cleaned_extra
    fixed_len = sum(len(part) + 1 for part in base_cmd) + sum(len(x) + 1 for x in extra)
    max_cmdline = 28000  # conservative ceiling vs the 32767 Windows limit

    batches: list[list[str]] = []
    current: list[str] = []
    current_len = fixed_len
    for f in files:
        addition = len(f) + 1
        if current and current_len + addition > max_cmdline:
            batches.append(current)
            current = [f]
            current_len = fixed_len + addition
        else:
            current.append(f)
            current_len += addition
    if current:
        batches.append(current)

    worst_rc = 0
    for i, batch in enumerate(batches, 1):
        print(f"[link_audit_author] batch {i}/{len(batches)} - {len(batch)} files")
        cmd = [*base_cmd, *batch, *extra]
        result = subprocess.run(cmd, cwd=str(repo_root))
        if result.returncode > worst_rc:
            worst_rc = result.returncode
    return worst_rc


def main() -> int:
    parser = argparse.ArgumentParser(prog="link_audit_author")
    parser.add_argument("--author", action="append", default=[],
                        help="Email to filter by (repeatable)")
    parser.add_argument("--author-self", action="store_true",
                        help="Auto-include git config user.email")
    parser.add_argument("--changed-only", action="store_true",
                        help="Intersect file set with git diff --name-only HEAD")
    parser.add_argument("--repo", type=Path, default=Path.cwd(),
                        help="Repo root (default: cwd's git root)")
    parser.add_argument("--report", type=Path, default=None,
                        help="Write JSON summary to this path")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print files but skip link_audit invocation")
    parser.add_argument("--no-cache", action="store_true",
                        help="Bypass the .git/info/author-map.json cache")
    parser.add_argument("--pass-through", action="append", default=[],
                        help="Extra arg to forward to link_audit.py (repeatable)")
    parser.add_argument("--apply-fixes", action="store_true",
                        help="Run link_audit.py with --fix instead of --dry-run (writes .bak backups)")
    args = parser.parse_args()

    try:
        repo_root = find_repo_root(args.repo)
    except RuntimeError as exc:
        print(f"[link_audit_author] ERROR: {exc}", file=sys.stderr)
        return 3

    target_authors = resolve_authors(args, repo_root)
    if not target_authors:
        print("[link_audit_author] ERROR: no authors specified — use --author or --author-self",
              file=sys.stderr)
        return 3

    author_map = load_or_build_author_map(repo_root, use_cache=not args.no_cache)
    all_md = collect_markdown(repo_root)
    filtered = filter_by_author(all_md, author_map, target_authors)

    if args.changed_only:
        changed = changed_files(repo_root)
        filtered = [f for f in filtered if f in changed]

    print(f"[link_audit_author] repo={repo_root.name} authors={sorted(target_authors)} "
          f"total_md={len(all_md)} author_md={len(filtered)}"
          + (f" changed={'on' if args.changed_only else 'off'}" if args.changed_only else ""))

    summary = {
        "repo": str(repo_root),
        "authors": sorted(target_authors),
        "totalMarkdown": len(all_md),
        "authorFilteredCount": len(filtered),
        "changedOnly": args.changed_only,
        "files": filtered,
    }

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    if not filtered:
        print("[link_audit_author] no files matched — nothing to audit")
        summary["exitCode"] = 2
        return 2

    if args.dry_run:
        for f in filtered:
            print(f"  {f}")
        summary["exitCode"] = 0
        return 0

    extra_args = list(args.pass_through)
    if args.apply_fixes:
        extra_args.append("--apply-fixes")
    rc = invoke_link_audit(repo_root, filtered, extra_args)
    summary["linkAuditExitCode"] = rc
    if args.report:
        args.report.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
