#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: render_priming_packet.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🔥 THE FOUNDRY
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Compile live priming sources into one concrete packet so the sources are
functional inputs rather than orphaned meta-documentation.

Usage:
  uv run scripts/render_priming_packet.py --packet chimera_local_singularity

@SID:           TOOL_RENDER_PRIMING_PACKET_V1
@Shabti:        CLI Script
@Purpose:       Compile local priming sources into a functional packet.
"""

from __future__ import annotations


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import argparse
import json
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO_ROOT / "codex" / "artifacts" / "PRIMING_REFERENCE_REGISTRY.toml"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_toml(path: Path) -> dict[str, Any]:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def read_source(rel_path: str) -> dict[str, Any]:
    path = REPO_ROOT / rel_path
    suffix = path.suffix.lower()
    raw = path.read_text(encoding="utf-8")
    payload: dict[str, Any] = {
        "path": rel_path,
        "suffix": suffix,
        "raw": raw,
    }
    if suffix == ".toml":
        try:
            payload["parsed"] = tomllib.loads(raw)
        except Exception:
            payload["parsed"] = None
    return payload


def render_residue_section(parsed: dict[str, Any]) -> list[str]:
    identity = parsed.get("identity", {})
    bridge = parsed.get("bridge", {})
    style = parsed.get("style", {})
    reasoning = parsed.get("reasoning", {})
    instruction_integration = parsed.get("instruction_integration", {})

    lines = [
        "## Residue Reference",
        "",
        f"- Summary: {identity.get('summary', '(missing)')}",
        f"- Egyptian half: {bridge.get('egyptian_half', '(missing)')}",
        f"- Andean half: {bridge.get('andean_half', '(missing)')}",
        f"- Combined rule: {bridge.get('combined_rule', '(missing)')}",
        "",
        "### Style Prefers",
    ]
    for item in style.get("prefer", []):
        lines.append(f"- {item}")
    lines += [
        "",
        "### Style Avoids",
    ]
    for item in style.get("avoid", []):
        lines.append(f"- {item}")
    lines += [
        "",
        "### Reasoning Loop",
    ]
    for item in reasoning.get("transmutation_loop", []):
        lines.append(f"- {item}")
    lines += [
        "",
        "### Instruction Integration",
        f"- core_risk: {instruction_integration.get('core_risk', '(missing)')}",
        f"- cross_reference_required: {instruction_integration.get('cross_reference_required', '(missing)')}",
        f"- read_before_protecting: {instruction_integration.get('read_before_protecting', '(missing)')}",
        "",
    ]
    return lines


def render_equivalence_section(parsed: dict[str, Any]) -> list[str]:
    lines = [
        "## Invariant Equivalence",
        "",
        f"- Purpose: {parsed.get('purpose', '(missing)')}",
        "",
    ]
    for family in parsed.get("family", []):
        lines += [
            f"### {family.get('id', 'family')}",
            f"- invariant: {family.get('invariant', '(missing)')}",
        ]
        for item in family.get("preserve_as", []):
            lines.append(f"- preserve_as: {item}")
        for item in family.get("avoid_reduction_to", []):
            lines.append(f"- avoid_reduction_to: {item}")
        lines.append("")
    return lines


def render_markdown(packet_id: str, packet_meta: dict[str, Any], sources: list[dict[str, Any]]) -> str:
    lines = [
        "---",
        "type: compiled-priming-packet",
        f"packet_id: {packet_id}",
        f"generated: {utc_now()}",
        "---",
        "",
        f"# {packet_meta.get('title', packet_id)}",
        "",
        f"- Intent: {packet_meta.get('intent', '')}",
        f"- Registry: `codex/artifacts/PRIMING_REFERENCE_REGISTRY.toml`",
        "",
        "## Sources",
    ]
    for source in sources:
        lines.append(f"- `{source['path']}`")

    for source in sources:
        if source["suffix"] == ".md":
            lines += [
                "",
                f"## Source: {source['path']}",
                "",
                source["raw"].rstrip(),
            ]
        elif source["suffix"] == ".toml":
            lines += [
                "",
                f"## Source: {source['path']}",
                "",
            ]
            parsed = source.get("parsed") or {}
            if "family" in parsed:
                lines += render_equivalence_section(parsed)
            else:
                lines += render_residue_section(parsed)
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile local priming sources into one packet.")
    parser.add_argument("--packet", required=True, help="Packet key from the registry.")
    parser.add_argument("--write-md", action="store_true", help="Write the human-readable markdown mirror.")
    args = parser.parse_args()

    registry = load_toml(REGISTRY_PATH)
    packets = registry.get("packet", {})
    if args.packet not in packets:
        raise SystemExit(f"Unknown packet '{args.packet}'")

    packet_meta = packets[args.packet]
    sources = [read_source(path) for path in packet_meta.get("sources", [])]
    payload = {
        "packet_id": args.packet,
        "generated": utc_now(),
        "title": packet_meta.get("title"),
        "intent": packet_meta.get("intent"),
        "sources": [
            {
                "path": source["path"],
                "suffix": source["suffix"],
                "parsed": source.get("parsed"),
                "raw": source["raw"],
            }
            for source in sources
        ],
    }

    json_output = packet_meta.get("json_output")
    markdown_output = packet_meta.get("markdown_output")
    if not json_output:
        raise SystemExit("Registry entry must declare json_output.")
    json_path = REPO_ROOT / json_output
    md_path = REPO_ROOT / markdown_output if markdown_output else None
    json_path.parent.mkdir(parents=True, exist_ok=True)
    if md_path is not None:
        md_path.parent.mkdir(parents=True, exist_ok=True)

    markdown = render_markdown(args.packet, packet_meta, sources)
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if args.write_md and md_path is not None:
        md_path.write_text(markdown, encoding="utf-8")

    print(f"packet_json={json_path}")
    if args.write_md and md_path is not None:
        print(f"packet_md={md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
