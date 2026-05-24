#!/usr/bin/env python3
#-*- coding: utf-8 -*-
# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: extract.py
# ║ Python module: Exchange, SessionData, sanitize_unicode, smart_truncate, classify_content, is_noise...
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: 🌿 THE GARDEN
# ║ Semantic ID: TOOL_SESSION_EXTRACTOR_V1
# ║ Purpose: extract.py — Claude Code Session Extractor
# ║ Exports: Exchange, SessionData, sanitize_unicode, smart_truncate, classify_co
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Cross-References (Bidirectional):
# ║ Dependents (Rely on me):
# ║   └─◄ scripts/lib/shared.py
# ╚════════════════════════════════════════════════════════════════════════════

#!/usr/bin/env python3
"""
extract.py — Claude Code Session Extractor

@SID:           TOOL_SESSION_EXTRACTOR_V1
@Type:          CLI Tool
@Context:       Hygiene / Session Analysis
@Implements:    CONCEPT_SESSION_VALUE_EXTRACTION, ROADMAP_TOOL_CONSOLIDATION_2026_01_27
@SessionOrigin: SESSION_DOC_2026_01_17_CLEANUP

Extract valuable content from Claude Code session JSONL files.
Classifies and condenses into structured markdown or JSON.

Usage:
    chthonic extract session.jsonl
    chthonic extract session.jsonl output.md
    chthonic extract session.jsonl --json
    chthonic extract session.jsonl --check-redundancy docs/
"""

from __future__ import annotations


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import argparse
import hashlib
import json
import logging
import re
import sys
import traceback
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from .shared import (
    configure_utf8_output,
    setup_logging,
    add_common_args,
    add_output_arg,
    print_json,
    handle_errors,
)

# Configure UTF-8 output
configure_utf8_output()


# === Data Classes ===

@dataclass
class Exchange:
    """A user-assistant exchange pair."""
    user: str
    assistant: str
    tags: list[str] = field(default_factory=list)
    thinking: str = ""
    content_hash: str = ""

    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = hashlib.md5(
                (self.user + self.assistant).encode()
            ).hexdigest()[:8]


@dataclass
class SessionData:
    """Extracted session data."""
    summary: str = ""
    session_id: str = ""
    git_branch: str = ""
    cwd: str = ""
    version: str = ""
    exchanges: list[Exchange] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    errors: list[str] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)


# === Text Processing ===

