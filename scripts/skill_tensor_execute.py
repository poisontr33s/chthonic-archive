#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Execute one sampled skill tensor plan with capability checks.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path


def find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for p in [cur, *cur.parents]:
        if (p / "AGENTS.md").exists() and (p / "pyproject.toml").exists():
            return p
    return start.resolve()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def capabilities_allow(step: dict) -> tuple[bool, list[str]]:
    caps = step.get("operator_capabilities", {})
    reasons: list[str] = []

    safety = step.get("safety_class")
    if safety == "read_only" and not caps.get("read", False):
        reasons.append("missing_read_capability")
    if safety == "local_mutation" and not caps.get("mutate", False):
        reasons.append("missing_mutate_capability")
    if safety == "cross_lane_mutation" and not caps.get("cross_lane_mutate", False):
        reasons.append("missing_cross_lane_mutate_capability")
    if safety == "meta_orchestration" and not caps.get("recurse", False):
        reasons.append("missing_recurse_capability")

    return (len(reasons) == 0), reasons


def existing_artifacts(expected_artifacts: list[str], repo_root: Path) -> tuple[list[str], list[str]]:
    present: list[str] = []
    missing: list[str] = []
    for artifact in expected_artifacts:
        p = Path(artifact)
        full = p if p.is_absolute() else (repo_root / p)
        if full.exists():
            present.append(artifact)
        else:
            missing.append(artifact)
    return present, missing


def classify_failure(result: dict) -> str | None:
    if result.get("status") == "blocked":
        return "capability_block"
    if result.get("status") != "failed":
        return None
    if result.get("missing_artifacts"):
        return "missing_artifact"
    command = " ".join(result.get("command", []))
    if "trainstop-orchestrator/scripts/orchestrate.py" in command:
        return "trainstop_gate_failure"
    if "skill_path_guard.py" in command:
        return "path_guard_failure"
    if "skill_audit.py" in command:
        return "skill_audit_failure"
    if "polish_skill.py" in command:
        return "skill_polisher_failure"
    return "generic_failure"


def write_markdown_summary(path: Path, payload: dict) -> None:
    lines = [
        "# Skill Tensor Execution",
        "",
        f"- Overall Status: `{payload.get('overall_status')}`",
        "",
        "## Steps",
    ]
    for result in payload.get("results", []):
        lines += [
            f"### Step {result.get('step')}",
            f"- Status: `{result.get('status')}`",
            f"- Failure Kind: `{result.get('failure_kind')}`",
            f"- RC: `{result.get('rc')}`",
            f"- Seconds: `{result.get('seconds')}`",
            "",
        ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_step(step: dict, repo_root: Path) -> dict:
    command = step.get("command", [])
    t0 = time.time()
    proc = subprocess.run(
        command,
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    dt = time.time() - t0
    expected = step.get("expected_artifacts", [])
    present, missing = existing_artifacts(expected, repo_root)
    status = "passed" if proc.returncode == 0 else "failed"
    if status == "passed" and expected and step.get("stop_condition") == "stop_on_nonzero_or_missing_artifact" and missing:
        status = "failed"

    result = {
        "step": step.get("step"),
        "command": command,
        "rc": proc.returncode,
        "seconds": round(dt, 3),
        "stdout_tail": "\n".join((proc.stdout or "").splitlines()[-20:]),
        "stderr_tail": "\n".join((proc.stderr or "").splitlines()[-20:]),
        "expected_artifacts": expected,
        "present_artifacts": present,
        "missing_artifacts": missing,
        "stop_condition": step.get("stop_condition"),
        "status": status,
    }
    result["failure_kind"] = classify_failure(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute one sampled skill tensor plan")
    parser.add_argument("--input", default="codex/mailbox/SKILL_TENSOR_PLAN_LATEST.json")
    parser.add_argument("--output", default="codex/mailbox/SKILL_TENSOR_EXECUTION_LATEST.json")
    args = parser.parse_args()

    repo_root = find_repo_root(Path.cwd())
    plan = load_json(repo_root / args.input)

    results = []
    overall_status = "passed"
    for step in plan.get("steps", []):
        allowed, deny_reasons = capabilities_allow(step)
        if not allowed:
            result = {
                "step": step.get("step"),
                "command": step.get("command", []),
                "rc": None,
                "seconds": 0.0,
                "stdout_tail": "",
                "stderr_tail": "",
                "expected_artifacts": step.get("expected_artifacts", []),
                "present_artifacts": [],
                "missing_artifacts": step.get("expected_artifacts", []),
                "stop_condition": step.get("stop_condition"),
                "status": "blocked",
                "blocked_by": deny_reasons,
            }
            result["failure_kind"] = classify_failure(result)
            results.append(result)
            overall_status = "blocked"
            break

        result = run_step(step, repo_root)
        results.append(result)
        if result["status"] != "passed":
            overall_status = "failed"
            break

    payload = {
        "schema_version": 1,
        "plan_source": args.input,
        "overall_status": overall_status,
        "results": results,
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
