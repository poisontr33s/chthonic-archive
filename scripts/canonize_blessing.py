#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: canonize_blessing.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ .codex/skills/script-envelope/scripts/script_envelope.py
# ╚════════════════════════════════════════════════════════════════════════════

"""
canonize_blessing.py — Batch-canonize Decorator's Blessing envelopes to
the Wedjat-Quipu / Temple-Ayllu / Ogdoad-Ceque format.

Handles three cases:
  1. Scripts with NO blessing → inject canon envelope
  2. Scripts with OLD-format blessing → replace with canon envelope
  3. Scripts with CANON-format blessing → preserve (skip)

Also fixes:
  - Duplicate shebangs (sometimes left after old injection)
  - Missing blank line between coding line and envelope
  - Docstring ordering (envelope always before docstring)

@SID:           TOOL_CANONIZE_BLESSING_V1
@Shabti:        CLI Script
@Purpose:       Normalize all script envelopes to Wedjat-Quipu canon format.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════
#  CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

SHEBANG = "#!/usr/bin/env python3"
CODING = "#-*- coding: utf-8 -*-"
BORDER_LEN = 76
TOP = f"# ╔{'═' * BORDER_LEN}"
MID = f"# ╠{'═' * BORDER_LEN}"
BOT = f"# ╚{'═' * BORDER_LEN}"

SCRIPTS_DIR = Path("scripts")

# Known zone+spectrum overrides for specific scripts
ZONE_OVERRIDES: dict[str, tuple[str, str]] = {
    # (spectrum, zone) — manually classified non-default scripts
    "genre_extractor.py":       ("RED",   "🔥 THE FOUNDRY"),
    "local_refiner_v2.py":      ("RED",   "🔥 THE FOUNDRY"),
    "sfs_reference_index.py":   ("BLUE",  "🔥 THE FOUNDRY"),
    "ankh_theme_reference.py":  ("GOLD",  "🛠️ THE FOUNDRY"),
    "product_icon_census.py":   ("WHITE", "🔭 THE OBSERVATORY"),
    "theme_token_coverage.py":  ("WHITE", "🔭 THE OBSERVATORY"),
    "theme_color_diversity.py": ("WHITE", "🔥 THE FOUNDRY"),
    "theme_promote_master.py":  ("WHITE", "🔥 THE FOUNDRY"),
    "theme_contrast_audit.py":  ("WHITE", "🔥 THE FOUNDRY"),
    "theme_artcop.py":          ("WHITE", "🔥 THE FOUNDRY"),
    "theme_parity.py":          ("WHITE", "🔥 THE FOUNDRY"),
    "theme_scaffold.py":        ("WHITE", "🔥 THE FOUNDRY"),
    "theme_sfs_transmute.py":   ("WHITE", "🔥 THE FOUNDRY"),
}

# SID construction: derive from filename if missing
def _derive_sid(filename: str) -> str:
    stem = Path(filename).stem.upper()
    return f"TOOL_{stem}_V1"


def _derive_shabti(text: str) -> str:
    """Extract @Shabti or @Type from docstring."""
    m = re.search(r"@Shabti:\s*(.+)", text)
    if m:
        return m.group(1).strip()
    m = re.search(r"@Type:\s*(.+)", text)
    if m:
        return m.group(1).strip()
    return "CLI Script"


def _derive_purpose(text: str, filename: str) -> str:
    """Extract purpose from docstring first line or @Purpose tag."""
    m = re.search(r"@Purpose:\s*(.+)", text)
    if m:
        return m.group(1).strip()
    # Try first sentence of module docstring
    try:
        tree = ast.parse(text)
        doc = ast.get_docstring(tree)
        if doc:
            first = doc.split("\n")[0].strip()
            # Skip lines that are just the filename
            if first and first != filename and not first.startswith("@"):
                return first
    except SyntaxError:
        pass
    return f"Script logic for {filename}."


def _extract_radiance(text: str) -> str:
    """Extract Ogdoad-Ceque Radiance from existing envelope."""
    m = re.search(r"└─◄\s*(.+)", text)
    if m:
        return m.group(1).strip()
    # Check Cross-References for dependency info
    m = re.search(r"Cross-References.*?└─◄\s*(.+)", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return "(Standalone)"


def _extract_spectrum_zone(text: str, filename: str,
                           filepath: Path | None = None) -> tuple[str, str]:
    """Extract or derive Spectrum and Zone."""
    # Check overrides first
    if filename in ZONE_OVERRIDES:
        return ZONE_OVERRIDES[filename]

    # Try existing canon fields
    m = re.search(r"Wedjat-Quipu Spectrum:\s*(\w+)", text)
    if m:
        spectrum = m.group(1).strip()
        zm = re.search(r"Temple-Ayllu Zone:\s*(.+)", text)
        zone = zm.group(1).strip() if zm else "🌿 THE GARDEN"
        return spectrum, zone

    # Try old-format fields
    m = re.search(r"Spectral Frequency:\s*(\w+)", text)
    if m:
        spectrum = m.group(1).strip()
        zm = re.search(r"Architectural Role:\s*(.+)", text)
        zone = zm.group(1).strip() if zm else "🌿 THE GARDEN"
        return spectrum, zone

    # Directory-based zone defaults for non-scripts/ files
    if filepath is not None:
        parts = set(filepath.parts)
        fp_str = str(filepath).replace("\\", "/")
        if "ankh_atlas" in parts:
            return "WHITE", "🔭 THE OBSERVATORY"
        if "mas_mcp" in parts:
            if "lib" in parts or "logic" in parts:
                return "WHITE", "🏰 THE FORTRESS"
            if "scripts" in parts:
                return "WHITE", "🌿 THE GARDEN"
            return "WHITE", "🏰 THE FORTRESS"
        if ".codex" in parts or ".temple" in parts:
            return "WHITE", "🔥 THE FOUNDRY"

    # Default for .py
    return "WHITE", "🌿 THE GARDEN"


def _extract_sid(text: str, filename: str) -> str:
    m = re.search(r"@SID:\s+(\S+)", text)
    return m.group(1).strip() if m else _derive_sid(filename)


# ═══════════════════════════════════════════════════════════════════════════
#  ENVELOPE CONSTRUCTION
# ═══════════════════════════════════════════════════════════════════════════

def build_canon_envelope(filename: str, spectrum: str, zone: str,
                         radiance: str) -> list[str]:
    """Build the canon Decorator's Blessing envelope lines."""
    return [
        TOP,
        f"# ║ THE DECORATOR'S BLESSING: {filename}",
        MID,
        f"# ║ Wedjat-Quipu Spectrum: {spectrum}",
        f"# ║ Temple-Ayllu Zone: {zone}",
        f"# ║ Ogdoad-Ceque Radiance:",
        f"# ║   └─◄ {radiance}",
        BOT,
    ]


