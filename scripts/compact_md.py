#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: compact_md.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
compact_md.py - Markdown Template-Based Compactor

@SID:           TOOL_COMPACT_MD_V1
@Shabti:          Script
@Context:       Hygiene / Content Compression
@Purpose:       compact_md.py - Markdown Template-Based Compactor

Condenses large .md files using template-based rules.
Preserves structured data (tables, @SID headers, decisions).
Strips noise (tool calls, terminal output, status lines).
Overwrites in-place (State File pattern).

Usage:
    uv run scripts/compact_md.py FILE.md                  # Compact in-place
    uv run scripts/compact_md.py FILE.md --dry-run         # Preview without writing
    uv run scripts/compact_md.py FILE.md --stats           # Show compression stats only
    uv run scripts/compact_md.py DIR/ --batch              # Compact all .md in directory
    uv run scripts/compact_md.py FILE.md --json            # Output stats as JSON
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Force UTF-8 output on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Section priority rules
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
    re.compile(r'^Ran terminal command:'),
    re.compile(r'^\s*"query"\s*:'),
    re.compile(r'^\}$'),  # lone closing brace (from JSON input blocks)
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
    re.compile(r'^\w+\.\w+\+\d+-\d+$'),  # file diff notation like "package.json+2-1"
    # Copilot Pro+ specific patterns
    re.compile(r'^Searched for (?:text|regex) `'),          # inline code search results
    re.compile(r'^Searched \S+ for '),                       # GitHub repo search
    re.compile(r'^Read \[]\(file:///'),                      # file read notifications
    re.compile(r'^Replacing \d+ lines with \d+ lines in'),  # patch with file ref
    re.compile(r'^Fetched \d+ resources?$'),                 # batch fetch
    re.compile(r'^Terminal (?:seems|is) (?:unresponsive|stuck|back)'),
    re.compile(r'^GitHub Copilot:\s*$'),                     # bare agent prefix
    re.compile(r'^GitHub Copilot:\s*(?:Read|Searched|Fetched|Created)'),
    re.compile(r'^Ran terminal command:'),                   # already covered but explicit
    re.compile(r'^It\'s capturing|^Good progress'),          # filler narration
    re.compile(r'^The crawler is (?:still )?running'),
    re.compile(r'^Terminal is back\.'),
    re.compile(r'^Replacing \d+ lines?$'),                   # bare patch stat
    re.compile(r'^warn:\s+'),                                # package manager warnings
    re.compile(r'^create mode \d+'),                         # git output
    re.compile(r'^PS (?:C:\\|/|~)'),                         # PowerShell prompts
    re.compile(r'^\(\d+/\d+\)'),                             # progress counters
    re.compile(r'^GitHub Copilot: Let me'),                  # chatty transitions
    # Additional file operation variants
    re.compile(r'^Created \[.*\]\(file:'),                   # Created with text
    re.compile(r'^Read \[.*\]\(file:'),                      # Read with text
    re.compile(r'^\[\]\(file:///'),                          # Empty file links []
    # More transition phrases
    re.compile(r'^Now implementing'),
    re.compile(r"^Now I'm "),
    re.compile(r'^Now I have (?:enough )?context'),
    re.compile(r'^Also update '),
    re.compile(r'^Also (?:add|fix|check) '),
    # Box drawing characters and decorative noise
    re.compile(r'^[\u2551\u2503\u2502\u2523\u2503]+\s*[\u2551\u2503\u2502]*\s*$'),  # ║ ┃ │ etc
    re.compile(r'^[-=_]{6,}$'),                              # Long separator lines
    re.compile(r'^[\u2193\u2191\u2192\u2190\u21B3↓]+\s*$'),  # Bare arrow lines
    re.compile(r'^\^+\s*$'),                                 # Bare caret markers
    re.compile(r'^\|+\s*$'),                                 # Bare pipe (table fragment)
    # Section/definition list markers from SSOT docs
    re.compile(r'^- §\d+\.\d+:\s+'),                         # e.g., "- §0.76: T-DECOR"
    re.compile(r'^- [A-Z]{2,}:\s+'),                         # e.g., "- NBF: Nascent"
    # High-frequency patterns from analysis
    re.compile(r'^Replacing \d+ lines?(?:\s+with \d+ lines?)?$'),  # Not followed by "in [file]"
    re.compile(r'^Searched for (?:regex|text) '),
    re.compile(r'^warn: (?:incorrect peer dependency|deprecated|SKIPPING OPTIONAL)'),
    re.compile(r'^create mode \d{6}'),
    re.compile(r'^PS [A-Z]:\\'),
    re.compile(r'^\[?\d{1,2}:\d{2}:\d{2}(?:\s+[AP]M)?\]?\s*$'),  # Bare timestamps
    # Test output noise
    re.compile(r'^\s+at <anonymous>'),                       # Stack traces
    re.compile(r'^\s+at .*\(.*:\d+:\d+\)$'),                # Stack trace lines
    re.compile(r'^error: expect\('),                         # Test failures
    re.compile(r'^SyntaxError:'),                            # Parser errors
    re.compile(r'^\s*\^$'),                                  # Error pointer lines
    re.compile(r'^\s+Expected (?:to )?(?:not )?'),          # Expect messages
    re.compile(r'^\s+Received:'),                            # Test diffs
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
    re.compile(r"^#{1,6}\s"),                # headings
    re.compile(r"^\|.*\|.*\|"),              # table rows
    re.compile(r"^[-*]\s+\[[ x]]\s"),        # task lists
    re.compile(r"^\*\*Verdict"),
    re.compile(r"^\*\*Key "),
    re.compile(r"^\*\*Summary"),
]

