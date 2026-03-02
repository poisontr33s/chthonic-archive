#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: git_snapshot.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Git Snapshot — session-resumption state capture.

Captures current git state (branch, recent commits, working tree, diff stats,
24h velocity) and writes a structured markdown snapshot to the mailbox.
Agents read the snapshot instead of burning tokens on git exploration.

@SID:           TOOL_GIT_SNAPSHOT_V1
@Type:          Utility
@Spectrum:      WHITE
@Zone:          THE GARDEN

Usage:
    uv run scripts/git_snapshot.py                # standard snapshot (15 commits)
    uv run scripts/git_snapshot.py full            # extended (30 commits, author info)
    uv run scripts/git_snapshot.py diff            # uncommitted changes only
    uv run scripts/git_snapshot.py --json          # JSON output to stdout
    uv run scripts/git_snapshot.py --emit PATH     # write to custom path instead of mailbox
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from scripts.lib.shared import configure_utf8_output, find_repo_root, setup_logging

# =============================================================================
# Constants
# =============================================================================

MAILBOX_REL = Path("claude/mailbox")
SNAPSHOT_FILENAME = "GIT_SNAPSHOT_LATEST.md"
COMMIT_COUNT_DEFAULT = 15
COMMIT_COUNT_FULL = 30


# =============================================================================
# Git helpers (recycled from scm_triage.py subprocess pattern)
# =============================================================================

def _git(repo: Path, *args: str) -> str:
    """Run a git command and return stdout. Returns empty string on failure."""
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        cwd=repo,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def get_branch(repo: Path) -> str:
    return _git(repo, "branch", "--show-current") or "(detached)"


def get_log_oneline(repo: Path, count: int) -> list[str]:
    raw = _git(repo, "log", f"--oneline", f"-{count}")
    return raw.splitlines() if raw else []


def get_log_full(repo: Path, count: int) -> list[str]:
    raw = _git(repo, "log", f"--format=%h %s (%an, %ar)", f"-{count}")
    return raw.splitlines() if raw else []


def get_status_short(repo: Path) -> list[str]:
    raw = _git(repo, "status", "--short")
    return raw.splitlines() if raw else []


def get_diff_stat(repo: Path) -> list[str]:
    raw = _git(repo, "diff", "--stat")
    return raw.splitlines() if raw else []


def get_velocity_24h(repo: Path) -> list[str]:
    raw = _git(repo, "log", "--oneline", "--since=24 hours ago")
    return raw.splitlines() if raw else []


def get_head_sha(repo: Path) -> str:
    return _git(repo, "rev-parse", "--short", "HEAD") or "unknown"


def get_remote_url(repo: Path) -> str:
    return _git(repo, "remote", "get-url", "origin") or "no remote"


# =============================================================================
# Snapshot Assembly
# =============================================================================

def build_snapshot(repo: Path, mode: str) -> dict:
    """Collect git state into a structured dict."""
    branch = get_branch(repo)
    status_lines = get_status_short(repo)
    is_clean = len(status_lines) == 0
    now = datetime.now(timezone.utc)

    data: dict = {
        "timestamp": now.isoformat(),
        "branch": branch,
        "head": get_head_sha(repo),
        "remote": get_remote_url(repo),
        "clean": is_clean,
        "mode": mode,
    }

    if mode != "diff":
        count = COMMIT_COUNT_FULL if mode == "full" else COMMIT_COUNT_DEFAULT
        if mode == "full":
            data["commits"] = get_log_full(repo, count)
        else:
            data["commits"] = get_log_oneline(repo, count)
        data["velocity_24h"] = get_velocity_24h(repo)

    data["status"] = status_lines if status_lines else ["Clean"]
    data["diff_stat"] = get_diff_stat(repo) if not is_clean else []

    return data


def render_markdown(data: dict) -> str:
    """Render snapshot dict to frontmatter-headed markdown."""
    ts = data["timestamp"]
    date_str = ts[:10]

    lines: list[str] = [
        "---",
        "type: git-snapshot",
        "from: git-snapshot-tool",
        "to: claude",
        f"created: {ts}",
        "priority: low",
        "scope: session-resumption",
        "---",
        "",
        f"# Git Snapshot — {date_str}",
        "",
        f"**Branch:** {data['branch']}",
        f"**HEAD:** {data['head']}",
        f"**Remote:** {data['remote']}",
        f"**Clean:** {'yes' if data['clean'] else 'no'}",
        "",
    ]

    if "commits" in data and data["commits"]:
        n = len(data["commits"])
        lines.append(f"## Recent Commits (last {n})")
        lines.append("")
        for c in data["commits"]:
            lines.append(f"- {c}")
        lines.append("")

    if "velocity_24h" in data:
        v = data["velocity_24h"]
        lines.append(f"## Today's Velocity (last 24h)")
        lines.append("")
        lines.append(f"{len(v)} commits")
        if v:
            lines.append("")
            for c in v:
                lines.append(f"- {c}")
        lines.append("")

    lines.append("## Working Tree")
    lines.append("")
    for s in data.get("status", ["Clean"]):
        lines.append(f"    {s}")
    lines.append("")

    if data.get("diff_stat"):
        lines.append("## Uncommitted Diff Stats")
        lines.append("")
        for d in data["diff_stat"]:
            lines.append(f"    {d}")
        lines.append("")

    return "\n".join(lines)


def render_json(data: dict) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)


# =============================================================================
# CLI
# =============================================================================

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Git Snapshot — session-resumption state capture.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Modes:\n"
            "  (default)  15 recent commits, status, diff stats\n"
            "  full       30 commits with author/age, status, diff stats\n"
            "  diff       Uncommitted changes only (no commit history)\n"
        ),
    )
    p.add_argument(
        "mode",
        nargs="?",
        default="default",
        choices=["default", "full", "diff"],
        help="Snapshot mode (default: standard 15-commit snapshot)",
    )
    p.add_argument("--json", action="store_true", help="Output as JSON to stdout")
    p.add_argument(
        "--emit",
        metavar="PATH",
        help="Write snapshot to custom path instead of mailbox",
    )
    p.add_argument("--verbose", "-v", action="store_true", help="Debug logging")
    p.add_argument("--quiet", "-q", action="store_true", help="Suppress info output")
    return p


def main() -> int:
    configure_utf8_output()
    parser = build_parser()
    args = parser.parse_args()
    log = setup_logging(verbose=args.verbose, quiet=args.quiet)

    repo = find_repo_root()
    log.info("Repository root: %s", repo)

    data = build_snapshot(repo, args.mode)

    # JSON to stdout
    if args.json:
        print(render_json(data))
        return 0

    md = render_markdown(data)

    # Determine output path
    if args.emit:
        out_path = Path(args.emit)
    else:
        out_path = repo / MAILBOX_REL / SNAPSHOT_FILENAME

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md, encoding="utf-8")
    log.info("Snapshot written to %s", out_path)

    if not args.quiet:
        print(f"✓ Git snapshot → {out_path.relative_to(repo)}")
        print(f"  Branch: {data['branch']}  HEAD: {data['head']}  Clean: {data['clean']}")
        if "commits" in data:
            print(f"  Commits: {len(data['commits'])}  24h velocity: {len(data.get('velocity_24h', []))}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