# ═══════════════════════════════════════════════════════════════════════════
#  ENVELOPE DETECTION & STRIPPING
# ═══════════════════════════════════════════════════════════════════════════

def _is_envelope_line(line: str) -> bool:
    """Check if a line belongs to a Decorator's Blessing envelope."""
    s = line.rstrip()
    if s.startswith("# ╔") or s.startswith("# ╠") or s.startswith("# ╚"):
        return True
    if s.startswith("# ║"):
        return True
    # Broken bottom border variant (missing ╚, using extra spaces)
    if s.startswith("#  ═══"):
        return True
    return False


def strip_envelope(lines: list[str]) -> tuple[list[str], bool]:
    """
    Remove any existing Decorator's Blessing envelope block from lines.
    Returns (remaining_lines, had_envelope).
    """
    # Find envelope boundaries
    start = None
    end = None
    for i, line in enumerate(lines):
        s = line.rstrip()
        if s.startswith("# ╔") and "═" in s:
            if start is None:
                start = i
        if start is not None and i >= start:
            if s.startswith("# ╚") and "═" in s:
                end = i
                break
            # Also detect broken bottom: line after last ║ that's a border
            if s.startswith("#  ═══"):
                end = i
                break

    if start is None:
        return lines, False

    # If no explicit bottom found, scan to end of ║ block
    if end is None:
        end = start
        for i in range(start + 1, len(lines)):
            s = lines[i].rstrip()
            if _is_envelope_line(s):
                end = i
            else:
                break

    remaining = lines[:start] + lines[end + 1:]
    return remaining, True


