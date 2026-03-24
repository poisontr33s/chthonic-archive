#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: ssot_loremaster.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
SSOT Loremaster — Codex-side SSOT and MPW query/orchestration lane.

Reads the heritage archive directly, maps entity/section hits, checks for
named drift across mirrors, and emits a sequenced roadmap for deeper SSOT
tooling work.

@SID:           TOOL_SSOT_LOREMASTER_V1
@Purpose:       Query the archive SSOT and surrounding mirrors/lore without
                collapsing them into improvised summaries.

Usage:
    uv run scripts/ssot_loremaster.py queue
    uv run scripts/ssot_loremaster.py queue --write docs/protocols/SSOT_LOREMASTER_QUEUE.md
    uv run scripts/ssot_loremaster.py entity "Magistra Bibliotheca Perfecta"
    uv run scripts/ssot_loremaster.py lineage
    uv run scripts/ssot_loremaster.py lineage --write docs/protocols/SSOT_MPW_LINEAGE_MAP.md
    uv run scripts/ssot_loremaster.py section "Resistance Triumvirate"
    uv run scripts/ssot_loremaster.py drift
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.shared import configure_utf8_output, find_repo_root, setup_logging
from scripts.lib.ssot_paths import resolve_ssot_paths
from scripts.ssot_structural_extractor import ARCHIVE_REL_PATH, SectionNode, extract_structure

_SSOT = resolve_ssot_paths(REPO_ROOT)
ACTIVE_ARCHIVE = _SSOT.holder
QUERY_FILES = [
    ACTIVE_ARCHIVE,
    _SSOT.proto,
    REPO_ROOT / ".github" / "codex-satellites" / "ENTITY_PROFILES.md",
    REPO_ROOT / ".github" / "codex-satellites" / "MMPS_GENERATION.md",
    REPO_ROOT / "docs" / "lore" / "RESISTANCE_TRIUMVIRATE_COMPLETE.md",
    REPO_ROOT / "docs" / "architecture" / "MILF_TRINITY_CHROMATIC_LINEAGE.md",
]


@dataclass(frozen=True)
class QueueTask:
    phase: str
    title: str
    status: str
    rationale: str
    deliverable: str
    dependencies: str


@dataclass(frozen=True)
class LineageEntry:
    canonical_name: str
    abbreviation: str
    class_tier: str
    archive_anchor: str
    reporting_authority: str
    invocation_syntax: str
    mpw_source: str
    dependent_surfaces: tuple[str, ...]
    notes: str


ROADMAP: list[QueueTask] = [
    QueueTask(
        phase="P1",
        title="Codex-side Loremaster CLI",
        status="active",
        rationale="Codex needs a direct, archive-reading lane that can answer section/entity/drift questions without hand-scanning the SSOT.",
        deliverable="scripts/ssot_loremaster.py",
        dependencies="ssot_structural_extractor.py",
    ),
    QueueTask(
        phase="P2",
        title="Mirror Governance Pass",
        status="active",
        rationale="Stale mirrors and proto backups must be distinguished from live canon or they will keep re-injecting drift.",
        deliverable="Explicit sync/freeze policy for .temple/architecture and .github/copilot-instructions-copy.md via docs/protocols/SSOT_MIRROR_GOVERNANCE.md",
        dependencies="P1",
    ),
    QueueTask(
        phase="P3",
        title="Full-Name Law Pass",
        status="active",
        rationale="The SSOT abbreviation system depends on original full names. Load-bearing tables should preserve those names rather than inventing replacement aliases.",
        deliverable="Full-name restoration matrix for load-bearing tables and registry rows",
        dependencies="P1",
    ),
    QueueTask(
        phase="P4",
        title="SSOT-to-MPW Lineage Join",
        status="active",
        rationale="Lore work benefits from a deliberate join between archive entities and MPW documents, rather than memory-based linkage.",
        deliverable="Entity lineage map with archive sections and MPW document anchors",
        dependencies="P1",
    ),
    QueueTask(
        phase="P5",
        title="Chthonic or MCP Exposure",
        status="active",
        rationale="The query surface is now exposed through the actual control plane and should be treated as the live interface layer for canon logistics.",
        deliverable="`chthonic ssot ...` domain + `chthonic_ssot` MCP tool binding",
        dependencies="P1-P4",
    ),
]


