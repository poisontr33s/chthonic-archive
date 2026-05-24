#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: wptg_repeatable_cycle.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Repeatable WPTG cycle orchestrator.

@SID:           WPTG_REPEATABLE_CYCLE_V1
@Shabti:        CLI Script
@Purpose:       Execute a reusable Phase 0 -> Part 4 WPTG cycle, persist cycle memory, and emit reverse-rarity-first baseline views.
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
import urllib.parse
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.wptg_common import (
    compound_extension,
    ensure_utf8,
    markdown_path_link,
    now_iso,
    repo_root,
    write_json,
    write_text,
)


@dataclass(frozen=True, slots=True)
class CycleStep:
    step_id: str
    label: str
    toolchain: str
    command: tuple[str, ...]
    expected_exit_codes: tuple[int, ...]
    required_outputs: tuple[str, ...]
    critical: bool = True


CYCLE_STEPS: tuple[CycleStep, ...] = (
    CycleStep(
        step_id="phase_0_universe",
        label="Phase 0 - Polyglot Extension Universe Scanner",
        toolchain="uv",
        command=("uv", "run", "scripts/extension_universe_scanner.py"),
        expected_exit_codes=(0, 1, 2),
        required_outputs=("audit-reports/extension_universe.json",),
    ),
    CycleStep(
        step_id="part_1_census",
        label="Part 1 - WPTG Filetype Census",
        toolchain="uv",
        command=("uv", "run", "scripts/wptg_filetype_census.py"),
        expected_exit_codes=(0, 1, 2),
        required_outputs=(
            "audit-reports/wptg_filetype_census.json",
            "audit-reports/orphaned_artifact_reconciliation.json",
            "codex/mailbox/LOG_ARCHAEOLOGY_TRIAGE.md",
            "codex/mailbox/WPTG_FILETYPE_GOVERNANCE_PROPOSAL.md",
        ),
    ),
    CycleStep(
        step_id="part_2_forge",
        label="Part 2 - Universal Forge",
        toolchain="uv",
        command=("uv", "run", "scripts/universal_forge.py"),
        expected_exit_codes=(0,),
        required_outputs=(
            "dumpster-dive/forge/furnace/FURNACE_MANIFEST.json",
            "dumpster-dive/forge/tempered/GRADUATION_MANIFEST.json",
            "codex/mailbox/FORGE_TRANSMUTATION_REPORT.md",
        ),
    ),
    CycleStep(
        step_id="part_3_ankh_scan",
        label="Part 3 - ankh-forge scan",
        toolchain="cargo",
        command=(
            "cargo",
            "run",
            "-p",
            "ankh-forge",
            "--",
            "scan",
            "--root",
            ".",
            "--output",
            "audit-reports/extension_universe_ankh.json",
        ),
        expected_exit_codes=(0,),
        required_outputs=("audit-reports/extension_universe_ankh.json",),
    ),
    CycleStep(
        step_id="part_3_ankh_census",
        label="Part 3 - ankh-forge census",
        toolchain="cargo",
        command=(
            "cargo",
            "run",
            "-p",
            "ankh-forge",
            "--",
            "census",
            "--root",
            ".",
            "--output",
            "audit-reports/wptg_filetype_census_ankh.json",
        ),
        expected_exit_codes=(0,),
        required_outputs=("audit-reports/wptg_filetype_census_ankh.json",),
    ),
    CycleStep(
        step_id="part_3_ankh_landscape",
        label="Part 3 - ankh-forge landscape",
        toolchain="cargo",
        command=(
            "cargo",
            "run",
            "-p",
            "ankh-forge",
            "--",
            "landscape",
            "--root",
            ".",
            "--output",
            "audit-reports/oxidized_tooling_landscape.json",
        ),
        expected_exit_codes=(0,),
        required_outputs=("audit-reports/oxidized_tooling_landscape.json",),
    ),
    CycleStep(
        step_id="part_3_ankh_eol",
        label="Part 3 - ankh-forge eol",
        toolchain="cargo",
        command=(
            "cargo",
            "run",
            "-p",
            "ankh-forge",
            "--",
            "eol",
            "--output",
            "audit-reports/oxidized_tooling_eol.json",
        ),
        expected_exit_codes=(0,),
        required_outputs=("audit-reports/oxidized_tooling_eol.json",),
    ),
    CycleStep(
        step_id="part_3_bun_lane_pulse",
        label="Part 3 - Bun lane pulse",
        toolchain="bun",
        command=("bun", "--version"),
        expected_exit_codes=(0,),
        required_outputs=(),
        critical=False,
    ),
    CycleStep(
        step_id="part_4_validator",
        label="Part 4 - Extension Contribution Validator",
        toolchain="uv",
        command=("uv", "run", "scripts/extension_contribution_audit.py"),
        expected_exit_codes=(0,),
        required_outputs=(
            "audit-reports/extension_contribution_audit.json",
            "audit-reports/extension_contribution_audit.md",
        ),
    ),
)


ANOMALY_WEIGHTS: dict[str, float] = {
    "tracked_bytecode": 2.5,
    "filename_encoding_damage": 2.3,
    "tracked_env_surface": 2.2,
    "orphan_json_candidate": 2.0,
    "filetype_directory_mismatch": 1.8,
    "legacy_batch_in_pwsh_repo": 1.6,
    "disabled_by_rename": 1.5,
}

