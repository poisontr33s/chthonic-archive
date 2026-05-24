#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: extract_session_value.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
extract_session_value.py — Claude Code Session Extractor

@SID:           TOOL_SESSION_EXTRACTOR_V1
@Shabti:          Script
@Context:       Hygiene / Session Analysis
@Implements:    CONCEPT_SESSION_VALUE_EXTRACTION
@Purpose:       extract_session_value.py — Claude Code Session Extractor
FILE METADATA (Legacy Path-Based — Deprecated)
Created:        2026-01-17
Session Doc:    docs/SESSION_2026-01-17_CLEANUP.md  # Use @SID reference instead
Related Files:  @SID:TOOL_ROOT_AUDIT_V1
Category:       Tooling / Session Analysis

Extract valuable content from Claude Code session JSONL files.
Classifies and condenses into structured markdown or JSON.

WHAT THIS SCRIPT DOES

Claude Code stores conversation history in JSONL files at:
  ~/.claude/projects/<project-name>/*.jsonl

This script extracts valuable exchanges (user questions + assistant answers),
filters out noise (tool calls, empty content), classifies by topic, and
outputs condensed markdown or JSON for documentation or review.

USAGE EXAMPLES

1. BASIC EXTRACTION (preview to console):
   uv run scripts/extract_session_value.py session.jsonl

2. EXTRACT TO FILE:
   uv run scripts/extract_session_value.py session.jsonl output.md

3. DRY RUN (show stats without output):
   uv run scripts/extract_session_value.py session.jsonl --dry-run

4. JSON OUTPUT (for automation/processing):
   uv run scripts/extract_session_value.py session.jsonl --format json > data.json

5. CHECK IF CONTENT IS REDUNDANT with existing docs:
   uv run scripts/extract_session_value.py session.jsonl --check-redundancy docs/

6. INCLUDE CLAUDE'S THINKING blocks (internal reasoning):
   uv run scripts/extract_session_value.py session.jsonl --include-thinking

7. FULL DEBUG MODE (logs everything to file):
   uv run scripts/extract_session_value.py session.jsonl --debug --log debug.log

8. COMBINE OPTIONS:
   uv run scripts/extract_session_value.py session.jsonl output.md \\
       --check-redundancy docs/ --include-thinking --debug

OPTIONS REFERENCE

Positional:
  input                   Path to .jsonl session file (required)
  output                  Path to output file (optional, prints to console if omitted)

Flags:
  --dry-run               Show extraction stats without generating output
  --format [md|json]      Output format: 'md' (default) or 'json'
  --include-thinking      Include Claude's <thinking> blocks in output
  --check-redundancy DIR  Cross-reference against .md files in DIR
  --debug                 Enable verbose debug logging to console and file
  --log FILE              Custom log file path (default: extract_session.log)
  -h, --help              Show help message

OUTPUT CLASSIFICATION TAGS

Exchanges are auto-tagged by content:
  architecture  - design, patterns, refactoring, modules
  fix           - bugs, errors, issues, problems
  feature       - new functionality, enhancements
  config        - settings, setup, environment
  performance   - optimization, speed, caching
  security      - auth, permissions, credentials
  test          - testing, coverage, assertions
  docs          - documentation, comments
  dependency    - packages, versions, lockfiles
  governance    - rules, policies, CI/CD, linting
  shell         - bash, powershell, terminal commands
  general       - uncategorized
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import sys
import traceback
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any


# === Logging Setup ===

def setup_logging(debug: bool = False, log_file: Path | None = None) -> logging.Logger:
    """Configure logging with file and console handlers."""
    logger = logging.getLogger("extract_session")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler (always, but level varies)
    console = logging.StreamHandler(sys.stderr)
    console.setLevel(logging.DEBUG if debug else logging.WARNING)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # File handler (if specified or debug mode)
    if log_file or debug:
        log_path = log_file or Path("extract_session.log")
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.info(f"Debug log: {log_path.absolute()}")

    return logger


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
        "\u2705": "[OK]",      # ✅
        "\u274c": "[X]",       # ❌
        "\u26a0": "[!]",       # ⚠
        "\u2714": "[v]",       # ✔
        "\u2718": "[x]",       # ✘
        "\u2192": "->",        # →
        "\u2190": "<-",        # ←
        "\u2022": "*",         # •
        "\u00b7": ".",         # ·
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    # Remove remaining non-ASCII if needed for console
    return text


def smart_truncate(text: str, max_len: int = 500, boundary: str = "sentence") -> str:
    """Truncate text at natural boundaries."""
    if len(text) <= max_len:
        return text

    truncated = text[:max_len]

    if boundary == "sentence":
        # Find last sentence boundary
        for sep in [". ", "! ", "? ", ".\n", "!\n", "?\n"]:
            last_sep = truncated.rfind(sep)
            if last_sep > max_len // 2:
                return truncated[:last_sep + 1].strip()

    elif boundary == "paragraph":
        last_para = truncated.rfind("\n\n")
        if last_para > max_len // 2:
            return truncated[:last_para].strip()

    # Fallback: word boundary
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
        r"^```\s*$",  # Empty code blocks
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
    """
    Extract text from various content formats.
    Returns (main_text, thinking_text).
    """
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


# === Deduplication ===

def compute_similarity_hash(text: str, granularity: int = 3) -> str:
    """Compute a fuzzy hash for near-duplicate detection."""
    # Normalize: lowercase, collapse whitespace, remove punctuation
    normalized = re.sub(r"[^\w\s]", "", text.lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()

    # Use n-gram based hashing for fuzzy matching
    words = normalized.split()
    if len(words) < granularity:
        return hashlib.md5(normalized.encode()).hexdigest()[:12]

    ngrams = [" ".join(words[i:i+granularity]) for i in range(len(words) - granularity + 1)]
    ngram_hash = hashlib.md5("".join(sorted(ngrams)).encode()).hexdigest()[:12]
    return ngram_hash


def deduplicate_exchanges(
    exchanges: list[Exchange],
    logger: logging.Logger | None = None
) -> list[Exchange]:
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


# === Redundancy Detection ===

def check_redundancy(
    data: SessionData,
    docs_dir: Path,
    logger: logging.Logger | None = None
) -> dict[str, list[str]]:
    """
    Check if extracted content is redundant with existing docs.
    Returns dict of {exchange_hash: [matching_doc_files]}.
    """
    redundancy_map: dict[str, list[str]] = {}

    if not docs_dir.exists():
        if logger:
            logger.warning(f"Docs directory not found: {docs_dir}")
        return redundancy_map

    # Load existing doc content
    doc_content = ""
    doc_files = list(docs_dir.glob("**/*.md"))
    for doc_file in doc_files:
        try:
            doc_content += doc_file.read_text(encoding="utf-8").lower()
        except Exception as e:
            if logger:
                logger.warning(f"Could not read {doc_file}: {e}")

    # Check each exchange for keyword overlap
    for ex in data.exchanges:
        # Extract key phrases (words > 5 chars)
        key_phrases = set(
            word for word in re.findall(r"\b\w{6,}\b", ex.user.lower() + ex.assistant.lower())
        )

        # Count matches
        matches = sum(1 for phrase in key_phrases if phrase in doc_content)
        overlap_ratio = matches / len(key_phrases) if key_phrases else 0

        if overlap_ratio > 0.5:  # More than 50% keyword overlap
            # Find which docs contain the most matches
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
                    logger.info(
                        f"Exchange {ex.content_hash} redundant with: {matching_docs}"
                    )

    return redundancy_map


