#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""
Bulk @SID header stamper for PowerShell scripts.

Reads each .ps1 file, checks for existing @SID. If missing, inserts a
compact header block after the shebang line (or at line 1 if no shebang).

Usage:
    uv run scripts/lib/stamp_sid.py --dry-run     # preview
    uv run scripts/lib/stamp_sid.py                # apply
    uv run scripts/lib/stamp_sid.py --json         # machine output
"""

from __future__ import annotations


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import argparse
import json
import re
import sys
from pathlib import Path


def find_repo_root() -> Path:
    cur = Path(__file__).resolve()
    for p in [cur, *cur.parents]:
        if (p / "pyproject.toml").exists() and (p / "AGENTS.md").exists():
            return p
    return Path.cwd()


ROOT = find_repo_root()
SCRIPTS = ROOT / "scripts"

# SID naming: SCRIPT_<UPPER_SNAKE>_V1
def make_sid(name: str) -> str:
    stem = Path(name).stem
    upper = re.sub(r"[^a-zA-Z0-9]", "_", stem).upper()
    upper = re.sub(r"_+", "_", upper).strip("_")
    # Avoid double version suffix (e.g., ssot_registry_query_v2 -> _V2_V1)
    if re.search(r"_V\d+$", upper):
        return f"SCRIPT_{upper}"
    return f"SCRIPT_{upper}_V1"


def extract_purpose(content: str, filename: str) -> str:
    """Try to extract a purpose from the first comment or param block."""
    # Check for a comment block after shebang
    lines = content.splitlines()
    for line in lines[1:10]:  # scan first 10 lines after shebang
        stripped = line.strip().lstrip("#").strip()
        if stripped and not stripped.startswith("!") and len(stripped) > 10:
            # Clean up common patterns
            if stripped.startswith(".SYNOPSIS"):
                continue
            if stripped.startswith("param("):
                break
            return stripped[:80]
    return Path(filename).stem.replace("_", " ").replace("-", " ").title()


def classify_role(stem: str) -> str:
    """Guess architectural role from filename."""
    s = stem.lower()
    if any(k in s for k in ["test", "check", "validate", "audit", "lint"]):
        return "VALIDATION"
    if any(k in s for k in ["run_", "launch", "start", "serve"]):
        return "RUNNER"
    if any(k in s for k in ["install", "patch", "update", "fix", "purge"]):
        return "MAINTENANCE"
    if any(k in s for k in ["bridge", "mcp", "sentry"]):
        return "INFRASTRUCTURE"
    if any(k in s for k in ["claude", "codex", "gemini"]):
        return "AGENT"
    if any(k in s for k in ["ssot", "probe", "scan"]):
        return "ANALYSIS"
    return "UTILITY"


def build_header(filename: str, content: str) -> str:
    stem = Path(filename).stem
    sid = make_sid(filename)
    purpose = extract_purpose(content, filename)
    role = classify_role(stem)
    return (
        f"#\n"
        f"# @SID: {sid}\n"
        f"# @Type: {role}\n"
        f"# @Spectrum: WHITE\n"
        f"# @Zone: THE GARDEN\n"
        f"# @Purpose: {purpose}\n"
        f"#\n"
    )


def stamp_file(path: Path, dry_run: bool = False) -> dict:
    content = path.read_text(encoding="utf-8", errors="replace")

    if "@SID" in content or "Semantic ID:" in content:
        return {"file": str(path.relative_to(ROOT)), "status": "already_compliant"}

    lines = content.splitlines(keepends=True)
    header = build_header(path.name, content)

    # Insert after shebang if present
    if lines and lines[0].startswith("#!"):
        insert_at = 1
    else:
        insert_at = 0

    if not dry_run:
        new_lines = lines[:insert_at] + [header] + lines[insert_at:]
        path.write_text("".join(new_lines), encoding="utf-8")

    sid = make_sid(path.name)
    return {
        "file": str(path.relative_to(ROOT)),
        "status": "stamped" if not dry_run else "would_stamp",
        "sid": sid,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Bulk @SID stamper for PS1 scripts")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    # Collect all PS1 files under scripts/
    targets: list[Path] = []
    for ps1 in sorted(SCRIPTS.rglob("*.ps1")):
        # Skip dumpster-dive and intake
        rel = str(ps1.relative_to(ROOT))
        if "dumpster-dive" in rel or "intake" in rel:
            continue
        targets.append(ps1)

    results = []
    for t in targets:
        results.append(stamp_file(t, dry_run=args.dry_run))

    stamped = [r for r in results if r["status"] in ("stamped", "would_stamp")]
    compliant = [r for r in results if r["status"] == "already_compliant"]

    if args.json:
        print(json.dumps({"stamped": len(stamped), "compliant": len(compliant), "results": results}, indent=2))
    else:
        for r in stamped:
            print(f"  {'STAMP' if r['status'] == 'stamped' else 'WOULD'}: {r['file']} -> {r.get('sid', '?')}")
        print(f"\n{'Stamped' if not args.dry_run else 'Would stamp'}: {len(stamped)}  |  Already compliant: {len(compliant)}  |  Total: {len(results)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
