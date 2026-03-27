#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""
Envelope Census — KCP header compliance auditor and stamper.

Scans .py, .ps1, .ts, and .rs files for Khipu-Cartouche Protocol (KCP)
compliance. Audits both Stratum 1 (Cartouche: Spectrum, Zone, Radiance)
and Stratum 2 (Khipu: @SID, @Shabti, @Purpose), reports field
completeness, and can batch-stamp full KCP headers on bare or missing files.

Per-language encapsulation follows KCP_PROTOCOL_ONTOLOGY.md:
  Python:  Cartouche in # comments, Khipu in docstring
  PS1:     Cartouche in # comments, Khipu in <# .NOTES #>
  TS:      Cartouche in // comments, Khipu in /** JSDoc */
  Rust:    Cartouche in // comments, Khipu in //! inner docs

@SID:           TOOL_ENVELOPE_CENSUS_V1
@Shabti:        Guardian
@Purpose:       Audit and enforce KCP header compliance across executable
                files. Supports bare @SID stamps (legacy), full KCP
                generation, and upgrade from bare to full KCP.

Usage:
    uv run scripts/envelope_census.py                       # full census report
    uv run scripts/envelope_census.py --json                 # JSON output
    uv run scripts/envelope_census.py --ext .ps1             # filter by extension
    uv run scripts/envelope_census.py --missing-only         # only show files without @SID
    uv run scripts/envelope_census.py --summary              # counts only
    uv run scripts/envelope_census.py --kcp-audit            # KCP field completeness audit
    uv run scripts/envelope_census.py --stamp                # bare @SID stamp (legacy)
    uv run scripts/envelope_census.py --kcp-stamp            # full KCP header stamp
    uv run scripts/envelope_census.py --kcp-stamp --dry-run  # preview KCP stamps
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from scripts.lib.shared import configure_utf8_output, find_repo_root, setup_logging

# Directories to skip during scanning
SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    "target",
    "build",
    "dist",
    ".venv",
    "venv",
    "NUL",
}

# Extensions to scan
SCANNABLE_EXTENSIONS = {".py", ".ps1", ".ts", ".rs"}

# Pattern to match @SID lines (e.g. @SID: TOOL_LINK_AUDIT_V1)
SID_PATTERN = re.compile(r"@SID:\s*(\S+)")


def scan_file(path: Path) -> dict:
    """Check a single file for @SID presence and KCP field coverage."""
    result = {
        "file": str(path),
        "extension": path.suffix,
        "has_sid": False,
        "sid": None,
        "kcp_fields": {},
        "kcp_tier": "NONE",
    }
    try:
        # Only read the first 60 lines — KCP header should be there
        with path.open("r", encoding="utf-8", errors="replace") as f:
            header_lines = []
            for i, line in enumerate(f):
                if i >= 60:
                    break
                header_lines.append(line)
                m = SID_PATTERN.search(line)
                if m and not result["has_sid"]:
                    result["has_sid"] = True
                    result["sid"] = m.group(1)
        # Audit KCP fields
        fields = {k: False for k in KCP_FIELD_PATTERNS}
        for line in header_lines:
            for field_name, pattern in KCP_FIELD_PATTERNS.items():
                if not fields[field_name] and pattern.search(line):
                    fields[field_name] = True
        result["kcp_fields"] = fields
        result["kcp_tier"] = kcp_tier(fields)
    except OSError:
        result["error"] = "unreadable"
    return result


def collect_files(repo_root: Path, extensions: set[str]) -> list[Path]:
    """Walk the repo tree collecting scannable files, pruning skipped dirs."""
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(repo_root):
        # Prune skipped directories in-place so os.walk doesn't descend
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            p = Path(dirpath) / fname
            if p.suffix in extensions:
                files.append(p)
    return sorted(files)


def run_census(
    repo_root: Path,
    extensions: set[str],
    missing_only: bool = False,
) -> list[dict]:
    """Run the census and return results."""
    files = collect_files(repo_root, extensions)
    results = []
    for f in files:
        rel = f.relative_to(repo_root)
        entry = scan_file(f)
        entry["file"] = str(rel).replace("\\", "/")
        if missing_only and entry["has_sid"]:
            continue
        results.append(entry)
    return results