# === Main Processing ===

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

                # Extract summary
                if entry_type == "summary":
                    data.summary = entry.get("summary", "")
                    data.tags.update(classify_content(data.summary))
                    if logger:
                        logger.debug(f"Found summary: {data.summary[:100]}")

                # Extract metadata (take first non-empty values)
                if not data.session_id and entry.get("sessionId"):
                    data.session_id = entry.get("sessionId", "")
                if not data.git_branch and entry.get("gitBranch"):
                    data.git_branch = entry.get("gitBranch", "")
                if not data.cwd and entry.get("cwd"):
                    data.cwd = entry.get("cwd", "")
                if not data.version and entry.get("version"):
                    data.version = entry.get("version", "")

                # Extract user messages
                if entry_type == "user":
                    msg = entry.get("message", {})
                    content, _ = extract_text_content(
                        msg.get("content", ""),
                        include_thinking=False,
                        logger=logger
                    )

                    if is_noise(content, logger):
                        data.stats["noise_filtered"] += 1
                        continue

                    # Save previous exchange if complete
                    if current_exchange["user"] and current_exchange["assistant"]:
                        ex = Exchange(
                            user=smart_truncate(current_exchange["user"], 500),
                            assistant=smart_truncate(current_exchange["assistant"], 800),
                            tags=list(set(current_exchange["tags"])),
                            thinking=smart_truncate(current_exchange["thinking"], 300) if include_thinking else ""
                        )
                        data.exchanges.append(ex)

                    # Start new exchange
                    current_exchange = {
                        "user": content,
                        "assistant": "",
                        "thinking": "",
                        "tags": classify_content(content),
                    }

                # Extract assistant responses
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

    # Add final exchange
    if current_exchange["user"] and current_exchange["assistant"]:
        ex = Exchange(
            user=smart_truncate(current_exchange["user"], 500),
            assistant=smart_truncate(current_exchange["assistant"], 800),
            tags=list(set(current_exchange["tags"])),
            thinking=smart_truncate(current_exchange["thinking"], 300) if include_thinking else ""
        )
        data.exchanges.append(ex)

    # Deduplicate
    original_count = len(data.exchanges)
    data.exchanges = deduplicate_exchanges(data.exchanges, logger)
    data.stats["deduplicated"] = original_count - len(data.exchanges)

    # Finalize tags
    data.tags = set(data.tags)
    for ex in data.exchanges:
        data.tags.update(ex.tags)

    if logger:
        logger.info(f"Stats: {data.stats}")
        logger.info(f"Extracted {len(data.exchanges)} exchanges, tags: {data.tags}")

    return data