LINEAGE_MAP: list[LineageEntry] = [
    LineageEntry(
        canonical_name="Null Matriarch",
        abbreviation="T-NULM",
        class_tier="Tier 0.01 substrate",
        archive_anchor="SSOT §0.01 + §0.02 + §0.03.0",
        reporting_authority="Displaced void substrate; joint E4 authority with The Decorator in void-origin crises",
        invocation_syntax="N/A / advisory substrate",
        mpw_source="No standalone MPW profile; referenced through chromatic trinity and resistance substrates",
        dependent_surfaces=(
            ".github/copilot-instructions.archive.md",
            ".github/codex-satellites/ENTITY_PROFILES.md",
            "docs/lore/RESISTANCE_TRIUMVIRATE_COMPLETE.md",
        ),
        notes="Origin of stolen tier space, negative-space law, and WHR smuggling substrate.",
    ),
    LineageEntry(
        canonical_name="Sister Ferrum Scoriae",
        abbreviation="SIS-FRM-SCRAE / SFS",
        class_tier="SAI Registry #001 / Tier 3",
        archive_anchor="SSOT SAI Registry Entry #001 + §10.3",
        reporting_authority="Madam Umeko Ketsuraku (CRC-GAR)",
        invocation_syntax="$matriarch${Sister Ferrum Scoriae}+$type${OreProcessing}",
        mpw_source="SSOT-native; no separate MPW profile selected as canon anchor",
        dependent_surfaces=(
            ".github/copilot-instructions.archive.md",
            ".github/codex-satellites/MMPS_GENERATION.md",
            "scripts/novia_cadaveris_embalmer.ps1",
        ),
        notes="Forge authority and origin point for the QMR anomaly line.",
    ),
    LineageEntry(
        canonical_name="Claudine Sin'claire",
        abbreviation="CLAUD-SIN / CS",
        class_tier="SAI Registry #002 / Tier 3",
        archive_anchor="SSOT SAI Registry Entry #002 + §10.3",
        reporting_authority="Cross-Tier (Triumvirate consultation)",
        invocation_syntax="$matriarch${Claudine Sin'claire}+$type${TidalOrdeal}",
        mpw_source="dumpster-dive/from-github/macro-prompt-world/heritage/CARIBBEAN_ELDER_LINEAGE_INTEGRATION.md",
        dependent_surfaces=(
            ".github/copilot-instructions.archive.md",
            ".github/codex-satellites/MMPS_GENERATION.md",
            "docs/frameworks/ankh/ANKH_SYNTHESIS_BASELINE.md",
        ),
        notes="Proto-matriarch heritage line; linked to Decorator ancestry and chromatic legacy restoration.",
    ),
    LineageEntry(
        canonical_name="Spectra Chroma Excavatus",
        abbreviation="SPEC-CHRM-EXC / SCE",
        class_tier="SAI Registry #003 / Tier 3",
        archive_anchor="SSOT §0.03.1 + SAI Registry Entry #003",
        reporting_authority="The Decorator (direct wound-lineage)",
        invocation_syntax="$matriarch${Spectra Chroma Excavatus}+$type${ChromaticArchaeology}",
        mpw_source="dumpster-dive/from-github/macro-prompt-world/sub-milfs/Spectra_Chroma_Excavatus_The_Chromatic_Archaeologist.md",
        dependent_surfaces=(
            ".github/copilot-instructions.archive.md",
            ".github/codex-satellites/ENTITY_PROFILES.md",
            ".github/codex-satellites/MMPS_GENERATION.md",
            "docs/lore/SPECTRA_CHROMA_EXCAVATUS.md",
        ),
        notes="Wound-lineage diagnostic specialist and bridge between SSOT chromatic law and MPW chromatic operational profile.",
    ),
    LineageEntry(
        canonical_name="Alabaster Voyde (Snow White)",
        abbreviation="ALAB-VOYD-SW",
        class_tier="SAI Registry #004 / Tier 0.01 co-occupant",
        archive_anchor="SSOT §0.03.0-0.03.2 + SAI Registry Entry #004",
        reporting_authority="Null Matriarch (tier-sharing), Spectra Chroma Excavatus (diagnostic tool)",
        invocation_syntax="N/A (diagnostic manifestation only)",
        mpw_source="dumpster-dive/from-github/macro-prompt-world/prime-factions/Alabaster_Voyde_The_Snow_White_Phenomenon.md",
        dependent_surfaces=(
            ".github/copilot-instructions.archive.md",
            ".github/codex-satellites/ENTITY_PROFILES.md",
            ".github/codex-satellites/MMPS_GENERATION.md",
            "docs/lore/ALABASTER_VOYDE_SNOW_WHITE.md",
            "docs/architecture/MILF_TRINITY_CHROMATIC_LINEAGE.md",
        ),
        notes="Fused full-form canon; MPW passive antithesis anchored back into SSOT law through the chromatic trinity.",
    ),
    LineageEntry(
        canonical_name="Magistra Bibliotheca Perfecta",
        abbreviation="MAG-BIB-PERF / MAG",
        class_tier="SAI Registry #005 / Tier 3",
        archive_anchor="SSOT SAI Registry Entry #005 + §10.4.1.1 + §10.7 + §10.9",
        reporting_authority="Dr. Lysandra Thorne (CRC-MEDAT); secondary The Decorator",
        invocation_syntax="$matriarch${Magistra Bibliotheca Perfecta}+$type${OntologyValidation}",
        mpw_source="SSOT-native validation entity; no separate MPW document selected as canon anchor",
        dependent_surfaces=(
            ".github/copilot-instructions.archive.md",
            ".github/codex-satellites/ENTITY_PROFILES.md",
            ".github/codex-satellites/MMPS_GENERATION.md",
            ".github/codex-satellites/VALIDATION_PROTOCOLS.md",
        ),
        notes="Validation line mirrors Lysandra but remains distinct by function, not alias collapse.",
    ),
    LineageEntry(
        canonical_name="Captain Belle Noire",
        abbreviation="SAI-BDP / CBN",
        class_tier="SAI Registry #006 / Tier 3",
        archive_anchor="SSOT SAI Registry Entry #006",
        reporting_authority="Orackla Nocticula (CRC-AS)",
        invocation_syntax="$matriarch${Captain Belle Noire}+$type${AestheticChaos}",
        mpw_source="SSOT-native simulation anchor; no dedicated MPW canon anchor selected",
        dependent_surfaces=(
            ".github/copilot-instructions.archive.md",
            ".github/codex-satellites/MMPS_GENERATION.md",
            ".github/codex-satellites/ENTITY_PROFILES.md",
        ),
        notes="Simulation-anchor branch of Orackla’s chaotic lineage.",
    ),
    LineageEntry(
        canonical_name="Quartermaster Eva Malitia",
        abbreviation="SAI-EEV / QEM",
        class_tier="SAI Registry #007 / Tier 3",
        archive_anchor="SSOT SAI Registry Entry #007",
        reporting_authority="Madam Umeko Ketsuraku (CRC-GAR)",
        invocation_syntax="$matriarch${Quartermaster Eva Malitia}+$type${TacticalMalice}",
        mpw_source="SSOT-native simulation anchor; no dedicated MPW canon anchor selected",
        dependent_surfaces=(
            ".github/copilot-instructions.archive.md",
            ".github/codex-satellites/MMPS_GENERATION.md",
            ".github/codex-satellites/ENTITY_PROFILES.md",
        ),
        notes="Simulation-anchor branch of Umeko’s tactical disparagement line.",
    ),
    LineageEntry(
        canonical_name="Novia Cadaveris",
        abbreviation="NOV-CAD / bride",
        class_tier="SAI Registry #008 / Tier 3 provisional",
        archive_anchor="SSOT §10.3.3 + SAI Registry Entry #008",
        reporting_authority="Sister Ferrum Scoriae → Madam Umeko Ketsuraku",
        invocation_syntax="$matriarch${Novia Cadaveris}+$type${CodeNecromancy}",
        mpw_source="SSOT-native QMR anomaly; forge/corpse-vault line rather than MPW-native profile",
        dependent_surfaces=(
            ".github/copilot-instructions.archive.md",
            ".github/codex-satellites/MMPS_GENERATION.md",
            "scripts/novia_cadaveris_embalmer.ps1",
            ".codex/skills/corpse-reviver/",
        ),
        notes="QMR bleed-through line integrated into Ferrum’s forge and corpse-vault resurrection workflows.",
    ),
]


