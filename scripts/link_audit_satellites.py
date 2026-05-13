#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: link_audit_satellites.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: GOLD
# ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Orchestrates: link_audit_author.py across SATELLITE_REGISTRY.json)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Link Audit Satellites — Fan link_audit_author.py across every satellite in
SATELLITE_REGISTRY.json, aggregate per-repo results into one JSON report,
and exit non-zero if any satellite has broken user-authored links.

@SID:           TOOL_LINK_AUDIT_SATELLITES_V1
@Shabti:        Orchestrator
@Context:       Infrastructure / Polyrepo pathfinder fanout
@Implements:    Polyrepo author-filtered pathfinder (chthonic-archive #C-landing)
@Purpose:       Read SATELLITE_REGISTRY.json -> resolve each satellite local_path
                -> run scripts/link_audit_author.py per repo with the same author
                filter -> aggregate exit codes + summaries.

Usage:
    uv run scripts/link_audit_satellites.py --author-self
    uv run scripts/link_audit_satellites.py --author eldnordd@gmail.com
    uv run scripts/link_audit_satellites.py --author-self --only pnk,rmo
    uv run scripts/link_audit_satellites.py --author-self --clone-missing
    uv run scripts/link_audit_satellites.py --author-self --report manifest/satellite_link_audit.json

Flags:
    --author EMAIL        Email to filter by (repeatable)
    --author-self         Auto-include git config user.email (per satellite)
    --only ALIAS[,ALIAS]  Restrict to specific satellites by alias (repeatable or comma-list)
    --clone-missing       git clone any satellite whose local_path is absent
    --report PATH         Write aggregate JSON summary (default: manifest/satellite_link_audit.json)
    --dry-run             Per-satellite dry-run (no actual link_audit invocation)
    --registry PATH       Override SATELLITE_REGISTRY.json location
    --include-primary     Also audit the chthonic-archive repo itself

Exit codes:
    0  all satellites green (or skipped)
    1  one or more satellites have broken user-authored links
    2  configuration/registry/clone issues
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY = REPO_ROOT / "SATELLITE_REGISTRY.json"
DEFAULT_REPORT = REPO_ROOT / "manifest" / "satellite_link_audit.json"
AUTHOR_SCRIPT = REPO_ROOT / "scripts" / "link_audit_author.py"


def load_registry(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Satellite registry missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def parse_only(values: list[str]) -> set[str]:
    selected: set[str] = set()
    for v in values:
        for piece in v.split(","):
            piece = piece.strip()
            if piece:
                selected.add(piece)
    return selected


def clone_satellite(github: str, local_path: Path, depth: int) -> tuple[bool, str]:
    cmd = ["git", "clone", "--depth", str(depth or 1), f"https://github.com/{github}.git",
           str(local_path)]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        return False, result.stderr.strip()
    return True, "cloned"


def run_satellite_audit(
    local_path: Path,
    author_args: list[str],
    *,
    dry_run: bool,
    report_path: Path | None,
) -> dict:
    cmd = [
        "uv", "run", str(AUTHOR_SCRIPT),
        "--repo", str(local_path),
        *author_args,
    ]
    if dry_run:
        cmd.append("--dry-run")
    if report_path:
        cmd.extend(["--report", str(report_path)])

    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    summary: dict = {
        "exitCode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }
    if report_path and report_path.exists():
        try:
            summary["details"] = json.loads(report_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(prog="link_audit_satellites")
    parser.add_argument("--author", action="append", default=[])
    parser.add_argument("--author-self", action="store_true")
    parser.add_argument("--only", action="append", default=[])
    parser.add_argument("--clone-missing", action="store_true")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--include-primary", action="store_true",
                        help="Also audit the chthonic-archive repo itself")
    args = parser.parse_args()

    if not args.author and not args.author_self:
        print("[link_audit_satellites] ERROR: specify --author or --author-self",
              file=sys.stderr)
        return 2

    try:
        registry = load_registry(args.registry)
    except FileNotFoundError as exc:
        print(f"[link_audit_satellites] ERROR: {exc}", file=sys.stderr)
        return 2

    selected = parse_only(args.only)
    satellites = registry.get("satellites", [])

    author_args: list[str] = []
    for a in args.author:
        author_args.extend(["--author", a])
    if args.author_self:
        author_args.append("--author-self")

    targets: list[tuple[str, Path]] = []
    if args.include_primary:
        targets.append(("chthonic-archive (primary)", REPO_ROOT))
    for sat in satellites:
        alias = sat.get("alias")
        if selected and alias not in selected:
            continue
        local = Path(sat["local_path"])
        targets.append((f"{alias}: {sat.get('name', '')}", local))

    aggregate: dict = {
        "registry": str(args.registry),
        "authorArgs": author_args,
        "results": [],
        "satelliteCount": len(targets),
    }
    overall_ok = True
    args.report.parent.mkdir(parents=True, exist_ok=True)

    for label, local_path in targets:
        entry: dict = {"label": label, "localPath": str(local_path)}
        if not local_path.exists():
            if args.clone_missing:
                # Find matching satellite entry for github url
                github = next(
                    (s["github"] for s in satellites if Path(s["local_path"]) == local_path),
                    None,
                )
                if not github:
                    entry["status"] = "missing-no-github"
                    overall_ok = False
                    aggregate["results"].append(entry)
                    continue
                depth = next(
                    (s.get("clone_depth", 1) for s in satellites if Path(s["local_path"]) == local_path),
                    1,
                )
                ok, msg = clone_satellite(github, local_path, depth)
                entry["clone"] = {"github": github, "ok": ok, "message": msg}
                if not ok:
                    entry["status"] = "clone-failed"
                    overall_ok = False
                    aggregate["results"].append(entry)
                    continue
            else:
                entry["status"] = "missing"
                overall_ok = False
                print(f"[link_audit_satellites] MISSING: {label} -> {local_path}  "
                      "(use --clone-missing to auto-clone)", file=sys.stderr)
                aggregate["results"].append(entry)
                continue

        per_sat_report = args.report.parent / f"satellite_{local_path.name}.json"
        summary = run_satellite_audit(
            local_path,
            author_args,
            dry_run=args.dry_run,
            report_path=per_sat_report,
        )
        entry["audit"] = summary
        entry["status"] = (
            "ok" if summary["exitCode"] in (0, 2)
            else "broken-links" if summary["exitCode"] == 1
            else "error"
        )
        if entry["status"] == "broken-links":
            overall_ok = False
        if entry["status"] == "error":
            overall_ok = False

        print(f"[satellite] {label}  exit={summary['exitCode']}  status={entry['status']}")
        aggregate["results"].append(entry)

    aggregate["allGreen"] = overall_ok
    args.report.write_text(json.dumps(aggregate, indent=2), encoding="utf-8")
    print(f"[link_audit_satellites] report -> {args.report}")
    print(f"[link_audit_satellites] {'OK' if overall_ok else 'FAIL'} "
          f"across {len(targets)} satellite(s)")

    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
