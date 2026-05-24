#!/usr/bin/env python3
#-*- coding: utf-8 -*-
# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: analyze.py
# ║ Python module: PatternStats, normalize_line, extract_patterns, suggest_regex, analyze_file, main
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: 🌿 THE GARDEN
# ║ Semantic ID: TOOL_PATTERN_ANALYZER_V1
# ║ Purpose: analyze.py - Pattern Frequency Analyzer for Markdown Files
# ║ Exports: PatternStats, normalize_line, extract_patterns, suggest_regex, analyze_file, main
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Cross-References (Bidirectional):
# ║ Dependents (Rely on me):
# ║   └─◄ scripts/lib/shared.py
# ╚════════════════════════════════════════════════════════════════════════════

#!/usr/bin/env python3
"""
analyze.py - Pattern Frequency Analyzer for Markdown Files

@SID:           TOOL_PATTERN_ANALYZER_V1
@Type:          CLI Tool
@Context:       Diagnostic / Tuning
@SessionOrigin: CONTINUATION_2026_01_27
@Implements:    ROADMAP_TOOL_CONSOLIDATION_2026_01_27
@Evolves:       _tmp_freq.py

Analyzes line pattern frequency in markdown files to identify noise candidates.
Used to tune NOISE_PATTERNS in compact.py and validate compression effectiveness.

Usage:
    chthonic analyze FILE.md                 # Show top 10 patterns
    chthonic analyze FILE.md --top 20        # Show top 20
    chthonic analyze FILE.md --min-freq 5    # Filter patterns appearing < 5 times
    chthonic analyze FILE.md --suggest       # Suggest new NOISE_PATTERNS
    chthonic analyze FILE.md --json          # Output as JSON
"""

from __future__ import annotations


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import argparse
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .shared import (
    configure_utf8_output,
    setup_logging,
    add_common_args,
    add_output_arg,
    print_json,
    print_table,
    handle_errors,
)

# Configure UTF-8 output
configure_utf8_output()


@dataclass
class PatternStats:
    """Statistics for a line pattern."""
    pattern: str
    count: int
    example_line: str
    suggested_regex: str = ""


def normalize_line(line: str) -> str:
    """Normalize line for pattern matching."""
    # Replace numbers with placeholder
    normalized = re.sub(r'\b\d+\b', 'N', line)
    # Replace file paths
    normalized = re.sub(r'file:///[^\s)]+', 'FILE_PATH', normalized)
    # Replace URLs
    normalized = re.sub(r'https?://[^\s)]+', 'URL', normalized)
    # Replace quoted strings
    normalized = re.sub(r'"[^"]+"', 'STRING', normalized)
    normalized = re.sub(r"'[^']+'", 'STRING', normalized)
    # Replace backtick code
    normalized = re.sub(r'`[^`]+`', 'CODE', normalized)
    return normalized.strip()


def extract_patterns(
    filepath: Path,
    min_length: int = 10,
    max_length: int = 150,
    logger=None
) -> list[PatternStats]:
    """Extract line patterns from markdown file."""
    line_patterns: dict[str, tuple[int, str]] = {}  # pattern -> (count, example)
    
    if logger:
        logger.info(f"Analyzing: {filepath}")
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.rstrip()
                
                # Skip empty lines and very short/long lines
                if not line or len(line) < min_length or len(line) > max_length:
                    continue
                
                # Normalize the line
                pattern = normalize_line(line)
                
                # Track pattern
                if pattern in line_patterns:
                    count, _ = line_patterns[pattern]
                    line_patterns[pattern] = (count + 1, line)
                else:
                    line_patterns[pattern] = (1, line)
    
    except Exception as e:
        if logger:
            logger.error(f"Error reading {filepath}: {e}")
        return []
    
    # Convert to PatternStats
    stats = [
        PatternStats(pattern=pattern, count=count, example_line=example[:100])
        for pattern, (count, example) in line_patterns.items()
    ]
    
    # Sort by frequency (descending)
    stats.sort(key=lambda s: s.count, reverse=True)
    
    return stats


