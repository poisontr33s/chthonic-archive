#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: ssot_entity_inject.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
SSOT Entity Injection Tool
--------------------------
Finds an anchor string in the SSOT, then inserts content (from a file)
immediately after that anchor's line. Verifies injection on completion.

Usage:
  uv run scripts/ssot_entity_inject.py \\
    --anchor "UNIQUE_TEXT_IN_SSOT" \\
    --content-file path/to/content.md \\
    --verify "TEXT_TO_VERIFY_EXISTS_AFTER" \\
    [--ssot .github/copilot-instructions.archive.md] \\
    [--occurrence 1] \\
    [--dry-run]

Design notes:
  - Reads all files with UTF-8 encoding (handles apostrophes, em-dashes, etc.)
  - The --anchor string is matched literally (no regex) — must be unique in file
  - If anchor appears multiple times, use --occurrence N to select Nth match
  - Content file is inserted after the anchor line's newline, preceded by a blank line
  - Safe for any entity content block containing non-ASCII characters
  - Designed for chthonic-archive SSOT §10.3.xx entity injection workflow

@SID:           SSOT_ENTITY_INJECT_V1
@Shabti:        CLI Script
@Purpose:       SSOT Entity Injection Tool
"""


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# @SID: SSOT_ENTITY_INJECT_V1
# @SCOPE: SSOT injection utility — persistent, parameterized, reusable
# @VERSION: 1.0.0

import argparse
import pathlib
import sys


SSOT_DEFAULT = ".github/copilot-instructions.archive.md"


def find_nth(text: str, pattern: str, n: int) -> int:
    """Find the nth occurrence (1-indexed) of pattern in text. Returns -1 if not found."""
    start = 0
    for i in range(n):
        idx = text.find(pattern, start)
        if idx == -1:
            return -1
        if i < n - 1:
            start = idx + len(pattern)
        else:
            return idx
    return -1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inject content into the SSOT after an anchor line."
    )
    parser.add_argument(
        "--anchor",
        required=True,
        help="Exact string in SSOT to inject after (end of its line is the insertion point)",
    )
    parser.add_argument(
        "--content-file",
        required=True,
        help="Path to file containing the content to inject",
    )
    parser.add_argument(
        "--verify",
        help="String to check exists in SSOT after injection (confirms success)",
    )
    parser.add_argument(
        "--ssot",
        default=SSOT_DEFAULT,
        help=f"Path to SSOT file (default: {SSOT_DEFAULT})",
    )
    parser.add_argument(
        "--occurrence",
        type=int,
        default=1,
        help="Which occurrence of the anchor to use (1=first, 2=second, etc.)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be injected without writing to disk",
    )
    args = parser.parse_args()

    ssot_path = pathlib.Path(args.ssot)
    content_path = pathlib.Path(args.content_file)

    if not ssot_path.exists():
        print(f"ERROR: SSOT file not found: {ssot_path}", file=sys.stderr)
        sys.exit(1)
    if not content_path.exists():
        print(f"ERROR: Content file not found: {content_path}", file=sys.stderr)
        sys.exit(1)

    ssot_text = ssot_path.read_text(encoding="utf-8")
    inject_content = content_path.read_text(encoding="utf-8")

    # Count occurrences for diagnostics
    total_occurrences = ssot_text.count(args.anchor)
    if total_occurrences == 0:
        print(f"ERROR: Anchor not found in SSOT.", file=sys.stderr)
        print(f"       Anchor: {args.anchor!r}", file=sys.stderr)
        sys.exit(1)

    if args.occurrence > total_occurrences:
        print(
            f"ERROR: Requested occurrence {args.occurrence} but anchor only appears {total_occurrences} time(s).",
            file=sys.stderr,
        )
        sys.exit(1)

    if total_occurrences > 1:
        print(
            f"NOTE: Anchor appears {total_occurrences} times — using occurrence {args.occurrence}."
        )

    anchor_idx = find_nth(ssot_text, args.anchor, args.occurrence)
    line_end_idx = ssot_text.find("\n", anchor_idx + len(args.anchor))
    if line_end_idx == -1:
        line_end_idx = len(ssot_text)

    # Insertion point is immediately after the anchor's line
    insert_pos = line_end_idx + 1

    # Build injected text: blank line separator + content (stripped of trailing whitespace)
    inject_block = "\n" + inject_content.rstrip("\n") + "\n"

    new_text = ssot_text[:insert_pos] + inject_block + ssot_text[insert_pos:]

    if args.dry_run:
        print(f"[DRY RUN] Would inject {len(inject_content)} chars at char position {insert_pos}")
        print(f"          SSOT: {ssot_path}")
        print(f"          Content file: {content_path}")
        print(f"          Anchor occurrence: {args.occurrence} of {total_occurrences}")
        print()
        print("--- CONTEXT PREVIEW (±200 chars around injection point) ---")
        lo = max(0, insert_pos - 150)
        hi = min(len(new_text), insert_pos + len(inject_block) + 150)
        print(new_text[lo:hi])
        print("---")
        return

    # Write back
    ssot_path.write_text(new_text, encoding="utf-8")
    print(f"[INJECTED] {len(inject_content)} chars after anchor (occurrence {args.occurrence})")
    print(f"           {ssot_path}")

    # Verify
    if args.verify:
        verify_text = ssot_path.read_text(encoding="utf-8")
        count = verify_text.count(args.verify)
        if count == 0:
            print(f"[FAIL] Verify string not found after injection: {args.verify!r}", file=sys.stderr)
            sys.exit(1)
        print(f"[VERIFY] '{args.verify}' found {count} time(s) — PASS")

    new_line_count = new_text.count("\n")
    print(f"[LINES] SSOT now ~{new_line_count} lines")
    print("[DONE]")


if __name__ == "__main__":
    main()
