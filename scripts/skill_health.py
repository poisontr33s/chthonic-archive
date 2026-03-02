#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: skill_health.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Skill Health Auditor — Automated 1-10 discriminatory scoring for all skill lanes.

Scans .claude/skills/ and .codex/skills/, parses SKILL.md frontmatter,
checks referenced script existence, classifies status (active/redirect/stashed),
scores each skill on deterministic criteria, and outputs JSON + markdown reports.

Code patterns recycled from (WPTG provenance):
- polish_skill.py    → frontmatter parsing, code-fence extraction
- scm_triage.py      → classification rules, pattern-based categorization
- handoff_loop.py    → JSON + MD dual output, argparse CLI
- mailbox_manifest.py → directory traversal, file inventory

@SID:           TOOL_SKILL_HEALTH_V1
@Shabti:          Utility
@Context:       Infrastructure / Skill Governance
@Implements:    Automated skill audit (replaces manual 1-10 review)
@Purpose:       Skill Health Auditor — Automated 1-10 discriminatory scoring for all skill lanes.

Usage:
    uv run scripts/skill_health.py                      # full audit, print summary
    uv run scripts/skill_health.py --json               # emit JSON report
    uv run scripts/skill_health.py --md                  # emit markdown report
    uv run scripts/skill_health.py --lane claude         # audit only Claude skills
    uv run scripts/skill_health.py --lane codex          # audit only Codex skills
    uv run scripts/skill_health.py --min-score 5         # filter to skills >= threshold
    uv run scripts/skill_health.py --below 5             # filter to skills < threshold
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

from scripts.lib.shared import configure_utf8_output, find_repo_root, setup_logging

# =============================================================================
# Constants
# =============================================================================

SKILL_LANES: dict[str, str] = {
    "claude": ".claude/skills",
    "codex": ".codex/skills",
}

SKIP_DIRS: set[str] = {".system", "__pycache__", "node_modules"}

# Frontmatter parsing (recycled from handoff_loop.py)
RE_FM_START = re.compile(r"^---\s*$")
RE_FM_KV = re.compile(r"^([A-Za-z0-9_-]+)\s*:\s*(.*?)\s*$")

# Status detection patterns (recycled from scm_triage.py classification logic)
# Precise redirect markers — must appear prominently, not as casual prose
REDIRECT_PATTERNS = [
    re.compile(r"(?i)^#.*?->\s"),               # heading with arrow: "# Postman -> mailbox-handoff"
    re.compile(r"(?i)redirect\s*[-—:]"),          # "REDIRECT -" or "REDIRECT:" in description
    re.compile(r"(?i)has been absorbed into"),    # explicit absorption notice
    re.compile(r"(?i)redirected to\b"),           # "redirected to X"
]
STASH_MARKERS = {"stashed"}

# Command patterns in code fences (recycled from polish_skill.py audit_wptg_transition)
COMMAND_PREFIXES = (
    "uv run ", "bun ", "pwsh ", "python ", "cargo ", "go ",
    "pytest", "npm ", "node ", "ruby ", "rv ", "goup ",
)

# Scoring weights — each dimension is 0-10, final score is weighted average
SCORING_WEIGHTS = {
    "has_cli":       2.5,  # concrete CLI commands in SKILL.md
    "scripts_exist": 2.5,  # referenced scripts physically present
    "deterministic": 2.0,  # produces deterministic artifact (not just LLM text)
    "cross_lane":    1.0,  # exists in both lanes (sync coverage)
    "active_status": 1.0,  # not redirect/stashed
    "description":   1.0,  # has meaningful description (not just a redirect notice)
}


# =============================================================================
# Data Structures
# =============================================================================


@dataclass
class SkillReport:
    name: str
    lane: str
    status: str                     # ACTIVE, REDIRECT, STASHED
    score: float                    # 1.0..10.0
    has_frontmatter: bool
    has_cli_commands: bool
    cli_commands: list[str]         # extracted command strings
    referenced_scripts: list[str]   # paths mentioned in code fences
    scripts_found: list[str]        # subset that exist on disk
    scripts_missing: list[str]      # subset that don't
    deterministic_output: bool      # produces file/artifact
    cross_lane: bool                # same skill exists in other lane
    description: str
    findings: list[str] = field(default_factory=list)