# Consecutive runs of these are collapsed to a single instance
COLLAPSE_PATTERNS: list[re.Pattern] = [
    re.compile(r"^```\s*$"),                 # empty code fences
    re.compile(r"^\s*$"),                    # blank lines (max 2 consecutive)
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
        return False  # blank lines handled separately
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
                # End of code block — decide whether to keep
                in_code_block = False
                # Keep if it has meaningful content (not just commands/noise)
                meaningful = [
                    cl for cl in code_block_lines
                    if cl.strip() and not is_noise(cl)
                ]
                if meaningful:
                    output.append(f"```{code_block_lang}")
                    # Limit long code blocks to 20 lines + truncation note
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

        # Blank line collapsing (max 1 consecutive)
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

        # Always keep
        if is_keep(line):
            if stripped.startswith("#"):
                stats.sections_found += 1
            output.append(line)
            i += 1
            continue

        # Remove noise
        if is_noise(line):
            stats.noise_removed += 1
            i += 1
            continue

        # Default: keep the line
        output.append(line)
        i += 1

    # Strip trailing blanks
    while output and not output[-1].strip():
        output.pop()
    output.append("")  # single trailing newline

    stats.output_lines = len(output)
    return output, stats


def compact_file(path: Path) -> tuple[str, CompactStats]:
    """Read and compact a single .md file."""
    content = path.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()
    output_lines, stats = compact_lines(lines)
    return "\n".join(output_lines), stats


def main():
    parser = argparse.ArgumentParser(
        description="Template-based markdown compactor (State File pattern)."
    )
    parser.add_argument(
        "target", type=Path,
        help="Markdown file or directory (with --batch)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview compacted output without writing"
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
        "--json", action="store_true",
        help="Output stats as JSON"
    )
    parser.add_argument(
        "--min-lines", type=int, default=100,
        help="Skip files shorter than this (batch mode, default: 100)"
    )

    args = parser.parse_args()

    if args.batch:
        if not args.target.is_dir():
            print(f"Error: {args.target} is not a directory", file=sys.stderr)
            sys.exit(1)
        files = sorted(args.target.glob("**/*.md"))
        results = []
        for f in files:
            line_count = sum(1 for _ in open(f, encoding="utf-8", errors="ignore"))
            if line_count < args.min_lines:
                continue
            output, stats = compact_file(f)
            results.append({"file": str(f), "stats": stats})
            if not args.dry_run and not args.stats:
                f.write_text(output, encoding="utf-8")
                print(f"  Compacted: {f} ({stats.original_lines} -> {stats.output_lines}, {stats.ratio:.0%} reduction)")
            elif args.stats or args.dry_run:
                print(f"  {f}: {stats.original_lines} -> {stats.output_lines} ({stats.ratio:.0%})")

        if args.json:
            print(json.dumps([
                {"file": r["file"], "original": r["stats"].original_lines,
                 "output": r["stats"].output_lines, "ratio": round(r["stats"].ratio, 3)}
                for r in results
            ], indent=2))
        return

    # Single file mode
    if not args.target.is_file():
        print(f"Error: {args.target} not found", file=sys.stderr)
        sys.exit(1)

    output, stats = compact_file(args.target)

    if args.json:
        print(json.dumps({
            "file": str(args.target),
            "original_lines": stats.original_lines,
            "output_lines": stats.output_lines,
            "ratio": round(stats.ratio, 3),
            "noise_removed": stats.noise_removed,
            "blanks_collapsed": stats.blanks_collapsed,
            "code_blocks_trimmed": stats.code_blocks_trimmed,
            "sections_found": stats.sections_found,
        }, indent=2))
        return

    if args.stats:
        print(f"File:             {args.target}")
        print(f"Original lines:   {stats.original_lines}")
        print(f"Output lines:     {stats.output_lines}")
        print(f"Reduction:        {stats.ratio:.0%}")
        print(f"Noise removed:    {stats.noise_removed}")
        print(f"Blanks collapsed: {stats.blanks_collapsed}")
        print(f"Code blocks trim: {stats.code_blocks_trimmed}")
        print(f"Sections found:   {stats.sections_found}")
        return

    if args.dry_run:
        print(f"[DRY RUN] {args.target}: {stats.original_lines} -> {stats.output_lines} ({stats.ratio:.0%} reduction)")
        print(f"[DRY RUN] First 50 lines of output:")
        print("-" * 60)
        for line in output.split("\n")[:50]:
            print(line)
        print("-" * 60)
        print(f"... ({stats.output_lines} total lines)")
        return

    # Write in-place
    args.target.write_text(output, encoding="utf-8")
    print(f"Compacted: {args.target}")
    print(f"  {stats.original_lines} -> {stats.output_lines} lines ({stats.ratio:.0%} reduction)")


if __name__ == "__main__":
    main()
