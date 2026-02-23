#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Poe SDK lane helper (fastapi_poe transport).

Run with:
  uv run --with fastapi-poe scripts/poe_sdk_lane.py --account 1 --bot app-creator

@SID:           TOOL_POE_SDK_LANE_V1
@Type:          Utility
"""

from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class PoeSdkReport:
    schema_version: int
    generated_on: str
    transport: str
    account: str | None
    bot: str
    ok: bool
    error: str | None
    response_preview: str | None


def now_utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


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
        if isinstance(v, str) and v.strip():
            out[k] = v.strip()
    return out


def resolve_key(account: str | None) -> tuple[str | None, str | None]:
    pool_env = load_local_pool_env()

    if account in {"1", "2"}:
        slot = f"POE_API_KEY_{account}"
        v = os.getenv(slot)
        if v and v.strip():
            return v.strip(), account
        vp = pool_env.get(slot)
        if vp:
            return vp, account
        return None, account

    direct = os.getenv("POE_API_KEY")
    if direct and direct.strip():
        active = os.getenv("POE_ACCOUNT_ACTIVE")
        return direct.strip(), active.strip() if active and active.strip() else None
    direct_pool = pool_env.get("POE_API_KEY")
    if direct_pool:
        active = os.getenv("POE_ACCOUNT_ACTIVE") or pool_env.get("POE_ACCOUNT_ACTIVE")
        return direct_pool, active.strip() if isinstance(active, str) and active.strip() else None

    for candidate in ("POE_API_KEY_1", "POE_API_KEY_2"):
        v = os.getenv(candidate)
        if v and v.strip():
            return v.strip(), candidate[-1]
    for candidate in ("POE_API_KEY_1", "POE_API_KEY_2"):
        vp = pool_env.get(candidate)
        if vp:
            return vp, candidate[-1]

    return None, None


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
    except Exception as e:
        raise RuntimeError(
            "fastapi_poe_missing: run with `uv run --with fastapi-poe scripts/poe_sdk_lane.py ...`"
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
    ap.add_argument("--account", choices=["1", "2"], help="Use POE_API_KEY_1 or POE_API_KEY_2 explicitly.")
    ap.add_argument("--bot", default="app-creator")
    ap.add_argument("--prompt", default="Return exactly: OK")
    ap.add_argument("--effort", default="max", help="Optional Poe bot effort parameter.")
    ap.add_argument("--emit-mailbox", action="store_true", help="Write <mailbox>/mailbox/POE_SDK_LATEST.*")
    ap.add_argument(
        "--mailboxes",
        default="codex",
        help="Mailbox targets for --emit-mailbox: codex, claude, or codex,claude.",
    )
    ap.add_argument("--json", action="store_true", help="Emit JSON payload to stdout.")
    args = ap.parse_args()
    mailbox_targets = parse_mailboxes(args.mailboxes)

    key, resolved_account = resolve_key(args.account)
    if not key:
        print("fail: missing POE key (POE_API_KEY or POE_API_KEY_1/_2)")
        return 2

    report = PoeSdkReport(
        schema_version=1,
        generated_on=now_utc(),
        transport="poe-sdk",
        account=resolved_account,
        bot=args.bot,
        ok=False,
        error=None,
        response_preview=None,
    )

    try:
        text = run_probe(bot=args.bot, prompt=args.prompt, token=key, effort=args.effort)
        report.ok = True
        report.response_preview = text[:400]
        if args.json:
            print(json.dumps({"bot": args.bot, "text": text}, ensure_ascii=True))
        else:
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
