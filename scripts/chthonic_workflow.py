#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Chthonic workflow runner.

Orchestrates higher-level development profiles from existing control-plane
commands so the archive can execute compound tasks instead of bouncing
between micro-commands.

@SID:           TOOL_CHTHONIC_WORKFLOW_V1
@Purpose:       Run sequenced higher-level workflow profiles for the archive.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"


def which_or_fallback(name: str, fallback: str) -> str:
    resolved = shutil.which(name)
    return resolved if resolved else fallback


PWSH = which_or_fallback("pwsh", r"C:\Program Files\PowerShell\7\pwsh.exe")
UV = which_or_fallback("uv", str(Path.home() / ".local" / "bin" / "uv.exe"))
BUN = which_or_fallback("bun", str(Path.home() / ".bun" / "bin" / "bun.exe"))


@dataclass
class StepResult:
    step_id: str
    command: list[str]
    exit_code: int
    duration_seconds: float
    stdout: str
    stderr: str


@dataclass
class WorkflowReport:
    profile: str
    generated_at: str
    step_count: int
    failed_step_count: int
    steps: list[StepResult]


def chthonic_cmd(*args: str) -> list[str]:
    return [PWSH, "-NoLogo", "-NoProfile", "-File", str(SCRIPTS_DIR / "chthonic.ps1"), *args]


def uv_cmd(*args: str) -> list[str]:
    return [UV, "run", *args]


def bun_cmd(*args: str) -> list[str]:
    return [BUN, *args]


WORKFLOWS: dict[str, list[tuple[str, list[str]]]] = {
    "control-plane": [
        ("status_json", chthonic_cmd("status", "--json")),
        ("shell_probe_json", chthonic_cmd("shell", "probe", "--json")),
        ("ssot_queue_json", uv_cmd(str(SCRIPTS_DIR / "ssot_loremaster.py"), "queue", "--json")),
        ("ssot_drift_json", uv_cmd(str(SCRIPTS_DIR / "ssot_loremaster.py"), "drift", "--json")),
        ("ssot_lineage_json", uv_cmd(str(SCRIPTS_DIR / "ssot_loremaster.py"), "lineage", "--json")),
        ("mcp_tool_names", bun_cmd(str(SCRIPTS_DIR / "mcp-chthonic-server.ts"), "--list-names-only")),
    ],
    "toolchain-governance": [
        ("doctor_dry_run", chthonic_cmd("doctor", "--dry-run")),
        ("doctor_origins", chthonic_cmd("doctor", "--origins")),
        ("shell_probe_json", chthonic_cmd("shell", "probe", "--json")),
        ("status_json", chthonic_cmd("status", "--json")),
        ("toolchain_probe", [PWSH, "-NoLogo", "-NoProfile", "-File", str(SCRIPTS_DIR / "probe_toolchain_path.ps1")]),
    ],
}


def run_step(step_id: str, command: list[str]) -> StepResult:
    start = time.perf_counter()
    proc = subprocess.run(
        command,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    duration = time.perf_counter() - start
    return StepResult(
        step_id=step_id,
        command=command,
        exit_code=proc.returncode,
        duration_seconds=duration,
        stdout=proc.stdout,
        stderr=proc.stderr,
    )


def build_report(profile: str) -> WorkflowReport:
    steps = [run_step(step_id, command) for step_id, command in WORKFLOWS[profile]]
    failed = sum(1 for step in steps if step.exit_code != 0)
    return WorkflowReport(
        profile=profile,
        generated_at=datetime.now(UTC).isoformat(),
        step_count=len(steps),
        failed_step_count=failed,
        steps=steps,
    )


def report_to_json(report: WorkflowReport) -> str:
    payload = asdict(report)
    payload["steps"] = [asdict(step) for step in report.steps]
    return json.dumps(payload, indent=2, ensure_ascii=False)


def report_to_markdown(report: WorkflowReport) -> str:
    lines = [
        f"# Chthonic Workflow Report: {report.profile}",
        "",
        f"- Generated: `{report.generated_at}`",
        f"- Steps: `{report.step_count}`",
        f"- Failed: `{report.failed_step_count}`",
        "",
        "| Step | Exit | Duration | Command |",
        "|---|---:|---:|---|",
    ]
    for step in report.steps:
        cmd = " ".join(step.command).replace("|", "\\|")
        lines.append(f"| `{step.step_id}` | `{step.exit_code}` | `{step.duration_seconds:.2f}s` | `{cmd}` |")
    lines.append("")
    lines.append("## Step Output")
    lines.append("")
    for step in report.steps:
        lines.append(f"### {step.step_id}")
        lines.append("")
        lines.append(f"- Exit: `{step.exit_code}`")
        lines.append(f"- Duration: `{step.duration_seconds:.2f}s`")
        lines.append("")
        if step.stdout.strip():
            lines.append("```text")
            lines.append(step.stdout.rstrip())
            lines.append("```")
            lines.append("")
        if step.stderr.strip():
            lines.append("```text")
            lines.append(step.stderr.rstrip())
            lines.append("```")
            lines.append("")
    return "\n".join(lines)


def default_output_dir() -> Path:
    stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%SZ")
    return REPO_ROOT / "dumpster-dive" / "intake" / "chthonic-workflows" / stamp


def main() -> int:
    parser = argparse.ArgumentParser(description="Run higher-level Chthonic workflow profiles.")
    parser.add_argument("profile", choices=sorted(WORKFLOWS.keys()))
    parser.add_argument("--json", action="store_true", help="Emit JSON to stdout.")
    parser.add_argument("--write", action="store_true", help="Write markdown/json artifacts under dumpster-dive/intake/chthonic-workflows/.")
    args = parser.parse_args()

    report = build_report(args.profile)

    if args.write:
        out_dir = default_output_dir()
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "report.json").write_text(report_to_json(report), encoding="utf-8")
        (out_dir / "report.md").write_text(report_to_markdown(report), encoding="utf-8")
        print(str(out_dir))

    if args.json:
        print(report_to_json(report))
    else:
        print(report_to_markdown(report))

    return 1 if report.failed_step_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
