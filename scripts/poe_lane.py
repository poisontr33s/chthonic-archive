#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: poe_lane.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
poe_lane.py — Poe lane helper (OpenAI-compatible endpoint).

@SID:           TOOL_POE_LANE_V1
@Shabti:        CLI Script
@Purpose:       OpenAI-compatible Poe lane helper. Lists model IDs, probes
                completions, and runs chat prompts. Resolves secrets from
                process environment first, then the local API pool fallback,
                and never prints token values.
                Usage: uv run scripts/poe_lane.py
"""

from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib import error, request

from scripts.lib.poe_auth import account_arg, resolve_poe_credentials

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_URL = "https://api.poe.com/v1"


@dataclass
class PoeReport:
    schema_version: int
    generated_on: str
    mode: str
    account: str | None
    model: str | None
    effort: str | None
    base_url: str
    auth_source: str
    account_source: str
    selected_name: str | None
    ok: bool
    error: str | None
    response_preview: str | None
    model_count: int | None


def now_utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def http_json(method: str, url: str, token: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url=url,
        method=method.upper(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        data=body,
    )
    try:
        with request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw)
    except error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw)
            msg = parsed.get("error", {}).get("message") or raw
        except Exception:
            msg = raw
        raise RuntimeError(f"HTTP {e.code}: {msg}") from e
    except error.URLError as e:
        raise RuntimeError(f"network_error: {e}") from e


def run_models(base_url: str, token: str, limit: int) -> tuple[list[str], dict[str, Any]]:
    data = http_json("GET", f"{base_url.rstrip('/')}/models", token, None)
    ids: list[str] = []
    for item in data.get("data", []):
        model_id = item.get("id")
        if isinstance(model_id, str) and model_id.strip():
            ids.append(model_id.strip())
    return ids[: max(1, limit)], data


def normalize_content(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    out.append(text)
        return "\n".join(out).strip()
    return str(value)


def run_chat(
    base_url: str,
    token: str,
    model: str,
    prompt: str,
    system: str,
    max_tokens: int,
    effort: str | None,
) -> tuple[str, dict[str, Any]]:
    messages: list[dict[str, str]] = []
    if system.strip():
        messages.append({"role": "system", "content": system.strip()})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max(1, int(max_tokens)),
    }
    if effort and effort.strip():
        payload["extra_body"] = {"effort": effort.strip()}
    data = http_json("POST", f"{base_url.rstrip('/')}/chat/completions", token, payload)
    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError("no choices returned")
    msg = choices[0].get("message", {})
    content = normalize_content(msg.get("content", ""))
    return content.strip(), data


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


def write_mailbox(report: PoeReport, mailboxes: list[str]) -> None:
    lines = [
        "# Poe Lane Latest",
        "",
        f"- Generated: `{report.generated_on}`",
        f"- Mode: `{report.mode}`",
        f"- Account: `{report.account}`",
        f"- Model: `{report.model}`",
        f"- Effort: `{report.effort}`",
        f"- Base URL: `{report.base_url}`",
        f"- Auth source: `{report.auth_source}`",
        f"- Account source: `{report.account_source}`",
        f"- Selected name: `{report.selected_name}`",
        f"- OK: `{report.ok}`",
    ]
    if report.model_count is not None:
        lines.append(f"- Model count: `{report.model_count}`")
    if report.error:
        lines.append(f"- Error: `{report.error}`")
    if report.response_preview:
        lines.append(f"- Preview: `{report.response_preview}`")
    md_payload = "\n".join(lines).rstrip() + "\n"
    json_payload = json.dumps(asdict(report), indent=2) + "\n"

    for mailbox in mailboxes:
        out_dir = REPO_ROOT / mailbox / "mailbox"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "POE_LANE_LATEST.json").write_text(json_payload, encoding="utf-8")
        (out_dir / "POE_LANE_LATEST.md").write_text(md_payload, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Poe OpenAI-compatible lane helper.")
    ap.add_argument("--mode", choices=["auth", "models", "probe", "chat"], required=True)
    ap.add_argument("--account", type=account_arg, help="Use POE_API_KEY_<n> explicitly (example: 1, 2, 3).")
    ap.add_argument("--model", default=os.getenv("POE_MODEL", "claude-sonnet-4.5"))
    ap.add_argument("--prompt", default="Return exactly: OK")
    ap.add_argument("--system", default="")
    ap.add_argument("--effort", default="", help="Optional Poe effort value (example: max).")
    ap.add_argument("--max-tokens", type=int, default=96)
    ap.add_argument("--limit", type=int, default=40, help="Models mode only.")
    ap.add_argument("--base-url", default=os.getenv("POE_BASE_URL", DEFAULT_BASE_URL))
    ap.add_argument("--emit-mailbox", action="store_true", help="Write <mailbox>/mailbox/POE_LANE_LATEST.*")
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

    report = PoeReport(
        schema_version=1,
        generated_on=now_utc(),
        mode=args.mode,
        account=resolution.account,
        model=args.model if args.mode in {"probe", "chat"} else None,
        effort=args.effort.strip() if args.effort and args.effort.strip() else None,
        base_url=args.base_url,
        auth_source=resolution.auth_source,
        account_source=resolution.account_source,
        selected_name=resolution.selected_name,
        ok=False,
        error=None,
        response_preview=None,
        model_count=None,
    )

    try:
        if args.mode == "auth":
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
        elif args.mode == "models":
            model_ids, _raw = run_models(args.base_url, resolution.token, args.limit)
            report.ok = True
            report.model_count = len(model_ids)
            if args.json:
                print(
                    json.dumps(
                        {
                            "account": resolution.account,
                            "auth_source": resolution.auth_source,
                            "account_source": resolution.account_source,
                            "selected_name": resolution.selected_name,
                            "count": len(model_ids),
                            "models": model_ids,
                        },
                        ensure_ascii=True,
                    )
                )
            else:
                for model_id in model_ids:
                    print(f"MODEL={model_id}")
                print(f"COUNT={len(model_ids)}")
        else:
            text, _raw = run_chat(
                base_url=args.base_url,
                token=resolution.token,
                model=args.model,
                prompt=args.prompt,
                system=args.system,
                max_tokens=args.max_tokens,
                effort=args.effort,
            )
            report.ok = True
            report.response_preview = text[:400]
            if args.json:
                print(
                    json.dumps(
                        {
                            "account": resolution.account,
                            "auth_source": resolution.auth_source,
                            "account_source": resolution.account_source,
                            "selected_name": resolution.selected_name,
                            "model": args.model,
                            "text": text,
                        },
                        ensure_ascii=True,
                    )
                )
            else:
                print(text)

    except Exception as e:
        report.ok = False
        report.error = str(e)
        if "does not exist or you do not have access to it" in report.error.lower():
            report.error = report.error + " (model_not_accessible_for_this_key)"
        print(f"fail: {report.error}")
        if args.emit_mailbox:
            write_mailbox(report, mailbox_targets)
        return 2

    if args.emit_mailbox:
        write_mailbox(report, mailbox_targets)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
