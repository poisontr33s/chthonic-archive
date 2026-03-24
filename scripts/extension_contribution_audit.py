#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: extension_contribution_audit.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Lane-aware extension contribution validator for Part 4.

@SID:           EXTENSION_CONTRIBUTION_AUDIT_V1
@Shabti:        CLI Script
@Purpose:       Validate non-frozen VS Code contribution chains and report lane-excluded skips explicitly.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.lib.shared import configure_utf8_output, find_repo_root
from scripts.wptg_common import now_iso, path_is_excluded, write_json, write_text

COMMAND_RE = re.compile(r"registerCommand\(\s*['\"]([^'\"]+)['\"]")


@dataclass(slots=True)
class ValidationContext:
    repo_root: Path
    extension_root: Path
    package_path: Path
    source_path: Path
    dist_path: Path


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_extension_rel(path_value: str) -> str:
    cleaned = path_value.replace("\\", "/").removeprefix("./")
    return f"extensions/chthonic-archive/{cleaned}"


def read_registered_commands(source_path: Path, dist_path: Path) -> dict[str, list[str]]:
    registered_in_source = set(COMMAND_RE.findall(source_path.read_text(encoding="utf-8")))
    registered_in_dist = set(COMMAND_RE.findall(dist_path.read_text(encoding="utf-8")))
    return {
        "source": sorted(registered_in_source),
        "dist": sorted(registered_in_dist),
        "combined": sorted(registered_in_source | registered_in_dist),
    }


def command_entries(package: dict[str, Any]) -> list[dict[str, Any]]:
    return package.get("contributes", {}).get("commands", [])


def menu_command_refs(package: dict[str, Any]) -> list[dict[str, str]]:
    menus = package.get("contributes", {}).get("menus", {})
    refs: list[dict[str, str]] = []
    for menu_id, entries in menus.items():
        for entry in entries:
            command = entry.get("command")
            if command:
                refs.append({"menu": menu_id, "command": command})
    return refs


def validate_commands_chain(
    package: dict[str, Any],
    registered_commands: set[str],
) -> dict[str, Any]:
    declared = [entry["command"] for entry in command_entries(package) if entry.get("command")]
    declared_set = set(declared)
    missing_registrations = sorted(command for command in declared if command not in registered_commands)
    orphan_menus = [
        ref for ref in menu_command_refs(package) if ref["command"] not in declared_set
    ]
    errors = [
        f"Missing registration: {command}" for command in missing_registrations
    ] + [
        f"Orphan menu reference: {ref['menu']} -> {ref['command']}" for ref in orphan_menus
    ]
    return {
        "status": "pass" if not errors else "fail",
        "declared": len(declared),
        "registered": len([command for command in declared if command in registered_commands]),
        "missing_registrations": missing_registrations,
        "orphan_menus": orphan_menus,
        "errors": errors,
        "warnings": [],
    }


def type_matches(declared_type: Any, value: Any) -> bool:
    if isinstance(declared_type, list):
        return any(type_matches(candidate, value) for candidate in declared_type)
    if declared_type == "string":
        return isinstance(value, str)
    if declared_type == "boolean":
        return isinstance(value, bool)
    if declared_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if declared_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if declared_type == "array":
        return isinstance(value, list)
    if declared_type == "object":
        return isinstance(value, dict)
    if declared_type == "null":
        return value is None
    return True


def validate_configuration_chain(package: dict[str, Any]) -> dict[str, Any]:
    properties = package.get("contributes", {}).get("configuration", {}).get("properties", {})
    namespace_violations: list[str] = []
    type_mismatches: list[dict[str, Any]] = []

    for key, spec in properties.items():
        if not key.startswith("chthonic."):
            namespace_violations.append(key)
        if "default" in spec and "type" in spec and not type_matches(spec["type"], spec["default"]):
            type_mismatches.append(
                {
                    "property": key,
                    "declared_type": spec["type"],
                    "default": spec["default"],
                }
            )

    errors = [f"Namespace violation: {key}" for key in namespace_violations] + [
        f"Type mismatch: {item['property']} expects {item['declared_type']}"
        for item in type_mismatches
    ]
    return {
        "status": "pass" if not errors else "fail",
        "properties": len(properties),
        "namespace_violations": namespace_violations,
        "type_mismatches": type_mismatches,
        "errors": errors,
        "warnings": [],
    }


def skipped_chain(label: str, paths: list[str]) -> dict[str, Any]:
    warnings = [
        f"{label} skipped because downstream targets are inside the lane exclusion table."
    ]
    return {
        "status": "skipped_lane_exclusion",
        "declared": len(paths),
        "valid": 0,
        "skipped_paths": paths,
        "errors": [],
        "warnings": warnings,
    }


def validate_excluded_theme_chains(package: dict[str, Any]) -> dict[str, dict[str, Any]]:
    themes = package.get("contributes", {}).get("themes", [])
    icon_themes = package.get("contributes", {}).get("iconThemes", [])
    product_icon_themes = package.get("contributes", {}).get("productIconThemes", [])

    def collect_paths(entries: list[dict[str, Any]]) -> list[str]:
        return [normalize_extension_rel(entry["path"]) for entry in entries if entry.get("path")]

    theme_paths = collect_paths(themes)
    file_icon_paths = collect_paths(icon_themes)
    product_icon_paths = collect_paths(product_icon_themes)

    assert all(path_is_excluded(path) for path in theme_paths)
    assert all(path_is_excluded(path) for path in file_icon_paths)
    assert all(path_is_excluded(path) for path in product_icon_paths)

    return {
        "color_themes": skipped_chain("Color themes", theme_paths),
        "file_icon_theme": skipped_chain("File icon theme", file_icon_paths),
        "product_icon_theme": skipped_chain("Product icon theme", product_icon_paths),
    }


