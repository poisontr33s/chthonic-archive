#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: skill_audit.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Cross-flavor skill auditor for Codex, Claude, and Gemini.

Usage:
  uv run scripts/skill_audit.py --flavor codex --root .codex/skills
  uv run scripts/skill_audit.py --flavor claude --root .claude/skills
  uv run scripts/skill_audit.py --flavor gemini --root .gemini/extensions/chthonic-archive-sync/skills

@SID:           TOOL_SKILL_AUDIT_V1
@Shabti:        CLI Script
@Purpose:       Cross-flavor skill auditor for Codex, Claude, and Gemini.
"""

from __future__ import annotations


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

# CLAUDE_TOOLS is loaded from .meta/skill-audit-tools.json if present.
# This allows the allowed-tools list to evolve without code changes.
# Fallback: the historical static set used before 2026-04.
_DEFAULT_CLAUDE_TOOLS = {"Read", "Write", "Glob", "Grep", "Bash"}


def _load_claude_tools() -> set[str]:
    config_path = Path(__file__).resolve().parents[1] / ".meta" / "skill-audit-tools.json"
    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return set(data)
            if isinstance(data, dict) and "allowed_tools" in data:
                return set(data["allowed_tools"])
        except (json.JSONDecodeError, ValueError):
            pass
    return set(_DEFAULT_CLAUDE_TOOLS)


CLAUDE_TOOLS = _load_claude_tools()


@dataclass
class AuditResult:
    name: str
    score: int
    issues: list[str]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def list_skills(root: Path, skill_name: str | None = None) -> list[Path]:
    skills = sorted([p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")])
    if skill_name:
        skills = [p for p in skills if p.name == skill_name]
    return skills


def check_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    raw = parts[1]
    body = parts[2]
    fm: dict[str, str] = {}
    current_section: str | None = None
    for line in raw.splitlines():
        if not line.strip():
            continue
        if not line.startswith(" ") and line.endswith(":"):
            current_section = line.strip()[:-1]
            fm[current_section] = ""
            continue
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key = key.strip()
        val = val.strip().strip("\"")
        if current_section == "metadata" and line.startswith(" "):
            fm[f"metadata.{key}"] = val
        else:
            fm[key] = val
    return fm, body


def audit_codex_skill(skill_dir: Path) -> AuditResult:
    issues: list[str] = []
    score = 100

    skill_md = skill_dir / "SKILL.md"
    codex_compat = False
    if not skill_md.exists():
        issues.append("[CRITICAL] Missing SKILL.md")
        score -= 20
    else:
        fm, _ = check_frontmatter(read_text(skill_md))
        codex_compat = fm.get("metadata.codex-compat", "").lower() == "true"

    yaml_path = skill_dir / "agents/openai.yaml"
    if not yaml_path.exists() and not codex_compat:
        issues.append("[CRITICAL] Missing agents/openai.yaml")
        score -= 20

    assets = skill_dir / "assets"
    if not assets.exists() and not codex_compat:
        issues.append("[WARN] Missing assets/ directory")
        score -= 10
    elif assets.exists():
        svgs = list(assets.glob("*.svg"))
        if not svgs and not codex_compat:
            issues.append("[WARN] No SVG icon found in assets/")
            score -= 10

    return AuditResult(skill_dir.name, max(score, 0), issues)


def parse_allowed_tools(val: str) -> list[str]:
    if not val:
        return []
    cleaned = val.strip().strip("[]")
    if not cleaned:
        return []
    return [v.strip().strip("\"") for v in cleaned.split(",") if v.strip()]


def audit_claude_skill(skill_dir: Path) -> AuditResult:
    issues: list[str] = []
    score = 100

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        issues.append("[CRITICAL] Missing SKILL.md")
        score -= 20
        return AuditResult(skill_dir.name, max(score, 0), issues)

    raw = read_text(skill_md)
    fm, _ = check_frontmatter(raw)
    if not fm.get("name"):
        issues.append("[CRITICAL] Missing frontmatter name")
        score -= 20
    if not fm.get("description"):
        issues.append("[CRITICAL] Missing frontmatter description")
        score -= 20

    tools = parse_allowed_tools(fm.get("allowed-tools", ""))
    for tool in tools:
        if tool not in CLAUDE_TOOLS:
            issues.append(f"[WARN] Unknown allowed-tool: {tool}")
            score -= 10

    return AuditResult(skill_dir.name, max(score, 0), issues)


def audit_gemini_skill(skill_dir: Path) -> AuditResult:
    issues: list[str] = []
    score = 100

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        issues.append("[CRITICAL] Missing SKILL.md")
        score -= 20
        return AuditResult(skill_dir.name, max(score, 0), issues)

    raw = read_text(skill_md)
    fm, _ = check_frontmatter(raw)
    if not fm.get("name"):
        issues.append("[CRITICAL] Missing frontmatter name")
        score -= 20
    if not fm.get("description"):
        issues.append("[CRITICAL] Missing frontmatter description")
        score -= 20

    return AuditResult(skill_dir.name, max(score, 0), issues)


def print_report(result: AuditResult, flavor: str = "") -> None:
    """Print audit result aligned with skill_health.py output style."""
    grade = "PASS" if result.score >= 90 else "WARN" if result.score >= 50 else "FAIL"
    status_char = "✅" if grade == "PASS" else "⚠️" if grade == "WARN" else "❌"
    label = f"[{flavor.upper()}]" if flavor else ""
    print(f"  {status_char} {label} {result.name}: {result.score}%")
    for issue in result.issues:
        print(f"    {issue}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Cross-flavor skill auditor")
    parser.add_argument("--flavor", choices=["codex", "claude", "gemini"], required=True)
    parser.add_argument("--root", required=True)
    parser.add_argument("--skill", help="Optional single skill name within the root")
    parser.add_argument("--json", dest="json_out", action="store_true")
    parser.add_argument("--json-path", dest="json_path")
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"ERROR: --root path not found: {root}", file=__import__('sys').stderr)
        raise SystemExit(1)
    if not root.is_dir():
        print(f"ERROR: --root must be a directory, got: {root}", file=__import__('sys').stderr)
        raise SystemExit(1)

    results: list[AuditResult] = []
    print(f"☥ Skill Audit [{args.flavor.upper()}] — {root}\n")
    for skill_dir in list_skills(root, args.skill):
        if args.flavor == "codex":
            result = audit_codex_skill(skill_dir)
        elif args.flavor == "claude":
            result = audit_claude_skill(skill_dir)
        else:
            result = audit_gemini_skill(skill_dir)
        results.append(result)
        print_report(result, args.flavor)

    if args.json_out:
        root_posix = root.as_posix()
        root_native = str(root)
        payload = {
            "schema_version": 1,
            "flavor": args.flavor,
            "root": root_posix,
            "root_native": root_native,
            "results": [r.__dict__ for r in results],
        }
        out_path = Path(args.json_path) if args.json_path else Path("codex/mailbox/skill_audit_summary.json")
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"\nWrote JSON: {out_path}")


if __name__ == "__main__":
    main()
