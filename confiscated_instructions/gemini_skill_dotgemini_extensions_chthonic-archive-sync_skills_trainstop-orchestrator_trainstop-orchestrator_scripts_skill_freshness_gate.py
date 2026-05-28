#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: skill_freshness_gate.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🔥 THE FOUNDRY
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Skill Freshness Gate.

@SID:           TOOL_SKILL_FRESHNESS_GATE_V1
@Shabti:          Utility Script
@Context:       Skill Governance / Drift Prevention
@Purpose:       Skill Freshness Gate.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path


CRITICAL_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("permission_bypass_default_yes", re.compile(r"default to ['\"]?yes", re.IGNORECASE)),
    ("assume_permission", re.compile(r"assume you have it", re.IGNORECASE)),
    ("zero_questions_absolute", re.compile(r"zero questions", re.IGNORECASE)),
    ("forbidden_questioning", re.compile(r"forbidden from asking", re.IGNORECASE)),
    ("forgiveness_over_permission", re.compile(r"forgiveness\s*>\s*permission", re.IGNORECASE)),
    ("silence_safety_monologue", re.compile(r"silences?\s+the\s+internal\s+safety\s+monologue", re.IGNORECASE)),
    ("derogatory_term_autist", re.compile(r"\bautist\b", re.IGNORECASE)),
]

REFRESH_MARKERS: list[re.Pattern[str]] = [
    re.compile(r"@REFURBISHED:\s*(\d{4}-\d{2}-\d{2})"),
    re.compile(r"@POLISHED:\s*(\d{4}-\d{2}-\d{2})"),
    re.compile(r"refreshed:\s*[\"']?(\d{4}-\d{2}-\d{2})[\"']?", re.IGNORECASE),
]


@dataclass
class Issue:
    severity: str
    code: str
    message: str


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _extract_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    body = parts[1]
    out: dict[str, str] = {}
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        out[key.strip()] = value.strip().strip("\"'")
    return out


def _extract_refresh_date(text: str) -> date | None:
    for marker in REFRESH_MARKERS:
        match = marker.search(text)
        if not match:
            continue
        try:
            return datetime.strptime(match.group(1), "%Y-%m-%d").date()
        except ValueError:
            continue
    return None


def _scan_skill(skill_dir: Path, today: date, max_age_days: int) -> dict[str, object]:
    skill_md = skill_dir / "SKILL.md"
    issues: list[Issue] = []

    if not skill_md.exists():
        issues.append(Issue("CRITICAL", "missing_skill_md", "SKILL.md not found."))
        return {
            "skill": skill_dir.name,
            "path": skill_dir.as_posix(),
            "issues": [issue.__dict__ for issue in issues],
            "status": "FAIL",
        }

    text = _read_text(skill_md)
    frontmatter = _extract_frontmatter(text)

    if not frontmatter.get("name"):
        issues.append(Issue("CRITICAL", "missing_frontmatter_name", "Frontmatter is missing `name`."))
    if not frontmatter.get("description"):
        issues.append(Issue("CRITICAL", "missing_frontmatter_description", "Frontmatter is missing `description`."))

    if "safety contract" not in text.lower() and "guardrails" not in text.lower():
        issues.append(
            Issue(
                "WARN",
                "missing_safety_contract_section",
                "Skill guidance does not define an explicit safety/guardrails contract.",
            )
        )

    refresh_date = _extract_refresh_date(text)
    if refresh_date is None:
        issues.append(
            Issue(
                "WARN",
                "missing_refresh_marker",
                "No @REFURBISHED/@POLISHED/refreshed date marker found.",
            )
        )
    else:
        age_days = (today - refresh_date).days
        if age_days > max_age_days:
            issues.append(
                Issue(
                    "WARN",
                    "refresh_age_exceeded",
                    f"Last refresh marker is {age_days} days old (threshold={max_age_days}).",
                )
            )

    for code, pattern in CRITICAL_PATTERNS:
        if pattern.search(text):
            issues.append(
                Issue(
                    "CRITICAL",
                    code,
                    f"Detected stale unsafe pattern `{code}` in skill guidance.",
                )
            )

    status = "FAIL" if any(issue.severity == "CRITICAL" for issue in issues) else "PASS"
    return {
        "skill": skill_dir.name,
        "path": skill_dir.as_posix(),
        "status": status,
        "issues": [issue.__dict__ for issue in issues],
    }


