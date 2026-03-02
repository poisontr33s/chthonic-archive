#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: fix_md_links.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🛠️ THE FOUNDRY
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
MD Link Fixer (Orackla-Class)
Purpose: Identify and repair broken relative links in Markdown files.
Scan Mode: Recursive walk from root.
Repair Logic: Fuzzy filename match for broken paths.
Governance: Consumes ANKH lineage; does not define it.

@SID:           TOOL_FIX_MD_LINKS_V1
@Shabti:        CLI Script
@Purpose:       Script logic for fix_md_links.py.
"""

import os
import re
import sys
import argparse
from pathlib import Path
from collections import defaultdict

# RegEx for Markdown links: [label](path)
# Ignores http://, https://, mailto:, and absolute paths starting with /
LINK_PATTERN = re.compile(r'\[([^\]]+)\]\((?!http|https|mailto:|#)([^)]+)\)')

def build_file_index(root_dir):
    """
    Builds a dictionary mapping filenames to their list of relative paths.
    Returns: { 'filename.md': ['path/to/filename.md', 'other/path/filename.md'] }
    """
    index = defaultdict(list)
    for root, dirs, files in os.walk(root_dir):
        # Exclude hidden directories and known ignore targets
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'target', 'mas_mcp', 'error-classifier']]

        for file in files:
            full_path = Path(root) / file
            rel_path = full_path.relative_to(root_dir)
            index[file].append(rel_path)
    return index

def resolve_link(link_path, source_file, file_index, root_dir):
    """
    Attempts to resolve a broken link.
    1. Checks if exact path exists relative to source.
    2. Checks if exact path exists relative to root.
    3. Searches file_index for the filename.
    """
    # Clean link (remove anchors/queries)
    clean_link = link_path.split('#')[0].split('?')[0]
    if not clean_link:
        return None # Internal anchor only

    source_dir = source_file.parent

    # Check 1: Is it valid relative to current file?
    target_path = (source_dir / link_path).resolve()
    if target_path.exists():
        return None # Valid link

    # Check 2: Is it valid relative to root?
    root_target_path = (root_dir / link_path).resolve()
    if root_target_path.exists():
        # It's valid from root, but MD links usually expect relative.
        # If the user wrote 'docs/file.md' but is in 'src/', they might mean root.
        # We can suggest fixing it to be relative properly.
        return os.path.relpath(root_target_path, source_dir).replace('', '/')

    # Check 3: Search by filename
    target_name = Path(clean_link).name
    candidates = file_index.get(target_name)

    if not candidates:
        return False # Truly broken, no candidate found

    if len(candidates) == 1:
        # Unique match found!
        # Calculate relative path from source_dir to the candidate
        # We need to reconstruct the full path including original anchor/query if any
        suffix = ""
        if '#' in link_path: suffix = '#' + link_path.split('#')[1]
        elif '?' in link_path: suffix = '?' + link_path.split('?')[1]

        abs_candidate = root_dir / candidates[0]
        rel_fix = os.path.relpath(abs_candidate, source_dir).replace('', '/')
        return rel_fix + suffix

    return False # Ambiguous (multiple files with same name)

def process_file(file_path, file_index, root_dir, fix_mode=False):
    """
    Scans a single file for broken links.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        return []

    new_content = content
    changes = []

    def replacement(match):
        label = match.group(1)
        link = match.group(2)

        fix = resolve_link(link, file_path, file_index, root_dir)

        if fix is None:
            return match.group(0) # No change needed

        if fix is False:
            print(f"❌ Broken: '{link}' in {file_path}")
            return match.group(0) # Cannot fix automatically

        # We have a fix
        print(f"✅ Fix found: '{link}' -> '{fix}' in {file_path}")
        changes.append((link, fix))
        return f"[{label}]({fix})"

    if fix_mode:
        new_content = LINK_PATTERN.sub(replacement, content)
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
    else:
        # Just scan
        for match in LINK_PATTERN.finditer(content):
            replacement(match)

    return changes

def main():
    parser = argparse.ArgumentParser(description="Find and replace broken relative Markdown links.")
    parser.add_argument("--fix", action="store_true", help="Apply fixes to files.")
    parser.add_argument("--root", type=str, default=".", help="Root directory to scan.")
    args = parser.parse_args()

    root_dir = Path(args.root).resolve()
    print(f"🔍 Indexing files in {root_dir}...")
    file_index = build_file_index(root_dir)
    print(f"📂 Indexed {len(file_index)} unique filenames.")

    print("🚀 Scanning for broken links...")
    total_fixes = 0

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'target', 'mas_mcp', 'error-classifier']]
        for file in files:
            if file.endswith('.md'):
                file_path = Path(root) / file
                changes = process_file(file_path, file_index, root_dir, fix_mode=args.fix)
                total_fixes += len(changes)

    if args.fix:
        print(f"
✨ Completed. Fixed {total_fixes} links.")
    else:
        print(f"
ℹ️  Dry run complete. Found {total_fixes} fixable links. Use --fix to apply.")

if __name__ == "__main__":
    main()
