#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""
Script-Envelope automation skeleton.
Not executed by default. Extend only when explicit automation is requested.
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

    This is a pure function: it does not read/write files.
    """
    top = f"# ╔{'═' * _BORDER_LEN}"
    mid = f"# ╠{'═' * _BORDER_LEN}"
    bottom = f"# ╚{'═' * _BORDER_LEN}"

    header = [
        top,
        _envelope_line(lines[0]),
        _envelope_line(lines[1]),
        mid,
    ]
    body = [_envelope_line(line) for line in lines[2:]]
    return header + body + [bottom]


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
    """
    fields = {
        "title": filename,
        "module": "",
        "spectral_frequency": "Unknown",
        "architectural_role": "Utility",
        "semantic_id": "",
        "purpose": "",
        "exports": "",
        "flags": "",
        "cross_references": "",
    }

    # Python Strategy
    if text.lstrip().startswith("#!") or "def " in text or "import " in text:
        try:
            tree = ast.parse(text)
            
            # Purpose: First docstring
            docstring = ast.get_docstring(tree)
            if docstring:
                fields["purpose"] = docstring.split('\n')[0]

            # Exports: Functions and Classes
            exports = []
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    if not node.name.startswith('_'):
                        exports.append(node.name)
            if exports:
                fields["exports"] = ", ".join(exports[:5]) # Limit to 5 for brevity

            # SID: Look for @SID tag in comments
            sid_match = re.search(r"@SID:\s*([A-Z0-9_]+)", text)
            if sid_match:
                fields["semantic_id"] = sid_match.group(1)

        except Exception:
            pass # Fallback to basic regex if AST fails

    # PowerShell Strategy (Basic Regex)
    if "function " in text or "param(" in text or "$env:" in text:
        # Purpose: Look for .SYNOPSIS or top comment
        synopsis_match = re.search(r"\.SYNOPSIS\s*\n\s*(.*)", text)
        if synopsis_match:
            fields["purpose"] = synopsis_match.group(1).strip()
        
        # Exports: Functions
        funcs = re.findall(r"function\s+([a-zA-Z0-9-]+)", text)
        if funcs:
            fields["exports"] = ", ".join(funcs[:5])

    return fields


def fields_to_lines(fields: dict[str, str]) -> list[str]:
    """
    Convert a field dict into ordered interior lines for the envelope.

    This is pure and deterministic: no IO, no guessing.
    Empty fields are allowed and preserved.
    """
    return [
        f"THE DECORATOR'S BLESSING: {fields.get('title', '')}",
        f"Module: {fields.get('module', '')}",
        f"Spectral Frequency: {fields.get('spectral_frequency', '')}",
        f"Architectural Role: {fields.get('architectural_role', '')}",
        f"Semantic ID: {fields.get('semantic_id', '')}",
        f"Purpose: {fields.get('purpose', '')}",
        f"Exports: {fields.get('exports', '')}",
        f"Flags/Modes: {fields.get('flags', '')}",
        f"Cross-References: {fields.get('cross_references', '')}",
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