def print_report(results: list[dict], summary_only: bool = False) -> None:
    """Print a human-readable census report."""
    total = len(results)
    compliant = sum(1 for r in results if r["has_sid"])
    missing = total - compliant

    if not summary_only:
        # Group by extension
        by_ext: dict[str, list[dict]] = {}
        for r in results:
            by_ext.setdefault(r["extension"], []).append(r)

        for ext in sorted(by_ext):
            group = by_ext[ext]
            ext_compliant = sum(1 for r in group if r["has_sid"])
            ext_total = len(group)
            print(f"\n{'=' * 60}")
            print(f"  {ext} files: {ext_compliant}/{ext_total} compliant")
            print(f"{'=' * 60}")
            for r in group:
                status = f"✅ {r['sid']}" if r["has_sid"] else "❌ MISSING"
                print(f"  {status:30s}  {r['file']}")

    print(f"\n{'─' * 60}")
    print(f"  TOTAL: {compliant}/{total} files have @SID headers")
    pct = (compliant / total * 100) if total > 0 else 0
    print(f"  COMPLIANCE: {pct:.0f}%")
    print(f"  MISSING: {missing}")
    print(f"{'─' * 60}")


# Directories to exclude from batch-stamping (archived/vendored content)
STAMP_EXCLUDE_DIRS = {
    "dumpster-dive/intake",
    ".venv",
    ".vscode-test",
    ".venv-py314-parked",
    ".next/",
    ".chthonic/cache/",
    "media/wasm/pkg/",
    "copilot-cli-0.0.406/",
}

# Filename patterns to exclude from batch-stamping (generated type defs)
STAMP_EXCLUDE_FILES = {
    "vscode.d.ts",
    "next-env.d.ts",
}

# ════════════════════════════════════════════════════════════════════════════
# KCP INFERENCE MAPS — directory context → metadata field values
# Reference: docs/standards/KCP_PROTOCOL_ONTOLOGY.md §4.1-4.3
# ════════════════════════════════════════════════════════════════════════════

