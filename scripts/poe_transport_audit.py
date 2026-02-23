#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Poe transport audit.

Compares OpenAI-compatible lane vs Poe SDK lane on selected accounts and bots/models.

@SID:           TOOL_POE_TRANSPORT_AUDIT_V1
@Type:          Utility
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class ProbeResult:
    rc: int
    ok: bool
    text_preview: str | None
    error: str | None


@dataclass
class AccountAudit:
    account: str
    openai_control: ProbeResult
    openai_app_creator: ProbeResult
    sdk_control: ProbeResult
    sdk_app_creator: ProbeResult
    openai_models_count: int | None
    openai_has_app_creator: bool | None


@dataclass
class TransportAudit:
    schema_version: int
    generated_on: str
    control_model: str
    target_bot: str
    accounts: list[AccountAudit]
    recommendation: str
    rationale: str


def now_utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def parse_mailboxes(value: str) -> list[str]:
    allowed = {"codex", "claude"}
    ordered: list[str] = []
    for chunk in (value or "").split(","):
        name = chunk.strip().lower()
        if not name or name not in allowed:
            continue
        if name not in ordered:
            ordered.append(name)
    if not ordered:
        ordered.append("codex")
    return ordered


def run_cmd(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def parse_json_line(stdout: str) -> dict[str, Any] | None:
    text = stdout.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        return None


def probe_openai(account: str, model: str, prompt: str, effort: str = "") -> ProbeResult:
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "poe_lane.py"),
        "--mode",
        "probe",
        "--account",
        account,
        "--model",
        model,
        "--prompt",
        prompt,
        "--json",
    ]
    if effort.strip():
        cmd.extend(["--effort", effort.strip()])
    rc, out, err = run_cmd(cmd)
    payload = parse_json_line(out)
    if rc == 0 and isinstance(payload, dict):
        text = payload.get("text")
        return ProbeResult(rc=rc, ok=True, text_preview=(str(text)[:300] if text is not None else None), error=None)
    message = (out.strip() or err.strip() or "probe_failed").strip()
    return ProbeResult(rc=rc, ok=False, text_preview=None, error=message[:400])


def probe_sdk(account: str, bot: str, prompt: str) -> ProbeResult:
    rc, out, err = run_cmd(
        [
            "uv",
            "run",
            "--with",
            "fastapi-poe",
            str(REPO_ROOT / "scripts" / "poe_sdk_lane.py"),
            "--account",
            account,
            "--bot",
            bot,
            "--prompt",
            prompt,
            "--json",
        ]
    )
    payload = parse_json_line(out)
    if rc == 0 and isinstance(payload, dict):
        text = payload.get("text")
        return ProbeResult(rc=rc, ok=True, text_preview=(str(text)[:300] if text is not None else None), error=None)
    message = (out.strip() or err.strip() or "probe_failed").strip()
    return ProbeResult(rc=rc, ok=False, text_preview=None, error=message[:400])


def inspect_openai_models(account: str, limit: int) -> tuple[int | None, bool | None]:
    rc, out, _err = run_cmd(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "poe_lane.py"),
            "--mode",
            "models",
            "--account",
            account,
            "--limit",
            str(limit),
            "--json",
        ]
    )
    if rc != 0:
        return None, None
    payload = parse_json_line(out)
    if not isinstance(payload, dict):
        return None, None
    models = payload.get("models")
    if not isinstance(models, list):
        return None, None
    has_app_creator = any(isinstance(m, str) and m.lower() == "app-creator" for m in models)
    return len(models), has_app_creator


def choose_recommendation(report: TransportAudit) -> tuple[str, str]:
    any_openai_app = any(a.openai_app_creator.ok for a in report.accounts)
    any_sdk_app = any(a.sdk_app_creator.ok for a in report.accounts)
    any_openai_control = any(a.openai_control.ok for a in report.accounts)
    any_sdk_control = any(a.sdk_control.ok for a in report.accounts)

    if any_openai_app and not any_sdk_app:
        return ("openai-compatible", "App-Creator works on OpenAI-compatible lane; SDK did not match.")
    if any_sdk_app and not any_openai_app:
        return ("poe-sdk", "App-Creator works on Poe SDK lane; OpenAI-compatible did not match.")
    if any_openai_app and any_sdk_app:
        return ("openai-compatible", "Both lanes can access App-Creator; OpenAI-compatible is better for cross-tool portability.")

    if any_openai_control and not any_sdk_control:
        return (
            "openai-compatible",
            "Control probes work on OpenAI-compatible lane while SDK control probes failed.",
        )
    if any_openai_control and any_sdk_control:
        return (
            "openai-compatible",
            "Both lanes work for control probes, but App-Creator is not API-accessible on tested keys.",
        )
    return ("indeterminate", "Neither lane passed control probes consistently; re-check account credits and API permissions.")


