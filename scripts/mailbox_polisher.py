#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mailbox Polisher.

Purpose:
- Reduce mailbox root noise without deleting history.
- Keep a minimal, high-signal root set.
- Move superseded artifacts to `archive/<YYYY_MM_DD>/`.

This is intentionally conservative: it only archives files matching known
churny patterns (matrix/per-run summaries and stamps) and leaves everything
else in place.

Invocation:
- Detect: uv run scripts/mailbox_polisher.py --target codex
- Apply:  uv run scripts/mailbox_polisher.py --target codex --apply
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


def utc_date_tag() -> str:
    return datetime.now(timezone.utc).strftime("%Y_%m_%d")


@dataclass(frozen=True)
class MovePlan:
    src: Path
    dst: Path
    reason: str


def mailbox_root(target: str) -> Path:
    if target == "codex":
        return Path("codex/mailbox")
    if target == "claude":
        return Path("claude/mailbox")
    raise ValueError(f"Unknown target: {target}")


def is_kept(name: str, keep: set[str]) -> bool:
    return name in keep


def iter_root_files(root: Path) -> Iterable[Path]:
    for p in sorted(root.iterdir()):
        if p.is_file() and p.name not in {".gitkeep"}:
            yield p


def build_keep_set(target: str) -> set[str]:
    # Root files we want to stay readable, stable, and current.
    keep = {
        "MAILBOX_CURRENT_STATE.md",
        "mailbox_manifest.json",
        "SESSION_CONTEXT_CHRONICLE_2026_02_06.md",
        "SESSION_CONTEXT_APPENDIX_2026_02_06.md",
        "SKILLS_PARITY_DISCREPANCY_2026_02_06.md",
        "KISS_PARITY_BRIEF_2026_02_06.md",
        "QUEUE_2026_02_07.md",
        "tatragrammatron_trend.json",
    }
    if target == "codex":
        keep |= {
            "TETRAGRAMMATON_PACKET.md",
            "CLAUDE_RUNBOOK_MATRIX.md",
            "HF_GEMMA_PROBE.md",
            "hf_gemma_probe.json",
            "tatragrammatron_matrix_2026_02_07.json",
            "TATRAGRAMMATRON_SUMMARY_LATEST_CODEX.md",
            "tatragrammatron_stamps_latest_codex.json",
            # Keep latest "doctor" and latest progress note if present.
            "TOOLCHAIN_DOCTOR_LATEST.md",
            "TETRAGRAMMATON_PROGRESS_2026_02_06.md",
        }
    if target == "claude":
        keep |= {
            # Claude mailbox is intentionally smaller and may not have the packet.
            "CLAUDE_META_VALIDATION_SUMMARY.json",
            "skills_parity_map_2026_02_06.json",
        }
    return keep


def should_archive(name: str, target: str) -> tuple[bool, str]:
    # Only archive patterns known to explode into many near-duplicates.
    if target == "codex":
        if name.startswith("TATRAGRAMMATRON_SUMMARY_") and name != "TATRAGRAMMATRON_SUMMARY_LATEST_CODEX.md":
            return True, "superseded summary (keep only LATEST at root)"
        if name.startswith("tatragrammatron_stamps_") and name != "tatragrammatron_stamps_latest_codex.json":
            return True, "superseded stamps (keep only LATEST at root)"
        if name.startswith("e2e_matrix_"):
            return True, "e2e matrix raw artifacts (packet/manifest keep reference; archive for traceability)"
        if name.endswith("_2026_02_06.md") and name.startswith("MAILBOX_CURRENT_STATE_"):
            return True, "dated mailbox state (keep stable MAILBOX_CURRENT_STATE.md)"
        if name.endswith("_2026_02_06.md") and name.startswith("TETRAGRAMMATON_PROGRESS_"):
            # keep this one in keep_set; anything else like it is safe to archive.
            return True, "dated progress note (optional at root)"
    if target == "claude":
        if name.startswith("e2e_matrix_") and name.endswith(".json"):
            return True, "e2e matrix raw artifacts (keep parity reports at root; archive run artifacts)"
        if name.startswith("MAILBOX_CURRENT_STATE_") and name.endswith(".md") and name != "MAILBOX_CURRENT_STATE.md":
            return True, "dated mailbox state (keep stable MAILBOX_CURRENT_STATE.md)"
    return False, ""


def plan_moves(root: Path, target: str) -> list[MovePlan]:
    keep = build_keep_set(target)
    archive_dir = root / "archive" / utc_date_tag()
    plans: list[MovePlan] = []
    for p in iter_root_files(root):
        if is_kept(p.name, keep):
            continue
        archive, reason = should_archive(p.name, target)
        if not archive:
            continue
        plans.append(MovePlan(src=p, dst=archive_dir / p.name, reason=reason))
    return plans


def apply_moves(plans: list[MovePlan]) -> None:
    for m in plans:
        m.dst.parent.mkdir(parents=True, exist_ok=True)
        if m.dst.exists():
            # Never overwrite archived artifacts; keep both by suffixing.
            stem = m.dst.stem
            suf = m.dst.suffix
            i = 2
            while True:
                cand = m.dst.with_name(f"{stem}__dup{i}{suf}")
                if not cand.exists():
                    m = MovePlan(src=m.src, dst=cand, reason=m.reason)
                    break
                i += 1
        m.src.replace(m.dst)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", choices=["codex", "claude"], required=True)
    ap.add_argument("--apply", action="store_true", help="Move files into archive folders.")
    args = ap.parse_args()

    root = mailbox_root(args.target)
    root.mkdir(parents=True, exist_ok=True)
    plans = plan_moves(root, args.target)

    if not plans:
        print("No archivable churn artifacts found.")
        return 0

    print(f"Planned moves: {len(plans)}")
    for m in plans:
        print(f"- {m.src.name} -> {m.dst.as_posix()} ({m.reason})")

    if args.apply:
        apply_moves(plans)
        print("Applied archive moves.")
    else:
        print("Detect-only; re-run with --apply to move.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