# Directory prefix → (Spectrum, Zone, Shabti)
# Matched in order — first match wins (most specific first)
KCP_CONTEXT_MAP: list[tuple[str, str, str, str]] = [
    # (path_prefix, spectrum, zone, shabti)
    # Hooks and enforcement
    ("scripts/hooks/", "WHITE", "⚔️ THE PYLONS", "Automation Script"),
    (".claude/hooks/", "WHITE", "⚔️ THE PYLONS", "Automation Script"),
    # Agent skills
    (".claude/skills/", "BLUE", "🏛️ THE HYPOSTYLE", "Config"),
    (".codex/skills/", "BLUE", "🏛️ THE HYPOSTYLE", "Config"),
    (".gemini/", "BLUE", "🏛️ THE HYPOSTYLE", "Config"),
    # Standards and templates
    ("docs/standards/templates/", "WHITE", "📜 THE SCRIPTORIUM", "Standard"),
    ("docs/standards/", "WHITE", "📜 THE SCRIPTORIUM", "Standard"),
    ("docs/", "WHITE", "📜 THE SCRIPTORIUM", "Standard"),
    # VS Code extension source
    ("extensions/chthonic-archive/scripts/", "ORANGE", "🔥 THE FOUNDRY", "Automation Script"),
    ("extensions/chthonic-archive/src/entropy/", "BLACK", "🕳️ THE NAOS", "Extension Module"),
    ("extensions/chthonic-archive/src/monolith/", "ORANGE", "🏛️ THE HYPOSTYLE", "Extension Module"),
    ("extensions/chthonic-archive/src/polyglot/", "ORANGE", "🏛️ THE HYPOSTYLE", "Extension Module"),
    ("extensions/chthonic-archive/src/reactor/", "ORANGE", "🏛️ THE HYPOSTYLE", "Extension Module"),
    ("extensions/chthonic-archive/src/acp/", "ORANGE", "🏛️ THE HYPOSTYLE", "Extension Module"),
    ("extensions/chthonic-archive/src/sdk/", "ORANGE", "🏛️ THE HYPOSTYLE", "Extension Module"),
    ("extensions/chthonic-archive/src/", "ORANGE", "🏛️ THE HYPOSTYLE", "Extension Module"),
    ("extensions/", "ORANGE", "🏛️ THE HYPOSTYLE", "Extension Module"),
    # MAS MCP
    ("mas_mcp/tests/", "WHITE", "⚔️ THE PYLONS", "CLI Script"),
    ("mas_mcp/logic/", "WHITE", "🏛️ THE HYPOSTYLE", "Library Module"),
    ("mas_mcp/frontend/pages/api/", "ORANGE", "🔭 THE OBSERVATORY", "Router"),
    ("mas_mcp/frontend/lib/", "ORANGE", "🏛️ THE HYPOSTYLE", "Library Module"),
    ("mas_mcp/frontend/", "ORANGE", "🔭 THE OBSERVATORY", "Extension Module"),
    ("mas_mcp/", "WHITE", "🏛️ THE HYPOSTYLE", "Library Module"),
    # Forge pipeline
    ("dumpster-dive/forge/anvil/", "GOLD", "🔥 THE FOUNDRY", "CLI Script"),
    ("dumpster-dive/forge/", "GOLD", "🔥 THE FOUNDRY", "CLI Script"),
    # Chthonic golden
    ("chthonic-golden/", "GOLD", "🔭 THE OBSERVATORY", "CLI Script"),
    # Scripts
    ("scripts/lib/", "WHITE", "🏛️ THE HYPOSTYLE", "Library Module"),
    ("scripts/", "WHITE", "🌿 THE GARDEN", "CLI Script"),
    # Meta-IDE / Copilot SDK
    ("meta-ide/copilot-sdk/shims/", "GREEN", "🏛️ THE HYPOSTYLE", "Library Module"),
    ("meta-ide/copilot-sdk/", "BLUE", "🔭 THE OBSERVATORY", "CLI Script"),
    ("meta-ide/", "BLUE", "🔭 THE OBSERVATORY", "CLI Script"),
    # Bun-playwright POC
    ("bun-playwright-poc/src/", "ORANGE", "🏛️ THE HYPOSTYLE", "Library Module"),
    ("bun-playwright-poc/scripts/", "ORANGE", "🌿 THE GARDEN", "Automation Script"),
    ("bun-playwright-poc/tests/", "ORANGE", "⚔️ THE PYLONS", "CLI Script"),
    ("bun-playwright-poc/", "ORANGE", "🌿 THE GARDEN", "CLI Script"),
    # Error classifier
    ("error-classifier/", "WHITE", "🔭 THE OBSERVATORY", "Library Module"),
    # Ankh atlas
    ("ankh_atlas/", "GOLD", "🏛️ THE HYPOSTYLE", "Library Module"),
    # Tools
    ("tools/", "WHITE", "🌿 THE GARDEN", "CLI Script"),
    # Apps
    ("apps/", "ORANGE", "🏛️ THE HYPOSTYLE", "Extension Module"),
    # Chthonic VSCode extension (legacy)
    ("chthonic-vscode-extension/", "ORANGE", "🏛️ THE HYPOSTYLE", "Extension Module"),
    # Config files at root
    ("", "WHITE", "🌿 THE GARDEN", "CLI Script"),
]


def infer_kcp_context(file_path: str) -> tuple[str, str, str]:
    """Infer (Spectrum, Zone, Shabti) from file path using KCP_CONTEXT_MAP."""
    for prefix, spectrum, zone, shabti in KCP_CONTEXT_MAP:
        if not prefix or file_path.startswith(prefix):
            return spectrum, zone, shabti
    return "WHITE", "🌿 THE GARDEN", "CLI Script"


