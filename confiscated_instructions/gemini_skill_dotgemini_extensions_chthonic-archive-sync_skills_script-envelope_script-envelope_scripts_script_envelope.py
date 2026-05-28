#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""
Script-Envelope automation skeleton.
Not executed by default. Extend only when explicit automation is requested.
@SID:           TOOL_SCRIPT_ENVELOPE_V1
@Shabti:        \s*(.+)", text)
@Purpose:       Script-Envelope automation skeleton.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path

_TOP_BORDER = "# ╔"
_MID_BORDER = "# ╠"
_BOT_BORDER = "# ╚"
_BORDER_LEN = 76
_PY_CANON = ["#!/usr/bin/env python3", "#-*- coding: utf-8 -*-"]
_RIGHT_CLOSERS = ("╗", "╣", "╝")
_DEFAULT_DEPS_POLICY = Path(".meta/python-deps-policy.json")
_REQUIRED_DEPS_POLICY_KEYS = {
    "version",
    "auto_add_enabled",
    "allowed_groups",
    "import_package_map",
    "lock_after_add",
    "sync_after_add",
    "audit_after_add",
}


def _envelope_line(content: str) -> str:
    return f"# ║ {content}"


def build_envelope(lines: list[str]) -> list[str]:
    """
    Build a canonical ASCII envelope from ordered interior lines.

    Canon layout:
      ╔═══...
      ║ THE DECORATOR'S BLESSING: <filename>
      ╠═══...
      ║ Wedjat-Quipu Spectrum: <color>
      ║ Temple-Ayllu Zone: <emoji zone>
      ║ Ogdoad-Ceque Radiance:
      ║   └─◄ <radiance>
      ╚═══...

    This is a pure function: it does not read/write files.
    """
    top = f"# ╔{'═' * _BORDER_LEN}"
    mid = f"# ╠{'═' * _BORDER_LEN}"
    bottom = f"# ╚{'═' * _BORDER_LEN}"

    result = [
        top,
        _envelope_line(lines[0]),
        mid,
    ]
    result.extend(_envelope_line(line) for line in lines[1:])
    result.append(bottom)
    return result


def extract_existing_envelope(text: str) -> tuple[list[str], list[str]]:
    """
    Return (envelope_lines, remaining_lines).

    This is a minimal parser stub. It detects a top/mid/bottom frame
    by line prefix and returns the first matched block only.
    """
    lines = text.splitlines()
    start = None
    end = None
    for i, line in enumerate(lines):
        if line.startswith(_TOP_BORDER):
            start = i
            break
    if start is not None:
        for j in range(start + 1, len(lines)):
            if lines[j].startswith(_BOT_BORDER):
                end = j
                break
    if start is None or end is None:
        return [], lines
    envelope = lines[start : end + 1]
    remaining = lines[:start] + lines[end + 1 :]
    return envelope, remaining


def extract_fields(text: str, filename: str = "") -> dict[str, str]:
    """
    Extract metadata fields from script content using AST/Regex.
    Supports Python and PowerShell.

    Canon field names (Wedjat-Quipu / Temple-Ayllu / Ogdoad-Ceque):
      spectrum        -> Wedjat-Quipu Spectrum color
      zone            -> Temple-Ayllu Zone (emoji + name)
      radiance        -> Ogdoad-Ceque Radiance (dep chain hint)
      sid             -> @SID value
      shabti          -> @Shabti type
      purpose         -> one-line purpose
    """
    fields = {
        "title": filename,
        "spectrum": "WHITE",
        "zone": "\U0001f33f THE GARDEN",
        "radiance": "(Standalone)",
        "sid": "",
        "shabti": "CLI Script",
        "purpose": "",
    }

    # Python Strategy
    if text.lstrip().startswith("#!") or "def " in text or "import " in text:
        try:
            tree = ast.parse(text)
            
            # Purpose: First docstring
            docstring = ast.get_docstring(tree)
            if docstring:
                fields["purpose"] = docstring.split('\n')[0]

            # Exports: Functions and Classes (not stored in envelope, for metadata only)
            exports = []
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    if not node.name.startswith('_'):
                        exports.append(node.name)

            # SID: Look for @SID tag in comments/docstrings
            sid_match = re.search(r"@SID:\s*([A-Z0-9_]+)", text)
            if sid_match:
                fields["sid"] = sid_match.group(1)

            # Shabti: Look for @Shabti tag
            shabti_match = re.search(r"@Shabti:\s*(.+)", text)
            if shabti_match:
                fields["shabti"] = shabti_match.group(1).strip()

            # Existing envelope: extract Spectrum/Zone/Radiance if present
            spectrum_match = re.search(r"(?:Wedjat-Quipu Spectrum|Spectral Frequency):\s*(.+)", text)
            if spectrum_match:
                fields["spectrum"] = spectrum_match.group(1).strip()
            zone_match = re.search(r"(?:Temple-Ayllu Zone|Architectural Role):\s*(.+)", text)
            if zone_match:
                fields["zone"] = zone_match.group(1).strip()
            radiance_match = re.search(r"\u2514\u2500\u25c4\s*(.+)", text)
            if radiance_match:
                fields["radiance"] = radiance_match.group(1).strip()

        except Exception:
            pass # Fallback to basic regex if AST fails

    # PowerShell Strategy (Basic Regex)
    if "function " in text or "param(" in text or "$env:" in text:
        # Purpose: Look for .SYNOPSIS or top comment
        synopsis_match = re.search(r"\.SYNOPSIS\s*\n\s*(.*)", text)
        if synopsis_match:
            fields["purpose"] = synopsis_match.group(1).strip()

    return fields


