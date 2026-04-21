#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: scm_triage.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
SCM Triage — Source Control Noise Reduction & Codebase Structurization.

Audits git status, classifies changes as signal/noise/transient/ghost,
generates gitignore/exclude recommendations, and produces structured
migration plans for ANKH-aligned file relocation.

@SID:           TOOL_SCM_TRIAGE_V1
@Shabti:          Utility
@Purpose:       SCM Triage — Source Control Noise Reduction & Codebase Structurization.
"""

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# sys.path guard: ensure repo root is importable regardless of invocation CWD
_REPO_ROOT_CANDIDATE = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT_CANDIDATE) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT_CANDIDATE))

from scripts.lib.shared import configure_utf8_output, find_repo_root, setup_logging

# =============================================================================
# Classification Rules
# =============================================================================

# Patterns for NOISE (transient outputs, never meaningful to track)
NOISE_PATTERNS = [
    r"dumpster-dive/intake/overnight-daemon/\d{8}_\d{6}/classifications/",
    r"dumpster-dive/intake/overnight-daemon/\d{8}_\d{6}/report\.(json|md)",
    r"dumpster-dive/intake/overnight-daemon/\d{8}_\d{6}/run\.json",
    r"dumpster-dive/intake/overnight-daemon/\d{8}_\d{6}/\.keep",
    r"\.tmp_fixture_eval/",
    r"__pycache__/",
    r"\.pyc$",
    r"\.log$",
    r"node_modules/",
    r"\.chthonic/cache/",
]

# Patterns for MAILBOX (agent deliverables awaiting integration)
MAILBOX_PATTERNS = [
    r"^claude/mailbox/",
    r"^codex/mailbox/",
    r"^gemini/mailbox/",
]

# Patterns for SIGNAL (intentional changes that matter)
SIGNAL_PATTERNS = [
    r"^\.gitignore$",
    r"^\.gitattributes$",
    r"^scripts/",
    r"^extensions/",
    r"^src/",
    r"^mas_mcp/",
    r"^game/",
    r"^\.temple/",
    r"^\.github/",
    r"^\.claude/skills/",
    r"^\.codex/skills/",
    r"^assets/",
    r"^claude-codex-gemini/",
    r"^docs/",
    r"^data/",
    r"^Cargo\.toml$",
    r"^package\.json$",
    r"^pyproject\.toml$",
    r"^tsconfig",
]

# Canonical directory structure per ANKH
CANONICAL_DIRS = {
    "scripts":      "Tools and automation scripts",
    "extensions":   "VS Code extension code",
    "game":         "cRPG content (lore, systems, dialogue)",
    ".temple":      "Protocols, methodology, handoffs",
    "claude":       "Claude agent lane",
    "codex":        "Codex agent lane",
    "gemini":       "Gemini agent lane",
    "dumpster-dive":"Intake, siphon, archive",
    "assets":       "Static resources (shaders, data, art)",
    "src":          "Rust/Vulkan source",
    "mas_mcp":      "Python MCP backend",
    "docs":         "Documentation",
    "data":         "Structured data files",
}


def git_status_porcelain(repo_root: Path) -> list[dict]:
    """Parse git status --porcelain into structured entries."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, cwd=repo_root,
        encoding="utf-8", errors="replace",
    )
    entries = []
    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue
        xy = line[:2]
        filepath = line[3:].strip()
        # Handle renames: "R  old -> new"
        if " -> " in filepath:
            filepath = filepath.split(" -> ")[1]
        entries.append({
            "status": xy,
            "path": filepath,
            "index": xy[0],
            "worktree": xy[1],
        })
    return entries


def classify_entry(entry: dict) -> str:
    """Classify a git status entry as SIGNAL, NOISE, GHOST, or MAILBOX."""
    path = entry["path"]
    status = entry["status"]

    # GHOST: tracked file deleted from disk
    if status.strip() == "D" or entry["index"] == "D":
        return "GHOST"

    # NOISE: matches transient output patterns
    for pattern in NOISE_PATTERNS:
        if re.search(pattern, path):
            return "NOISE"

    # MAILBOX: agent deliverables
    for pattern in MAILBOX_PATTERNS:
        if re.search(pattern, path):
            return "MAILBOX"

    # SIGNAL: intentional changes
    for pattern in SIGNAL_PATTERNS:
        if re.search(pattern, path):
            return "SIGNAL"

    # Default: classify by directory depth
    parts = Path(path).parts
    if len(parts) >= 2 and parts[0] in CANONICAL_DIRS:
        return "SIGNAL"

    return "NOISE"