def humanize_stem(stem: str) -> str:
    """Convert a filename stem to a readable purpose string.

    Examples:
        'ssot_hash' → 'SSOT hash'
        'pre-commit-guardian' → 'Pre-commit guardian'
        'entropyWorker' → 'Entropy worker'
    """
    # Split camelCase
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", stem)
    # Replace separators
    s = s.replace("-", " ").replace("_", " ")
    # Collapse whitespace
    s = " ".join(s.split())
    # Uppercase known acronyms
    acronyms = {"ssot", "kcp", "mcp", "sid", "cli", "api", "gpu", "ui", "cdp", "hf", "ide"}
    words = s.split()
    result = []
    for i, w in enumerate(words):
        if w.lower() in acronyms:
            result.append(w.upper())
        elif i == 0:
            result.append(w.capitalize())
        else:
            result.append(w.lower())
    return " ".join(result)


# ════════════════════════════════════════════════════════════════════════════
# KCP HEADER GENERATORS — per-language Cartouche + Khipu construction
# ════════════════════════════════════════════════════════════════════════════

CARTOUCHE_WIDTH = 76  # chars of ═ after ╔/╠/╚ (fits in 80-col with comment prefix)


def build_cartouche(filename: str, spectrum: str, zone: str,
                    radiance: str, comment_prefix: str) -> list[str]:
    """Build Stratum 1 Cartouche lines with the given comment prefix."""
    border = "═" * CARTOUCHE_WIDTH
    p = comment_prefix
    lines = [
        f"{p} ╔{border}\n",
        f"{p} ║ THE DECORATOR'S BLESSING: {filename}\n",
        f"{p} ╠{border}\n",
        f"{p} ║ Wedjat-Quipu Spectrum: {spectrum}\n",
        f"{p} ║ Temple-Ayllu Zone: {zone}\n",
        f"{p} ║ Ogdoad-Ceque Radiance:\n",
        f"{p} ║   └─◄ {radiance}\n",
        f"{p} ╚{border}\n",
    ]
    return lines


def build_kcp_header_python(
    filename: str, sid: str, spectrum: str, zone: str,
    shabti: str, purpose: str, radiance: str = "(Standalone)",
) -> str:
    """Build a full KCP header for a Python file."""
    cartouche = build_cartouche(filename, spectrum, zone, radiance, "#")
    lines = [
        "#!/usr/bin/env python3\n",
        "#-*- coding: utf-8 -*-\n",
        "\n",
    ]
    lines.extend(cartouche)
    lines.append("\n")
    lines.append(f'"""\n')
    lines.append(f"{filename} — {purpose}\n")
    lines.append(f"\n")
    lines.append(f"@SID:           {sid}\n")
    lines.append(f"@Shabti:        {shabti}\n")
    lines.append(f"@Purpose:       {purpose}\n")
    lines.append(f'"""\n')
    return "".join(lines)


def build_kcp_header_ps1(
    filename: str, sid: str, spectrum: str, zone: str,
    shabti: str, purpose: str, radiance: str = "(Standalone)",
) -> str:
    """Build a full KCP header for a PowerShell file."""
    cartouche = build_cartouche(filename, spectrum, zone, radiance, "#")
    lines = [
        "#!/usr/bin/env pwsh\n",
        "\n",
    ]
    lines.extend(cartouche)
    lines.append("\n")
    lines.append("<#\n")
    lines.append(".SYNOPSIS\n")
    lines.append(f"    {purpose}\n")
    lines.append("\n")
    lines.append(".NOTES\n")
    lines.append(f"@SID:           {sid}\n")
    lines.append(f"@Shabti:        {shabti}\n")
    lines.append(f"@Purpose:       {purpose}\n")
    lines.append("#>\n")
    return "".join(lines)


def build_kcp_header_ts(
    filename: str, sid: str, spectrum: str, zone: str,
    shabti: str, purpose: str, radiance: str = "(Standalone)",
) -> str:
    """Build a full KCP header for a TypeScript file."""
    cartouche = build_cartouche(filename, spectrum, zone, radiance, "//")
    lines = []
    lines.extend(cartouche)
    lines.append("\n")
    lines.append("/**\n")
    lines.append(f" * {filename} — {purpose}\n")
    lines.append(f" *\n")
    lines.append(f" * @SID           {sid}\n")
    lines.append(f" * @Shabti        {shabti}\n")
    lines.append(f" * @Purpose       {purpose}\n")
    lines.append(f" */\n")
    return "".join(lines)