# ═══════════════════════════════════════════════════════════════════════════
#  DOCSTRING EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════

def _find_docstring_range(lines: list[str]) -> tuple[int, int] | None:
    """Find the module-level docstring line range (triple-quote block)."""
    start = None
    for i, line in enumerate(lines):
        s = line.rstrip()
        # Skip shebangs, coding, blank lines
        if s.startswith("#") or s == "":
            continue
        # Found first non-comment, non-blank line
        if s.startswith('"""') or s.startswith("'''"):
            start = i
            quote = s[:3]
            # Single-line docstring
            if s.count(quote) >= 2 and len(s) > 3:
                return (i, i)
            # Multi-line: find closing
            for j in range(i + 1, len(lines)):
                if quote in lines[j]:
                    return (i, j)
        break
    return None


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN CANONIZATION LOGIC
# ═══════════════════════════════════════════════════════════════════════════

def canonize_file(filepath: Path, dry_run: bool = True) -> dict:
    """
    Canonize a single Python script's Decorator's Blessing envelope.

    Returns a status dict with keys: status, changes, details.
    """
    text = filepath.read_text(encoding="utf-8", errors="replace")
    filename = filepath.name
    original = text

    # Check if already in canon format
    if "Wedjat-Quipu Spectrum:" in text and "Temple-Ayllu Zone:" in text:
        if "Ogdoad-Ceque Radiance:" in text:
            return {"status": "already-canon", "changes": 0, "details": ""}

    lines = text.splitlines()

    # ── Step 1: Extract metadata from existing content ──
    spectrum, zone = _extract_spectrum_zone(text, filename, filepath)
    radiance = _extract_radiance(text)
    sid = _extract_sid(text, filename)
    shabti = _derive_shabti(text)
    purpose = _derive_purpose(text, filename)

    # ── Step 2: Strip existing envelope (old or partial) ──
    lines, had_envelope = strip_envelope(lines)

    # ── Step 3: Remove duplicate shebangs ──
    # After stripping envelope, there might be dup shebangs
    shebang_count = 0
    cleaned = []
    for line in lines:
        s = line.rstrip()
        if s == SHEBANG:
            shebang_count += 1
            if shebang_count > 1:
                continue  # skip duplicate
        cleaned.append(line)
    lines = cleaned

    # ── Step 4: Ensure canonical header (shebang + coding) ──
    # Strip any existing shebangs/coding from top, then re-add canonical
    body_start = 0
    for i, line in enumerate(lines):
        s = line.rstrip()
        if s.startswith("#!") or s.startswith("#-*-") or s.startswith("# -*-") or s == "":
            body_start = i + 1
        else:
            break
    body_lines = lines[body_start:]

    # ── Step 5: Find and separate docstring ──
    # The docstring should come AFTER the envelope, not before
    doc_range = _find_docstring_range(body_lines)
    if doc_range:
        ds, de = doc_range
        docstring_lines = body_lines[ds:de + 1]
        rest_lines = body_lines[:ds] + body_lines[de + 1:]
    else:
        docstring_lines = []
        rest_lines = body_lines

    # ── Step 6: Build canon envelope ──
    envelope = build_canon_envelope(filename, spectrum, zone, radiance)

    # ── Step 7: Build docstring if missing ──
    if not docstring_lines:
        docstring_lines = [
            '"""',
            f"{filename} — {purpose}",
            "",
            f"@SID:           {sid}",
            f"@Shabti:        {shabti}",
            f"@Purpose:       {purpose}",
            '"""',
        ]
    else:
        # Ensure docstring has @SID if missing
        doc_text = "\n".join(docstring_lines)
        if "@SID:" not in doc_text:
            # Insert @SID before closing quotes
            insert_lines = [
                f"@SID:           {sid}",
                f"@Shabti:        {shabti}",
                f"@Purpose:       {purpose}",
            ]
            # Find closing triple-quote
            for idx in range(len(docstring_lines) - 1, -1, -1):
                if '"""' in docstring_lines[idx] or "'''" in docstring_lines[idx]:
                    # Insert before close
                    close = docstring_lines[idx]
                    docstring_lines = (
                        docstring_lines[:idx]
                        + [""]
                        + insert_lines
                        + [close]
                    )
                    break

    # ── Step 8: Reassemble ──
    # Remove leading blank lines from rest_lines
    while rest_lines and rest_lines[0].rstrip() == "":
        rest_lines.pop(0)

    final_lines = [
        SHEBANG,
        CODING,
        "",  # blank line after coding
    ]
    final_lines.extend(envelope)
    final_lines.append("")  # blank line after envelope
    final_lines.extend(docstring_lines)
    if rest_lines:
        # Ensure blank line between docstring and code
        if rest_lines[0].rstrip() != "":
            final_lines.append("")
        final_lines.extend(rest_lines)

    # Ensure trailing newline
    result = "\n".join(final_lines)
    if not result.endswith("\n"):
        result += "\n"

    if result == original:
        return {"status": "no-change", "changes": 0, "details": ""}

    changes = []
    if not had_envelope:
        changes.append("added envelope")
    else:
        changes.append("replaced envelope")
    if shebang_count > 1:
        changes.append(f"removed {shebang_count - 1} dup shebang(s)")

    if not dry_run:
        filepath.write_text(result, encoding="utf-8")

    return {
        "status": "changed",
        "changes": len(changes),
        "details": ", ".join(changes),
    }