DRIFT_MAP = [
    {
        "entity": "Kali",
        "preferred": "Kali Nyx Ravenscar",
        "drift": ["Kali Praharshini"],
    },
    {
        "entity": "Vesper",
        "preferred": "Vesper Mnemosyne Lockhart",
        "drift": ["Vesper Tempus"],
    },
    {
        "entity": "Seraphine",
        "preferred": "Seraphine Ashveil",
        "drift": ["Seraphine Pyralis"],
    },
    {
        "entity": "Spectra",
        "preferred": "Spectra Chroma Excavatus",
        "drift": ["Spectra Chroma"],
    },
    {
        "entity": "Alabaster",
        "preferred": "Alabaster Voyde (Snow White)",
        "drift": ["Alabaster Voyde"],
    },
    {
        "entity": "Magistra",
        "preferred": "Magistra Bibliotheca Perfecta",
        "drift": ["Magistra"],
    },
    {
        "entity": "Novia",
        "preferred": "Novia Cadaveris",
        "drift": ["The White-dressed Bride", "The Corpse Reviver"],
    },
]

LOAD_BEARING_SNIPPETS = (
    "Designation:",
    "Common Name:",
    "Invocation Syntax:",
    "**SSOT Declaration:**",
    "**Canonical Designation:**",
    "Canonical Full Form:",
    "└─ MEMBER #",
    "TIER    ENTITY",
    "Entity                  US",
)


