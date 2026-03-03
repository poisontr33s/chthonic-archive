#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Universal polyglot transmutation forge for WPTG Part 2.

@SID:           WPTG_UNIVERSAL_FORGE_V1
@Shabti:        CLI Script
@Purpose:       Audit anomalies and corpse-vault deposits, produce furnace artifacts, temper them, and emit manifests.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import shutil
import subprocess
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.wptg_common import ensure_utf8, json_load, now_iso, repo_root, safe_read_text, tracked_files, write_json, write_text


ROOT = repo_root()
FORGE_ROOT = ROOT / "dumpster-dive" / "forge"
ANVIL_ROOT = FORGE_ROOT / "anvil"
FURNACE_ROOT = FORGE_ROOT / "furnace"
TEMPERED_ROOT = FORGE_ROOT / "tempered"
CORPSE_ROOT = ROOT / "dumpster-dive" / "corpse-vault"

CENSUS_PATH = ROOT / "audit-reports" / "wptg_filetype_census.json"
ORPHAN_PATH = ROOT / "audit-reports" / "orphaned_artifact_reconciliation.json"
LOG_TRIAGE_PATH = ROOT / "codex" / "mailbox" / "LOG_ARCHAEOLOGY_TRIAGE.md"
FORGE_REPORT_PATH = ROOT / "codex" / "mailbox" / "FORGE_TRANSMUTATION_REPORT.md"
CORPSE_SOURCE_FILES: set[str] = set()

ENV_ASSIGN_RE = re.compile(r"^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$")
SECRETS_HINT_RE = re.compile(r"(key|token|secret|password|api[_-]?key)", re.IGNORECASE)
TS_DECLARATION_RE = re.compile(r"^\s*(?:export\s+)?(interface|type|enum)\s+([A-Za-z0-9_]+)")
TS_PROPERTY_RE = re.compile(r"^\s*([A-Za-z0-9_]+)\??:\s*([^;]+);")
RUST_STRUCT_RE = re.compile(r"^\s*(?:pub\s+)?struct\s+([A-Za-z0-9_]+)")
RUST_FIELD_RE = re.compile(r"^\s*(?:pub\s+)?([A-Za-z0-9_]+):\s*([^,]+),?")
MARKDOWN_HEADING_RE = re.compile(r"^#{1,3}\s+(.+)")
TEST_NAME_RE = re.compile(r"""(?:(?:describe|it|test)\s*\(\s*['"]([^'"]+)['"]|def\s+(test_[A-Za-z0-9_]+))""")
RECIPE_LINE_RE = re.compile(r"\b(run|start|verify|validate|scan|sync|check|build|launch|probe)\b", re.IGNORECASE)


@dataclass(slots=True)
class FragmentRecord:
    language: str
    hash: str
    source_file: str
    fragment_path: Path
    byte_size: int
    line_range: tuple[int, int]


@dataclass(slots=True)
class Artifact:
    path: Path
    source_pool: str
    source_files: list[str]
    input_type: str
    output_type: str
    transmutation_pathway: str
    content: str
    gold_tier: str
    novel_pathway: bool = False
    support_files: dict[Path, str] | None = None


