#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: apply_doc_fixes.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
@SID: TOOL_APPLY_DOC_FIXES
@Shabti: Utility Script
@Context: Documentation Validation / Automated Path Correction
@Implements: Bulk find-replace for fixable path references
@Purpose:       Script logic for apply_doc_fixes.py.
"""

from __future__ import annotations
import sys
from pathlib import Path
import json
import re

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Load categorized issues
issues_file = Path("docs/VALIDATION_CATEGORIZED.json")
with open(issues_file) as f:
    data = json.load(f)

fixable = data["fixable"]

print(f"\n{'='*60}")
print(f"APPLYING PATH CORRECTIONS")
print(f"{'='*60}\n")
print(f"Total fixable issues: {len(fixable)}\n")

# Group by document for efficient processing
by_doc = {}
for item in fixable:
    doc_name = item["Doc"]
    if doc_name not in by_doc:
        by_doc[doc_name] = []
    by_doc[doc_name].append(item)

# Apply fixes
docs_path = Path("docs")
fixed_count = 0
skipped_count = 0

for doc_name, items in sorted(by_doc.items()):
    doc_path = docs_path / doc_name

    if not doc_path.exists():
        print(f"⚠️  Skipping {doc_name} (file not found)")
        skipped_count += len(items)
        continue

    # Read content
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content
    changes = []

    # Apply each replacement
    for item in items:
        old_ref = item["Reference"]
        new_ref = item["Correction"]

        # Try multiple patterns to catch different contexts
        patterns = [
            # Markdown link
            (f"[{old_ref}]", f"[{new_ref}]"),
            # Inline code/path
            (f"`{old_ref}`", f"`{new_ref}`"),
            # Plain text reference
            (old_ref, new_ref),
        ]

        replaced = False
        for old_pattern, new_pattern in patterns:
            if old_pattern in content:
                content = content.replace(old_pattern, new_pattern)
                replaced = True
                break

        if replaced:
            changes.append(f"  {old_ref} → {new_ref}")
            fixed_count += 1
        else:
            print(f"  ⚠️  Pattern not found in {doc_name}: {old_ref}")
            skipped_count += 1

    # Write back if changes were made
    if content != original_content:
        with open(doc_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ {doc_name} ({len(changes)} fixes)")
        for change in changes[:3]:  # Show first 3
            print(change)
        if len(changes) > 3:
            print(f"  ... and {len(changes)-3} more")
        print()
    else:
        print(f"❌ {doc_name} (no changes applied)")

print(f"\n{'='*60}")
print(f"SUMMARY")
print(f"{'='*60}\n")
print(f"✅ Fixed: {fixed_count}")
print(f"⚠️  Skipped: {skipped_count}")
print(f"📁 Documents updated: {len([d for d in by_doc.keys() if (docs_path / d).exists()])}\n")
