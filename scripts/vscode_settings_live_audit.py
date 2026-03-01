#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""
VS Code Settings Live Audit — validate workspace settings against the local IDE.

Cross-references `.vscode/settings.json` with:
- the current VS Code Insiders install
- built-in extension configuration manifests
- user-installed Insiders extension manifests
- repo-local extension manifests

This replaces comment-lore like "unsupported in the current build" with a
repeatable audit that can be rerun after every editor or extension update.

@SID:           TOOL_VSCODE_SETTINGS_LIVE_AUDIT_V1
@Type:          Utility
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.lib.shared import configure_utf8_output, find_repo_root

COMMENTED_SETTING_RE = re.compile(r'^\s*//\s*"([^"]+)"\s*:')
ACTIVE_SETTING_RE = re.compile(r'^\s*"([^"]+)"\s*:')
INSTALL_HASH_RE = re.compile(r"^[0-9a-f]{10}$")
VSCODE_ENV_RE = re.compile(r"\$\{env:([^}]+)\}")
SKIP_DIRS: set[str] = {
    ".git",
    "node_modules",
    "dist",
    "build",
    "target",
    ".venv",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    "dumpster-dive",
    ".next",
    "book",
}


def strip_json_comments(text: str) -> str:
    """Strip JSONC comments while preserving string contents."""
    out: list[str] = []
    in_string = False
    in_line_comment = False
    in_block_comment = False
    escaped = False
    quote_char = ""
    i = 0

    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""

        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
                out.append(ch)
            i += 1
            continue

        if in_block_comment:
            if ch == "*" and nxt == "/":
                in_block_comment = False
                i += 2
            else:
                i += 1
            continue

        if in_string:
            out.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote_char:
                in_string = False
            i += 1
            continue

        if ch in ("'", '"'):
            in_string = True
            quote_char = ch
            out.append(ch)
            i += 1
            continue

        if ch == "/" and nxt == "/":
            in_line_comment = True
            i += 2
            continue

        if ch == "/" and nxt == "*":
            in_block_comment = True
            i += 2
            continue

        out.append(ch)
        i += 1

    return "".join(out)


def strip_trailing_json_commas(text: str) -> str:
    """Strip trailing commas before } or ] while preserving string contents."""
    out: list[str] = []
    in_string = False
    escaped = False
    quote_char = ""
    i = 0

    while i < len(text):
        ch = text[i]

        if in_string:
            out.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote_char:
                in_string = False
            i += 1
            continue

        if ch in ("'", '"'):
            in_string = True
            quote_char = ch
            out.append(ch)
            i += 1
            continue

        if ch == ",":
            j = i + 1
            while j < len(text) and text[j] in " \t\r\n":
                j += 1
            if j < len(text) and text[j] in "}]":
                i += 1
                continue

        out.append(ch)
        i += 1

    return "".join(out)


def load_json(path: Path, *, jsonc: bool = False) -> Any:
    text = path.read_text(encoding="utf-8")
    if jsonc:
        text = strip_json_comments(text)
        text = strip_trailing_json_commas(text)
    return json.loads(text)


def rel(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root).as_posix()
    except ValueError:
        return path.resolve().as_posix()


@dataclass(slots=True)
class SettingEntry:
    key: str
    line: int
    kind: str
    note: str | None = None
    value: Any = None


def json_type_matches(value: Any, expected_type: str) -> bool:
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "null":
        return value is None
    return True


def extract_settings(settings_path: Path) -> tuple[list[SettingEntry], list[SettingEntry]]:
    text = settings_path.read_text(encoding="utf-8")
    data = load_json(settings_path, jsonc=True)
    lines = text.splitlines()

    active_by_key: dict[str, SettingEntry] = {}
    commented: list[SettingEntry] = []

    for index, line in enumerate(lines, start=1):
        commented_match = COMMENTED_SETTING_RE.match(line)
        if commented_match:
            key = commented_match.group(1)
            note = collect_preceding_comment_block(lines, index - 1)
            commented.append(SettingEntry(key=key, line=index, kind="commented", note=note))
            continue

        active_match = ACTIVE_SETTING_RE.match(line)
        if not active_match:
            continue
        key = active_match.group(1)
        if key in data and key not in active_by_key:
            active_by_key[key] = SettingEntry(
                key=key,
                line=index,
                kind="active",
                value=data.get(key),
            )

    active = [active_by_key[key] for key in data.keys()]
    return active, commented