def group_by_directory(entries: list[dict]) -> dict[str, list[dict]]:
    """Group entries by top-level directory."""
    groups = defaultdict(list)
    for entry in entries:
        parts = Path(entry["path"]).parts
        top = parts[0] if parts else "(root)"
        groups[top].append(entry)
    return dict(sorted(groups.items()))


def audit(repo_root: Path, logger) -> dict:
    """Phase 1: Audit git status and classify all changes."""
    entries = git_status_porcelain(repo_root)
    classified = {"SIGNAL": [], "NOISE": [], "GHOST": [], "MAILBOX": []}

    for entry in entries:
        category = classify_entry(entry)
        entry["classification"] = category
        classified[category].append(entry)

    by_dir = group_by_directory(entries)

    # Summary by status code
    status_counts = defaultdict(int)
    for e in entries:
        status_counts[e["status"]] += 1

    result = {
        "total_changes": len(entries),
        "by_classification": {k: len(v) for k, v in classified.items()},
        "by_directory": {k: len(v) for k, v in by_dir.items()},
        "by_status": dict(status_counts),
        "signal": [e["path"] for e in classified["SIGNAL"]],
        "noise": [e["path"] for e in classified["NOISE"]],
        "ghost": [e["path"] for e in classified["GHOST"]],
        "mailbox": [e["path"] for e in classified["MAILBOX"]],
    }

    # Print audit summary
    print(f"\n{'='*60}")
    print(f"  SCM TRIAGE AUDIT — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}")
    print(f"\n  Total changes: {result['total_changes']}")
    print(f"  ├── SIGNAL:  {result['by_classification']['SIGNAL']:>4}  (intentional changes)")
    print(f"  ├── NOISE:   {result['by_classification']['NOISE']:>4}  (transient outputs)")
    print(f"  ├── GHOST:   {result['by_classification']['GHOST']:>4}  (deleted but tracked)")
    print(f"  └── MAILBOX: {result['by_classification']['MAILBOX']:>4}  (agent deliverables)")

    if by_dir:
        print(f"\n  By directory:")
        for d, count in sorted(by_dir.items(), key=lambda x: -len(x[1])):
            print(f"    {d:<30} {len(count):>4}")

    if classified["GHOST"]:
        print(f"\n  ⚠ GHOST entries (need git rm --cached):")
        for path in result["ghost"][:10]:
            print(f"    D  {path}")
        if len(result["ghost"]) > 10:
            print(f"    ... and {len(result['ghost']) - 10} more")

    if classified["NOISE"]:
        print(f"\n  🔇 NOISE entries (candidates for .gitignore):")
        for path in result["noise"][:10]:
            print(f"    ??  {path}")
        if len(result["noise"]) > 10:
            print(f"    ... and {len(result['noise']) - 10} more")

    print()
    return result


def generate_fix_recommendations(audit_result: dict) -> dict:
    """Phase 2: Generate gitignore/exclude recommendations."""
    gitignore_additions = set()
    exclude_additions = set()
    ghost_removals = []

    # Ghost files need git rm --cached
    for path in audit_result["ghost"]:
        ghost_removals.append(path)

    # Noise files need gitignore or exclude patterns
    for path in audit_result["noise"]:
        # Find the most specific directory pattern
        p = Path(path)
        parts = p.parts
        if len(parts) >= 3:
            # Use the parent directory as the pattern
            pattern = "/".join(parts[:-1]) + "/"
            gitignore_additions.add(pattern)
        elif len(parts) >= 2:
            pattern = "/".join(parts[:-1]) + "/"
            gitignore_additions.add(pattern)
        else:
            gitignore_additions.add(path)

    return {
        "gitignore_additions": sorted(gitignore_additions),
        "exclude_additions": sorted(exclude_additions),
        "ghost_removals": ghost_removals,
    }


