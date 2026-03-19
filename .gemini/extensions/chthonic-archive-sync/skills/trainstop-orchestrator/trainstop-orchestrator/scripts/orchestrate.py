#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: orchestrate.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🔥 THE FOUNDRY
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Trainstop Orchestrator.

Runs a deterministic maintenance chain without touching official OpenAI skills.

Invocation:
  uv run .codex/skills/trainstop-orchestrator/scripts/orchestrate.py --target both [--apply]
  uv run .codex/skills/trainstop-orchestrator/scripts/orchestrate.py --lane mcp-auth

@SID:           TOOL_TRAINSTOP_ORCHESTRATOR_V1
@Shabti:          Utility
@Purpose:       Trainstop Orchestrator.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for p in [cur, *cur.parents]:
        if (p / "pyproject.toml").exists() and (p / "AGENTS.md").exists():
            return p
    return start.resolve().parents[4]


REPO_ROOT = find_repo_root(Path(__file__))


@dataclass(frozen=True)
class Step:
    name: str
    cmd: list[str]
    timeout_s: float | None = None
    expect_artifacts: list[str] | None = None


@dataclass
class StepResult:
    name: str
    cmd: list[str]
    rc: int
    seconds: float
    stdout: str
    stderr: str
    missing_artifacts: list[str]
    notes: list[str]


def run_step(step: Step) -> StepResult:
    print(f"\n=== {step.name} ===")
    print(" ".join(step.cmd))
    t0 = time.time()
    try:
        proc = subprocess.run(
            step.cmd,
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=step.timeout_s,
        )
    except subprocess.TimeoutExpired as e:
        dt = time.time() - t0
        return StepResult(
            name=step.name,
            cmd=step.cmd,
            rc=124,
            seconds=dt,
            stdout=(e.stdout or "") if isinstance(e.stdout, str) else "",
            stderr=(e.stderr or "") if isinstance(e.stderr, str) else "TimeoutExpired",
            missing_artifacts=[],
            notes=[f"timeout_s={step.timeout_s}"],
        )
    dt = time.time() - t0
    if proc.returncode != 0:
        print(f"FAILED: {step.name} (exit {proc.returncode})")
    # Keep console noise bounded; details go into report.
    if proc.stdout.strip():
        print(proc.stdout.strip().splitlines()[-1])
    if proc.stderr.strip():
        print(proc.stderr.strip().splitlines()[-1])
    return StepResult(
        name=step.name,
        cmd=step.cmd,
        rc=proc.returncode,
        seconds=dt,
        stdout=proc.stdout or "",
        stderr=proc.stderr or "",
        missing_artifacts=[],
        notes=[],
    )


def read_stamps(path: Path) -> list[dict]:
    try:
        obj = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return []
    recs = obj.get("records")
    if isinstance(recs, list):
        return [r for r in recs if isinstance(r, dict)]
    return []


def has_blocking_issues(stamps: list[dict]) -> bool:
    for r in stamps:
        sev = r.get("severity")
        if sev in {"CRITICAL", "WARN"}:
            return True
    return False


