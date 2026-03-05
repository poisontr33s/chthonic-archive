#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WPTG filetype census, log archaeology, and governance proposal generator.

@SID:           WPTG_FILETYPE_CENSUS_V1
@Shabti:        CLI Script
@Purpose:       Generate Part 1 census outputs, log triage, orphan JSON tracing, and governance proposals.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.wptg_common import (
    baseline_gold_tier,
    compound_extension,
    ensure_utf8,
    is_textlike,
    markdown_path_link,
    now_iso,
    path_is_excluded,
    repo_root,
    safe_read_text,
    tracked_files,
    write_json,
    write_text,
)


SECRETS_HINT_RE = re.compile(r"(key|token|secret|password|api[_-]?key)", re.IGNORECASE)
PLACEHOLDER_RE = re.compile(r"^(?:<[^>]+>|\$\{[^}]+\}|changeme|todo|tbd|example|placeholder)$", re.IGNORECASE)
ERROR_LINE_RE = re.compile(r"(?i)\b(error|failed|exception|traceback|panic|fatal)\b")
TIMESTAMP_KEY_RE = re.compile(r"(date|time|timestamp|generated|created|updated)", re.IGNORECASE)
GENERIC_JSON_BASENAMES = {
    "expected.json",
    "package.json",
    "tsconfig.json",
    "settings.json",
    "launch.json",
}


@dataclass(slots=True)
class FileRecord:
    path: str
    extension: str
    gold_tier: str
    anomalies: list[dict[str, str]]


def extension_key(path: str) -> str:
    return compound_extension(path) or "[no_ext]"