def sanitize_unicode(text: str) -> str:
    """Remove or replace problematic Unicode characters for Windows console."""
    replacements = {
        "\u2705": "[OK]",
        "\u274c": "[X]",
        "\u26a0": "[!]",
        "\u2714": "[v]",
        "\u2718": "[x]",
        "\u2192": "->",
        "\u2190": "<-",
        "\u2022": "*",
        "\u00b7": ".",
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text


def smart_truncate(text: str, max_len: int = 500, boundary: str = "sentence") -> str:
    """Truncate text at natural boundaries."""
    if len(text) <= max_len:
        return text

    truncated = text[:max_len]

    if boundary == "sentence":
        for sep in [". ", "! ", "? ", ".\n", "!\n", "?\n"]:
            last_sep = truncated.rfind(sep)
            if last_sep > max_len // 2:
                return truncated[:last_sep + 1].strip()
    elif boundary == "paragraph":
        last_para = truncated.rfind("\n\n")
        if last_para > max_len // 2:
            return truncated[:last_para].strip()

    last_space = truncated.rfind(" ")
    if last_space > max_len // 2:
        return truncated[:last_space].strip() + "..."

    return truncated.strip() + "..."


def classify_content(text: str) -> list[str]:
    """Classify content by topic/intent."""
    patterns = {
        "architecture": r"architect|structure|design|pattern|refactor|module|component",
        "fix": r"\bfix\b|bug|error|issue|problem|broken|crash|fail",
        "feature": r"\badd\b|implement|create|new feature|enhance|introduce",
        "config": r"config|setting|setup|install|environment|\.env|yaml|json",
        "performance": r"optimi[zs]e|performance|speed|slow|fast|cache|memory",
        "security": r"security|auth|permission|credential|secret|token|password",
        "test": r"\btest|spec|coverage|assert|mock|fixture",
        "docs": r"document|readme|comment|explain|jsdoc|docstring",
        "dependency": r"dependency|package|upgrade|version|lockfile|node_modules",
        "governance": r"governance|rule|policy|enforce|lint|ci|workflow",
        "shell": r"shell|bash|pwsh|powershell|terminal|command",
    }

    tags = []
    text_lower = text.lower()
    for tag, pattern in patterns.items():
        if re.search(pattern, text_lower):
            tags.append(tag)

    return tags or ["general"]


def is_noise(text: str, logger: logging.Logger | None = None) -> bool:
    """Filter out noisy/low-value content."""
    noise_patterns = [
        r"^<command-name>",
        r"^<local-command-stdout>",
        r"^<system-reminder>",
        r"^Caveat: The messages below",
        r"^\s*$",
        r"^```\s*$",
        r"^\[object Object\]",
    ]

    text_stripped = text.strip()

    for pattern in noise_patterns:
        if re.match(pattern, text_stripped):
            if logger:
                logger.debug(f"Noise filtered (pattern '{pattern}'): {text_stripped[:50]}")
            return True

    if len(text_stripped) < 20:
        if logger:
            logger.debug(f"Noise filtered (too short): {text_stripped}")
        return True

    return False


def extract_text_content(
    content: Any,
    include_thinking: bool = False,
    logger: logging.Logger | None = None
) -> tuple[str, str]:
    """Extract text from various content formats. Returns (main_text, thinking_text)."""
    main_texts = []
    thinking_texts = []

    try:
        if isinstance(content, str):
            return content, ""

        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    item_type = item.get("type", "")
                    if item_type == "text":
                        main_texts.append(item.get("text", ""))
                    elif item_type == "thinking" and include_thinking:
                        thinking_texts.append(item.get("thinking", ""))
                elif isinstance(item, str):
                    main_texts.append(item)

        if isinstance(content, dict):
            return content.get("text", content.get("content", "")), ""

    except Exception as e:
        if logger:
            logger.warning(f"Error extracting content: {e}")
        return "", ""

    return "\n".join(main_texts), "\n".join(thinking_texts)


def compute_similarity_hash(text: str, granularity: int = 3) -> str:
    """Compute a fuzzy hash for near-duplicate detection."""
    normalized = re.sub(r"[^\w\s]", "", text.lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()

    words = normalized.split()
    if len(words) < granularity:
        return hashlib.md5(normalized.encode()).hexdigest()[:12]

    ngrams = [" ".join(words[i:i+granularity]) for i in range(len(words) - granularity + 1)]
    ngram_hash = hashlib.md5("".join(sorted(ngrams)).encode()).hexdigest()[:12]
    return ngram_hash


def deduplicate_exchanges(exchanges: list[Exchange], logger: logging.Logger | None = None) -> list[Exchange]:
    """Remove near-duplicate exchanges."""
    seen_hashes: set[str] = set()
    unique = []

    for ex in exchanges:
        fuzzy_hash = compute_similarity_hash(ex.user + ex.assistant)
        if fuzzy_hash not in seen_hashes:
            seen_hashes.add(fuzzy_hash)
            unique.append(ex)
        elif logger:
            logger.debug(f"Deduplicated exchange: {ex.user[:50]}...")

    if logger and len(exchanges) != len(unique):
        logger.info(f"Deduplicated: {len(exchanges)} -> {len(unique)} exchanges")

    return unique


def check_redundancy(
    data: SessionData,
    docs_dir: Path,
    logger: logging.Logger | None = None
) -> dict[str, list[str]]:
    """Check if extracted content is redundant with existing docs."""
    redundancy_map: dict[str, list[str]] = {}

    if not docs_dir.exists():
        if logger:
            logger.warning(f"Docs directory not found: {docs_dir}")
        return redundancy_map

    doc_content = ""
    doc_files = list(docs_dir.glob("**/*.md"))
    for doc_file in doc_files:
        try:
            doc_content += doc_file.read_text(encoding="utf-8").lower()
        except Exception as e:
            if logger:
                logger.warning(f"Could not read {doc_file}: {e}")

    for ex in data.exchanges:
        key_phrases = set(
            word for word in re.findall(r"\b\w{6,}\b", ex.user.lower() + ex.assistant.lower())
        )

        matches = sum(1 for phrase in key_phrases if phrase in doc_content)
        overlap_ratio = matches / len(key_phrases) if key_phrases else 0

        if overlap_ratio > 0.5:
            matching_docs = []
            for doc_file in doc_files:
                try:
                    content = doc_file.read_text(encoding="utf-8").lower()
                    doc_matches = sum(1 for p in key_phrases if p in content)
                    if doc_matches > len(key_phrases) * 0.3:
                        matching_docs.append(doc_file.name)
                except:
                    pass

            if matching_docs:
                redundancy_map[ex.content_hash] = matching_docs
                if logger:
                    logger.info(f"Exchange {ex.content_hash} redundant with: {matching_docs}")

    return redundancy_map


def process_session(
    filepath: Path,
    include_thinking: bool = False,
    logger: logging.Logger | None = None
) -> SessionData:
    """Process a session JSONL file and extract valuable content."""
    data = SessionData()
    data.stats = {"lines": 0, "parsed": 0, "errors": 0, "noise_filtered": 0}

    current_exchange: dict[str, Any] = {"user": "", "assistant": "", "thinking": "", "tags": []}

    if logger:
        logger.info(f"Processing: {filepath}")

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                data.stats["lines"] += 1
                line = line.strip()

                if not line:
                    continue

                try:
                    entry = json.loads(line)
                    data.stats["parsed"] += 1
                except json.JSONDecodeError as e:
                    data.stats["errors"] += 1
                    if logger:
                        logger.debug(f"JSON parse error at line {line_num}: {e}")
                    data.errors.append(f"Line {line_num}: JSON parse error - {e}")
                    continue

                entry_type = entry.get("type", "")

                if entry_type == "summary":
                    data.summary = entry.get("summary", "")
                    data.tags.update(classify_content(data.summary))
                    if logger:
                        logger.debug(f"Found summary: {data.summary[:100]}")

                if not data.session_id and entry.get("sessionId"):
                    data.session_id = entry.get("sessionId", "")
                if not data.git_branch and entry.get("gitBranch"):
                    data.git_branch = entry.get("gitBranch", "")
                if not data.cwd and entry.get("cwd"):
                    data.cwd = entry.get("cwd", "")
                if not data.version and entry.get("version"):
                    data.version = entry.get("version", "")

                if entry_type == "user":
                    msg = entry.get("message", {})
                    content, _ = extract_text_content(msg.get("content", ""), include_thinking=False, logger=logger)

                    if is_noise(content, logger):
                        data.stats["noise_filtered"] += 1
                        continue

                    if current_exchange["user"] and current_exchange["assistant"]:
                        ex = Exchange(
                            user=smart_truncate(current_exchange["user"], 500),
                            assistant=smart_truncate(current_exchange["assistant"], 800),
                            tags=list(set(current_exchange["tags"])),
                            thinking=smart_truncate(current_exchange["thinking"], 300) if include_thinking else ""
                        )
                        data.exchanges.append(ex)

                    current_exchange = {
                        "user": content,
                        "assistant": "",
                        "thinking": "",
                        "tags": classify_content(content),
                    }

                if entry_type == "assistant":
                    msg = entry.get("message", {})
                    content_list = msg.get("content", [])

                    main_text, thinking_text = extract_text_content(
                        content_list,
                        include_thinking=include_thinking,
                        logger=logger
                    )

                    if main_text and not is_noise(main_text, logger):
                        current_exchange["assistant"] += main_text + "\n"
                        current_exchange["tags"].extend(classify_content(main_text))
                    else:
                        data.stats["noise_filtered"] += 1

                    if thinking_text:
                        current_exchange["thinking"] += thinking_text + "\n"

    except Exception as e:
        error_msg = f"Fatal error processing file: {e}\n{traceback.format_exc()}"
        data.errors.append(error_msg)
        if logger:
            logger.error(error_msg)

    if current_exchange["user"] and current_exchange["assistant"]:
        ex = Exchange(
            user=smart_truncate(current_exchange["user"], 500),
            assistant=smart_truncate(current_exchange["assistant"], 800),
            tags=list(set(current_exchange["tags"])),
            thinking=smart_truncate(current_exchange["thinking"], 300) if include_thinking else ""
        )
        data.exchanges.append(ex)

    original_count = len(data.exchanges)
    data.exchanges = deduplicate_exchanges(data.exchanges, logger)
    data.stats["deduplicated"] = original_count - len(data.exchanges)

    data.tags = set(data.tags)
    for ex in data.exchanges:
        data.tags.update(ex.tags)

    if logger:
        logger.info(f"Stats: {data.stats}")
        logger.info(f"Extracted {len(data.exchanges)} exchanges, tags: {data.tags}")

    return data


def generate_markdown(data: SessionData, redundancy: dict[str, list[str]] | None = None) -> str:
    """Generate condensed markdown from extracted data."""
    lines = [
        f"# Session Archive: {data.summary or 'Untitled'}",
        "",
        "## Metadata",
    ]

    if data.session_id:
        lines.append(f"- **Session ID:** `{data.session_id[:8]}...`")
    if data.git_branch:
        lines.append(f"- **Branch:** `{data.git_branch}`")
    if data.version:
        lines.append(f"- **Claude Code Version:** `{data.version}`")
    if data.tags:
        lines.append(f"- **Tags:** {', '.join(f'`{t}`' for t in sorted(data.tags))}")
    if data.stats:
        lines.append(f"- **Stats:** {data.stats.get('parsed', 0)} entries parsed, "
                    f"{len(data.exchanges)} exchanges extracted")
    lines.append("")

    if data.errors:
        lines.append("## Errors")
        lines.append("")
        for err in data.errors[:5]:
            lines.append(f"- {err[:200]}")
        lines.append("")

    if data.exchanges:
        lines.append("## Key Exchanges")
        lines.append("")

        by_tag: dict[str, list[Exchange]] = defaultdict(list)
        for ex in data.exchanges:
            primary_tag = ex.tags[0] if ex.tags else "general"
            by_tag[primary_tag].append(ex)

        for tag in sorted(by_tag.keys()):
            exchanges = by_tag[tag]
            lines.append(f"### {tag.title()}")
            lines.append("")

            for i, ex in enumerate(exchanges[:5], 1):
                user_excerpt = sanitize_unicode(ex.user.replace("\n", " "))
                assistant_excerpt = sanitize_unicode(ex.assistant.replace("\n", " "))

                redundancy_note = ""
                if redundancy and ex.content_hash in redundancy:
                    docs = ", ".join(redundancy[ex.content_hash])
                    redundancy_note = f" *(redundant with: {docs})*"

                lines.append(f"**Q{i}:** {user_excerpt[:200]}...{redundancy_note}")
                lines.append("")
                lines.append(f"> {assistant_excerpt[:400]}...")
                lines.append("")

                if ex.thinking:
                    lines.append(f"<details><summary>Thinking</summary>")
                    lines.append("")
                    lines.append(f"{sanitize_unicode(ex.thinking[:200])}...")
                    lines.append("")
                    lines.append("</details>")
                    lines.append("")

    return "\n".join(lines)


@handle_errors
def main():
    parser = argparse.ArgumentParser(
        description="Extract valuable content from Claude Code session JSONL files.",
        prog="chthonic extract"
    )
    parser.add_argument("input", type=Path, help="Input JSONL file")
    parser.add_argument("--include-thinking", action="store_true", help="Include Claude's thinking blocks")
    parser.add_argument("--check-redundancy", type=Path, metavar="DIR", help="Cross-reference against docs in DIR")
    parser.add_argument("--format", choices=["md", "json"], default="md", help="Output format (md or json)")
    
    add_common_args(parser)
    add_output_arg(parser, "Output file (prints to console if omitted)")

    args = parser.parse_args()
    logger = setup_logging(verbose=args.verbose, quiet=args.quiet)

    if not args.input.exists():
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)

    data = process_session(args.input, include_thinking=args.include_thinking, logger=logger)

    redundancy = None
    if args.check_redundancy:
        redundancy = check_redundancy(data, args.check_redundancy, logger)
        redundant_count = len(redundancy)
        logger.info(f"Redundancy check: {redundant_count}/{len(data.exchanges)} exchanges overlap with existing docs")

    if args.dry_run:
        logger.info("=" * 60)
        logger.info("DRY RUN - Extraction Stats")
        logger.info("=" * 60)
        logger.info(f"Input file:      {args.input}")
        logger.info(f"Summary:         {data.summary or '(none)'}")
        logger.info(f"Session ID:      {data.session_id[:8]}..." if data.session_id else "Session ID:      (none)")
        logger.info(f"Branch:          {data.git_branch or '(none)'}")
        logger.info(f"Version:         {data.version or '(none)'}")
        logger.info(f"Lines parsed:    {data.stats.get('parsed', 0)}")
        logger.info(f"Noise filtered:  {data.stats.get('noise_filtered', 0)}")
        logger.info(f"Exchanges:       {len(data.exchanges)}")
        logger.info(f"Deduplicated:    {data.stats.get('deduplicated', 0)}")
        logger.info(f"Tags:            {', '.join(sorted(data.tags)) or '(none)'}")
        logger.info(f"Parse errors:    {len(data.errors)}")
        if redundancy:
            logger.info(f"Redundant:       {len(redundancy)}/{len(data.exchanges)} overlap with existing docs")
        logger.info("=" * 60)
        return

    if args.format == "json" or args.json:
        output_data = {
            "summary": data.summary,
            "session_id": data.session_id,
            "git_branch": data.git_branch,
            "cwd": data.cwd,
            "version": data.version,
            "tags": sorted(data.tags),
            "stats": data.stats,
            "errors": data.errors,
            "exchanges": [
                {
                    "user": ex.user,
                    "assistant": ex.assistant,
                    "tags": ex.tags,
                    "thinking": ex.thinking,
                    "content_hash": ex.content_hash,
                    "redundant_with": redundancy.get(ex.content_hash, []) if redundancy else []
                }
                for ex in data.exchanges
            ]
        }
        
        if args.output:
            args.output.write_text(json.dumps(output_data, indent=2, ensure_ascii=False), encoding="utf-8")
            logger.info(f"Written to {args.output}")
        else:
            print_json(output_data)
    else:
        output = generate_markdown(data, redundancy)
        
        if args.output:
            args.output.write_text(output, encoding="utf-8")
            logger.info(f"Written to {args.output}")
        else:
            print(sanitize_unicode(output))

    logger.info(f"Extracted: {len(data.exchanges)} exchanges, tags: {sorted(data.tags)}")


if __name__ == "__main__":
    main()