# ═══════════════════════════════════════════════════════════════════════════
#  IDENTITY BLOCK CANONIZATION (Layer 2)
# ═══════════════════════════════════════════════════════════════════════════
#
#  Rules:
#    @Type → @Shabti  (rename)
#    @SessionOrigin   → strip (provenance noise)
#    @ReferencedBy    → strip (envelope Radiance handles this)
#    @Spectrum/@Zone  → strip from docstring (envelope dupes)
#    @Context         → keep (useful metadata)
#    @Implements      → keep (cross-reference)
#    @Backend/@Emits/@Related → keep (rare, specific)
#    @Heka-Ayni etc.  → keep (non-standard extensions)
#    Ensure canon trio: @SID / @Shabti / @Purpose

# Fields to strip entirely from docstrings
_STRIP_FIELDS = {"@SessionOrigin", "@ReferencedBy", "@Spectrum", "@Zone"}

# Old SEMANTIC IDENTITY banner lines to strip
_BANNER_RE = re.compile(
    r"^={10,}$"
    r"|^SEMANTIC IDENTITY"
    r"|^Anchor & Signal Protocol",
    re.IGNORECASE,
)


def canonize_identity(filepath: Path, dry_run: bool = True) -> dict:
    """
    Canonize the docstring @-field identity block of a Python script.

    Returns a status dict with keys: status, changes, details.
    """
    text = filepath.read_text(encoding="utf-8", errors="replace")
    filename = filepath.name
    lines = text.splitlines()

    # Find the module-level docstring boundaries
    doc_start = None
    doc_end = None
    quote_char = None
    for i, line in enumerate(lines):
        s = line.rstrip()
        # Skip shebangs, coding, blank lines, envelope
        if s.startswith("#") or s == "":
            continue
        if s.startswith('"""') or s.startswith("'''"):
            doc_start = i
            quote_char = s[:3]
            # Single-line docstring
            if s.count(quote_char) >= 2 and len(s) > 3:
                doc_end = i
                break
            for j in range(i + 1, len(lines)):
                if quote_char in lines[j]:
                    doc_end = j
                    break
            break
        # Non-docstring code before any docstring
        break

    if doc_start is None or doc_end is None:
        return {"status": "no-docstring", "changes": 0, "details": ""}

    # Extract docstring lines (between the triple quotes)
    doc_lines = lines[doc_start:doc_end + 1]
    original_doc = "\n".join(doc_lines)

    # Work on the inner lines (between opening and closing quotes)
    # Opening line
    open_line = doc_lines[0]
    close_line = doc_lines[-1] if len(doc_lines) > 1 else None
    if len(doc_lines) <= 1:
        # Single-line docstring — nothing to canonize
        return {"status": "no-change", "changes": 0, "details": ""}

    inner = doc_lines[1:-1]  # lines between """ and """
    changes = []

    # Pass 1: Rename @Type → @Shabti
    new_inner = []
    for line in inner:
        m = re.match(r"^(\s*)@Type:(\s+)(.*)", line)
        if m:
            indent, space, value = m.group(1), m.group(2), m.group(3)
            # Align @Shabti to same column width as other fields
            new_inner.append(f"{indent}@Shabti:{space}{value}")
            changes.append("@Type→@Shabti")
        else:
            new_inner.append(line)
    inner = new_inner

    # Pass 2: Strip deprecated fields and banner lines
    new_inner = []
    stripped = set()
    for line in inner:
        s = line.strip()
        # Strip deprecated @-fields
        skip = False
        for field in _STRIP_FIELDS:
            if s.startswith(f"{field[1:]}:") or s.startswith(field + ":"):
                # Match both "SessionOrigin:" and "@SessionOrigin:"
                stripped.add(field)
                skip = True
                break
            # Also match without @ prefix (sometimes written as plain "SessionOrigin:")
            bare = field[1:]  # remove @
            if re.match(rf"^@?{re.escape(bare)}:", s):
                stripped.add(field)
                skip = True
                break
        if skip:
            continue
        # Strip old SEMANTIC IDENTITY banners
        if _BANNER_RE.match(s):
            if "stripped-banner" not in changes:
                changes.append("stripped-banner")
            continue
        new_inner.append(line)
    if stripped:
        changes.append(f"stripped {','.join(sorted(stripped))}")
    inner = new_inner

    # Pass 3: Clean up consecutive blank lines left by stripping
    cleaned = []
    prev_blank = False
    for line in inner:
        is_blank = line.strip() == ""
        if is_blank and prev_blank:
            continue
        cleaned.append(line)
        prev_blank = is_blank
    # Strip leading/trailing blanks from inner
    while cleaned and cleaned[0].strip() == "":
        cleaned.pop(0)
    while cleaned and cleaned[-1].strip() == "":
        cleaned.pop()
    inner = cleaned

    # Pass 4: Ensure canon trio present (@SID, @Shabti, @Purpose)
    inner_text = "\n".join(inner)
    missing_trio = []
    if "@SID:" not in inner_text:
        sid = _extract_sid(text, filename)
        missing_trio.append(f"@SID:           {sid}")
    if "@Shabti:" not in inner_text:
        shabti = _derive_shabti(text)
        missing_trio.append(f"@Shabti:        {shabti}")
    if "@Purpose:" not in inner_text:
        purpose = _derive_purpose(text, filename)
        missing_trio.append(f"@Purpose:       {purpose}")

    if missing_trio:
        # Find where to insert: after last existing @-field, or before close
        insert_idx = len(inner)
        for idx in range(len(inner) - 1, -1, -1):
            if re.match(r"^\s*@\w", inner[idx]):
                insert_idx = idx + 1
                # Skip continuation lines (indented more than the @-field)
                while insert_idx < len(inner):
                    next_s = inner[insert_idx]
                    if next_s.strip() == "" or re.match(r"^\s*@\w", next_s):
                        break
                    # Check if it's a continuation (more indented)
                    if next_s.startswith("    ") and not next_s.strip().startswith("@"):
                        insert_idx += 1
                    else:
                        break
                break
        for m_line in missing_trio:
            inner.insert(insert_idx, m_line)
            insert_idx += 1
        changes.append(f"added {','.join(f.split(':')[0] for f in missing_trio)}")

    if not changes:
        return {"status": "no-change", "changes": 0, "details": ""}

    # Reassemble docstring
    new_doc_lines = [open_line] + inner + [close_line]
    new_doc = "\n".join(new_doc_lines)

    if new_doc == original_doc:
        return {"status": "no-change", "changes": 0, "details": ""}

    # Reassemble full file
    result_lines = lines[:doc_start] + new_doc_lines + lines[doc_end + 1:]
    result = "\n".join(result_lines)
    if not result.endswith("\n"):
        result += "\n"

    if not dry_run:
        filepath.write_text(result, encoding="utf-8")

    return {
        "status": "changed",
        "changes": len(changes),
        "details": ", ".join(changes),
    }


