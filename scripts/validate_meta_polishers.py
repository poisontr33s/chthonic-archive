#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: validate_meta_polishers.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Meta-skill validator for the meta-polisher stack.
Validates that meta-skills and shared hooks are present and aligned.

@SID:           TOOL_VALIDATE_META_POLISHERS_V1
@Shabti:        CLI Script
@Purpose:       Meta-skill validator for the meta-polisher stack.
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

    codex_polisher = Path(".codex/skills/skill-polisher/SKILL.md")
    claude_polisher = Path(".claude/skills/skill-polisher/SKILL.md")
    shared_audit = Path("scripts/skill_audit.py")

    run_codex = Path("scripts/run_codex_polisher.ps1")
    run_claude = Path("scripts/run_claude_skill_polisher.ps1")
    run_cross = Path("scripts/run_claude_cross_polish.ps1")

    # Presence checks
    checks.append(Check("codex_skill_polisher", exists(codex_polisher), str(codex_polisher)))
    checks.append(Check("claude_skill_polisher", exists(claude_polisher), str(claude_polisher)))
    checks.append(Check("shared_audit", exists(shared_audit), str(shared_audit)))
    checks.append(Check("run_codex_hook", exists(run_codex), str(run_codex)))
    checks.append(Check("run_claude_hook", exists(run_claude), str(run_claude)))
    checks.append(Check("run_cross_hook", exists(run_cross), str(run_cross)))

    # Content checks
    if codex_polisher.exists():
        text = read_text(codex_polisher)
        ok = "Cross-Flavor Audit" in text
        checks.append(Check("codex_cross_flavor_section", ok, "Cross-Flavor Audit section"))

    if claude_polisher.exists():
        text = read_text(claude_polisher)
        ok = "Cross-Flavor Audit" in text
        checks.append(Check("claude_cross_flavor_section", ok, "Cross-Flavor Audit section"))

    # Shared audit references
    if codex_polisher.exists():
        ok = "scripts/skill_audit.py" in read_text(codex_polisher)
        checks.append(Check("codex_references_shared_audit", ok, "scripts/skill_audit.py referenced"))

    if claude_polisher.exists():
        ok = "scripts/skill_audit.py" in read_text(claude_polisher)
        checks.append(Check("claude_references_shared_audit", ok, "scripts/skill_audit.py referenced"))

    overall_ok = all(c.ok for c in checks)

    print("META-POLISHER VALIDATION")
    for c in checks:
        status = "OK" if c.ok else "FAIL"
        print(f"- {status}: {c.name} ({c.detail})")

    summary = {
        "ok": overall_ok,
        "checks": [c.__dict__ for c in checks],
    }
    Path("codex/mailbox/META_POLISHER_VALIDATION_SUMMARY.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print("\nWrote JSON: codex/mailbox/META_POLISHER_VALIDATION_SUMMARY.json")
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
