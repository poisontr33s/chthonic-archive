#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Canonical single-entry runner for one full skill tensor cycle.
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path


def find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for p in [cur, *cur.parents]:
        if (p / "AGENTS.md").exists() and (p / "pyproject.toml").exists():
            return p
    return start.resolve()


def write_markdown_summary(path: Path, payload: dict) -> None:
    lines = [
        "# Skill Tensor Cycle",
        "",
        f"- Overall Status: `{payload.get('overall_status')}`",
        f"- Queue Length: `{payload.get('queue_length')}`",
        "",
        "## Severity",
        f"- Freshness Status: `{payload.get('freshness', {}).get('status')}`",
        f"- Critical Issues: `{payload.get('freshness', {}).get('critical_issues')}`",
        f"- Warnings: `{payload.get('freshness', {}).get('warnings')}`",
        "",
        "## Duplication",
        f"- Managed Artifact Duplicates: `{payload.get('duplication', {}).get('managed_duplicates')}`",
        f"- Extra Managed Files: `{payload.get('duplication', {}).get('extra_managed_files')}`",
        "",
        "## Dependencies",
        f"- Estimated External Packages: `{payload.get('dependencies', {}).get('count')}`",
        "",
        "## Steps",
    ]
    for step in payload.get("steps", []):
        lines += [
            f"### {step['name']}",
            f"- Status: `{step['status']}`",
            f"- RC: `{step['rc']}`",
            f"- Seconds: `{step['seconds']}`",
            "",
        ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_json_if_exists(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_text_if_exists(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def build_freshness_summary(repo_root: Path) -> dict:
    report = load_json_if_exists(repo_root / "codex/mailbox/SKILL_FRESHNESS_LATEST.json")
    summary = report.get("summary", {})
    return {
        "status": report.get("status", "unknown"),
        "critical_issues": summary.get("critical_issues", 0),
        "warnings": summary.get("warnings", 0),
    }


def build_duplication_summary(repo_root: Path) -> dict:
    mailbox = repo_root / "codex/mailbox"
    managed = sorted(mailbox.glob("SKILL_TENSOR_*"))
    canonical = {
        "SKILL_TENSOR_INVENTORY.json",
        "SKILL_TENSOR_INVENTORY.md",
        "SKILL_TENSOR_POOL.json",
        "SKILL_TENSOR_POOL.md",
        "SKILL_TENSOR_ROULETTE_LATEST.json",
        "SKILL_TENSOR_ROULETTE_LATEST.md",
        "SKILL_TENSOR_PLAN_LATEST.json",
        "SKILL_TENSOR_PLAN_LATEST.md",
        "SKILL_TENSOR_EXECUTION_LATEST.json",
        "SKILL_TENSOR_EXECUTION_LATEST.md",
        "SKILL_TENSOR_LEDGER.json",
        "SKILL_TENSOR_LEDGER.md",
        "SKILL_TENSOR_WEIGHTS_LATEST.json",
        "SKILL_TENSOR_WEIGHTS_LATEST.md",
        "SKILL_TENSOR_CYCLE_LATEST.json",
        "SKILL_TENSOR_CYCLE_LATEST.md",
    }
    extra = [p.name for p in managed if p.name not in canonical]
    return {
        "managed_duplicates": len(extra),
        "extra_managed_files": extra,
        "managed_files": [p.name for p in managed],
    }


def estimate_dependencies(repo_root: Path) -> dict:
    tensor_scripts = sorted(repo_root.glob("scripts/skill_tensor*.py"))
    stdlib = set(getattr(sys, "stdlib_module_names", set()))
    module_to_package = {
        "yaml": "pyyaml",
        "tomli": "tomli",
        "toml": "toml",
        "requests": "requests",
        "numpy": "numpy",
        "pandas": "pandas",
        "polars": "polars",
        "networkx": "networkx",
        "fastmcp": "fastmcp",
        "huggingface_hub": "huggingface-hub",
        "pydantic": "pydantic",
    }
    discovered = set()
    for script in tensor_scripts:
        try:
            tree = ast.parse(script.read_text(encoding="utf-8"))
        except Exception:
            continue
        for node in ast.walk(tree):
            mod = None
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod = alias.name.split(".")[0]
                    if mod and mod not in stdlib and importlib.util.find_spec(mod) is None:
                        discovered.add(module_to_package.get(mod, mod))
            elif isinstance(node, ast.ImportFrom) and node.module:
                mod = node.module.split(".")[0]
                if mod and mod not in stdlib and importlib.util.find_spec(mod) is None:
                    discovered.add(module_to_package.get(mod, mod))
    packages = sorted(discovered)
    return {
        "count": len(packages),
        "packages": packages,
        "scripts_scanned": [p.name for p in tensor_scripts],
    }


def collect_sections(repo_root: Path) -> dict:
    mailbox = repo_root / "codex" / "mailbox"
    return {
        "inventory": load_json_if_exists(mailbox / "SKILL_TENSOR_INVENTORY.json"),
        "pool": load_json_if_exists(mailbox / "SKILL_TENSOR_POOL.json"),
        "roulette": load_json_if_exists(mailbox / "SKILL_TENSOR_ROULETTE_LATEST.json"),
        "plan": load_json_if_exists(mailbox / "SKILL_TENSOR_PLAN_LATEST.json"),
        "execution": load_json_if_exists(mailbox / "SKILL_TENSOR_EXECUTION_LATEST.json"),
        "ledger": load_json_if_exists(mailbox / "SKILL_TENSOR_LEDGER.json"),
        "weights": load_json_if_exists(mailbox / "SKILL_TENSOR_WEIGHTS_LATEST.json"),
        "spec": load_text_if_exists(repo_root / "docs" / "ops" / "SKILL_TENSOR_ROULETTE_SPEC.md"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one full tensor cycle")
    parser.add_argument("--output", default="codex/mailbox/SKILL_TENSOR_CYCLE_LATEST.json")
    args = parser.parse_args()

    repo_root = find_repo_root(Path.cwd())
    sequence = [
        ("inventory", ["uv", "run", "scripts/skill_tensor_inventory.py"]),
        ("pool", ["uv", "run", "scripts/skill_tensor_pool.py"]),
        ("weights", ["uv", "run", "scripts/skill_tensor_weights.py"]),
        ("roulette", ["uv", "run", "scripts/skill_tensor_roulette.py"]),
        ("plan", ["uv", "run", "scripts/skill_tensor_plan.py"]),
        ("execute", ["uv", "run", "scripts/skill_tensor_execute.py"]),
        ("feedback", ["uv", "run", "scripts/skill_tensor_feedback.py"]),
    ]

    results = []
    overall_status = "passed"
    for name, cmd in sequence:
        t0 = time.time()
        proc = subprocess.run(
            cmd,
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        dt = time.time() - t0
        status = "passed" if proc.returncode == 0 else "failed"
        results.append(
            {
                "name": name,
                "cmd": cmd,
                "rc": proc.returncode,
                "seconds": round(dt, 3),
                "status": status,
                "stdout_tail": "\n".join((proc.stdout or "").splitlines()[-12:]),
                "stderr_tail": "\n".join((proc.stderr or "").splitlines()[-12:]),
            }
        )
        if status != "passed":
            overall_status = "failed"
            # still continue to allow feedback/spec regeneration if execute failed
            if name not in {"execute", "feedback"}:
                break

    payload = {
        "schema_version": 1,
        "overall_status": overall_status,
        "queue_length": len(sequence),
        "subprocess_queue": [name for name, _ in sequence],
        "freshness": build_freshness_summary(repo_root),
        "duplication": build_duplication_summary(repo_root),
        "dependencies": estimate_dependencies(repo_root),
        "steps": results,
        "sections": collect_sections(repo_root),
    }

    out = repo_root / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_markdown_summary(out.with_suffix(".md"), payload)
    print(out.relative_to(repo_root).as_posix())
    print(f"overall_status={overall_status}")
    return 0 if overall_status == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