def suppress_noise(repo_root: Path, recommendations: dict, dry_run: bool = True) -> dict:
    """Apply noise suppression: append to .gitignore, skip-worktree ghosts.

    Args:
        repo_root: Repository root path.
        recommendations: Output of generate_fix_recommendations().
        dry_run: If True, report what would change without writing anything.

    Returns:
        Dict with applied/skipped counts and details.
    """
    gitignore_path = repo_root / ".gitignore"
    existing_lines: set[str] = set()
    if gitignore_path.exists():
        existing_lines = {
            ln.strip()
            for ln in gitignore_path.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.strip().startswith("#")
        }

    new_patterns = [
        p for p in recommendations.get("gitignore_additions", [])
        if p not in existing_lines
    ]
    ghost_removals = recommendations.get("ghost_removals", [])

    result = {
        "dry_run": dry_run,
        "gitignore_added": new_patterns,
        "gitignore_already_present": len(recommendations.get("gitignore_additions", [])) - len(new_patterns),
        "ghost_skip_worktree": [],
        "ghost_skip_worktree_failed": [],
    }

    if dry_run:
        result["ghost_skip_worktree"] = ghost_removals
        return result

    # Append new patterns to .gitignore
    if new_patterns:
        with open(gitignore_path, "a", encoding="utf-8") as f:
            f.write("\n# Auto-suppressed by mas_scm_suppress\n")
            for pattern in new_patterns:
                f.write(f"{pattern}\n")

    # Apply skip-worktree to ghost files (tracked but deleted — hide from status)
    for ghost_path in ghost_removals:
        r = subprocess.run(
            ["git", "update-index", "--skip-worktree", ghost_path],
            capture_output=True, text=True, cwd=repo_root,
            encoding="utf-8", errors="replace",
        )
        if r.returncode == 0:
            result["ghost_skip_worktree"].append(ghost_path)
        else:
            result["ghost_skip_worktree_failed"].append(
                {"path": ghost_path, "error": r.stderr.strip()}
            )

    return result


def write_plan(repo_root: Path, audit_result: dict, fix_recs: dict) -> Path:
    """Phase 3: Write structured triage plan to mailbox."""
    plan = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "tool": "TOOL_SCM_TRIAGE_V1",
        "audit": audit_result,
        "noise_fixes": fix_recs,
        "migrations": [],  # Phase 3 migration planning (future)
    }

    output_path = repo_root / "claude" / "mailbox" / "SCM_TRIAGE_PLAN.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)

    print(f"  Plan written to: {output_path.relative_to(repo_root)}")
    return output_path