# ═══════════════════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════════════════

# Paths/names to skip in recursive mode
_SKIP_DIRS = {".venv", "__pycache__", "site-packages", ".system", "node_modules"}
_SKIP_NAMES = {"__init__.py", "__main__.py"}


def _should_skip(filepath: Path) -> bool:
    """Return True if this file should be skipped."""
    if filepath.name.startswith("_"):
        return True
    if filepath.name in _SKIP_NAMES:
        return True
    if filepath.name.startswith("test_"):
        return True
    if any(part in _SKIP_DIRS for part in filepath.parts):
        return True
    return False


def _run_envelope(args, files) -> int:
    """Run envelope canonization (Layer 1)."""
    dry_run = args.dry_run
    stats = {"already-canon": 0, "changed": 0, "no-change": 0, "error": 0, "skipped": 0}

    for filepath in files:
        if _should_skip(filepath):
            stats["skipped"] += 1
            continue
        try:
            result = canonize_file(filepath, dry_run=dry_run)
            status = result["status"]
            stats[status] = stats.get(status, 0) + 1
            if args.verbose or status == "changed":
                marker = "✅" if status == "changed" else ("⏭️" if status == "already-canon" else "·")
                detail = f" ({result['details']})" if result["details"] else ""
                print(f"  {marker} {filepath.name}: {status}{detail}")
        except Exception as e:
            stats["error"] += 1
            print(f"  ❌ {filepath.name}: ERROR — {e}", file=sys.stderr)

    processed = len(files) - stats["skipped"]
    mode_label = "DRY RUN" if dry_run else "APPLIED"
    print(f"\n{'═' * 60}")
    print(f"  CANONIZE BLESSING — {mode_label}")
    print(f"{'═' * 60}")
    print(f"  ✅ Changed:       {stats['changed']}")
    print(f"  ⏭️  Already canon: {stats['already-canon']}")
    print(f"  ·  No change:     {stats['no-change']}")
    print(f"  ❌ Errors:        {stats['error']}")
    print(f"  📁 Processed:     {processed} ({stats['skipped']} skipped)")
    print()
    return 0