def fields_to_lines(fields: dict[str, str]) -> list[str]:
    """
    Convert a field dict into ordered interior lines for the canon envelope.

    Canon format (Wedjat-Quipu / Temple-Ayllu / Ogdoad-Ceque):
      Line 1: THE DECORATOR'S BLESSING: <filename>
      --- mid border ---
      Line 2: Wedjat-Quipu Spectrum: <color>
      Line 3: Temple-Ayllu Zone: <emoji zone_name>
      Line 4: Ogdoad-Ceque Radiance:
      Line 5:   └─◄ <radiance>
    """
    return [
        f"THE DECORATOR'S BLESSING: {fields.get('title', '')}",
        f"Wedjat-Quipu Spectrum: {fields.get('spectrum', 'WHITE')}",
        f"Temple-Ayllu Zone: {fields.get('zone', '\U0001f33f THE GARDEN')}",
        "Ogdoad-Ceque Radiance:",
        f"  \u2514\u2500\u25c4 {fields.get('radiance', '(Standalone)')}",
    ]


def canonicalize_script(text: str, interior_lines: list[str]) -> str:
    """
    Return full script text with a canonical envelope inserted.

    This is a stub: it expects already-ordered interior lines.
    """
    envelope = build_envelope(interior_lines)
    _, remaining = extract_existing_envelope(text)
    return "\n".join(envelope + [""] + remaining)


def normalize_python_header(text: str) -> tuple[str, bool]:
    """
    Normalize Python script header to canonical two-line form.

    Idempotent:
    - If header is already canonical, returns (original_text, False)
    - Otherwise returns (updated_text, True)
    """
    lines = text.splitlines()
    if len(lines) >= 2 and lines[0] == _PY_CANON[0] and lines[1] == _PY_CANON[1]:
        return text, False

    idx = 0
    if idx < len(lines) and lines[idx].startswith("#!"):
        idx += 1
    if idx < len(lines) and lines[idx].strip() in {"# -*- coding: utf-8 -*-", "#-*- coding: utf-8 -*-"}:
        idx += 1

    updated = "\n".join(_PY_CANON + lines[idx:]) + "\n"
    if updated == text:
        return text, False
    return updated, True


def replace_envelope_in_file(path: Path, interior_lines: list[str]) -> None:
    """
    Explicit IO stub: read file, canonicalize, write back.
    This function is not called unless explicitly invoked.
    """
    text = path.read_text(encoding="utf-8")
    updated = canonicalize_script(text, interior_lines)
    if updated != text:
        path.write_text(updated, encoding="utf-8")


def normalize_python_header_in_file(path: Path) -> bool:
    """
    Normalize Python header in file with no-op write behavior.
    """
    text = path.read_text(encoding="utf-8")
    updated, changed = normalize_python_header(text)
    if changed:
        path.write_text(updated, encoding="utf-8")
    return changed


def strip_right_edge_box_glyphs(text: str) -> tuple[str, bool]:
    """
    Convert closed box-drawing envelope lines to open-sided form.

    - Removes trailing right-edge glyphs on border lines: ╗ ╣ ╝
    - Removes trailing content-side right border on comment lines ending in `║`
    """
    changed = False
    out: list[str] = []
    for line in text.splitlines():
        new_line = line
        stripped = new_line.rstrip()
        if stripped.endswith(_RIGHT_CLOSERS):
            new_line = stripped[:-1].rstrip()
            changed = True
        # Content lines like "# ║ ... ║" become "# ║ ..."
        stripped = new_line.rstrip()
        if stripped.startswith("# ║") and stripped.endswith("║"):
            new_line = stripped[:-1].rstrip()
            changed = True
        # Docstring banner lines like "║ ... ║" become "║ ..."
        stripped = new_line.rstrip()
        if stripped.startswith("║") and stripped.endswith("║"):
            new_line = stripped[:-1].rstrip()
            changed = True
        out.append(new_line)

    updated = "\n".join(out) + "\n"
    return updated, changed