def build_self_check(package: dict[str, Any], registered_commands: set[str]) -> dict[str, Any]:
    broken = copy.deepcopy(package)
    broken.setdefault("contributes", {}).setdefault("commands", []).append(
        {"command": "chthonic.syntheticBroken", "title": "Synthetic broken command"}
    )
    broken["contributes"].setdefault("menus", {}).setdefault("commandPalette", []).append(
        {"command": "chthonic.syntheticOrphan"}
    )
    broken.setdefault("contributes", {}).setdefault("configuration", {}).setdefault(
        "properties", {}
    )["chthonic.syntheticBroken"] = {"type": "boolean", "default": "not-a-bool"}

    broken_commands = validate_commands_chain(broken, registered_commands)
    broken_config = validate_configuration_chain(broken)
    passed = bool(
        broken_commands["missing_registrations"]
        and broken_commands["orphan_menus"]
        and broken_config["type_mismatches"]
    )
    return {
        "passed": passed,
        "detected": {
            "missing_registrations": broken_commands["missing_registrations"],
            "orphan_menus": broken_commands["orphan_menus"],
            "type_mismatches": broken_config["type_mismatches"],
        },
    }


def build_payload(ctx: ValidationContext) -> dict[str, Any]:
    package = load_json(ctx.package_path)
    registered = read_registered_commands(ctx.source_path, ctx.dist_path)
    registered_set = set(registered["combined"])

    chains = validate_excluded_theme_chains(package)
    chains["commands"] = validate_commands_chain(package, registered_set)
    chains["configuration"] = validate_configuration_chain(package)

    error_count = sum(len(chain["errors"]) for chain in chains.values())
    warning_count = sum(len(chain["warnings"]) for chain in chains.values())
    skipped = sum(1 for chain in chains.values() if chain["status"] == "skipped_lane_exclusion")
    verdict = "FAIL" if error_count else "WARN" if warning_count else "PASS"

    return {
        "timestamp": now_iso(),
        "extension_version": package["version"],
        "chains": chains,
        "verdict": verdict,
        "error_count": error_count,
        "warning_count": warning_count,
        "skipped_due_to_lane_exclusion": skipped,
        "self_check": build_self_check(package, registered_set),
        "registered_command_sources": {
            "source": registered["source"],
            "dist": registered["dist"],
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    commands = payload["chains"]["commands"]
    config = payload["chains"]["configuration"]
    skipped = [
        name
        for name, chain in payload["chains"].items()
        if chain["status"] == "skipped_lane_exclusion"
    ]
    lines = [
        "# Extension Contribution Audit",
        "",
        f"- Verdict: `{payload['verdict']}`",
        f"- Errors: `{payload['error_count']}`",
        f"- Warnings: `{payload['warning_count']}`",
        f"- Lane-excluded chains skipped: `{payload['skipped_due_to_lane_exclusion']}`",
        "",
        "## Commands",
        "",
        f"- Declared commands: `{commands['declared']}`",
        f"- Registered commands found: `{commands['registered']}`",
        f"- Missing registrations: `{len(commands['missing_registrations'])}`",
        f"- Orphan menu references: `{len(commands['orphan_menus'])}`",
        "",
        "## Configuration",
        "",
        f"- Properties audited: `{config['properties']}`",
        f"- Namespace violations: `{len(config['namespace_violations'])}`",
        f"- Type mismatches: `{len(config['type_mismatches'])}`",
        "",
        "## Lane Exclusions",
        "",
        "- Skipped chains:",
        *(f"  - `{name}`" for name in skipped),
        "",
        "## Self Check",
        "",
        f"- Synthetic break caught: `{payload['self_check']['passed']}`",
        f"- Synthetic missing registrations: `{len(payload['self_check']['detected']['missing_registrations'])}`",
        f"- Synthetic orphan menus: `{len(payload['self_check']['detected']['orphan_menus'])}`",
        f"- Synthetic type mismatches: `{len(payload['self_check']['detected']['type_mismatches'])}`",
    ]
    return "\n".join(lines)


def main() -> int:
    configure_utf8_output()
    parser = argparse.ArgumentParser(description="Validate extension contribution graphs.")
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("audit-reports/extension_contribution_audit.json"),
        help="Output JSON path.",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("audit-reports/extension_contribution_audit.md"),
        help="Output markdown path.",
    )
    args = parser.parse_args()

    repo_root = find_repo_root()
    ctx = ValidationContext(
        repo_root=repo_root,
        extension_root=repo_root / "extensions/chthonic-archive",
        package_path=repo_root / "extensions/chthonic-archive/package.json",
        source_path=repo_root / "extensions/chthonic-archive/src/extension.ts",
        dist_path=repo_root / "extensions/chthonic-archive/dist/extension.js",
    )
    payload = build_payload(ctx)
    write_json(repo_root / args.json_output, payload)
    write_text(repo_root / args.markdown_output, render_markdown(payload))
    print(f"Wrote {args.json_output}")
    print(f"Wrote {args.markdown_output}")
    return 0 if payload["error_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