# === Output Generators ===

def generate_markdown(
    data: SessionData,
    redundancy: dict[str, list[str]] | None = None
) -> str:
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
        for err in data.errors[:5]:  # Limit displayed errors
            lines.append(f"- {err[:200]}")
        lines.append("")

    if data.exchanges:
        lines.append("## Key Exchanges")
        lines.append("")

        # Group by primary tag
        by_tag: dict[str, list[Exchange]] = defaultdict(list)
        for ex in data.exchanges:
            primary_tag = ex.tags[0] if ex.tags else "general"
            by_tag[primary_tag].append(ex)

        for tag in sorted(by_tag.keys()):
            exchanges = by_tag[tag]
            lines.append(f"### {tag.title()}")
            lines.append("")

            for i, ex in enumerate(exchanges[:5], 1):  # Limit 5 per tag
                user_excerpt = sanitize_unicode(ex.user.replace("\n", " "))
                assistant_excerpt = sanitize_unicode(ex.assistant.replace("\n", " "))

                # Mark redundant exchanges
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


def generate_json(data: SessionData, redundancy: dict[str, list[str]] | None = None) -> str:
    """Generate JSON output from extracted data."""
    output = {
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
    return json.dumps(output, indent=2, ensure_ascii=False)


# === CLI ===

def main():
    parser = argparse.ArgumentParser(
        description="Extract valuable content from Claude Code session JSONL files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("input", type=Path, help="Input JSONL file")
    parser.add_argument("output", type=Path, nargs="?", help="Output file (optional)")
    parser.add_argument("--dry-run", action="store_true", help="Show stats without generating output")
    parser.add_argument("--format", choices=["md", "json"], default="md", help="Output format (md or json)")
    parser.add_argument("--include-thinking", action="store_true", help="Include Claude's thinking blocks")
    parser.add_argument("--check-redundancy", type=Path, metavar="DIR", help="Cross-reference against docs in DIR")
    parser.add_argument("--debug", action="store_true", help="Enable verbose debug logging")
    parser.add_argument("--log", type=Path, help="Log file path (default: extract_session.log)")

    args = parser.parse_args()

    # Setup logging
    logger = setup_logging(debug=args.debug, log_file=args.log)

    # Validate input
    if not args.input.exists():
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)

    # Process
    try:
        data = process_session(
            args.input,
            include_thinking=args.include_thinking,
            logger=logger
        )

        # Check redundancy if requested
        redundancy = None
        if args.check_redundancy:
            redundancy = check_redundancy(data, args.check_redundancy, logger)
            redundant_count = len(redundancy)
            logger.info(f"Redundancy check: {redundant_count}/{len(data.exchanges)} exchanges overlap with existing docs")

        # Dry run: show stats and exit
        if args.dry_run:
            print("=" * 60)
            print("DRY RUN - Extraction Stats")
            print("=" * 60)
            print(f"Input file:      {args.input}")
            print(f"Summary:         {data.summary or '(none)'}")
            print(f"Session ID:      {data.session_id[:8]}..." if data.session_id else "Session ID:      (none)")
            print(f"Branch:          {data.git_branch or '(none)'}")
            print(f"Version:         {data.version or '(none)'}")
            print(f"Lines parsed:    {data.stats.get('parsed', 0)}")
            print(f"Noise filtered:  {data.stats.get('noise_filtered', 0)}")
            print(f"Exchanges:       {len(data.exchanges)}")
            print(f"Deduplicated:    {data.stats.get('deduplicated', 0)}")
            print(f"Tags:            {', '.join(sorted(data.tags)) or '(none)'}")
            print(f"Parse errors:    {len(data.errors)}")
            if redundancy:
                print(f"Redundant:       {len(redundancy)}/{len(data.exchanges)} overlap with existing docs")
            print("=" * 60)
            if data.exchanges:
                print("\nSample exchanges (first 3):")
                for i, ex in enumerate(data.exchanges[:3], 1):
                    print(f"  {i}. [{', '.join(ex.tags[:2])}] {ex.user[:60]}...")
            print("\nRun without --dry-run to generate output.")
            sys.exit(0)

        # Generate output
        if args.format == "json":
            output = generate_json(data, redundancy)
        else:
            output = generate_markdown(data, redundancy)

        # Write or print
        if args.output:
            args.output.write_text(output, encoding="utf-8")
            print(f"Written to {args.output}")
        else:
            # Safe console output
            try:
                print(sanitize_unicode(output))
            except UnicodeEncodeError:
                # Fallback for Windows console
                print(output.encode("ascii", errors="replace").decode())

        # Summary to stderr
        print(f"\nExtracted: {len(data.exchanges)} exchanges, tags: {sorted(data.tags)}", file=sys.stderr)
        if data.errors:
            print(f"Errors: {len(data.errors)} (see log for details)", file=sys.stderr)

    except Exception as e:
        logger.error(f"Fatal error: {e}\n{traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    main()
