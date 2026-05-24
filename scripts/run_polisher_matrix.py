#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: run_polisher_matrix.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""Run the Codex-side polisher matrix and emit a single JSON report.

This is intentionally KISS: it shells out to the existing polisher (uv run) so
behavior stays centralized in `.codex/skills/skill-polisher/scripts/polish_skill.py`.

Outputs are written to `codex/mailbox/`.

@SID:           TOOL_RUN_POLISHER_MATRIX_V1
@Shabti:        CLI Script
@Purpose:       Run the Codex-side polisher matrix and emit a single JSON report.
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class MatrixCase:
    name: str
    root: str
    target_flavor: str
    require_assets: bool


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_case(case: MatrixCase, stamps_path: Path, summary_path: Path) -> dict:
    polisher = Path(".codex/skills/skill-polisher/scripts/polish_skill.py")
    cmd = [
        "uv",
        "run",
        str(polisher),
        case.root,
        "--all",
        "--mode",
        "verify",
        "--subprocess-fix",
        "--target-flavor",
        case.target_flavor,
        "--emit-stamps-json",
        str(stamps_path),
        "--emit-summary-md",
        str(summary_path),
    ]
    if case.require_assets:
        cmd.append("--require-assets")
    else:
        cmd.append("--no-require-assets")

    proc = subprocess.run(cmd, check=False)
    return {
        "case": {
            "name": case.name,
            "root": case.root,
            "target_flavor": case.target_flavor,
            "require_assets": case.require_assets,
        },
        "exit_code": proc.returncode,
        "stamps_json": stamps_path.as_posix(),
        "summary_md": summary_path.as_posix(),
    }


def main() -> None:
    out_dir = Path("codex/mailbox")
    out_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime("%Y_%m_%d")

    cases = [
        MatrixCase(
            name="codex_on_codex",
            root=".codex/skills",
            target_flavor="codex",
            require_assets=True,
        ),
        MatrixCase(
            name="codex_on_claude",
            root=".claude/skills",
            target_flavor="claude",
            require_assets=True,
        ),
        MatrixCase(
            name="auto_on_claude",
            root=".claude/skills",
            target_flavor="auto",
            require_assets=True,
        ),
        MatrixCase(
            name="claude_contract_on_codex",
            root=".codex/skills",
            target_flavor="claude",
            require_assets=True,
        ),
    ]

    results = []
    for c in cases:
        stamps_path = out_dir / f"tatragrammatron_stamps_{stamp}_{c.name}.json"
        summary_path = out_dir / f"TATRAGRAMMATRON_SUMMARY_{stamp}_{c.name.upper()}.md"
        results.append(run_case(c, stamps_path, summary_path))

    matrix = {
        "generated_at": utc_now(),
        "runner": "codex",
        "cases": results,
    }
    matrix_path = out_dir / f"tatragrammatron_matrix_{stamp}.json"
    matrix_path.write_text(json.dumps(matrix, indent=2), encoding="utf-8")
    print(f"Wrote: {matrix_path}")


if __name__ == "__main__":
    main()
