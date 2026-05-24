#!/usr/bin/env python3
#-*- coding: utf-8 -*-
# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: compact.py
# ║ Python module: CompactStats, is_noise, is_keep, compact_lines, compact_file, main
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: 🌿 THE GARDEN
# ║ Semantic ID: TOOL_COMPACT_MD_V1
# ║ Purpose: compact.py - Markdown Template-Based Compactor
# ║ Exports: CompactStats, is_noise, is_keep, compact_lines, compact_file, main
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Cross-References (Bidirectional):
# ║ Dependents (Rely on me):
# ║   └─◄ scripts/lib/shared.py
# ╚════════════════════════════════════════════════════════════════════════════

#!/usr/bin/env python3
"""
compact.py - Markdown Template-Based Compactor

@SID:           TOOL_COMPACT_MD_V1
@Type:          CLI Tool
@Context:       Hygiene / Content Compression
@SessionOrigin: STANDALONE_2026_01_27
@Implements:    ROADMAP_TOOL_CONSOLIDATION_2026_01_27
@ReferencedBy:  DOC_CLAUDE_MD_ROOT

Condenses large .md files using template-based rules.
Preserves structured data (tables, @SID headers, decisions).
Strips noise (tool calls, terminal output, status lines).
Overwrites in-place (State File pattern).

Usage:
    chthonic compact FILE.md                    # Compact in-place
    chthonic compact FILE.md --dry-run          # Preview without writing
    chthonic compact FILE.md --stats            # Show compression stats only
    chthonic compact DIR/ --batch               # Compact all .md in directory
    chthonic compact FILE.md --json             # Output stats as JSON
"""

from __future__ import annotations

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')



import argparse
import re
from dataclasses import dataclass
from pathlib import Path

from .shared import (
    configure_utf8_output,
    setup_logging,
    add_common_args,
    print_json,
    handle_errors,
)

# Configure UTF-8 output
configure_utf8_output()


# ---------------------------------------------------------------------------
#  Pattern Definitions
# ---------------------------------------------------------------------------

# Lines matching these patterns are NOISE — removed entirely
NOISE_PATTERNS: list[re.Pattern] = [
    re.compile(r"^Ran terminal command:.*", re.IGNORECASE),
    re.compile(r"^Checked background terminal output"),
    re.compile(r"^Got (last )?terminal command"),
    re.compile(r"^Got output for .* task"),
    re.compile(r"^Enable shell integration.*"),
    re.compile(r"^Terminal is no longer available\."),
    re.compile(r"^Optimizing tool selection\.\.\."),
    re.compile(r"^Summarized conversation history"),
    re.compile(r"^Made changes\.\s*$"),
    re.compile(r"^Read \[]\(file:///.*\)"),
    re.compile(r"^Searched .*for .*,\s*\d+ results"),
    re.compile(r"^Ran `Search\w+`"),
    re.compile(r"^Completed with input:\s*\{"),
    re.compile(r"^Fetched https?://"),
    re.compile(r"^Generating patch \(\d+ lines?\)"),
    re.compile(r"^Replacing \d+ lines with \d+ lines"),
    re.compile(r"^Created \[]\(file:///.*\)$"),
    re.compile(r'^Searched for files matching `.*`, no matches$'),
    re.compile(r'^\s*"query"\s*:'),
    re.compile(r'^\}$'),
    re.compile(r'^Created \d+ todos?$'),
    re.compile(r'^Starting: \*.*\*\s*\(\d+/\d+\)$'),
    re.compile(r'^Completed: \*.*\*\s*\(\d+/\d+\)$'),
    re.compile(r'^GitHub Copilot:\s*Read \['),
    re.compile(r'^Now let me (?:search|update|create|check|get|install|capture)'),
    re.compile(r"^Now I'll (?:create|build|add|update|check|fix)"),
    re.compile(r'^Now I can use'),
    re.compile(r'^Now (?:applying|fixing) '),
    re.compile(r'^Let me (?:check|try|fix|update|create|get|capture|wait|add|run)'),
    re.compile(r'^Edited$'),
    re.compile(r'^\w+\.\w+\+\d+-\d+$'),
    re.compile(r'^Searched for (?:text|regex) `'),
    re.compile(r'^Searched \S+ for '),
    re.compile(r'^Read \[]\(file:///'),
    re.compile(r'^Replacing \d+ lines with \d+ lines in'),
    re.compile(r'^Fetched \d+ resources?$'),
    re.compile(r'^Terminal (?:seems|is) (?:unresponsive|stuck|back)'),
    re.compile(r'^GitHub Copilot:\s*$'),
    re.compile(r'^GitHub Copilot:\s*(?:Read|Searched|Fetched|Created)'),
    re.compile(r'^It\'s capturing|^Good progress'),
    re.compile(r'^The crawler is (?:still )?running'),
    re.compile(r'^Terminal is back\.'),
    re.compile(r'^Replacing \d+ lines?$'),
    re.compile(r'^warn:\s+'),
    re.compile(r'^create mode \d+'),
    re.compile(r'^PS (?:C:\\|/|~)'),
    re.compile(r'^\(\d+/\d+\)'),
    re.compile(r'^GitHub Copilot: Let me'),
    re.compile(r'^Created \[.*\]\(file:'),
    re.compile(r'^Read \[.*\]\(file:'),
    re.compile(r'^\[\]\(file:///'),
    re.compile(r'^Now implementing'),
    re.compile(r"^Now I'm "),
    re.compile(r'^Now I have (?:enough )?context'),
    re.compile(r'^Also update '),
    re.compile(r'^Also (?:add|fix|check) '),
    re.compile(r'^[\u2551\u2503\u2502\u2523\u2503]+\s*[\u2551\u2503\u2502]*\s*$'),
    re.compile(r'^[-=_]{6,}$'),
    re.compile(r'^[\u2193\u2191\u2192\u2190\u21B3↓]+\s*$'),
    re.compile(r'^\^+\s*$'),
    re.compile(r'^\|+\s*$'),
    re.compile(r'^- §\d+\.\d+:\s+'),
    re.compile(r'^- [A-Z]{2,}:\s+'),
    re.compile(r'^warn: (?:incorrect peer dependency|deprecated|SKIPPING OPTIONAL)'),
    re.compile(r'^create mode \d{6}'),
    re.compile(r'^PS [A-Z]:\\'),
    re.compile(r'^\[?\d{1,2}:\d{2}:\d{2}(?:\s+[AP]M)?\]?\s*$'),
    re.compile(r'^\s+at <anonymous>'),
    re.compile(r'^\s+at .*\(.*:\d+:\d+\)$'),
    re.compile(r'^error: expect\('),
    re.compile(r'^SyntaxError:'),
    re.compile(r'^\s*\^$'),
    re.compile(r'^\s+Expected (?:to )?(?:not )?'),
    re.compile(r'^\s+Received:'),
]