def collect_preceding_comment_block(lines: list[str], zero_based_index: int) -> str | None:
    note_lines: list[str] = []
    idx = zero_based_index - 1

    while idx >= 0:
        line = lines[idx]
        stripped = line.strip()
        if not stripped:
            break
        if not stripped.startswith("//"):
            break
        if COMMENTED_SETTING_RE.match(line):
            break
        note_lines.append(stripped.removeprefix("//").strip())
        idx -= 1

    note_lines.reverse()
    note_lines = [line for line in note_lines if line]
    if not note_lines:
        return None
    return " ".join(note_lines)


def find_insiders_install_root() -> Path | None:
    base = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Microsoft VS Code Insiders"
    if not base.exists():
        return None
    candidates = [child for child in base.iterdir() if child.is_dir() and INSTALL_HASH_RE.fullmatch(child.name)]
    if candidates:
        return sorted(candidates)[-1]
    return None


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8")


def get_insiders_version(install_root: Path | None) -> dict[str, str | None]:
    candidates: list[Path | str] = ["code-insiders"]
    if install_root:
        candidates.insert(0, install_root.parent / "bin" / "code-insiders.cmd")
        candidates.insert(1, install_root.parent / "bin" / "code-insiders")

    result: subprocess.CompletedProcess[str] | None = None
    for candidate in candidates:
        try:
            result = run_command([str(candidate), "--version"])
        except FileNotFoundError:
            continue
        if result.returncode == 0:
            break

    if result is None or result.returncode != 0:
        return {"version": None, "commit": None, "arch": None}

    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return {
        "version": lines[0] if len(lines) > 0 else None,
        "commit": lines[1] if len(lines) > 1 else None,
        "arch": lines[2] if len(lines) > 2 else None,
    }


def iter_manifest_paths(repo_root: Path, install_root: Path | None) -> list[tuple[str, Path]]:
    manifest_paths: list[tuple[str, Path]] = []

    if install_root:
        builtin_root = install_root / "resources" / "app" / "extensions"
        if builtin_root.exists():
            manifest_paths.extend(("builtin-extension", path) for path in builtin_root.rglob("package.json"))

    user_root = Path(os.environ.get("USERPROFILE", "")) / ".vscode-insiders" / "extensions"
    if user_root.exists():
        manifest_paths.extend(("installed-extension", path) for path in user_root.rglob("package.json"))

    repo_extensions_root = repo_root / "extensions"
    if repo_extensions_root.exists():
        manifest_paths.extend(("repo-extension", path) for path in repo_extensions_root.glob("*/package.json"))

    return manifest_paths


def collect_configuration_properties(node: Any) -> set[str]:
    keys: set[str] = set()

    if isinstance(node, dict):
        properties = node.get("properties")
        if isinstance(properties, dict):
            for key in properties.keys():
                if isinstance(key, str):
                    keys.add(key)
        for value in node.values():
            keys.update(collect_configuration_properties(value))
    elif isinstance(node, list):
        for item in node:
            keys.update(collect_configuration_properties(item))

    return keys


def build_manifest_index(repo_root: Path, install_root: Path | None) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}

    for source_kind, manifest_path in iter_manifest_paths(repo_root, install_root):
        try:
            package = load_json(manifest_path)
        except Exception:
            continue

        contributes = package.get("contributes", {})
        config_node = contributes.get("configuration")
        if config_node is None:
            continue

        keys = sorted(collect_configuration_properties(config_node))
        if not keys:
            continue

        label = f"{source_kind}:{rel(manifest_path, repo_root)}"
        for key in keys:
            index.setdefault(key, []).append(label)

    return index


def build_manifest_schema_index(repo_root: Path, install_root: Path | None) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = {}

    for source_kind, manifest_path in iter_manifest_paths(repo_root, install_root):
        try:
            package = load_json(manifest_path)
        except Exception:
            continue

        contributes = package.get("contributes", {})
        config_node = contributes.get("configuration")
        if config_node is None:
            continue

        source_label = f"{source_kind}:{rel(manifest_path, repo_root)}"
        collect_configuration_schemas(config_node, source_label, index)

    return index