def build_kcp_header_rs(
    filename: str, sid: str, spectrum: str, zone: str,
    shabti: str, purpose: str, radiance: str = "(Standalone)",
) -> str:
    """Build a full KCP header for a Rust file."""
    cartouche = build_cartouche(filename, spectrum, zone, radiance, "//")
    lines = []
    lines.extend(cartouche)
    lines.append("\n")
    lines.append(f"//! {filename} — {purpose}\n")
    lines.append(f"//!\n")
    lines.append(f"//! @SID:           {sid}\n")
    lines.append(f"//! @Shabti:        {shabti}\n")
    lines.append(f"//! @Purpose:       {purpose}\n")
    return "".join(lines)


def build_kcp_header(
    file_path: str, sid: str, ext: str,
    spectrum: str, zone: str, shabti: str,
    radiance: str = "(Standalone)",
) -> str:
    """Build a full KCP header for any supported file type."""
    filename = Path(file_path).name
    purpose = humanize_stem(Path(file_path).stem)
    builders = {
        ".py": build_kcp_header_python,
        ".ps1": build_kcp_header_ps1,
        ".ts": build_kcp_header_ts,
        ".rs": build_kcp_header_rs,
    }
    builder = builders.get(ext)
    if not builder:
        return ""
    return builder(filename, sid, spectrum, zone, shabti, purpose, radiance)


# ════════════════════════════════════════════════════════════════════════════
# KCP COMPLIANCE AUDIT — field-level completeness beyond bare @SID
# ════════════════════════════════════════════════════════════════════════════

# Patterns for detecting KCP fields in source files
KCP_FIELD_PATTERNS = {
    "sid": re.compile(r"@SID[: ]"),
    "shabti": re.compile(r"@Shabti[: ]"),
    "purpose": re.compile(r"@Purpose[: ]"),
    "heka_ayni": re.compile(r"@Heka-Ayni[: ]"),
    "ankh_tinku": re.compile(r"@Ankh-Tinku[: ]"),
    "cartouche": re.compile(r"THE DECORATOR'S BLESSING:"),
    "spectrum": re.compile(r"Wedjat-Quipu Spectrum:"),
    "zone": re.compile(r"Temple-Ayllu Zone:"),
    "radiance": re.compile(r"Ogdoad-Ceque Radiance:"),
}


def audit_kcp_fields(path: Path) -> dict[str, bool]:
    """Audit a file for KCP field presence. Returns field→present map."""
    fields = {k: False for k in KCP_FIELD_PATTERNS}
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f):
                if i >= 60:  # KCP header should be in first 60 lines
                    break
                for field_name, pattern in KCP_FIELD_PATTERNS.items():
                    if not fields[field_name] and pattern.search(line):
                        fields[field_name] = True
    except OSError:
        pass
    return fields


def kcp_tier(fields: dict[str, bool]) -> str:
    """Classify KCP compliance tier from field presence."""
    required_khipu = fields.get("sid", False) and fields.get("shabti", False) and fields.get("purpose", False)
    has_cartouche = fields.get("cartouche", False)
    has_spectrum = fields.get("spectrum", False)
    has_zone = fields.get("zone", False)
    optional_count = sum(1 for f in ("heka_ayni", "ankh_tinku") if fields.get(f, False))

    if has_cartouche and has_spectrum and has_zone and required_khipu and optional_count == 2:
        return "FULL"      # All fields present
    if has_cartouche and has_spectrum and required_khipu:
        return "STANDARD"  # Both strata, missing optionals
    if required_khipu:
        return "KHIPU"     # Stratum 2 only
    if fields.get("sid", False):
        return "BARE"      # @SID only
    return "NONE"          # No KCP


TIER_ICONS = {
    "FULL": "🏅",
    "STANDARD": "✅",
    "KHIPU": "🔶",
    "BARE": "⚠️",
    "NONE": "❌",
}