# Lines matching these are KEEP — never removed
KEEP_PATTERNS: list[re.Pattern] = [
    re.compile(r"^@SID:"),
    re.compile(r"^@Type:"),
    re.compile(r"^@Context:"),
    re.compile(r"^@Implements:"),
    re.compile(r"^@SessionOrigin:"),
    re.compile(r"^@Emits:"),
    re.compile(r"^@References:"),
    re.compile(r"^@ReferencedBy:"),
    re.compile(r"^@Related:"),
    re.compile(r"^@Spawned:"),
    re.compile(r"^#{1,6}\s"),
    re.compile(r"^\|.*\|.*\|"),
    re.compile(r"^[-*]\s+\[[ x]]\s"),
    re.compile(r"^\*\*Verdict"),
    re.compile(r"^\*\*Key "),
    re.compile(r"^\*\*Summary"),
]


@dataclass
class CompactStats:
    original_lines: int = 0
    output_lines: int = 0
    noise_removed: int = 0
    blanks_collapsed: int = 0
    code_blocks_trimmed: int = 0
    sections_found: int = 0

    @property
    def ratio(self) -> float:
        if self.original_lines == 0:
            return 0.0
        return 1 - (self.output_lines / self.original_lines)


def is_noise(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    for pat in NOISE_PATTERNS:
        if pat.search(stripped):
            return True
    return False


def is_keep(line: str) -> bool:
    stripped = line.strip()
    for pat in KEEP_PATTERNS:
        if pat.search(stripped):
            return True
    return False


def compact_lines(lines: list[str]) -> tuple[list[str], CompactStats]:
    """Apply template rules to condense lines."""
    stats = CompactStats(original_lines=len(lines))
    output: list[str] = []
    consecutive_blanks = 0
    in_code_block = False
    code_block_lines: list[str] = []
    code_block_lang = ""

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Track code blocks
        if stripped.startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_block_lang = stripped[3:].strip()
                code_block_lines = []
                i += 1
                continue
            else:
                in_code_block = False
                meaningful = [cl for cl in code_block_lines if cl.strip() and not is_noise(cl)]
                if meaningful:
                    output.append(f"```{code_block_lang}")
                    if len(meaningful) > 20:
                        output.extend(meaningful[:20])
                        output.append(f"  ... ({len(meaningful) - 20} more lines)")
                        stats.code_blocks_trimmed += 1
                    else:
                        output.extend(meaningful)
                    output.append("```")
                else:
                    stats.noise_removed += len(code_block_lines) + 2
                consecutive_blanks = 0
                i += 1
                continue

        if in_code_block:
            code_block_lines.append(line)
            i += 1
            continue

        if not stripped:
            consecutive_blanks += 1
            if consecutive_blanks <= 1:
                output.append("")
            else:
                stats.blanks_collapsed += 1
            i += 1
            continue
        else:
            consecutive_blanks = 0

        if is_keep(line):
            if stripped.startswith("#"):
                stats.sections_found += 1
            output.append(line)
            i += 1
            continue

        if is_noise(line):
            stats.noise_removed += 1
            i += 1
            continue

        output.append(line)
        i += 1

    while output and not output[-1].strip():
        output.pop()
    output.append("")

    stats.output_lines = len(output)
    return output, stats


def compact_file(path: Path, logger) -> tuple[str, CompactStats]:
    """Read and compact a single .md file."""
    logger.debug(f"Compacting: {path}")
    content = path.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()
    output_lines, stats = compact_lines(lines)
    return "\n".join(output_lines), stats


@handle_errors
def main():
    parser = argparse.ArgumentParser(
        description="Template-based markdown compactor (State File pattern).",
        prog="chthonic compact"
    )
    parser.add_argument(
        "target", type=Path,
        help="Markdown file or directory (with --batch)"
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="Show compression statistics only"
    )
    parser.add_argument(
        "--batch", action="store_true",
        help="Compact all .md files in directory"
    )
    parser.add_argument(
        "--min-lines", type=int, default=100,
        help="Skip files shorter than this (batch mode, default: 100)"
    )
    
    add_common_args(parser)

    args = parser.parse_args()
    logger = setup_logging(verbose=args.verbose, quiet=args.quiet)

    if args.batch:
        if not args.target.is_dir():
            logger.error(f"{args.target} is not a directory")
            return
        
        files = sorted(args.target.glob("**/*.md"))
        results = []
        
        for f in files:
            line_count = sum(1 for _ in open(f, encoding="utf-8", errors="ignore"))
            if line_count < args.min_lines:
                continue
            
            output, stats = compact_file(f, logger)
            results.append({"file": str(f), "stats": stats})
            
            if not args.dry_run and not args.stats:
                f.write_text(output, encoding="utf-8")
                logger.info(f"Compacted: {f} ({stats.original_lines} -> {stats.output_lines}, {stats.ratio:.0%} reduction)")
            elif args.stats or args.dry_run:
                logger.info(f"{f}: {stats.original_lines} -> {stats.output_lines} ({stats.ratio:.0%})")

        if args.json:
            print_json([
                {
                    "file": r["file"],
                    "original": r["stats"].original_lines,
                    "output": r["stats"].output_lines,
                    "ratio": round(r["stats"].ratio, 3)
                }
                for r in results
            ])
        return

    # Single file mode
    if not args.target.is_file():
        logger.error(f"{args.target} not found")
        return

    output, stats = compact_file(args.target, logger)

    if args.json:
        print_json({
            "file": str(args.target),
            "original_lines": stats.original_lines,
            "output_lines": stats.output_lines,
            "ratio": round(stats.ratio, 3),
            "noise_removed": stats.noise_removed,
            "blanks_collapsed": stats.blanks_collapsed,
            "code_blocks_trimmed": stats.code_blocks_trimmed,
            "sections_found": stats.sections_found,
        })
        return

    if args.stats:
        logger.info(f"File:             {args.target}")
        logger.info(f"Original lines:   {stats.original_lines}")
        logger.info(f"Output lines:     {stats.output_lines}")
        logger.info(f"Reduction:        {stats.ratio:.0%}")
        logger.info(f"Noise removed:    {stats.noise_removed}")
        logger.info(f"Blanks collapsed: {stats.blanks_collapsed}")
        logger.info(f"Code blocks trim: {stats.code_blocks_trimmed}")
        logger.info(f"Sections found:   {stats.sections_found}")
        return

    if args.dry_run:
        logger.info(f"[DRY RUN] {args.target}: {stats.original_lines} -> {stats.output_lines} ({stats.ratio:.0%} reduction)")
        logger.info("[DRY RUN] First 50 lines of output:")
        logger.info("-" * 60)
        for line in output.split("\n")[:50]:
            print(line)
        logger.info("-" * 60)
        logger.info(f"... ({stats.output_lines} total lines)")
        return

    # Write in-place
    args.target.write_text(output, encoding="utf-8")
    logger.info(f"Compacted: {args.target}")
    logger.info(f"  {stats.original_lines} -> {stats.output_lines} lines ({stats.ratio:.0%} reduction)")


if __name__ == "__main__":
    main()