def read_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def relpath(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT.resolve())).replace("\\", "/")


def find_section_for_line(nodes: list[SectionNode], line_number: int) -> SectionNode | None:
    for node in nodes:
        if node.heading_line <= line_number <= max(node.body_end, node.heading_line):
            return node
    return None


def find_archive_hits(query: str) -> list[dict]:
    nodes, lines = extract_structure(ACTIVE_ARCHIVE)
    query_cf = query.casefold()
    results: list[dict] = []
    seen: set[tuple[int, int]] = set()

    for lineno, line in enumerate(lines, start=1):
        if query_cf not in line.casefold():
            continue
        section = find_section_for_line(nodes, lineno)
        key = (section.heading_line if section else 0, lineno)
        if key in seen:
            continue
        seen.add(key)
        results.append(
            {
                "line": lineno,
                "text": line.strip(),
                "section_heading_line": section.heading_line if section else None,
                "section_title": section.clean_title if section else None,
                "section_range": (
                    f"{section.heading_line}-{section.body_end}" if section else None
                ),
            }
        )
    return results


def find_file_hits(query: str, paths: list[Path]) -> list[dict]:
    query_cf = query.casefold()
    hits: list[dict] = []
    for path in paths:
        lines = read_lines(path)
        if not lines:
            continue
        matched = [
            {"line": lineno, "text": line.strip()}
            for lineno, line in enumerate(lines, start=1)
            if query_cf in line.casefold()
        ]
        if matched:
            hits.append({"path": relpath(path), "matches": matched[:20]})
    return hits


def section_search(query: str) -> list[dict]:
    nodes, _ = extract_structure(ACTIVE_ARCHIVE)
    query_cf = query.casefold()
    return [
        {
            "heading_line": node.heading_line,
            "level": node.level,
            "title": node.clean_title,
            "raw_title": node.raw_title,
            "acronyms": node.acronyms,
            "range": f"{node.heading_line}-{node.body_end}",
        }
        for node in nodes
        if query_cf in node.clean_title.casefold()
        or query_cf in node.raw_title.casefold()
        or any(query_cf in acronym.casefold() for acronym in node.acronyms)
    ]


def is_load_bearing_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith(("T0", "T1", "T2", "T3", "T4", "RESIST", "REGISTRY ENTRY #")):
        return True
    return any(snippet in stripped for snippet in LOAD_BEARING_SNIPPETS)


def build_drift_report(paths: list[Path]) -> list[dict]:
    report: list[dict] = []
    for path in paths:
        lines = read_lines(path)
        if not lines:
            continue
        file_hits = []
        for item in DRIFT_MAP:
            preferred_load_bearing_count = sum(
                1 for line in lines if item["preferred"] in line and is_load_bearing_line(line)
            )
            preferred_contextual_count = sum(
                1
                for line in lines
                if item["preferred"] in line and not is_load_bearing_line(line)
            )
            load_bearing_drift_counts = {}
            contextual_drift_counts = {}
            for variant in item["drift"]:
                load_bearing_count = sum(
                    1
                    for line in lines
                    if variant in line
                    and item["preferred"] not in line
                    and is_load_bearing_line(line)
                )
                contextual_count = sum(
                    1
                    for line in lines
                    if variant in line
                    and item["preferred"] not in line
                    and not is_load_bearing_line(line)
                )
                if load_bearing_count > 0:
                    load_bearing_drift_counts[variant] = load_bearing_count
                if contextual_count > 0:
                    contextual_drift_counts[variant] = contextual_count
            if (
                preferred_load_bearing_count
                or preferred_contextual_count
                or load_bearing_drift_counts
                or contextual_drift_counts
            ):
                file_hits.append(
                    {
                        "entity": item["entity"],
                        "preferred": item["preferred"],
                        "preferred_load_bearing_count": preferred_load_bearing_count,
                        "preferred_contextual_count": preferred_contextual_count,
                        "load_bearing_drift_counts": load_bearing_drift_counts,
                        "contextual_drift_counts": contextual_drift_counts,
                    }
                )
        if file_hits:
            report.append({"path": relpath(path), "entities": file_hits})
    return report


