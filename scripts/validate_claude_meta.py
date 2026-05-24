#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: validate_claude_meta.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Claude-only meta-skill validator.
Checks Claude skill-polisher and Claude hook presence; writes JSON to claude/mailbox.

@SID:           TOOL_VALIDATE_CLAUDE_META_V1
@Shabti:        CLI Script
@Purpose:       Claude-only meta-skill validator.
"""

from __future__ import annotations


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Check:
    name: str
    ok: bool
    detail: str


def exists(path: Path) -> bool:
    return path.exists()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    checks: list[Check] = []

    claude_polisher = Path(".claude/skills/skill-polisher/SKILL.md")
    run_claude = Path("scripts/run_claude_skill_polisher.ps1")
    run_cross = Path("scripts/run_claude_cross_polish.ps1")

    checks.append(Check("claude_skill_polisher", exists(claude_polisher), str(claude_polisher)))
    checks.append(Check("run_claude_hook", exists(run_claude), str(run_claude)))
    checks.append(Check("run_cross_hook", exists(run_cross), str(run_cross)))

    if claude_polisher.exists():
        text = read_text(claude_polisher)
        checks.append(Check("claude_frontmatter", "name:" in text and "description:" in text, "frontmatter name/description"))
        checks.append(Check("claude_cross_flavor_section", "Cross-Flavor Audit" in text, "Cross-Flavor Audit section"))

    overall_ok = all(c.ok for c in checks)

    print("CLAUDE META VALIDATION")
    for c in checks:
        status = "OK" if c.ok else "FAIL"
        print(f"- {status}: {c.name} ({c.detail})")

    out_dir = Path("claude/mailbox")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "CLAUDE_META_VALIDATION_SUMMARY.json"
    out_path.write_text(json.dumps({"ok": overall_ok, "checks": [c.__dict__ for c in checks]}, indent=2), encoding="utf-8")
    print(f"\nWrote JSON: {out_path}")
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
