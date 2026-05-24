#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: oversight_upcycle.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Oversight upcycle controller.

Goal:
- Convert daemon telemetry into one hierarchical execution stack.
- Focus on codebase action, not document churn.
- Emit a single LATEST artifact pair (json + markdown), overwritten each run.

@SID:           TOOL_OVERSIGHT_UPCYCLE_V1
@Shabti:        CLI Script
@Purpose:       Oversight upcycle controller.
"""

from __future__ import annotations


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


MAILBOX_DIRS = {
    "codex": Path("codex/mailbox"),
    "claude": Path("claude/mailbox"),
}

NOISE_PREFIXES = (
    "docs/",
    "claude-codex-gemini/",
    "debugging_data/",
    "dev/",
    "codex/mailbox/",
    "claude/mailbox/",
)

ACTIONABLE_PREFIXES = (
    "scripts/",
    "src/",
    "extensions/",
    "error-classifier/",
    "mas_mcp/",
    "game/",
)


@dataclass
class Task:
    tier: str
    title: str
    target: str
    rationale: str
    action: str
    score: int


def find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for p in [cur, *cur.parents]:
        if (p / "AGENTS.md").exists() and (p / ".gitignore").exists():
            return p
    raise SystemExit("Could not locate repo root (expected AGENTS.md + .gitignore).")


REPO_ROOT = find_repo_root(Path(__file__))


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def latest_daemon_report() -> Path:
    base = REPO_ROOT / "dumpster-dive" / "intake" / "overnight-daemon"
    if not base.exists():
        raise SystemExit("Missing overnight-daemon intake directory.")

    runs = sorted([p for p in base.glob("20*") if p.is_dir()], key=lambda x: x.name, reverse=True)
    for run in runs:
        report = run / "report.json"
        if report.exists():
            return report
    raise SystemExit("No report.json found in overnight-daemon runs.")


def is_noise(path: str) -> bool:
    lowered = path.replace("\\", "/").lower()
    return lowered.startswith(NOISE_PREFIXES)


def is_actionable(path: str) -> bool:
    lowered = path.replace("\\", "/").lower()
    return lowered.startswith(ACTIONABLE_PREFIXES)


def score_monolith(score: int, todo_hits: int) -> int:
    return int(score + (todo_hits * 30))


def build_tasks(report: dict) -> tuple[list[Task], dict]:
    top = report.get("topCandidates", []) or []
    todos = report.get("todoHits", []) or []

    actionable_todos = [t for t in todos if is_actionable(str(t.get("file", "")))]
    noise_todos = [t for t in todos if is_noise(str(t.get("file", "")))]

    monoliths = []
    for candidate in top:
        rel_path = str(candidate.get("relPath", ""))
        score = int(candidate.get("score", 0))
        todo_hits = int(candidate.get("todoHits", 0))
        if score >= 800 and is_actionable(rel_path):
            monoliths.append(
                {
                    "path": rel_path,
                    "score": score,
                    "todo_hits": todo_hits,
                    "derived": score_monolith(score, todo_hits),
                }
            )
    monoliths.sort(key=lambda x: x["derived"], reverse=True)

    tasks: list[Task] = []

    if len(noise_todos) >= len(actionable_todos):
        tasks.append(
            Task(
                tier="TIER-0",
                title="Stabilize TODO signal quality",
                target="scripts/overnight_daemon.ts + error-classifier/ingest.ts",
                rationale=(
                    f"Noise TODO hits ({len(noise_todos)}) are >= actionable code TODO hits ({len(actionable_todos)}). "
                    "Current telemetry is polluting prioritization."
                ),
                action=(
                    "Restrict scored TODO extraction to actionable code prefixes and keep docs/research TODOs informational."
                ),
                score=980,
            )
        )

    if monoliths:
        primary = monoliths[0]
        tasks.append(
            Task(
                tier="TIER-0",
                title="Decompose primary monolith",
                target=primary["path"],
                rationale=(
                    f"Highest structural complexity hotspot (score={primary['score']}, derived={primary['derived']}). "
                    "This file dominates systemic change risk."
                ),
                action=(
                    "Extract bounded modules by responsibility and keep CLI surface unchanged; add regression checks."
                ),
                score=950,
            )
        )

    for m in monoliths[1:4]:
        tasks.append(
            Task(
                tier="TIER-1",
                title="Decompose secondary monolith",
                target=m["path"],
                rationale=f"High complexity hotspot (score={m['score']}, derived={m['derived']}).",
                action="Split analyzer/core/output concerns into separate units with deterministic interfaces.",
                score=max(700, 900 - (m["score"] // 10)),
            )
        )

    if actionable_todos:
        top_todo_files: dict[str, int] = {}
        for row in actionable_todos:
            f = str(row.get("file", "")).replace("\\", "/")
            top_todo_files[f] = top_todo_files.get(f, 0) + 1
        ordered = sorted(top_todo_files.items(), key=lambda x: x[1], reverse=True)[:3]
        for file_path, count in ordered:
            tasks.append(
                Task(
                    tier="TIER-2",
                    title="Close actionable TODO cluster",
                    target=file_path,
                    rationale=f"{count} actionable TODO/FIXME/HACK markers in code path.",
                    action="Convert TODOs to either implemented behavior or explicit deferred issue references.",
                    score=500 + (count * 20),
                )
            )

    tasks.sort(key=lambda x: x.score, reverse=True)

    summary = {
        "files_scanned": int(report.get("summary", {}).get("filesScanned", 0)),
        "todo_hits_total": int(report.get("summary", {}).get("todoHits", 0)),
        "todo_hits_actionable": len(actionable_todos),
        "todo_hits_noise": len(noise_todos),
        "monolith_count": len(monoliths),
    }
    return tasks, summary


def render_markdown(source_report: Path, summary: dict, tasks: list[Task]) -> str:
    lines: list[str] = []
    lines.append("# Oversight Upcycle (Latest)")
    lines.append("")
    lines.append(f"- Generated UTC: `{utc_now_iso()}`")
    lines.append(f"- Source report: `{source_report.as_posix()}`")
    lines.append(f"- Files scanned: `{summary['files_scanned']}`")
    lines.append(f"- TODO hits total: `{summary['todo_hits_total']}`")
    lines.append(f"- Actionable TODO hits: `{summary['todo_hits_actionable']}`")
    lines.append(f"- Noise TODO hits: `{summary['todo_hits_noise']}`")
    lines.append(f"- Monolith hotspots: `{summary['monolith_count']}`")
    lines.append("")

    for tier in ("TIER-0", "TIER-1", "TIER-2"):
        tier_tasks = [t for t in tasks if t.tier == tier]
        if not tier_tasks:
            continue
        lines.append(f"## {tier}")
        for idx, task in enumerate(tier_tasks, start=1):
            lines.append(f"{idx}. `{task.title}`")
            lines.append(f"target: `{task.target}`")
            lines.append(f"why: {task.rationale}")
            lines.append(f"do: {task.action}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a single hierarchical oversight task stack.")
    parser.add_argument(
        "--target-mailbox",
        choices=sorted(MAILBOX_DIRS.keys()),
        default="codex",
        help="Mailbox for OVERSIGHT_UPCYCLE_LATEST outputs.",
    )
    parser.add_argument("--json", action="store_true", help="Print compact JSON to stdout.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    report_path = latest_daemon_report()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    tasks, summary = build_tasks(report)

    payload = {
        "generated_at": utc_now_iso(),
        "source_report": report_path.as_posix(),
        "summary": summary,
        "tasks": [asdict(t) for t in tasks],
    }

    out_dir = REPO_ROOT / MAILBOX_DIRS[args.target_mailbox]
    json_path = out_dir / "OVERSIGHT_UPCYCLE_LATEST.json"
    md_path = out_dir / "OVERSIGHT_UPCYCLE_LATEST.md"

    write_text(json_path, json.dumps(payload, indent=2) + "\n")
    write_text(md_path, render_markdown(report_path, summary, tasks))

    print(f"Wrote: {json_path.as_posix()}")
    print(f"Wrote: {md_path.as_posix()}")
    print(
        "Summary: actionable_todos={0} noise_todos={1} monoliths={2} tasks={3}".format(
            summary["todo_hits_actionable"],
            summary["todo_hits_noise"],
            summary["monolith_count"],
            len(tasks),
        )
    )

    if args.json:
        print(json.dumps(payload, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
