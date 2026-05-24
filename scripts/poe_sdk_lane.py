#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: poe_sdk_lane.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
poe_sdk_lane.py — Poe SDK lane helper (fastapi_poe transport).

@SID:           TOOL_POE_SDK_LANE_V1
@Shabti:        CLI Script
@Purpose:       Poe SDK lane helper using fastapi_poe transport. Connects
                to Poe bots via the SDK pathway for direct bot interaction
                with shared process-env then pool-file credential resolution.
                Usage: uv run --with fastapi-poe scripts/poe_sdk_lane.py --account 1 --bot app-creator
"""

from __future__ import annotations


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import argparse
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from scripts.lib.poe_auth import account_arg, resolve_poe_credentials

REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class PoeSdkReport:
    schema_version: int
    generated_on: str
    transport: str
    account: str | None
    bot: str
    auth_source: str
    account_source: str
    selected_name: str | None
    ok: bool
    error: str | None
    response_preview: str | None


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


def write_mailbox(report: PoeSdkReport, mailboxes: list[str]) -> None:
    lines = [
        "# Poe SDK Latest",
        "",
        f"- Generated: `{report.generated_on}`",
        f"- Transport: `{report.transport}`",
        f"- Account: `{report.account}`",
        f"- Bot: `{report.bot}`",
        f"- Auth source: `{report.auth_source}`",
        f"- Account source: `{report.account_source}`",
        f"- Selected name: `{report.selected_name}`",
        f"- OK: `{report.ok}`",
    ]
    if report.error:
        lines.append(f"- Error: `{report.error}`")
    if report.response_preview:
        lines.append(f"- Preview: `{report.response_preview}`")
    md_payload = "\n".join(lines).rstrip() + "\n"
    json_payload = json.dumps(asdict(report), indent=2) + "\n"

    for mailbox in mailboxes:
        out_dir = REPO_ROOT / mailbox / "mailbox"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "POE_SDK_LATEST.json").write_text(json_payload, encoding="utf-8")
        (out_dir / "POE_SDK_LATEST.md").write_text(md_payload, encoding="utf-8")


def run_probe(bot: str, prompt: str, token: str, effort: str | None) -> str:
    try:
        import fastapi_poe as fp  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "fastapi_poe not installed — run: uv run --with fastapi-poe scripts/poe_sdk_lane.py ..."
        ) from e

    msg_kwargs: dict[str, object] = {"role": "user", "content": prompt}
    if effort and effort.strip():
        msg_kwargs["parameters"] = {"effort": effort.strip()}

    message = fp.ProtocolMessage(**msg_kwargs)
    pieces: list[str] = []
    for partial in fp.get_bot_response_sync(messages=[message], bot_name=bot, api_key=token):
        text = getattr(partial, "text", None)
        if isinstance(text, str) and text:
            pieces.append(text)
    return "".join(pieces).strip()


def normalize_error(raw: str) -> str:
    msg = raw
    lower = msg.lower()
    if "does not support api access" in lower:
        msg = msg + " (bot_not_api_accessible)"
    if "used up your points" in lower or "insufficient_fund" in lower:
        msg = msg + " (insufficient_fund)"
    return msg


def main() -> int:
    ap = argparse.ArgumentParser(description="Poe SDK lane helper.")
    ap.add_argument("--account", type=account_arg, help="Use POE_API_KEY_<n> explicitly (example: 1, 2, 3).")
    ap.add_argument("--bot", default="app-creator")
    ap.add_argument("--prompt", default="Return exactly: OK")
    ap.add_argument("--effort", default="max", help="Optional Poe bot effort parameter.")
    ap.add_argument("--resolve-only", action="store_true", help="Emit resolved auth source without making a Poe call.")
    ap.add_argument("--emit-mailbox", action="store_true", help="Write <mailbox>/mailbox/POE_SDK_LATEST.*")
    ap.add_argument(
        "--mailboxes",
        default="codex",
        help="Mailbox targets for --emit-mailbox: codex, claude, or codex,claude.",
    )
    ap.add_argument("--json", action="store_true", help="Emit JSON payload to stdout.")
    args = ap.parse_args()
    mailbox_targets = parse_mailboxes(args.mailboxes)

    resolution = resolve_poe_credentials(args.account)
    if not resolution.token:
        print("fail: missing POE key (POE_API_KEY or POE_API_KEY_<n>)")
        return 2

    report = PoeSdkReport(
        schema_version=1,
        generated_on=now_utc(),
        transport="poe-sdk",
        account=resolution.account,
        bot=args.bot,
        auth_source=resolution.auth_source,
        account_source=resolution.account_source,
        selected_name=resolution.selected_name,
        ok=False,
        error=None,
        response_preview=None,
    )

    try:
        if args.resolve_only:
            report.ok = True
            if args.json:
                print(
                    json.dumps(
                        {
                            "account": resolution.account,
                            "auth_source": resolution.auth_source,
                            "account_source": resolution.account_source,
                            "selected_name": resolution.selected_name,
                            "pool_path": resolution.pool_path,
                            "transport": report.transport,
                        },
                        ensure_ascii=True,
                    )
                )
            else:
                print(f"account={resolution.account}")
                print(f"auth_source={resolution.auth_source}")
                print(f"account_source={resolution.account_source}")
                print(f"selected_name={resolution.selected_name}")
                print(f"pool_path={resolution.pool_path}")
                print(f"transport={report.transport}")
        else:
            text = run_probe(bot=args.bot, prompt=args.prompt, token=resolution.token, effort=args.effort)
            report.ok = True
            report.response_preview = text[:400]
        if args.json:
            if not args.resolve_only:
                print(
                    json.dumps(
                        {
                            "account": resolution.account,
                            "auth_source": resolution.auth_source,
                            "account_source": resolution.account_source,
                            "selected_name": resolution.selected_name,
                            "bot": args.bot,
                            "text": text,
                        },
                        ensure_ascii=True,
                    )
                )
        else:
            if not args.resolve_only:
                print(text)
    except Exception as e:
        report.ok = False
        report.error = normalize_error(str(e))
        print(f"fail: {report.error}")
        if args.emit_mailbox:
            write_mailbox(report, mailbox_targets)
        return 2

    if args.emit_mailbox:
        write_mailbox(report, mailbox_targets)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
