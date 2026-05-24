#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: compare_e2e_matrices.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
compare_e2e_matrices.py — Script logic for compare_e2e_matrices.py.

@SID:           TOOL_COMPARE_E2E_MATRICES_V1
@Shabti:        CLI Script
@Purpose:       Script logic for compare_e2e_matrices.py.
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


from __future__ import annotations

import argparse
import json
from pathlib import Path

MATRIX_FILES = [
    "e2e_matrix_codex_on_codex.json",
    "e2e_matrix_codex_on_claude.json",
    "e2e_matrix_claude_on_codex.json",
    "e2e_matrix_claude_on_claude.json",
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def matrix_summary(payload: dict) -> dict:
    results = payload.get("results", [])
    return {
        "flavor": payload.get("flavor"),
        "root": payload.get("root"),
        "count": len(results),
        "all_clean": all((r.get("score", 0) == 100 and not r.get("issues")) for r in results),
        "score_map": {r.get("name"): r.get("score", 0) for r in results},
        "issue_count": sum(len(r.get("issues", [])) for r in results),
    }


def compare_summaries(left: dict, right: dict) -> tuple[bool, list[str]]:
    issues: list[str] = []
    if left["flavor"] != right["flavor"]:
        issues.append(f"flavor mismatch: {left['flavor']} != {right['flavor']}")
    if left["root"] != right["root"]:
        issues.append(f"root mismatch: {left['root']} != {right['root']}")
    if left["count"] != right["count"]:
        issues.append(f"result count mismatch: {left['count']} != {right['count']}")
    if left["all_clean"] != right["all_clean"]:
        issues.append(f"all_clean mismatch: {left['all_clean']} != {right['all_clean']}")
    if left["issue_count"] != right["issue_count"]:
        issues.append(f"issue_count mismatch: {left['issue_count']} != {right['issue_count']}")
    if left["score_map"] != right["score_map"]:
        issues.append("score map mismatch")
    return (len(issues) == 0, issues)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare Codex-side and Claude-side E2E matrix JSON outputs.")
    parser.add_argument("--codex-dir", default="codex/mailbox", help="Directory with Codex matrix JSON files")
    parser.add_argument("--claude-dir", default="claude/mailbox", help="Directory with Claude matrix JSON files")
    parser.add_argument("--json-out", default="codex/mailbox/e2e_matrix_compare_summary.json", help="Comparison summary JSON output path")
    args = parser.parse_args()

    codex_dir = Path(args.codex_dir)
    claude_dir = Path(args.claude_dir)
    summary: dict[str, dict] = {}
    mismatches: dict[str, list[str]] = {}

    for name in MATRIX_FILES:
        codex_path = codex_dir / name
        claude_path = claude_dir / name
        if not codex_path.exists() or not claude_path.exists():
            missing = []
            if not codex_path.exists():
                missing.append(f"missing codex file: {codex_path.as_posix()}")
            if not claude_path.exists():
                missing.append(f"missing claude file: {claude_path.as_posix()}")
            mismatches[name] = missing
            continue

        codex_payload = load_json(codex_path)
        claude_payload = load_json(claude_path)
        codex_summary = matrix_summary(codex_payload)
        claude_summary = matrix_summary(claude_payload)
        ok, issues = compare_summaries(codex_summary, claude_summary)
        summary[name] = {
            "ok": ok,
            "codex": codex_summary,
            "claude": claude_summary,
            "issues": issues,
        }
        if not ok:
            mismatches[name] = issues

    out = {
        "ok": len(mismatches) == 0,
        "compared": len(summary),
        "mismatches": mismatches,
        "summary": summary,
    }
    out_path = Path(args.json_out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print(f"Compared matrix files: {len(summary)}")
    print(f"Mismatched files: {len(mismatches)}")
    print(f"Wrote JSON: {out_path.as_posix()}")
    if mismatches:
        for name, issues in mismatches.items():
            print(name)
            for issue in issues:
                print(f"  - {issue}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
