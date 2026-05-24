#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: check_mailbox_manifest.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Mailbox manifest contract checks.

KISS: fail fast on regressions that break consumers.
Checks (schema v2+):
- manifest_file present and equals mailbox_manifest.json
- active.json list does NOT include mailbox_manifest.json (avoid self-loop)

Invocation:
- uv run scripts/check_mailbox_manifest.py

@SID:           TOOL_CHECK_MAILBOX_MANIFEST_V1
@Shabti:        CLI Script
@Purpose:       Mailbox manifest contract checks.
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


from __future__ import annotations

import json
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check_one(path: Path) -> list[str]:
    issues: list[str] = []
    obj = load(path)
    ver = int(obj.get("schema_version", 1))
    if ver >= 2:
        mf = obj.get("manifest_file")
        if mf != "mailbox_manifest.json":
            issues.append(f"{path.as_posix()}: schema v{ver} requires manifest_file=mailbox_manifest.json")
        active = obj.get("active") or {}
        active_json = active.get("json") or []
        if "mailbox_manifest.json" in active_json:
            issues.append(f"{path.as_posix()}: manifest must not self-include in active.json list")
    return issues


def main() -> int:
    paths = [
        Path("codex/mailbox/mailbox_manifest.json"),
        Path("claude/mailbox/mailbox_manifest.json"),
    ]
    all_issues: list[str] = []
    for p in paths:
        if not p.exists():
            continue
        all_issues.extend(check_one(p))
    if all_issues:
        for i in all_issues:
            print(i)
        return 2
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