def _run_identity(args, files) -> int:
    """Run docstring identity canonization (Layer 2)."""
    dry_run = args.dry_run
    stats = {"changed": 0, "no-change": 0, "no-docstring": 0, "error": 0, "skipped": 0}

    for filepath in files:
        if _should_skip(filepath):
            stats["skipped"] += 1
            continue
        try:
            result = canonize_identity(filepath, dry_run=dry_run)
            status = result["status"]
            stats[status] = stats.get(status, 0) + 1
            if args.verbose or status == "changed":
                marker = "✅" if status == "changed" else ("·" if status == "no-change" else "⏭️")
                detail = f" ({result['details']})" if result["details"] else ""
                print(f"  {marker} {filepath.name}: {status}{detail}")
        except Exception as e:
            stats["error"] += 1
            print(f"  ❌ {filepath.name}: ERROR — {e}", file=sys.stderr)

    processed = len(files) - stats["skipped"]
    mode_label = "DRY RUN" if dry_run else "APPLIED"
    print(f"\n{'═' * 60}")
    print(f"  CANONIZE IDENTITY — {mode_label}")
    print(f"{'═' * 60}")
    print(f"  ✅ Changed:       {stats['changed']}")
    print(f"  ·  No change:     {stats['no-change']}")
    print(f"  ⏭️  No docstring:  {stats['no-docstring']}")
    print(f"  ❌ Errors:        {stats['error']}")
    print(f"  📁 Processed:     {processed} ({stats['skipped']} skipped)")
    print()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Canonize Decorator's Blessing envelopes and identity blocks."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true",
                      help="Preview changes without writing")
    mode.add_argument("--apply", action="store_true",
                      help="Apply changes to files")
    parser.add_argument("--identity", action="store_true",
                        help="Canonize docstring @-fields (Layer 2) instead of envelope (Layer 1)")
    parser.add_argument("--target", type=Path, default=SCRIPTS_DIR,
                        help="Target directory (default: scripts/)")
    parser.add_argument("--recursive", action="store_true",
                        help="Recursively scan subdirectories (rglob)")
    parser.add_argument("--file", type=Path, default=None,
                        help="Process a single file instead of a directory")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Show per-file details")
    args = parser.parse_args()

    if args.file:
        files = [args.file]
    else:
        glob_fn = args.target.rglob if args.recursive else args.target.glob
        files = sorted(glob_fn("*.py"))

    if args.identity:
        return _run_identity(args, files)
    return _run_envelope(args, files)


if __name__ == "__main__":
    raise SystemExit(main())