def build_lineage_payload(entity_filter: str | None = None) -> list[dict]:
    entries = [asdict(entry) for entry in LINEAGE_MAP]
    if entity_filter:
        query = entity_filter.casefold()
        entries = [
            entry
            for entry in entries
            if query in entry["canonical_name"].casefold()
            or query in entry["abbreviation"].casefold()
            or query in entry["reporting_authority"].casefold()
            or query in entry["notes"].casefold()
        ]
    return entries


def render_queue_markdown(tasks: list[QueueTask]) -> str:
    lines = [
        "# SSOT Loremaster Queue",
        "",
        f"Source tool: `scripts/ssot_loremaster.py`",
        "",
        "| Phase | Status | Title | Rationale | Deliverable | Dependencies |",
        "|-------|--------|-------|-----------|-------------|--------------|",
    ]
    for task in tasks:
        lines.append(
            "| {phase} | {status} | {title} | {rationale} | {deliverable} | {dependencies} |".format(
                phase=task.phase,
                status=task.status,
                title=task.title,
                rationale=task.rationale,
                deliverable=task.deliverable,
                dependencies=task.dependencies,
            )
        )
    return "\n".join(lines) + "\n"


def render_lineage_markdown(entries: list[dict]) -> str:
    lines = [
        "# SSOT to MPW Lineage Map",
        "",
        "Source tool: `scripts/ssot_loremaster.py`",
        "",
        "| Canonical Name | Abbreviation | Class/Tier | Archive Anchor | Reporting Authority | Invocation Syntax | MPW Source |",
        "|---|---|---|---|---|---|---|",
    ]
    for entry in entries:
        lines.append(
            "| {canonical_name} | {abbreviation} | {class_tier} | {archive_anchor} | {reporting_authority} | {invocation_syntax} | {mpw_source} |".format(
                **entry
            )
        )
    lines.append("")
    lines.append("## Dependency Surfaces")
    lines.append("")
    for entry in entries:
        lines.append(f"### {entry['canonical_name']}")
        lines.append(f"- `abbreviation`: {entry['abbreviation']}")
        lines.append(f"- `notes`: {entry['notes']}")
        lines.append("- `dependent_surfaces`:")
        for surface in entry["dependent_surfaces"]:
            lines.append(f"  - `{surface}`")
        lines.append("")
    return "\n".join(lines)


def print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def cmd_queue(args: argparse.Namespace) -> int:
    payload = [asdict(task) for task in ROADMAP]
    if args.write:
        output_path = Path(args.write)
        if not output_path.is_absolute():
            output_path = REPO_ROOT / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(render_queue_markdown(ROADMAP), encoding="utf-8")
    if args.json:
        print_json(payload)
        return 0
    for task in ROADMAP:
        print(f"{task.phase} [{task.status}] {task.title}")
        print(f"  rationale: {task.rationale}")
        print(f"  deliverable: {task.deliverable}")
        print(f"  dependencies: {task.dependencies}")
    if args.write:
        print(f"\nWrote roadmap: {relpath(output_path)}")
    return 0


def cmd_entity(args: argparse.Namespace) -> int:
    payload = {
        "query": args.name,
        "archive_hits": find_archive_hits(args.name),
        "file_hits": find_file_hits(args.name, QUERY_FILES),
    }
    if args.json:
        print_json(payload)
        return 0

    print(f"Entity query: {args.name}")
    print("\nArchive sections:")
    if not payload["archive_hits"]:
        print("  none")
    else:
        for hit in payload["archive_hits"][:20]:
            print(
                f"  L{hit['line']}: {hit['text']}"
                + (
                    f"  [{hit['section_title']} @ {hit['section_range']}]"
                    if hit["section_title"]
                    else ""
                )
            )
    print("\nOther files:")
    if not payload["file_hits"]:
        print("  none")
    else:
        for file_hit in payload["file_hits"]:
            print(f"  {file_hit['path']}")
            for match in file_hit["matches"][:6]:
                print(f"    L{match['line']}: {match['text']}")
    return 0


