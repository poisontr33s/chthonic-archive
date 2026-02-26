#!/usr/bin/env python3
#-*- coding: utf-8 -*-
"""
Handoff Audit.

Audits cross-agent handoff quality across canonical and triad roots, computes:
- contract compliance
- evidence/verifiability
- continuity quality
- noise discipline
- cross-lane routing integrity
- linguistic profile compliance

Outputs:
- codex/mailbox/HANDOFF_AUDIT_LATEST.json
- codex/mailbox/HANDOFF_AUDIT_LATEST.md
- claude/mailbox/HANDOFF_AUDIT_LATEST.json
- claude/mailbox/HANDOFF_AUDIT_LATEST.md
"""

from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.lib.shared import configure_utf8_output, find_repo_root


SCHEMA_VERSION = 2
REPO_LANES = {"codex", "claude", "gemini"}

RE_HM_START = re.compile(r"^---\s*$")
RE_HM_KV = re.compile(r"^([A-Za-z0-9_-]+)\s*:\s*(.*?)\s*$")
RE_SECTION = re.compile(r"^#{1,6}\s+(.+?)\s*$")
RE_BULLET = re.compile(r"^\s*(?:[-*]|\d+\.)\s+")
RE_CODE_INLINE_COMMAND = re.compile(r"`[^`]*(?:uv run|git|pwsh|bun|cargo|python)[^`]*`", re.IGNORECASE)
RE_COMMAND_LINE = re.compile(r"^\s*(?:uv run|git|pwsh|bun|cargo|python)\b", re.IGNORECASE)
RE_PATH_UNIX = re.compile(r"\b(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+\.[A-Za-z0-9]{1,12}\b")
RE_PATH_WIN = re.compile(r"\b[A-Za-z]:\\(?:[^\\/:*?\"<>|\r\n]+\\)+[^\\/:*?\"<>|\r\n]+\.[A-Za-z0-9]{1,12}\b")
RE_CODE_FENCE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
RE_INLINE_CODE = re.compile(r"`[^`\n]+`")

REQUIRED_FRONTMATTER = ["type", "from", "to", "created", "priority", "scope"]
REQUIRED_SECTION_KEYS = ["actions_taken", "files_changed", "how_to_verify", "next_actions"]

SECTION_ALIASES: dict[str, list[str]] = {
    "actions_taken": ["Actions Taken", "What I Did", "What I Did (Concrete Changes)"],
    "files_changed": ["Files Changed", "Changed Files"],
    "how_to_verify": ["How to verify", "How To Verify", "Verification Evidence", "How to Verify"],
    "next_actions": ["Next Actions", "What's next", "What’s next", "What is next"],
    "tasks": ["Tasks", "Task List"],
}

WEIGHTS = {
    "contract_compliance": 0.30,
    "evidence_verifiability": 0.25,
    "continuity_quality": 0.20,
    "noise_discipline": 0.15,
    "cross_lane_integrity": 0.10,
}

CREATIVITY_ABSTRACTION_TERMS = {
    "abstraction", "abstract", "conceptual", "ontology", "protocol", "architecture",
    "taxonomy", "model", "framework", "synthesis", "matrix", "nonlinear", "non-linear",
    "phase", "strata", "bridge", "migration", "contract", "pattern", "invariant",
}
CREATIVITY_CHTHONIC_TERMS = {
    "chthonic", "ankh", "wedjat", "ogdoad", "temple", "spectrum", "khipu",
    "cartouche", "wptg", "upcycle", "transmutation", "matriarch",
}
CREATIVITY_NOVELTY_TERMS = {
    "novel", "creative", "iterate", "evolve", "emergent", "hybrid", "fuse",
    "derive", "derived", "synthesize", "remediate", "reframe", "bridge",
}

LINGUISTIC_PROFILE_NAME = "milfological_female_derived"
LINGUISTIC_DISALLOWED_TERMS = {
    "he", "him", "his", "himself",
    "male", "masculine", "man", "men",
    "boy", "boys", "guy", "guys", "dude",
    "father", "patriarch", "brother", "bros",
    "sir", "king", "gentleman", "gentlemen",
}
LINGUISTIC_PREFERRED_TERMS = {
    "she", "her", "hers", "herself",
    "female", "feminine", "woman", "women",
    "matriarch", "lady", "sister", "queen",
}
LINGUISTIC_TERM_EQUIVALENTS = {
    "he": "she",
    "him": "her",
    "his": "her",
    "himself": "herself",
    "male": "female",
    "masculine": "feminine",
    "man": "woman",
    "men": "women",
    "boy": "girl/woman",
    "boys": "girls/women",
    "guy": "woman",
    "guys": "women",
    "dude": "lady",
    "father": "mother",
    "patriarch": "matriarch",
    "brother": "sister",
    "bros": "sisters",
    "sir": "madam",
    "king": "queen",
    "gentleman": "lady",
    "gentlemen": "ladies",
}
LINGUISTIC_DISALLOWED_PATTERNS = {
    term: re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
    for term in LINGUISTIC_DISALLOWED_TERMS
}
LINGUISTIC_PREFERRED_PATTERNS = {
    term: re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
    for term in LINGUISTIC_PREFERRED_TERMS
}


@dataclass(frozen=True)
class RootConfig:
    token: str
    path: str
    recursive: bool
    handoff_glob: str
    markdown_glob: str


