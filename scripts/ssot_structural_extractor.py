#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: ssot_structural_extractor.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
SSOT Structural Extractor — Lossless section-level index of the heritage SSOT.

Parses copilot-instructions.archive.md into a mechanically verifiable
heading tree with line ranges, content fingerprints, word counts, and
structural element census per section.

This is the ground-truth structural map. Downstream ANKH corpus files
can be audited against this index to verify chain of custody from
archive section to downstream assertion — objectively, not subjectively.

The archive is the Single Source of Truth. This tool reads it losslessly.
It does not interpret, summarize, or filter. It counts and fingerprints.

@SID:           TOOL_SSOT_STRUCTURAL_EXTRACTOR_V1
@Shabti:        CLI Script
@Heka-Ayni:     Produces SSOT_ARCHIVE_STRUCTURAL_INDEX.json
@Ankh-Tinku:    Consumed by link_audit.py, path_naming_audit.py, synthesis baseline
@Purpose:       Lossless structural extraction from heritage archive SSOT

Usage:
    uv run scripts/ssot_structural_extractor.py                   # human report
    uv run scripts/ssot_structural_extractor.py --json            # full JSON index
    uv run scripts/ssot_structural_extractor.py --update-index    # write index file
    uv run scripts/ssot_structural_extractor.py --section "FA1"   # search sections
    uv run scripts/ssot_structural_extractor.py --stats           # heading census only
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from scripts.lib.shared import configure_utf8_output, find_repo_root, setup_logging
from scripts.lib.ssot_paths import SSOT_HOLDER

# =============================================================================
# Constants
# =============================================================================

ARCHIVE_REL_PATH = SSOT_HOLDER

# Heading pattern: captures the # prefix and the rest of the line
RE_HEADING = re.compile(r"^(#{1,6})\s+(.+)$")

# Acronym pattern: (WORD-LIKE) or (`WORD-LIKE`) inside heading text
RE_ACRONYM = re.compile(r"\(`?([A-Z][A-Z0-9_-]{1,})`?\)")

# Bold markers to strip for clean title
RE_BOLD = re.compile(r"\*{1,2}")

# Emoji pattern for census
RE_EMOJI = re.compile(
    r"[\U0001F300-\U0001F9FF\U00002600-\U000027BF\U0001FA00-\U0001FA6F"
    r"\U0001FA70-\U0001FAFF\U00002702-\U000027B0\U0000FE00-\U0000FE0F"
    r"\U0001F1E0-\U0001F1FF]+"
)

# Markdown structural elements
RE_LINK = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
RE_CODE_FENCE = re.compile(r"^```")
RE_LIST_ITEM = re.compile(r"^\s*[-*+]\s")
RE_NUMBERED_ITEM = re.compile(r"^\s*\d+\.\s")
RE_TABLE_ROW = re.compile(r"^\|.+\|$")
RE_BLOCKQUOTE = re.compile(r"^>\s")


# =============================================================================
# Data structures
# =============================================================================


@dataclass
class SectionNode:
    """One heading and its body content in the archive SSOT."""

    heading_line: int  # 1-based line number of the heading
    level: int  # 1-6
    raw_title: str  # heading text as-is (with bold, emoji, etc.)
    clean_title: str  # stripped of bold markers
    acronyms: list[str]  # extracted from (WORD) patterns
    body_start: int  # first line of body (heading_line + 1)
    body_end: int  # last line of body (inclusive), set after parsing
    body_lines: int = 0  # count of body lines
    body_words: int = 0  # word count in body
    body_hash: str = ""  # SHA-256 of normalized body text
    # Structural element census within this section's body
    links: int = 0
    code_fences: int = 0
    list_items: int = 0
    numbered_items: int = 0
    table_rows: int = 0
    blockquotes: int = 0
    emojis: int = 0
    # Tree position
    depth: int = 0  # 0-based depth in the tree (level - 1)
    parent_line: int | None = None  # heading_line of parent section
    children_lines: list[int] = field(default_factory=list)


# =============================================================================
# Parsing
# =============================================================================


def parse_headings(lines: list[str]) -> list[SectionNode]:
    """Extract all headings from the archive lines (1-indexed)."""
    nodes: list[SectionNode] = []
    for lineno_0, line in enumerate(lines):
        m = RE_HEADING.match(line)
        if m:
            level = len(m.group(1))
            raw_title = m.group(2).strip()
            clean = RE_BOLD.sub("", raw_title).strip()
            acronyms = RE_ACRONYM.findall(raw_title)
            nodes.append(
                SectionNode(
                    heading_line=lineno_0 + 1,
                    level=level,
                    raw_title=raw_title,
                    clean_title=clean,
                    acronyms=list(dict.fromkeys(acronyms)),  # dedupe, preserve order
                    body_start=lineno_0 + 2,  # 1-indexed, line after heading
                    body_end=0,  # filled in later
                    depth=level - 1,
                )
            )
    return nodes