def collect_configuration_schemas(
    node: Any,
    source_label: str,
    index: dict[str, list[dict[str, Any]]],
) -> None:
    if isinstance(node, dict):
        properties = node.get("properties")
        if isinstance(properties, dict):
            for key, schema in properties.items():
                if isinstance(key, str) and isinstance(schema, dict):
                    index.setdefault(key, []).append({"source": source_label, "schema": schema})
        for value in node.values():
            collect_configuration_schemas(value, source_label, index)
    elif isinstance(node, list):
        for item in node:
            collect_configuration_schemas(item, source_label, index)


def build_catalogs(repo_root: Path, install_root: Path | None) -> dict[str, dict[str, list[str]]]:
    catalogs: dict[str, dict[str, list[str]]] = {
        "themes": {},
        "iconThemes": {},
        "productIconThemes": {},
        "languages": {},
    }

    for source_kind, manifest_path in iter_manifest_paths(repo_root, install_root):
        try:
            package = load_json(manifest_path)
        except Exception:
            continue

        contributes = package.get("contributes", {})
        source_label = f"{source_kind}:{rel(manifest_path, repo_root)}"

        for theme in contributes.get("themes", []):
            label = theme.get("label")
            if isinstance(label, str):
                catalogs["themes"].setdefault(label, []).append(source_label)

        for theme in contributes.get("iconThemes", []):
            theme_id = theme.get("id")
            if isinstance(theme_id, str):
                catalogs["iconThemes"].setdefault(theme_id, []).append(source_label)

        for theme in contributes.get("productIconThemes", []):
            theme_id = theme.get("id")
            if isinstance(theme_id, str):
                catalogs["productIconThemes"].setdefault(theme_id, []).append(source_label)

        for language in contributes.get("languages", []):
            language_id = language.get("id")
            if isinstance(language_id, str):
                catalogs["languages"].setdefault(language_id, []).append(source_label)

    return catalogs


def build_workspace_context(repo_root: Path) -> dict[str, Any]:
    relative_files: list[str] = []
    basenames: set[str] = set()
    suffixes: set[str] = set()

    for dirpath, dirnames, filenames in os.walk(repo_root):
        dirnames[:] = [name for name in dirnames if name not in SKIP_DIRS]
        current = Path(dirpath)
        for filename in filenames:
            path = current / filename
            relative_path = rel(path, repo_root)
            relative_files.append(relative_path)
            basenames.add(filename.lower())
            suffix = path.suffix.lower().lstrip(".")
            if suffix:
                suffixes.add(suffix)

    expected_languages: set[str] = set()
    if any(suffix in suffixes for suffix in ("vert", "frag", "geom", "comp", "tesc", "tese")):
        expected_languages.add("glsl")
    if "toml" in suffixes:
        expected_languages.add("toml")
    if "spv" in suffixes:
        expected_languages.add("binary")

    return {
        "relative_files": relative_files,
        "basenames": basenames,
        "suffixes": suffixes,
        "expected_languages": expected_languages,
    }


def pattern_matches_workspace(pattern: str, workspace_context: dict[str, Any]) -> bool:
    normalized = pattern.replace("\\", "/")
    if "*" not in normalized and "?" not in normalized and "[" not in normalized:
        return normalized.lower() in workspace_context["basenames"]

    if normalized.startswith("*.") and normalized.count("*") == 1:
        suffix = normalized[2:].lower()
        return suffix in workspace_context["suffixes"]

    for relative_path in workspace_context["relative_files"]:
        if fnmatch.fnmatch(relative_path.lower(), normalized.lower()):
            return True
        if fnmatch.fnmatch(Path(relative_path).name.lower(), normalized.lower()):
            return True
    return False


def find_core_hits(key: str, install_root: Path | None, repo_root: Path) -> list[str]:
    if not install_root:
        return []

    app_root = install_root / "resources" / "app"
    if not app_root.exists():
        return []

    try:
        result = run_command(
            [
                "rg",
                "-l",
                "-F",
                f'"{key}"',
                str(app_root / "out"),
            ]
        )
    except FileNotFoundError:
        return []
    if result.returncode not in (0, 1):
        return []

    hits = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return [f"core:{rel(Path(hit), repo_root)}" for hit in hits]