def generate_snapshot(repo_root: Path, audit_result: dict, target_lane: str) -> Path:
    """Phase 4: Pre-nuke clarity snapshot — full working context to mailbox."""
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y-%m-%d %H:%M UTC")
    ts_file = now.strftime("%Y_%m_%dT%H_%M_%SZ")

    # Git metadata
    branch = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True, text=True, cwd=repo_root,
        encoding="utf-8", errors="replace",
    ).stdout.strip()

    head = subprocess.run(
        ["git", "log", "--oneline", "-1"],
        capture_output=True, text=True, cwd=repo_root,
        encoding="utf-8", errors="replace",
    ).stdout.strip()

    recent = subprocess.run(
        ["git", "log", "--oneline", "-15"],
        capture_output=True, text=True, cwd=repo_root,
        encoding="utf-8", errors="replace",
    ).stdout.strip()

    # Commits ahead of origin
    ahead = subprocess.run(
        ["git", "rev-list", "--count", f"origin/{branch}..HEAD"],
        capture_output=True, text=True, cwd=repo_root,
        encoding="utf-8", errors="replace",
    )
    ahead_count = ahead.stdout.strip() if ahead.returncode == 0 else "?"

    # 24h velocity
    velocity = subprocess.run(
        ["git", "log", "--oneline", "--since=24 hours ago"],
        capture_output=True, text=True, cwd=repo_root,
        encoding="utf-8", errors="replace",
    ).stdout.strip()
    velocity_count = len(velocity.splitlines()) if velocity else 0

    # Diff stats for uncommitted work
    diff_stat = subprocess.run(
        ["git", "diff", "--stat"],
        capture_output=True, text=True, cwd=repo_root,
        encoding="utf-8", errors="replace",
    ).stdout.strip()

    # Mailbox inventory
    mailbox_files = {}
    for lane in ["claude/mailbox", "codex/mailbox", "gemini/mailbox"]:
        lane_path = repo_root / lane
        if lane_path.is_dir():
            files = [f.name for f in lane_path.iterdir()
                     if f.is_file() and not f.name.startswith(".")]
            if files:
                mailbox_files[lane] = sorted(files)

    # Build snapshot markdown
    lines = [
        "---",
        "type: scm-triage-snapshot",
        "from: scm-triage-skill",
        f"to: {target_lane}",
        f"created: {now.isoformat()}",
        "priority: high",
        "scope: session-resumption",
        "---",
        "",
        f"# SCM Triage Snapshot — {ts}",
        "",
        f"**Branch:** {branch}",
        f"**HEAD:** {head}",
        f"**Ahead of origin:** {ahead_count} commits",
        f"**24h velocity:** {velocity_count} commits",
        "",
        "## Recent Commits (last 15)",
        "```",
        recent,
        "```",
        "",
        "## Change Classification",
        f"- **Total:** {audit_result['total_changes']}",
        f"- **SIGNAL:** {audit_result['by_classification']['SIGNAL']} (intentional)",
        f"- **NOISE:** {audit_result['by_classification']['NOISE']} (transient)",
        f"- **GHOST:** {audit_result['by_classification']['GHOST']} (deleted but tracked)",
        f"- **MAILBOX:** {audit_result['by_classification']['MAILBOX']} (agent deliverables)",
        "",
    ]

    if audit_result["signal"]:
        lines.append("### Signal Files")
        for p in audit_result["signal"]:
            lines.append(f"- `{p}`")
        lines.append("")

    if audit_result["mailbox"]:
        lines.append("### Mailbox Deliverables (pending)")
        for p in audit_result["mailbox"]:
            lines.append(f"- `{p}`")
        lines.append("")

    if audit_result["noise"]:
        lines.append(f"### Noise ({len(audit_result['noise'])} items)")
        for p in audit_result["noise"][:20]:
            lines.append(f"- `{p}`")
        if len(audit_result["noise"]) > 20:
            lines.append(f"- ... and {len(audit_result['noise']) - 20} more")
        lines.append("")

    if audit_result["ghost"]:
        lines.append(f"### Ghosts ({len(audit_result['ghost'])} items — need `git rm --cached`)")
        for p in audit_result["ghost"][:20]:
            lines.append(f"- `{p}`")
        if len(audit_result["ghost"]) > 20:
            lines.append(f"- ... and {len(audit_result['ghost']) - 20} more")
        lines.append("")

    if diff_stat:
        lines.extend([
            "## Uncommitted Diff Stats",
            "```",
            diff_stat,
            "```",
            "",
        ])

    if mailbox_files:
        lines.append("## Mailbox Inventory")
        for lane, files in mailbox_files.items():
            lines.append(f"### {lane}/")
            for f in files:
                lines.append(f"- `{f}`")
        lines.append("")

    lines.extend([
        "## Recovery Actions",
        "```powershell",
        "# Read this snapshot for instant context:",
        f"# cat {target_lane}/mailbox/SCM_TRIAGE_SNAPSHOT_LATEST.md",
        "",
        "# Run triage to see current state:",
        "uv run scripts/scm_triage.py",
        "",
        "# Fix noise + ghosts:",
        "uv run scripts/scm_triage.py --fix",
        "",
        "# Full audit + fix + plan:",
        "uv run scripts/scm_triage.py --full",
        "```",
        "",
    ])

    content = "\n".join(lines)

    # Write timestamped + LATEST
    mailbox = repo_root / target_lane / "mailbox"
    mailbox.mkdir(parents=True, exist_ok=True)

    latest_path = mailbox / "SCM_TRIAGE_SNAPSHOT_LATEST.md"
    with open(latest_path, "w", encoding="utf-8") as f:
        f.write(content)

    ts_path = mailbox / f"SCM_TRIAGE_SNAPSHOT_{ts_file}.md"
    with open(ts_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"  Snapshot: {latest_path.relative_to(repo_root)}")
    print(f"  Archive:  {ts_path.relative_to(repo_root)}")
    return latest_path


def _new_gitignore_patterns(repo_root: Path, fix_recs: dict) -> list[str]:
    """Return gitignore patterns from fix_recs that are not already in .gitignore."""
    gitignore_path = repo_root / ".gitignore"
    existing: set[str] = set()
    if gitignore_path.exists():
        existing = {
            ln.strip()
            for ln in gitignore_path.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.strip().startswith("#")
        }
    return [p for p in fix_recs.get("gitignore_additions", []) if p not in existing]