def classify_env(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    anomalies: list[dict[str, str]] = []
    variables: list[str] = []
    content = safe_read_text(path, limit_bytes=200_000) or ""
    substantive = 0

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        variables.append(key)
        if value and not PLACEHOLDER_RE.match(value):
            substantive += 1

    if substantive:
        anomalies.append(
            {
                "type": "tracked_env_surface",
                "recommendation": "extract_schema_and_integration_map",
                "wptg_rationale": "The variable contract is gold; live values should not be the tracked artifact.",
            }
        )
    return anomalies, variables


def classify_file(root: Path, rel_path: str) -> FileRecord:
    path = root / rel_path
    extension = extension_key(rel_path)
    anomalies: list[dict[str, str]] = []
    gold_tier = baseline_gold_tier(extension)
    name = path.name
    normalized = rel_path.replace("\\", "/")

    if extension in {".pyc", ".cpython-313.pyc", ".cpython-314.pyc"}:
        anomalies.append(
            {
                "type": "tracked_bytecode",
                "recommendation": "extract_contract_then_ignore",
                "wptg_rationale": "Bytecode is derivative output; preserve interface signal, not the cache artifact.",
            }
        )

    if extension == ".env":
        env_anomalies, _ = classify_env(path)
        anomalies.extend(env_anomalies)

    if extension == ".off" or name.startswith(".bak") or " - Copy." in name:
        anomalies.append(
            {
                "type": "disabled_by_rename",
                "recommendation": "extract_pattern_then_govern",
                "wptg_rationale": "Dormant logic should be governed by intent and templates, not filename mutation.",
            }
        )

    if extension == '.md"' or any(ord(char) > 127 for char in normalized):
        anomalies.append(
            {
                "type": "filename_encoding_damage",
                "recommendation": "repair_with_provenance_copy",
                "wptg_rationale": "The content remains gold, but the path has become unreliable and needs a traced repair proposal.",
            }
        )

    if extension == ".md" and normalized.startswith("scripts/"):
        anomalies.append(
            {
                "type": "filetype_directory_mismatch",
                "recommendation": "rehome_to_docs_or_mailbox",
                "wptg_rationale": "Documentation in execution lanes obscures operational ownership and should be proposed for canonical placement.",
            }
        )

    if extension == ".log" and normalized.startswith("codex/mailbox/"):
        anomalies.append(
            {
                "type": "filetype_directory_mismatch",
                "recommendation": "extract_signal_then_archive_menu",
                "wptg_rationale": "Mailbox logs are derivative evidence and should be separated from active handoff packets by proposal, not deletion.",
            }
        )

    if extension == ".bat":
        anomalies.append(
            {
                "type": "legacy_batch_in_pwsh_repo",
                "recommendation": "transliterate_to_powershell",
                "wptg_rationale": "The automation logic is gold, but the repo's canonical shell is PowerShell.",
            }
        )

    if anomalies:
        gold_tier = "raw_unrefined"

    return FileRecord(path=rel_path, extension=extension, gold_tier=gold_tier, anomalies=anomalies)


def load_text_cache(root: Path, paths: list[str]) -> dict[str, str]:
    cache: dict[str, str] = {}
    for rel_path in paths:
        if not is_textlike(rel_path):
            continue
        text = safe_read_text(root / rel_path, limit_bytes=1_500_000)
        if text is None:
            continue
        cache[rel_path] = text
    return cache


def detect_references(target_path: str, basename: str, text_cache: dict[str, str]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    normalized_target = target_path.replace("\\", "/").lower()
    basename_lower = basename.lower()
    basename_patterns = [
        f'"{basename_lower}"',
        f"'{basename_lower}'",
        f"`{basename_lower}`",
        f"/{basename_lower}",
        f"\\{basename_lower}",
    ]

    for ref_path, content in text_cache.items():
        if ref_path == target_path:
            continue
        lowered = content.lower()
        match_value = None
        if normalized_target in lowered or f"./{normalized_target}" in lowered:
            match_value = normalized_target
        elif basename_lower not in GENERIC_JSON_BASENAMES:
            for pattern in basename_patterns:
                if pattern in lowered:
                    match_value = pattern
                    break
        if match_value:
            refs.append({"path": ref_path, "match": match_value})
        if len(refs) >= 20:
            break
    return refs


def extract_timestamp_fields(payload: Any, prefix: str = "") -> dict[str, Any]:
    found: dict[str, Any] = {}
    if isinstance(payload, dict):
        for key, value in payload.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if TIMESTAMP_KEY_RE.search(key):
                found[full_key] = value
            found.update(extract_timestamp_fields(value, full_key))
    elif isinstance(payload, list):
        for index, item in enumerate(payload[:10]):
            full_key = f"{prefix}[{index}]"
            found.update(extract_timestamp_fields(item, full_key))
    return found


def recognized_artifact_path(path: str) -> bool:
    prefixes = (
        "codex/mailbox/",
        "claude/mailbox/",
        "gemini/mailbox/",
        ".temple/session-archives/",
        ".temple/handoffs/",
        "dumpster-dive/forge/",
    )
    return path.replace("\\", "/").startswith(prefixes)


def build_orphan_reconciliation(root: Path, eligible_paths: list[str], text_cache: dict[str, str]) -> dict:
    now = datetime.now(UTC)
    entries: list[dict[str, Any]] = []
    orphan_candidates: list[dict[str, Any]] = []

    for rel_path in eligible_paths:
        full_path = root / rel_path
        basename = full_path.name
        references = detect_references(rel_path, basename, text_cache)
        text = safe_read_text(full_path, limit_bytes=1_500_000)
        timestamp_fields: dict[str, Any] = {}
        json_parse_error = None
        if text is not None:
            try:
                payload = json.loads(text)
                timestamp_fields = extract_timestamp_fields(payload)
            except json.JSONDecodeError as exc:
                json_parse_error = str(exc)

        modified_at = datetime.fromtimestamp(full_path.stat().st_mtime, UTC)
        age_days = int((now - modified_at).total_seconds() // 86400)
        orphan = not references and not recognized_artifact_path(rel_path) and age_days > 30
        entry = {
            "path": rel_path,
            "references": references,
            "reference_count": len(references),
            "modified_at": modified_at.replace(microsecond=0).isoformat(),
            "age_days": age_days,
            "timestamp_fields": timestamp_fields,
            "recognized_artifact_format": recognized_artifact_path(rel_path),
            "json_parse_error": json_parse_error,
            "orphan_candidate": orphan,
        }
        entries.append(entry)
        if orphan:
            orphan_candidates.append(entry)

    return {
        "timestamp": now_iso(),
        "total_json_files": len(eligible_paths),
        "orphan_candidate_count": len(orphan_candidates),
        "orphan_candidates": orphan_candidates,
        "reference_traces": entries,
    }


def classify_log(path: str, text: str) -> dict[str, Any]:
    lowered = text.lower()
    if any(token in lowered for token in ("cuda", "nvcc", "gpu", "nvidia")):
        category = "cuda_or_gpu"
    elif any(token in lowered for token in ("build", "compile", "cargo", "bun build", "msbuild", "linker")):
        category = "build_or_compile"
    elif any(token in lowered for token in ("audit", "validate", "verification", "policy", "census", "scan")):
        category = "validation_or_audit"
    elif any(token in lowered for token in ("traceback", "exception", "panic", "runtime")):
        category = "runtime_or_failure"
    else:
        category = "environment_or_misc"

    signal_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if ERROR_LINE_RE.search(stripped) or "version" in stripped.lower():
            signal_lines.append(stripped[:180])
        if len(signal_lines) >= 5:
            break

    recommendation = "preserve"
    if len(signal_lines) <= 1 and len(text.splitlines()) < 20:
        recommendation = "extract_then_archive"
    if category == "environment_or_misc" and len(signal_lines) <= 1:
        recommendation = "proposal_untrack_after_extraction"

    return {
        "path": path,
        "category": category,
        "signal_lines": signal_lines,
        "signal_count": len(signal_lines),
        "recommendation": recommendation,
    }


def build_log_archaeology(root: Path, log_paths: list[str], output_path: Path) -> tuple[dict[str, Any], str]:
    results: list[dict[str, Any]] = []
    category_counts: Counter[str] = Counter()
    recommendation_counts: Counter[str] = Counter()
    unique_patterns: Counter[str] = Counter()

    for rel_path in log_paths:
        text = safe_read_text(root / rel_path, limit_bytes=2_000_000) or ""
        analysis = classify_log(rel_path, text)
        results.append(analysis)
        category_counts[analysis["category"]] += 1
        recommendation_counts[analysis["recommendation"]] += 1
        for line in analysis["signal_lines"]:
            unique_patterns[line] += 1

    lines = [
        "---",
        "type: proposal",
        "from: codex",
        "to: user",
        f"created: {now_iso()}",
        "priority: high",
        "subject: LOG_ARCHAEOLOGY_TRIAGE",
        "---",
        "",
        "# Log Archaeology Triage",
        "",
        f"- Total logs triaged: {len(results)}",
        f"- Categories: {dict(category_counts)}",
        f"- Recommendations: {dict(recommendation_counts)}",
        "",
        "## Distinct Signal Lines",
        "",
    ]

    for line, count in unique_patterns.most_common(20):
        lines.append(f"- `{count}x` {line}")

    lines.extend(["", "## Per-Log Triage", ""])
    for entry in results:
        signal_preview = "; ".join(entry["signal_lines"][:3]) or "no strong signal extracted"
        path_link = markdown_path_link(entry["path"], output_path)
        lines.append(f"- {path_link} | `{entry['category']}` | `{entry['recommendation']}` | {signal_preview}")

    return {
        "total_logs": len(results),
        "category_counts": dict(category_counts),
        "recommendation_counts": dict(recommendation_counts),
        "entries": results,
    }, "\n".join(lines)


def build_governance_proposal(
    census: dict[str, Any],
    orphan_data: dict[str, Any],
    log_data: dict[str, Any],
    output_path: Path,
) -> str:
    anomaly_index = census["anomalies"]
    rename_candidates = [entry["path"] for entry in anomaly_index if entry["type"] == "disabled_by_rename"]
    encoding_candidates = [entry["path"] for entry in anomaly_index if entry["type"] == "filename_encoding_damage"]
    migration_candidates = [entry["path"] for entry in anomaly_index if entry["type"] == "filetype_directory_mismatch"]
    bytecode_candidates = [entry["path"] for entry in anomaly_index if entry["type"] == "tracked_bytecode"]
    env_candidates = [entry["path"] for entry in anomaly_index if entry["type"] == "tracked_env_surface"]
    archive_candidates = [
        entry["path"]
        for entry in log_data["entries"]
        if entry["recommendation"] in {"extract_then_archive", "proposal_untrack_after_extraction"}
    ]

    lines = [
        "---",
        "type: proposal",
        "from: codex",
        "to: user",
        f"created: {now_iso()}",
        "priority: high",
        "subject: WPTG_FILETYPE_GOVERNANCE_PROPOSAL",
        "---",
        "",
        "# WPTG Filetype Governance Proposal",
        "",
        "## .gitignore Additions",
        "",
        "- `__pycache__/`",
        "- `*.py[cod]`",
        "- `*.tsbuildinfo`",
        "- `*.db` where the generator or seed artifact remains tracked elsewhere",
        "",
        "## Archive Candidates",
        "",
    ]

    for path in archive_candidates[:80]:
        lines.append(f"- {markdown_path_link(path, output_path)}")

    lines.extend(["", "## Rename Candidates", ""])
    for path in rename_candidates[:80]:
        lines.append(f"- {markdown_path_link(path, output_path)}")

    lines.extend(["", "## Encoding Repair Candidates", ""])
    for path in encoding_candidates[:80]:
        lines.append(f"- {markdown_path_link(path, output_path)}")

    lines.extend(["", "## Directory Migration Candidates", ""])
    for path in migration_candidates[:80]:
        lines.append(f"- {markdown_path_link(path, output_path)}")

    lines.extend(["", "## Schema / Contract Extraction Candidates", ""])
    for path in bytecode_candidates[:80]:
        lines.append(f"- {markdown_path_link(path, output_path)} -> extract interface contract before any ignore proposal")
    for path in env_candidates[:80]:
        lines.append(f"- {markdown_path_link(path, output_path)} -> extract env schema and integration map")

    lines.extend(["", "## Orphan JSON Candidates", ""])
    for entry in orphan_data["orphan_candidates"][:120]:
        path_link = markdown_path_link(entry["path"], output_path)
        lines.append(f"- {path_link} | age `{entry['age_days']}` days | references `{entry['reference_count']}`")

    return "\n".join(lines)


def build_census(root: Path, log_output: Path, proposal_output: Path) -> tuple[dict[str, Any], dict[str, Any], str, str]:
    tracked = tracked_files(root)
    excluded = [path for path in tracked if path_is_excluded(path)]
    audited = [path for path in tracked if not path_is_excluded(path)]
    text_cache = load_text_cache(root, audited)

    by_extension: dict[str, dict[str, Any]] = defaultdict(lambda: {"count": 0, "anomalies": Counter()})
    anomalies: list[dict[str, str]] = []
    gold_tiers: Counter[str] = Counter()

    for rel_path in audited:
        record = classify_file(root, rel_path)
        by_extension[record.extension]["count"] += 1
        gold_tiers[record.gold_tier] += 1
        for anomaly in record.anomalies:
            anomalies.append(
                {
                    "path": rel_path,
                    "type": anomaly["type"],
                    "gold_grade": record.gold_tier,
                    "recommendation": anomaly["recommendation"],
                    "wptg_rationale": anomaly["wptg_rationale"],
                }
            )
            by_extension[record.extension]["anomalies"][anomaly["type"]] += 1

    log_paths = [path for path in audited if extension_key(path) == ".log"]
    json_paths = [path for path in audited if extension_key(path) == ".json"]

    orphan_data = build_orphan_reconciliation(root, json_paths, text_cache)
    for entry in orphan_data["orphan_candidates"]:
        anomalies.append(
            {
                "path": entry["path"],
                "type": "orphan_json_candidate",
                "gold_grade": "raw_unrefined",
                "recommendation": "derive_schema_then_review_for_archive",
                "wptg_rationale": "State snapshots without consumers should become schema artifacts before any relocation proposal.",
            }
        )
        by_extension[".json"]["anomalies"]["orphan_json_candidate"] += 1

    log_data, log_markdown = build_log_archaeology(root, log_paths, log_output)

    verdict = "PASS"
    if any(entry["type"] in {"tracked_bytecode", "filename_encoding_damage", "tracked_env_surface"} for entry in anomalies):
        verdict = "FAIL"
    elif anomalies:
        verdict = "WARN"

    census = {
        "timestamp": now_iso(),
        "total_tracked": len(tracked),
        "excluded_lane_files": len(excluded),
        "audited_files": len(audited),
        "excluded_paths": excluded,
        "by_extension": {
            extension: {
                "count": data["count"],
                "anomalies": dict(data["anomalies"]),
            }
            for extension, data in sorted(by_extension.items())
        },
        "anomalies": anomalies,
        "by_gold_tier": dict(gold_tiers),
        "verdict": verdict,
    }
    governance_markdown = build_governance_proposal(census, orphan_data, log_data, proposal_output)
    return census, orphan_data, log_markdown, governance_markdown


def exit_code_for_verdict(verdict: str) -> int:
    if verdict == "PASS":
        return 0
    if verdict == "WARN":
        return 1
    return 2


def main() -> int:
    ensure_utf8()
    parser = argparse.ArgumentParser(description="Generate WPTG filetype census artifacts.")
    parser.add_argument(
        "--census-output",
        type=Path,
        default=Path("audit-reports/wptg_filetype_census.json"),
    )
    parser.add_argument(
        "--orphan-output",
        type=Path,
        default=Path("audit-reports/orphaned_artifact_reconciliation.json"),
    )
    parser.add_argument(
        "--log-output",
        type=Path,
        default=Path("codex/mailbox/LOG_ARCHAEOLOGY_TRIAGE.md"),
    )
    parser.add_argument(
        "--proposal-output",
        type=Path,
        default=Path("codex/mailbox/WPTG_FILETYPE_GOVERNANCE_PROPOSAL.md"),
    )
    args = parser.parse_args()

    root = repo_root()
    census, orphan_data, log_markdown, governance_markdown = build_census(
        root,
        args.log_output,
        args.proposal_output,
    )
    write_json(root / args.census_output, census)
    write_json(root / args.orphan_output, orphan_data)
    write_text(root / args.log_output, log_markdown)
    write_text(root / args.proposal_output, governance_markdown)
    print(f"Wrote {args.census_output}")
    print(f"Wrote {args.orphan_output}")
    print(f"Wrote {args.log_output}")
    print(f"Wrote {args.proposal_output}")
    return exit_code_for_verdict(census["verdict"])


if __name__ == "__main__":
    raise SystemExit(main())
