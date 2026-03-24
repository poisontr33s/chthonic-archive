#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: skill_tensor_cycle.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Single-file authority for the skill tensor cycle and stage compatibility shims.

@SID:           TOOL_SKILL_TENSOR_CYCLE_V1
@Shabti:        CLI Script
@Purpose:       Single-file authority for the skill tensor cycle and stage compatibility shims.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import random
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


def find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for p in [cur, *cur.parents]:
        if (p / "AGENTS.md").exists() and (p / "pyproject.toml").exists():
            return p
    return start.resolve()


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def lane_for_root(root: str) -> str:
    if ".codex/skills" in root:
        return "codex"
    if ".claude/skills" in root:
        return "claude"
    if ".gemini/extensions/chthonic-archive-sync/skills" in root:
        return "gemini"
    return ""


def operator_execution_scope(operator: str, rules: dict | None = None) -> str:
    scopes = (rules or {}).get("operator_execution_scopes", {})
    if operator in scopes:
        return str(scopes[operator])
    if operator == "trainstop-orchestrator":
        return "lane"
    return "skill"


def action_key_parts(cell: dict, rules: dict | None = None) -> list[str]:
    operator = str(cell.get("operator_skill", "unknown"))
    scope = operator_execution_scope(operator, rules)
    target_root = str(cell.get("target_root", ""))
    target_skill = str(cell.get("target_skill", ""))
    target_lane = str(cell.get("target_skill_lane", ""))
    target_flavor = str(cell.get("target_flavor_mode", ""))

    if scope == "lane":
        return [operator, scope, target_lane, "maintenance"]
    if operator == "skill-audit":
        return [operator, scope, target_flavor, target_root, target_skill]
    if operator == "skill-polisher":
        return [operator, scope, "verify", target_flavor, target_root, target_skill]
    if operator == "link-path-guard":
        return [operator, scope, target_root, target_skill]
    return [operator, scope, target_lane, target_flavor, target_root, target_skill]


def action_key_string(cell_or_key: dict | list[str], rules: dict | None = None) -> str:
    parts = action_key_parts(cell_or_key, rules) if isinstance(cell_or_key, dict) else list(cell_or_key)
    return json.dumps(parts, separators=(",", ":"))


def cell_sort_key(cell: dict) -> tuple[str, ...]:
    return (
        str(cell.get("operator_skill", "")),
        str(cell.get("target_root", "")),
        str(cell.get("target_skill", "")),
        str(cell.get("target_skill_lane", "")),
        str(cell.get("target_flavor_mode", "")),
        str(cell.get("executor_flavor", "")),
        str(cell.get("source_root", "")),
    )


def touch_record_for_cell(cell: dict, rules: dict | None = None) -> dict:
    scope = str(cell.get("action_scope") or operator_execution_scope(str(cell.get("operator_skill", "")), rules))
    lane = str(cell.get("target_skill_lane", ""))
    root = str(cell.get("target_root", ""))
    skill = str(cell.get("target_skill", ""))
    if scope == "lane":
        return {"lane": lane, "root": root, "skill": "__lane__maintenance"}
    return {"lane": lane, "root": root, "skill": skill}


def parse_frontmatter(path: Path) -> tuple[dict[str, str], bool]:
    if not path.exists():
        return {}, False
    raw = path.read_text(encoding="utf-8", errors="replace")
    if not raw.startswith("---"):
        return {}, False
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return {}, False
    fm: dict[str, str] = {}
    current_section: str | None = None
    for line in parts[1].splitlines():
        if not line.strip():
            continue
        if not line.startswith(" ") and line.endswith(":"):
            current_section = line.strip()[:-1]
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
    return fm, True


def classify_skill(_name: str, fm: dict[str, str], has_md: bool) -> str:
    if not has_md:
        return "missing"
    desc = fm.get("description", "").lower()
    if "redirect" in desc or "stashed" in desc or "protocol" in desc:
        return "redirect_or_stub"
    return "candidate"


KNOWN_OPERATOR_ADAPTERS = {
    "trainstop-orchestrator": "lane_orchestrator",
    "skill-polisher": "skill_polisher_verify",
    "skill-audit": "skill_audit",
    "link-path-guard": "skill_path_guard",
    "python-header-canon": "python_header_report",
    "mailbox-handoff": "mailbox_link_canon",
}

ADAPTER_DEFAULT_MODES = {
    "lane_orchestrator": "meta",
    "skill_polisher_verify": "mutating",
    "skill_audit": "read_only",
    "skill_path_guard": "mutating",
    "python_header_report": "read_only",
    "mailbox_link_canon": "read_only",
}

ADAPTER_DEFAULT_CAPABILITIES = {
    "lane_orchestrator": {
        "mode": "meta",
        "read": True,
        "mutate": False,
        "cross_lane_mutate": False,
        "self_target": True,
        "recurse": True,
        "requires_artifacts": True,
        "requires_review": True,
    },
    "skill_polisher_verify": {
        "mode": "mutating",
        "read": True,
        "mutate": True,
        "cross_lane_mutate": True,
        "self_target": True,
        "recurse": False,
        "requires_artifacts": True,
        "requires_review": True,
    },
    "skill_audit": {
        "mode": "read_only",
        "read": True,
        "mutate": False,
        "cross_lane_mutate": False,
        "self_target": True,
        "recurse": False,
        "requires_artifacts": True,
        "requires_review": False,
    },
    "skill_path_guard": {
        "mode": "mutating",
        "read": True,
        "mutate": True,
        "cross_lane_mutate": True,
        "self_target": True,
        "recurse": False,
        "requires_artifacts": True,
        "requires_review": True,
    },
    "python_header_report": {
        "mode": "read_only",
        "read": True,
        "mutate": False,
        "cross_lane_mutate": False,
        "self_target": True,
        "recurse": False,
        "requires_artifacts": False,
        "requires_review": False,
    },
    "mailbox_link_canon": {
        "mode": "read_only",
        "read": True,
        "mutate": False,
        "cross_lane_mutate": False,
        "self_target": True,
        "recurse": False,
        "requires_artifacts": False,
        "requires_review": False,
    },
}


def adapter_kind_for_skill(skill_name: str) -> str | None:
    return KNOWN_OPERATOR_ADAPTERS.get(skill_name)


def operator_mode_for_skill(skill_name: str, rules: dict, adapter_kind: str | None = None) -> str:
    operator_modes = rules.get("operator_modes", {})
    if skill_name in operator_modes:
        return str(operator_modes[skill_name])
    resolved_kind = adapter_kind or adapter_kind_for_skill(skill_name)
    if resolved_kind:
        return ADAPTER_DEFAULT_MODES.get(resolved_kind, "meta")
    return "meta"


def adapter_capabilities_for_skill(skill_name: str, adapter_kind: str | None = None) -> dict:
    resolved_kind = adapter_kind or adapter_kind_for_skill(skill_name)
    if not resolved_kind:
        return {}
    return dict(ADAPTER_DEFAULT_CAPABILITIES.get(resolved_kind, {}))