def apply_ghost_cleanup(repo_root: Path, ghost_paths: list[str], dry_run: bool) -> int:
    """Remove ghost entries from git index."""
    if not ghost_paths:
        return 0

    # Group by parent directory for efficiency
    dirs = set()
    for path in ghost_paths:
        p = Path(path)
        if len(p.parts) >= 3:
            dirs.add("/".join(p.parts[:3]))
        else:
            dirs.add(str(p.parent))

    removed = 0
    for d in sorted(dirs):
        if dry_run:
            print(f"  [DRY RUN] Would git rm --cached -r {d}")
        else:
            result = subprocess.run(
                ["git", "rm", "--cached", "-r", d],
                capture_output=True, text=True, cwd=repo_root,
                encoding="utf-8", errors="replace",
            )
            if result.returncode == 0:
                count = result.stdout.count("rm '")
                removed += count
                print(f"  Removed {count} entries from index: {d}")
            else:
                print(f"  ⚠ Failed to remove {d}: {result.stderr.strip()}")
    return removed


def main():
    configure_utf8_output()

    parser = argparse.ArgumentParser(
        description="SCM Triage — Source Control Noise Reduction & Structurization"
    )
    parser.add_argument("--fix", action="store_true", help="Apply noise fixes (ghost cleanup; show gitignore candidates)")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write new gitignore entries to .gitignore (prompts for confirmation unless --dry-run)",
    )
    parser.add_argument(
        "--preview-gitignore",
        action="store_true",
        help="Print new .gitignore entries that would be added without writing anything",
    )
    parser.add_argument("--plan", action="store_true", help="Generate migration plan")
    parser.add_argument("--snapshot", action="store_true",
                        help="Write pre-nuke clarity snapshot to mailbox")
    parser.add_argument(
        "--target",
        choices=["claude", "codex", "gemini"],
        default="claude",
        help="Target mailbox lane for snapshot output (default: claude)",
    )
    parser.add_argument("--full", action="store_true", help="Audit + fix + plan + snapshot")
    parser.add_argument("--dry-run", action="store_true", help="Preview without applying")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress info output")
    args = parser.parse_args()

    logger = setup_logging(verbose=args.verbose, quiet=args.quiet)
    repo_root = find_repo_root()

    if args.full:
        args.fix = True
        args.plan = True
        args.snapshot = True

    # Phase 1: Always audit
    audit_result = audit(repo_root, logger)

    if audit_result["total_changes"] == 0:
        print("  Source control is clean. Nothing to triage.")
        return

    # Phase 2: Fix (if requested)
    if args.fix or args.apply or args.preview_gitignore:
        fix_recs = generate_fix_recommendations(audit_result)

        # --preview-gitignore: show candidates, no write
        if args.preview_gitignore:
            new_patterns = _new_gitignore_patterns(repo_root, fix_recs)
            if new_patterns:
                print(f"  .gitignore — {len(new_patterns)} new pattern(s) would be added:")
                for p in new_patterns:
                    print(f"    + {p}")
            else:
                print("  .gitignore — no new patterns needed.")

        if args.fix:
            if fix_recs["ghost_removals"]:
                removed = apply_ghost_cleanup(
                    repo_root, fix_recs["ghost_removals"], args.dry_run
                )
                print(f"  Ghost cleanup: {removed} entries removed from index")

            if fix_recs["gitignore_additions"]:
                print(f"\n  Recommended .gitignore additions:")
                for pattern in fix_recs["gitignore_additions"]:
                    print(f"    + {pattern}")

        if args.apply:
            new_patterns = _new_gitignore_patterns(repo_root, fix_recs)
            if not new_patterns:
                print("  .gitignore — already up-to-date, nothing to apply.")
            elif args.dry_run:
                print(f"  [dry-run] Would append {len(new_patterns)} pattern(s) to .gitignore:")
                for p in new_patterns:
                    print(f"    + {p}")
            else:
                print(f"  About to append {len(new_patterns)} pattern(s) to .gitignore:")
                for p in new_patterns:
                    print(f"    + {p}")
                try:
                    confirm = input("  Apply? [y/N] ").strip().lower()
                except EOFError:
                    confirm = ""
                if confirm == "y":
                    suppress_noise(repo_root, fix_recs, dry_run=False)
                    print("  .gitignore updated.")
                else:
                    print("  Skipped — nothing written.")
    else:
        fix_recs = generate_fix_recommendations(audit_result)

    # Phase 3: Plan (if requested)
    if args.plan:
        write_plan(repo_root, audit_result, fix_recs)

    # Phase 4: Snapshot (if requested)
    if args.snapshot:
        generate_snapshot(repo_root, audit_result, args.target)

    # Final state
    if args.fix and not args.dry_run:
        entries = git_status_porcelain(repo_root)
        print(f"\n  Post-triage: {len(entries)} changes remaining")


if __name__ == "__main__":
    main()