LEGACY_SCRIPT_REL = "scripts/wpth_repeatable_cycle_LEGACY"
PROFILE_NAME = "WPTG-AMALGAM-RR v1-candidate"
TARGET_V1_NAME = "WPTG-AMALGAM-RR v1"
PROFILE_CONTRACT_OUTPUT = Path("audit-reports/wptg_amalgam_rr_v1_candidate_contract.json")
PROMOTION_REGISTRY_OUTPUT = Path("audit-reports/wptg_promotion_adoption.json")
MIN_PROMOTED_FOR_V1 = 3
PROMOTION_LANE_TOKENS: tuple[str, ...] = ("go/", "csharp/", "c_cpp/", "python/", "powershell/")
PROMOTION_STATUSES: tuple[str, ...] = ("pending", "promoted", "rejected", "deferred")
HARD_BLOCKER_ANOMALY_TYPES: tuple[str, ...] = (
    "tracked_env_surface",
    "filename_encoding_damage",
    "tracked_bytecode",
)
GOVERNANCE_BACKLOG_ANOMALY_TYPES: tuple[str, ...] = (
    "filetype_directory_mismatch",
    "disabled_by_rename",
    "legacy_batch_in_pwsh_repo",
    "orphan_json_candidate",
)
MARKDOWN_REFERENCE_EXTRA_GLOBS: tuple[str, ...] = (
    "dumpster-dive/forge/furnace/docs/*.md",
    "dumpster-dive/forge/tempered/docs/*.md",
    "dumpster-dive/forge/furnace/workflows/workflow_pattern_catalog.md",
    "dumpster-dive/forge/tempered/workflows/workflow_pattern_catalog.md",
)
MARKDOWN_REF_DEF_RE = re.compile(r"^\s*\[([^\]]+)\]:\s*(\S+)?")
MARKDOWN_EXPLICIT_REF_RE = re.compile(r"(?<!\\)\[([^\]]+)\]\[([^\]]*)\]")
MARKDOWN_SHORTCUT_REF_RE = re.compile(r"(?<!\\)\[([^\[\]\n]+?)\](?!\(|\[|:)")
MARKDOWN_INLINE_LINK_RE = re.compile(r"(?<!\\)\[[^\]]+\]\(([^)]+)\)")
INLINE_CODE_RE = re.compile(r"`[^`]*`")
EXTERNAL_LINK_PREFIXES: tuple[str, ...] = (
    "http://",
    "https://",
    "mailto:",
    "tel:",
    "data:",
    "ftp://",
    "vscode:",
)


def _output_pre_state(root: Path, outputs: tuple[str, ...]) -> dict[str, float | None]:
    state: dict[str, float | None] = {}
    for rel in outputs:
        path = root / rel
        state[rel] = path.stat().st_mtime if path.exists() else None
    return state


def _output_post_state(root: Path, outputs: tuple[str, ...]) -> dict[str, dict[str, Any]]:
    state: dict[str, dict[str, Any]] = {}
    for rel in outputs:
        path = root / rel
        if path.exists():
            state[rel] = {"exists": True, "mtime": path.stat().st_mtime}
        else:
            state[rel] = {"exists": False, "mtime": None}
    return state