def print_kcp_audit(results: list[dict]) -> None:
    """Print a KCP field completeness audit report."""
    print(f"\n{'═' * 70}")
    print(f"  KCP COMPLIANCE AUDIT — Khipu-Cartouche Protocol Field Completeness")
    print(f"{'═' * 70}")
    print(f"  Tiers: 🏅 FULL | ✅ STANDARD | 🔶 KHIPU-only | ⚠️  BARE @SID | ❌ NONE")
    print(f"{'─' * 70}")

    tier_counts: dict[str, int] = {"FULL": 0, "STANDARD": 0, "KHIPU": 0, "BARE": 0, "NONE": 0}

    by_ext: dict[str, list[dict]] = {}
    for r in results:
        by_ext.setdefault(r["extension"], []).append(r)

    for ext in sorted(by_ext):
        group = by_ext[ext]
        print(f"\n  {ext} ({len(group)} files):")
        for r in group:
            tier = r.get("kcp_tier", "NONE")
            icon = TIER_ICONS.get(tier, "?")
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
            fields = r.get("kcp_fields", {})
            field_marks = "".join(
                "█" if fields.get(f, False) else "░"
                for f in ("cartouche", "spectrum", "zone", "radiance", "sid", "shabti", "purpose", "heka_ayni", "ankh_tinku")
            )
            print(f"    {icon} {tier:8s} [{field_marks}] {r['file']}")

    total = sum(tier_counts.values())
    print(f"\n{'─' * 70}")
    print(f"  FIELD KEY: C=Cartouche S=Spectrum Z=Zone R=Radiance | @SID @Shabti @Purpose @Heka @Ankh")
    print(f"{'─' * 70}")
    print(f"  TIER SUMMARY:")
    for tier_name in ("FULL", "STANDARD", "KHIPU", "BARE", "NONE"):
        count = tier_counts.get(tier_name, 0)
        pct = (count / total * 100) if total else 0
        icon = TIER_ICONS.get(tier_name, "?")
        print(f"    {icon} {tier_name:10s}: {count:4d} ({pct:5.1f}%)")
    print(f"{'─' * 70}")
    full_or_std = tier_counts.get("FULL", 0) + tier_counts.get("STANDARD", 0)
    pct = (full_or_std / total * 100) if total else 0
    print(f"  KCP COMPLIANT (FULL+STANDARD): {full_or_std}/{total} ({pct:.0f}%)")
    print(f"{'═' * 70}")

# SID prefix map based on directory context
SID_PREFIX_MAP = [
    ("scripts/hooks/", "HOOK"),
    (".claude/hooks/", "AGENT_HOOK"),
    (".claude/skills/", "SKILL"),
    (".codex/skills/", "SKILL"),
    (".gemini/", "SKILL"),
    (".github/tools/", "TOOL"),
    ("scripts/", "SCRIPT"),
    ("extensions/", "EXT"),
    ("chthonic-golden/", "GOLDEN"),
    ("chthonic-vscode-extension/", "EXT"),
    ("mas_mcp/", "MAS"),
    ("dumpster-dive/forge/", "FORGE"),
    ("dumpster-dive/", "DUMPSTER"),
]


def generate_sid(file_path: str) -> str:
    """Generate a canonical @SID from a file path."""
    # Determine prefix
    prefix = "SCRIPT"
    for path_prefix, sid_prefix in SID_PREFIX_MAP:
        if file_path.startswith(path_prefix):
            prefix = sid_prefix
            break

    # Extract stem, normalize
    stem = Path(file_path).stem
    sid_name = stem.replace("-", "_").replace(".", "_").upper()
    return f"{prefix}_{sid_name}_V1"


def find_insertion_line(lines: list[str], ext: str) -> int:
    """Find the line index where @SID should be inserted."""
    if not lines:
        return 0

    # For PS1/Python: insert after shebang line if present
    first = lines[0].strip()
    if ext in (".ps1", ".py") and first.startswith("#!"):
        # Check if next line is coding declaration
        if len(lines) > 1 and lines[1].strip().startswith("#-*-"):
            return 2
        return 1

    # For TS: insert at line 0
    return 0


