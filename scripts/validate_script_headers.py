#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: validate_script_headers.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
validate_script_headers.py - Validate script metadata headers in scripts/.

@SID:           TOOL_VALIDATE_SCRIPT_HEADERS_V1
@Shabti:          Utility Script
@Context:       Metadata Validation / Headers
@Implements:    PROTOCOL_ANCHOR_SIGNAL
@Purpose:       validate_script_headers.py - Validate script metadata headers in scripts/.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

REQUIRED_FIELDS = ["SID", "Shabti", "Purpose"]
SHEBANG_PYTHON = "#!/usr/bin/env python3"


def _has_required_fields(text: str) -> Tuple[bool, List[str]]:
    missing = []
    for field in REQUIRED_FIELDS:
        if not re.search(rf"@{field}:\s+\S+", text):
            missing.append(field)
    return len(missing) == 0, missing


def _python_docstring(text: str) -> str | None:
    try:
        module = ast.parse(text)
    except SyntaxError:
        return None
    return ast.get_docstring(module)


def _validate_python(path: Path) -> Dict:
    text = path.read_text(encoding="utf-8")
    shebang_ok = text.startswith(SHEBANG_PYTHON)
    docstring = _python_docstring(text)

    issues = []
    missing_fields: List[str] = []

    if not shebang_ok:
        issues.append("missing_shebang")

    if not docstring:
        issues.append("missing_docstring")
    else:
        has_fields, missing_fields = _has_required_fields(docstring)
        if not has_fields:
            issues.append("missing_metadata_fields")

        first_line = docstring.splitlines()[0].strip() if docstring else ""
        if ".py -" not in first_line:
            issues.append("missing_module_summary")

    return {
        "path": path.as_posix(),
        "type": "python",
        "status": "ok" if not issues else "issues",
        "issues": issues,
        "missing_fields": missing_fields,
        "shebang": shebang_ok,
    }


def _validate_shell(path: Path, script_type: str) -> Dict:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()[:40]
    header_block = "\n".join(lines)
    has_fields, missing_fields = _has_required_fields(header_block)

    shebang_ok = True
    if script_type == "sh":
        shebang_ok = header_block.startswith("#!/usr/bin/env bash") or header_block.startswith("#!/bin/bash")
        if not shebang_ok:
            missing_fields.append("Shebang")

    issues = []
    if not shebang_ok:
        issues.append("missing_shebang")
    if not has_fields:
        issues.append("missing_metadata_fields")

    return {
        "path": path.as_posix(),
        "type": script_type,
        "status": "ok" if not issues else "issues",
        "issues": issues,
        "missing_fields": missing_fields,
        "shebang": shebang_ok,
    }


def _scan_scripts(root: Path) -> List[Dict]:
    results: List[Dict] = []
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        if path.suffix == ".py":
            results.append(_validate_python(path))
        elif path.suffix == ".ps1":
            results.append(_validate_shell(path, "ps1"))
        elif path.suffix == ".sh":
            results.append(_validate_shell(path, "sh"))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate script metadata headers in scripts/")
    parser.add_argument(
        "--root",
        type=str,
        default="scripts",
        help="Root directory to scan",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON report",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if any issues are found",
    )

    args = parser.parse_args()
    root = Path(args.root)

    results = _scan_scripts(root)
    issue_count = sum(1 for r in results if r["status"] != "ok")

    if args.json:
        payload = {
            "root": root.as_posix(),
            "total": len(results),
            "issues": issue_count,
            "results": results,
        }
        print(json.dumps(payload, indent=2))
    else:
        print(f"Scanned: {len(results)} files")
        print(f"Issues: {issue_count}")
        for result in results:
            if result["status"] != "ok":
                missing = ", ".join(result["missing_fields"]) if result["missing_fields"] else "unknown"
                print(f"- {result['path']} -> {missing}")

    if args.strict and issue_count > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