def resolve_adapter_script_path(operator_root: str, operator_skill: str, filename: str) -> str:
    candidates = [
        Path(operator_root) / operator_skill / "scripts" / filename,
        Path(operator_root) / operator_skill / operator_skill / "scripts" / filename,
        Path(".codex/skills") / operator_skill / "scripts" / filename,
        Path(".gemini/extensions/chthonic-archive-sync/skills") / operator_skill / "scripts" / filename,
        Path(".claude/skills") / operator_skill / "scripts" / filename,
        Path(".claude/skills") / operator_skill / operator_skill / "scripts" / filename,
        Path(".gemini/extensions/chthonic-archive-sync/skills") / operator_skill / operator_skill / "scripts" / filename,
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return str(candidates[0])


def role_profile_for_skill(row: dict) -> dict:
    classification = str(row.get("classification", "missing"))
    has_skill_md = bool(row.get("has_skill_md"))
    has_scripts_dir = bool(row.get("has_scripts_dir"))
    adapter_kind = adapter_kind_for_skill(str(row.get("skill", "")))

    operator_role = "blocked"
    operator_reasons: list[str] = []
    target_role = "blocked"
    target_reasons: list[str] = []

    if not has_skill_md or classification == "missing":
        operator_reasons.append("missing_skill_surface")
        target_reasons.append("missing_skill_surface")
    else:
        target_role = "legal"
        if classification == "redirect_or_stub":
            target_role = "degraded"
            target_reasons.append("target_redirect_or_stub")

        if classification == "redirect_or_stub":
            operator_role = "legacy_only"
            operator_reasons.append("operator_redirect_or_stub")
        elif adapter_kind:
            operator_role = "executable"
            operator_reasons.append(f"registered_adapter:{adapter_kind}")
        elif has_scripts_dir:
            operator_role = "analysis_only"
            operator_reasons.append("scripts_present_no_registered_adapter")
        else:
            operator_role = "analysis_only"
            operator_reasons.append("document_only_operator")

    return {
        "adapter_kind": adapter_kind,
        "can_target": target_role != "blocked",
        "can_operator": operator_role != "blocked",
        "operator_role": operator_role,
        "operator_reasons": operator_reasons,
        "target_role": target_role,
        "target_reasons": target_reasons,
    }


def inventory_root(repo_root: Path, lane: str, root_rel: str) -> list[dict]:
    root = repo_root / root_rel
    if not root.exists():
        return []
    rows: list[dict] = []
    for skill_dir in sorted([p for p in root.iterdir() if p.is_dir()], key=lambda p: p.name.lower()):
        skill_md = skill_dir / "SKILL.md"
        fm, has_yaml = parse_frontmatter(skill_md)
        rows.append(
            {
                "lane": lane,
                "root": root_rel,
                "skill": skill_dir.name,
                "path": str(skill_dir.relative_to(repo_root)).replace("\\", "/"),
                "has_skill_md": skill_md.exists(),
                "has_yaml_frontmatter": has_yaml,
                "has_scripts_dir": (skill_dir / "scripts").exists(),
                "has_assets_dir": (skill_dir / "assets").exists(),
                "last_modified": skill_dir.stat().st_mtime,
                "description": fm.get("description"),
                "classification": classify_skill(skill_dir.name, fm, skill_md.exists()),
            }
        )
        rows[-1]["role_profile"] = role_profile_for_skill(rows[-1])
    return rows


def render_inventory_markdown(payload: dict) -> str:
    skills = payload.get("skills", [])
    by_lane: dict[str, int] = {}
    for row in skills:
        by_lane[row["lane"]] = by_lane.get(row["lane"], 0) + 1
    lines = ["# Skill Tensor Inventory", "", f"- Total Skills: `{len(skills)}`", "", "## Per Lane"]
    for lane, count in sorted(by_lane.items()):
        lines.append(f"- `{lane}`: `{count}`")
    return "\n".join(lines) + "\n"


def build_inventory_payload(repo_root: Path) -> dict:
    roots = {
        "codex": ".codex/skills",
        "claude": ".claude/skills",
        "gemini": ".gemini/extensions/chthonic-archive-sync/skills",
    }
    payload = {
        "schema_version": 1,
        "generated_from": str(repo_root).replace("\\", "/"),
        "skills": [],
    }
    for lane, root_rel in roots.items():
        payload["skills"].extend(inventory_root(repo_root, lane, root_rel))
    return payload


@dataclass
class RunCell:
    executor_flavor: str
    operator_flavor: str
    operator_skill: str
    operator_root: str
    source_root: str
    target_root: str
    target_flavor: str
    target_skill: str
    target_skill_lane: str
    target_flavor_mode: str
    action_scope: str
    action_key: list[str]
    adapter_kind: str | None
    legality_status: str
    legality_reasons: list[str]


@dataclass
class ExcludedCell:
    executor_flavor: str
    operator_flavor: str
    operator_skill: str
    target_root: str
    target_flavor: str
    target_skill: str
    target_skill_lane: str
    target_flavor_mode: str
    action_scope: str
    reason: str


@dataclass
class UniverseCell:
    executor_flavor: str
    operator_flavor: str
    operator_root: str
    source_root: str
    operator_skill: str
    operator_classification: str
    operator_role: str
    target_flavor: str
    target_root: str
    target_skill: str
    target_classification: str
    target_role: str
    interpretation_flavor: str
    target_flavor_mode: str
    action_scope: str
    action_key: list[str]
    symbolic_key: list[str]
    adapter_kind: str | None
    execution_kind: str
    legality_status: str
    legality_reasons: list[str]


def compact_skill_entry(row: dict) -> dict:
    profile = dict(row.get("role_profile", {}))
    return {
        "lane": str(row.get("lane", "")),
        "root": str(row.get("root", "")),
        "skill": str(row.get("skill", "")),
        "classification": str(row.get("classification", "missing")),
        "operator_role": str(profile.get("operator_role", "blocked")),
        "target_role": str(profile.get("target_role", "blocked")),
        "adapter_kind": profile.get("adapter_kind"),
    }


def universe_move_dict_from_record(universe: dict, record: list) -> dict:
    executors = universe.get("executors", [])
    interpretations = universe.get("interpretations", [])
    skills = universe.get("skills", [])
    statuses = universe.get("statuses", [])
    execution_kinds = universe.get("execution_kinds", [])
    reasons = universe.get("reasons", [])

    executor_idx, operator_idx, target_idx, interpretation_idx, status_idx, execution_kind_idx, reason_idxs = record
    operator = skills[operator_idx]
    target = skills[target_idx]
    executor_flavor = executors[executor_idx]
    interpretation_flavor = interpretations[interpretation_idx]
    legality_status = statuses[status_idx]
    execution_kind = execution_kinds[execution_kind_idx]
    legality_reasons = [reasons[idx] for idx in reason_idxs]

    move = {
        "executor_flavor": executor_flavor,
        "operator_flavor": operator["lane"],
        "operator_root": operator["root"],
        "source_root": operator["root"],
        "operator_skill": operator["skill"],
        "operator_classification": operator["classification"],
        "operator_role": operator["operator_role"],
        "target_flavor": target["lane"],
        "target_root": target["root"],
        "target_skill": target["skill"],
        "target_classification": target["classification"],
        "target_role": target["target_role"],
        "interpretation_flavor": interpretation_flavor,
        "target_flavor_mode": interpretation_flavor,
        "adapter_kind": operator.get("adapter_kind"),
        "execution_kind": execution_kind,
        "legality_status": legality_status,
        "legality_reasons": legality_reasons,
    }
    move["action_scope"] = operator_execution_scope(move["operator_skill"])
    move["action_key"] = action_key_parts(move)
    move["symbolic_key"] = symbolic_key_parts(executor_flavor, operator, target, interpretation_flavor)
    return move


def iter_universe_moves(universe: dict):
    if universe.get("move_encoding") == "indexed-v1":
        for record in universe.get("moves", []):
            yield universe_move_dict_from_record(universe, record)
        return
    for row in universe.get("moves", []):
        if isinstance(row, dict):
            yield row


def render_universe_markdown(payload: dict) -> str:
    lines = [
        "# Skill Tensor Universe",
        "",
        f"- Move Count: `{payload.get('move_count')}`",
        f"- Legal: `{payload.get('status_counts', {}).get('legal', 0)}`",
        f"- Degraded: `{payload.get('status_counts', {}).get('degraded', 0)}`",
        f"- Blocked: `{payload.get('status_counts', {}).get('blocked', 0)}`",
        "",
        "## Notes",
        "- Universe includes all inventoried skills, not just runnable candidates.",
        "- Legality records symbolic moves, even when execution adapters do not exist.",
    ]
    return "\n".join(lines) + "\n"


def symbolic_key_parts(executor_flavor: str, operator: dict, target: dict, interpretation_flavor: str) -> list[str]:
    return [
        executor_flavor,
        str(operator.get("lane", "")),
        str(operator.get("skill", "")),
        str(target.get("lane", "")),
        str(target.get("skill", "")),
        interpretation_flavor,
    ]


def evaluate_universe_cell(
    executor_flavor: str,
    operator: dict,
    target: dict,
    interpretation_flavor: str,
    rules: dict,
) -> UniverseCell:
    operator_profile = dict(operator.get("role_profile", {}))
    target_profile = dict(target.get("role_profile", {}))
    operator_skill = str(operator.get("skill", ""))
    target_skill = str(target.get("skill", ""))
    operator_flavor = str(operator.get("lane", ""))
    target_flavor = str(target.get("lane", ""))
    operator_root = str(operator.get("root", ""))
    target_root = str(target.get("root", ""))
    action_scope = operator_execution_scope(operator_skill, rules)
    action_seed = {
        "executor_flavor": executor_flavor,
        "operator_flavor": operator_flavor,
        "operator_skill": operator_skill,
        "operator_root": operator_root,
        "target_flavor": target_flavor,
        "target_root": target_root,
        "target_skill": target_skill,
        "target_skill_lane": target_flavor,
        "target_flavor_mode": interpretation_flavor,
    }
    action_key = action_key_parts(action_seed, rules)
    symbolic_key = symbolic_key_parts(executor_flavor, operator, target, interpretation_flavor)
    reasons: list[str] = []
    legality_status = "legal"
    execution_kind = "native"
    adapter_kind = operator_profile.get("adapter_kind")

    if not operator_profile.get("can_operator", False):
        legality_status = "blocked"
        execution_kind = "none"
        reasons.extend(operator_profile.get("operator_reasons", []) or ["operator_not_legal"])
    elif not target_profile.get("can_target", False):
        legality_status = "blocked"
        execution_kind = "none"
        reasons.extend(target_profile.get("target_reasons", []) or ["target_not_legal"])
    else:
        reasons.extend(operator_profile.get("operator_reasons", []))
        reasons.extend(target_profile.get("target_reasons", []))
        if operator_profile.get("operator_role") in {"legacy_only", "analysis_only"}:
            legality_status = "degraded"
            execution_kind = "analysis_only" if adapter_kind is None else "native"
        if target_profile.get("target_role") == "degraded":
            legality_status = "degraded"
        if operator_skill == target_skill and operator_flavor == target_flavor:
            reasons.append("self_target_skill")
            if not rules.get("self_target_rules", {}).get("default_allow_same_skill", True):
                legality_status = "degraded"
        if operator_root == target_root:
            reasons.append("same_root")
            if not rules.get("self_target_rules", {}).get("default_allow_same_root", True):
                legality_status = "degraded"
        flavor_rule = rules.get("operator_target_flavor_rules", {}).get(operator_skill)
        if flavor_rule == "match_target_lane" and interpretation_flavor != target_flavor:
            legality_status = "degraded"
            reasons.append("interpretation_flavor_mismatch")
        if action_scope == "lane":
            reasons.append("lane_scoped_action")
        if adapter_kind is None and legality_status != "blocked":
            execution_kind = "analysis_only"

    if not reasons:
        reasons.append("native_move")

    return UniverseCell(
        executor_flavor=executor_flavor,
        operator_flavor=operator_flavor,
        operator_root=operator_root,
        source_root=operator_root,
        operator_skill=operator_skill,
        operator_classification=str(operator.get("classification", "missing")),
        operator_role=str(operator_profile.get("operator_role", "blocked")),
        target_flavor=target_flavor,
        target_root=target_root,
        target_skill=target_skill,
        target_classification=str(target.get("classification", "missing")),
        target_role=str(target_profile.get("target_role", "blocked")),
        interpretation_flavor=interpretation_flavor,
        target_flavor_mode=interpretation_flavor,
        action_scope=action_scope,
        action_key=action_key,
        symbolic_key=symbolic_key,
        adapter_kind=adapter_kind,
        execution_kind=execution_kind,
        legality_status=legality_status,
        legality_reasons=sorted(set(reasons)),
    )


def build_universe_payload(rules: dict, inventory: dict, rules_source: str, inventory_source: str) -> dict:
    agent_flavors = list(rules["agent_flavors"])
    raw_skills = [row for row in inventory.get("skills", []) if isinstance(row, dict)]
    skills = [compact_skill_entry(row) for row in raw_skills]
    skill_index = {(
        skill["lane"],
        skill["root"],
        skill["skill"],
    ): idx for idx, skill in enumerate(skills)}
    reasons: list[str] = []
    reason_index: dict[str, int] = {}
    statuses = ["legal", "degraded", "blocked"]
    status_index = {name: idx for idx, name in enumerate(statuses)}
    execution_kinds = ["native", "analysis_only", "none"]
    execution_index = {name: idx for idx, name in enumerate(execution_kinds)}
    moves: list[list[object]] = []
    status_counts = {"legal": 0, "degraded": 0, "blocked": 0}
    execution_kind_counts: dict[str, int] = defaultdict(int)
    reason_counts: dict[str, int] = defaultdict(int)

    for executor_flavor in agent_flavors:
        for operator_raw, operator in zip(raw_skills, skills):
            operator_idx = skill_index[(operator["lane"], operator["root"], operator["skill"])]
            for target_raw, target in zip(raw_skills, skills):
                target_idx = skill_index[(target["lane"], target["root"], target["skill"])]
                for interpretation_flavor in agent_flavors:
                    move = evaluate_universe_cell(executor_flavor, operator_raw, target_raw, interpretation_flavor, rules)
                    reason_ids: list[int] = []
                    for reason in move.legality_reasons:
                        if reason not in reason_index:
                            reason_index[reason] = len(reasons)
                            reasons.append(reason)
                        reason_ids.append(reason_index[reason])
                    moves.append(
                        [
                            agent_flavors.index(executor_flavor),
                            operator_idx,
                            target_idx,
                            agent_flavors.index(interpretation_flavor),
                            status_index[move.legality_status],
                            execution_index[move.execution_kind],
                            reason_ids,
                        ]
                    )
                    status_counts[move.legality_status] = status_counts.get(move.legality_status, 0) + 1
                    execution_kind_counts[move.execution_kind] = execution_kind_counts.get(move.execution_kind, 0) + 1
                    for reason in move.legality_reasons:
                        reason_counts[reason] = reason_counts.get(reason, 0) + 1

    return {
        "schema_version": 2,
        "move_encoding": "indexed-v1",
        "rules_source": rules_source,
        "inventory_source": inventory_source,
        "move_count": len(moves),
        "status_counts": status_counts,
        "execution_kind_counts": dict(sorted(execution_kind_counts.items())),
        "reason_counts": dict(sorted(reason_counts.items())),
        "executors": agent_flavors,
        "interpretations": agent_flavors,
        "statuses": statuses,
        "execution_kinds": execution_kinds,
        "reasons": reasons,
        "skills": skills,
        "moves": moves,
    }


def render_legality_markdown(payload: dict) -> str:
    lines = [
        "# Skill Tensor Legality",
        "",
        f"- Legal: `{payload.get('status_counts', {}).get('legal', 0)}`",
        f"- Degraded: `{payload.get('status_counts', {}).get('degraded', 0)}`",
        f"- Blocked: `{payload.get('status_counts', {}).get('blocked', 0)}`",
        "",
        "## Top Reasons",
    ]
    for reason, count in payload.get("reason_counts_top", []):
        lines.append(f"- `{reason}`: `{count}`")
    return "\n".join(lines) + "\n"


def build_legality_payload(universe: dict, universe_source: str) -> dict:
    moves = list(iter_universe_moves(universe))
    degraded = [row for row in moves if row.get("legality_status") == "degraded"]
    blocked = [row for row in moves if row.get("legality_status") == "blocked"]
    reason_counts: dict[str, int] = defaultdict(int)
    for row in degraded + blocked:
        for reason in row.get("legality_reasons", []):
            reason_counts[reason] = reason_counts.get(reason, 0) + 1

    top_reasons = sorted(reason_counts.items(), key=lambda item: (-item[1], item[0]))[:20]
    return {
        "schema_version": 1,
        "universe_source": universe_source,
        "move_count": universe.get("move_count", 0),
        "status_counts": dict(universe.get("status_counts", {})),
        "reason_counts_top": top_reasons,
        "degraded_count": len(degraded),
        "blocked_count": len(blocked),
        "degraded": degraded[:400],
        "blocked": blocked[:400],
    }


def render_pool_markdown(payload: dict) -> str:
    lines = [
        "# Skill Tensor Pool",
        "",
        f"- Pool Size: `{payload.get('pool_size')}`",
        f"- Unique Action Keys: `{payload.get('action_group_count')}`",
        f"- Excluded Size: `{payload.get('excluded_size')}`",
        "",
        "## Notes",
        "- Pool contains legal run-cells only.",
        "- Excluded cells include reasons in the JSON artifact.",
    ]
    return "\n".join(lines) + "\n"


def build_pool_payload(rules: dict, universe: dict, rules_source: str, universe_source: str) -> dict:
    moves = list(iter_universe_moves(universe))
    pool: list[RunCell] = []
    excluded: list[ExcludedCell] = []

    for move in moves:
        action_scope = str(move.get("action_scope", operator_execution_scope(str(move.get("operator_skill", "")), rules)))
        if move.get("execution_kind") == "native":
            pool.append(
                RunCell(
                    executor_flavor=str(move.get("executor_flavor", "")),
                    operator_flavor=str(move.get("operator_flavor", "")),
                    operator_skill=str(move.get("operator_skill", "")),
                    operator_root=str(move.get("operator_root", "")),
                    source_root=str(move.get("source_root", move.get("operator_root", ""))),
                    target_root=str(move.get("target_root", "")),
                    target_flavor=str(move.get("target_flavor", "")),
                    target_skill=str(move.get("target_skill", "")),
                    target_skill_lane=str(move.get("target_flavor", "")),
                    target_flavor_mode=str(move.get("target_flavor_mode", "")),
                    action_scope=action_scope,
                    action_key=list(move.get("action_key", [])),
                    adapter_kind=move.get("adapter_kind"),
                    legality_status=str(move.get("legality_status", "legal")),
                    legality_reasons=list(move.get("legality_reasons", [])),
                )
            )
        else:
            excluded.append(
                ExcludedCell(
                    executor_flavor=str(move.get("executor_flavor", "")),
                    operator_flavor=str(move.get("operator_flavor", "")),
                    operator_skill=str(move.get("operator_skill", "")),
                    target_root=str(move.get("target_root", "")),
                    target_flavor=str(move.get("target_flavor", "")),
                    target_skill=str(move.get("target_skill", "")),
                    target_skill_lane=str(move.get("target_flavor", "")),
                    target_flavor_mode=str(move.get("target_flavor_mode", "")),
                    action_scope=action_scope,
                    reason=";".join(move.get("legality_reasons", [])) or str(move.get("legality_status", "blocked")),
                )
            )

    unique_action_keys = {json.dumps(cell.action_key, separators=(",", ":")) for cell in pool}
    return {
        "schema_version": 2,
        "rules_source": rules_source,
        "universe_source": universe_source,
        "pool_size": len(pool),
        "action_group_count": len(unique_action_keys),
        "excluded_size": len(excluded),
        "pool": [asdict(cell) for cell in pool],
        "excluded": [asdict(cell) for cell in excluded],
    }


def render_weights_markdown(payload: dict) -> str:
    lines = [
        "# Skill Tensor Weights",
        "",
        f"- Pool Size: `{payload.get('pool_size')}`",
        f"- Ledger Entries: `{payload.get('recent_entry_count')}`",
        f"- Pruned Exact Cells: `{len(payload.get('pruned_exact_cells', []))}`",
        f"- Pruned Action Keys: `{len(payload.get('pruned_action_keys', []))}`",
        "",
        "## Operator Adjustments",
    ]
    for op, val in sorted(payload.get("per_operator_weight_adjustments", {}).items()):
        lines.append(f"- `{op}`: `{val}`")
    return "\n".join(lines) + "\n"


def build_weights_payload(
    rules: dict,
    inventory: dict,
    pool: dict,
    ledger: dict,
    rules_source: str,
    inventory_source: str,
    pool_source: str,
    ledger_source: str,
) -> dict:
    skills = inventory.get("skills", [])
    pool_cells = pool.get("pool", [])
    runs = ledger.get("runs", [])

    recent_targets = set()
    failed_targets = set()
    recent_success_cells = set()
    recent_success_action_keys = set()
    operator_counts: dict[str, int] = {}
    success_window = int(rules.get("history_pruning", {}).get("recent_success_window", 5))
    for entry in runs:
        for touched in entry.get("touched", []):
            recent_targets.add((touched.get("root"), touched.get("skill")))
        for op in entry.get("operators", []):
            if op:
                operator_counts[op] = operator_counts.get(op, 0) + 1
        if entry.get("execution_status") in {"failed", "blocked"}:
            for touched in entry.get("touched", []):
                failed_targets.add((touched.get("root"), touched.get("skill")))
        if entry.get("execution_status") == "passed":
            for ident in entry.get("sampled_exact_cells", []):
                if isinstance(ident, list) and len(ident) == 6:
                    recent_success_cells.add(tuple(ident))
            for action_key in entry.get("sampled_action_keys", []):
                if isinstance(action_key, list):
                    recent_success_action_keys.add(tuple(action_key))

    per_skill = {}
    for row in skills:
        lane = row["lane"]
        root = row["root"]
        skill = row["skill"]
        stale_bonus = 1.0
        if row.get("classification") == "candidate":
            stale_bonus += 0.25
        if (root, skill) in recent_targets:
            stale_bonus -= 0.2
        if (root, skill) in failed_targets:
            stale_bonus += 0.35
        if skill in rules.get("lane_specific_targets", {}).get(lane, []):
            stale_bonus += 0.15
        per_skill[f"{root}::{skill}"] = round(stale_bonus, 4)

    per_operator = {}
    total_operator_hits = sum(operator_counts.values()) or 1
    for op in sorted({cell.get("operator_skill") for cell in pool_cells if isinstance(cell, dict)}):
        count = operator_counts.get(op, 0)
        ratio = count / total_operator_hits
        adj = 1.0 - min(0.25, ratio * 0.5)
        per_operator[op] = round(adj, 4)

    pruned_exact_cells = []
    if rules.get("history_pruning", {}).get("prune_exact_success_cells", False):
        for ident in list(recent_success_cells)[: success_window * 8]:
            pruned_exact_cells.append(list(ident))

    pruned_action_keys = [list(action_key) for action_key in sorted(recent_success_action_keys)]

    return {
        "schema_version": 2,
        "sources": {
            "rules": rules_source,
            "inventory": inventory_source,
            "pool": pool_source,
            "ledger": ledger_source,
        },
        "pool_size": pool.get("pool_size"),
        "recent_entry_count": len(runs),
        "per_skill_weight_adjustments": per_skill,
        "per_operator_weight_adjustments": per_operator,
        "pruned_exact_cells": pruned_exact_cells,
        "pruned_action_keys": pruned_action_keys,
    }


def deterministic_seed(seed_text: str) -> int:
    digest = hashlib.sha256(seed_text.encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def weight_cell(cell: dict, rules: dict, weights: dict | None = None) -> tuple[float, list[str]]:
    reasons: list[str] = []
    weight = 1.0

    mode = operator_mode_for_skill(cell["operator_skill"], rules, cell.get("adapter_kind"))
    if mode == "mutating":
        weight *= 1.4
        reasons.append("mutating_operator:+0.4x")
    elif mode == "read_only":
        weight *= 1.1
        reasons.append("read_only_operator:+0.1x")
    else:
        weight *= 1.2
        reasons.append("meta_operator:+0.2x")

    if cell["executor_flavor"] != cell["target_skill_lane"]:
        weight *= 1.5
        reasons.append("cross_lane:+0.5x")
    else:
        weight *= 1.1
        reasons.append("self_lane:+0.1x")

    if cell["target_flavor_mode"] != cell["target_skill_lane"]:
        weight *= 1.25
        reasons.append("cross_flavor_interp:+0.25x")

    if cell["operator_skill"] == "trainstop-orchestrator":
        weight *= 0.85
        reasons.append("meta_heavy_penalty:-0.15x")

    if weights:
        key = f"{cell['target_root']}::{cell['target_skill']}"
        delta = weights.get("per_skill_weight_adjustments", {}).get(key)
        if isinstance(delta, (int, float)):
            weight *= float(delta)
            reasons.append(f"adaptive_weight:{delta}x")
        op_delta = weights.get("per_operator_weight_adjustments", {}).get(cell["operator_skill"])
        if isinstance(op_delta, (int, float)):
            weight *= float(op_delta)
            reasons.append(f"operator_weight:{op_delta}x")

    return weight, reasons


def cell_identity(cell: dict, rules: dict) -> tuple[str, ...]:
    return tuple(cell.get("action_key") or action_key_parts(cell, rules))


def target_identity(cell: dict, rules: dict) -> tuple[str, str]:
    action_scope = str(cell.get("action_scope") or operator_execution_scope(cell["operator_skill"], rules))
    if action_scope == "lane":
        return (cell["target_root"], "__lane__maintenance")
    return (cell["target_root"], cell["target_skill"])


def transition_allowed(candidate: dict, previous: dict | None, chain: list[dict], rules: dict) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    tr = rules.get("transition_rules", {})

    if tr.get("disallow_duplicate_cells_in_chain", False):
        seen = {
            tuple(step.get("action_key") or step["cell"].get("action_key") or action_key_parts(step["cell"], rules))
            for step in chain
        }
        if cell_identity(candidate, rules) in seen:
            return False, ["duplicate_cell_blocked"]

    if tr.get("disallow_same_target_skill_repeat", False):
        seen_skills = {target_identity(step["cell"], rules) for step in chain}
        if target_identity(candidate, rules) in seen_skills:
            return False, ["repeated_target_skill_blocked"]

    if previous and tr.get("disallow_same_operator_consecutive", False):
        if candidate["operator_skill"] == previous["cell"]["operator_skill"]:
            return False, ["same_operator_consecutive_blocked"]

    return True, reasons


def build_pruned_action_keys(weights: dict | None, rules: dict) -> set[str]:
    if not weights:
        return set()
    pruned = set()
    for parts in weights.get("pruned_action_keys", []):
        if isinstance(parts, list):
            pruned.add(action_key_string(parts))
    for ident in weights.get("pruned_exact_cells", []):
        if not isinstance(ident, list) or len(ident) != 6:
            continue
        cell = {
            "executor_flavor": ident[0],
            "operator_skill": ident[1],
            "source_root": ident[2],
            "target_root": ident[3],
            "target_skill": ident[4],
            "target_flavor_mode": ident[5],
            "target_skill_lane": lane_for_root(ident[3]),
        }
        pruned.add(action_key_string(cell, rules))
    return pruned


def transition_weight(candidate: dict, previous: dict | None, rules: dict) -> tuple[float, list[str]]:
    if previous is None:
        return 1.0, ["initial_step"]
    tr = rules.get("transition_rules", {})
    weight = 1.0
    reasons: list[str] = []
    if tr.get("prefer_target_lane_to_next_executor", False) and previous["cell"]["target_skill_lane"] == candidate["executor_flavor"]:
        weight *= 1.8
        reasons.append("handoff_continuity:+0.8x")
    if tr.get("prefer_root_continuity", False) and previous["cell"]["target_root"] == candidate["source_root"]:
        weight *= 1.25
        reasons.append("root_continuity:+0.25x")
    return weight, reasons


def transition_artifact(candidate: dict, previous: dict | None, chain: list[dict], rules: dict, filtered_out: list[str]) -> dict:
    allowed, _ = transition_allowed(candidate, previous, chain, rules)
    weight_mult, weight_reasons = transition_weight(candidate, previous, rules)
    return {
        "allowed": allowed,
        "previous_target_lane": None if previous is None else previous["cell"]["target_skill_lane"],
        "previous_operator": None if previous is None else previous["cell"]["operator_skill"],
        "transition_weight_multiplier": round(weight_mult, 6),
        "transition_weight_reasons": weight_reasons,
        "filtered_out_rules": filtered_out,
    }


def summarize_chain(chain: list[dict]) -> dict:
    if not chain:
        return {
            "diversity_score": 0.0,
            "cross_lane_coverage": 0.0,
            "operator_spread": 0.0,
            "target_spread": 0.0,
        }

    executors = {step["cell"]["executor_flavor"] for step in chain}
    operator_skills = {step["cell"]["operator_skill"] for step in chain}
    targets = {(step["cell"]["target_root"], step["cell"]["target_skill"]) for step in chain}
    action_keys = {
        json.dumps(step.get("action_key") or step["cell"].get("action_key") or action_key_parts(step["cell"]), separators=(",", ":"))
        for step in chain
    }
    action_scopes = {
        step.get("action_scope") or step["cell"].get("action_scope") or operator_execution_scope(step["cell"]["operator_skill"])
        for step in chain
    }
    cross_lane_steps = [step for step in chain if step["cell"]["executor_flavor"] != step["cell"]["target_skill_lane"]]
    diversity_score = round((len(executors) + len(operator_skills) + len(targets)) / (3 + 4 + len(chain)), 4)
    cross_lane_coverage = round(len(cross_lane_steps) / len(chain), 4)
    operator_spread = round(len(operator_skills) / len(chain), 4)
    target_spread = round(len(targets) / len(chain), 4)
    return {
        "diversity_score": diversity_score,
        "cross_lane_coverage": cross_lane_coverage,
        "operator_spread": operator_spread,
        "target_spread": target_spread,
        "executor_flavors_seen": sorted(executors),
        "operator_skills_seen": sorted(operator_skills),
        "distinct_targets_seen": len(targets),
        "distinct_action_keys_seen": len(action_keys),
        "action_scopes_seen": sorted(action_scopes),
    }


def meets_diversity_minimums(summary: dict, rules: dict) -> bool:
    mins = rules.get("diversity_minimums", {})
    if len(summary.get("executor_flavors_seen", [])) < mins.get("min_executor_flavors", 1):
        return False
    if len(summary.get("operator_skills_seen", [])) < mins.get("min_operator_skills", 1):
        return False
    if summary.get("cross_lane_coverage", 0.0) < mins.get("min_cross_lane_coverage", 0.0):
        return False
    return True


def render_roulette_markdown(payload: dict) -> str:
    summary = payload.get("summary", {})
    lines = [
        "# Skill Tensor Roulette",
        "",
        f"- Seed: `{payload.get('seed_text')}`",
        f"- Seed Value: `{payload.get('seed_value')}`",
        f"- Chain Length: `{payload.get('chain_length_actual')}`",
        f"- Pool Size: `{payload.get('pool_size')}`",
        f"- Diversity Score: `{summary.get('diversity_score')}`",
        f"- Cross-Lane Coverage: `{summary.get('cross_lane_coverage')}`",
        f"- Distinct Action Keys: `{summary.get('distinct_action_keys_seen')}`",
        "",
        "## Steps",
    ]
    for step in payload.get("selected", []):
        cell = step["cell"]
        lines += [
            f"### Step {step['step']}",
            f"- Executor: `{cell['executor_flavor']}`",
            f"- Operator: `{cell['operator_skill']}`",
            f"- Target: `{cell['target_root']}::{cell['target_skill']}`",
            f"- Flavor: `{cell['target_flavor_mode']}`",
            f"- Action Scope: `{step.get('action_scope')}`",
            f"- Action Key: `{step.get('action_key')}`",
            f"- Equivalent Cells: `{step.get('equivalent_cell_count')}`",
            f"- Weight: `{step['weight']}`",
            "",
        ]
    return "\n".join(lines) + "\n"


def merge_count_dict(dst: dict[str, int], src: dict[str, int]) -> None:
    for key, value in src.items():
        dst[key] = dst.get(key, 0) + value


def evaluate_action_group(
    cells: list[dict],
    previous: dict | None,
    chain: list[dict],
    rules: dict,
    weights: dict | None,
) -> tuple[dict | None, dict[str, int]]:
    filtered: dict[str, int] = {}
    candidates: list[tuple[dict, float, list[str]]] = []
    for cell in cells:
        allowed, blocked_reasons = transition_allowed(cell, previous, chain, rules)
        if not allowed:
            for reason in blocked_reasons:
                filtered[reason] = filtered.get(reason, 0) + 1
            continue
        base_weight, base_reasons = weight_cell(cell, rules, weights)
        trans_weight, trans_reasons = transition_weight(cell, previous, rules)
        candidates.append((cell, base_weight * trans_weight, base_reasons + trans_reasons))
    if not candidates:
        return None, filtered
    candidates.sort(key=lambda item: (-item[1], cell_sort_key(item[0])))
    representative, _, representative_reasons = candidates[0]
    group_weight = sum(weight for _, weight, _ in candidates) / len(candidates)
    target_sample = sorted({f"{cell['target_root']}::{cell['target_skill']}" for cell in cells})[:6]
    return ({
        "representative_cell": representative,
        "group_weight": group_weight,
        "representative_reasons": representative_reasons,
        "equivalent_cell_count": len(cells),
        "available_variant_count": len(candidates),
        "equivalent_target_sample": target_sample,
    }, filtered)


def sample_chain(pool: list[dict], rules: dict, weights: dict | None, rng: random.Random, chain_length: int) -> list[dict]:
    action_groups: dict[str, list[dict]] = defaultdict(list)
    for cell in pool:
        key = action_key_string(cell.get("action_key") or cell, rules)
        action_groups[key].append(cell)

    pruned_action_keys = build_pruned_action_keys(weights, rules)
    chain: list[dict] = []
    previous: dict | None = None
    for step_index in range(chain_length):
        available: list[tuple[dict, float, list[str], list[str], dict]] = []
        filtered_summary: dict[str, int] = {}
        for action_key_json, group_cells in action_groups.items():
            if action_key_json in pruned_action_keys:
                filtered_summary["history_pruned_action"] = filtered_summary.get("history_pruned_action", 0) + 1
                continue
            group_result, group_filtered = evaluate_action_group(group_cells, previous, chain, rules, weights)
            if group_result is None:
                merge_count_dict(filtered_summary, group_filtered)
                continue
            representative = group_result["representative_cell"]
            available.append((
                representative,
                group_result["group_weight"],
                group_result["representative_reasons"] + [f"action_group_size:{group_result['equivalent_cell_count']}"],
                json.loads(action_key_json),
                group_result,
            ))
        if not available:
            break
        total = sum(weight for _, weight, _, _, _ in available)
        pick = rng.uniform(0, total)
        upto = 0.0
        chosen_index = 0
        for i, (_, weight, _, _, _) in enumerate(available):
            upto += weight
            if upto >= pick:
                chosen_index = i
                break
        cell, weight, reasons, action_key, group_result = available[chosen_index]
        chain.append(
            {
                "step": step_index + 1,
                "cell": cell,
                "action_key": action_key,
                "action_scope": cell.get("action_scope") or operator_execution_scope(cell["operator_skill"], rules),
                "equivalent_cell_count": group_result["equivalent_cell_count"],
                "available_variant_count": group_result["available_variant_count"],
                "equivalent_target_sample": group_result["equivalent_target_sample"],
                "weight": round(weight, 6),
                "reasons": reasons,
                "transition": transition_artifact(cell, previous, chain, rules, [f"{k}:{v}" for k, v in sorted(filtered_summary.items())]),
            }
        )
        previous = chain[-1]
    return chain


def build_roulette_payload(
    rules: dict,
    pool_payload: dict,
    weights: dict | None,
    seed_text: str,
    chain_length: int,
    weights_source: str | None,
) -> dict:
    pool = list(pool_payload.get("pool", []))
    seed_value = deterministic_seed(seed_text)
    rng = random.Random(seed_value)
    chain: list[dict] = []
    for _ in range(12):
        chain = sample_chain(pool, rules, weights, rng, chain_length)
        if meets_diversity_minimums(summarize_chain(chain), rules):
            break
    summary = summarize_chain(chain)
    return {
        "schema_version": 2,
        "seed_text": seed_text,
        "seed_value": seed_value,
        "chain_length_requested": chain_length,
        "chain_length_actual": len(chain),
        "pool_size": pool_payload.get("pool_size"),
        "action_group_count": pool_payload.get("action_group_count"),
        "weights_source": weights_source if weights is not None else None,
        "selected": chain,
        "summary": summary,
    }


def command_for_step(cell: dict) -> list[str]:
    operator = cell["operator_skill"]
    operator_root = cell.get("operator_root") or cell.get("source_root") or ""
    target_root = cell["target_root"]
    flavor = cell["target_flavor_mode"]
    target_skill = cell["target_skill"]
    skill_dir = str(Path(target_root) / target_skill)

    if operator == "skill-audit":
        return ["uv", "run", "scripts/skill_audit.py", "--flavor", flavor, "--root", target_root, "--skill", target_skill]
    if operator == "skill-polisher":
        target_flavor = flavor if flavor in {"codex", "claude"} else "auto"
        return ["uv", "run", resolve_adapter_script_path(operator_root, operator, "polish_skill.py"), skill_dir, "--mode", "verify", "--target-flavor", target_flavor, "--no-require-assets"]
    if operator == "link-path-guard":
        return ["uv", "run", "scripts/skill_path_guard.py", str(Path(skill_dir) / "SKILL.md")]
    if operator == "trainstop-orchestrator":
        return ["uv", "run", resolve_adapter_script_path(operator_root, operator, "orchestrate.py"), "--target", cell["target_skill_lane"], "--lane", "maintenance"]
    if operator == "python-header-canon":
        return ["uv", "run", resolve_adapter_script_path(operator_root, operator, "python_header_canon.py"), "--report-only", skill_dir]
    if operator == "mailbox-handoff":
        return ["uv", "run", resolve_adapter_script_path(operator_root, operator, "mailbox_check.py"), "--mode", "link-canon", "--link-canon-file", str(Path(skill_dir) / "SKILL.md"), "--link-canon-no-fail"]
    return ["echo", f"NO_COMMAND_MAPPING:{operator}"]


def expected_artifacts(cell: dict) -> list[str]:
    operator = cell["operator_skill"]
    if operator == "link-path-guard":
        return ["logs/skill_path_guard.log"]
    if operator == "trainstop-orchestrator":
        return ["codex/mailbox/TRAINSTOP_ORCHESTRATOR_LATEST.json"]
    return []


def expected_artifact_class(cell: dict) -> str:
    operator = cell["operator_skill"]
    if operator == "skill-audit":
        return "machine_report"
    if operator == "skill-polisher":
        return "verification_report"
    if operator == "link-path-guard":
        return "log"
    if operator == "trainstop-orchestrator":
        return "orchestration_report"
    if operator == "python-header-canon":
        return "header_report"
    if operator == "mailbox-handoff":
        return "link_report"
    return "unspecified"


def safety_class(cell: dict, rules: dict) -> str:
    mode = operator_mode_for_skill(cell["operator_skill"], rules, cell.get("adapter_kind"))
    if mode == "read_only":
        return "read_only"
    if mode == "mutating":
        if cell["executor_flavor"] == cell["target_skill_lane"]:
            return "local_mutation"
        return "cross_lane_mutation"
    return "meta_orchestration"


def stop_condition(step: dict) -> str:
    safety = step["safety_class"]
    if safety in {"cross_lane_mutation", "meta_orchestration"}:
        return "stop_on_nonzero_or_missing_artifact"
    return "stop_on_nonzero"


def capability_for(cell: dict, capabilities: dict) -> dict:
    configured = capabilities.get("operators", {}).get(cell["operator_skill"])
    if configured:
        return configured
    return adapter_capabilities_for_skill(cell["operator_skill"], cell.get("adapter_kind"))


def render_plan_markdown(payload: dict) -> str:
    lines = [
        "# Skill Tensor Plan",
        "",
        f"- Seed: `{payload.get('seed_text')}`",
        f"- Seed Value: `{payload.get('seed_value')}`",
        f"- Chain Length: `{payload.get('chain_length')}`",
        "",
        "## Steps",
    ]
    for step in payload.get("steps", []):
        cell = step["cell"]
        lines += [
            f"### Step {step['step']}",
            f"- Executor: `{cell['executor_flavor']}`",
            f"- Operator: `{cell['operator_skill']}`",
            f"- Target: `{cell['target_root']}::{cell['target_skill']}`",
            f"- Flavor: `{cell['target_flavor_mode']}`",
            f"- Action Scope: `{step['action_scope']}`",
            f"- Action Key: `{step['action_key']}`",
            f"- Safety: `{step['safety_class']}`",
            f"- Artifact Class: `{step['expected_artifact_class']}`",
            f"- Command: `{' '.join(step['command'])}`",
            "",
        ]
    return "\n".join(lines) + "\n"


def build_plan_payload(sampled: dict, rules: dict, capabilities: dict, input_source: str, capabilities_source: str) -> dict:
    plan_steps = []
    for selected in sampled.get("selected", []):
        cell = selected["cell"]
        step_plan = {
            "step": selected["step"],
            "cell": cell,
            "action_key": selected.get("action_key", cell.get("action_key")),
            "action_scope": selected.get("action_scope", cell.get("action_scope")),
            "equivalent_cell_count": selected.get("equivalent_cell_count", 1),
            "available_variant_count": selected.get("available_variant_count", 1),
            "equivalent_target_sample": selected.get("equivalent_target_sample", []),
            "command": command_for_step(cell),
            "expected_artifacts": expected_artifacts(cell),
            "expected_artifact_class": expected_artifact_class(cell),
            "operator_mode": rules.get("operator_modes", {}).get(cell["operator_skill"], "meta"),
            "operator_capabilities": capability_for(cell, capabilities),
            "safety_class": safety_class(cell, rules),
            "weight": selected.get("weight"),
            "weight_reasons": selected.get("reasons", []),
            "transition": selected.get("transition", {}),
        }
        step_plan["stop_condition"] = stop_condition(step_plan)
        plan_steps.append(step_plan)
    return {
        "schema_version": 2,
        "roulette_source": input_source,
        "capabilities_source": capabilities_source,
        "seed_text": sampled.get("seed_text"),
        "seed_value": sampled.get("seed_value"),
        "chain_length": sampled.get("chain_length_actual"),
        "steps": plan_steps,
    }


def render_ledger_markdown(ledger: dict) -> str:
    runs = ledger.get("runs", [])
    latest = runs[-1] if runs else {}
    lines = [
        "# Skill Tensor Ledger",
        "",
        f"- Runs: `{len(runs)}`",
        f"- Latest Status: `{latest.get('execution_status')}`",
        f"- Latest Seed: `{latest.get('seed_text')}`",
        "",
    ]
    return "\n".join(lines) + "\n"


def compact_sampled_exact_cell(cell: dict) -> list[str]:
    return [
        str(cell.get("executor_flavor", "")),
        str(cell.get("operator_skill", "")),
        str(cell.get("source_root", cell.get("operator_root", ""))),
        str(cell.get("target_root", "")),
        str(cell.get("target_skill", "")),
        str(cell.get("target_flavor_mode", "")),
    ]


def build_compact_run_record(roulette: dict, plan: dict, rules: dict, execution_status: str = "planned") -> dict:
    sampled_steps = roulette.get("selected", [])
    operators = sorted(
        {
            str(step.get("cell", {}).get("operator_skill", ""))
            for step in sampled_steps
            if step.get("cell", {}).get("operator_skill")
        }
    )
    touched = [touch_record_for_cell(step["cell"], rules) for step in plan.get("steps", [])]
    return {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "seed_text": roulette.get("seed_text"),
        "seed_value": roulette.get("seed_value"),
        "chain_length": roulette.get("chain_length_actual"),
        "summary": roulette.get("summary", {}),
        "operators": operators,
        "sampled_action_keys": [
            step.get("action_key") or step.get("cell", {}).get("action_key") or action_key_parts(step.get("cell", {}), rules)
            for step in sampled_steps
        ],
        "sampled_exact_cells": [
            compact_sampled_exact_cell(step.get("cell", {}))
            for step in sampled_steps
        ],
        "touched": touched,
        "execution_status": execution_status,
        "failure_classes": [],
        "execution_results": [],
    }


def ledger_history_limit(rules: dict) -> int:
    success_window = int(rules.get("history_pruning", {}).get("recent_success_window", 5))
    return max(12, success_window * 3)


def normalize_ledger(ledger: dict, rules: dict) -> dict:
    if ledger.get("ledger_mode") == "bounded-history-v1":
        runs = list(ledger.get("runs", []))
    else:
        runs = []
        for entry in ledger.get("entries", []):
            run = {
                "recorded_at": entry.get("recorded_at"),
                "seed_text": entry.get("seed_text"),
                "seed_value": entry.get("seed_value"),
                "chain_length": entry.get("chain_length"),
                "summary": entry.get("summary", {}),
                "operators": sorted(
                    {
                        str(step.get("cell", {}).get("operator_skill", ""))
                        for step in entry.get("sampled_steps", [])
                        if step.get("cell", {}).get("operator_skill")
                    }
                ),
                "sampled_action_keys": [
                    step.get("action_key") or step.get("cell", {}).get("action_key") or action_key_parts(step.get("cell", {}), rules)
                    for step in entry.get("sampled_steps", [])
                ],
                "sampled_exact_cells": [
                    compact_sampled_exact_cell(step.get("cell", {}))
                    for step in entry.get("sampled_steps", [])
                ],
                "touched": list(entry.get("touched", [])),
                "execution_status": entry.get("execution_status", "unknown"),
                "failure_classes": list(entry.get("failure_classes", [])),
                "execution_results": [
                    {
                        "step": result.get("step"),
                        "status": result.get("status"),
                        "failure_kind": result.get("failure_kind"),
                        "rc": result.get("rc"),
                    }
                    for result in entry.get("execution_results", [])
                ],
            }
            runs.append(run)

    max_runs = ledger_history_limit(rules)
    runs = runs[-max_runs:]
    return {
        "schema_version": 3,
        "ledger_mode": "bounded-history-v1",
        "max_runs": max_runs,
        "runs": runs,
    }


def ensure_bootstrap_ledger(repo_root: Path, ledger_rel: str) -> tuple[dict, dict]:
    ledger_path = repo_root / ledger_rel
    rules = load_json(repo_root / "config/skill_tensor_rules.json")
    if ledger_path.exists():
        ledger = normalize_ledger(load_json(ledger_path), rules)
        write_json(ledger_path, ledger)
        write_text(ledger_path.with_suffix(".md"), render_ledger_markdown(ledger))
        return ledger, {
            "ledger_path": ledger_rel,
            "ledger_existed": True,
            "ledger_initialized": False,
            "entries_before_run": len(ledger.get("runs", [])),
        }
    payload = {
        "schema_version": 3,
        "ledger_mode": "bounded-history-v1",
        "max_runs": ledger_history_limit(rules),
        "runs": [],
    }
    write_json(ledger_path, payload)
    write_text(ledger_path.with_suffix(".md"), render_ledger_markdown(payload))
    return payload, {
        "ledger_path": ledger_rel,
        "ledger_existed": False,
        "ledger_initialized": True,
        "entries_before_run": 0,
    }


def append_ledger_entry(ledger: dict, roulette: dict, plan: dict, rules: dict) -> tuple[dict, dict]:
    ledger = normalize_ledger(ledger, rules)
    entry = build_compact_run_record(roulette, plan, rules, execution_status="planned")
    ledger.setdefault("runs", []).append(entry)
    ledger["runs"] = ledger["runs"][-ledger.get("max_runs", ledger_history_limit(rules)):]
    return ledger, entry


def capabilities_allow(step: dict) -> tuple[bool, list[str]]:
    caps = step.get("operator_capabilities", {})
    reasons: list[str] = []
    safety = step.get("safety_class")
    if safety == "read_only" and not caps.get("read", False):
        reasons.append("missing_read_capability")
    if safety == "local_mutation" and not caps.get("mutate", False):
        reasons.append("missing_mutate_capability")
    if safety == "cross_lane_mutation" and not caps.get("cross_lane_mutate", False):
        reasons.append("missing_cross_lane_mutate_capability")
    if safety == "meta_orchestration" and not caps.get("recurse", False):
        reasons.append("missing_recurse_capability")
    return len(reasons) == 0, reasons


def existing_artifacts(expected_artifacts: list[str], repo_root: Path) -> tuple[list[str], list[str]]:
    present: list[str] = []
    missing: list[str] = []
    for artifact in expected_artifacts:
        p = Path(artifact)
        full = p if p.is_absolute() else (repo_root / p)
        if full.exists():
            present.append(artifact)
        else:
            missing.append(artifact)
    return present, missing


def classify_failure(result: dict) -> str | None:
    if result.get("status") == "blocked":
        return "capability_block"
    if result.get("status") != "failed":
        return None
    if result.get("missing_artifacts"):
        return "missing_artifact"
    command = " ".join(result.get("command", []))
    if "trainstop-orchestrator/scripts/orchestrate.py" in command:
        return "trainstop_gate_failure"
    if "skill_path_guard.py" in command:
        return "path_guard_failure"
    if "skill_audit.py" in command:
        return "skill_audit_failure"
    if "polish_skill.py" in command:
        return "skill_polisher_failure"
    return "generic_failure"


def render_execution_markdown(payload: dict) -> str:
    lines = ["# Skill Tensor Execution", "", f"- Overall Status: `{payload.get('overall_status')}`", "", "## Steps"]
    for result in payload.get("results", []):
        lines += [
            f"### Step {result.get('step')}",
            f"- Status: `{result.get('status')}`",
            f"- Failure Kind: `{result.get('failure_kind')}`",
            f"- RC: `{result.get('rc')}`",
            f"- Seconds: `{result.get('seconds')}`",
            "",
        ]
    return "\n".join(lines) + "\n"


def execute_plan(plan: dict, repo_root: Path) -> dict:
    results = []
    overall_status = "passed"
    for step in plan.get("steps", []):
        allowed, deny_reasons = capabilities_allow(step)
        if not allowed:
            result = {
                "step": step.get("step"),
                "command": step.get("command", []),
                "rc": None,
                "seconds": 0.0,
                "stdout_tail": "",
                "stderr_tail": "",
                "expected_artifacts": step.get("expected_artifacts", []),
                "present_artifacts": [],
                "missing_artifacts": step.get("expected_artifacts", []),
                "stop_condition": step.get("stop_condition"),
                "status": "blocked",
                "blocked_by": deny_reasons,
            }
            result["failure_kind"] = classify_failure(result)
            results.append(result)
            overall_status = "blocked"
            break

        command = step.get("command", [])
        t0 = time.time()
        proc = subprocess.run(
            command,
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        dt = time.time() - t0
        expected = step.get("expected_artifacts", [])
        present, missing = existing_artifacts(expected, repo_root)
        status = "passed" if proc.returncode == 0 else "failed"
        if status == "passed" and expected and step.get("stop_condition") == "stop_on_nonzero_or_missing_artifact" and missing:
            status = "failed"
        result = {
            "step": step.get("step"),
            "command": command,
            "rc": proc.returncode,
            "seconds": round(dt, 3),
            "stdout_tail": "\n".join((proc.stdout or "").splitlines()[-20:]),
            "stderr_tail": "\n".join((proc.stderr or "").splitlines()[-20:]),
            "expected_artifacts": expected,
            "present_artifacts": present,
            "missing_artifacts": missing,
            "stop_condition": step.get("stop_condition"),
            "status": status,
        }
        result["failure_kind"] = classify_failure(result)
        results.append(result)
        if result["status"] != "passed":
            overall_status = "failed"
            break

    return {
        "schema_version": 1,
        "plan_source": "codex/mailbox/SKILL_TENSOR_PLAN_LATEST.json",
        "overall_status": overall_status,
        "results": results,
    }


def ensure_current_cycle_entry(ledger: dict, roulette: dict, plan: dict, rules: dict) -> dict:
    ledger = normalize_ledger(ledger, rules)
    runs = ledger.setdefault("runs", [])
    if not runs:
        latest = build_compact_run_record(roulette, plan, rules, execution_status="planned")
        runs.append(latest)
        return latest
    latest = runs[-1]
    latest_actions = latest.get("sampled_action_keys", [])
    current_actions = [
        step.get("action_key") or step.get("cell", {}).get("action_key") or action_key_parts(step.get("cell", {}), rules)
        for step in roulette.get("selected", [])
    ]
    if latest.get("seed_value") != roulette.get("seed_value") or latest_actions != current_actions:
        latest = build_compact_run_record(roulette, plan, rules, execution_status="planned")
        runs.append(latest)
        runs[:] = runs[-ledger.get("max_runs", ledger_history_limit(rules)):]
        return latest
    latest.update(build_compact_run_record(roulette, plan, rules, execution_status=latest.get("execution_status", "planned")))
    return latest


def apply_feedback(ledger: dict, execution: dict, roulette: dict, plan: dict, rules: dict) -> dict:
    ledger = normalize_ledger(ledger, rules)
    latest = ensure_current_cycle_entry(ledger, roulette, plan, rules)
    latest["execution_status"] = execution.get("overall_status", "unknown")
    failure_classes = []
    for result in execution.get("results", []):
        if result.get("status") != "passed":
            kind = result.get("failure_kind") or "generic_failure"
            failure_classes.append(
                {
                    "step": result.get("step"),
                    "kind": kind,
                    "status": result.get("status"),
                    "command": result.get("command"),
                    "rc": result.get("rc"),
                }
            )
    latest["failure_classes"] = failure_classes
    latest["execution_results"] = [
        {
            "step": result.get("step"),
            "status": result.get("status"),
            "failure_kind": result.get("failure_kind"),
            "rc": result.get("rc"),
        }
        for result in execution.get("results", [])
    ]
    return ledger


def exists(repo_root: Path, rel: str) -> bool:
    return (repo_root / rel).exists()


def load_cycle_sections(repo_root: Path) -> dict:
    cycle_path = repo_root / "codex/mailbox/SKILL_TENSOR_CYCLE_LATEST.json"
    if not cycle_path.exists():
        return {}
    cycle = load_json(cycle_path)
    sections = cycle.get("sections")
    return sections if isinstance(sections, dict) else {}


def section_value(section: dict, key: str, fallback=None):
    if key in section:
        return section.get(key)
    return fallback


def phase_status(repo_root: Path) -> dict[str, str]:
    cycle_sections = load_cycle_sections(repo_root)
    exec_payload = load_json(repo_root / "codex/mailbox/SKILL_TENSOR_EXECUTION_LATEST.json")
    if not exec_payload and cycle_sections.get("execution"):
        exec_payload = cycle_sections["execution"]
    ledger_exists = exists(repo_root, "codex/mailbox/SKILL_TENSOR_LEDGER.json") or bool(cycle_sections.get("ledger"))
    weights_exists = exists(repo_root, "codex/mailbox/SKILL_TENSOR_WEIGHTS_LATEST.json") or bool(cycle_sections.get("weights"))
    capabilities_exists = exists(repo_root, "config/skill_operator_capabilities.json")
    plan_exists = exists(repo_root, "codex/mailbox/SKILL_TENSOR_PLAN_LATEST.json") or bool(cycle_sections.get("plan"))
    roulette_exists = exists(repo_root, "codex/mailbox/SKILL_TENSOR_ROULETTE_LATEST.json") or bool(cycle_sections.get("roulette"))
    pool_exists = exists(repo_root, "codex/mailbox/SKILL_TENSOR_POOL.json") or bool(cycle_sections.get("pool"))
    inventory_exists = exists(repo_root, "codex/mailbox/SKILL_TENSOR_INVENTORY.json") or bool(cycle_sections.get("inventory"))
    universe_exists = exists(repo_root, "codex/mailbox/SKILL_TENSOR_UNIVERSE_LATEST.json") or bool(cycle_sections.get("universe"))
    legality_exists = exists(repo_root, "codex/mailbox/SKILL_TENSOR_LEGALITY_LATEST.json") or bool(cycle_sections.get("legality"))
    return {
        "phase0": "DONE" if inventory_exists and universe_exists and legality_exists and pool_exists and roulette_exists else "IN PROGRESS",
        "phase1": "DONE" if plan_exists else "IN PROGRESS",
        "phase2": "DONE" if ledger_exists else "IN PROGRESS",
        "phase3": "DONE" if weights_exists else "IN PROGRESS",
        "phase4": "DONE" if capabilities_exists else "IN PROGRESS",
        "phase5": "DONE" if exec_payload.get("overall_status") == "passed" else ("IN PROGRESS" if exec_payload else "PENDING"),
        "phase6": "DONE" if ledger_exists and weights_exists and roulette_exists else "IN PROGRESS",
        "execution_status": exec_payload.get("overall_status", "unknown"),
    }


def render_spec(repo_root: Path, sections: dict | None = None, execution_status: str | None = None) -> str:
    if sections is None:
        statuses = phase_status(repo_root)
        cycle_sections = load_cycle_sections(repo_root)
        inventory = load_json(repo_root / "codex/mailbox/SKILL_TENSOR_INVENTORY.json") or cycle_sections.get("inventory", {})
        universe = load_json(repo_root / "codex/mailbox/SKILL_TENSOR_UNIVERSE_LATEST.json") or cycle_sections.get("universe", {})
        legality = load_json(repo_root / "codex/mailbox/SKILL_TENSOR_LEGALITY_LATEST.json") or cycle_sections.get("legality", {})
        pool = load_json(repo_root / "codex/mailbox/SKILL_TENSOR_POOL.json") or cycle_sections.get("pool", {})
        roulette = load_json(repo_root / "codex/mailbox/SKILL_TENSOR_ROULETTE_LATEST.json") or cycle_sections.get("roulette", {})
        weights = load_json(repo_root / "codex/mailbox/SKILL_TENSOR_WEIGHTS_LATEST.json") or cycle_sections.get("weights", {})
    else:
        inventory = sections.get("inventory", {})
        universe = sections.get("universe", {})
        legality = sections.get("legality", {})
        pool = sections.get("pool", {})
        roulette = sections.get("roulette", {})
        weights = sections.get("weights", {})
        statuses = {
            "phase0": "DONE",
            "phase1": "DONE",
            "phase2": "DONE",
            "phase3": "DONE",
            "phase4": "DONE",
            "phase5": "DONE" if execution_status == "passed" else "IN PROGRESS",
            "phase6": "DONE",
            "execution_status": execution_status or "unknown",
        }
    skill_count = section_value(inventory, "skill_count", len(inventory.get("skills", [])))
    move_count = section_value(universe, "move_count", 0)
    legal_moves = universe.get("status_counts", {}).get("legal", 0) if isinstance(universe.get("status_counts"), dict) else 0
    degraded_moves = section_value(legality, "degraded_count", legality.get("status_counts", {}).get("degraded", 0))
    blocked_moves = section_value(legality, "blocked_count", legality.get("status_counts", {}).get("blocked", 0))
    pool_size = section_value(pool, "pool_size", 0)
    action_group_count = section_value(pool, "action_group_count", 0)
    excluded_size = section_value(pool, "excluded_size", 0)
    chain_length = section_value(roulette, "chain_length", roulette.get("chain_length_actual", 0))
    roulette_summary = roulette.get("summary", {})
    diversity_score = roulette_summary.get("diversity_score", 0)
    cross_lane_coverage = roulette_summary.get("cross_lane_coverage", 0)
    distinct_action_keys = roulette_summary.get("distinct_action_keys_seen", 0)
    pruned = section_value(weights, "pruned_exact_cell_count", len(weights.get("pruned_exact_cells", [])))
    pruned_action_keys = section_value(weights, "pruned_action_key_count", len(weights.get("pruned_action_keys", [])))
    return f"""---
type: design-spec
category: operations
created: 2026-03-19
description: Ontology and execution model for trainstop skill tensor roulette
---

# Skill Tensor Roulette Spec

This spec is regenerated from the live tensor artifacts. It is the canonical anchor for current state, not a manually-maintained note.

## Live Cycle State

- Latest execution status: `{statuses["execution_status"]}`
- Inventory skill count: `{skill_count}`
- Full move count: `{move_count}`
- Legal moves: `{legal_moves}`
- Degraded moves: `{degraded_moves}`
- Blocked moves: `{blocked_moves}`
- Pool size: `{pool_size}`
- Unique action-key groups: `{action_group_count}`
- Excluded cells: `{excluded_size}`
- Current chain length: `{chain_length}`
- Current diversity score: `{diversity_score}`
- Current cross-lane coverage: `{cross_lane_coverage}`
- Current distinct sampled action keys: `{distinct_action_keys}`
- Current history-pruned exact cells: `{pruned}`
- Current history-pruned action keys: `{pruned_action_keys}`

## Core Objects

### Agent Flavor

- `codex`
- `claude`
- `gemini`

### Skill Root

- `.codex/skills`
- `.claude/skills`
- `.gemini/extensions/chthonic-archive-sync/skills`

### Operator Skill

Any inventoried skill can appear as a symbolic operator in the tensor universe.

Current native adapter-backed operator families include:

- `trainstop-orchestrator`
- `skill-polisher`
- `skill-audit`
- `link-path-guard`
- `mailbox-handoff`
- `python-header-canon`

### Target Skill

Any skill entry discovered under a skill root.

### Target Flavor Mode

- `codex`
- `claude`
- `gemini`

## Universe

The full tensor is generated across:

- `executor_flavor`
- `operator_flavor`
- `operator_skill`
- `target_flavor`
- `target_skill`
- `interpretation_flavor`

## Tensor Axes

A minimal run cell is:

`(executor_flavor, operator_skill, source_root, target_root, target_skill, target_flavor_mode)`

Extended chains add:

`(previous_state, chain_depth, seed, weighting_profile)`

## Action Identity

Each symbolic cell now resolves to a normalized execution identity:

`action_key = (operator, scope, actionable-target...)`

Current execution scopes:

- `skill`
- `lane`

## Current Artifact Policy

- `LATEST.json` and `LATEST.md` companions are regenerated in place.
- No timestamp duplication is required for normal iteration.
- The loop state should be read from the latest artifacts, not reconstructed manually.

## Canonical Current Artifacts

- `docs/ops/SKILL_TENSOR_ROULETTE_SPEC.md`
- `codex/mailbox/SKILL_TENSOR_CYCLE_LATEST.json`
- `codex/mailbox/SKILL_TENSOR_CYCLE_LATEST.md`

## Debug / Compatibility Exports

- Stage exports exist only as explicit debug outputs under `codex/mailbox/.tensor_debug/`
- The cycle JSON embeds the summarized state needed for repo-facing review

## Phases

### Phase 0: Anchors

Status: `{statuses["phase0"]}`

### Phase 1: Plan Layer

Status: `{statuses["phase1"]}`

Outputs:

- Embedded in `codex/mailbox/SKILL_TENSOR_CYCLE_LATEST.json`

### Phase 2: Historical Memory

Status: `{statuses["phase2"]}`

Outputs:

- Embedded in `codex/mailbox/SKILL_TENSOR_CYCLE_LATEST.json`

### Phase 3: Adaptive Weighting

Status: `{statuses["phase3"]}`

Current refinements:

- recent-touch penalties
- failed-target promotion
- operator-level adjustments
- exact successful recent-cell pruning

Outputs:

- Embedded in `codex/mailbox/SKILL_TENSOR_CYCLE_LATEST.json`

### Phase 4: Operator Capability Manifest

Status: `{statuses["phase4"]}`

Outputs:

- `config/skill_operator_capabilities.json`

### Phase 5: Sampled-Chain Executor

Status: `{statuses["phase5"]}`

Current refinements:

- capability enforcement
- artifact verification
- explicit failure kinds
- advisory trainstop freshness gate
- operator-specific command templates beyond root-wide defaults

Outputs:

- Embedded in `codex/mailbox/SKILL_TENSOR_CYCLE_LATEST.json`

### Phase 6: Feedback Loop

Status: `{statuses["phase6"]}`

Current refinements:

- execution -> ledger writeback
- ledger -> weight refresh
- weights -> next roulette sample
- stronger history-driven pruning
- richer diversity constraints

## Next Frontier

- stronger history-driven pruning
- more sophisticated weight formulas
- richer roulette diversity constraints
- operator-specific execution semantics
- better pruning of low-value chains
"""


def build_freshness_summary(repo_root: Path) -> dict:
    report = load_json(repo_root / "codex/mailbox/SKILL_FRESHNESS_LATEST.json")
    summary = report.get("summary", {})
    return {
        "status": report.get("status", "unknown"),
        "critical_issues": summary.get("critical_issues", 0),
        "warnings": summary.get("warnings", 0),
    }


def build_duplication_summary(repo_root: Path) -> dict:
    mailbox = repo_root / "codex/mailbox"
    managed = sorted(mailbox.glob("SKILL_TENSOR_*"))
    canonical = {
        "SKILL_TENSOR_INVENTORY.json",
        "SKILL_TENSOR_INVENTORY.md",
        "SKILL_TENSOR_UNIVERSE_LATEST.json",
        "SKILL_TENSOR_UNIVERSE_LATEST.md",
        "SKILL_TENSOR_LEGALITY_LATEST.json",
        "SKILL_TENSOR_LEGALITY_LATEST.md",
        "SKILL_TENSOR_POOL.json",
        "SKILL_TENSOR_POOL.md",
        "SKILL_TENSOR_ROULETTE_LATEST.json",
        "SKILL_TENSOR_ROULETTE_LATEST.md",
        "SKILL_TENSOR_PLAN_LATEST.json",
        "SKILL_TENSOR_PLAN_LATEST.md",
        "SKILL_TENSOR_EXECUTION_LATEST.json",
        "SKILL_TENSOR_EXECUTION_LATEST.md",
        "SKILL_TENSOR_LEDGER.json",
        "SKILL_TENSOR_LEDGER.md",
        "SKILL_TENSOR_WEIGHTS_LATEST.json",
        "SKILL_TENSOR_WEIGHTS_LATEST.md",
        "SKILL_TENSOR_CYCLE_LATEST.json",
        "SKILL_TENSOR_CYCLE_LATEST.md",
    }
    extra = [p.name for p in managed if p.name not in canonical]
    return {
        "managed_duplicates": len(extra),
        "extra_managed_files": extra,
        "managed_files": [p.name for p in managed],
    }


def estimate_dependencies(repo_root: Path) -> dict:
    tensor_scripts = sorted(repo_root.glob("scripts/skill_tensor*.py"))
    stdlib = set(getattr(sys, "stdlib_module_names", set()))
    module_to_package = {
        "yaml": "pyyaml",
        "tomli": "tomli",
        "toml": "toml",
        "requests": "requests",
        "numpy": "numpy",
        "pandas": "pandas",
        "polars": "polars",
        "networkx": "networkx",
        "fastmcp": "fastmcp",
        "huggingface_hub": "huggingface-hub",
        "pydantic": "pydantic",
    }
    discovered = set()
    for script in tensor_scripts:
        try:
            tree = ast.parse(script.read_text(encoding="utf-8"))
        except Exception:
            continue
        for node in ast.walk(tree):
            mod = None
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod = alias.name.split(".")[0]
                    if mod and mod not in stdlib and importlib.util.find_spec(mod) is None:
                        discovered.add(module_to_package.get(mod, mod))
            elif isinstance(node, ast.ImportFrom) and node.module:
                mod = node.module.split(".")[0]
                if mod and mod not in stdlib and importlib.util.find_spec(mod) is None:
                    discovered.add(module_to_package.get(mod, mod))
    packages = sorted(discovered)
    return {
        "count": len(packages),
        "packages": packages,
        "scripts_scanned": [p.name for p in tensor_scripts],
    }


def collect_sections(repo_root: Path) -> dict:
    mailbox = repo_root / "codex" / "mailbox"
    spec_path = repo_root / "docs" / "ops" / "SKILL_TENSOR_ROULETTE_SPEC.md"
    inventory = load_json(mailbox / "SKILL_TENSOR_INVENTORY.json")
    universe = load_json(mailbox / "SKILL_TENSOR_UNIVERSE_LATEST.json")
    legality = load_json(mailbox / "SKILL_TENSOR_LEGALITY_LATEST.json")
    pool = load_json(mailbox / "SKILL_TENSOR_POOL.json")
    roulette = load_json(mailbox / "SKILL_TENSOR_ROULETTE_LATEST.json")
    plan = load_json(mailbox / "SKILL_TENSOR_PLAN_LATEST.json")
    execution = load_json(mailbox / "SKILL_TENSOR_EXECUTION_LATEST.json")
    ledger = load_json(mailbox / "SKILL_TENSOR_LEDGER.json")
    weights = load_json(mailbox / "SKILL_TENSOR_WEIGHTS_LATEST.json")
    spec_text = spec_path.read_text(encoding="utf-8") if spec_path.exists() else None

    latest_ledger = {}
    if ledger.get("entries"):
        latest_ledger = ledger["entries"][-1]

    return {
        "inventory": {
            "path": "codex/mailbox/SKILL_TENSOR_INVENTORY.json",
            "skill_count": len(inventory.get("skills", [])),
        },
        "universe": {
            "path": "codex/mailbox/SKILL_TENSOR_UNIVERSE_LATEST.json",
            "move_count": universe.get("move_count", 0),
            "status_counts": universe.get("status_counts", {}),
            "execution_kind_counts": universe.get("execution_kind_counts", {}),
        },
        "legality": {
            "path": "codex/mailbox/SKILL_TENSOR_LEGALITY_LATEST.json",
            "blocked_count": legality.get("blocked_count", 0),
            "degraded_count": legality.get("degraded_count", 0),
            "reason_counts_top": legality.get("reason_counts_top", []),
        },
        "pool": {
            "path": "codex/mailbox/SKILL_TENSOR_POOL.json",
            "pool_size": pool.get("pool_size", 0),
            "action_group_count": pool.get("action_group_count", 0),
            "excluded_size": pool.get("excluded_size", 0),
        },
        "roulette": {
            "path": "codex/mailbox/SKILL_TENSOR_ROULETTE_LATEST.json",
            "chain_length": roulette.get("chain_length_actual", 0),
            "summary": roulette.get("summary", {}),
        },
        "plan": {
            "path": "codex/mailbox/SKILL_TENSOR_PLAN_LATEST.json",
            "step_count": len(plan.get("steps", [])),
        },
        "execution": {
            "path": "codex/mailbox/SKILL_TENSOR_EXECUTION_LATEST.json",
            "overall_status": execution.get("overall_status"),
            "result_count": len(execution.get("results", [])),
        },
        "ledger": {
            "path": "codex/mailbox/SKILL_TENSOR_LEDGER.json",
            "entry_count": len(ledger.get("entries", [])),
            "latest_execution_status": latest_ledger.get("execution_status"),
            "latest_seed_text": latest_ledger.get("seed_text"),
        },
        "weights": {
            "path": "codex/mailbox/SKILL_TENSOR_WEIGHTS_LATEST.json",
            "recent_entry_count": weights.get("recent_entry_count", 0),
            "pruned_action_key_count": len(weights.get("pruned_action_keys", [])),
            "pruned_exact_cell_count": len(weights.get("pruned_exact_cells", [])),
        },
        "spec": {
            "path": "docs/ops/SKILL_TENSOR_ROULETTE_SPEC.md",
            "exists": spec_text is not None,
            "length": 0 if spec_text is None else len(spec_text),
        },
    }


def build_action_model_summary_from_payloads(pool: dict, roulette: dict) -> dict:
    groups: dict[str, list[dict]] = defaultdict(list)
    for cell in pool.get("pool", []):
        if not isinstance(cell, dict):
            continue
        key = json.dumps(cell.get("action_key") or action_key_parts(cell), separators=(",", ":"))
        groups[key].append(cell)

    collapsed = []
    for key, cells in groups.items():
        if len(cells) <= 1:
            continue
        distinct_targets = sorted({f"{cell.get('target_root')}::{cell.get('target_skill')}" for cell in cells})
        if len(distinct_targets) <= 1:
            continue
        collapsed.append(
            {
                "action_key": json.loads(key),
                "cell_count": len(cells),
                "distinct_target_count": len(distinct_targets),
                "sample_targets": distinct_targets[:6],
            }
        )
    collapsed.sort(key=lambda row: (row["cell_count"], row["distinct_target_count"]), reverse=True)
    sampled = roulette.get("selected", [])
    sampled_keys = [
        json.dumps(step.get("action_key") or step.get("cell", {}).get("action_key") or action_key_parts(step.get("cell", {})), separators=(",", ":"))
        for step in sampled
    ]
    return {
        "pool_cell_count": pool.get("pool_size", 0),
        "unique_action_key_count": len(groups),
        "collapsed_group_count": len(collapsed),
        "largest_collision_group": 0 if not collapsed else collapsed[0]["cell_count"],
        "top_collisions": collapsed[:5],
        "sampled_chain_length": len(sampled),
        "sampled_unique_action_keys": len(set(sampled_keys)),
        "sampled_has_action_collisions": len(sampled_keys) != len(set(sampled_keys)),
    }


def build_action_model_summary(repo_root: Path) -> dict:
    mailbox = repo_root / "codex" / "mailbox"
    pool = load_json(mailbox / "SKILL_TENSOR_POOL.json")
    roulette = load_json(mailbox / "SKILL_TENSOR_ROULETTE_LATEST.json")
    return build_action_model_summary_from_payloads(pool, roulette)


def render_cycle_markdown(payload: dict) -> str:
    bootstrap = payload.get("bootstrap", {})
    action_model = payload.get("action_model", {})
    lines = [
        "# Skill Tensor Cycle",
        "",
        f"- Overall Status: `{payload.get('overall_status')}`",
        f"- Queue Length: `{payload.get('queue_length')}`",
        "",
        "## Bootstrap",
        f"- Ledger Existed: `{bootstrap.get('ledger_existed')}`",
        f"- Ledger Initialized: `{bootstrap.get('ledger_initialized')}`",
        f"- Ledger Entries Before Run: `{bootstrap.get('entries_before_run')}`",
        "",
        "## Severity",
        f"- Freshness Status: `{payload.get('freshness', {}).get('status')}`",
        f"- Critical Issues: `{payload.get('freshness', {}).get('critical_issues')}`",
        f"- Warnings: `{payload.get('freshness', {}).get('warnings')}`",
        "",
        "## Action Model",
        f"- Pool Unique Action Keys: `{action_model.get('unique_action_key_count')}`",
        f"- Collapsed Action Groups: `{action_model.get('collapsed_group_count')}`",
        f"- Largest Collision Group: `{action_model.get('largest_collision_group')}`",
        f"- Sampled Unique Action Keys: `{action_model.get('sampled_unique_action_keys')}`",
        "",
        "## Duplication",
        f"- Managed Artifact Duplicates: `{payload.get('duplication', {}).get('managed_duplicates')}`",
        f"- Extra Managed Files: `{payload.get('duplication', {}).get('extra_managed_files')}`",
        "",
        "## Dependencies",
        f"- Estimated External Packages: `{payload.get('dependencies', {}).get('count')}`",
        "",
        "## Steps",
    ]
    for step in payload.get("steps", []):
        lines += [f"### {step['name']}", f"- Status: `{step['status']}`", f"- RC: `{step['rc']}`", f"- Seconds: `{step['seconds']}`", ""]
    return "\n".join(lines) + "\n"


def stage_inventory(repo_root: Path, output: str) -> dict:
    payload = build_inventory_payload(repo_root)
    out = repo_root / output
    write_json(out, payload)
    write_text(out.with_suffix(".md"), render_inventory_markdown(payload))
    return payload


def stage_universe(repo_root: Path, rules_path: str, inventory_path: str, output: str) -> dict:
    rules = load_json(repo_root / rules_path)
    inventory = load_json(repo_root / inventory_path)
    payload = build_universe_payload(rules, inventory, rules_path, inventory_path)
    out = repo_root / output
    write_json(out, payload)
    write_text(out.with_suffix(".md"), render_universe_markdown(payload))
    return payload


def stage_legality(repo_root: Path, universe_path: str, output: str) -> dict:
    universe = load_json(repo_root / universe_path)
    payload = build_legality_payload(universe, universe_path)
    out = repo_root / output
    write_json(out, payload)
    write_text(out.with_suffix(".md"), render_legality_markdown(payload))
    return payload


def stage_pool(repo_root: Path, rules_path: str, universe_path: str, output: str) -> dict:
    rules = load_json(repo_root / rules_path)
    universe = load_json(repo_root / universe_path)
    payload = build_pool_payload(rules, universe, rules_path, universe_path)
    out = repo_root / output
    write_json(out, payload)
    write_text(out.with_suffix(".md"), render_pool_markdown(payload))
    return payload


def stage_weights(repo_root: Path, rules_path: str, inventory_path: str, pool_path: str, ledger_path: str, output: str) -> dict:
    rules = load_json(repo_root / rules_path)
    inventory = load_json(repo_root / inventory_path)
    pool = load_json(repo_root / pool_path)
    ledger = load_json(repo_root / ledger_path)
    payload = build_weights_payload(rules, inventory, pool, ledger, rules_path, inventory_path, pool_path, ledger_path)
    out = repo_root / output
    write_json(out, payload)
    write_text(out.with_suffix(".md"), render_weights_markdown(payload))
    return payload


def stage_roulette(repo_root: Path, rules_path: str, pool_path: str, weights_path: str, output: str, seed: str, chain_length: int) -> dict:
    rules = load_json(repo_root / rules_path)
    pool = load_json(repo_root / pool_path)
    weights_full = load_json(repo_root / weights_path)
    weights = weights_full if weights_full else None
    payload = build_roulette_payload(rules, pool, weights, seed, chain_length, weights_path if weights else None)
    out = repo_root / output
    write_json(out, payload)
    write_text(out.with_suffix(".md"), render_roulette_markdown(payload))
    return payload


def stage_plan(repo_root: Path, rules_path: str, capabilities_path: str, input_path: str, output: str) -> dict:
    rules = load_json(repo_root / rules_path)
    capabilities = load_json(repo_root / capabilities_path)
    sampled = load_json(repo_root / input_path)
    payload = build_plan_payload(sampled, rules, capabilities, input_path, capabilities_path)
    out = repo_root / output
    write_json(out, payload)
    write_text(out.with_suffix(".md"), render_plan_markdown(payload))
    return payload


def stage_ledger(repo_root: Path, rules_path: str, roulette_path: str, plan_path: str, output: str) -> dict:
    rules = load_json(repo_root / rules_path)
    roulette = load_json(repo_root / roulette_path)
    plan = load_json(repo_root / plan_path)
    out = repo_root / output
    ledger = load_json(out) if out.exists() else {"schema_version": 2, "entries": []}
    ledger, _ = append_ledger_entry(ledger, roulette, plan, rules)
    write_json(out, ledger)
    write_text(out.with_suffix(".md"), render_ledger_markdown(ledger))
    return ledger


def stage_execute(repo_root: Path, input_path: str, output: str) -> dict:
    plan = load_json(repo_root / input_path)
    payload = execute_plan(plan, repo_root)
    out = repo_root / output
    write_json(out, payload)
    write_text(out.with_suffix(".md"), render_execution_markdown(payload))
    return payload


def stage_render_spec(repo_root: Path, output: str) -> str:
    content = render_spec(repo_root)
    out = repo_root / output
    write_text(out, content)
    return content


def stage_feedback(
    repo_root: Path,
    rules_path: str,
    ledger_path: str,
    execution_path: str,
    roulette_path: str,
    plan_path: str,
    weights_path: str,
    inventory_path: str,
    pool_path: str,
    spec_path: str,
) -> tuple[dict, dict]:
    rules = load_json(repo_root / rules_path)
    ledger = load_json(repo_root / ledger_path)
    execution = load_json(repo_root / execution_path)
    roulette = load_json(repo_root / roulette_path)
    plan = load_json(repo_root / plan_path)
    ledger = apply_feedback(ledger, execution, roulette, plan, rules)
    write_json(repo_root / ledger_path, ledger)
    write_text((repo_root / ledger_path).with_suffix(".md"), render_ledger_markdown(ledger))
    weights = stage_weights(repo_root, rules_path, inventory_path, pool_path, ledger_path, weights_path)
    stage_render_spec(repo_root, spec_path)
    return ledger, weights


def load_embedded_or_legacy_ledger(repo_root: Path, cycle_output_rel: str, legacy_ledger_rel: str, rules: dict) -> dict:
    cycle_path = repo_root / cycle_output_rel
    if cycle_path.exists():
        cycle_payload = load_json(cycle_path)
        embedded = cycle_payload.get("sections", {}).get("ledger")
        if isinstance(embedded, dict) and embedded.get("ledger_mode") == "bounded-history-v1":
            return normalize_ledger(embedded, rules)
    legacy_path = repo_root / legacy_ledger_rel
    if legacy_path.exists():
        return normalize_ledger(load_json(legacy_path), rules)
    return {
        "schema_version": 3,
        "ledger_mode": "bounded-history-v1",
        "max_runs": ledger_history_limit(rules),
        "runs": [],
    }


def run_cycle(args: argparse.Namespace) -> int:
    repo_root = find_repo_root(Path.cwd())
    sequence = [
        "inventory",
        "universe",
        "legality",
        "pool",
        "ledger-bootstrap",
        "weights",
        "roulette",
        "plan",
        "ledger",
        "execute",
        "feedback",
    ]
    results = []
    overall_status = "passed"
    continue_after_failure = {"ledger", "execute", "feedback"}

    inventory_path = "codex/mailbox/.tmp_tensor_cycle/SKILL_TENSOR_INVENTORY.json"
    universe_path = "codex/mailbox/.tmp_tensor_cycle/SKILL_TENSOR_UNIVERSE_LATEST.json"
    legality_path = "codex/mailbox/.tmp_tensor_cycle/SKILL_TENSOR_LEGALITY_LATEST.json"
    pool_path = "codex/mailbox/.tmp_tensor_cycle/SKILL_TENSOR_POOL.json"
    roulette_path = "codex/mailbox/.tmp_tensor_cycle/SKILL_TENSOR_ROULETTE_LATEST.json"
    plan_path = "codex/mailbox/.tmp_tensor_cycle/SKILL_TENSOR_PLAN_LATEST.json"
    execution_path = "codex/mailbox/.tmp_tensor_cycle/SKILL_TENSOR_EXECUTION_LATEST.json"
    ledger_path = "codex/mailbox/.tmp_tensor_cycle/SKILL_TENSOR_LEDGER.json"
    weights_path = "codex/mailbox/.tmp_tensor_cycle/SKILL_TENSOR_WEIGHTS_LATEST.json"
    spec_path = "codex/mailbox/.tmp_tensor_cycle/SKILL_TENSOR_ROULETTE_SPEC.md"
    rules_path = "config/skill_tensor_rules.json"
    capabilities_path = "config/skill_operator_capabilities.json"
    cycle_output_rel = args.output
    bootstrap = {"ledger_path": args.ledger, "ledger_existed": False, "ledger_initialized": False, "entries_before_run": 0}

    tmp_root = repo_root / "codex" / "mailbox" / ".tmp_tensor_cycle"
    if tmp_root.exists():
        shutil.rmtree(tmp_root)
    tmp_root.mkdir(parents=True, exist_ok=True)

    rules = load_json(repo_root / rules_path)
    seeded_ledger = load_embedded_or_legacy_ledger(repo_root, cycle_output_rel, args.ledger, rules)
    write_json(repo_root / ledger_path, seeded_ledger)
    write_text((repo_root / ledger_path).with_suffix(".md"), render_ledger_markdown(seeded_ledger))

    for name in sequence:
        t0 = time.time()
        status = "passed"
        rc = 0
        stdout_tail = ""
        stderr_tail = ""
        try:
            if name == "inventory":
                stage_inventory(repo_root, inventory_path)
                stdout_tail = inventory_path
            elif name == "universe":
                stage_universe(repo_root, rules_path, inventory_path, universe_path)
                stdout_tail = universe_path
            elif name == "legality":
                stage_legality(repo_root, universe_path, legality_path)
                stdout_tail = legality_path
            elif name == "pool":
                stage_pool(repo_root, rules_path, universe_path, pool_path)
                stdout_tail = pool_path
            elif name == "ledger-bootstrap":
                _, bootstrap = ensure_bootstrap_ledger(repo_root, ledger_path)
                stdout_tail = json.dumps(bootstrap, sort_keys=True)
            elif name == "weights":
                stage_weights(repo_root, rules_path, inventory_path, pool_path, ledger_path, weights_path)
                stdout_tail = weights_path
            elif name == "roulette":
                stage_roulette(repo_root, rules_path, pool_path, weights_path, roulette_path, args.seed, args.chain_length)
                stdout_tail = roulette_path
            elif name == "plan":
                stage_plan(repo_root, rules_path, capabilities_path, roulette_path, plan_path)
                stdout_tail = plan_path
            elif name == "ledger":
                stage_ledger(repo_root, rules_path, roulette_path, plan_path, ledger_path)
                stdout_tail = ledger_path
            elif name == "execute":
                execution = stage_execute(repo_root, plan_path, execution_path)
                stdout_tail = execution_path
                if execution.get("overall_status") != "passed":
                    raise RuntimeError(f"execution:{execution.get('overall_status')}")
            elif name == "feedback":
                stage_feedback(repo_root, rules_path, ledger_path, execution_path, roulette_path, plan_path, weights_path, inventory_path, pool_path, spec_path)
                stdout_tail = ledger_path
            else:
                raise RuntimeError(f"unknown-stage:{name}")
        except Exception as exc:  # noqa: BLE001
            status = "failed"
            rc = 2
            stderr_tail = str(exc)
            overall_status = "failed"
            if name not in continue_after_failure:
                results.append({"name": name, "cmd": [], "rc": rc, "seconds": round(time.time() - t0, 3), "status": status, "stdout_tail": stdout_tail, "stderr_tail": stderr_tail})
                break
        results.append({"name": name, "cmd": [], "rc": rc, "seconds": round(time.time() - t0, 3), "status": status, "stdout_tail": stdout_tail, "stderr_tail": stderr_tail})

    inventory = load_json(repo_root / inventory_path)
    universe = load_json(repo_root / universe_path)
    legality = load_json(repo_root / legality_path)
    pool = load_json(repo_root / pool_path)
    roulette = load_json(repo_root / roulette_path)
    plan = load_json(repo_root / plan_path)
    execution = load_json(repo_root / execution_path)
    ledger = load_json(repo_root / ledger_path)
    weights = load_json(repo_root / weights_path)

    latest_run = {}
    if ledger.get("runs"):
        latest_run = ledger["runs"][-1]

    sections = {
        "inventory": {
            "path": "codex/mailbox/.tmp_tensor_cycle/SKILL_TENSOR_INVENTORY.json",
            "skill_count": len(inventory.get("skills", [])),
        },
        "universe": {
            "path": "codex/mailbox/.tmp_tensor_cycle/SKILL_TENSOR_UNIVERSE_LATEST.json",
            "move_count": universe.get("move_count", 0),
            "status_counts": universe.get("status_counts", {}),
            "execution_kind_counts": universe.get("execution_kind_counts", {}),
        },
        "legality": {
            "path": "codex/mailbox/.tmp_tensor_cycle/SKILL_TENSOR_LEGALITY_LATEST.json",
            "blocked_count": legality.get("blocked_count", 0),
            "degraded_count": legality.get("degraded_count", 0),
            "reason_counts_top": legality.get("reason_counts_top", []),
        },
        "pool": {
            "path": "codex/mailbox/.tmp_tensor_cycle/SKILL_TENSOR_POOL.json",
            "pool_size": pool.get("pool_size", 0),
            "action_group_count": pool.get("action_group_count", 0),
            "excluded_size": pool.get("excluded_size", 0),
        },
        "roulette": {
            "path": "codex/mailbox/.tmp_tensor_cycle/SKILL_TENSOR_ROULETTE_LATEST.json",
            "chain_length": roulette.get("chain_length_actual", 0),
            "summary": roulette.get("summary", {}),
        },
        "plan": {
            "path": "codex/mailbox/.tmp_tensor_cycle/SKILL_TENSOR_PLAN_LATEST.json",
            "step_count": len(plan.get("steps", [])),
        },
        "execution": {
            "path": "codex/mailbox/.tmp_tensor_cycle/SKILL_TENSOR_EXECUTION_LATEST.json",
            "overall_status": execution.get("overall_status"),
            "result_count": len(execution.get("results", [])),
        },
        "ledger": {
            "path": "codex/mailbox/.tmp_tensor_cycle/SKILL_TENSOR_LEDGER.json",
            "ledger_mode": ledger.get("ledger_mode"),
            "max_runs": ledger.get("max_runs"),
            "run_count": len(ledger.get("runs", [])),
            "latest_execution_status": latest_run.get("execution_status"),
            "latest_seed_text": latest_run.get("seed_text"),
        },
        "weights": {
            "path": "codex/mailbox/.tmp_tensor_cycle/SKILL_TENSOR_WEIGHTS_LATEST.json",
            "recent_entry_count": weights.get("recent_entry_count", 0),
            "pruned_action_key_count": len(weights.get("pruned_action_keys", [])),
            "pruned_exact_cell_count": len(weights.get("pruned_exact_cells", [])),
        },
    }

    payload = {
        "schema_version": 2,
        "overall_status": overall_status,
        "queue_length": len(sequence),
        "stage_queue": sequence,
        "bootstrap": bootstrap,
        "freshness": build_freshness_summary(repo_root),
        "action_model": build_action_model_summary_from_payloads(pool, roulette),
        "duplication": build_duplication_summary(repo_root),
        "dependencies": estimate_dependencies(repo_root),
        "steps": results,
        "sections": sections,
    }
    out = repo_root / args.output
    write_json(out, payload)
    write_text(out.with_suffix(".md"), render_cycle_markdown(payload))
    write_text(repo_root / "docs/ops/SKILL_TENSOR_ROULETTE_SPEC.md", render_spec(repo_root, sections=sections, execution_status=overall_status))
    shutil.rmtree(tmp_root, ignore_errors=True)
    print(out.relative_to(repo_root).as_posix())
    print(f"overall_status={overall_status}")
    print(f"ledger_initialized={bootstrap['ledger_initialized']}")
    return 0 if overall_status == "passed" else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Single-file authority for skill tensor stages and full cycle")
    sub = parser.add_subparsers(dest="command")

    p_cycle = sub.add_parser("cycle")
    p_cycle.add_argument("--output", default="codex/mailbox/SKILL_TENSOR_CYCLE_LATEST.json")
    p_cycle.add_argument("--ledger", default="codex/mailbox/SKILL_TENSOR_LEDGER.json")
    p_cycle.add_argument("--seed", default="trainstop-default-seed")
    p_cycle.add_argument("--chain-length", type=int, default=4)

    p_inventory = sub.add_parser("inventory")
    p_inventory.add_argument("--output", default="codex/mailbox/.tensor_debug/SKILL_TENSOR_INVENTORY.json")

    p_universe = sub.add_parser("universe")
    p_universe.add_argument("--rules", default="config/skill_tensor_rules.json")
    p_universe.add_argument("--inventory", default="codex/mailbox/.tensor_debug/SKILL_TENSOR_INVENTORY.json")
    p_universe.add_argument("--output", default="codex/mailbox/.tensor_debug/SKILL_TENSOR_UNIVERSE_LATEST.json")

    p_legality = sub.add_parser("legality")
    p_legality.add_argument("--universe", default="codex/mailbox/.tensor_debug/SKILL_TENSOR_UNIVERSE_LATEST.json")
    p_legality.add_argument("--output", default="codex/mailbox/.tensor_debug/SKILL_TENSOR_LEGALITY_LATEST.json")

    p_pool = sub.add_parser("pool")
    p_pool.add_argument("--rules", default="config/skill_tensor_rules.json")
    p_pool.add_argument("--universe", default="codex/mailbox/.tensor_debug/SKILL_TENSOR_UNIVERSE_LATEST.json")
    p_pool.add_argument("--output", default="codex/mailbox/.tensor_debug/SKILL_TENSOR_POOL.json")

    p_weights = sub.add_parser("weights")
    p_weights.add_argument("--rules", default="config/skill_tensor_rules.json")
    p_weights.add_argument("--inventory", default="codex/mailbox/.tensor_debug/SKILL_TENSOR_INVENTORY.json")
    p_weights.add_argument("--pool", default="codex/mailbox/.tensor_debug/SKILL_TENSOR_POOL.json")
    p_weights.add_argument("--ledger", default="codex/mailbox/SKILL_TENSOR_LEDGER.json")
    p_weights.add_argument("--output", default="codex/mailbox/.tensor_debug/SKILL_TENSOR_WEIGHTS_LATEST.json")

    p_roulette = sub.add_parser("roulette")
    p_roulette.add_argument("--rules", default="config/skill_tensor_rules.json")
    p_roulette.add_argument("--pool", default="codex/mailbox/.tensor_debug/SKILL_TENSOR_POOL.json")
    p_roulette.add_argument("--weights", default="codex/mailbox/.tensor_debug/SKILL_TENSOR_WEIGHTS_LATEST.json")
    p_roulette.add_argument("--output", default="codex/mailbox/.tensor_debug/SKILL_TENSOR_ROULETTE_LATEST.json")
    p_roulette.add_argument("--seed", default="trainstop-default-seed")
    p_roulette.add_argument("--chain-length", type=int, default=4)

    p_plan = sub.add_parser("plan")
    p_plan.add_argument("--rules", default="config/skill_tensor_rules.json")
    p_plan.add_argument("--capabilities", default="config/skill_operator_capabilities.json")
    p_plan.add_argument("--input", default="codex/mailbox/.tensor_debug/SKILL_TENSOR_ROULETTE_LATEST.json")
    p_plan.add_argument("--output", default="codex/mailbox/.tensor_debug/SKILL_TENSOR_PLAN_LATEST.json")

    p_ledger = sub.add_parser("ledger")
    p_ledger.add_argument("--rules", default="config/skill_tensor_rules.json")
    p_ledger.add_argument("--roulette", default="codex/mailbox/.tensor_debug/SKILL_TENSOR_ROULETTE_LATEST.json")
    p_ledger.add_argument("--plan", default="codex/mailbox/.tensor_debug/SKILL_TENSOR_PLAN_LATEST.json")
    p_ledger.add_argument("--output", default="codex/mailbox/SKILL_TENSOR_LEDGER.json")

    p_execute = sub.add_parser("execute")
    p_execute.add_argument("--input", default="codex/mailbox/.tensor_debug/SKILL_TENSOR_PLAN_LATEST.json")
    p_execute.add_argument("--output", default="codex/mailbox/.tensor_debug/SKILL_TENSOR_EXECUTION_LATEST.json")

    p_feedback = sub.add_parser("feedback")
    p_feedback.add_argument("--rules", default="config/skill_tensor_rules.json")
    p_feedback.add_argument("--ledger", default="codex/mailbox/SKILL_TENSOR_LEDGER.json")
    p_feedback.add_argument("--execution", default="codex/mailbox/.tensor_debug/SKILL_TENSOR_EXECUTION_LATEST.json")
    p_feedback.add_argument("--roulette", default="codex/mailbox/.tensor_debug/SKILL_TENSOR_ROULETTE_LATEST.json")
    p_feedback.add_argument("--plan", default="codex/mailbox/.tensor_debug/SKILL_TENSOR_PLAN_LATEST.json")

    p_spec = sub.add_parser("render-spec")
    p_spec.add_argument("--output", default="docs/ops/SKILL_TENSOR_ROULETTE_SPEC.md")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command in {None, "cycle"}:
        if args.command is None:
            args.output = "codex/mailbox/SKILL_TENSOR_CYCLE_LATEST.json"
            args.ledger = "codex/mailbox/SKILL_TENSOR_LEDGER.json"
            args.seed = "trainstop-default-seed"
            args.chain_length = 4
        return run_cycle(args)

    repo_root = find_repo_root(Path.cwd())
    if args.command == "inventory":
        payload = stage_inventory(repo_root, args.output)
        print((repo_root / args.output).relative_to(repo_root).as_posix())
        return 0 if payload else 2
    if args.command == "universe":
        payload = stage_universe(repo_root, args.rules, args.inventory, args.output)
        print((repo_root / args.output).relative_to(repo_root).as_posix())
        print(f"move_count={payload.get('move_count')}")
        return 0
    if args.command == "legality":
        payload = stage_legality(repo_root, args.universe, args.output)
        print((repo_root / args.output).relative_to(repo_root).as_posix())
        print(f"blocked_count={payload.get('blocked_count')}")
        print(f"degraded_count={payload.get('degraded_count')}")
        return 0
    if args.command == "pool":
        payload = stage_pool(repo_root, args.rules, args.universe, args.output)
        print((repo_root / args.output).relative_to(repo_root).as_posix())
        print(f"pool_size={payload.get('pool_size')}")
        print(f"excluded_size={payload.get('excluded_size')}")
        return 0
    if args.command == "weights":
        stage_weights(repo_root, args.rules, args.inventory, args.pool, args.ledger, args.output)
        print((repo_root / args.output).relative_to(repo_root).as_posix())
        return 0
    if args.command == "roulette":
        payload = stage_roulette(repo_root, args.rules, args.pool, args.weights, args.output, args.seed, args.chain_length)
        print((repo_root / args.output).relative_to(repo_root).as_posix())
        print(f"seed_value={payload.get('seed_value')}")
        print(f"chain_length={payload.get('chain_length_actual')}")
        return 0
    if args.command == "plan":
        stage_plan(repo_root, args.rules, args.capabilities, args.input, args.output)
        print((repo_root / args.output).relative_to(repo_root).as_posix())
        return 0
    if args.command == "ledger":
        ledger = stage_ledger(repo_root, args.rules, args.roulette, args.plan, args.output)
        print((repo_root / args.output).relative_to(repo_root).as_posix())
        print(f"entries={len(ledger.get('entries', []))}")
        return 0
    if args.command == "execute":
        payload = stage_execute(repo_root, args.input, args.output)
        print((repo_root / args.output).relative_to(repo_root).as_posix())
        print(f"overall_status={payload.get('overall_status')}")
        return 0 if payload.get("overall_status") == "passed" else 2
    if args.command == "feedback":
        stage_feedback(
            repo_root,
            args.rules,
            args.ledger,
            args.execution,
            args.roulette,
            args.plan,
            "codex/mailbox/SKILL_TENSOR_WEIGHTS_LATEST.json",
            "codex/mailbox/SKILL_TENSOR_INVENTORY.json",
            "codex/mailbox/SKILL_TENSOR_POOL.json",
            "docs/ops/SKILL_TENSOR_ROULETTE_SPEC.md",
        )
        latest = load_json(repo_root / args.ledger).get("entries", [])[-1]
        print((repo_root / args.ledger).relative_to(repo_root).as_posix())
        print(f"execution_status={latest.get('execution_status')}")
        print(f"failure_classes={len(latest.get('failure_classes', []))}")
        return 0
    if args.command == "render-spec":
        stage_render_spec(repo_root, args.output)
        print((repo_root / args.output).relative_to(repo_root).as_posix())
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