def compute_body_ranges(nodes: list[SectionNode], total_lines: int) -> None:
    """Set body_end for each section: runs until next heading or EOF."""
    heading_lines = {n.heading_line for n in nodes}
    for i, node in enumerate(nodes):
        if i + 1 < len(nodes):
            node.body_end = nodes[i + 1].heading_line - 1
        else:
            node.body_end = total_lines
        # Clamp: body_start > body_end means empty body
        if node.body_start > node.body_end:
            node.body_end = node.body_start - 1


def compute_tree_relationships(nodes: list[SectionNode]) -> None:
    """Assign parent_line and children_lines based on heading levels."""
    stack: list[SectionNode] = []
    for node in nodes:
        # Pop stack until we find a parent (lower level)
        while stack and stack[-1].level >= node.level:
            stack.pop()
        if stack:
            node.parent_line = stack[-1].heading_line
            stack[-1].children_lines.append(node.heading_line)
        stack.append(node)


def fingerprint_body(lines: list[str], node: SectionNode) -> None:
    """Compute body stats and SHA-256 for a section's body text."""
    if node.body_start > node.body_end:
        node.body_lines = 0
        node.body_words = 0
        node.body_hash = hashlib.sha256(b"").hexdigest()
        return

    body = lines[node.body_start - 1 : node.body_end]  # 0-indexed slice
    node.body_lines = len(body)
    text = "\n".join(body)
    node.body_words = len(text.split())

    # Normalize for hashing: strip trailing whitespace per line, normalize newlines
    normalized = "\n".join(line.rstrip() for line in body).strip()
    node.body_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    # Structural census
    for line in body:
        node.links += len(RE_LINK.findall(line))
        if RE_CODE_FENCE.match(line):
            node.code_fences += 1
        if RE_LIST_ITEM.match(line):
            node.list_items += 1
        if RE_NUMBERED_ITEM.match(line):
            node.numbered_items += 1
        if RE_TABLE_ROW.match(line):
            node.table_rows += 1
        if RE_BLOCKQUOTE.match(line):
            node.blockquotes += 1
        node.emojis += len(RE_EMOJI.findall(line))


def extract_structure(archive_path: Path) -> tuple[list[SectionNode], list[str]]:
    """Full extraction pipeline. Returns (nodes, lines)."""
    text = archive_path.read_text(encoding="utf-8", errors="replace")
    lines = text.split("\n")
    nodes = parse_headings(lines)
    compute_body_ranges(nodes, len(lines))
    compute_tree_relationships(nodes)
    for node in nodes:
        fingerprint_body(lines, node)
    return nodes, lines


# =============================================================================
# Output
# =============================================================================


def build_payload(
    nodes: list[SectionNode],
    lines: list[str],
    archive_path: Path,
    repo_root: Path,
) -> dict:
    """Build the full JSON payload."""
    level_counts = Counter(n.level for n in nodes)
    total_words = sum(n.body_words for n in nodes)
    total_links = sum(n.links for n in nodes)
    total_code_fences = sum(n.code_fences for n in nodes)
    total_table_rows = sum(n.table_rows for n in nodes)
    total_list_items = sum(n.list_items for n in nodes)
    total_emojis = sum(n.emojis for n in nodes)

    # Whole-file hash
    full_text = "\n".join(line.rstrip() for line in lines).strip()
    file_hash = hashlib.sha256(full_text.encode("utf-8")).hexdigest()

    # Acronym registry: acronym -> [heading_lines]
    acronym_map: dict[str, list[int]] = {}
    for node in nodes:
        for acr in node.acronyms:
            acronym_map.setdefault(acr, []).append(node.heading_line)

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "archive_path": str(archive_path.relative_to(repo_root)),
        "file_hash_sha256": file_hash,
        "totals": {
            "lines": len(lines),
            "headings": len(nodes),
            "words": total_words,
            "links": total_links,
            "code_fences": total_code_fences,
            "table_rows": total_table_rows,
            "list_items": total_list_items,
            "emojis": total_emojis,
            "unique_acronyms": len(acronym_map),
        },
        "heading_census": {
            f"H{level}": count
            for level, count in sorted(level_counts.items())
        },
        "acronym_registry": {
            k: v for k, v in sorted(acronym_map.items())
        },
        "sections": [
            {
                "heading_line": n.heading_line,
                "level": n.level,
                "raw_title": n.raw_title,
                "clean_title": n.clean_title,
                "acronyms": n.acronyms,
                "body_start": n.body_start,
                "body_end": n.body_end,
                "body_lines": n.body_lines,
                "body_words": n.body_words,
                "body_hash": n.body_hash,
                "links": n.links,
                "code_fences": n.code_fences,
                "list_items": n.list_items,
                "numbered_items": n.numbered_items,
                "table_rows": n.table_rows,
                "blockquotes": n.blockquotes,
                "emojis": n.emojis,
                "parent_line": n.parent_line,
                "children_count": len(n.children_lines),
            }
            for n in nodes
        ],
    }


