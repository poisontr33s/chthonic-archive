#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: mailbox_polisher.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

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

@SID:           TOOL_MAILBOX_POLISHER_V1
@Shabti:        CLI Script
@Purpose:       Mailbox Polisher.
"""

from __future__ import annotations


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

_REPO_ROOT = Path(__file__).resolve().parent.parent
_PATTERNS_PATH = _REPO_ROOT / ".meta" / "mailbox-polisher-patterns.json"


def utc_date_tag() -> str:
    return datetime.now(timezone.utc).strftime("%Y_%m_%d")


_DEFAULT_PATTERNS: dict = {
    "keep_base": [
        "MAILBOX_CURRENT_STATE.md",
        "mailbox_manifest.json",
        "SESSION_CONTEXT_CHRONICLE_2026_02_06.md",
        "SESSION_CONTEXT_APPENDIX_2026_02_06.md",
        "SKILLS_PARITY_DISCREPANCY_2026_02_06.md",
        "KISS_PARITY_BRIEF_2026_02_06.md",
        "QUEUE_2026_02_07.md",
        "tatragrammatron_trend.json",
    ],
    "keep_codex": [
        "TETRAGRAMMATON_PACKET.md",
        "CLAUDE_RUNBOOK_MATRIX.md",
        "HF_GEMMA_PROBE.md",
        "hf_gemma_probe.json",
        "tatragrammatron_matrix_2026_02_07.json",
        "TATRAGRAMMATRON_SUMMARY_LATEST_CODEX.md",
        "tatragrammatron_stamps_latest_codex.json",
        "TOOLCHAIN_DOCTOR_LATEST.md",
        "TETRAGRAMMATON_PROGRESS_2026_02_06.md",
    ],
    "keep_claude": [
        "CLAUDE_META_VALIDATION_SUMMARY.json",
        "skills_parity_map_2026_02_06.json",
    ],
    "keep_gemini": [
        "MAILBOX_CURRENT_STATE.md",
        "mailbox_manifest.json",
        "TETRAGRAMMATON_PACKET.md",
    ],
    "archive_codex": [
        {"prefix": "TATRAGRAMMATRON_SUMMARY_", "exclude_exact": "TATRAGRAMMATRON_SUMMARY_LATEST_CODEX.md", "reason": "superseded summary (keep only LATEST at root)"},
        {"prefix": "tatragrammatron_stamps_", "exclude_exact": "tatragrammatron_stamps_latest_codex.json", "reason": "superseded stamps (keep only LATEST at root)"},
        {"prefix": "e2e_matrix_", "reason": "e2e matrix raw artifacts (packet/manifest keep reference; archive for traceability)"},
        {"startswith": "MAILBOX_CURRENT_STATE_", "endswith": "_2026_02_06.md", "reason": "dated mailbox state (keep stable MAILBOX_CURRENT_STATE.md)"},
        {"startswith": "TETRAGRAMMATON_PROGRESS_", "endswith": "_2026_02_06.md", "reason": "dated progress note (optional at root)"},
    ],
    "archive_claude": [
        {"prefix": "e2e_matrix_", "suffix": ".json", "reason": "e2e matrix raw artifacts (keep parity reports at root; archive run artifacts)"},
        {"prefix": "MAILBOX_CURRENT_STATE_", "suffix": ".md", "exclude_exact": "MAILBOX_CURRENT_STATE.md", "reason": "dated mailbox state (keep stable MAILBOX_CURRENT_STATE.md)"},
    ],
}


def load_patterns() -> dict:
    """Load patterns from .meta/mailbox-polisher-patterns.json, creating defaults if absent."""
    if _PATTERNS_PATH.exists():
        with open(_PATTERNS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    # Write defaults on first use.
    _PATTERNS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_PATTERNS_PATH, "w", encoding="utf-8") as f:
        json.dump(_DEFAULT_PATTERNS, f, indent=2)
    return _DEFAULT_PATTERNS



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
    if target == "gemini":
        return Path("gemini/mailbox")
    raise ValueError(f"Unknown target: {target}")


def is_kept(name: str, keep: set[str]) -> bool:
    return name in keep


def iter_root_files(root: Path) -> Iterable[Path]:
    for p in sorted(root.iterdir()):
        if p.is_file() and p.name not in {".gitkeep"}:
            yield p


def build_keep_set(target: str, patterns: dict | None = None) -> set[str]:
    if patterns is None:
        patterns = load_patterns()
    keep = set(patterns.get("keep_base", []))
    keep |= set(patterns.get(f"keep_{target}", []))
    return keep


def _matches_archive_rule(name: str, rule: dict) -> bool:
    if "prefix" in rule and not name.startswith(rule["prefix"]):
        return False
    if "startswith" in rule and not name.startswith(rule["startswith"]):
        return False
    if "endswith" in rule and not name.endswith(rule["endswith"]):
        return False
    if "suffix" in rule and not name.endswith(rule["suffix"]):
        return False
    if "exclude_exact" in rule and name == rule["exclude_exact"]:
        return False
    return True


def should_archive(name: str, target: str, patterns: dict | None = None) -> tuple[bool, str]:
    if patterns is None:
        patterns = load_patterns()
    for rule in patterns.get(f"archive_{target}", []):
        if _matches_archive_rule(name, rule):
            return True, rule.get("reason", "archived")
    return False, ""


def plan_moves(root: Path, target: str) -> list[MovePlan]:
    patterns = load_patterns()
    keep = build_keep_set(target, patterns)
    archive_dir = root / "archive" / utc_date_tag()
    plans: list[MovePlan] = []
    for p in iter_root_files(root):
        if is_kept(p.name, keep):
            continue
        archive, reason = should_archive(p.name, target, patterns)
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
    ap.add_argument("--target", choices=["codex", "claude", "gemini"], required=True)
    ap.add_argument("--apply", action="store_true", help="Move files into archive folders.")
    ap.add_argument("--dry-run", action="store_true", help="Print table of files-to-archive + target path (implied when --apply is absent).")
    args = ap.parse_args()

    root = mailbox_root(args.target)
    root.mkdir(parents=True, exist_ok=True)
    plans = plan_moves(root, args.target)

    if not plans:
        print("No archivable churn artifacts found.")
        return 0

    if not args.apply or args.dry_run:
        # Table output for dry-run / preview
        col_src = max(len(m.src.name) for m in plans)
        col_dst = max(len(str(m.dst.as_posix())) for m in plans)
        header = f"  {'SOURCE':<{col_src}}  {'TARGET':<{col_dst}}  REASON"
        print(header)
        print("  " + "-" * (len(header) - 2))
        for m in plans:
            print(f"  {m.src.name:<{col_src}}  {m.dst.as_posix():<{col_dst}}  {m.reason}")
        print(f"\nPlanned moves: {len(plans)}")

    if args.apply:
        apply_moves(plans)
        print(f"Applied {len(plans)} archive move(s).")
    elif not args.dry_run:
        print("\nDetect-only; re-run with --apply to move.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