def write_mailbox(report: TransportAudit, mailboxes: list[str]) -> None:
    json_payload = json.dumps(asdict(report), indent=2) + "\n"

    lines = [
        "# Poe Transport Audit",
        "",
        f"- Generated: `{report.generated_on}`",
        f"- Control model: `{report.control_model}`",
        f"- Target bot: `{report.target_bot}`",
        f"- Recommendation: `{report.recommendation}`",
        f"- Rationale: `{report.rationale}`",
        "",
        "## Accounts",
    ]
    for acc in report.accounts:
        lines.append(f"- Account `{acc.account}`")
        lines.append(f"  - OpenAI control ok: `{acc.openai_control.ok}`")
        lines.append(f"  - OpenAI app-creator ok: `{acc.openai_app_creator.ok}`")
        lines.append(f"  - SDK control ok: `{acc.sdk_control.ok}`")
        lines.append(f"  - SDK app-creator ok: `{acc.sdk_app_creator.ok}`")
        lines.append(f"  - OpenAI model count inspected: `{acc.openai_models_count}`")
        lines.append(f"  - OpenAI has app-creator id: `{acc.openai_has_app_creator}`")

    md_payload = "\n".join(lines).rstrip() + "\n"

    for mailbox in mailboxes:
        out_dir = REPO_ROOT / mailbox / "mailbox"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "POE_TRANSPORT_AUDIT_LATEST.json").write_text(json_payload, encoding="utf-8")
        (out_dir / "POE_TRANSPORT_AUDIT_LATEST.md").write_text(md_payload, encoding="utf-8")


def parse_accounts(raw: str) -> list[str]:
    out: list[str] = []
    for token in (raw or "").split(","):
        v = token.strip()
        if v in {"1", "2"} and v not in out:
            out.append(v)
    if not out:
        out = ["1", "2"]
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit Poe OpenAI-compatible lane vs Poe SDK lane.")
    ap.add_argument("--accounts", default="1,2", help="Comma-separated account list from {1,2}.")
    ap.add_argument("--control-model", default="claude-sonnet-4.5")
    ap.add_argument("--target-bot", default="app-creator")
    ap.add_argument("--prompt", default="Return exactly: OK")
    ap.add_argument("--models-limit", type=int, default=400)
    ap.add_argument("--emit-mailbox", action="store_true")
    ap.add_argument("--mailboxes", default="codex,claude")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    accounts = parse_accounts(args.accounts)
    results: list[AccountAudit] = []
    for account in accounts:
        openai_control = probe_openai(account=account, model=args.control_model, prompt=args.prompt)
        openai_app = probe_openai(account=account, model=args.target_bot, prompt=args.prompt, effort="max")
        sdk_control = probe_sdk(account=account, bot=args.control_model, prompt=args.prompt)
        sdk_app = probe_sdk(account=account, bot=args.target_bot, prompt=args.prompt)
        models_count, has_app_creator = inspect_openai_models(account=account, limit=max(1, int(args.models_limit)))
        results.append(
            AccountAudit(
                account=account,
                openai_control=openai_control,
                openai_app_creator=openai_app,
                sdk_control=sdk_control,
                sdk_app_creator=sdk_app,
                openai_models_count=models_count,
                openai_has_app_creator=has_app_creator,
            )
        )

    report = TransportAudit(
        schema_version=1,
        generated_on=now_utc(),
        control_model=args.control_model,
        target_bot=args.target_bot,
        accounts=results,
        recommendation="",
        rationale="",
    )
    recommendation, rationale = choose_recommendation(report)
    report.recommendation = recommendation
    report.rationale = rationale

    if args.emit_mailbox:
        write_mailbox(report, parse_mailboxes(args.mailboxes))

    if args.json:
        print(json.dumps(asdict(report), ensure_ascii=True))
    else:
        print(f"recommendation={report.recommendation}")
        print(f"rationale={report.rationale}")
        for acc in report.accounts:
            print(
                "account="
                + acc.account
                + f" openai_control={acc.openai_control.ok}"
                + f" openai_app_creator={acc.openai_app_creator.ok}"
                + f" sdk_control={acc.sdk_control.ok}"
                + f" sdk_app_creator={acc.sdk_app_creator.ok}"
                + f" models_has_app_creator={acc.openai_has_app_creator}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
