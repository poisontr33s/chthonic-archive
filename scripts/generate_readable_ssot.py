#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: generate_readable_ssot.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
generate_readable_ssot.py — Script logic for generate_readable_ssot.py.

@SID:           TOOL_GENERATE_READABLE_SSOT_V1
@Shabti:        CLI Script
@Purpose:       Script logic for generate_readable_ssot.py.
"""

import re
import hashlib
import sys
from pathlib import Path

def calculate_hash(content):
    text = content.replace('\r\n', '\n').replace('\r', '\n')
    lines = [line.rstrip() for line in text.split('\n')]
    text = '\n'.join(lines).strip()
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def clean_slug(text):
    # Mimic GFM (GitHub Flavored Markdown) slugification
    s = text.lower()
    # Remove non-word, non-space, non-hyphen (removes punctuation, arrows, emojis)
    s = re.sub(r'[^\w\s-]', '', s)
    # Replace spaces with dashes
    s = s.replace(' ', '-')
    # Do NOT deduplicate dashes (GFM preserves them)
    s = s.strip('-')
    return s

def process_text(text):
    lines = text.split('\n')
    processed_lines = []
    toc = []

    # Track used slugs to ensure uniqueness
    used_slugs = {}

    in_code_block = False

    for line in lines:
        # Check for code block toggle
        # Assumes standard markdown ``` or ~~~
        if line.strip().startswith('```') or line.strip().startswith('~~~'):
            in_code_block = not in_code_block
            processed_lines.append(line)
            continue

        if in_code_block:
            # Pass through code blocks exactly as is, no decompression
            processed_lines.append(line)
            continue

        # 1. Decompression Logic (Only outside code blocks)
        new_line = line.replace('`', '')

        # Remove outer parens of dense syntax: (Key) -> Key
        new_line = re.sub(r'(?<!\])\(([^)]+)\)', r'\1', new_line)

        # Cleanup definitions
        new_line = new_line.replace(': =', ' =')
        new_line = new_line.replace('):', ':')

        # Cleanup bold/italic markers from headers/text for better readability?
        # The user complained about **T-DECOR** in the ToC.
        # Let's strip ** and __ only from HEADERS or everywhere?
        # "Lossless" implies keeping emphasis in body. But ToC should be clean.
        # We will strip them from the TITLE extracted, and maybe from the header line itself?
        # The user's prompt implies the readable projection should be "Readable". **Text** is readable, but in a header it's noisy.

        # 2. Escape non-link brackets to prevent "No link definition" errors
        def escape_brackets(match):
            return f"\\[{match.group(1)}\\]"

        new_line = re.sub(r'\[([^\]]+)\](?!\()', escape_brackets, new_line)

        # 3. Header Processing
        header_match = re.match(r'^(#+)\s+(.+)', new_line)
        if header_match:
            level = len(header_match.group(1))
            raw_title = header_match.group(2).strip()

            # Clean title for ToC and Header Display
            # Remove markdown bold/italic/code markers: **, *, __, _, `
            # Also replace arrows → with space
            clean_title = re.sub(r'[*_`]', '', raw_title)
            clean_title = clean_title.replace('→', ' ')
            # Cleanup multiple spaces
            clean_title = re.sub(r'\s+', ' ', clean_title).strip()

            # Generate slug for ToC from the CLEAN title
            slug = clean_slug(clean_title)

            # Handle duplicates
            if slug in used_slugs:
                count = used_slugs[slug]
                used_slugs[slug] += 1
                slug = f"{slug}-{count}"
            else:
                used_slugs[slug] = 1

            # Add to ToC (Using GFM-compatible slug)
            toc.append(f"{'  ' * (level-1)}- [{clean_title}](#{slug})")

            # Update the line to use the clean title
            new_line = f"{'#' * level} {clean_title}"

        processed_lines.append(new_line)

    return processed_lines, toc

def main():
    root = Path(__file__).parent.parent
    sys.path.insert(0, str(root))
    from scripts.lib.ssot_paths import resolve_ssot_paths
    _ssot = resolve_ssot_paths(root)
    ssot_path = _ssot.pointer
    out_path = root / '.github' / 'copilot-instructions.readable.md'

    if not ssot_path.exists():
        print(f"Error: {ssot_path} not found")
        sys.exit(1)

    content = ssot_path.read_text(encoding='utf-8')
    ssot_hash = calculate_hash(content)

    processed_lines, toc = process_text(content)

    output = []
    output.append("# CODEX BRAHMANICA PERFECTUS - READABLE PROJECTION")
    output.append(f"**Source Hash:** `{ssot_hash}`")
    output.append("**Auto-Generated by:** `uv run python scripts/generate_readable_ssot.py`")
    output.append("\n---\n")
    output.append("## TABLE OF CONTENTS")
    output.extend(toc)
    output.append("\n---\n")
    output.extend(processed_lines)
    output.append("\n---\n")
    output.append("**END OF AUTOMATED DECOMPRESSION**")
    output.append("**LOSSLESS DECOMPRESSION**")
    output.append("**⚓**")

    out_path.write_text('\n'.join(output), encoding='utf-8')
    print(f"Generated {out_path} with {len(output)} lines.")

if __name__ == '__main__':
    main()
