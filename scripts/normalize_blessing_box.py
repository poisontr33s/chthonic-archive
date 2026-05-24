#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: normalize_blessing_box.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
normalize_blessing_box.py - Strip right borders from Decorator's Blessing envelopes.

@SID:           TOOL_NORMALIZE_BLESSING_BOX_V1
@Shabti:          Hygiene / Batch Normalization
@Purpose:       normalize_blessing_box.py - Strip right borders from Decorator's Blessing envelopes.

Converts closed-box envelopes (with ╗╣╝ right borders) to open-sided canonical
format per STD_SCRIPT_METADATA_V2.

Usage:
    python scripts/normalize_blessing_box.py --dry-run    # Preview changes
    python scripts/normalize_blessing_box.py --apply      # Apply changes
"""


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import argparse
import os
import re
import sys
from pathlib import Path

# Comment prefix patterns that precede box drawing chars
COMMENT_PREFIXES = (
    "# ",    # Python, PowerShell, TOML, YAML
    "// ",   # TypeScript, Rust, JavaScript
    "/* ",   # CSS (unlikely but possible)
)

SKIP_DIRS = {
    "node_modules", "__pycache__", ".venv", "dist", "build",
    ".git", "target", "bun-playwright-poc", ".temple",
}

EXTENSIONS = {".py", ".ps1", ".ts", ".tsx", ".rs", ".js"}

# Regex patterns for closed-box line types
# Border lines: <prefix>╔═...═
RE_BORDER_CLOSED = re.compile(
    r"^(\s*(?://|#)\s*)"   # comment prefix (group 1)
    r"(╔═+)═╗\s*$"         # top border with ╗
    r"|"
    r"^(\s*(?://|#)\s*)"
    r"(╠═+)═╣\s*$"         # divider with ╣
    r"|"
    r"^(\s*(?://|#)\s*)"
    r"(╚═+)═╝\s*$"         # bottom border with ╝
)

# Content lines: <prefix>║  <content>  (trailing spaces or trailing ║)
# Two spaces after ║ in closed boxes → normalize to one space
RE_CONTENT_CLOSED = re.compile(
    r"^(\s*(?://|#)\s*║)  (.*)$"  # ║ + 2 spaces + content
)


def should_skip(path: Path) -> bool:
    """Check if path is in a skipped directory."""
    return any(part in SKIP_DIRS for part in path.parts)


def is_closed_box(text: str) -> bool:
    """Detect if file has a closed-box Decorator's Blessing envelope."""
    scan = text[:1500]
    if "╔═" not in scan:
        return False
    # Check for border caps (adjacent or with spaces): ═╗, ═ ╗, ═
    for cap in ("╗", "╣", "╝"):
        if cap in scan:
            return True
    # Check for content lines with right-border ║ (two ║ on same line, in comments)
    for line in scan.splitlines():
        ls = line.lstrip()
        if (ls.startswith("# ") or ls.startswith("// ")) and line.count("║") >= 2:
            return True
    return False


def normalize_line(line: str) -> str:
    """Normalize a single line from closed to open-sided format."""
    stripped = line.rstrip()

    # Only process comment lines (not runtime string literals)
    is_comment = False
    for prefix in ("# ", "// ", "/* "):
        if stripped.lstrip().startswith(prefix):
            is_comment = True
            break
    if not is_comment:
        return stripped

    # Border lines: strip right-cap character (possibly with spaces before it)
    # Patterns: ═╗ or ═ ╗ or ═
    for cap in ("╗", "╣", "╝"):
        if cap in stripped:
            idx = stripped.rfind(cap)
            before = stripped[:idx].rstrip()
            if before and before[-1] == "═":
                return before

    # Content lines: strip trailing ║ (right border) and normalize spacing
    # Pattern: # ║ ...content...  ║  →  # ║ content
    #          // ║ ...content... ║  →  // ║ content
    if "║" in stripped:
        # Strip trailing ║ and whitespace from content lines
        if stripped.rstrip().endswith("║"):
            # Count ║ occurrences — if ≥2, the last one is right border
            if stripped.count("║") >= 2:
                # Remove trailing ║ and whitespace before it
                idx = stripped.rstrip().rfind("║")
                stripped = stripped[:idx].rstrip()

        # Normalize double-space after left ║ to single space
        m = RE_CONTENT_CLOSED.match(stripped)
        if m:
            prefix = m.group(1)  # e.g. "# ║" or "// ║"
            content = m.group(2).rstrip()
            if content:
                return f"{prefix} {content}"
            return prefix

    return stripped


def process_file(filepath: Path, apply: bool) -> dict:
    """Process a single file. Returns stats dict."""
    text = filepath.read_text(encoding="utf-8", errors="replace")

    if not is_closed_box(text):
        return {"status": "skip", "reason": "not closed"}

    lines = text.splitlines()
    new_lines = []
    changes = 0
    in_envelope = False

    for line in lines:
        # Detect envelope region (from ╔ to ╚)
        if "╔═" in line:
            in_envelope = True
        if in_envelope:
            new_line = normalize_line(line)
            if new_line != line.rstrip():
                changes += 1
            new_lines.append(new_line)
            if "╚═" in line:
                in_envelope = False
        else:
            new_lines.append(line.rstrip() if line.rstrip() != line else line)

    if changes == 0:
        return {"status": "skip", "reason": "already open"}

    # Preserve original trailing newline
    new_text = "\n".join(new_lines)
    if text.endswith("\n"):
        new_text += "\n"

    if apply:
        filepath.write_text(new_text, encoding="utf-8")

    return {"status": "changed", "changes": changes}


def main():
    parser = argparse.ArgumentParser(
        description="Normalize Decorator's Blessing boxes to open-sided format."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    mode.add_argument("--apply", action="store_true", help="Apply changes to files")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show per-file details")
    args = parser.parse_args()

    root = Path(".")
    files_changed = 0
    files_skipped = 0
    files_already_open = 0
    total_line_changes = 0

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in sorted(filenames):
            filepath = Path(dirpath) / fn
            if filepath.suffix not in EXTENSIONS:
                continue

            try:
                text = filepath.read_text(encoding="utf-8", errors="replace")
            except (OSError, UnicodeDecodeError):
                continue

            if "╔═" not in text[:1500]:
                files_skipped += 1
                continue

            result = process_file(filepath, apply=args.apply)

            if result["status"] == "changed":
                files_changed += 1
                total_line_changes += result["changes"]
                if args.verbose or args.dry_run:
                    action = "WOULD CHANGE" if args.dry_run else "CHANGED"
                    print(f"  {action}: {filepath} ({result['changes']} lines)")
            elif result["status"] == "skip":
                if result["reason"] == "already open":
                    files_already_open += 1
                else:
                    files_skipped += 1

    print(f"\n{'DRY RUN' if args.dry_run else 'APPLIED'} Summary:")
    print(f"  Files normalized:   {files_changed}")
    print(f"  Lines changed:      {total_line_changes}")
    print(f"  Already open-sided: {files_already_open}")
    print(f"  No envelope:        {files_skipped}")


if __name__ == "__main__":
    main()