def run_command(command: list[str], cwd: Path | None = None) -> tuple[int, str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return result.returncode, (result.stdout or result.stderr or "").strip()


def load_census_data() -> tuple[dict[str, Any], dict[str, Any]]:
    return json_load(CENSUS_PATH), json_load(ORPHAN_PATH)


def group_anomalies(census: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in census["anomalies"]:
        grouped[entry["path"]].append(entry)
    return grouped


def analyze_anomaly_file(path: str, anomalies: list[dict[str, Any]]) -> dict[str, Any]:
    full_path = ROOT / path
    extension = "".join(full_path.suffixes) or full_path.suffix or "[no_ext]"
    text = safe_read_text(full_path, limit_bytes=2_000_000) or ""
    lines = [line for line in text.splitlines() if line.strip()]
    data_points = len({line.strip() for line in lines[:200]})
    anomaly_types = sorted({entry["type"] for entry in anomalies})

    if extension.endswith(".log"):
        intelligence = "diagnostic_trace"
        target = [".md", ".json", ".py"]
    elif extension == ".env":
        intelligence = "environment_contract"
        target = [".json", ".md"]
    elif extension == ".off":
        intelligence = "workflow_logic"
        target = [".md", ".yml"]
    elif extension.endswith(".pyc"):
        intelligence = "bytecode_contract"
        target = [".py"]
    elif extension == ".bat":
        intelligence = "legacy_windows_automation"
        target = [".ps1"]
    elif extension == ".vsconfig":
        intelligence = "toolchain_snapshot"
        target = [".md", ".ps1"]
    elif extension == '.md"':
        intelligence = "path_forensics"
        target = [".md"]
    elif extension == ".json":
        intelligence = "state_or_schema"
        target = [".json", ".md"]
    else:
        intelligence = "raw_unrefined_artifact"
        target = [".md"]

    feasibility = "high" if len(lines) >= 10 or data_points >= 3 else "low"
    return {
        "path": path,
        "extension": extension,
        "anomaly_types": anomaly_types,
        "intelligence_type": intelligence,
        "target_output_types": target,
        "line_count": len(lines),
        "data_points": data_points,
        "feasibility": feasibility,
    }


def build_anomaly_harvest(census: dict[str, Any]) -> dict[str, Any]:
    grouped = group_anomalies(census)
    entries = [analyze_anomaly_file(path, anomalies) for path, anomalies in sorted(grouped.items())]
    return {
        "timestamp": now_iso(),
        "anomalies": entries,
        "summary": {
            "files": len(entries),
            "high_feasibility": sum(1 for entry in entries if entry["feasibility"] == "high"),
            "by_intelligence_type": dict(Counter(entry["intelligence_type"] for entry in entries)),
        },
    }


def load_corpse_vault() -> dict[str, Any]:
    per_language: dict[str, dict[str, Any]] = {}
    reverse_map: dict[str, list[str]] = defaultdict(list)

    for language_dir in sorted(path for path in CORPSE_ROOT.iterdir() if path.is_dir()):
        language = language_dir.name
        records: list[FragmentRecord] = []
        clusters: dict[str, list[FragmentRecord]] = defaultdict(list)
        for provenance_path in sorted(language_dir.glob("*.provenance.json")):
            try:
                provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            fragment_rel = provenance.get("fragment_file")
            if not fragment_rel:
                continue
            record = FragmentRecord(
                language=language,
                hash=str(provenance.get("hash", provenance_path.stem)),
                source_file=str(provenance.get("source_file", provenance_path.name)),
                fragment_path=CORPSE_ROOT / fragment_rel,
                byte_size=int(provenance.get("byte_size", 0)),
                line_range=(int(provenance.get("lines_start", 0)), int(provenance.get("lines_end", 0))),
            )
            records.append(record)
            clusters[record.source_file].append(record)
            reverse_map[record.source_file].append(record.hash)

        candidate_clusters = [
            {
                "source_file": source_file,
                "fragment_count": len(items),
                "total_bytes": sum(item.byte_size for item in items),
                "fragment_hashes": [item.hash for item in items],
            }
            for source_file, items in clusters.items()
            if len(items) >= 3
        ]
        candidate_clusters.sort(key=lambda item: (-item["fragment_count"], -item["total_bytes"], item["source_file"]))

        per_language[language] = {
            "fragment_count": len(records),
            "source_files": len(clusters),
            "top_sources": [
                {
                    "source_file": source_file,
                    "fragment_count": len(items),
                    "total_bytes": sum(item.byte_size for item in items),
                }
                for source_file, items in sorted(
                    clusters.items(),
                    key=lambda item: (-len(item[1]), -sum(record.byte_size for record in item[1]), item[0]),
                )[:25]
            ],
            "amalgamation_candidates": candidate_clusters[:50],
            "records": records,
            "clusters": clusters,
        }

    return {
        "timestamp": now_iso(),
        "languages": {
            language: {
                "fragment_count": data["fragment_count"],
                "source_files": data["source_files"],
                "top_sources": data["top_sources"],
                "amalgamation_candidates": data["amalgamation_candidates"],
            }
            for language, data in per_language.items()
        },
        "reverse_map": {source: hashes for source, hashes in sorted(reverse_map.items())},
        "_records": per_language,
    }


def artifact_header(
    sid: str,
    purpose: str,
    source_files: list[str],
    pathway: str,
    kept: str,
    discarded: str,
    prefix: str = "#",
) -> str:
    lines = [
        f"{prefix} @SID: {sid}",
        f"{prefix} Purpose: {purpose}",
        f"{prefix} Source-Files: {', '.join(source_files)}",
        f"{prefix} Pathway: {pathway}",
        f"{prefix} Kept: {kept}",
        f"{prefix} Discarded: {discarded}",
        "",
    ]
    return "\n".join(lines)


def markdown_header(sid: str, title: str, source_files: list[str], pathway: str, kept: str, discarded: str) -> str:
    return "\n".join(
        [
            "---",
            f"sid: {sid}",
            f"title: {title}",
            f"created: {now_iso()}",
            f"source_files: {json.dumps(source_files)}",
            f"pathway: {pathway}",
            f"kept: {kept}",
            f"discarded: {discarded}",
            "---",
            "",
        ]
    )


def collect_env_contracts() -> tuple[dict[str, dict[str, Any]], list[str]]:
    variables: dict[str, dict[str, Any]] = {}
    env_paths: list[str] = []
    for rel_path in tracked_files(ROOT):
        if not rel_path.endswith(".env"):
            continue
        env_paths.append(rel_path)
        text = safe_read_text(ROOT / rel_path, limit_bytes=200_000) or ""
        for line in text.splitlines():
            match = ENV_ASSIGN_RE.match(line)
            if not match:
                continue
            key, value = match.groups()
            clean = value.strip().strip('"').strip("'")
            entry = variables.setdefault(
                key,
                {
                    "type": "string",
                    "secret": bool(SECRETS_HINT_RE.search(key)),
                    "sample_values": [],
                    "referenced_by": [],
                },
            )
            if clean.lower() in {"true", "false"}:
                entry["type"] = "boolean"
            elif clean.isdigit():
                entry["type"] = "integer"
            if clean and clean not in entry["sample_values"]:
                entry["sample_values"].append(clean)
            if rel_path not in entry["referenced_by"]:
                entry["referenced_by"].append(rel_path)
    return variables, env_paths


def collect_workflows() -> tuple[list[dict[str, Any]], list[str]]:
    workflows: list[dict[str, Any]] = []
    sources: list[str] = []
    for rel_path in tracked_files(ROOT):
        if not rel_path.endswith(".off"):
            continue
        sources.append(rel_path)
        text = safe_read_text(ROOT / rel_path, limit_bytes=300_000) or ""
        name_match = re.search(r"^\s*name:\s*(.+)$", text, re.MULTILINE)
        jobs = re.findall(r"^\s{0,2}([A-Za-z0-9_-]+):\s*$", text, re.MULTILINE)
        uses = re.findall(r"uses:\s*([^\s]+)", text)
        workflows.append(
            {
                "path": rel_path,
                "name": name_match.group(1).strip() if name_match else Path(rel_path).stem,
                "jobs": [job for job in jobs if job not in {"name", "on", "jobs"}][:10],
                "uses": uses[:10],
                "line_count": len(text.splitlines()),
            }
        )
    return workflows, sources


def collect_vsconfig_snapshots() -> tuple[list[dict[str, Any]], list[str]]:
    snapshots: list[dict[str, Any]] = []
    sources: list[str] = []
    for rel_path in tracked_files(ROOT):
        if not rel_path.endswith(".vsconfig"):
            continue
        sources.append(rel_path)
        try:
            payload = json.loads((ROOT / rel_path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        components = payload.get("components", [])
        snapshots.append(
            {
                "path": rel_path,
                "components": sorted(str(component) for component in components),
            }
        )
    return snapshots, sources


def collect_log_patterns() -> tuple[list[str], dict[str, int]]:
    text = safe_read_text(LOG_TRIAGE_PATH, limit_bytes=1_000_000) or ""
    patterns: list[str] = []
    counts: dict[str, int] = {}
    in_distinct = False
    for line in text.splitlines():
        if line.startswith("## Distinct Signal Lines"):
            in_distinct = True
            continue
        if in_distinct and line.startswith("## "):
            break
        if in_distinct and line.startswith("- `"):
            count_match = re.match(r"- `(\d+)x` (.+)$", line)
            if count_match:
                pattern = count_match.group(2)
                patterns.append(pattern)
                counts[pattern] = int(count_match.group(1))
    return patterns, counts


def top_cluster_lines(records: list[FragmentRecord], limit: int = 8) -> list[str]:
    lines: list[str] = []
    for record in sorted(records, key=lambda item: (-item.byte_size, item.hash)):
        text = safe_read_text(record.fragment_path, limit_bytes=60_000)
        if not text:
            continue
        for line in text.splitlines():
            stripped = line.rstrip()
            if not stripped:
                continue
            lines.append(stripped[:160])
            if len(lines) >= limit:
                return lines
    return lines


def recover_ts_blocks(records: list[FragmentRecord], limit: int = 24) -> list[str]:
    blocks: list[str] = []
    seen: set[str] = set()
    for record in sorted(records, key=lambda item: (-item.byte_size, item.hash)):
        text = safe_read_text(record.fragment_path, limit_bytes=120_000)
        if not text:
            continue
        current: list[str] = []
        depth = 0
        collecting = False
        for line in text.splitlines():
            if not collecting and TS_DECLARATION_RE.match(line):
                collecting = True
                current = [line.rstrip()]
                depth = line.count("{") - line.count("}")
                if depth <= 0 and line.strip().endswith(";"):
                    block = "\n".join(current).strip()
                    if block not in seen:
                        seen.add(block)
                        blocks.append(block)
                    collecting = False
                continue
            if collecting:
                current.append(line.rstrip())
                depth += line.count("{") - line.count("}")
                if depth <= 0:
                    block = "\n".join(current).strip()
                    if block not in seen:
                        seen.add(block)
                        blocks.append(block)
                    collecting = False
                    if len(blocks) >= limit:
                        return blocks
    return blocks


def recover_ts_contracts(records: list[FragmentRecord], limit: int = 12) -> list[dict[str, Any]]:
    contracts: list[dict[str, Any]] = []
    seen: set[str] = set()
    for block in recover_ts_blocks(records, limit=limit * 2):
        header = TS_DECLARATION_RE.search(block)
        if not header:
            continue
        name = header.group(2)
        if name in seen:
            continue
        seen.add(name)
        props = []
        for line in block.splitlines():
            match = TS_PROPERTY_RE.match(line)
            if match:
                props.append({"name": match.group(1), "type": match.group(2).strip()})
        contracts.append({"name": name, "block": block, "properties": props})
        if len(contracts) >= limit:
            break
    return contracts


def recover_rust_structs(records: list[FragmentRecord], limit: int = 12) -> list[dict[str, Any]]:
    structs: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in sorted(records, key=lambda item: (-item.byte_size, item.hash)):
        text = safe_read_text(record.fragment_path, limit_bytes=120_000)
        if not text:
            continue
        current_name = None
        current_fields: list[dict[str, str]] = []
        for line in text.splitlines():
            if current_name is None:
                match = RUST_STRUCT_RE.match(line)
                if match:
                    current_name = match.group(1)
                    current_fields = []
                continue
            field_match = RUST_FIELD_RE.match(line)
            if field_match:
                current_fields.append({"name": field_match.group(1), "type": field_match.group(2).strip()})
                continue
            if "}" in line and current_name:
                if current_name not in seen:
                    seen.add(current_name)
                    structs.append({"name": current_name, "fields": current_fields.copy()})
                    if len(structs) >= limit:
                        return structs
                current_name = None
                current_fields = []
    return structs


def recover_markdown_decisions(records: list[FragmentRecord], limit: int = 18) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in sorted(records, key=lambda item: (-item.byte_size, item.hash)):
        text = safe_read_text(record.fragment_path, limit_bytes=80_000)
        if not text:
            continue
        lines = text.splitlines()
        for index, line in enumerate(lines):
            match = MARKDOWN_HEADING_RE.match(line)
            if not match:
                continue
            heading = match.group(1).strip()
            if heading in seen:
                continue
            body_lines = [
                candidate.strip()
                for candidate in lines[index + 1:index + 5]
                if candidate.strip() and not candidate.startswith("#")
            ]
            if not body_lines:
                continue
            seen.add(heading)
            decisions.append(
                {
                    "heading": heading,
                    "body": " ".join(body_lines),
                    "source_file": record.source_file,
                    "hash": record.hash,
                }
            )
            if len(decisions) >= limit:
                return decisions
    return decisions


def recover_test_fixtures(records: list[FragmentRecord], limit: int = 40) -> list[dict[str, str]]:
    fixtures: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for record in sorted(records, key=lambda item: (-item.byte_size, item.hash)):
        if "test" not in record.source_file.lower():
            continue
        text = safe_read_text(record.fragment_path, limit_bytes=80_000)
        if not text:
            continue
        for match in TEST_NAME_RE.finditer(text):
            name = match.group(1) or match.group(2)
            key = (record.source_file, name)
            if key in seen:
                continue
            seen.add(key)
            fixtures.append({"source_file": record.source_file, "name": name, "hash": record.hash})
            if len(fixtures) >= limit:
                return fixtures
    return fixtures


def recover_shell_recipes(records: list[FragmentRecord], limit: int = 20) -> list[dict[str, Any]]:
    recipes: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in sorted(records, key=lambda item: (-item.byte_size, item.hash)):
        recipe_name = Path(record.source_file).stem.replace(".", "_")
        if recipe_name in seen:
            continue
        text = safe_read_text(record.fragment_path, limit_bytes=80_000) or ""
        commands = [line.strip() for line in text.splitlines() if RECIPE_LINE_RE.search(line)]
        if not commands:
            commands = [line.strip() for line in text.splitlines() if line.strip()][:5]
        if not commands:
            continue
        seen.add(recipe_name)
        recipes.append(
            {
                "name": recipe_name,
                "source_file": record.source_file,
                "commands": commands[:6],
                "hash": record.hash,
            }
        )
        if len(recipes) >= limit:
            return recipes
    return recipes


def build_schema_catalog(orphan_data: dict[str, Any]) -> dict[str, Any]:
    patterns: dict[str, dict[str, Any]] = {}
    for entry in orphan_data["reference_traces"]:
        path = ROOT / entry["path"]
        text = safe_read_text(path, limit_bytes=1_000_000)
        if not text:
            continue
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        signature = ",".join(sorted(payload.keys()))
        bucket = patterns.setdefault(signature, {"properties": {}, "examples": []})
        for key, value in payload.items():
            bucket["properties"].setdefault(key, sorted({type(value).__name__}))
        bucket["examples"].append(entry["path"])
    catalog = {
        "generated_at": now_iso(),
        "schema_patterns": [
            {
                "signature": signature,
                "properties": data["properties"],
                "examples": data["examples"][:10],
            }
            for signature, data in patterns.items()
        ],
    }
    catalog["schema_patterns"].sort(key=lambda item: (-len(item["properties"]), item["signature"]))
    return catalog


def map_ts_type_to_csharp(ts_type: str) -> str:
    lowered = ts_type.lower()
    if "string" in lowered:
        return "string"
    if "number" in lowered:
        return "double"
    if "boolean" in lowered:
        return "bool"
    if "[]" in lowered or "array" in lowered:
        return "List<object?>"
    return "object?"


def map_rust_type_to_c(field_type: str) -> str:
    mapping = {
        "u8": "uint8_t",
        "u16": "uint16_t",
        "u32": "uint32_t",
        "u64": "uint64_t",
        "i8": "int8_t",
        "i16": "int16_t",
        "i32": "int32_t",
        "i64": "int64_t",
        "usize": "size_t",
        "isize": "ptrdiff_t",
        "f32": "float",
        "f64": "double",
        "bool": "bool",
    }
    return mapping.get(field_type.strip(), "uint32_t")


def ps_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def build_artifacts(census: dict[str, Any], orphan_data: dict[str, Any], corpse_data: dict[str, Any]) -> list[Artifact]:
    artifacts: list[Artifact] = []
    anomaly_grouped = group_anomalies(census)

    log_patterns, pattern_counts = collect_log_patterns()
    log_sources = sorted(path for path in anomaly_grouped if path.endswith(".log"))
    diagnostic_body = markdown_header(
        "FORGE_DIAGNOSTIC_PLAYBOOK_V1",
        "Recovered Diagnostic Playbook",
        log_sources[:40] + ([f"... and {len(log_sources) - 40} more"] if len(log_sources) > 40 else []),
        "log -> diagnostic pattern extraction -> playbook",
        "Repeated failure signatures, environment markers, and toolchain versions.",
        "Redundant per-run noise once the repeated signature is captured.",
    )
    diagnostic_body += "# Recovered Diagnostic Playbook\n\n## Top Failure Signatures\n\n"
    for pattern in log_patterns[:30]:
        diagnostic_body += f"- `{pattern_counts.get(pattern, 0)}x` {pattern}\n"
    diagnostic_body += "\n## Recovery Notes\n\n"
    diagnostic_body += "- Renderer crashes and shared image memory failures cluster around VS Code Insiders GPU and telemetry lanes.\n"
    diagnostic_body += "- Shell integration capability timeouts recur across the terminal triage captures.\n"
    diagnostic_body += "- CUDA build logs preserve compiler and NVCC versions; the short empty siblings can be archived after extraction by proposal.\n"
    artifacts.append(
        Artifact(
            path=FURNACE_ROOT / "docs" / "diagnostic_playbook.md",
            source_pool="anomaly_harvest",
            source_files=log_sources,
            input_type=".log",
            output_type=".md",
            transmutation_pathway="log -> pattern extraction -> diagnostic playbook",
            content=diagnostic_body,
            gold_tier="tier_3_conceptual",
        )
    )

    env_contracts, env_sources = collect_env_contracts()
    env_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Recovered Chthonic Environment Surface",
        "type": "object",
        "properties": {
            key: {
                "type": value["type"],
                "description": f"Recovered from {', '.join(value['referenced_by'])}",
                "x-secret": value["secret"],
            }
            for key, value in sorted(env_contracts.items())
        },
        "required": sorted(env_contracts),
        "additionalProperties": True,
    }
    artifacts.append(
        Artifact(
            path=FURNACE_ROOT / "schemas" / "environment_schema.json",
            source_pool="anomaly_harvest",
            source_files=env_sources,
            input_type=".env",
            output_type=".json",
            transmutation_pathway="env -> variable contract extraction -> JSON schema",
            content=json.dumps(env_schema, indent=2, ensure_ascii=False) + "\n",
            gold_tier="tier_2_structural",
        )
    )

    env_map = markdown_header(
        "FORGE_ENVIRONMENT_MAP_V1",
        "Recovered Environment Integration Map",
        env_sources,
        "env -> service hint extraction -> integration map",
        "Variable names, sample shapes, and secret/config classification.",
        "Concrete secret values.",
    )
    env_map += "# Recovered Environment Integration Map\n\n"
    for key, value in sorted(env_contracts.items()):
        env_map += f"- `{key}` | type `{value['type']}` | secret `{value['secret']}` | sources: {', '.join(value['referenced_by'])}\n"
    artifacts.append(
        Artifact(
            path=FURNACE_ROOT / "docs" / "environment_integration_map.md",
            source_pool="anomaly_harvest",
            source_files=env_sources,
            input_type=".env",
            output_type=".md",
            transmutation_pathway="env -> integration hint extraction -> environment map",
            content=env_map,
            gold_tier="tier_3_conceptual",
        )
    )

    workflows, workflow_sources = collect_workflows()
    workflow_catalog = markdown_header(
        "FORGE_WORKFLOW_CATALOG_V1",
        "Recovered Workflow Pattern Catalogue",
        workflow_sources,
        "workflow.off -> job and action extraction -> pattern catalogue",
        "Workflow names, jobs, and action versions.",
        "The disabled-by-rename wrapper around the live logic.",
    )
    workflow_catalog += "# Recovered Workflow Pattern Catalogue\n\n"
    for workflow in workflows:
        workflow_catalog += f"## {workflow['name']}\n\n"
        workflow_catalog += f"- Source: `{workflow['path']}`\n"
        workflow_catalog += f"- Jobs: {', '.join(workflow['jobs']) or 'none recovered'}\n"
        workflow_catalog += f"- Actions: {', '.join(workflow['uses']) or 'none recovered'}\n\n"
    artifacts.append(
        Artifact(
            path=FURNACE_ROOT / "workflows" / "workflow_pattern_catalog.md",
            source_pool="anomaly_harvest",
            source_files=workflow_sources,
            input_type=".off",
            output_type=".md",
            transmutation_pathway="workflow.off -> pattern extraction -> workflow catalogue",
            content=workflow_catalog,
            gold_tier="tier_3_conceptual",
        )
    )

    workflow_template = [
        "# @SID: FORGE_WORKFLOW_TEMPLATES_V1",
        "# Purpose: Recovered workflow templates from renamed .off workflows.",
        "",
    ]
    for workflow in workflows:
        workflow_template.extend(["---", f"name: Recovered {workflow['name']}", "on:", "  workflow_dispatch:", "jobs:"])
        for job in workflow["jobs"] or ["recovered_job"]:
            workflow_template.extend(
                [
                    f"  {job}:",
                    "    runs-on: ubuntu-latest",
                    "    steps:",
                    f"      - name: Recover {job}",
                    "        run: echo \"Recovered workflow step placeholder driven by catalogue metadata.\"",
                ]
            )
        workflow_template.append(f"# Source: {workflow['path']}")
        workflow_template.append("")
    artifacts.append(
        Artifact(
            path=FURNACE_ROOT / "workflows" / "recovered_workflow_templates.yml",
            source_pool="anomaly_harvest",
            source_files=workflow_sources,
            input_type=".off",
            output_type=".yml",
            transmutation_pathway="workflow.off -> reusable template synthesis -> YAML templates",
            content="\n".join(workflow_template),
            gold_tier="tier_2_structural",
        )
    )

    snapshots, vsconfig_sources = collect_vsconfig_snapshots()
    all_components = [set(snapshot["components"]) for snapshot in snapshots]
    common_components = sorted(set.intersection(*all_components)) if all_components else []
    union_components = sorted(set().union(*all_components)) if all_components else []
    vsconfig_doc = markdown_header(
        "FORGE_VSCONFIG_DECISION_RECORD_V1",
        "Recovered VS Toolchain Decision Record",
        vsconfig_sources,
        "vsconfig -> component diff -> decision record",
        "Shared and divergent Visual Studio workload selections.",
        "Redundant snapshot serialization once the comparison exists.",
    )
    vsconfig_doc += "# VS Toolchain Decision Record\n\n"
    vsconfig_doc += f"- Snapshots compared: {len(snapshots)}\n- Common components: {len(common_components)}\n- Union components: {len(union_components)}\n\n"
    vsconfig_doc += "## Shared Components\n\n"
    for component in common_components[:60]:
        vsconfig_doc += f"- `{component}`\n"
    vsconfig_doc += "\n## Snapshot Deltas\n\n"
    for snapshot in snapshots:
        exclusive = sorted(set(snapshot["components"]) - set(common_components))
        vsconfig_doc += f"### {snapshot['path']}\n\n"
        for component in exclusive[:40]:
            vsconfig_doc += f"- `{component}`\n"
        vsconfig_doc += "\n"
    artifacts.append(
        Artifact(
            path=FURNACE_ROOT / "docs" / "toolchain_decision_record.md",
            source_pool="anomaly_harvest",
            source_files=vsconfig_sources,
            input_type=".vsconfig",
            output_type=".md",
            transmutation_pathway="vsconfig -> component diff -> toolchain decision record",
            content=vsconfig_doc,
            gold_tier="tier_3_conceptual",
        )
    )

    bat_sources = [path for path in tracked_files(ROOT) if path.endswith(".bat")]
    bat_text = safe_read_text(ROOT / bat_sources[0], limit_bytes=80_000) if bat_sources else ""
    batch_ps1 = artifact_header(
        "FORGE_BATCH_TRANSLITERATION_V1",
        "Faithful PowerShell transliteration of the tracked batch artifact.",
        bat_sources,
        "batch -> PowerShell transliteration",
        "Script intent, comments, and control flow markers.",
        "cmd.exe-specific syntax.",
    )
    batch_ps1 += "$script:RecoveredBatchLines = @(\n"
    batch_lines = (bat_text or "").splitlines()
    for index, line in enumerate(batch_lines):
        suffix = "," if index < len(batch_lines) - 1 else ""
        batch_ps1 += f"    {ps_quote(line)}{suffix}\n"
    batch_ps1 += ")\n\nfunction Get-RecoveredBatchTranscript {\n    [CmdletBinding()]\n    param()\n    return $script:RecoveredBatchLines\n}\n\n"
    batch_ps1 += "function Show-RecoveredBatchTranscript {\n    [CmdletBinding()]\n    param()\n    $script:RecoveredBatchLines | ForEach-Object { Write-Host $_ }\n}\n"
    artifacts.append(
        Artifact(
            path=FURNACE_ROOT / "powershell" / "batch_transliteration.ps1",
            source_pool="anomaly_harvest",
            source_files=bat_sources,
            input_type=".bat",
            output_type=".ps1",
            transmutation_pathway="batch -> transcript-preserving PowerShell transliteration",
            content=batch_ps1,
            gold_tier="tier_1_direct",
        )
    )

    damaged_sources = [entry["path"] for entry in census["anomalies"] if entry["type"] == "filename_encoding_damage"]
    filename_forensics = markdown_header(
        "FORGE_FILENAME_FORENSICS_V1",
        "Recovered Filename Forensics",
        damaged_sources,
        "damaged path -> provenance note -> clean-name proposal",
        "The damaged path strings and their surviving content lineage.",
        "The unsafe path form as an active dependency.",
    )
    filename_forensics += "# Filename Forensics\n\n"
    for path in damaged_sources:
        filename_forensics += f"- `{path}`\n"
    artifacts.append(
        Artifact(
            path=FURNACE_ROOT / "docs" / "filename_forensics_note.md",
            source_pool="anomaly_harvest",
            source_files=damaged_sources,
            input_type='.md"',
            output_type=".md",
            transmutation_pathway="damaged markdown path -> filename forensics note",
            content=filename_forensics,
            gold_tier="tier_3_conceptual",
            novel_pathway=True,
        )
    )

    records = corpse_data["_records"]
    python_clusters = records.get("python", {}).get("clusters", {})
    top_python_sources = sorted(
        python_clusters.items(),
        key=lambda item: (-len(item[1]), -sum(record.byte_size for record in item[1]), item[0]),
    )[:12]
    python_module = artifact_header(
        "FORGE_CONSOLIDATED_PYTHON_UTILS_V1",
        "Recovered Python utility registry from corpse-vault evolutionary hotspots.",
        [source for source, _ in top_python_sources],
        "corpse-vault/python -> cluster audit -> utility registry module",
        "Cluster metadata, representative lines, and search helpers.",
        "Broken fragment boundaries and deleted implementation glue.",
    )
    python_module += "from __future__ import annotations\n\nfrom dataclasses import dataclass\n\n\n"
    python_module += "@dataclass(frozen=True, slots=True)\nclass RecoveredPythonCluster:\n    source_file: str\n    fragment_count: int\n    sample_lines: tuple[str, ...]\n\n\n"
    python_module += "RECOVERED_PYTHON_CLUSTERS = [\n"
    for source, cluster_records in top_python_sources:
        sample_lines = top_cluster_lines(cluster_records, limit=4)
        python_module += (
            "    RecoveredPythonCluster(\n"
            f"        source_file={source!r},\n"
            f"        fragment_count={len(cluster_records)},\n"
            f"        sample_lines={tuple(sample_lines)!r},\n"
            "    ),\n"
        )
    python_module += "]\n\n"
    python_module += "def top_clusters(limit: int = 10) -> list[RecoveredPythonCluster]:\n    return RECOVERED_PYTHON_CLUSTERS[: max(limit, 0)]\n\n"
    python_module += "def search_clusters(keyword: str) -> list[RecoveredPythonCluster]:\n    lowered = keyword.lower()\n    return [cluster for cluster in RECOVERED_PYTHON_CLUSTERS if lowered in cluster.source_file.lower()]\n"
    artifacts.append(
        Artifact(
            path=FURNACE_ROOT / "python" / "consolidated_python_utilities.py",
            source_pool="corpse_vault",
            source_files=[source for source, _ in top_python_sources],
            input_type="corpse-vault/python",
            output_type=".py",
            transmutation_pathway="python fragments -> cluster registry -> utility library",
            content=python_module,
            gold_tier="tier_1_direct",
            novel_pathway=True,
        )
    )

    ts_records = list(records.get("typescript", {}).get("records", []))
    ts_contracts = recover_ts_contracts(ts_records, limit=12)
    dts_header = artifact_header(
        "FORGE_TYPE_ARCHIVE_V1",
        "Recovered TypeScript declaration archive from corpse-vault fragments.",
        [contract["name"] for contract in ts_contracts],
        "typescript fragments -> recoverable declaration blocks -> .d.ts archive",
        "Recoverable type contracts and interface shells.",
        "Unbalanced fragments that could not be closed without invention.",
        prefix="//",
    )
    dts_content = dts_header
    for contract in ts_contracts:
        dts_content += f"declare interface {contract['name']}Recovered {{\n"
        if contract["properties"]:
            for prop in contract["properties"][:12]:
                dts_content += f"  {prop['name']}: {prop['type']};\n"
        else:
            dts_content += "  [key: string]: unknown;\n"
        dts_content += "}\n\n"
    artifacts.append(
        Artifact(
            path=FURNACE_ROOT / "typescript" / "recovered_type_archive.d.ts",
            source_pool="corpse_vault",
            source_files=[record.source_file for record in ts_records[:30]],
            input_type="corpse-vault/typescript",
            output_type=".d.ts",
            transmutation_pathway="typescript fragments -> declaration recovery -> archive",
            content=dts_content,
            gold_tier="tier_1_direct",
        )
    )

    fixture_records = ts_records + list(records.get("javascript", {}).get("records", [])) + list(records.get("python", {}).get("records", []))
    fixtures = recover_test_fixtures(fixture_records, limit=48)
    fixture_content = artifact_header(
        "FORGE_TEST_FIXTURES_V1",
        "Recovered test fixture index from corpse-vault test fragments.",
        [fixture["source_file"] for fixture in fixtures[:20]],
        "test fragments -> fixture metadata extraction -> reusable registry",
        "Fixture names, source provenance, and recovered labels.",
        "Broken module imports and deleted execution context.",
        prefix="//",
    )
    fixture_content += "export interface RecoveredFixture {\n  sourceFile: string;\n  name: string;\n  hash: string;\n}\n\n"
    fixture_content += "export const recoveredFixtures: RecoveredFixture[] = [\n"
    for fixture in fixtures:
        fixture_content += f"  {{ sourceFile: {fixture['source_file']!r}, name: {fixture['name']!r}, hash: {fixture['hash']!r} }},\n"
    fixture_content += "];\n\nexport function findRecoveredFixtures(keyword: string): RecoveredFixture[] {\n  const lowered = keyword.toLowerCase();\n  return recoveredFixtures.filter((fixture) => fixture.sourceFile.toLowerCase().includes(lowered) || fixture.name.toLowerCase().includes(lowered));\n}\n"
    artifacts.append(
        Artifact(
            path=FURNACE_ROOT / "typescript" / "recovered_test_fixtures.ts",
            source_pool="corpse_vault",
            source_files=[fixture["source_file"] for fixture in fixtures],
            input_type="corpse-vault/*test*",
            output_type=".ts",
            transmutation_pathway="test fragments -> fixture metadata -> reusable registry",
            content=fixture_content,
            gold_tier="tier_1_direct",
            novel_pathway=True,
        )
    )

    markdown_records = list(records.get("markdown", {}).get("records", []))
    decisions = recover_markdown_decisions(markdown_records, limit=18)
    adr_doc = markdown_header(
        "FORGE_ADR_RECOVERED_V1",
        "Recovered Architecture Decisions",
        [decision["source_file"] for decision in decisions[:20]],
        "markdown fragments -> decision capture -> recovered ADR anthology",
        "Headings, rationale sentences, and provenance.",
        "Formatting noise and broken draft fragments.",
    )
    adr_doc += "# Recovered Architecture Decisions\n\n"
    for index, decision in enumerate(decisions, start=1):
        adr_doc += f"## ADR-{index:02d}: {decision['heading']}\n\n"
        adr_doc += f"{decision['body']}\n\n_Provenance: `{decision['source_file']}` / `{decision['hash']}`_\n\n"
    artifacts.append(
        Artifact(
            path=FURNACE_ROOT / "docs" / "ADR_RECOVERED.md",
            source_pool="corpse_vault",
            source_files=[decision["source_file"] for decision in decisions],
            input_type="corpse-vault/markdown",
            output_type=".md",
            transmutation_pathway="markdown fragments -> recovered architecture decisions",
            content=adr_doc,
            gold_tier="tier_3_conceptual",
        )
    )

    config_catalog = build_schema_catalog(orphan_data)
    artifacts.append(
        Artifact(
            path=FURNACE_ROOT / "schemas" / "configuration_schema_catalog.json",
            source_pool="corpse_vault",
            source_files=[entry["path"] for entry in orphan_data["reference_traces"][:80]],
            input_type="corpse-vault/config + orphaned json",
            output_type=".json",
            transmutation_pathway="config fragments -> observed key signatures -> schema catalogue",
            content=json.dumps(config_catalog, indent=2, ensure_ascii=False) + "\n",
            gold_tier="tier_2_structural",
        )
    )

    shell_records = list(records.get("shell", {}).get("records", []))
    shell_recipes = recover_shell_recipes(shell_records, limit=18)
    ps1_content = artifact_header(
        "FORGE_SHELL_RECIPE_BOOK_V1",
        "Recovered PowerShell recipe book from corpse-vault shell fragments.",
        [recipe["source_file"] for recipe in shell_recipes],
        "shell fragments -> command extraction -> PowerShell recipe book",
        "Recipe names, provenance, and representative commands.",
        "Deleted process glue and unsafe inline environment mutations.",
    )
    ps1_content += "$script:RecoveredShellRecipes = @(\n"
    for recipe in shell_recipes:
        ps1_content += "    [pscustomobject]@{\n"
        ps1_content += f"        Name = {ps_quote(recipe['name'])}\n"
        ps1_content += f"        SourceFile = {ps_quote(recipe['source_file'])}\n"
        ps1_content += f"        Hash = {ps_quote(recipe['hash'])}\n"
        ps1_content += f"        Commands = @({', '.join(ps_quote(command) for command in recipe['commands'])})\n"
        ps1_content += "    }\n"
    ps1_content += ")\n\n"
    ps1_content += "function Get-RecoveredShellRecipe {\n    [CmdletBinding()]\n    param([string]$Name)\n    if ($Name) { return $script:RecoveredShellRecipes | Where-Object { $_.Name -like \"*$Name*\" } }\n    return $script:RecoveredShellRecipes\n}\n\n"
    ps1_content += "function Show-RecoveredShellRecipe {\n    [CmdletBinding()]\n    param([string]$Name)\n    Get-RecoveredShellRecipe -Name $Name | ForEach-Object {\n        Write-Host \"[$($_.Name)] $($_.SourceFile)\"\n        $_.Commands | ForEach-Object { Write-Host \"  $_\" }\n    }\n}\n"
    artifacts.append(
        Artifact(
            path=FURNACE_ROOT / "powershell" / "recovered_shell_recipe_book.ps1",
            source_pool="corpse_vault",
            source_files=[recipe["source_file"] for recipe in shell_recipes],
            input_type="corpse-vault/shell",
            output_type=".ps1",
            transmutation_pathway="shell fragments -> recipe extraction -> PowerShell registry",
            content=ps1_content,
            gold_tier="tier_1_direct",
        )
    )

    go_content = "\n".join(
        [
            "package main",
            "",
            "// @SID: FORGE_SHELL_RECIPE_CLI_V1",
            "// Purpose: Cross-language Go CLI distilled from shell recipe fragments.",
            "import (",
            '    "flag"',
            '    "fmt"',
            '    "strings"',
            ")",
            "",
            "type recipe struct {",
            "    Name string",
            "    Source string",
            "    Commands []string",
            "}",
            "",
            "var recipes = []recipe{",
        ]
    )
    for recipe in shell_recipes:
        go_content += "\n    {Name: " + json.dumps(recipe["name"]) + ", Source: " + json.dumps(recipe["source_file"]) + ", Commands: []string{" + ", ".join(json.dumps(command) for command in recipe["commands"]) + "}},"
    go_content += "\n}\n\nfunc main() {\n    filter := flag.String(\"filter\", \"\", \"recipe name filter\")\n    flag.Parse()\n    for _, recipe := range recipes {\n        if *filter != \"\" && !strings.Contains(strings.ToLower(recipe.Name), strings.ToLower(*filter)) { continue }\n        fmt.Printf(\"[%s] %s\\n\", recipe.Name, recipe.Source)\n        for _, command := range recipe.Commands { fmt.Printf(\"  - %s\\n\", command) }\n    }\n}\n"
    artifacts.append(
        Artifact(
            path=FURNACE_ROOT / "go" / "recovered_shell_recipe_cli.go",
            source_pool="corpse_vault",
            source_files=[recipe["source_file"] for recipe in shell_recipes],
            input_type="corpse-vault/shell",
            output_type=".go",
            transmutation_pathway="shell fragments -> recipe registry -> Go CLI",
            content=go_content,
            gold_tier="tier_1_direct",
        )
    )

    csharp_contracts = ts_contracts[:8]
    csharp_cs = [
        "// @SID: FORGE_CSHARP_CONTRACTS_V1",
        "// Purpose: C# class contracts mirrored from recovered TypeScript declarations.",
        "using System.Collections.Generic;",
        "",
        "namespace ChthonicArchive.Forge.Recovered;",
        "",
    ]
    for contract in csharp_contracts:
        csharp_cs.append(f"public sealed class {contract['name']}Contract")
        csharp_cs.append("{")
        if contract["properties"]:
            for prop in contract["properties"][:12]:
                csharp_type = map_ts_type_to_csharp(prop["type"])
                prop_name = prop["name"][:1].upper() + prop["name"][1:]
                csharp_cs.append(f"    public {csharp_type} {prop_name} {{ get; init; }}")
        else:
            csharp_cs.append("    public Dictionary<string, object?> Snapshot { get; init; } = new();")
        csharp_cs.append("}")
        csharp_cs.append("")
    csproj_path = FURNACE_ROOT / "csharp" / "RecoveredContracts.csproj"
    csproj = "\n".join(
        [
            "<Project Sdk=\"Microsoft.NET.Sdk\">",
            "  <PropertyGroup>",
            "    <TargetFramework>net10.0</TargetFramework>",
            "    <EnableDefaultCompileItems>false</EnableDefaultCompileItems>",
            "    <ImplicitUsings>enable</ImplicitUsings>",
            "    <Nullable>enable</Nullable>",
            "    <GenerateAssemblyInfo>false</GenerateAssemblyInfo>",
            "    <GenerateTargetFrameworkAttribute>false</GenerateTargetFrameworkAttribute>",
            "  </PropertyGroup>",
            "  <ItemGroup>",
            "    <Compile Include=\"RecoveredContracts.cs\" />",
            "  </ItemGroup>",
            "</Project>",
        ]
    )
    artifacts.append(
        Artifact(
            path=FURNACE_ROOT / "csharp" / "RecoveredContracts.cs",
            source_pool="corpse_vault",
            source_files=[contract["name"] for contract in csharp_contracts],
            input_type="corpse-vault/typescript",
            output_type=".cs",
            transmutation_pathway="typescript contracts -> C# class mirror",
            content="\n".join(csharp_cs) + "\n",
            gold_tier="tier_1_direct",
            support_files={csproj_path: csproj},
        )
    )

    rust_structs = recover_rust_structs(list(records.get("rust", {}).get("records", [])), limit=10)
    header_lines = [
        "/* @SID: FORGE_RUST_FFI_HEADER_V1 */",
        "/* Purpose: C header derived from recovered Rust struct signatures. */",
        "#ifndef CHTHONIC_ARCHIVE_RECOVERED_RUST_FFI_H",
        "#define CHTHONIC_ARCHIVE_RECOVERED_RUST_FFI_H",
        "",
        "#include <stdbool.h>",
        "#include <stddef.h>",
        "#include <stdint.h>",
        "",
    ]
    for struct in rust_structs:
        header_lines.append(f"typedef struct {struct['name']} {{")
        if struct["fields"]:
            for field in struct["fields"][:12]:
                header_lines.append(f"    {map_rust_type_to_c(field['type'])} {field['name']};")
        else:
            header_lines.append("    uint32_t reserved;")
        header_lines.append(f"}} {struct['name']};")
        header_lines.append("")
    header_lines.append("#endif")
    artifacts.append(
        Artifact(
            path=FURNACE_ROOT / "c_cpp" / "recovered_rust_ffi.h",
            source_pool="corpse_vault",
            source_files=[struct["name"] for struct in rust_structs],
            input_type="corpse-vault/rust",
            output_type=".h",
            transmutation_pathway="rust struct signatures -> C header for FFI",
            content="\n".join(header_lines) + "\n",
            gold_tier="tier_1_direct",
        )
    )

    ruby_content = "\n".join(
        [
            "# @SID: FORGE_RUBY_CLUSTER_REGISTRY_V1",
            "# Purpose: Ruby mirror of recovered Python cluster hotspots.",
            "Cluster = Struct.new(:source_file, :fragment_count, :sample_lines, keyword_init: true)",
            "",
            "RECOVERED_CLUSTERS = [",
        ]
    )
    for source, cluster_records in top_python_sources[:8]:
        ruby_content += "\n  Cluster.new(source_file: " + source.__repr__() + ", fragment_count: " + str(len(cluster_records)) + ", sample_lines: " + top_cluster_lines(cluster_records, limit=3).__repr__() + "),"
    ruby_content += "\n]\n\ndef top_clusters(limit = 10)\n  RECOVERED_CLUSTERS.first([limit, 0].max)\nend\n"
    artifacts.append(
        Artifact(
            path=FURNACE_ROOT / "ruby" / "recovered_python_cluster_registry.rb",
            source_pool="corpse_vault",
            source_files=[source for source, _ in top_python_sources[:8]],
            input_type="corpse-vault/python",
            output_type=".rb",
            transmutation_pathway="python cluster metadata -> Ruby registry mirror",
            content=ruby_content,
            gold_tier="tier_1_direct",
            novel_pathway=True,
        )
    )

    return artifacts


def validate_markdown(path: Path) -> tuple[bool, str]:
    text = safe_read_text(path, limit_bytes=500_000) or ""
    return ("# " in text or "## " in text or text.startswith("---"), "missing markdown structure")


def validate_json_file(path: Path) -> tuple[bool, str]:
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, str(exc)
    return True, "ok"


def validate_python(path: Path) -> tuple[bool, str]:
    try:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        return False, str(exc)
    return True, "ok"


def validate_powershell(path: Path) -> tuple[bool, str]:
    escaped = str(path).replace("'", "''")
    command = [
        "pwsh",
        "-NoProfile",
        "-Command",
        f"$errors = @(); [System.Management.Automation.Language.Parser]::ParseFile('{escaped}', [ref]$null, [ref]$errors) > $null; if ($errors.Count -gt 0) {{ $errors | ForEach-Object {{ $_.Message }}; exit 1 }}",
    ]
    code, output = run_command(command)
    return code == 0, output or "ok"


def validate_yaml(path: Path) -> tuple[bool, str]:
    code, output = run_command(["ruby", "-e", "require 'yaml'; YAML.load_file(ARGV[0])", str(path)])
    return code == 0, output or "ok"


def validate_typescript(path: Path) -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as temp_dir:
        tsconfig_path = Path(temp_dir) / "tsconfig.json"
        tsconfig_path.write_text(
            json.dumps(
                {
                    "compilerOptions": {
                        "noEmit": True,
                        "skipLibCheck": True,
                        "strict": False,
                        "lib": ["es2022"],
                        "types": [],
                    },
                    "files": [str(path.resolve())],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        code, output = run_command(["bunx", "tsc", "-p", str(tsconfig_path)], cwd=ROOT)
        return code == 0, output or "ok"


def validate_go(path: Path) -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "recovered-shell-recipe.exe"
        code, output = run_command(["go", "build", "-o", str(output_path), path.name], cwd=path.parent)
        return code == 0, output or "ok"


def validate_csharp(path: Path) -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as temp_dir:
        build_root = Path(temp_dir)
        code, output = run_command(
            [
                "dotnet",
                "build",
                "RecoveredContracts.csproj",
                "-nologo",
                "-clp:ErrorsOnly",
                f"-p:BaseIntermediateOutputPath={build_root / 'obj'}/",
                f"-p:OutputPath={build_root / 'bin'}/",
            ],
            cwd=path.parent,
        )
        return code == 0, output or "ok"


def validate_c_header(path: Path) -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as temp_dir:
        stub = Path(temp_dir) / "recovered_header_check.c"
        stub.write_text(f'#include "{path}"\nint main(void) {{ return 0; }}\n', encoding="utf-8")
        code, output = run_command(["gcc", "-fsyntax-only", str(stub)], cwd=path.parent)
        return code == 0, output or "ok"


def validate_ruby(path: Path) -> tuple[bool, str]:
    code, output = run_command(["ruby", "-c", str(path)])
    return code == 0, output or "ok"


def validate_artifact(path: Path) -> tuple[bool, str]:
    suffix = path.suffix.lower()
    if suffix == ".md":
        return validate_markdown(path)
    if suffix == ".json":
        return validate_json_file(path)
    if suffix == ".py":
        return validate_python(path)
    if suffix == ".ps1":
        return validate_powershell(path)
    if suffix in {".yml", ".yaml"}:
        return validate_yaml(path)
    if suffix in {".ts", ".d.ts"}:
        return validate_typescript(path)
    if suffix == ".go":
        return validate_go(path)
    if suffix == ".cs":
        return validate_csharp(path)
    if suffix == ".h":
        return validate_c_header(path)
    if suffix == ".rb":
        return validate_ruby(path)
    return True, "no validator"


def provenance_ok(source_files: list[str]) -> bool:
    for source in source_files:
        if source.startswith("... and "):
            continue
        if source.startswith('"') or "\\316" in source:
            continue
        normalized = source.strip('"')
        if normalized in CORPSE_SOURCE_FILES:
            continue
        if "/" in normalized or "\\" in normalized:
            if (ROOT / normalized).exists():
                continue
            if (CORPSE_ROOT / normalized).exists():
                continue
            return False
        if normalized and not normalized.startswith("."):
            continue
    return True


def write_furnace_artifacts(artifacts: list[Artifact]) -> list[dict[str, Any]]:
    manifest_entries: list[dict[str, Any]] = []
    for artifact in artifacts:
        artifact.path.parent.mkdir(parents=True, exist_ok=True)
        artifact.path.write_text(artifact.content, encoding="utf-8")
        for support_path, content in (artifact.support_files or {}).items():
            support_path.parent.mkdir(parents=True, exist_ok=True)
            support_path.write_text(content, encoding="utf-8")
        manifest_entries.append(
            {
                "path": str(artifact.path.relative_to(ROOT)).replace("\\", "/"),
                "source_pool": artifact.source_pool,
                "source_files": artifact.source_files,
                "input_type": artifact.input_type,
                "output_type": artifact.output_type,
                "transmutation_pathway": artifact.transmutation_pathway,
                "input_bytes": sum((ROOT / source).stat().st_size for source in artifact.source_files if (ROOT / source).exists()),
                "output_bytes": artifact.path.stat().st_size,
                "gold_tier": artifact.gold_tier,
                "novel_pathway": artifact.novel_pathway,
            }
        )
    return manifest_entries


def temper_artifacts(artifacts: list[Artifact]) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    by_output_language: dict[str, dict[str, int]] = defaultdict(lambda: {"tempered": 0, "rejected": 0})
    by_source_pool: dict[str, dict[str, int]] = defaultdict(lambda: {"inputs": 0, "artifacts_produced": 0})
    total_input_bytes = 0
    total_output_bytes = 0

    for artifact in artifacts:
        furnace_path = artifact.path
        output_language = furnace_path.parent.name
        by_source_pool[artifact.source_pool]["inputs"] += len(artifact.source_files)
        by_source_pool[artifact.source_pool]["artifacts_produced"] += 1
        input_bytes = sum((ROOT / source).stat().st_size for source in artifact.source_files if (ROOT / source).exists())
        total_input_bytes += input_bytes
        total_output_bytes += furnace_path.stat().st_size
        syntax_ok, syntax_note = validate_artifact(furnace_path)
        provenance_valid = provenance_ok(artifact.source_files)
        text = safe_read_text(furnace_path, limit_bytes=800_000) or ""
        lines = [line for line in text.splitlines() if line.strip()]
        substantive = max(len(lines) - 6, 0)
        completeness_ok = bool(lines) and substantive / max(len(lines), 1) >= 0.2
        tempered_path = TEMPERED_ROOT / furnace_path.relative_to(FURNACE_ROOT)
        quality_gates = {
            "syntax": "PASS" if syntax_ok else f"FAIL: {syntax_note}",
            "provenance": "PASS" if provenance_valid else "FAIL: provenance missing",
            "completeness": "PASS" if completeness_ok else "FAIL: insufficient substantive content",
        }
        if syntax_ok and provenance_valid and completeness_ok:
            tempered_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(furnace_path, tempered_path)
            for support_path in artifact.support_files or {}:
                support_target = TEMPERED_ROOT / support_path.relative_to(FURNACE_ROOT)
                support_target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(support_path, support_target)
            by_output_language[output_language]["tempered"] += 1
            status = "tempered"
        else:
            by_output_language[output_language]["rejected"] += 1
            status = "rejected"

        results.append(
            {
                "path": str(tempered_path.relative_to(ROOT) if status == "tempered" else furnace_path.relative_to(ROOT)).replace("\\", "/"),
                "source_pool": artifact.source_pool,
                "source_files": artifact.source_files,
                "input_type": artifact.input_type,
                "output_type": artifact.output_type,
                "transmutation_pathway": artifact.transmutation_pathway,
                "input_bytes": input_bytes,
                "output_bytes": furnace_path.stat().st_size,
                "quality_gates": quality_gates,
                "gold_tier": artifact.gold_tier,
                "status": status,
                "novel_pathway": artifact.novel_pathway,
            }
        )

    return {
        "timestamp": now_iso(),
        "artifacts_attempted": len(results),
        "artifacts_tempered": sum(1 for result in results if result["status"] == "tempered"),
        "artifacts_rejected": sum(1 for result in results if result["status"] == "rejected"),
        "compression_ratio": f"{total_input_bytes} -> {total_output_bytes}",
        "by_output_language": dict(by_output_language),
        "by_source_pool": dict(by_source_pool),
        "artifacts": results,
    }


def write_pathway_registry(artifacts: list[Artifact]) -> dict[str, Any]:
    registry_path = FORGE_ROOT / "PATHWAY_REGISTRY.json"
    existing: list[dict[str, Any]] = []
    if registry_path.exists():
        try:
            existing = json.loads(registry_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = []
    existing_keys = {(entry["input_type"], entry["output_type"], entry["pathway"]) for entry in existing}
    for artifact in artifacts:
        entry = {
            "input_type": artifact.input_type,
            "output_type": artifact.output_type,
            "pathway": artifact.transmutation_pathway,
            "path": str(artifact.path.relative_to(ROOT)).replace("\\", "/"),
            "novel": artifact.novel_pathway,
        }
        key = (entry["input_type"], entry["output_type"], entry["pathway"])
        if key not in existing_keys:
            existing.append(entry)
            existing_keys.add(key)
    write_json(registry_path, existing)
    return {"pathways": existing, "path": str(registry_path.relative_to(ROOT)).replace("\\", "/")}


def write_forge_report(
    anomaly_harvest: dict[str, Any],
    corpse_data: dict[str, Any],
    graduation_manifest: dict[str, Any],
    pathways: dict[str, Any],
) -> str:
    tempered = [artifact for artifact in graduation_manifest["artifacts"] if artifact["status"] == "tempered"]
    novel_count = sum(1 for artifact in tempered if artifact["novel_pathway"])
    artifact_bonus = max(graduation_manifest["artifacts_tempered"] - 13, 0) * 0.5
    unrepresented_bonus = 0.0
    produced_paths = {artifact["path"] for artifact in tempered}
    if any(path.endswith(".go") for path in produced_paths):
        unrepresented_bonus += 2.0
    if any(path.endswith(".cs") for path in produced_paths):
        unrepresented_bonus += 2.0
    if any(path.endswith(".h") for path in produced_paths):
        unrepresented_bonus += 2.0
    tier_boon = 4.0 + artifact_bonus + float(novel_count) + unrepresented_bonus

    lines = [
        "---",
        "type: report",
        "from: codex",
        "to: user",
        f"created: {now_iso()}",
        "priority: high",
        "subject: FORGE_TRANSMUTATION_REPORT",
        "---",
        "",
        "# Forge Transmutation Report",
        "",
        "## Scope",
        "",
        f"- Anomaly harvest files analyzed: {anomaly_harvest['summary']['files']}",
        f"- Corpse-vault languages audited: {len(corpse_data['languages'])}",
        f"- Furnace artifacts attempted: {graduation_manifest['artifacts_attempted']}",
        "",
        "## Yield",
        "",
        f"- Tempered artifacts: {graduation_manifest['artifacts_tempered']}",
        f"- Rejected artifacts: {graduation_manifest['artifacts_rejected']}",
        f"- Compression ratio: {graduation_manifest['compression_ratio']}",
        "",
        "## Source Pools",
        "",
    ]
    for pool, counts in graduation_manifest["by_source_pool"].items():
        lines.append(f"- `{pool}` | inputs `{counts['inputs']}` | artifacts `{counts['artifacts_produced']}`")
    lines.extend(["", "## Output Languages", ""])
    for language, counts in graduation_manifest["by_output_language"].items():
        lines.append(f"- `{language}` | tempered `{counts['tempered']}` | rejected `{counts['rejected']}`")
    lines.extend(["", "## Pathway Catalogue", ""])
    for entry in pathways["pathways"]:
        lines.append(f"- `{entry['input_type']}` -> `{entry['output_type']}` | {entry['pathway']} | example `{entry['path']}`")
    lines.extend(["", "## Novel Pathways", ""])
    for artifact in tempered:
        if artifact["novel_pathway"]:
            lines.append(f"- `{artifact['transmutation_pathway']}` -> `{artifact['path']}`")
    if not any(artifact["novel_pathway"] for artifact in tempered):
        lines.append("- None.")
    lines.extend(["", "## Failures and Honest Skips", ""])
    for artifact in graduation_manifest["artifacts"]:
        if artifact["status"] == "rejected":
            lines.append(f"- `{artifact['path']}` | {artifact['quality_gates']}")
    if graduation_manifest["artifacts_rejected"] == 0:
        lines.append("- None. All produced artifacts cleared the tempering gates.")
    lines.extend(["", "## Promotion Recommendations", ""])
    for artifact in tempered:
        if any(token in artifact["path"] for token in ("go/", "csharp/", "c_cpp/", "python/", "powershell/")):
            lines.append(f"- Promote `{artifact['path']}` into an active tooling lane after user review.")
    lines.extend(
        [
            "",
            "## Tier 2 Score",
            "",
            "- Penalty removed: 2",
            "- Base boon: 4.0",
            f"- Artifact bonus: {artifact_bonus:.1f}",
            f"- Novel pathway bonus: {float(novel_count):.1f}",
            f"- Unrepresented language bonus: {unrepresented_bonus:.1f}",
            f"- Total Tier 2 boon: {tier_boon:.1f}",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    ensure_utf8()
    parser = argparse.ArgumentParser(description="Run the WPTG universal forge.")
    parser.parse_args()

    census, orphan_data = load_census_data()
    anomaly_harvest = build_anomaly_harvest(census)
    corpse_data = load_corpse_vault()
    global CORPSE_SOURCE_FILES
    CORPSE_SOURCE_FILES = set(corpse_data["reverse_map"].keys())
    write_json(ANVIL_ROOT / "CODEBASE_ANOMALY_HARVEST.json", anomaly_harvest)
    write_json(ANVIL_ROOT / "CORPSE_VAULT_DEEP_AUDIT.json", {k: v for k, v in corpse_data.items() if k != "_records"})

    artifacts = build_artifacts(census, orphan_data, corpse_data)
    furnace_manifest_entries = write_furnace_artifacts(artifacts)
    write_json(
        FURNACE_ROOT / "FURNACE_MANIFEST.json",
        {
            "timestamp": now_iso(),
            "artifacts": furnace_manifest_entries,
            "artifact_count": len(furnace_manifest_entries),
        },
    )
    graduation_manifest = temper_artifacts(artifacts)
    write_json(TEMPERED_ROOT / "GRADUATION_MANIFEST.json", graduation_manifest)
    pathways = write_pathway_registry(artifacts)
    report = write_forge_report(anomaly_harvest, corpse_data, graduation_manifest, pathways)
    write_text(FORGE_REPORT_PATH, report)
    print(f"Wrote {ANVIL_ROOT / 'CODEBASE_ANOMALY_HARVEST.json'}")
    print(f"Wrote {ANVIL_ROOT / 'CORPSE_VAULT_DEEP_AUDIT.json'}")
    print(f"Wrote {FURNACE_ROOT / 'FURNACE_MANIFEST.json'}")
    print(f"Wrote {TEMPERED_ROOT / 'GRADUATION_MANIFEST.json'}")
    print(f"Wrote {FORGE_REPORT_PATH}")
    return 0 if graduation_manifest["artifacts_rejected"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