def write_report(path: Path, results: list[StepResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "generated_on": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "results": [
            {
                "name": r.name,
                "rc": r.rc,
                "seconds": round(r.seconds, 3),
                "cmd": r.cmd,
                "stdout_tail": "\n".join((r.stdout or "").splitlines()[-30:]),
                "stderr_tail": "\n".join((r.stderr or "").splitlines()[-30:]),
                "missing_artifacts": list(r.missing_artifacts),
                "notes": list(r.notes),
            }
            for r in results
        ],
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")


def pwsh_cmd(command: str) -> list[str]:
    return ["pwsh", "-NoProfile", "-Command", command]


def load_lane_config(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    if not isinstance(obj, dict):
        raise SystemExit(f"Invalid lane config: expected object at {path.as_posix()}")
    return obj


def expand_lane_steps(cfg: dict[str, Any], lane_name: str) -> list[str]:
    lanes = cfg.get("lanes")
    if not isinstance(lanes, dict):
        raise SystemExit("Invalid lane config: missing lanes object")
    lane = lanes.get(lane_name)
    if not isinstance(lane, dict):
        raise SystemExit(f"Lane not found: {lane_name}")
    steps = lane.get("steps")
    if not isinstance(steps, list):
        raise SystemExit(f"Invalid lane '{lane_name}': missing steps[]")

    out: list[str] = []
    for s in steps:
        if not isinstance(s, str):
            continue
        # Allow nesting by lane name.
        if s in lanes:
            out.extend(expand_lane_steps(cfg, s))
        else:
            out.append(s)
    return out


def render_command_from_def(defn: dict[str, Any], input_path: str | None) -> list[str]:
    if "command" in defn:
        cmd = defn["command"]
        if not isinstance(cmd, list) or not all(isinstance(x, str) for x in cmd):
            raise SystemExit("Invalid definition: command must be string list")
        return list(cmd)

    if "command_template" in defn:
        if not input_path:
            raise SystemExit("This lane requires --input-path because a step uses command_template.")
        tmpl = defn["command_template"]
        if not isinstance(tmpl, list) or not all(isinstance(x, str) for x in tmpl):
            raise SystemExit("Invalid definition: command_template must be string list")
        return [x.format(input_path=input_path) for x in tmpl]

    raise SystemExit("Invalid definition: missing command or command_template")


def artifacts_from_def(defn: dict[str, Any], input_path: str | None) -> list[str]:
    arts: list[str] = []
    a = defn.get("artifacts")
    if isinstance(a, list):
        arts.extend([x for x in a if isinstance(x, str)])
    at = defn.get("artifacts_template")
    if at is not None:
        if not input_path:
            return arts
        if isinstance(at, list):
            arts.extend([x.format(input_path=input_path) for x in at if isinstance(x, str)])
    return arts


def validate_artifacts(artifacts: list[str]) -> list[str]:
    """
    Validate expected artifacts. Supports simple glob patterns like foo_*.md.
    Paths are treated as repo-relative unless absolute.
    """
    missing: list[str] = []
    for a in artifacts:
        if not a or not isinstance(a, str):
            continue
        p = Path(a)
        base = p if p.is_absolute() else (REPO_ROOT / p)
        # Glob support: any wildcard triggers parent glob.
        if any(ch in a for ch in ("*", "?", "[")):
            parent = base.parent if base.parent != Path("") else REPO_ROOT
            pat = base.name
            hits = list(parent.glob(pat))
            if not hits:
                missing.append(a)
            continue
        if not base.exists():
            missing.append(a)
    return missing


def _glob_hits(artifact: str) -> set[Path]:
    p = Path(artifact)
    base = p if p.is_absolute() else (REPO_ROOT / p)
    parent = base.parent if base.parent != Path("") else REPO_ROOT
    pat = base.name
    return {x.resolve() for x in parent.glob(pat)}


def validate_artifacts_fresh(artifacts: list[str], pre_globs: dict[str, set[Path]]) -> list[str]:
    """
    For glob artifacts, require that at least one *new* file appears vs pre-run snapshot.
    This prevents false-green when the repo already has old artifacts matching the glob.
    Returns a list of glob patterns that did not produce any new matches.
    """
    stale: list[str] = []
    for a in artifacts:
        if not a or not isinstance(a, str):
            continue
        if not any(ch in a for ch in ("*", "?", "[")):
            continue
        before = pre_globs.get(a, set())
        after = _glob_hits(a)
        if not (after - before):
            stale.append(a)
    return stale


def apply_mode_transform(step_name: str, cmd: list[str], apply: bool) -> list[str]:
    if not apply:
        return cmd
    # Conservative transform: if a command contains "--mode verify", replace verify -> apply.
    # This keeps config v1 simple and predictable.
    if "--mode" in cmd:
        out = list(cmd)
        try:
            midx = out.index("--mode")
            if midx + 1 < len(out) and out[midx + 1] == "verify":
                out[midx + 1] = "apply"
        except ValueError:
            pass
        return out
    return cmd


def step_enabled_for_run(defn: dict[str, Any], target: str, apply: bool) -> bool:
    targets = defn.get("targets")
    if isinstance(targets, list):
        allowed = {str(x).lower() for x in targets if isinstance(x, str)}
        if target.lower() not in allowed:
            return False
    requires_apply = defn.get("requires_apply")
    if isinstance(requires_apply, bool) and requires_apply and not apply:
        return False
    return True


def mailboxes_for_target(target: str) -> str:
    t = target.lower()
    if t == "codex":
        return "codex"
    if t == "claude":
        return "claude"
    return "codex,claude"


def load_local_pool_env() -> dict[str, str]:
    pool_path = Path.home() / ".chthonic" / "api_pool.json"
    if not pool_path.exists():
        return {}
    try:
        obj = json.loads(pool_path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}
    env = obj.get("env")
    if not isinstance(env, dict):
        return {}
    out: dict[str, str] = {}
    for k, v in env.items():
        if isinstance(v, str):
            cleaned = v.strip()
            if cleaned:
                out[k] = cleaned
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", choices=["codex", "claude", "both"], required=True)
    ap.add_argument("--apply", action="store_true", help="Enable safe apply modes where supported.")
    ap.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="When --apply is set, retry polish/apply until clean (or max iterations).",
    )
    ap.add_argument(
        "--lane",
        choices=[
            "maintenance",
            "mcp-auth",
            "hf-discovery",
            "mcp-client-emitter",
            "hf-prep",
            "local-ai-readiness",
            "poe-smoke",
            "all",
        ],
        default="maintenance",
        help="Which lane to run. 'all' runs maintenance + mcp-auth + local-ai-readiness + poe-smoke.",
    )
    ap.add_argument(
        "--lane-config",
        help="Optional path to a declarative lane config JSON. When provided, lanes/steps are executed from this file.",
    )
    ap.add_argument(
        "--input-path",
        help="Input path for lanes that require templates (e.g., resume lane in lane_config.v1.json).",
    )
    args = ap.parse_args()

    steps: list[Step] = []

    # Config-driven mode: execute lanes/steps from JSON, with minimal apply-mode transform.
    if args.lane_config:
        cfg_path = Path(args.lane_config)
        cfg = load_lane_config(cfg_path)
        defs = cfg.get("definitions")
        if not isinstance(defs, dict):
            raise SystemExit("Invalid lane config: missing definitions object")
        step_names = expand_lane_steps(cfg, args.lane)
        for sname in step_names:
            defn = defs.get(sname)
            if not isinstance(defn, dict):
                raise SystemExit(f"Definition not found for step: {sname}")
            if not step_enabled_for_run(defn, args.target, bool(args.apply)):
                continue
            cmd = render_command_from_def(defn, args.input_path)
            cmd = apply_mode_transform(sname, cmd, bool(args.apply))
            timeout_s = defn.get("timeout_s")
            tval = None
            if isinstance(timeout_s, (int, float)) and timeout_s > 0:
                tval = float(timeout_s)
            arts = artifacts_from_def(defn, args.input_path)
            steps.append(Step(f"CFG:{sname}", cmd, timeout_s=tval, expect_artifacts=arts))

        failures = 0
        results: list[StepResult] = []
        for s in steps:
            pre_globs: dict[str, set[Path]] = {}
            if s.expect_artifacts:
                # Snapshot glob hits before running, so we can require fresh emission.
                for a in s.expect_artifacts:
                    if isinstance(a, str) and any(ch in a for ch in ("*", "?", "[")):
                        pre_globs[a] = _glob_hits(a)
            r = run_step(s)
            if s.expect_artifacts:
                r.missing_artifacts = validate_artifacts(s.expect_artifacts)
                stale_globs = validate_artifacts_fresh(s.expect_artifacts, pre_globs)
                if stale_globs:
                    r.notes.append(f"no_new_artifacts_for_globs:{','.join(stale_globs)}")
                    if r.rc == 0:
                        r.rc = 3
                if r.missing_artifacts:
                    r.notes.append("missing_expected_artifacts")
                    if r.rc == 0:
                        r.rc = 3
            results.append(r)
            if r.rc != 0:
                failures += 1
                break

        report = Path("codex/mailbox/TRAINSTOP_ORCHESTRATOR_LATEST.json")
        write_report(REPO_ROOT / report, results)
        return 0 if failures == 0 else 2

    api_mgr = ".codex/skills/api-manager/scripts/api_manager.ps1"
    api_mgr_exists = (REPO_ROOT / api_mgr).exists()
    polisher = ".codex/skills/skill-polisher/scripts/polish_skill.py"

    def with_auth_loaded(inner: str) -> list[str]:
        if api_mgr_exists:
            return pwsh_cmd(rf".\.codex\skills\api-manager\scripts\api_manager.ps1 -Load | Out-Null; {inner}")
        return pwsh_cmd(rf".\scripts\api_pool.ps1 -Load | Out-Null; {inner}")

    def add_maintenance_lane() -> None:
        nonlocal steps
        # 0) Skill freshness gate (Codex skills): stale unsafe patterns + refresh drift.
        steps.append(
            Step(
                "Skill Freshness Gate (Codex)",
                [
                    "uv",
                    "run",
                    ".codex/skills/trainstop-orchestrator/scripts/skill_freshness_gate.py",
                    "--skills-root",
                    ".codex/skills",
                    "--emit-json",
                    "codex/mailbox/SKILL_FRESHNESS_LATEST.json",
                    "--emit-md",
                    "codex/mailbox/SKILL_FRESHNESS_LATEST.md",
                    "--strict",
                ],
            )
        )

        # 1) Auth drift doctor (non-fatal). Runs only local checks; never prints secrets.
        if api_mgr_exists:
            steps.append(Step("API Manager (Doctor)", ["pwsh", "-NoProfile", "-File", api_mgr, "-Doctor"]))

        # 2) Toolchain health.
        td = ["uv", "run", ".codex/skills/toolchain-doctor/scripts/toolchain_doctor.py", "--bun", "--uv"]
        if args.apply:
            td.append("--apply")
        steps.append(Step("Toolchain Doctor", td))

        # 3) Codex skill integrity (optionally iterative in --apply mode).
        steps.append(
            Step(
                "Skill Polisher (Codex on Codex)",
                [
                    "uv",
                    "run",
                    polisher,
                    ".codex/skills",
                    "--all",
                    "--mode",
                    "verify" if not args.apply else "apply",
                    "--target-flavor",
                    "codex",
                    "--subprocess-fix",
                    "--emit-stamps-json",
                    "codex/mailbox/tatragrammatron_stamps_latest_codex.json",
                    "--emit-summary-md",
                    "codex/mailbox/TATRAGRAMMATRON_SUMMARY_LATEST_CODEX.md",
                ],
            )
        )

        # 4) Optional cross recon (Codex runner validating Claude tree).
        if args.target in ("claude", "both"):
            steps.append(
                Step(
                    "Skill Polisher (Claude contract on Claude skills)",
                    [
                        "uv",
                        "run",
                        polisher,
                        ".claude/skills",
                        "--all",
                        "--mode",
                        "verify",
                        "--target-flavor",
                        "claude",
                        "--subprocess-fix",
                        "--no-require-assets",
                    ],
                )
            )

        # 5) Mailbox hygiene.
        for tgt in (["codex"] if args.target == "codex" else ["claude"] if args.target == "claude" else ["codex", "claude"]):
            steps.append(Step(f"Mailbox Polisher ({tgt})", ["uv", "run", "scripts/mailbox_polisher.py", "--target", tgt, "--apply"]))

        # 6) Packet refresh.
        if args.target in ("codex", "both"):
            steps.append(
                Step(
                    "Mailbox Scribe (codex)",
                    ["uv", "run", "scripts/mailbox_scribe.py", "--target", "codex", "--packet", "codex/mailbox/TETRAGRAMMATON_PACKET.md"],
                )
            )
        if args.target in ("claude", "both"):
            steps.append(
                Step(
                    "Mailbox Scribe (claude)",
                    ["uv", "run", "scripts/mailbox_scribe.py", "--target", "claude", "--packet", "claude/mailbox/TETRAGRAMMATON_PACKET.md"],
                )
            )

        # 7) Contract check.
        steps.append(Step("Mailbox Manifest Check", ["uv", "run", "scripts/check_mailbox_manifest.py"]))

    def add_mcp_auth_lane() -> None:
        nonlocal steps
        # MCP server status (global codex config).
        steps.append(Step("Codex MCP List", ["codex", "mcp", "list"]))
        # HF probe must run in the same process that loads env vars.
        # Prefer canonical API manager loader, fallback to legacy loader.
        steps.append(
            Step(
                "HF Probe (Auth Loaded)",
                with_auth_loaded("uv run scripts/hf_probe.py"),
            )
        )
        steps.append(Step("MCP Validation Runner (local)", ["bun", "run", "scripts/run_mcp_validation.ts"]))

    def add_hf_discovery_lane() -> None:
        nonlocal steps
        steps.append(
            Step(
                "HF Discovery (spaces/session ops)",
                with_auth_loaded(r"uv run scripts/hf_discovery.py --kind spaces --q 'mcp tools gradio text extraction ocr' --limit 10"),
            )
        )

    def add_mcp_client_emitter_lane() -> None:
        nonlocal steps
        steps.append(
            Step(
                "HF MCP Client Emitter",
                with_auth_loaded("uv run scripts/mcp_client_emitter.py --url https://huggingface.co/mcp --min-despair 0"),
            )
        )

    def add_hf_prep_lane() -> None:
        nonlocal steps
        steps.append(
            Step(
                "HF Prep (verify)",
                with_auth_loaded("uv run scripts/hf_prep.py --with transformers,datasets,accelerate"),
            )
        )
        if args.apply:
            steps.append(
                Step(
                    "HF Prep (apply)",
                    with_auth_loaded("uv run scripts/hf_prep.py --apply --with transformers,datasets,accelerate --strict"),
                    timeout_s=1800,
                )
            )

    def add_local_ai_readiness_lane() -> None:
        nonlocal steps
        steps.append(
            Step(
                "Local AI Readiness",
                [
                    "uv",
                    "run",
                    ".codex/skills/trainstop-orchestrator/scripts/local_ai_readiness.py",
                    "--mailboxes",
                    mailboxes_for_target(args.target),
                ],
            )
        )

    def add_poe_smoke_lane() -> None:
        nonlocal steps
        pool_env = load_local_pool_env()
        mailbox_targets = mailboxes_for_target(args.target)
        added = 0
        available_accounts: list[str] = []

        for account in ("1", "2"):
            slot = f"POE_API_KEY_{account}"
            val = os.getenv(slot) or pool_env.get(slot)
            if not val:
                continue
            available_accounts.append(account)
            steps.append(
                Step(
                    f"Poe Models (account {account})",
                    [
                        "uv",
                        "run",
                        "scripts/poe_lane.py",
                        "--mode",
                        "models",
                        "--account",
                        account,
                        "--limit",
                        "5",
                        "--emit-mailbox",
                        "--mailboxes",
                        mailbox_targets,
                    ],
                )
            )
            added += 1

        if added == 0:
            direct = os.getenv("POE_API_KEY") or pool_env.get("POE_API_KEY")
            if direct:
                steps.append(
                    Step(
                        "Poe Models (active key)",
                        [
                            "uv",
                            "run",
                            "scripts/poe_lane.py",
                            "--mode",
                            "models",
                            "--limit",
                            "5",
                            "--emit-mailbox",
                            "--mailboxes",
                            mailbox_targets,
                        ],
                    )
                )
                added += 1

        if available_accounts:
            steps.append(
                Step(
                    "Poe Transport Audit",
                    [
                        "uv",
                        "run",
                        "scripts/poe_transport_audit.py",
                        "--accounts",
                        ",".join(available_accounts),
                        "--emit-mailbox",
                        "--mailboxes",
                        mailbox_targets,
                    ],
                )
            )

        if added == 0:
            print("\n=== Poe Smoke Lane ===")
            print("skip: no POE_API_KEY / POE_API_KEY_1 / POE_API_KEY_2 in env or local pool.")

    if args.lane in ("maintenance", "all"):
        add_maintenance_lane()
    if args.lane in ("mcp-auth", "all"):
        add_mcp_auth_lane()
    if args.lane == "hf-discovery":
        add_hf_discovery_lane()
    if args.lane == "mcp-client-emitter":
        add_mcp_client_emitter_lane()
    if args.lane == "hf-prep":
        add_hf_prep_lane()
    if args.lane in ("local-ai-readiness", "all"):
        add_local_ai_readiness_lane()
    if args.lane in ("poe-smoke", "all"):
        add_poe_smoke_lane()

    failures = 0
    results: list[StepResult] = []
    codex_stamps = Path("codex/mailbox/tatragrammatron_stamps_latest_codex.json")
    for s in steps:
        r = run_step(s)
        results.append(r)
        if r.rc != 0:
            failures += 1

        # If we're applying fixes, re-run skill-polisher until clean (or max iterations).
        if args.apply and s.name == "Skill Polisher (Codex on Codex)":
            for i in range(1, max(1, args.max_iterations)):
                stamps = read_stamps(REPO_ROOT / codex_stamps)
                if not has_blocking_issues(stamps):
                    break
                r2 = run_step(
                    Step(
                        f"Skill Polisher (Codex on Codex) retry {i+1}/{args.max_iterations}",
                        [
                            "uv",
                            "run",
                            polisher,
                            ".codex/skills",
                            "--all",
                            "--mode",
                            "apply",
                            "--target-flavor",
                            "codex",
                            "--subprocess-fix",
                            "--emit-stamps-json",
                            str(codex_stamps.as_posix()),
                            "--emit-summary-md",
                            "codex/mailbox/TATRAGRAMMATRON_SUMMARY_LATEST_CODEX.md",
                        ],
                    )
                )
                results.append(r2)
                if r2.rc != 0:
                    failures += 1
                    break

    # Consolidated report (machine-readable).
    report = Path("codex/mailbox/TRAINSTOP_ORCHESTRATOR_LATEST.json")
    write_report(REPO_ROOT / report, results)

    return 0 if failures == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