def suggest_regex(pattern: str, example: str) -> str:
    """Suggest a regex pattern for matching this line type."""
    # Start with the normalized pattern
    regex = pattern
    
    # Replace placeholders with regex
    regex = regex.replace('N', r'\d+')
    regex = regex.replace('FILE_PATH', r'file:///[^\s)]+')
    regex = regex.replace('URL', r'https?://[^\s)]+')
    regex = regex.replace('STRING', r'"[^"]+"')
    regex = regex.replace('CODE', r'`[^`]+`')
    
    # Escape special regex chars
    for char in r'.()[]{}?*+|^$\\':
        if char not in r'\d+':  # Don't double-escape
            regex = regex.replace(char, '\\' + char)
    
    # Add anchors if pattern starts/ends cleanly
    if example.startswith(example.split()[0]):
        regex = '^' + regex
    
    return regex


def analyze_file(
    filepath: Path,
    top: int = 10,
    min_freq: int = 1,
    suggest_mode: bool = False,
    logger=None
) -> list[PatternStats]:
    """Analyze a markdown file for line patterns."""
    patterns = extract_patterns(filepath, logger=logger)
    
    # Filter by minimum frequency
    patterns = [p for p in patterns if p.count >= min_freq]
    
    # Limit to top N
    patterns = patterns[:top]
    
    # Generate regex suggestions if requested
    if suggest_mode:
        for p in patterns:
            p.suggested_regex = suggest_regex(p.pattern, p.example_line)
    
    if logger:
        logger.info(f"Found {len(patterns)} patterns (filtered by freq >= {min_freq}, top {top})")
    
    return patterns


@handle_errors
def main():
    parser = argparse.ArgumentParser(
        description="Analyze line pattern frequency in markdown files",
        prog="chthonic analyze"
    )
    parser.add_argument("input", type=Path, help="Markdown file to analyze")
    parser.add_argument("--top", type=int, default=10, help="Number of top patterns to show")
    parser.add_argument("--min-freq", type=int, default=2, help="Minimum frequency to include")
    parser.add_argument("--suggest", action="store_true", help="Suggest regex patterns for compact.py")
    
    add_common_args(parser)
    add_output_arg(parser, "Output file for results")
    
    args = parser.parse_args()
    logger = setup_logging(verbose=args.verbose, quiet=args.quiet)
    
    if not args.input.exists():
        logger.error(f"File not found: {args.input}")
        return
    
    patterns = analyze_file(
        args.input,
        top=args.top,
        min_freq=args.min_freq,
        suggest_mode=args.suggest,
        logger=logger
    )
    
    if args.dry_run:
        logger.info(f"[DRY RUN] Would analyze {args.input}")
        logger.info(f"Parameters: top={args.top}, min_freq={args.min_freq}, suggest={args.suggest}")
        return
    
    if args.json:
        output = {
            "file": str(args.input),
            "top": args.top,
            "min_freq": args.min_freq,
            "patterns": [
                {
                    "pattern": p.pattern,
                    "count": p.count,
                    "example": p.example_line,
                    **({"regex": p.suggested_regex} if args.suggest else {})
                }
                for p in patterns
            ]
        }
        
        if args.output:
            import json
            args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")
            logger.info(f"Written to {args.output}")
        else:
            print_json(output)
    else:
        # Table output
        title = f"\n=== Pattern Frequency Analysis: {args.input.name} ===\n"
        print(title)
        
        if args.suggest:
            headers = ["Count", "Pattern", "Suggested Regex"]
            rows = [
                [str(p.count), p.pattern[:50], p.suggested_regex[:60]]
                for p in patterns
            ]
        else:
            headers = ["Count", "Pattern", "Example"]
            rows = [
                [str(p.count), p.pattern[:50], p.example_line[:60]]
                for p in patterns
            ]
        
        print_table(rows, headers)
        
        if args.suggest:
            print("\n📋 Copy these to compact.py NOISE_PATTERNS:")
            print()
            for p in patterns:
                print(f'    re.compile(r"{p.suggested_regex}"),')
        
        print(f"\n✓ Analyzed {len(patterns)} patterns (min freq: {args.min_freq})")
        
        if args.output:
            lines = [title]
            lines.extend([f"{c}  {pat}  {ex}" for c, pat, ex in rows])
            args.output.write_text("\n".join(lines), encoding="utf-8")
            logger.info(f"Written to {args.output}")


if __name__ == "__main__":
    main()