def run_step(root: Path, step: CycleStep) -> dict[str, Any]:
    start = time.perf_counter()
    pre_state = _output_pre_state(root, step.required_outputs)

    result = subprocess.run(
        list(step.command),
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    elapsed = time.perf_counter() - start
    post_state = _output_post_state(root, step.required_outputs)

    output_checks: dict[str, dict[str, Any]] = {}
    for rel in step.required_outputs:
        before = pre_state[rel]
        after = post_state[rel]
        fresh = bool(after["exists"]) and (before is None or float(after["mtime"]) > float(before))
        output_checks[rel] = {
            "exists": bool(after["exists"]),
            "fresh": fresh,
        }

    command_ok = result.returncode in step.expected_exit_codes
    outputs_ok = all(check["exists"] and check["fresh"] for check in output_checks.values())
    status = "pass" if command_ok and outputs_ok and result.returncode == 0 else "warn"
    if not command_ok or not outputs_ok:
        status = "fail"

    stdout_tail = "\n".join(result.stdout.strip().splitlines()[-12:]).strip()
    stderr_tail = "\n".join(result.stderr.strip().splitlines()[-12:]).strip()

    return {
        "step_id": step.step_id,
        "label": step.label,
        "toolchain": step.toolchain,
        "command": list(step.command),
        "exit_code": result.returncode,
        "expected_exit_codes": list(step.expected_exit_codes),
        "duration_seconds": round(elapsed, 3),
        "status": status,
        "critical": step.critical,
        "required_outputs": output_checks,
        "stdout_tail": stdout_tail,
        "stderr_tail": stderr_tail,
    }


def _load_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def markdown_check_globs() -> tuple[str, ...]:
    generated_markdown_outputs = {
        output
        for step in CYCLE_STEPS
        for output in step.required_outputs
        if output.lower().endswith(".md")
    }
    return tuple(sorted(generated_markdown_outputs | set(MARKDOWN_REFERENCE_EXTRA_GLOBS)))


def _parse_markdown_link_target(raw_target: str) -> str:
    target = raw_target.strip()
    if not target:
        return ""
    if target.startswith("<") and ">" in target:
        target = target[1 : target.find(">")].strip()
    if " " in target:
        target = target.split(None, 1)[0]
    return target.strip()


def _should_skip_link_target(target: str) -> bool:
    lowered = target.lower()
    if not lowered or lowered.startswith("#"):
        return True
    return any(lowered.startswith(prefix) for prefix in EXTERNAL_LINK_PREFIXES)


def collect_markdown_reference_issues(root: Path) -> dict[str, Any]:
    files: list[Path] = []
    for pattern in markdown_check_globs():
        files.extend(path for path in root.glob(pattern) if path.is_file())
    unique_files = sorted({path.resolve() for path in files})

    reference_issues: list[dict[str, Any]] = []
    missing_target_issues: list[dict[str, Any]] = []
    for file_path in unique_files:
        try:
            lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue

        definitions: set[str] = set()
        definition_targets: list[tuple[int, str]] = []
        in_frontmatter = False
        for line_number, line in enumerate(lines, start=1):
            if line_number == 1 and line.strip() == "---":
                in_frontmatter = True
                continue
            if in_frontmatter and line.strip() == "---":
                in_frontmatter = False
                continue
            if in_frontmatter:
                continue
            match = MARKDOWN_REF_DEF_RE.match(line)
            if match:
                definitions.add(match.group(1).strip().lower())
                target = _parse_markdown_link_target(match.group(2) or "")
                if target:
                    definition_targets.append((line_number, target))

        in_fence = False
        in_frontmatter = False
        for line_number, line in enumerate(lines, start=1):
            if line_number == 1 and line.strip() == "---":
                in_frontmatter = True
                continue
            if in_frontmatter and line.strip() == "---":
                in_frontmatter = False
                continue
            if in_frontmatter:
                continue
            if line.strip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue

            stripped_inline_code = INLINE_CODE_RE.sub("", line)
            explicit_seen: set[str] = set()
            for match in MARKDOWN_EXPLICIT_REF_RE.finditer(stripped_inline_code):
                label = (match.group(2) or match.group(1)).strip().lower()
                explicit_seen.add(label)
                if label and label not in definitions:
                    reference_issues.append(
                        {
                            "path": str(file_path.relative_to(root)).replace("\\", "/"),
                            "line": line_number,
                            "label": label,
                            "kind": "explicit_reference",
                        }
                    )

            for match in MARKDOWN_SHORTCUT_REF_RE.finditer(stripped_inline_code):
                label = match.group(1).strip().lower()
                if not label or label in {"x"}:
                    continue
                if label in definitions or label in explicit_seen:
                    continue
                reference_issues.append(
                    {
                        "path": str(file_path.relative_to(root)).replace("\\", "/"),
                        "line": line_number,
                        "label": label,
                        "kind": "shortcut_reference",
                    }
                )
            for match in MARKDOWN_INLINE_LINK_RE.finditer(stripped_inline_code):
                target = _parse_markdown_link_target(match.group(1))
                if _should_skip_link_target(target):
                    continue
                target_rel = target.split("#", 1)[0].split("?", 1)[0]
                if not target_rel:
                    continue
                resolved_target = (file_path.parent / urllib.parse.unquote(target_rel)).resolve()
                if not resolved_target.exists():
                    missing_target_issues.append(
                        {
                            "path": str(file_path.relative_to(root)).replace("\\", "/"),
                            "line": line_number,
                            "target": target_rel,
                            "kind": "missing_link_target",
                        }
                    )

        for line_number, target in definition_targets:
            if _should_skip_link_target(target):
                continue
            target_rel = target.split("#", 1)[0].split("?", 1)[0]
            if not target_rel:
                continue
            resolved_target = (file_path.parent / urllib.parse.unquote(target_rel)).resolve()
            if not resolved_target.exists():
                missing_target_issues.append(
                    {
                        "path": str(file_path.relative_to(root)).replace("\\", "/"),
                        "line": line_number,
                        "target": target_rel,
                        "kind": "missing_reference_target",
                    }
                )

    return {
        "count": len(reference_issues) + len(missing_target_issues),
        "reference_count": len(reference_issues),
        "path_count": len(missing_target_issues),
        "samples": (reference_issues + missing_target_issues)[:30],
        "files_scanned": len(unique_files),
    }


def build_profile_contract() -> dict[str, Any]:
    return {
        "profile_name": PROFILE_NAME,
        "target_name": TARGET_V1_NAME,
        "status": "candidate",
        "phase_contract": [
            {
                "step_id": step.step_id,
                "toolchain": step.toolchain,
                "command": list(step.command),
                "expected_exit_codes": list(step.expected_exit_codes),
                "critical": step.critical,
            }
            for step in CYCLE_STEPS
        ],
        "score_contract": {
            "anomaly_weights": ANOMALY_WEIGHTS,
            "minimum_tempered_for_tier2": 13,
            "required_validator_errors": 0,
            "promotion_bonus_cap": 1.5,
        },
        "gate_contract": {
            "hard_blocker_anomaly_types": list(HARD_BLOCKER_ANOMALY_TYPES),
            "governance_backlog_anomaly_types": list(GOVERNANCE_BACKLOG_ANOMALY_TYPES),
            "minimum_promotions_for_v1": MIN_PROMOTED_FOR_V1,
            "required_gates": [
                "validator_zero_errors",
                "hard_blockers_zero",
                "restart_ready",
                "forge_no_rejections",
                "stability_two_runs",
                "promotion_adoption_minimum",
                "generated_markdown_reference_clean",
                "contract_profile_frozen",
            ],
        },
    }


def sync_promotion_registry(root: Path) -> dict[str, Any]:
    graduation = _load_json_if_exists(root / "dumpster-dive/forge/tempered/GRADUATION_MANIFEST.json")
    existing = _load_json_if_exists(root / PROMOTION_REGISTRY_OUTPUT)

    recommended_paths = sorted(
        {
            str(entry.get("path", ""))
            for entry in graduation.get("artifacts", [])
            if entry.get("status") == "tempered"
            and any(token in str(entry.get("path", "")) for token in PROMOTION_LANE_TOKENS)
        }
    )

    existing_map = {
        str(entry.get("path", "")): entry
        for entry in existing.get("entries", [])
        if str(entry.get("path", ""))
    }

    entries: list[dict[str, Any]] = []
    for path in recommended_paths:
        prior = existing_map.get(path, {})
        status = str(prior.get("status", "pending")).strip().lower()
        if status not in PROMOTION_STATUSES:
            status = "pending"
        entries.append(
            {
                "path": path,
                "status": status,
                "notes": str(prior.get("notes", "")).strip(),
            }
        )

    recommended_set = set(recommended_paths)
    stale_entries = [
        entry
        for old_path, entry in existing_map.items()
        if old_path and old_path not in recommended_set
    ]

    promoted = sum(1 for entry in entries if entry["status"] == "promoted")
    payload = {
        "profile_name": PROFILE_NAME,
        "target_name": TARGET_V1_NAME,
        "required_promotions_for_v1": MIN_PROMOTED_FOR_V1,
        "summary": {
            "recommended": len(entries),
            "promoted": promoted,
            "pending": sum(1 for entry in entries if entry["status"] == "pending"),
            "deferred": sum(1 for entry in entries if entry["status"] == "deferred"),
            "rejected": sum(1 for entry in entries if entry["status"] == "rejected"),
            "ready_for_v1": promoted >= MIN_PROMOTED_FOR_V1,
        },
        "entries": entries,
        "stale_entries": stale_entries,
        "status_enum": list(PROMOTION_STATUSES),
    }
    write_json(root / PROMOTION_REGISTRY_OUTPUT, payload)
    return payload


def collect_metrics(
    root: Path,
    promotion_registry: dict[str, Any],
    markdown_reference_report: dict[str, Any],
) -> dict[str, Any]:
    extension_universe = _load_json_if_exists(root / "audit-reports/extension_universe.json")
    census = _load_json_if_exists(root / "audit-reports/wptg_filetype_census.json")
    graduation = _load_json_if_exists(root / "dumpster-dive/forge/tempered/GRADUATION_MANIFEST.json")
    validator = _load_json_if_exists(root / "audit-reports/extension_contribution_audit.json")
    ankh_scan = _load_json_if_exists(root / "audit-reports/extension_universe_ankh.json")
    ankh_census = _load_json_if_exists(root / "audit-reports/wptg_filetype_census_ankh.json")
    legacy_path = root / LEGACY_SCRIPT_REL
    legacy_present = legacy_path.exists()
    legacy_size = legacy_path.stat().st_size if legacy_present else 0
    anomaly_counts = Counter(str(entry.get("type", "unknown")) for entry in census.get("anomalies", []))
    hard_blocker_count = sum(anomaly_counts.get(kind, 0) for kind in HARD_BLOCKER_ANOMALY_TYPES)
    governance_backlog_count = sum(anomaly_counts.get(kind, 0) for kind in GOVERNANCE_BACKLOG_ANOMALY_TYPES)

    return {
        "profile_name": PROFILE_NAME,
        "codebase_extensions_unique": extension_universe.get("codebase_extensions", {}).get("total_unique", 0),
        "tracked_files": extension_universe.get("summary", {}).get("tracked_files", 0),
        "census_verdict": census.get("verdict", "UNKNOWN"),
        "census_anomaly_count": len(census.get("anomalies", [])),
        "anomaly_type_counts": dict(anomaly_counts),
        "hard_blocker_count": hard_blocker_count,
        "governance_backlog_count": governance_backlog_count,
        "forge_tempered": graduation.get("artifacts_tempered", 0),
        "forge_rejected": graduation.get("artifacts_rejected", 0),
        "validator_verdict": validator.get("verdict", "UNKNOWN"),
        "validator_errors": validator.get("error_count", 0),
        "validator_warnings": validator.get("warning_count", 0),
        "ankh_extensions_unique": ankh_scan.get("codebase_extensions", {}).get("total_unique", 0),
        "ankh_census_anomalies": len(ankh_census.get("anomalies", [])),
        "legacy_guard_present": legacy_present,
        "legacy_guard_size_bytes": legacy_size,
        "legacy_guard_path": LEGACY_SCRIPT_REL,
        "promotion_recommended": promotion_registry.get("summary", {}).get("recommended", 0),
        "promotion_promoted": promotion_registry.get("summary", {}).get("promoted", 0),
        "promotion_ready_for_v1": promotion_registry.get("summary", {}).get("ready_for_v1", False),
        "markdown_reference_issue_count": markdown_reference_report.get("count", 0),
        "markdown_reference_issue_samples": markdown_reference_report.get("samples", []),
        "markdown_reference_files_scanned": markdown_reference_report.get("files_scanned", 0),
    }


def derive_learning(previous: dict[str, Any], current: dict[str, Any], baseline_mode: bool) -> dict[str, Any]:
    prev_metrics = previous.get("metrics", {})
    if baseline_mode or not prev_metrics:
        return {
            "deltas": {
                "census_anomaly_count": 0,
                "forge_tempered": 0,
                "validator_errors": 0,
                "validator_warnings": 0,
                "markdown_reference_issue_count": 0,
            },
            "guidance": [
                "Baseline cycle established; use this snapshot as the default comparison anchor for future runs.",
                "Reverse-rarity queue is now the primary selection mode for high-effort nurturing.",
                "Validator warnings are lane-exclusion skips; treat current validator posture as operationally expected.",
            ],
        }

    deltas: dict[str, Any] = {}
    for key in (
        "census_anomaly_count",
        "forge_tempered",
        "validator_errors",
        "validator_warnings",
        "markdown_reference_issue_count",
    ):
        deltas[key] = current.get(key, 0) - prev_metrics.get(key, 0)

    guidance: list[str] = []
    if deltas["census_anomaly_count"] > 0:
        guidance.append("Anomalies increased; expand reverse-priority salvage targeting before standard promotion.")
    elif deltas["census_anomaly_count"] < 0:
        guidance.append("Anomalies dropped; preserve current reverse-priority tactics as cycle defaults.")
    else:
        guidance.append("Anomaly count stable; continue rarity-first nurturing focus.")

    if current.get("forge_tempered", 0) < 13:
        guidance.append("Forge yield below Tier 2 gate; prioritize least-viable items for next transmutation run.")
    else:
        guidance.append("Forge yield remains above Tier 2 gate; maintain provenance lanes and promotion discipline.")

    if current.get("validator_errors", 0) > 0:
        guidance.append("Validator errors present; block restart until zero-error continuation is reached.")
    elif current.get("validator_warnings", 0) > 0:
        guidance.append("Validator warnings are lane-exclusion related; continue without treating them as hard blockers.")
    else:
        guidance.append("Validator clean; restart readiness can be evaluated immediately.")

    if current.get("markdown_reference_issue_count", 0) > 0:
        guidance.append("Generated markdown reference issues detected; sanitize bracket-token shortcuts before commit.")
    else:
        guidance.append("Generated markdown reference checks are clean.")

    return {"deltas": deltas, "guidance": guidance}


def build_stability_signature(metrics: dict[str, Any], reverse_queue: dict[str, Any]) -> dict[str, Any]:
    top_extensions = [row.get("extension", "") for row in reverse_queue.get("extension_priority", [])[:10]]
    top_files = [row.get("path", "") for row in reverse_queue.get("file_priority", [])[:10]]
    return {
        "census_anomaly_count": int(metrics.get("census_anomaly_count", 0)),
        "hard_blocker_count": int(metrics.get("hard_blocker_count", 0)),
        "governance_backlog_count": int(metrics.get("governance_backlog_count", 0)),
        "forge_tempered": int(metrics.get("forge_tempered", 0)),
        "forge_rejected": int(metrics.get("forge_rejected", 0)),
        "validator_errors": int(metrics.get("validator_errors", 0)),
        "validator_warnings": int(metrics.get("validator_warnings", 0)),
        "markdown_reference_issue_count": int(metrics.get("markdown_reference_issue_count", 0)),
        "top_extensions": top_extensions,
        "top_files": top_files,
    }


def evaluate_gate_model(
    cycle_data: dict[str, Any],
    previous_state: dict[str, Any],
    reverse_queue: dict[str, Any],
    contract_profile: dict[str, Any],
) -> dict[str, Any]:
    metrics = cycle_data["metrics"]
    restart_ready = bool(cycle_data.get("restart_readiness", {}).get("ready", False))
    current_signature = build_stability_signature(metrics, reverse_queue)
    previous_signature = previous_state.get("gate_model", {}).get("stability_signature")
    stability_ok = bool(previous_signature) and previous_signature == current_signature

    gates = [
        {
            "id": "validator_zero_errors",
            "passed": metrics.get("validator_errors", 0) == 0,
            "value": metrics.get("validator_errors", 0),
            "required": 0,
        },
        {
            "id": "hard_blockers_zero",
            "passed": metrics.get("hard_blocker_count", 0) == 0,
            "value": metrics.get("hard_blocker_count", 0),
            "required": 0,
        },
        {
            "id": "restart_ready",
            "passed": restart_ready,
            "value": restart_ready,
            "required": True,
        },
        {
            "id": "forge_no_rejections",
            "passed": metrics.get("forge_rejected", 0) == 0,
            "value": metrics.get("forge_rejected", 0),
            "required": 0,
        },
        {
            "id": "stability_two_runs",
            "passed": stability_ok,
            "value": "matched" if stability_ok else "mismatch_or_missing_previous_signature",
            "required": "two_consecutive_identical_signatures",
        },
        {
            "id": "promotion_adoption_minimum",
            "passed": metrics.get("promotion_promoted", 0) >= MIN_PROMOTED_FOR_V1,
            "value": metrics.get("promotion_promoted", 0),
            "required": MIN_PROMOTED_FOR_V1,
        },
        {
            "id": "generated_markdown_reference_clean",
            "passed": metrics.get("markdown_reference_issue_count", 0) == 0,
            "value": metrics.get("markdown_reference_issue_count", 0),
            "required": 0,
        },
        {
            "id": "contract_profile_frozen",
            "passed": contract_profile.get("profile_name") == PROFILE_NAME,
            "value": contract_profile.get("profile_name"),
            "required": PROFILE_NAME,
        },
    ]
    blockers = [gate["id"] for gate in gates if not gate["passed"]]

    anomaly_counts = metrics.get("anomaly_type_counts", {})
    dominant_anomalies = sorted(anomaly_counts.items(), key=lambda item: (-item[1], item[0]))[:3]
    findings: list[str] = []
    if dominant_anomalies:
        rendered = ", ".join(f"{name}={count}" for name, count in dominant_anomalies)
        findings.append(f"Dominant anomaly types: {rendered}.")
    if metrics.get("governance_backlog_count", 0) > metrics.get("hard_blocker_count", 0):
        findings.append("Backlog pressure is governance-heavy; critical risk concentration is comparatively low.")
    if metrics.get("hard_blocker_count", 0) > 0:
        findings.append("Hard blockers remain; keep profile in candidate mode until count reaches zero.")
    promoted = metrics.get("promotion_promoted", 0)
    if promoted < MIN_PROMOTED_FOR_V1:
        findings.append(
            f"Promotion adoption shortfall: {promoted}/{MIN_PROMOTED_FOR_V1} required promoted artifacts."
        )
    markdown_issues = metrics.get("markdown_reference_issue_count", 0)
    if markdown_issues > 0:
        sample = metrics.get("markdown_reference_issue_samples", [])
        if sample:
            first = sample[0]
            findings.append(
                f"Markdown shortcut reference issue sample: {first.get('path')}:{first.get('line')} [{first.get('label')}]."
            )
        findings.append("Generated markdown contains unresolved shortcut/reference labels; fix before commit.")

    return {
        "profile_name": PROFILE_NAME,
        "target_name": TARGET_V1_NAME,
        "status": "candidate",
        "ready_for_v1": not blockers,
        "gates": gates,
        "blockers": blockers,
        "hard_blocker_types": list(HARD_BLOCKER_ANOMALY_TYPES),
        "governance_backlog_types": list(GOVERNANCE_BACKLOG_ANOMALY_TYPES),
        "promotion_registry_reference": str(PROMOTION_REGISTRY_OUTPUT).replace("\\", "/"),
        "contract_reference": str(PROFILE_CONTRACT_OUTPUT).replace("\\", "/"),
        "stability_signature": current_signature,
        "additional_findings": findings,
    }


def compute_scoring(results: list[dict[str, Any]], metrics: dict[str, Any]) -> dict[str, Any]:
    penalties = 0.0
    boon = 0.0

    step_by_id = {result["step_id"]: result for result in results}
    if step_by_id.get("phase_0_universe", {}).get("status") == "pass":
        boon += 1.0
    elif step_by_id.get("phase_0_universe", {}).get("status") == "warn":
        boon += 0.5

    census_verdict = metrics.get("census_verdict", "UNKNOWN")
    if census_verdict == "PASS":
        boon += 2.0
    elif census_verdict == "WARN":
        boon += 1.0
    elif census_verdict == "FAIL":
        penalties += 1.0

    if metrics.get("forge_tempered", 0) >= 13 and metrics.get("forge_rejected", 0) == 0:
        boon += 4.0
    elif metrics.get("forge_tempered", 0) > 0:
        boon += 1.0
    else:
        penalties += 2.0

    oxidized_steps = (
        "part_3_ankh_scan",
        "part_3_ankh_census",
        "part_3_ankh_landscape",
        "part_3_ankh_eol",
    )
    if all(step_by_id.get(step, {}).get("status") == "pass" for step in oxidized_steps):
        boon += 3.0
    else:
        penalties += 1.0

    if metrics.get("validator_errors", 0) == 0:
        boon += 2.0
    else:
        penalties += float(metrics.get("validator_errors", 0))

    warnings = metrics.get("validator_warnings", 0)
    if warnings:
        penalties += min(1.0, warnings * 0.1)
    markdown_issues = int(metrics.get("markdown_reference_issue_count", 0))
    if markdown_issues:
        penalties += min(2.0, markdown_issues * 0.05)

    promoted_count = int(metrics.get("promotion_promoted", 0))
    promotion_bonus = min(1.5, promoted_count * 0.5)
    boon += promotion_bonus

    return {
        "penalty_total": round(penalties, 2),
        "boon_total": round(boon, 2),
        "net_score": round(boon - penalties, 2),
        "components": {
            "phase_0_boon": 1.0 if step_by_id.get("phase_0_universe", {}).get("status") == "pass" else 0.5,
            "part_1_verdict": census_verdict,
            "part_2_tempered": metrics.get("forge_tempered", 0),
            "part_3_all_passed": all(step_by_id.get(step, {}).get("status") == "pass" for step in oxidized_steps),
            "part_4_validator_errors": metrics.get("validator_errors", 0),
            "markdown_reference_issues": markdown_issues,
            "stage_3_promotion_bonus": promotion_bonus,
            "promotions_counted": promoted_count,
        },
    }


def cycle_verdict(results: list[dict[str, Any]], metrics: dict[str, Any]) -> str:
    if any(result["status"] == "fail" and result["critical"] for result in results):
        return "FAIL"
    if metrics.get("validator_errors", 0) > 0:
        return "FAIL"
    if any(result["status"] == "warn" for result in results):
        return "WARN"
    if metrics.get("census_verdict") in {"WARN", "FAIL"}:
        return "WARN"
    if metrics.get("validator_warnings", 0) > 0:
        return "WARN"
    return "PASS"


def assess_restart_readiness(snapshot: dict[str, Any]) -> dict[str, Any]:
    metrics = snapshot.get("metrics", {})
    results = snapshot.get("results", [])
    blockers: list[str] = []
    notes: list[str] = []

    if not results:
        blockers.append("No cycle results found; run a continuation cycle first.")
    if metrics.get("validator_errors", 1) > 0:
        blockers.append("Validator has non-zero errors.")
    if metrics.get("forge_tempered", 0) < 13:
        blockers.append("Forge tempered yield below Tier 2 minimum (13).")
    if not metrics.get("legacy_guard_present", False):
        blockers.append(f"Legacy salvage guard missing: {metrics.get('legacy_guard_path', LEGACY_SCRIPT_REL)}")
    if metrics.get("markdown_reference_issue_count", 0) > 0:
        blockers.append("Generated markdown has unresolved reference-style labels.")
    if any(result.get("critical") and result.get("status") == "fail" for result in results):
        blockers.append("At least one critical step failed in the most recent cycle.")

    oxidized_ids = {"part_3_ankh_scan", "part_3_ankh_census", "part_3_ankh_landscape", "part_3_ankh_eol"}
    oxidized_results = [result for result in results if result.get("step_id") in oxidized_ids]
    if oxidized_results and any(result.get("status") != "pass" for result in oxidized_results):
        blockers.append("Oxidized stage has non-pass substeps.")

    if metrics.get("census_anomaly_count", 0) > 0:
        notes.append("Census anomalies exist; they are handled via reverse-rarity-first priority.")
    if metrics.get("hard_blocker_count", 0) > 0:
        notes.append(
            f"Hard blocker anomalies present ({metrics.get('hard_blocker_count', 0)}); profile remains {PROFILE_NAME}."
        )
    if metrics.get("validator_warnings", 0) > 0:
        notes.append("Validator warnings are currently lane-exclusion skips.")
    notes.append(
        f"Generated markdown reference scan: {metrics.get('markdown_reference_issue_count', 0)} issues across {metrics.get('markdown_reference_files_scanned', 0)} files."
    )
    if metrics.get("legacy_guard_present", False):
        notes.append(
            f"Legacy salvage guard preserved: {metrics.get('legacy_guard_path', LEGACY_SCRIPT_REL)} ({metrics.get('legacy_guard_size_bytes', 0)} bytes)."
        )

    return {"ready": not blockers, "blockers": blockers, "notes": notes}


def build_reverse_viability_queue(root: Path, limit: int = 64) -> dict[str, Any]:
    extension_universe = _load_json_if_exists(root / "audit-reports/extension_universe.json")
    census = _load_json_if_exists(root / "audit-reports/wptg_filetype_census.json")

    inventory = extension_universe.get("codebase_extensions", {}).get("inventory", {})
    by_extension = census.get("by_extension", {})
    anomalies = census.get("anomalies", [])

    all_extensions = sorted(set(inventory) | set(by_extension))
    counts = [int(inventory.get(ext, {}).get("count", by_extension.get(ext, {}).get("count", 0))) for ext in all_extensions]
    max_count = max(counts) if counts else 1

    extension_rows: list[dict[str, Any]] = []
    priority_map: dict[str, float] = {}
    for extension in all_extensions:
        inv = inventory.get(extension, {})
        ext_count = int(inv.get("count", by_extension.get(extension, {}).get("count", 0)))
        anomaly_map = by_extension.get(extension, {}).get("anomalies", {})
        anomaly_count = int(sum(int(value) for value in anomaly_map.values()))
        runtime_supported = bool(inv.get("runtime_support", {}).get("supported", True))
        category = inv.get("category", "unknown")

        rarity_ratio = 1.0 - min(1.0, (ext_count / max_count if max_count else 0.0))
        anomaly_density = min(1.0, anomaly_count / max(ext_count, 1))
        runtime_penalty = 0.0 if runtime_supported else 1.0
        rarity_bonus = 0.1 if ext_count <= 2 else 0.0
        category_bonus = 0.1 if category in {"unclassified", "build_output", "governance", "damaged", "unknown"} else 0.0

        risk = min(1.0, 0.5 * rarity_ratio + 0.3 * anomaly_density + 0.2 * runtime_penalty + rarity_bonus + category_bonus)
        viability = max(0.0, 1.0 - risk)
        effort_priority = round(risk * 10.0, 2)
        priority_map[extension] = effort_priority

        extension_rows.append(
            {
                "extension": extension,
                "count": ext_count,
                "anomaly_count": anomaly_count,
                "category": category,
                "runtime_supported": runtime_supported,
                "rarity_ratio": round(rarity_ratio, 4),
                "viability_score": round(viability, 4),
                "reverse_effort_priority": effort_priority,
            }
        )

    extension_rows.sort(key=lambda row: (-row["reverse_effort_priority"], row["count"], -row["anomaly_count"], row["extension"]))
    for index, row in enumerate(extension_rows, start=1):
        row["reverse_rank"] = index

    file_rows: list[dict[str, Any]] = []
    for anomaly in anomalies:
        path = str(anomaly.get("path", ""))
        extension = compound_extension(path) or "[no_ext]"
        anomaly_type = str(anomaly.get("type", "unknown"))
        base = priority_map.get(extension, 0.0)
        weight = ANOMALY_WEIGHTS.get(anomaly_type, 1.0)
        file_rows.append(
            {
                "path": path,
                "extension": extension,
                "anomaly_type": anomaly_type,
                "reverse_effort_score": round(base + weight, 2),
            }
        )
    file_rows.sort(key=lambda row: (-row["reverse_effort_score"], row["path"]))

    return {
        "timestamp": now_iso(),
        "perspective": "reverse_rarity_first",
        "selection_principle": "least_viable_first",
        "extension_priority": extension_rows[: max(1, limit)],
        "file_priority": file_rows[: max(1, limit * 2)],
        "summary": {
            "extensions_ranked": len(extension_rows),
            "anomaly_files_ranked": len(file_rows),
            "highest_effort_extension": extension_rows[0]["extension"] if extension_rows else None,
            "highest_effort_file": file_rows[0]["path"] if file_rows else None,
        },
    }


def build_default_view(
    cycle_data: dict[str, Any],
    reverse_queue: dict[str, Any],
    reverse_output_path: Path,
) -> dict[str, Any]:
    metrics = cycle_data["metrics"]
    learning = cycle_data["learning"]
    score = cycle_data["score"]
    verdict = cycle_data["verdict"]
    top_extensions = reverse_queue.get("extension_priority", [])[:10]
    top_files = reverse_queue.get("file_priority", [])[:10]

    return {
        "timestamp": now_iso(),
        "profile_name": PROFILE_NAME,
        "default_mode": "renewal_loop_reverse_rarity_first",
        "cycle_verdict": verdict,
        "score": score,
        "restart_readiness": cycle_data["restart_readiness"],
        "gate_model": {
            "status": cycle_data.get("gate_model", {}).get("status", "candidate"),
            "ready_for_v1": cycle_data.get("gate_model", {}).get("ready_for_v1", False),
            "blockers": cycle_data.get("gate_model", {}).get("blockers", []),
        },
        "status_snapshot": {
            "extensions_unique": metrics.get("codebase_extensions_unique", 0),
            "tracked_files": metrics.get("tracked_files", 0),
            "census_anomalies": metrics.get("census_anomaly_count", 0),
            "hard_blockers": metrics.get("hard_blocker_count", 0),
            "governance_backlog": metrics.get("governance_backlog_count", 0),
            "forge_tempered": metrics.get("forge_tempered", 0),
            "validator_errors": metrics.get("validator_errors", 0),
            "validator_warnings": metrics.get("validator_warnings", 0),
            "promotion_recommended": metrics.get("promotion_recommended", 0),
            "promotion_promoted": metrics.get("promotion_promoted", 0),
            "markdown_reference_issues": metrics.get("markdown_reference_issue_count", 0),
        },
        "legacy_guard": {
            "path": metrics.get("legacy_guard_path", LEGACY_SCRIPT_REL),
            "present": bool(metrics.get("legacy_guard_present", False)),
            "size_bytes": int(metrics.get("legacy_guard_size_bytes", 0)),
        },
        "contract_reference": str(PROFILE_CONTRACT_OUTPUT).replace("\\", "/"),
        "promotion_registry_reference": str(PROMOTION_REGISTRY_OUTPUT).replace("\\", "/"),
        "reverse_priority_reference": str(reverse_output_path).replace("\\", "/"),
        "reverse_priority_top_extensions": top_extensions,
        "reverse_priority_top_files": top_files,
        "learning_guidance": learning["guidance"],
        "next_cycle_focus": [
            "Apply least-viable-first triage before common-path optimizations.",
            "Run Phase 0 -> Part 4 sequentially with lane exclusions preserved.",
            "Invest highest effort in top reverse-priority files regardless of filetype.",
            "Restart only when readiness gate remains green.",
        ],
    }


def render_report(cycle_data: dict[str, Any], reverse_queue: dict[str, Any], report_path: Path) -> str:
    lines = [
        "# WPTG Repeatable Cycle Report",
        "",
        f"- Profile: `{PROFILE_NAME}`",
        f"- Timestamp: `{cycle_data['timestamp']}`",
        f"- Cycle ID: `{cycle_data['cycle_id']}`",
        f"- Begin Anew Mode: `{cycle_data['begin_anew']}`",
        f"- Execution Mode: `{cycle_data['execution_mode']}`",
        f"- Verdict: `{cycle_data['verdict']}`",
        "",
        "## Restart Readiness",
        "",
        f"- Ready for restart: `{cycle_data['restart_readiness']['ready']}`",
    ]
    blockers = cycle_data["restart_readiness"]["blockers"]
    notes = cycle_data["restart_readiness"]["notes"]
    if blockers:
        lines.append("- Blockers:")
        lines.extend(f"  - {blocker}" for blocker in blockers)
    if notes:
        lines.append("- Notes:")
        lines.extend(f"  - {note}" for note in notes)

    legacy_path = cycle_data["metrics"].get("legacy_guard_path", LEGACY_SCRIPT_REL)
    legacy_present = cycle_data["metrics"].get("legacy_guard_present", False)
    legacy_size = cycle_data["metrics"].get("legacy_guard_size_bytes", 0)
    lines.extend(
        [
            "",
            "## Legacy Guard",
            "",
            f"- Path: {markdown_path_link(legacy_path, report_path)}",
            f"- Present: `{legacy_present}`",
            f"- Size bytes: `{legacy_size}`",
        ]
    )

    lines.extend(
        [
            "",
            "## Step Results",
            "",
            "| Step | Toolchain | Exit | Status | Duration(s) |",
            "|---|---|---:|---|---:|",
        ]
    )
    for result in cycle_data["results"]:
        lines.append(
            f"| {result['step_id']} | {result['toolchain']} | {result['exit_code']} | {result['status']} | {result['duration_seconds']:.3f} |"
        )

    metrics = cycle_data["metrics"]
    lines.extend(
        [
            "",
            "## Metrics",
            "",
            f"- Extensions unique: `{metrics['codebase_extensions_unique']}`",
            f"- Tracked files: `{metrics['tracked_files']}`",
            f"- Census verdict/anomalies: `{metrics['census_verdict']}` / `{metrics['census_anomaly_count']}`",
            f"- Hard blockers/governance backlog: `{metrics['hard_blocker_count']}` / `{metrics['governance_backlog_count']}`",
            f"- Forge tempered/rejected: `{metrics['forge_tempered']}` / `{metrics['forge_rejected']}`",
            f"- Validator verdict/errors/warnings: `{metrics['validator_verdict']}` / `{metrics['validator_errors']}` / `{metrics['validator_warnings']}`",
            f"- Promotion recommended/promoted: `{metrics['promotion_recommended']}` / `{metrics['promotion_promoted']}`",
            f"- Markdown reference issues: `{metrics['markdown_reference_issue_count']}`",
            "",
            "## Candidate Gates",
            "",
        ]
    )
    gate_model = cycle_data.get("gate_model", {})
    lines.extend(
        [
            f"- Ready for {TARGET_V1_NAME}: `{gate_model.get('ready_for_v1', False)}`",
            "",
            "| Gate | Passed | Value | Required |",
            "|---|---|---|---|",
        ]
    )
    for gate in gate_model.get("gates", []):
        lines.append(f"| {gate['id']} | {gate['passed']} | `{gate['value']}` | `{gate['required']}` |")
    if gate_model.get("blockers"):
        lines.append("")
        lines.append("- Blocking gates:")
        lines.extend(f"  - `{gate_id}`" for gate_id in gate_model["blockers"])
    if gate_model.get("additional_findings"):
        lines.append("")
        lines.append("- Additional findings:")
        lines.extend(f"  - {finding}" for finding in gate_model["additional_findings"])

    lines.extend(
        [
            "",
            "## Reverse-Rarity Priority (Top 10 Extensions)",
            "",
            "| Rank | Ext | Count | Anomalies | Effort | Viability |",
            "|---:|---|---:|---:|---:|---:|",
        ]
    )
    for row in reverse_queue.get("extension_priority", [])[:10]:
        lines.append(
            f"| {row['reverse_rank']} | `{row['extension']}` | {row['count']} | {row['anomaly_count']} | {row['reverse_effort_priority']:.2f} | {row['viability_score']:.4f} |"
        )

    lines.extend(["", "## Reverse-Rarity Priority (Top 10 Files)", ""])
    for row in reverse_queue.get("file_priority", [])[:10]:
        path_link = markdown_path_link(row["path"], report_path)
        lines.append(
            f"- `{row['reverse_effort_score']:.2f}` | `{row['anomaly_type']}` | {path_link}"
        )

    lines.extend(["", "## Learning Deltas", ""])
    for key, value in cycle_data["learning"]["deltas"].items():
        lines.append(f"- `{key}` delta: `{value}`")

    lines.extend(["", "## Guidance", ""])
    for guidance in cycle_data["learning"]["guidance"]:
        lines.append(f"- {guidance}")

    score = cycle_data["score"]
    lines.extend(
        [
            "",
            "## Boon/Penalty",
            "",
            f"- Boon total: `{score['boon_total']}`",
            f"- Penalty total: `{score['penalty_total']}`",
            f"- Net score: `{score['net_score']}`",
        ]
    )
    return "\n".join(lines)


def verdict_exit_code(verdict: str) -> int:
    if verdict == "FAIL":
        return 2
    if verdict == "WARN":
        return 1
    return 0


def execute_single_cycle(
    root: Path,
    args: argparse.Namespace,
    previous_state: dict[str, Any],
    begin_anew: bool,
    execution_mode: str,
) -> dict[str, Any]:
    previous_cycle_id = int(previous_state.get("cycle_id", 0)) if previous_state else 0
    cycle_id = 1 if begin_anew or previous_cycle_id == 0 else previous_cycle_id + 1

    results = [run_step(root, step) for step in CYCLE_STEPS]
    contract_profile = build_profile_contract()
    write_json(root / PROFILE_CONTRACT_OUTPUT, contract_profile)
    promotion_registry = sync_promotion_registry(root)
    markdown_reference_report = collect_markdown_reference_issues(root)
    metrics = collect_metrics(root, promotion_registry, markdown_reference_report)
    learning = derive_learning(previous_state, metrics, begin_anew)
    score = compute_scoring(results, metrics)
    verdict = cycle_verdict(results, metrics)

    cycle_data = {
        "timestamp": now_iso(),
        "profile_name": PROFILE_NAME,
        "cycle_id": cycle_id,
        "begin_anew": begin_anew,
        "execution_mode": execution_mode,
        "verdict": verdict,
        "results": results,
        "metrics": metrics,
        "learning": learning,
        "score": score,
        "previous_cycle_reference": {
            "cycle_id": previous_state.get("cycle_id"),
            "verdict": previous_state.get("verdict"),
            "timestamp": previous_state.get("timestamp"),
        },
        "profile_contract_reference": str(PROFILE_CONTRACT_OUTPUT).replace("\\", "/"),
        "promotion_registry_reference": str(PROMOTION_REGISTRY_OUTPUT).replace("\\", "/"),
    }
    cycle_data["restart_readiness"] = assess_restart_readiness(cycle_data)

    reverse_queue = build_reverse_viability_queue(root, limit=args.reverse_limit)
    cycle_data["gate_model"] = evaluate_gate_model(cycle_data, previous_state, reverse_queue, contract_profile)
    default_view = build_default_view(cycle_data, reverse_queue, args.reverse_output)

    write_json(root / args.state_output, cycle_data)
    write_json(root / args.default_view_output, default_view)
    write_json(root / args.reverse_output, reverse_queue)
    write_text(root / args.report_output, render_report(cycle_data, reverse_queue, args.report_output))

    print(f"Wrote {args.state_output}")
    print(f"Wrote {args.default_view_output}")
    print(f"Wrote {args.reverse_output}")
    print(f"Wrote {args.report_output}")
    print(f"Wrote {PROFILE_CONTRACT_OUTPUT}")
    print(f"Wrote {PROMOTION_REGISTRY_OUTPUT}")
    return cycle_data


def main() -> int:
    ensure_utf8()
    parser = argparse.ArgumentParser(description="Execute repeatable WPTG cycle framework.")
    parser.add_argument(
        "--begin-anew",
        action="store_true",
        help="Start a fresh cycle baseline while preserving prior cycle memory.",
    )
    parser.add_argument(
        "--auto-restart",
        action="store_true",
        help="If ready, restart immediately; otherwise run continuation first and restart when readiness turns green.",
    )
    parser.add_argument(
        "--state-output",
        type=Path,
        default=Path("audit-reports/wptg_cycle_state.json"),
        help="Cycle state JSON output path.",
    )
    parser.add_argument(
        "--default-view-output",
        type=Path,
        default=Path("audit-reports/wptg_default_view.json"),
        help="Default-view JSON output path.",
    )
    parser.add_argument(
        "--reverse-output",
        type=Path,
        default=Path("audit-reports/wptg_reverse_viability_queue.json"),
        help="Reverse-rarity-first priority queue JSON output path.",
    )
    parser.add_argument(
        "--reverse-limit",
        type=int,
        default=64,
        help="Maximum number of extension rows in reverse-rarity queue output.",
    )
    parser.add_argument(
        "--report-output",
        type=Path,
        default=Path("codex/mailbox/WPTG_REPEATABLE_CYCLE_REPORT.md"),
        help="Markdown report output path.",
    )
    args = parser.parse_args()

    root = repo_root()
    state_path = root / args.state_output
    previous_state = _load_json_if_exists(state_path) if state_path.exists() else {}

    if args.auto_restart:
        readiness = assess_restart_readiness(previous_state)
        if readiness["ready"]:
            final_cycle = execute_single_cycle(
                root=root,
                args=args,
                previous_state=previous_state,
                begin_anew=True,
                execution_mode="auto_restart_ready_now",
            )
            return verdict_exit_code(final_cycle["verdict"])

        continuation_cycle = execute_single_cycle(
            root=root,
            args=args,
            previous_state=previous_state,
            begin_anew=False,
            execution_mode="auto_restart_continuation_before_restart",
        )
        if continuation_cycle["restart_readiness"]["ready"]:
            final_cycle = execute_single_cycle(
                root=root,
                args=args,
                previous_state=continuation_cycle,
                begin_anew=True,
                execution_mode="auto_restart_after_continuation",
            )
            return verdict_exit_code(final_cycle["verdict"])
        return verdict_exit_code(continuation_cycle["verdict"])

    execution_mode = "manual_begin_anew" if args.begin_anew else "manual_continuation"
    cycle_data = execute_single_cycle(
        root=root,
        args=args,
        previous_state=previous_state,
        begin_anew=args.begin_anew,
        execution_mode=execution_mode,
    )
    return verdict_exit_code(cycle_data["verdict"])


if __name__ == "__main__":
    raise SystemExit(main())