def schema_violations(value: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    if "oneOf" in schema:
        options = [option for option in schema.get("oneOf", []) if isinstance(option, dict)]
        if any(not schema_violations(value, option, path) for option in options):
            return []
        return [f"{path}: value does not satisfy any allowed schema variant"]

    if "anyOf" in schema:
        options = [option for option in schema.get("anyOf", []) if isinstance(option, dict)]
        if any(not schema_violations(value, option, path) for option in options):
            return []
        return [f"{path}: value does not satisfy any allowed schema variant"]

    if "enum" in schema and value not in schema["enum"]:
        return [f"{path}: value `{value}` not in enum {schema['enum']}"]

    schema_type = schema.get("type")
    if schema_type is not None:
        allowed_types = schema_type if isinstance(schema_type, list) else [schema_type]
        if not any(json_type_matches(value, item) for item in allowed_types if isinstance(item, str)):
            return [f"{path}: value has wrong type for schema {allowed_types}"]

    if isinstance(value, list) and isinstance(schema.get("items"), dict):
        for index, item in enumerate(value):
            violations = schema_violations(item, schema["items"], f"{path}[{index}]")
            if violations:
                return violations

    if isinstance(value, dict):
        properties = schema.get("properties")
        if isinstance(properties, dict):
            for key, item in value.items():
                if key in properties and isinstance(properties[key], dict):
                    violations = schema_violations(item, properties[key], f"{path}.{key}")
                    if violations:
                        return violations
        additional = schema.get("additionalProperties")
        if additional is False and isinstance(properties, dict):
            unknown = sorted(key for key in value.keys() if key not in properties)
            if unknown:
                return [f"{path}: unknown object keys {unknown}"]
        if isinstance(additional, dict):
            for key, item in value.items():
                if isinstance(properties, dict) and key in properties:
                    continue
                violations = schema_violations(item, additional, f"{path}.{key}")
                if violations:
                    return violations

    return []


def validate_manifest_schema(
    entry: SettingEntry,
    schema_index: dict[str, list[dict[str, Any]]],
) -> list[dict[str, str]]:
    schemas = schema_index.get(entry.key, [])
    if not schemas:
        return []

    for item in schemas:
        violations = schema_violations(entry.value, item["schema"])
        if not violations:
            return [{
                "name": "manifest-schema",
                "status": "ok",
                "detail": f"accepted by {item['source']}",
            }]

    first = schemas[0]
    violations = schema_violations(entry.value, first["schema"])
    detail = violations[0] if violations else f"value rejected by {first['source']}"
    return [{
        "name": "manifest-schema",
        "status": "drift",
        "detail": f"{detail} ({first['source']})",
    }]


def expand_vscode_env_vars(value: str) -> str:
    def replacer(match: re.Match[str]) -> str:
        return os.environ.get(match.group(1), "")

    return VSCODE_ENV_RE.sub(replacer, value)


def validate_custom_value(
    entry: SettingEntry,
    settings_data: dict[str, Any],
    catalogs: dict[str, dict[str, list[str]]],
    workspace_context: dict[str, Any],
    repo_root: Path,
) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    key = entry.key
    value = entry.value

    if key == "workbench.colorTheme" and isinstance(value, str):
        if value in catalogs["themes"]:
            checks.append({"name": "theme-label", "status": "ok", "detail": "theme label exists"})
        else:
            checks.append({"name": "theme-label", "status": "drift", "detail": f"theme label `{value}` not contributed by installed or repo manifests"})

    elif key == "workbench.iconTheme" and isinstance(value, str):
        if value in catalogs["iconThemes"]:
            checks.append({"name": "icon-theme-id", "status": "ok", "detail": "file icon theme id exists"})
        else:
            checks.append({"name": "icon-theme-id", "status": "drift", "detail": f"icon theme id `{value}` not contributed by installed or repo manifests"})

    elif key == "workbench.productIconTheme" and isinstance(value, str):
        if value in catalogs["productIconThemes"]:
            checks.append({"name": "product-icon-theme-id", "status": "ok", "detail": "product icon theme id exists"})
        else:
            checks.append({"name": "product-icon-theme-id", "status": "drift", "detail": f"product icon theme id `{value}` not contributed by installed or repo manifests"})

    elif key.startswith("[") and key.endswith("]"):
        language_id = key[1:-1]
        if language_id in catalogs["languages"]:
            checks.append({"name": "language-override", "status": "ok", "detail": f"language id `{language_id}` exists"})
        elif language_id in workspace_context["expected_languages"]:
            checks.append({
                "name": "language-override",
                "status": "warning",
                "detail": f"language id `{language_id}` is expected by workspace content but is not registered in the current VS Code profile",
            })
        else:
            checks.append({"name": "language-override", "status": "drift", "detail": f"language id `{language_id}` not contributed by installed or repo manifests"})

    elif key == "files.associations" and isinstance(value, dict):
        drift_pairs: list[str] = []
        warning_pairs: list[str] = []
        for pattern, language_id in value.items():
            if not isinstance(pattern, str) or not isinstance(language_id, str):
                continue
            if language_id in catalogs["languages"]:
                continue
            if language_id in workspace_context["expected_languages"] or pattern_matches_workspace(pattern, workspace_context):
                warning_pairs.append(f"{pattern} -> {language_id}")
            else:
                drift_pairs.append(f"{pattern} -> {language_id}")

        if drift_pairs:
            checks.append({"name": "file-associations", "status": "drift", "detail": f"unresolved associations {drift_pairs}"})
        elif warning_pairs:
            checks.append({
                "name": "file-associations",
                "status": "warning",
                "detail": f"stack-derived associations are not registered as local VS Code language ids {warning_pairs}",
            })
        else:
            checks.append({"name": "file-associations", "status": "ok", "detail": "all mapped language ids exist"})

    elif key == "terminal.integrated.defaultProfile.windows" and isinstance(value, str):
        profiles = settings_data.get("terminal.integrated.profiles.windows", {})
        if isinstance(profiles, dict) and value in profiles:
            checks.append({"name": "default-terminal-profile", "status": "ok", "detail": f"profile `{value}` exists"})
        else:
            checks.append({"name": "default-terminal-profile", "status": "drift", "detail": f"default profile `{value}` is not declared in terminal.integrated.profiles.windows"})

    elif key == "terminal.integrated.profiles.windows" and isinstance(value, dict):
        missing_paths: list[str] = []
        for profile_name, profile in value.items():
            if not isinstance(profile, dict):
                continue
            profile_path = profile.get("path")
            if not isinstance(profile_path, str):
                continue
            expanded = expand_vscode_env_vars(profile_path)
            if not Path(expanded).exists():
                missing_paths.append(f"{profile_name} -> {profile_path}")
        if missing_paths:
            checks.append({"name": "terminal-profile-paths", "status": "drift", "detail": f"missing profile executables {missing_paths}"})
        else:
            checks.append({"name": "terminal-profile-paths", "status": "ok", "detail": "all profile executables exist"})

    elif key == "terminal.integrated.env.windows" and isinstance(value, dict):
        path_value = value.get("PATH")
        if isinstance(path_value, str):
            missing_segments = []
            for segment in path_value.split(";"):
                segment = segment.strip()
                if not segment or segment == "${env:PATH}":
                    continue
                expanded = expand_vscode_env_vars(segment)
                if not Path(expanded).exists():
                    missing_segments.append(segment)
            if missing_segments:
                checks.append({"name": "terminal-env-path", "status": "drift", "detail": f"missing PATH segments {missing_segments}"})
            else:
                checks.append({"name": "terminal-env-path", "status": "ok", "detail": "all explicit PATH segments exist"})

    elif key == "chat.instructionsFilesLocations" and isinstance(value, dict):
        missing_paths = []
        for relative_path in value.keys():
            if not isinstance(relative_path, str):
                continue
            if not (repo_root / relative_path).exists():
                missing_paths.append(relative_path)
        if missing_paths:
            checks.append({"name": "instruction-files", "status": "drift", "detail": f"missing instruction files {missing_paths}"})
        else:
            checks.append({"name": "instruction-files", "status": "ok", "detail": "all instruction files exist"})

    elif key == "chat.mcp.serverSampling" and isinstance(value, dict):
        mcp_path = repo_root / ".vscode" / "mcp.json"
        if mcp_path.exists():
            mcp_data = load_json(mcp_path, jsonc=True)
            known_servers = sorted(
                key
                for key in mcp_data.get("servers", {}).keys()
                if isinstance(key, str)
            )
            unknown_servers = []
            for sampling_key in value.keys():
                if not isinstance(sampling_key, str):
                    continue
                server_name = sampling_key.rsplit(":", 1)[-1].strip()
                if server_name not in known_servers:
                    unknown_servers.append(server_name)
            if unknown_servers:
                checks.append({
                    "name": "mcp-server-sampling",
                    "status": "drift",
                    "detail": f"sampling references unknown MCP servers {sorted(set(unknown_servers))}; known servers are {known_servers}",
                })
            else:
                checks.append({"name": "mcp-server-sampling", "status": "ok", "detail": "all sampled MCP servers exist in .vscode/mcp.json"})

    return checks


def summarize_value_checks(checks: list[dict[str, str]]) -> str:
    if any(check["status"] == "drift" for check in checks):
        return "drift"
    if any(check["status"] == "warning" for check in checks):
        return "warning"
    if checks:
        return "ok"
    return "unchecked"


def classify_setting(
    entry: SettingEntry,
    manifest_index: dict[str, list[str]],
    schema_index: dict[str, list[dict[str, Any]]],
    install_root: Path | None,
    settings_data: dict[str, Any],
    catalogs: dict[str, dict[str, list[str]]],
    workspace_context: dict[str, Any],
    repo_root: Path,
) -> dict[str, Any]:
    value_checks: list[dict[str, str]] = []

    if entry.key.startswith("[") and entry.key.endswith("]"):
        value_checks = validate_custom_value(entry, settings_data, catalogs, workspace_context, repo_root)
        return {
            "key": entry.key,
            "line": entry.line,
            "kind": entry.kind,
            "status": "supported",
            "value_status": summarize_value_checks(value_checks),
            "value_checks": value_checks,
            "note": entry.note,
            "value": entry.value,
            "evidence": ["core:language-override-section"],
        }

    evidence = list(manifest_index.get(entry.key, []))
    if not evidence:
        evidence = find_core_hits(entry.key, install_root, repo_root)

    status = "supported" if evidence else "missing"
    if entry.kind == "active":
        value_checks.extend(validate_manifest_schema(entry, schema_index))
        value_checks.extend(validate_custom_value(entry, settings_data, catalogs, workspace_context, repo_root))

    return {
        "key": entry.key,
        "line": entry.line,
        "kind": entry.kind,
        "status": status,
        "value_status": summarize_value_checks(value_checks),
        "value_checks": value_checks,
        "note": entry.note,
        "value": entry.value,
        "evidence": evidence,
    }


def build_report(
    repo_root: Path,
    active: list[dict[str, Any]],
    commented: list[dict[str, Any]],
    version_info: dict[str, str | None],
    install_root: Path | None,
) -> str:
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%SZ")
    active_missing = [item for item in active if item["status"] == "missing"]
    active_value_drift = [item for item in active if item.get("value_status") == "drift"]
    active_value_warning = [item for item in active if item.get("value_status") == "warning"]
    commented_supported = [item for item in commented if item["status"] == "supported"]
    commented_missing = [item for item in commented if item["status"] == "missing"]

    lines: list[str] = []
    lines.append("# VS Code Settings Live Audit")
    lines.append("")
    lines.append(f"- Generated: {now}")
    lines.append(f"- Workspace: `{repo_root}`")
    lines.append(f"- VS Code Insiders: {version_info.get('version') or 'unresolved'}")
    lines.append(f"- Commit: {version_info.get('commit') or 'unresolved'}")
    lines.append(f"- Install root: `{install_root}`" if install_root else "- Install root: unresolved")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Active top-level settings: {len(active)}")
    lines.append(f"- Active settings without live evidence: {len(active_missing)}")
    lines.append(f"- Active settings with value drift: {len(active_value_drift)}")
    lines.append(f"- Active settings with integration warnings: {len(active_value_warning)}")
    lines.append(f"- Commented settings with live evidence now: {len(commented_supported)}")
    lines.append(f"- Commented settings still absent in live sources: {len(commented_missing)}")
    lines.append("")

    lines.append("## Active Settings Without Live Evidence")
    lines.append("")
    if active_missing:
        for item in active_missing:
            lines.append(f"- `{item['key']}` at line {item['line']}")
    else:
        lines.append("- None")
    lines.append("")

    lines.append("## Active Settings With Value Drift")
    lines.append("")
    if active_value_drift:
        for item in active_value_drift:
            lines.append(f"- `{item['key']}` at line {item['line']}")
            for check in item.get("value_checks", []):
                if check["status"] == "drift":
                    lines.append(f"  drift: {check['detail']}")
    else:
        lines.append("- None")
    lines.append("")

    lines.append("## Active Settings With Integration Warnings")
    lines.append("")
    if active_value_warning:
        for item in active_value_warning:
            lines.append(f"- `{item['key']}` at line {item['line']}")
            for check in item.get("value_checks", []):
                if check["status"] == "warning":
                    lines.append(f"  warning: {check['detail']}")
    else:
        lines.append("- None")
    lines.append("")

    lines.append("## Commented Settings That Now Exist")
    lines.append("")
    if commented_supported:
        for item in commented_supported:
            evidence = ", ".join(item["evidence"][:3])
            lines.append(f"- `{item['key']}` at line {item['line']}")
            if item.get("note"):
                lines.append(f"  note: {item['note']}")
            lines.append(f"  evidence: {evidence}")
    else:
        lines.append("- None")
    lines.append("")

    lines.append("## Commented Settings Still Absent")
    lines.append("")
    if commented_missing:
        for item in commented_missing:
            lines.append(f"- `{item['key']}` at line {item['line']}")
            if item.get("note"):
                lines.append(f"  note: {item['note']}")
    else:
        lines.append("- None")
    lines.append("")

    lines.append("## Supported Commented Settings Matrix")
    lines.append("")
    lines.append("| Key | Line | Status | Evidence |")
    lines.append("| --- | ---: | --- | --- |")
    for item in commented:
        evidence = "<br>".join(item["evidence"][:2]) if item["evidence"] else "none"
        lines.append(f"| `{item['key']}` | {item['line']} | {item['status']} | {evidence} |")
    lines.append("")

    return "\n".join(lines) + "\n"


def build_json_payload(
    repo_root: Path,
    active: list[dict[str, Any]],
    commented: list[dict[str, Any]],
    version_info: dict[str, str | None],
    install_root: Path | None,
) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "workspace": str(repo_root),
        "vscode_insiders": {
            **version_info,
            "install_root": str(install_root) if install_root else None,
        },
        "summary": {
            "active_count": len(active),
            "active_missing_count": sum(1 for item in active if item["status"] == "missing"),
            "active_value_drift_count": sum(1 for item in active if item.get("value_status") == "drift"),
            "active_value_warning_count": sum(1 for item in active if item.get("value_status") == "warning"),
            "commented_count": len(commented),
            "commented_supported_count": sum(1 for item in commented if item["status"] == "supported"),
            "commented_missing_count": sum(1 for item in commented if item["status"] == "missing"),
        },
        "active": active,
        "commented": commented,
    }