def render_report(payload: dict, section_filter: str | None = None) -> str:
    """Render human-readable report."""
    out: list[str] = []
    a = out.append

    a("SSOT Archive Structural Index")
    a(f"  source: {payload['archive_path']}")
    a(f"  generated: {payload['generated_at']}")
    a(f"  file hash: {payload['file_hash_sha256'][:16]}...")
    a("")

    t = payload["totals"]
    a("Totals")
    a(f"  lines: {t['lines']}")
    a(f"  headings: {t['headings']}")
    a(f"  words: {t['words']}")
    a(f"  links: {t['links']}")
    a(f"  code fences: {t['code_fences']}")
    a(f"  table rows: {t['table_rows']}")
    a(f"  list items: {t['list_items']}")
    a(f"  emojis: {t['emojis']}")
    a(f"  unique acronyms: {t['unique_acronyms']}")
    a("")

    a("Heading Census")
    for level_key, count in payload["heading_census"].items():
        a(f"  {level_key}: {count}")
    a("")

    sections = payload["sections"]
    if section_filter:
        pat = re.compile(section_filter, re.IGNORECASE)
        sections = [
            s for s in sections
            if pat.search(s["clean_title"])
            or pat.search(s["raw_title"])
            or any(pat.search(acr) for acr in s["acronyms"])
        ]

    a(f"Sections ({len(sections)} shown)")
    for s in sections:
        indent = "  " * (s["level"] - 1)
        acr_str = f" [{', '.join(s['acronyms'])}]" if s["acronyms"] else ""
        line_range = f"L{s['heading_line']}–L{s['body_end']}"
        a(
            f"  {s['heading_line']:>5} | {indent}H{s['level']} {s['clean_title'][:80]}{acr_str}"
        )
        a(
            f"        {indent}  {line_range} ({s['body_lines']} body lines, "
            f"{s['body_words']} words, hash:{s['body_hash'][:12]})"
        )

    a("")
    return "\n".join(out)


def render_stats(payload: dict) -> str:
    """Render heading census only."""
    out: list[str] = []
    a = out.append
    a("SSOT Archive Heading Census")
    a(f"  source: {payload['archive_path']}")
    a(f"  total lines: {payload['totals']['lines']}")
    a(f"  total headings: {payload['totals']['headings']}")
    a("")
    for level_key, count in payload["heading_census"].items():
        a(f"  {level_key}: {count}")
    a("")
    a(f"  unique acronyms: {payload['totals']['unique_acronyms']}")
    a(f"  total words: {payload['totals']['words']}")
    a(f"  total emojis: {payload['totals']['emojis']}")
    return "\n".join(out)


# =============================================================================
# CLI
# =============================================================================


def main() -> int:
    configure_utf8_output()

    parser = argparse.ArgumentParser(
        description="Lossless structural extractor for the heritage archive SSOT."
    )
    parser.add_argument(
        "--json", action="store_true", help="Full JSON index to stdout"
    )
    parser.add_argument(
        "--update-index",
        action="store_true",
        help="Write SSOT_ARCHIVE_STRUCTURAL_INDEX.json to data/indices/",
    )
    parser.add_argument(
        "--section",
        type=str,
        default=None,
        help="Filter sections by regex (searches title and acronyms)",
    )
    parser.add_argument(
        "--stats", action="store_true", help="Heading census only"
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--quiet", "-q", action="store_true")

    args = parser.parse_args()
    log = setup_logging(verbose=args.verbose, quiet=args.quiet)
    repo_root = find_repo_root()

    archive_path = repo_root / ARCHIVE_REL_PATH
    if not archive_path.is_file():
        log.error("Archive SSOT not found: %s", archive_path)
        return 1

    log.info("Parsing %s ...", ARCHIVE_REL_PATH)
    nodes, lines = extract_structure(archive_path)
    payload = build_payload(nodes, lines, archive_path, repo_root)

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    if args.stats:
        print(render_stats(payload))
        return 0

    if args.update_index:
        index_dir = repo_root / "data" / "indices"
        index_dir.mkdir(parents=True, exist_ok=True)
        index_path = index_dir / "SSOT_ARCHIVE_STRUCTURAL_INDEX.json"
        index_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        log.info("Index written: %s", index_path.relative_to(repo_root))
        print(f"Written: {index_path.relative_to(repo_root)}")
        # Also print the report
        print(render_report(payload, section_filter=args.section))
        return 0

    print(render_report(payload, section_filter=args.section))
    return 0


if __name__ == "__main__":
    sys.exit(main())