def normalize_open_sided_in_file(path: Path) -> bool:
    """
    Rewrite box envelopes to open-sided format only when needed.
    """
    text = path.read_text(encoding="utf-8")
    updated, changed = strip_right_edge_box_glyphs(text)
    if changed:
        path.write_text(updated, encoding="utf-8")
    return changed


def has_python_module_docstring(text: str) -> bool:
    """
    Return True when the script has a module-level docstring.
    """
    try:
        tree = ast.parse(text)
    except Exception:
        return False
    return bool(ast.get_docstring(tree))


def validate_python_prologue(text: str) -> tuple[bool, list[str]]:
    """
    Validate canonical Python prologue convention without modifying content.
    """
    issues: list[str] = []
    lines = text.splitlines()
    if len(lines) < 2:
        return False, ["File too short for canonical Python prologue."]

    if lines[0] != _PY_CANON[0]:
        issues.append(f"Line 1 mismatch: expected `{_PY_CANON[0]}`")
    if lines[1] != _PY_CANON[1]:
        issues.append(f"Line 2 mismatch: expected `{_PY_CANON[1]}`")
    if not has_python_module_docstring(text):
        issues.append("Missing module-level docstring banner.")

    return len(issues) == 0, issues


def validate_deps_policy(path: Path) -> tuple[bool, list[str]]:
    """
    Validate dependency metadata policy file shape.
    """
    issues: list[str] = []
    if not path.exists():
        return False, [f"Policy file not found: {path}"]

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return False, [f"Invalid JSON: {exc}"]

    missing = sorted(k for k in _REQUIRED_DEPS_POLICY_KEYS if k not in data)
    if missing:
        issues.append(f"Missing keys: {', '.join(missing)}")

    if not isinstance(data.get("allowed_groups", None), list):
        issues.append("`allowed_groups` must be a list.")
    if not isinstance(data.get("import_package_map", None), dict):
        issues.append("`import_package_map` must be an object/map.")

    bool_keys = ("auto_add_enabled", "lock_after_add", "sync_after_add", "audit_after_add")
    for key in bool_keys:
        if key in data and not isinstance(data[key], bool):
            issues.append(f"`{key}` must be a boolean.")

    return len(issues) == 0, issues


def main() -> int:
    # DO NOT add business logic here unless explicitly requested.
    # This script is not part of the default skill execution path.
    # If automation is added, keep borders open-sided and fixed-width.
    parser = argparse.ArgumentParser(description="Script-Envelope skeleton")
    parser.add_argument("path", help="Target script file")
    parser.add_argument(
        "--normalize-python-header",
        action="store_true",
        help="Apply canonical Python shebang/coding header with no-op write if already canonical.",
    )
    parser.add_argument(
        "--validate-python-prologue",
        action="store_true",
        help="Validate canonical Python header + module docstring convention without rewriting.",
    )
    parser.add_argument(
        "--normalize-open-sided",
        action="store_true",
        help="Strip right-edge box glyphs (╗ ╣ ╝ and trailing content ║) to enforce open-sided envelopes.",
    )
    parser.add_argument(
        "--check-deps-policy",
        action="store_true",
        help="Validate dependency metadata policy JSON shape (default: .meta/python-deps-policy.json).",
    )
    parser.add_argument(
        "--deps-policy-path",
        default=str(_DEFAULT_DEPS_POLICY),
        help="Dependency policy JSON path used by --check-deps-policy.",
    )
    args = parser.parse_args()

    target = Path(args.path)
    if not target.exists():
        raise SystemExit(f"Target not found: {target}")

    if args.normalize_python_header:
        changed = normalize_python_header_in_file(target)
        print(f"Python header target: {target}")
        print(f"Changed: {changed}")
        return 0

    if args.validate_python_prologue:
        text = target.read_text(encoding="utf-8")
        ok, issues = validate_python_prologue(text)
        print(f"Python prologue target: {target}")
        print(f"Valid: {ok}")
        if not ok:
            for issue in issues:
                print(f"- {issue}")
        return 0 if ok else 1

    if args.normalize_open_sided:
        changed = normalize_open_sided_in_file(target)
        print(f"Open-sided target: {target}")
        print(f"Changed: {changed}")
        return 0

    if args.check_deps_policy:
        policy_path = Path(args.deps_policy_path)
        ok, issues = validate_deps_policy(policy_path)
        print(f"Deps policy target: {policy_path}")
        print(f"Valid: {ok}")
        if not ok:
            for issue in issues:
                print(f"- {issue}")
        return 0 if ok else 1

    print(f"Envelope target: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