# =============================================================================
# Frontmatter Parsing (recycled from handoff_loop.py + polish_skill.py)
# =============================================================================


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Extract YAML frontmatter from SKILL.md content."""
    lines = text.split("\n")
    if not lines or not RE_FM_START.match(lines[0]):
        return {}, text

    fm: dict[str, str] = {}
    body_start = 1
    for i, line in enumerate(lines[1:], start=1):
        if RE_FM_START.match(line):
            body_start = i + 1
            break
        m = RE_FM_KV.match(line)
        if m:
            fm[m.group(1).lower()] = m.group(2).strip().strip('"').strip("'")
    return fm, "\n".join(lines[body_start:])


# =============================================================================
# Code Fence Extraction (recycled from polish_skill.py _extract_code_fence_lines)
# =============================================================================


def extract_code_fence_lines(text: str) -> list[str]:
    """Extract all non-empty lines inside code fences AND inline backtick commands."""
    lines = text.splitlines()
    in_fence = False
    extracted: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence and stripped:
            extracted.append(stripped)

    # Also extract inline backtick content that looks like commands
    # Pattern: `uv run ...`, `python ...`, `pwsh ...`, etc. (single backtick pairs)
    inline_pat = re.compile(r"`([^`]{8,})`")
    for line in lines:
        if in_fence:
            continue  # already captured
        for m in inline_pat.finditer(line):
            candidate = m.group(1).strip()
            low = candidate.lower()
            if any(low.startswith(p) for p in COMMAND_PREFIXES):
                extracted.append(candidate)
            elif low.startswith(".\\") or low.startswith("./"):
                extracted.append(candidate)

    return extracted


def extract_commands(code_lines: list[str]) -> list[str]:
    """Filter code-fence lines to actual CLI commands."""
    commands = []
    for line in code_lines:
        # Skip comments and variable assignments
        if line.startswith("#") or line.startswith("//"):
            continue
        low = line.lower()
        if any(low.startswith(p) or low.startswith(f".\\{p}") or low.startswith(f"./{p}") for p in COMMAND_PREFIXES):
            commands.append(line)
        # PowerShell commands with backslash paths
        elif low.startswith(".\\scripts\\") or low.startswith("./scripts/"):
            commands.append(line)
    return commands


def extract_script_refs(code_lines: list[str], repo_root: Path) -> tuple[list[str], list[str], list[str]]:
    """
    Extract script path references from code-fence lines.
    Returns (all_refs, found, missing).
    """
    # Pattern: anything that looks like a file path ending in .py, .ps1, .ts, .sh
    path_pat = re.compile(r"""((?:[\w./\\-]+/)?[\w.-]+\.(?:py|ps1|ts|sh|rb))""")
    refs: set[str] = set()
    for line in code_lines:
        for m in path_pat.finditer(line):
            raw = m.group(1).replace("\\", "/")
            # Skip obvious non-paths
            if raw.startswith("http") or raw.startswith("//"):
                continue
            refs.add(raw)

    all_refs = sorted(refs)
    found = []
    missing = []
    for ref in all_refs:
        if (repo_root / ref).exists():
            found.append(ref)
        else:
            missing.append(ref)
    return all_refs, found, missing


# =============================================================================
# Status Classification (recycled from scm_triage.py classification logic)
# =============================================================================


def classify_status(fm: dict[str, str], body: str) -> str:
    """Classify a skill as ACTIVE, REDIRECT, or STASHED."""
    desc = fm.get("description", "").lower()

    # Check description for explicit REDIRECT marker (strongest signal)
    if "redirect" in desc:
        return "REDIRECT"

    # Check first 500 chars of body for specific redirect patterns
    head = body[:500]
    for pat in REDIRECT_PATTERNS:
        if pat.search(head):
            return "REDIRECT"

    # Explicit frontmatter non-invocable → STASHED
    if fm.get("user-invocable", "").lower() == "false":
        return "STASHED"

    # Check for stash markers
    low_head = head.lower()
    for marker in STASH_MARKERS:
        if marker in low_head:
            return "STASHED"

    return "ACTIVE"


# =============================================================================
# Deterministic Output Detection
# =============================================================================


def has_deterministic_output(body: str, commands: list[str]) -> bool:
    """Check if the skill produces a deterministic file artifact."""
    low = body.lower()
    # Look for output file patterns
    output_markers = [
        ".json", ".md", ".yaml", ".yml", ".toml",
        "mailbox/", "codex/mailbox", "claude/mailbox",
        "--emit-json", "--emit-md", "--json", "--out",
        "write", "output", "report",
    ]
    marker_count = sum(1 for m in output_markers if m in low)
    # If commands produce named artifacts, that counts
    cmd_output = any("--emit" in c or "--out" in c or "--json" in c for c in commands)
    return marker_count >= 3 or cmd_output


# =============================================================================
# Scoring Engine
# =============================================================================


def score_skill(report: SkillReport) -> float:
    """
    Score a skill 1.0-10.0 using weighted criteria.
    Redirect/stashed skills are capped.
    """
    if report.status == "REDIRECT":
        return 1.0
    if report.status == "STASHED":
        return 2.0

    raw_scores: dict[str, float] = {}

    # has_cli: 10 if has commands, 0 if not
    raw_scores["has_cli"] = 10.0 if report.has_cli_commands else 0.0

    # scripts_exist: proportion of referenced scripts that exist
    if report.referenced_scripts:
        ratio = len(report.scripts_found) / len(report.referenced_scripts)
        raw_scores["scripts_exist"] = ratio * 10.0
    else:
        # No scripts referenced — penalize but not to zero (some skills are workflow-based)
        raw_scores["scripts_exist"] = 3.0 if report.has_cli_commands else 0.0

    # deterministic: 10 if yes, 2 if no
    raw_scores["deterministic"] = 10.0 if report.deterministic_output else 2.0

    # cross_lane: 10 if both lanes, 5 if one
    raw_scores["cross_lane"] = 10.0 if report.cross_lane else 5.0

    # active_status: always 10 (we already filtered redirect/stashed above)
    raw_scores["active_status"] = 10.0

    # description: 10 if >20 chars, 3 if sparse
    raw_scores["description"] = 10.0 if len(report.description) > 20 else 3.0

    # Weighted average
    total_weight = sum(SCORING_WEIGHTS.values())
    weighted = sum(raw_scores[k] * SCORING_WEIGHTS[k] for k in SCORING_WEIGHTS)
    final = weighted / total_weight

    # Clamp to 1-10 and round to 1 decimal
    return round(max(1.0, min(10.0, final)), 1)


# =============================================================================
# Single Skill Audit
# =============================================================================


def audit_skill(skill_dir: Path, lane: str, repo_root: Path, other_lane_skills: set[str]) -> SkillReport:
    """Audit a single skill directory and return a structured report."""
    name = skill_dir.name
    skill_md = skill_dir / "SKILL.md"

    if not skill_md.exists():
        report = SkillReport(
            name=name, lane=lane, status="ACTIVE", score=1.0,
            has_frontmatter=False, has_cli_commands=False,
            cli_commands=[], referenced_scripts=[], scripts_found=[],
            scripts_missing=[], deterministic_output=False,
            cross_lane=(name in other_lane_skills),
            description="",
            findings=["CRITICAL: No SKILL.md found"],
        )
        report.score = 1.0
        return report

    raw = skill_md.read_text(encoding="utf-8", errors="ignore")
    fm, body = parse_frontmatter(raw)
    status = classify_status(fm, body)

    # Extract code fence content
    code_lines = extract_code_fence_lines(raw)
    commands = extract_commands(code_lines)
    all_refs, found, missing = extract_script_refs(code_lines, repo_root)

    description = fm.get("description", "")
    cross_lane = name in other_lane_skills
    det_output = has_deterministic_output(body, commands)

    # Build findings
    findings: list[str] = []
    if not fm:
        findings.append("WARN: No YAML frontmatter")
    if not commands:
        findings.append("INFO: No CLI commands found in code fences")
    if missing:
        findings.append(f"WARN: Missing scripts: {', '.join(missing)}")
    if not det_output and status == "ACTIVE":
        findings.append("INFO: No clear deterministic output artifact")
    if not cross_lane:
        findings.append(f"INFO: Only in {lane} lane")

    report = SkillReport(
        name=name,
        lane=lane,
        status=status,
        score=0.0,
        has_frontmatter=bool(fm),
        has_cli_commands=bool(commands),
        cli_commands=commands,
        referenced_scripts=all_refs,
        scripts_found=found,
        scripts_missing=missing,
        deterministic_output=det_output,
        cross_lane=cross_lane,
        description=description,
        findings=findings,
    )

    report.score = score_skill(report)
    return report


# =============================================================================
# Full Audit Orchestrator
# =============================================================================


def run_audit(repo_root: Path, lane_filter: str | None = None) -> list[SkillReport]:
    """Audit all skills across requested lanes."""
    # Build cross-lane lookup
    lane_skills: dict[str, set[str]] = {}
    for lane_name, rel_path in SKILL_LANES.items():
        lane_dir = repo_root / rel_path
        if lane_dir.exists():
            lane_skills[lane_name] = {
                d.name for d in lane_dir.iterdir()
                if d.is_dir() and d.name not in SKIP_DIRS
            }
        else:
            lane_skills[lane_name] = set()

    reports: list[SkillReport] = []

    for lane_name, rel_path in SKILL_LANES.items():
        if lane_filter and lane_name != lane_filter:
            continue
        lane_dir = repo_root / rel_path
        if not lane_dir.exists():
            continue

        # Other lane's skill names for cross-lane check
        other_lanes = set()
        for other_name, other_skills in lane_skills.items():
            if other_name != lane_name:
                other_lanes |= other_skills

        for skill_dir in sorted(lane_dir.iterdir()):
            if not skill_dir.is_dir() or skill_dir.name in SKIP_DIRS:
                continue
            report = audit_skill(skill_dir, lane_name, repo_root, other_lanes)
            reports.append(report)

    # Sort by score descending
    reports.sort(key=lambda r: (-r.score, r.name))
    return reports


# =============================================================================
# Output Formatters
# =============================================================================


def format_summary(reports: list[SkillReport]) -> str:
    """Format a concise terminal summary."""
    lines: list[str] = []
    lines.append(f"Skill Health Audit — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(f"{'=' * 72}")
    lines.append("")

    # Distribution
    buckets: dict[str, int] = {"9-10": 0, "7-8": 0, "5-6": 0, "3-4": 0, "1-2": 0}
    for r in reports:
        if r.score >= 9:
            buckets["9-10"] += 1
        elif r.score >= 7:
            buckets["7-8"] += 1
        elif r.score >= 5:
            buckets["5-6"] += 1
        elif r.score >= 3:
            buckets["3-4"] += 1
        else:
            buckets["1-2"] += 1

    lines.append("Score Distribution:")
    for bucket, count in buckets.items():
        bar = "#" * count
        lines.append(f"  {bucket}: {bar} ({count})")
    lines.append("")

    # Table
    lines.append(f"{'Score':>5}  {'Status':<9}  {'Lane':<6}  {'CLI':>3}  {'Scripts':>7}  {'Det':>3}  {'XLane':>5}  {'Name'}")
    lines.append(f"{'-----':>5}  {'------':<9}  {'----':<6}  {'---':>3}  {'-------':>7}  {'---':>3}  {'-----':>5}  {'----'}")
    for r in reports:
        cli_mark = "Y" if r.has_cli_commands else "-"
        scripts_mark = f"{len(r.scripts_found)}/{len(r.referenced_scripts)}" if r.referenced_scripts else "-"
        det_mark = "Y" if r.deterministic_output else "-"
        xl_mark = "Y" if r.cross_lane else "-"
        lines.append(
            f"{r.score:>5.1f}  {r.status:<9}  {r.lane:<6}  {cli_mark:>3}  {scripts_mark:>7}  {det_mark:>3}  {xl_mark:>5}  {r.name}"
        )

    # Findings for skills with issues
    lines.append("")
    lines.append("Findings:")
    for r in reports:
        if r.findings:
            lines.append(f"  {r.lane}/{r.name} ({r.score:.1f}):")
            for f in r.findings:
                lines.append(f"    - {f}")

    active = [r for r in reports if r.status == "ACTIVE"]
    redirect = [r for r in reports if r.status == "REDIRECT"]
    stashed = [r for r in reports if r.status == "STASHED"]
    lines.append("")
    lines.append(f"Total: {len(reports)} skills — {len(active)} active, {len(redirect)} redirect, {len(stashed)} stashed")
    if active:
        avg = sum(r.score for r in active) / len(active)
        lines.append(f"Active skill average score: {avg:.1f}/10")

    return "\n".join(lines)


def format_json(reports: list[SkillReport]) -> str:
    """Format reports as JSON."""
    data = {
        "schema_version": 1,
        "generated": datetime.now(timezone.utc).isoformat(),
        "tool": "skill_health.py",
        "summary": {
            "total": len(reports),
            "active": len([r for r in reports if r.status == "ACTIVE"]),
            "redirect": len([r for r in reports if r.status == "REDIRECT"]),
            "stashed": len([r for r in reports if r.status == "STASHED"]),
            "avg_active_score": round(
                sum(r.score for r in reports if r.status == "ACTIVE")
                / max(1, len([r for r in reports if r.status == "ACTIVE"])),
                1,
            ),
        },
        "skills": [asdict(r) for r in reports],
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


def format_markdown(reports: list[SkillReport]) -> str:
    """Format reports as a markdown table report."""
    lines: list[str] = []
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines.append(f"# Skill Health Report — {ts}")
    lines.append("")
    lines.append("| Score | Status | Lane | CLI | Scripts | Det | XLane | Skill |")
    lines.append("|------:|--------|------|:---:|--------:|:---:|:-----:|-------|")
    for r in reports:
        cli = "Y" if r.has_cli_commands else "-"
        scr = f"{len(r.scripts_found)}/{len(r.referenced_scripts)}" if r.referenced_scripts else "-"
        det = "Y" if r.deterministic_output else "-"
        xl = "Y" if r.cross_lane else "-"
        lines.append(f"| {r.score:.1f} | {r.status} | {r.lane} | {cli} | {scr} | {det} | {xl} | {r.name} |")

    active = [r for r in reports if r.status == "ACTIVE"]
    if active:
        avg = sum(r.score for r in active) / len(active)
        lines.append("")
        lines.append(f"**Active average: {avg:.1f}/10** | {len(active)} active, "
                      f"{len([r for r in reports if r.status == 'REDIRECT'])} redirect, "
                      f"{len([r for r in reports if r.status == 'STASHED'])} stashed")

    # Findings section
    flagged = [r for r in reports if r.findings]
    if flagged:
        lines.append("")
        lines.append("## Findings")
        for r in flagged:
            lines.append(f"\n### {r.lane}/{r.name} ({r.score:.1f})")
            for f in r.findings:
                lines.append(f"- {f}")

    return "\n".join(lines)


# =============================================================================
# CLI
# =============================================================================


def main() -> None:
    configure_utf8_output()
    logger = setup_logging("skill_health")

    parser = argparse.ArgumentParser(
        description="Skill Health Auditor — automated 1-10 scoring for all skill lanes."
    )
    parser.add_argument("--lane", choices=["claude", "codex"], help="Audit only this lane")
    parser.add_argument("--json", action="store_true", help="Emit JSON report to stdout")
    parser.add_argument("--md", action="store_true", help="Emit markdown report to stdout")
    parser.add_argument("--emit", metavar="PATH", help="Write report to file (JSON or MD by extension)")
    parser.add_argument("--min-score", type=float, help="Show only skills >= this score")
    parser.add_argument("--below", type=float, help="Show only skills < this score")
    parser.add_argument("--active-only", action="store_true", help="Hide redirect/stashed skills")
    args = parser.parse_args()

    repo_root = find_repo_root()
    logger.info("Scanning skills from %s", repo_root)

    reports = run_audit(repo_root, lane_filter=args.lane)

    # Filters
    if args.min_score is not None:
        reports = [r for r in reports if r.score >= args.min_score]
    if args.below is not None:
        reports = [r for r in reports if r.score < args.below]
    if args.active_only:
        reports = [r for r in reports if r.status == "ACTIVE"]

    # Output
    if args.json:
        print(format_json(reports))
    elif args.md:
        print(format_markdown(reports))
    elif args.emit:
        emit_path = Path(args.emit)
        if emit_path.suffix == ".json":
            emit_path.write_text(format_json(reports), encoding="utf-8")
        else:
            emit_path.write_text(format_markdown(reports), encoding="utf-8")
        print(f"Report written to {emit_path}")
    else:
        print(format_summary(reports))


if __name__ == "__main__":
    main()