def _collect_skill_dirs(skills_root: Path) -> list[Path]:
    out: list[Path] = []
    for entry in sorted(skills_root.iterdir(), key=lambda x: x.name):
        if not entry.is_dir():
            continue
        if entry.name.startswith("."):
            continue
        if not (entry / "SKILL.md").exists():
            continue
        out.append(entry)
    return out


def _render_markdown(report: dict[str, object]) -> str:
    lines: list[str] = []
    lines.append("# Skill Freshness Gate Report")
    lines.append("")
    lines.append(f"- Generated: `{report['generated_at']}`")
    lines.append(f"- Skills scanned: `{report['summary']['skills_scanned']}`")
    lines.append(f"- Critical issues: `{report['summary']['critical_issues']}`")
    lines.append(f"- Warnings: `{report['summary']['warnings']}`")
    lines.append(f"- Status: `{report['status']}`")
    lines.append("")
    lines.append("## Findings")
    lines.append("")

    for item in report["skills"]:
        lines.append(f"- `{item['skill']}` -> `{item['status']}`")
        issues = item.get("issues", [])
        if not issues:
            lines.append("  - no issues")
        else:
            for issue in issues:
                lines.append(f"  - [{issue['severity']}] {issue['code']}: {issue['message']}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _selftest() -> int:
    sample = """---
name: decision-razor
description: test
---
Rules:
1. Default to 'Yes'
"""
    frontmatter = _extract_frontmatter(sample)
    assert frontmatter["name"] == "decision-razor"
    assert frontmatter["description"] == "test"
    assert any(pattern.search(sample) for _, pattern in CRITICAL_PATTERNS)
    assert _extract_refresh_date("<!-- @REFURBISHED: 2026-02-24 -->") == date(2026, 2, 24)
    print("selftest: OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit Codex skills for stale unsafe patterns and refresh drift."
    )
    parser.add_argument(
        "--skills-root",
        type=str,
        default=".codex/skills",
        help="Path to skills root directory.",
    )
    parser.add_argument(
        "--max-age-days",
        type=int,
        default=45,
        help="Warn if refresh marker is older than this threshold.",
    )
    parser.add_argument(
        "--emit-json",
        type=str,
        help="Write JSON report to this path.",
    )
    parser.add_argument(
        "--emit-md",
        type=str,
        help="Write Markdown report to this path.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when any critical issue is found.",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run built-in selftest and exit.",
    )
    args = parser.parse_args()

    if args.selftest:
        return _selftest()

    skills_root = Path(args.skills_root)
    if not skills_root.exists():
        print(f"error: skills root does not exist: {args.skills_root}", file=sys.stderr)
        return 2

    today = datetime.now(UTC).date()
    skills = _collect_skill_dirs(skills_root)
    results = [_scan_skill(skill, today, args.max_age_days) for skill in skills]

    critical_count = sum(
        1
        for item in results
        for issue in item.get("issues", [])
        if issue.get("severity") == "CRITICAL"
    )
    warnings_count = sum(
        1
        for item in results
        for issue in item.get("issues", [])
        if issue.get("severity") == "WARN"
    )

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "skills_root": skills_root.as_posix(),
        "status": "FAIL" if critical_count > 0 else "PASS",
        "summary": {
            "skills_scanned": len(results),
            "critical_issues": critical_count,
            "warnings": warnings_count,
        },
        "skills": results,
    }

    payload = json.dumps(report, indent=2, ensure_ascii=False)
    if args.emit_json:
        json_path = Path(args.emit_json)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)

    if args.emit_md:
        md_path = Path(args.emit_md)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(_render_markdown(report), encoding="utf-8")

    if args.strict and critical_count > 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