def build_sid_comment(sid: str, ext: str) -> str:
    """Build a @SID comment line for the given extension."""
    if ext == ".ts":
        return f"// @SID: {sid}\n"
    else:
        return f"# @SID: {sid}\n"


def stamp_files(
    repo_root: Path,
    results: list[dict],
    dry_run: bool = False,
) -> list[dict]:
    """Stamp @SID headers on files that don't have one. Returns actions taken."""
    actions = []
    for r in results:
        if r["has_sid"]:
            continue

        file_path = r["file"]

        # Skip excluded directories
        if any(excl in file_path for excl in STAMP_EXCLUDE_DIRS):
            continue

        # Skip excluded filenames
        fname = Path(file_path).name
        if fname in STAMP_EXCLUDE_FILES:
            continue

        sid = generate_sid(file_path)
        full_path = repo_root / file_path

        try:
            lines = full_path.read_text(encoding="utf-8", errors="replace").splitlines(True)
        except OSError:
            actions.append({"file": file_path, "sid": sid, "status": "error", "reason": "unreadable"})
            continue

        insert_at = find_insertion_line(lines, r["extension"])
        comment = build_sid_comment(sid, r["extension"])

        action = {"file": file_path, "sid": sid, "insert_line": insert_at + 1, "status": "stamped"}

        if not dry_run:
            lines.insert(insert_at, comment)
            full_path.write_text("".join(lines), encoding="utf-8")

        actions.append(action)

    return actions


# Patterns that indicate a file already has a partial/full KCP header beyond bare @SID
BARE_SID_PATTERN = re.compile(r"^(#|//) @SID: \S+\s*$")


def detect_bare_sid_line(lines: list[str]) -> int | None:
    """Find the line index of a bare @SID comment (not in docstring/JSDoc/.NOTES).

    Returns the line index if found, None otherwise.
    """
    for i, line in enumerate(lines[:20]):
        if BARE_SID_PATTERN.match(line.strip()):
            return i
    return None


def kcp_stamp_files(
    repo_root: Path,
    results: list[dict],
    dry_run: bool = False,
) -> list[dict]:
    """Stamp full KCP headers (Cartouche + Khipu) on files.

    Handles three cases:
    1. No header at all → insert full KCP header
    2. Bare @SID only → replace bare line with full KCP header
    3. Already has Cartouche (STANDARD or FULL) → skip
    """
    actions = []
    for r in results:
        file_path = r["file"]
        ext = r["extension"]
        tier = r.get("kcp_tier", "NONE")

        # Skip files that already have proper KCP (Cartouche present)
        if tier in ("FULL", "STANDARD"):
            continue

        # Skip excluded directories
        if any(excl in file_path for excl in STAMP_EXCLUDE_DIRS):
            continue

        # Skip excluded filenames
        fname = Path(file_path).name
        if fname in STAMP_EXCLUDE_FILES:
            continue

        # Generate metadata
        sid = r.get("sid") or generate_sid(file_path)
        spectrum, zone, shabti = infer_kcp_context(file_path)
        full_path = repo_root / file_path

        try:
            content = full_path.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines(True)
        except OSError:
            actions.append({"file": file_path, "sid": sid, "status": "error",
                            "reason": "unreadable", "tier": tier})
            continue

        kcp_header = build_kcp_header(file_path, sid, ext, spectrum, zone, shabti)
        if not kcp_header:
            continue

        action = {
            "file": file_path, "sid": sid, "status": "kcp_stamped",
            "tier_before": tier, "spectrum": spectrum, "zone": zone, "shabti": shabti,
        }

        if tier == "BARE":
            # Remove the bare @SID line before inserting full header
            bare_idx = detect_bare_sid_line(lines)
            if bare_idx is not None:
                lines.pop(bare_idx)

        # Find where to insert the KCP header
        # For files with existing shebang, we need to handle carefully
        insert_at = 0
        if lines:
            first_line = lines[0].strip() if lines else ""
            # If file already has shebang and KCP header includes one, skip the existing
            if first_line.startswith("#!") and ext in (".py", ".ps1"):
                # KCP header generators include shebang — remove existing one
                lines.pop(0)
                # Also remove coding declaration if present (Python)
                if ext == ".py" and lines and lines[0].strip().startswith("#-*-"):
                    lines.pop(0)
                # Remove blank line after shebang/coding
                while lines and lines[0].strip() == "":
                    lines.pop(0)
            elif first_line.startswith("#!/") and ext == ".ts":
                # TS with shebang — rare but handle it
                lines.pop(0)
                while lines and lines[0].strip() == "":
                    lines.pop(0)

        if not dry_run:
            new_content = kcp_header + "\n" + "".join(lines)
            full_path.write_text(new_content, encoding="utf-8")

        actions.append(action)

    return actions