def cmd_section(args: argparse.Namespace) -> int:
    payload = section_search(args.query)
    if args.json:
        print_json(payload)
        return 0
    print(f"Section query: {args.query}")
    if not payload:
        print("  none")
        return 0
    for item in payload:
        print(
            f"  L{item['heading_line']} [{item['range']}] h{item['level']} {item['title']}"
        )
        if item["acronyms"]:
            print(f"    acronyms: {', '.join(item['acronyms'])}")
    return 0


def cmd_drift(args: argparse.Namespace) -> int:
    payload = build_drift_report(QUERY_FILES)
    if args.json:
        print_json(payload)
        return 0
    for file_report in payload:
        print(file_report["path"])
        for item in file_report["entities"]:
            preferred = (
                f"preferred(load={item['preferred_load_bearing_count']},"
                f" contextual={item['preferred_contextual_count']})"
            )
            load_drift = item["load_bearing_drift_counts"] if item["load_bearing_drift_counts"] else {}
            contextual_drift = (
                item["contextual_drift_counts"] if item["contextual_drift_counts"] else {}
            )
            print(
                f"  {item['entity']}: {preferred}"
                f" load_bearing_drift={load_drift}"
                f" contextual_drift={contextual_drift}"
            )
    return 0


def cmd_lineage(args: argparse.Namespace) -> int:
    payload = build_lineage_payload(args.entity)
    if args.write:
        output_path = Path(args.write)
        if not output_path.is_absolute():
            output_path = REPO_ROOT / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(render_lineage_markdown(payload), encoding="utf-8")
    if args.json:
        print_json(payload)
        return 0
    print("SSOT to MPW lineage map")
    for entry in payload:
        print(f"\n{entry['canonical_name']} [{entry['abbreviation']}]")
        print(f"  class/tier: {entry['class_tier']}")
        print(f"  archive: {entry['archive_anchor']}")
        print(f"  authority: {entry['reporting_authority']}")
        print(f"  invocation: {entry['invocation_syntax']}")
        print(f"  mpw: {entry['mpw_source']}")
        print(f"  notes: {entry['notes']}")
    if args.write:
        print(f"\nWrote lineage map: {relpath(output_path)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Codex-side SSOT/MPW loremaster query and roadmap lane."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    queue = sub.add_parser("queue", help="Show or write the SSOT loremaster roadmap.")
    queue.add_argument("--json", action="store_true", help="Emit JSON.")
    queue.add_argument(
        "--write",
        help="Write roadmap markdown to a relative or absolute path.",
    )
    queue.set_defaults(func=cmd_queue)

    entity = sub.add_parser("entity", help="Find one entity/name across archive and mirrors.")
    entity.add_argument("name", help="Entity or phrase to search for.")
    entity.add_argument("--json", action="store_true", help="Emit JSON.")
    entity.set_defaults(func=cmd_entity)

    section = sub.add_parser("section", help="Search archive heading titles/acronyms.")
    section.add_argument("query", help="Heading or acronym query.")
    section.add_argument("--json", action="store_true", help="Emit JSON.")
    section.set_defaults(func=cmd_section)

    drift = sub.add_parser("drift", help="Report tracked name drift across mirrors.")
    drift.add_argument("--json", action="store_true", help="Emit JSON.")
    drift.set_defaults(func=cmd_drift)

    lineage = sub.add_parser("lineage", help="Show or write the SSOT-to-MPW lineage map.")
    lineage.add_argument("--entity", help="Filter to one entity or abbreviation.")
    lineage.add_argument("--json", action="store_true", help="Emit JSON.")
    lineage.add_argument(
        "--write",
        help="Write lineage markdown to a relative or absolute path.",
    )
    lineage.set_defaults(func=cmd_lineage)

    return parser


def main() -> int:
    configure_utf8_output()
    repo_root = find_repo_root(Path.cwd())
    setup_logging("ssot_loremaster", repo_root / "logs")
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