ROOT_CONFIGS = [
    RootConfig("codex", "codex/mailbox", False, "SESSION_HANDOFF_*.md", "*.md"),
    RootConfig("claude", "claude/mailbox", False, "SESSION_HANDOFF_*.md", "*.md"),
    RootConfig("gemini", "gemini/mailbox", False, "SESSION_HANDOFF_*.md", "*.md"),
    RootConfig(".codex", ".codex/mailbox", False, "SESSION_HANDOFF_*.md", "*.md"),
    RootConfig(".claude", ".claude/mailbox", False, "SESSION_HANDOFF_*.md", "*.md"),
    RootConfig("claude-codex-gemini", "claude-codex-gemini", True, "*HANDOFF*.md", "*.md"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_lane(value: str | None) -> str | None:
    if not value:
        return None
    name = value.strip().lower()
    if name in REPO_LANES:
        return name
    if name == ".codex":
        return "codex"
    if name == ".claude":
        return "claude"
    return name if name else None


def root_expected_lane(root_token: str) -> str | None:
    if root_token == ".codex":
        return "codex"
    if root_token == ".claude":
        return "claude"
    if root_token in REPO_LANES:
        return root_token
    return None


def parse_frontmatter(md_text: str) -> tuple[dict[str, str], str]:
    lines = md_text.splitlines()
    if not lines or not RE_HM_START.match(lines[0]):
        return {}, md_text
    end = None
    for i in range(1, len(lines)):
        if RE_HM_START.match(lines[i]):
            end = i
            break
    if end is None:
        return {}, md_text
    fm: dict[str, str] = {}
    for ln in lines[1:end]:
        m = RE_HM_KV.match(ln)
        if not m:
            continue
        key = m.group(1).strip()
        value = m.group(2).strip()
        if key:
            fm[key] = value
    body = "\n".join(lines[end + 1 :])
    return fm, body


def parse_sections(md_body: str) -> dict[str, str]:
    current: str | None = None
    sections: dict[str, list[str]] = {}
    for line in md_body.splitlines():
        m = RE_SECTION.match(line)
        if m:
            current = m.group(1).strip()
            sections.setdefault(current, [])
            continue
        if current is not None:
            sections[current].append(line)
    out: dict[str, str] = {}
    for key, lines in sections.items():
        text = "\n".join(lines).strip()
        if text:
            out[key] = text
    return out


def find_section_content(sections: dict[str, str], aliases: list[str]) -> str:
    for alias in aliases:
        if alias in sections:
            return sections[alias]
    return ""


def count_bullets(text: str) -> int:
    if not text:
        return 0
    return sum(1 for line in text.splitlines() if RE_BULLET.match(line))


def count_command_refs(md_body: str) -> int:
    inline_count = len(RE_CODE_INLINE_COMMAND.findall(md_body))
    line_count = sum(1 for line in md_body.splitlines() if RE_COMMAND_LINE.search(line))
    return inline_count + line_count


def count_path_refs(md_body: str) -> int:
    return len(RE_PATH_UNIX.findall(md_body)) + len(RE_PATH_WIN.findall(md_body))


def count_term_hits(text: str, terms: set[str]) -> int:
    lower = text.lower()
    total = 0
    for term in terms:
        total += len(re.findall(rf"\b{re.escape(term)}\b", lower))
    return total


def strip_markdown_code(text: str) -> str:
    no_fence = RE_CODE_FENCE.sub(" ", text)
    return RE_INLINE_CODE.sub(" ", no_fence)


def count_pattern_hits(text: str, patterns: dict[str, re.Pattern[str]]) -> dict[str, int]:
    hits: dict[str, int] = {}
    for term, pattern in patterns.items():
        count = len(pattern.findall(text))
        if count > 0:
            hits[term] = count
    return hits


def extract_domain_roots(md_body: str) -> set[str]:
    roots: set[str] = set()
    for match in RE_PATH_UNIX.findall(md_body):
        token = match.strip().strip("`'\"")
        if token.startswith(("http://", "https://")):
            continue
        root = token.split("/", 1)[0].strip()
        if root:
            roots.add(root.lower())
    for match in RE_PATH_WIN.findall(md_body):
        token = match.strip().strip("`'\"")
        parts = token.split("\\")
        if len(parts) >= 2:
            roots.add(parts[0].lower())
    return roots


def geometric_mean(values: list[float]) -> float:
    if not values:
        return 0.0
    product = 1.0
    for value in values:
        product *= max(0.001, float(value))
    return product ** (1.0 / len(values))


def relpath(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def glob_files(root: Path, pattern: str, recursive: bool) -> list[Path]:
    if recursive:
        return sorted([p for p in root.rglob(pattern) if p.is_file()])
    return sorted([p for p in root.glob(pattern) if p.is_file()])


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def score_handoff(
    *,
    handoff_path: Path,
    repo_root: Path,
    root_token: str,
    root_md_count: int,
    root_handoff_count: int,
) -> dict[str, Any]:
    raw = handoff_path.read_text(encoding="utf-8", errors="replace")
    frontmatter, body = parse_frontmatter(raw)
    has_frontmatter = bool(frontmatter)
    sections = parse_sections(body)

    section_presence = {
        key: bool(find_section_content(sections, aliases))
        for key, aliases in SECTION_ALIASES.items()
        if key in REQUIRED_SECTION_KEYS
    }
    missing_sections = [key for key in REQUIRED_SECTION_KEYS if not section_presence.get(key, False)]
    missing_frontmatter = [key for key in REQUIRED_FRONTMATTER if not frontmatter.get(key)]

    actions_text = find_section_content(sections, SECTION_ALIASES["actions_taken"])
    files_text = find_section_content(sections, SECTION_ALIASES["files_changed"])
    verify_text = find_section_content(sections, SECTION_ALIASES["how_to_verify"])
    next_text = find_section_content(sections, SECTION_ALIASES["next_actions"])
    tasks_text = find_section_content(sections, SECTION_ALIASES["tasks"])

    action_bullets = count_bullets(actions_text)
    files_bullets = count_bullets(files_text)
    next_bullets = count_bullets(next_text)
    task_bullets = count_bullets(tasks_text)

    command_refs = count_command_refs(body)
    path_refs = count_path_refs(body)
    domain_roots = extract_domain_roots(body)

    declared_units = len(REQUIRED_SECTION_KEYS) + task_bullets
    completed_contract_units = sum(1 for key in REQUIRED_SECTION_KEYS if section_presence.get(key))
    completed_evidence_units = (1 if command_refs > 0 else 0) + (1 if path_refs > 0 else 0)
    completed_units = completed_contract_units + completed_evidence_units
    est_ratio = clamp01(completed_units / float(max(1, declared_units)))

    fm_completeness = 1.0 - (len(missing_frontmatter) / float(len(REQUIRED_FRONTMATTER)))
    section_completeness = 1.0 - (len(missing_sections) / float(len(REQUIRED_SECTION_KEYS)))

    name = handoff_path.name
    if name.startswith("SESSION_HANDOFF_"):
        filename_score = 1.0
    elif "HANDOFF" in name:
        filename_score = 0.7
    else:
        filename_score = 0.0

    contract_compliance = clamp01(
        0.50 * fm_completeness + 0.40 * section_completeness + 0.10 * filename_score
    )

    verify_presence = 1.0 if bool(verify_text.strip()) else 0.0
    command_signal = clamp01(command_refs / 2.0)
    path_signal = clamp01(path_refs / 3.0)
    evidence_verifiability = clamp01(
        0.40 * verify_presence + 0.30 * command_signal + 0.30 * path_signal
    )

    in_response = 1.0 if bool(frontmatter.get("in_response_to")) else 0.0
    scope_present = 1.0 if bool(frontmatter.get("scope")) else 0.0
    continuity_quality = clamp01(
        0.35 * (1.0 if section_presence.get("actions_taken") else 0.0)
        + 0.35 * (1.0 if section_presence.get("next_actions") else 0.0)
        + 0.15 * in_response
        + 0.15 * scope_present
    )

    handoff_ratio = (root_handoff_count / float(max(1, root_md_count)))
    noise_discipline = clamp01(handoff_ratio / 0.20)

    from_lane = normalize_lane(frontmatter.get("from"))
    to_lane = normalize_lane(frontmatter.get("to"))
    recognized = 1.0 if (from_lane in REPO_LANES and to_lane in REPO_LANES) else 0.0
    lane_direction = 1.0 if (from_lane and to_lane and from_lane != to_lane) else 0.7
    expected_lane = root_expected_lane(root_token)
    if expected_lane and to_lane:
        alignment = 1.0 if to_lane == expected_lane else 0.5
    else:
        alignment = 0.8
    cross_lane_integrity = clamp01(0.45 * recognized + 0.25 * lane_direction + 0.30 * alignment)

    technical_index = (
        WEIGHTS["contract_compliance"] * contract_compliance
        + WEIGHTS["evidence_verifiability"] * evidence_verifiability
        + WEIGHTS["continuity_quality"] * continuity_quality
        + WEIGHTS["noise_discipline"] * noise_discipline
        + WEIGHTS["cross_lane_integrity"] * cross_lane_integrity
    )
    technical_score_10 = round(1.0 + 9.0 * clamp01(technical_index), 2)

    # Hard caps for missing core contract elements.
    if missing_frontmatter:
        technical_score_10 = min(technical_score_10, 5.0)
    if not section_presence.get("how_to_verify"):
        technical_score_10 = min(technical_score_10, 6.0)
    if not section_presence.get("next_actions"):
        technical_score_10 = min(technical_score_10, 7.0)
    technical_score_10 = round(technical_score_10, 2)

    words = re.findall(r"[A-Za-z][A-Za-z0-9_\-']*", body)
    word_count = len(words)
    abstraction_hits = count_term_hits(body, CREATIVITY_ABSTRACTION_TERMS)
    chthonic_hits = count_term_hits(body, CREATIVITY_CHTHONIC_TERMS)
    novelty_hits = count_term_hits(body, CREATIVITY_NOVELTY_TERMS)

    heading_count = len([line for line in body.splitlines() if re.match(r"^#{1,6}\s+", line)])
    deep_heading_count = len([line for line in body.splitlines() if re.match(r"^#{3,6}\s+", line)])
    section_count = len(sections)
    present_sections_count = sum(1 for key in REQUIRED_SECTION_KEYS if section_presence.get(key))
    domain_count = len(domain_roots)

    abstraction_density = clamp01(
        abstraction_hits / max(4.0, float(word_count) / 120.0)
    )
    chthonic_alignment = clamp01(
        chthonic_hits / max(2.0, float(word_count) / 240.0)
    )
    structural_depth = clamp01(
        (section_count + heading_count + deep_heading_count + present_sections_count) / 20.0
    )
    synthesis_span = clamp01(domain_count / 6.0)
    novelty_signal = clamp01(
        (novelty_hits + task_bullets + next_bullets) / max(4.0, float(word_count) / 140.0)
    )

    creativity_components = [
        abstraction_density,
        chthonic_alignment,
        structural_depth,
        synthesis_span,
        novelty_signal,
    ]
    creativity_index = clamp01(geometric_mean(creativity_components))
    creativity_score_10 = round(1.0 + 9.0 * creativity_index, 2)

    linguistic_text = strip_markdown_code(body)
    disallowed_term_hits = count_pattern_hits(linguistic_text, LINGUISTIC_DISALLOWED_PATTERNS)
    preferred_term_hits = count_pattern_hits(linguistic_text, LINGUISTIC_PREFERRED_PATTERNS)
    disallowed_total = sum(disallowed_term_hits.values())
    preferred_total = sum(preferred_term_hits.values())
    replacement_suggestions = {
        term: LINGUISTIC_TERM_EQUIVALENTS.get(term, "replace_with_female_derived_equivalent")
        for term in sorted(disallowed_term_hits)
    }

    disallowed_penalty = clamp01(disallowed_total / max(1.0, float(word_count) / 45.0))
    preferred_signal = clamp01(preferred_total / max(2.0, float(word_count) / 100.0))
    linguistic_profile_compliance = clamp01((1.0 - disallowed_penalty) * 0.90 + 0.10 * preferred_signal)
    if disallowed_total == 0:
        linguistic_profile_compliance = max(linguistic_profile_compliance, 0.95)
    elif disallowed_total >= 6:
        linguistic_profile_compliance = min(linguistic_profile_compliance, 0.20)
    elif disallowed_total >= 3:
        linguistic_profile_compliance = min(linguistic_profile_compliance, 0.45)
    else:
        linguistic_profile_compliance = min(linguistic_profile_compliance, 0.69)
    linguistic_score_10 = round(1.0 + 9.0 * linguistic_profile_compliance, 2)

    technical_norm = clamp01((technical_score_10 - 1.0) / 9.0)
    balance_term = math.sqrt(max(0.0, technical_norm * creativity_index))
    creative_expectation = clamp01((abstraction_hits + chthonic_hits + novelty_hits) / 8.0)
    technical_weight = 0.75 - (0.20 * creative_expectation)
    creativity_weight = 0.15 + (0.20 * creative_expectation)
    balance_weight = 0.10
    technical_creative_index = clamp01(
        technical_weight * technical_norm
        + creativity_weight * creativity_index
        + balance_weight * balance_term
    )
    overall_index = clamp01(0.80 * technical_creative_index + 0.20 * linguistic_profile_compliance)
    overall_score_10 = round(1.0 + 9.0 * overall_index, 2)
    if disallowed_total >= 1:
        overall_score_10 = min(overall_score_10, 6.5)
    if disallowed_total >= 3:
        overall_score_10 = min(overall_score_10, 5.5)
    if disallowed_total >= 6:
        overall_score_10 = min(overall_score_10, 4.5)
    overall_score_10 = round(overall_score_10, 2)

    reasoning: list[str] = []
    if missing_frontmatter:
        reasoning.append(f"missing_frontmatter={missing_frontmatter}")
    if missing_sections:
        reasoning.append(f"missing_sections={missing_sections}")
    if creativity_score_10 < 6.0:
        reasoning.append("low_creativity_signal")
    if disallowed_total > 0:
        reasoning.append("linguistic_profile_non_compliant")
        reasoning.append(f"linguistic_disallowed_terms={sorted(disallowed_term_hits)}")
    if not reasoning:
        reasoning.append("contract_complete")
    if path_refs == 0:
        reasoning.append("no_path_references_detected")
    if command_refs == 0:
        reasoning.append("no_command_references_detected")

    return {
        "path": relpath(repo_root, handoff_path),
        "root_token": root_token,
        "filename": handoff_path.name,
        "mtime_utc": datetime.fromtimestamp(handoff_path.stat().st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "has_frontmatter": has_frontmatter,
        "frontmatter": frontmatter,
        "missing_frontmatter": missing_frontmatter,
        "section_presence": section_presence,
        "missing_sections": missing_sections,
        "reference_counts": {"commands": command_refs, "paths": path_refs},
        "bullet_counts": {
            "actions_taken": action_bullets,
            "files_changed": files_bullets,
            "next_actions": next_bullets,
            "tasks": task_bullets,
        },
        "declared_units": declared_units,
        "completed_units": completed_units,
        "est_ratio": round(est_ratio, 4),
        "dimension_scores": {
            "contract_compliance": round(contract_compliance, 4),
            "evidence_verifiability": round(evidence_verifiability, 4),
            "continuity_quality": round(continuity_quality, 4),
            "noise_discipline": round(noise_discipline, 4),
            "cross_lane_integrity": round(cross_lane_integrity, 4),
            "linguistic_profile_compliance": round(linguistic_profile_compliance, 4),
        },
        "creativity_matrix": {
            "abstraction_density": round(abstraction_density, 4),
            "chthonic_alignment": round(chthonic_alignment, 4),
            "structural_depth": round(structural_depth, 4),
            "synthesis_span": round(synthesis_span, 4),
            "novelty_signal": round(novelty_signal, 4),
            "creative_expectation": round(creative_expectation, 4),
            "weight_profile": {
                "technical_weight": round(technical_weight, 4),
                "creativity_weight": round(creativity_weight, 4),
                "balance_weight": round(balance_weight, 4),
            },
            "domain_roots": sorted(domain_roots),
            "word_count": word_count,
            "term_hits": {
                "abstraction": abstraction_hits,
                "chthonic": chthonic_hits,
                "novelty": novelty_hits,
            },
            "creativity_score_10": creativity_score_10,
        },
        "linguistic_profile": {
            "name": LINGUISTIC_PROFILE_NAME,
            "compliance_index": round(linguistic_profile_compliance, 4),
            "linguistic_score_10": linguistic_score_10,
            "disallowed_total": disallowed_total,
            "preferred_total": preferred_total,
            "disallowed_term_hits": disallowed_term_hits,
            "preferred_term_hits": preferred_term_hits,
            "replacement_suggestions": replacement_suggestions,
        },
        "technical_score_10": technical_score_10,
        "overall_score_10": overall_score_10,
        "score_10": overall_score_10,
        "reasoning": reasoning,
    }


def build_audit(repo_root: Path) -> dict[str, Any]:
    roots_payload: list[dict[str, Any]] = []
    handoffs: list[dict[str, Any]] = []

    for cfg in ROOT_CONFIGS:
        root_path = repo_root / cfg.path
        if not root_path.exists():
            roots_payload.append(
                {
                    "token": cfg.token,
                    "path": cfg.path,
                    "exists": False,
                    "recursive": cfg.recursive,
                    "md_count": 0,
                    "handoff_count": 0,
                    "handoff_ratio": 0.0,
                    "latest_handoff": None,
                }
            )
            continue

        md_files = glob_files(root_path, cfg.markdown_glob, cfg.recursive)
        handoff_files = glob_files(root_path, cfg.handoff_glob, cfg.recursive)
        md_count = len(md_files)
        handoff_count = len(handoff_files)
        latest_handoff = (
            relpath(repo_root, sorted(handoff_files, key=lambda p: p.stat().st_mtime, reverse=True)[0])
            if handoff_files
            else None
        )
        handoff_ratio = (handoff_count / float(max(1, md_count)))

        roots_payload.append(
            {
                "token": cfg.token,
                "path": cfg.path,
                "exists": True,
                "recursive": cfg.recursive,
                "md_count": md_count,
                "handoff_count": handoff_count,
                "handoff_ratio": round(handoff_ratio, 4),
                "latest_handoff": latest_handoff,
            }
        )

        for handoff in handoff_files:
            handoffs.append(
                score_handoff(
                    handoff_path=handoff,
                    repo_root=repo_root,
                    root_token=cfg.token,
                    root_md_count=md_count,
                    root_handoff_count=handoff_count,
                )
            )

    handoffs_sorted = sorted(handoffs, key=lambda item: (item["score_10"], item["mtime_utc"]))
    score_values = [float(item.get("overall_score_10", item.get("score_10", 0.0))) for item in handoffs_sorted]
    technical_values = [float(item.get("technical_score_10", item.get("score_10", 0.0))) for item in handoffs_sorted]
    creativity_values = [
        float((item.get("creativity_matrix") or {}).get("creativity_score_10", item.get("score_10", 0.0)))
        for item in handoffs_sorted
    ]
    linguistic_values = [
        float((item.get("linguistic_profile") or {}).get("linguistic_score_10", item.get("score_10", 0.0)))
        for item in handoffs_sorted
    ]
    est_ratios = [float(item["est_ratio"]) for item in handoffs_sorted]

    summary = {
        "handoff_count": len(handoffs_sorted),
        "avg_score_10": round(sum(score_values) / len(score_values), 3) if score_values else 0.0,
        "avg_overall_score_10": round(sum(score_values) / len(score_values), 3) if score_values else 0.0,
        "avg_technical_score_10": round(sum(technical_values) / len(technical_values), 3) if technical_values else 0.0,
        "avg_creativity_score_10": round(sum(creativity_values) / len(creativity_values), 3) if creativity_values else 0.0,
        "avg_linguistic_score_10": round(sum(linguistic_values) / len(linguistic_values), 3) if linguistic_values else 0.0,
        "min_score_10": min(score_values) if score_values else 0.0,
        "max_score_10": max(score_values) if score_values else 0.0,
        "est_ratio_avg": round(sum(est_ratios) / len(est_ratios), 4) if est_ratios else 0.0,
        "frontmatter_complete_count": sum(1 for item in handoffs_sorted if not item["missing_frontmatter"]),
        "sections_complete_count": sum(1 for item in handoffs_sorted if not item["missing_sections"]),
        "linguistic_non_compliant_count": sum(
            1
            for item in handoffs_sorted
            if int((item.get("linguistic_profile") or {}).get("disallowed_total", 0) or 0) > 0
        ),
        "linguistic_compliant_count": sum(
            1
            for item in handoffs_sorted
            if int((item.get("linguistic_profile") or {}).get("disallowed_total", 0) or 0) == 0
        ),
        "linguistic_profile_name": LINGUISTIC_PROFILE_NAME,
        "below_6_count": sum(1 for item in handoffs_sorted if float(item.get("overall_score_10", item.get("score_10", 0.0))) < 6.0),
        "between_6_8_count": sum(1 for item in handoffs_sorted if 6.0 <= float(item.get("overall_score_10", item.get("score_10", 0.0))) < 8.0),
        "above_8_count": sum(1 for item in handoffs_sorted if float(item.get("overall_score_10", item.get("score_10", 0.0))) >= 8.0),
    }
    summary["strict_linguistic_pass"] = bool(summary["linguistic_non_compliant_count"] == 0)

    derived_metrics = compute_derived_metrics(roots_payload, handoffs_sorted, summary)
    peer_scoring_matrix = compute_peer_scoring_matrix(handoffs_sorted)

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_on": utc_now(),
        "scoring_model": {
            "weights": WEIGHTS,
            "required_frontmatter": REQUIRED_FRONTMATTER,
            "required_sections": REQUIRED_SECTION_KEYS,
            "linguistic_profile_name": LINGUISTIC_PROFILE_NAME,
            "linguistic_disallowed_terms": sorted(LINGUISTIC_DISALLOWED_TERMS),
            "linguistic_preferred_terms": sorted(LINGUISTIC_PREFERRED_TERMS),
            "hard_caps": {
                "missing_frontmatter_cap": 5.0,
                "missing_verify_cap": 6.0,
                "missing_next_actions_cap": 7.0,
                "linguistic_violation_cap_1plus": 6.5,
                "linguistic_violation_cap_3plus": 5.5,
                "linguistic_violation_cap_6plus": 4.5,
            },
        },
        "roots": roots_payload,
        "handoffs": handoffs_sorted,
        "summary": summary,
        "derived_metrics": derived_metrics,
        "peer_scoring_matrix": peer_scoring_matrix,
    }


def compute_derived_metrics(
    roots_payload: list[dict[str, Any]],
    handoffs_sorted: list[dict[str, Any]],
    summary: dict[str, Any],
) -> dict[str, Any]:
    if not handoffs_sorted:
        return {
            "contract_integrity_index": 0.0,
            "evidence_traceability_index": 0.0,
            "continuity_bridge_index": 0.0,
            "linguistic_profile_index": 0.0,
            "lane_balance_index": 0.0,
            "triad_presence_index": 0.0,
            "handoff_density_index": 0.0,
            "migration_readiness_index": 0.0,
            "global_workspace_alignment_10": 1.0,
        }

    contract_vals: list[float] = []
    evidence_vals: list[float] = []
    continuity_vals: list[float] = []
    linguistic_vals: list[float] = []
    response_link_count = 0
    scope_present_count = 0

    for item in handoffs_sorted:
        missing_fm = len(item.get("missing_frontmatter", []))
        missing_sec = len(item.get("missing_sections", []))
        contract = clamp01(0.60 * (1.0 - missing_fm / float(len(REQUIRED_FRONTMATTER))) + 0.40 * (1.0 - missing_sec / float(len(REQUIRED_SECTION_KEYS))))
        contract_vals.append(contract)

        refs = item.get("reference_counts", {})
        commands = int(refs.get("commands", 0) or 0)
        paths = int(refs.get("paths", 0) or 0)
        evidence = clamp01(0.50 * min(1.0, commands / 2.0) + 0.50 * min(1.0, paths / 5.0))
        evidence_vals.append(evidence)

        sections = item.get("section_presence", {})
        actions = 1.0 if sections.get("actions_taken") else 0.0
        verify = 1.0 if sections.get("how_to_verify") else 0.0
        next_actions = 1.0 if sections.get("next_actions") else 0.0

        fm = item.get("frontmatter", {})
        in_response = 1.0 if fm.get("in_response_to") else 0.0
        scope_present = 1.0 if fm.get("scope") else 0.0
        if in_response > 0:
            response_link_count += 1
        if scope_present > 0:
            scope_present_count += 1

        continuity = clamp01(0.30 * actions + 0.30 * verify + 0.20 * next_actions + 0.10 * in_response + 0.10 * scope_present)
        continuity_vals.append(continuity)

        lp = item.get("linguistic_profile", {})
        linguistic_vals.append(clamp01(float(lp.get("compliance_index", 0.0) or 0.0)))

    by_token = {row.get("token"): row for row in roots_payload}
    codex_count = int((by_token.get("codex") or {}).get("handoff_count") or 0)
    claude_count = int((by_token.get("claude") or {}).get("handoff_count") or 0)
    gemini_count = int((by_token.get("gemini") or {}).get("handoff_count") or 0)

    lane_balance_index = 1.0 - (abs(codex_count - claude_count) / float(max(1, codex_count + claude_count)))
    lane_balance_index = clamp01(lane_balance_index)

    triad_presence_index = sum(1 for value in (codex_count, claude_count, gemini_count) if value > 0) / 3.0
    triad_presence_index = clamp01(triad_presence_index)

    density_ratios = []
    for token in ("codex", "claude", "gemini"):
        row = by_token.get(token)
        if not row:
            density_ratios.append(0.0)
            continue
        ratio = float(row.get("handoff_ratio") or 0.0)
        density_ratios.append(clamp01(ratio / 0.15))
    handoff_density_index = sum(density_ratios) / len(density_ratios)

    contract_integrity_index = sum(contract_vals) / len(contract_vals)
    evidence_traceability_index = sum(evidence_vals) / len(evidence_vals)
    continuity_bridge_index = sum(continuity_vals) / len(continuity_vals)
    linguistic_profile_index = sum(linguistic_vals) / len(linguistic_vals)
    avg_score_norm = clamp01(float(summary.get("avg_score_10", 0.0)) / 10.0)

    migration_readiness_index = clamp01(
        0.24 * avg_score_norm
        + 0.20 * contract_integrity_index
        + 0.14 * evidence_traceability_index
        + 0.12 * continuity_bridge_index
        + 0.10 * linguistic_profile_index
        + 0.10 * lane_balance_index
        + 0.05 * triad_presence_index
        + 0.05 * handoff_density_index
    )

    return {
        "contract_integrity_index": round(contract_integrity_index, 4),
        "evidence_traceability_index": round(evidence_traceability_index, 4),
        "continuity_bridge_index": round(continuity_bridge_index, 4),
        "linguistic_profile_index": round(linguistic_profile_index, 4),
        "lane_balance_index": round(lane_balance_index, 4),
        "triad_presence_index": round(triad_presence_index, 4),
        "handoff_density_index": round(handoff_density_index, 4),
        "response_link_coverage": round(response_link_count / float(len(handoffs_sorted)), 4),
        "scope_coverage": round(scope_present_count / float(len(handoffs_sorted)), 4),
        "migration_readiness_index": round(migration_readiness_index, 4),
        "global_workspace_alignment_10": round(1.0 + 9.0 * migration_readiness_index, 2),
    }


def compute_peer_scoring_matrix(handoffs_sorted: list[dict[str, Any]]) -> dict[str, Any]:
    pair_acc: dict[str, dict[str, float]] = {}
    for item in handoffs_sorted:
        fm = item.get("frontmatter", {})
        from_lane = normalize_lane(fm.get("from"))
        to_lane = normalize_lane(fm.get("to"))
        if from_lane not in REPO_LANES or to_lane not in REPO_LANES:
            continue

        key = f"{from_lane}_to_{to_lane}"
        entry = pair_acc.setdefault(
            key,
            {
                "from": from_lane,
                "to": to_lane,
                "handoff_count": 0.0,
                "sum_overall": 0.0,
                "sum_technical": 0.0,
                "sum_creativity": 0.0,
                "sum_linguistic": 0.0,
                "sum_est_ratio": 0.0,
            },
        )
        entry["handoff_count"] += 1.0
        entry["sum_overall"] += float(item.get("overall_score_10", item.get("score_10", 0.0)))
        entry["sum_technical"] += float(item.get("technical_score_10", item.get("score_10", 0.0)))
        entry["sum_creativity"] += float((item.get("creativity_matrix") or {}).get("creativity_score_10", item.get("score_10", 0.0)))
        entry["sum_linguistic"] += float((item.get("linguistic_profile") or {}).get("linguistic_score_10", item.get("score_10", 0.0)))
        entry["sum_est_ratio"] += float(item.get("est_ratio", 0.0))

    pair_scores: dict[str, dict[str, Any]] = {}
    for key, value in pair_acc.items():
        count = max(1.0, value["handoff_count"])
        pair_scores[key] = {
            "from": value["from"],
            "to": value["to"],
            "handoff_count": int(value["handoff_count"]),
            "avg_overall_score_10": round(value["sum_overall"] / count, 3),
            "avg_technical_score_10": round(value["sum_technical"] / count, 3),
            "avg_creativity_score_10": round(value["sum_creativity"] / count, 3),
            "avg_linguistic_score_10": round(value["sum_linguistic"] / count, 3),
            "avg_est_ratio": round(value["sum_est_ratio"] / count, 4),
        }

    evaluator_views: dict[str, list[dict[str, Any]]] = {}
    for evaluator in sorted(REPO_LANES):
        inbound = []
        for key, pair in pair_scores.items():
            if pair["to"] != evaluator:
                continue
            inbound.append(
                {
                    "rates_lane": pair["from"],
                    "handoff_count": pair["handoff_count"],
                    "overall_score_10": pair["avg_overall_score_10"],
                    "technical_score_10": pair["avg_technical_score_10"],
                    "creativity_score_10": pair["avg_creativity_score_10"],
                    "linguistic_score_10": pair["avg_linguistic_score_10"],
                }
            )
        inbound_sorted = sorted(
            inbound,
            key=lambda row: (row["overall_score_10"], row["creativity_score_10"], row["linguistic_score_10"], row["technical_score_10"]),
            reverse=True,
        )
        evaluator_views[evaluator] = inbound_sorted

    mutual_rankings: dict[str, dict[str, Any]] = {}
    pairings = [("codex", "claude"), ("codex", "gemini"), ("claude", "gemini")]
    for left, right in pairings:
        left_key = f"{left}_to_{right}"
        right_key = f"{right}_to_{left}"
        l2r = pair_scores.get(left_key)
        r2l = pair_scores.get(right_key)
        mutual_key = f"{left}<->{right}"
        mutual_rankings[mutual_key] = {
            "left_to_right": l2r,
            "right_to_left": r2l,
            "present_both_directions": bool(l2r and r2l),
        }
        if l2r and r2l:
            mutual_rankings[mutual_key]["overall_delta"] = round(
                float(l2r["avg_overall_score_10"]) - float(r2l["avg_overall_score_10"]), 3
            )
            mutual_rankings[mutual_key]["creativity_delta"] = round(
                float(l2r["avg_creativity_score_10"]) - float(r2l["avg_creativity_score_10"]), 3
            )
            mutual_rankings[mutual_key]["linguistic_delta"] = round(
                float(l2r["avg_linguistic_score_10"]) - float(r2l["avg_linguistic_score_10"]), 3
            )
            mutual_rankings[mutual_key]["technical_delta"] = round(
                float(l2r["avg_technical_score_10"]) - float(r2l["avg_technical_score_10"]), 3
            )

    return {
        "pair_scores": pair_scores,
        "evaluator_views": evaluator_views,
        "mutual_rankings": mutual_rankings,
    }


def to_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Handoff Audit",
        "",
        f"- Generated: `{payload.get('generated_on')}`",
        f"- Handoff count: `{payload.get('summary', {}).get('handoff_count')}`",
        f"- Avg overall score: `{payload.get('summary', {}).get('avg_overall_score_10', payload.get('summary', {}).get('avg_score_10'))}`",
        f"- Avg technical score: `{payload.get('summary', {}).get('avg_technical_score_10')}`",
        f"- Avg creativity score: `{payload.get('summary', {}).get('avg_creativity_score_10')}`",
        f"- Avg linguistic score: `{payload.get('summary', {}).get('avg_linguistic_score_10')}`",
        f"- Linguistic non-compliant: `{payload.get('summary', {}).get('linguistic_non_compliant_count')}`",
        f"- Avg est_ratio: `{payload.get('summary', {}).get('est_ratio_avg')}`",
        "",
        "## Root Coverage",
    ]
    for root in payload.get("roots", []):
        lines.append(
            "- "
            + f"`{root.get('token')}` path=`{root.get('path')}` "
            + f"md=`{root.get('md_count')}` handoff=`{root.get('handoff_count')}` "
            + f"ratio=`{root.get('handoff_ratio')}` latest=`{root.get('latest_handoff')}`"
        )

    lines.extend(["", "## Lowest Scores (Top 10)"])
    low = sorted(payload.get("handoffs", []), key=lambda item: item.get("score_10", 0.0))[:10]
    if not low:
        lines.append("- No handoffs found.")
    for item in low:
        lines.append(
            "- "
            + f"`{item.get('overall_score_10', item.get('score_10'))}` "
            + f"`{item.get('path')}` "
            + f"missing_frontmatter=`{item.get('missing_frontmatter')}` "
            + f"missing_sections=`{item.get('missing_sections')}` "
            + f"creativity=`{(item.get('creativity_matrix') or {}).get('creativity_score_10')}` "
            + f"linguistic=`{(item.get('linguistic_profile') or {}).get('linguistic_score_10')}` "
            + f"est_ratio=`{item.get('est_ratio')}`"
        )

    lines.extend(["", "## Highest Scores (Top 10)"])
    high = sorted(payload.get("handoffs", []), key=lambda item: item.get("score_10", 0.0), reverse=True)[:10]
    if not high:
        lines.append("- No handoffs found.")
    for item in high:
        lines.append(
            "- "
            + f"`{item.get('overall_score_10', item.get('score_10'))}` "
            + f"`{item.get('path')}` "
            + f"creativity=`{(item.get('creativity_matrix') or {}).get('creativity_score_10')}` "
            + f"linguistic=`{(item.get('linguistic_profile') or {}).get('linguistic_score_10')}` "
            + f"est_ratio=`{item.get('est_ratio')}`"
        )

    lines.extend(["", "## Gate Summary"])
    summary = payload.get("summary", {})
    for key in (
        "frontmatter_complete_count",
        "sections_complete_count",
        "linguistic_profile_name",
        "linguistic_non_compliant_count",
        "linguistic_compliant_count",
        "strict_linguistic_pass",
        "below_6_count",
        "between_6_8_count",
        "above_8_count",
    ):
        lines.append(f"- {key}: `{summary.get(key)}`")

    lines.extend(["", "## Derived Metrics"])
    derived = payload.get("derived_metrics", {})
    for key in (
        "contract_integrity_index",
        "evidence_traceability_index",
        "continuity_bridge_index",
        "linguistic_profile_index",
        "lane_balance_index",
        "triad_presence_index",
        "handoff_density_index",
        "response_link_coverage",
        "scope_coverage",
        "migration_readiness_index",
        "global_workspace_alignment_10",
    ):
        lines.append(f"- {key}: `{derived.get(key)}`")

    lines.extend(["", "## Creativity Matrix"])
    creative_sorted = sorted(
        payload.get("handoffs", []),
        key=lambda item: float((item.get("creativity_matrix") or {}).get("creativity_score_10", 0.0)),
        reverse=True,
    )
    for item in creative_sorted[:10]:
        cm = item.get("creativity_matrix") or {}
        lines.append(
            "- "
            + f"`{cm.get('creativity_score_10')}` "
            + f"`{item.get('path')}` "
            + f"abstraction=`{cm.get('abstraction_density')}` "
            + f"chthonic=`{cm.get('chthonic_alignment')}` "
            + f"synthesis=`{cm.get('synthesis_span')}`"
        )

    lines.extend(["", "## Linguistic Profile Compliance (Lowest 10)"])
    linguistic_sorted = sorted(
        payload.get("handoffs", []),
        key=lambda item: float((item.get("linguistic_profile") or {}).get("linguistic_score_10", 10.0)),
    )
    for item in linguistic_sorted[:10]:
        lp = item.get("linguistic_profile") or {}
        lines.append(
            "- "
            + f"`{lp.get('linguistic_score_10')}` "
            + f"`{item.get('path')}` "
            + f"disallowed_total=`{lp.get('disallowed_total')}` "
            + f"preferred_total=`{lp.get('preferred_total')}` "
            + f"terms=`{sorted((lp.get('disallowed_term_hits') or {}).keys())}`"
        )

    lines.extend(["", "## Peer Scoring Matrix"])
    peer = payload.get("peer_scoring_matrix", {})
    pairs = peer.get("pair_scores", {})
    if not pairs:
        lines.append("- No cross-lane pair scores available.")
    else:
        for key in sorted(pairs):
            row = pairs[key]
            lines.append(
                "- "
                + f"`{key}` count=`{row.get('handoff_count')}` "
                + f"overall=`{row.get('avg_overall_score_10')}` "
                + f"technical=`{row.get('avg_technical_score_10')}` "
                + f"creativity=`{row.get('avg_creativity_score_10')}` "
                + f"linguistic=`{row.get('avg_linguistic_score_10')}`"
            )

    lines.extend(["", "## Evaluator Views"])
    evaluator_views = peer.get("evaluator_views", {})
    for evaluator in sorted(evaluator_views):
        lines.append(f"- `{evaluator}` inbound rankings:")
        rows = evaluator_views.get(evaluator) or []
        if not rows:
            lines.append("  - (no inbound handoffs)")
            continue
        for row in rows:
            lines.append(
                "  - "
                + f"rates `{row.get('rates_lane')}` overall=`{row.get('overall_score_10')}` "
                + f"creativity=`{row.get('creativity_score_10')}` linguistic=`{row.get('linguistic_score_10')}` "
                + f"technical=`{row.get('technical_score_10')}` "
                + f"count=`{row.get('handoff_count')}`"
            )

    return "\n".join(lines).rstrip() + "\n"


def write_mailbox_artifacts(repo_root: Path, payload: dict[str, Any], mailboxes: list[str]) -> None:
    payload_json = json.dumps(payload, indent=2, ensure_ascii=True) + "\n"
    payload_md = to_markdown(payload)
    for mailbox in mailboxes:
        out_dir = repo_root / mailbox / "mailbox"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "HANDOFF_AUDIT_LATEST.json").write_text(payload_json, encoding="utf-8")
        (out_dir / "HANDOFF_AUDIT_LATEST.md").write_text(payload_md, encoding="utf-8")


def parse_mailboxes(value: str) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for chunk in (value or "").split(","):
        name = normalize_lane(chunk.strip())
        if name in REPO_LANES and name not in seen:
            seen.add(name)
            out.append(name)
    return out or ["codex", "claude"]


def main() -> int:
    configure_utf8_output()
    parser = argparse.ArgumentParser(description="Audit cross-agent handoff quality and emit score artifacts.")
    parser.add_argument("--mailboxes", default="codex,claude", help="Comma-separated output mailbox lanes.")
    parser.add_argument("--emit-mailbox", action="store_true", help="Write HANDOFF_AUDIT_LATEST.{json,md} to mailboxes.")
    parser.add_argument("--json", action="store_true", help="Print payload JSON to stdout.")
    parser.add_argument("--min-score", type=float, default=0.0, help="Fail if average score is below this threshold.")
    parser.add_argument("--strict-linguistic", action="store_true", help="Fail if any handoff has linguistic profile violations.")
    args = parser.parse_args()

    repo_root = find_repo_root()
    payload = build_audit(repo_root)

    if args.emit_mailbox:
        write_mailbox_artifacts(repo_root, payload, parse_mailboxes(args.mailboxes))

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=True))
    else:
        summary = payload.get("summary", {})
        print(
            "handoff_audit: "
            + f"count={summary.get('handoff_count')} "
            + f"avg_score={summary.get('avg_score_10')} "
            + f"avg_linguistic={summary.get('avg_linguistic_score_10')} "
            + f"linguistic_non_compliant={summary.get('linguistic_non_compliant_count')} "
            + f"avg_est_ratio={summary.get('est_ratio_avg')}"
        )

    avg_score = float(payload.get("summary", {}).get("avg_score_10", 0.0))
    if args.min_score > 0.0 and avg_score < args.min_score:
        print(f"gate_failed: avg_score={avg_score} < min_score={args.min_score}")
        return 2
    if args.strict_linguistic:
        non_compliant = int(payload.get("summary", {}).get("linguistic_non_compliant_count", 0) or 0)
        if non_compliant > 0:
            print(f"gate_failed: linguistic_non_compliant_count={non_compliant} > 0")
            return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