def main() -> int:
    configure_utf8_output()
    logger = setup_logging("envelope_census")

    parser = argparse.ArgumentParser(
        description="Audit @SID header compliance across .py, .ps1, .ts files"
    )
    parser.add_argument(
        "--json", action="store_true", help="JSON output"
    )
    parser.add_argument(
        "--ext",
        action="append",
        help="Filter by extension (e.g. --ext .ps1 --ext .ts). Default: all",
    )
    parser.add_argument(
        "--missing-only",
        action="store_true",
        help="Only show files without @SID",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Counts only, no per-file listing",
    )
    parser.add_argument(
        "--stamp",
        action="store_true",
        help="Batch-insert @SID headers on files that don't have one",
    )
    parser.add_argument(
        "--kcp-stamp",
        action="store_true",
        help="Batch-insert full KCP headers (Cartouche + Khipu) on files missing them",
    )
    parser.add_argument(
        "--kcp-audit",
        action="store_true",
        help="Show per-file KCP tier breakdown with field heat map",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what --stamp/--kcp-stamp would do without writing files",
    )

    args = parser.parse_args()

    repo_root = find_repo_root()
    extensions = set(args.ext) if args.ext else SCANNABLE_EXTENSIONS

    results = run_census(repo_root, extensions, missing_only=args.missing_only)

    if args.kcp_stamp or (args.kcp_stamp and args.dry_run):
        actions = kcp_stamp_files(repo_root, results, dry_run=args.dry_run)
        if args.json:
            json.dump({"actions": actions, "count": len(actions)}, sys.stdout, indent=2)
            print()
        else:
            mode = "DRY RUN" if args.dry_run else "KCP STAMPED"
            for a in actions:
                status = a.get("status", "unknown")
                if status == "error":
                    print(f"  ⚠️  SKIP  {a['file']} ({a.get('reason', '')})")
                else:
                    print(f"  {'🔍' if args.dry_run else '✅'} {a['sid']:40s} → {a['file']}")
            print(f"\n  {mode}: {len(actions)} files")
        return 0 if not actions else (0 if not args.dry_run else 1)

    if args.stamp or args.dry_run:
        actions = stamp_files(repo_root, results, dry_run=args.dry_run)
        if args.json:
            json.dump({"actions": actions, "count": len(actions)}, sys.stdout, indent=2)
            print()
        else:
            mode = "DRY RUN" if args.dry_run else "STAMPED"
            for a in actions:
                status = a.get("status", "unknown")
                if status == "error":
                    print(f"  ⚠️  SKIP  {a['file']} ({a.get('reason', '')})")
                else:
                    print(f"  {'🔍' if args.dry_run else '✅'} {a['sid']:40s} → {a['file']}")
            print(f"\n  {mode}: {len(actions)} files")
        return 0 if not actions else (0 if not args.dry_run else 1)

    if args.json:
        total = len(results)
        compliant = sum(1 for r in results if r["has_sid"])
        output = {
            "total": total,
            "compliant": compliant,
            "missing": total - compliant,
            "compliance_pct": round(compliant / total * 100, 1) if total else 0,
            "files": results,
        }
        json.dump(output, sys.stdout, indent=2)
        print()
    else:
        if args.kcp_audit:
            print_kcp_audit(results)
        else:
            print_report(results, summary_only=args.summary)

    # Exit code: 0 = all compliant, 1 = some missing
    missing = sum(1 for r in results if not r.get("has_sid"))
    return 1 if missing > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