def main() -> int:
    configure_utf8_output()

    parser = argparse.ArgumentParser(
        description="Audit .vscode/settings.json against the live local VS Code Insiders install."
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown.")
    parser.add_argument("--output", type=Path, help="Optional output path.")
    parser.add_argument(
        "--report",
        action="store_true",
        help="Write the default Markdown report to .vscode/SETTINGS_LIVE_AUDIT.md.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when active settings lack live evidence, active values drift, or commented settings have come back.",
    )
    args = parser.parse_args()

    repo_root = find_repo_root(Path(__file__).resolve())
    settings_path = repo_root / ".vscode" / "settings.json"
    settings_data = load_json(settings_path, jsonc=True)
    workspace_context = build_workspace_context(repo_root)

    active_entries, commented_entries = extract_settings(settings_path)
    install_root = find_insiders_install_root()
    version_info = get_insiders_version(install_root)
    manifest_index = build_manifest_index(repo_root, install_root)
    schema_index = build_manifest_schema_index(repo_root, install_root)
    catalogs = build_catalogs(repo_root, install_root)

    active = [
        classify_setting(entry, manifest_index, schema_index, install_root, settings_data, catalogs, workspace_context, repo_root)
        for entry in active_entries
    ]
    commented = [
        classify_setting(entry, manifest_index, schema_index, install_root, settings_data, catalogs, workspace_context, repo_root)
        for entry in commented_entries
    ]

    if args.json:
        rendered = json.dumps(
            build_json_payload(repo_root, active, commented, version_info, install_root),
            indent=2,
            ensure_ascii=False,
        )
    else:
        rendered = build_report(repo_root, active, commented, version_info, install_root)

    output_path = args.output
    if args.report and output_path is None:
        output_path = repo_root / ".vscode" / "SETTINGS_LIVE_AUDIT.md"

    if output_path:
        output_path.write_text(rendered if rendered.endswith("\n") else rendered + "\n", encoding="utf-8")
    else:
        print(rendered)

    if args.strict:
        active_missing = any(item["status"] == "missing" for item in active)
        active_value_drift = any(item.get("value_status") == "drift" for item in active)
        commented_supported = any(item["status"] == "supported" for item in commented)
        return 1 if (active_missing or active_value_drift or commented_supported) else 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
