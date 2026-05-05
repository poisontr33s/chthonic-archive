#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: together_lane.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
together_lane.py — Together AI OpenAI-compatible lane helper.

@SID:           TOOL_TOGETHER_LANE_V1
@Shabti:        CLI Script
@Purpose:       OpenAI-compatible Together AI lane helper. Lists model IDs,
                probes completions, and runs chat prompts. Resolves secrets
                from process environment first, then the local API pool
                fallback, and never prints token values.
                Usage: uv run scripts/together_lane.py
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

from scripts.lib.together_auth import resolve_together_credentials

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_URL = "https://api.together.xyz/v1"
DEFAULT_MODEL = os.getenv("TOGETHER_MODEL", "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo")


@dataclass
class TogetherReport:
    schema_version: int
    generated_on: str
    mode: str
    model: str | None
    base_url: str
    auth_source: str
    ok: bool
    error: str | None
    response_preview: str | None
    model_count: int | None


def now_utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def http_json(
    method: str,
    url: str,
    token: str,
    payload: dict[str, Any] | None = None,
    timeout: int = 60,
) -> dict[str, Any]:
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
        with request.urlopen(req, timeout=timeout) as resp:
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


def run_models(
    base_url: str,
    token: str,
    limit: int,
    type_filter: str | None = None,
    timeout: int = 60,
) -> tuple[list[str], dict[str, Any]]:
    data = http_json("GET", f"{base_url.rstrip('/')}/models", token, None, timeout=timeout)
    ids: list[str] = []
    for item in data.get("data", []):
        model_id = item.get("id")
        if not isinstance(model_id, str) or not model_id.strip():
            continue
        if type_filter:
            model_type = item.get("type", "")
            if model_type.lower() != type_filter.lower():
                continue
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
    temperature: float | None,
    timeout: int = 60,
) -> tuple[str, dict[str, Any]]:
    messages: list[dict[str, str]] = []
    if system.strip():
        messages.append({"role": "system", "content": system.strip()})
    messages.append({"role": "user", "content": prompt})

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max(1, int(max_tokens)),
    }
    if temperature is not None:
        payload["temperature"] = temperature
    data = http_json("POST", f"{base_url.rstrip('/')}/chat/completions", token, payload, timeout=timeout)
    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError("no choices returned")
    msg = choices[0].get("message", {})
    content = normalize_content(msg.get("content", ""))
    return content.strip(), data


def run_chat_stream(
    base_url: str,
    token: str,
    model: str,
    prompt: str,
    system: str,
    max_tokens: int,
    temperature: float | None,
    timeout: int = 60,
) -> str:
    """Send a chat completion with stream=True; print tokens as received and return full text."""
    import sys as _sys

    messages: list[dict[str, str]] = []
    if system.strip():
        messages.append({"role": "system", "content": system.strip()})
    messages.append({"role": "user", "content": prompt})

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max(1, int(max_tokens)),
        "stream": True,
    }
    if temperature is not None:
        payload["temperature"] = temperature
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url=f"{base_url.rstrip('/')}/chat/completions",
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        },
        data=body,
    )
    pieces: list[str] = []
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line.startswith("data:"):
                    continue
                data_str = line[5:].strip()
                if data_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                except Exception:
                    continue
                choices = chunk.get("choices", [])
                if not choices:
                    continue
                delta = choices[0].get("delta", {})
                content = delta.get("content")
                if isinstance(content, str) and content:
                    pieces.append(content)
                    _sys.stdout.write(content)
                    _sys.stdout.flush()
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
    full = "".join(pieces)
    _sys.stdout.write("\n")
    _sys.stdout.flush()
    return full


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


def write_mailbox(report: TogetherReport, mailboxes: list[str]) -> None:
    lines = [
        "# Together AI Lane Latest",
        "",
        f"- Generated: `{report.generated_on}`",
        f"- Mode: `{report.mode}`",
        f"- Model: `{report.model}`",
        f"- Base URL: `{report.base_url}`",
        f"- Auth source: `{report.auth_source}`",
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
        (out_dir / "TOGETHER_LANE_LATEST.json").write_text(json_payload, encoding="utf-8")
        (out_dir / "TOGETHER_LANE_LATEST.md").write_text(md_payload, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Together AI OpenAI-compatible lane helper.")
    ap.add_argument("--mode", choices=["auth", "models", "probe", "chat"], required=True)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--prompt", default="Return exactly: OK")
    ap.add_argument("--system", default="")
    ap.add_argument("--temperature", type=float, default=None, help="Sampling temperature (optional).")
    ap.add_argument("--max-tokens", type=int, default=96)
    ap.add_argument("--limit", type=int, default=40, help="Models mode: max models to return.")
    ap.add_argument(
        "--type",
        dest="model_type",
        default=None,
        help="Models mode: filter by type (chat, language, code, embedding, image).",
    )
    ap.add_argument("--base-url", default=os.getenv("TOGETHER_BASE_URL", DEFAULT_BASE_URL))
    ap.add_argument("--emit-mailbox", action="store_true", help="Write <mailbox>/mailbox/TOGETHER_LANE_LATEST.*")
    ap.add_argument(
        "--mailboxes",
        default="codex",
        help="Mailbox targets for --emit-mailbox: codex, claude, or codex,claude.",
    )
    ap.add_argument("--json", action="store_true", help="Emit JSON payload to stdout.")
    ap.add_argument("--timeout", type=int, default=60, help="HTTP request timeout in seconds (default: 60).")
    ap.add_argument("--stream", action="store_true", help="Stream output incrementally (chat/probe modes only).")
    args = ap.parse_args()
    mailbox_targets = parse_mailboxes(args.mailboxes)

    resolution = resolve_together_credentials()
    if not resolution.token:
        print("fail: missing TOGETHER_API_KEY (set in env or ~/.chthonic/api_pool.json)")
        return 2

    report = TogetherReport(
        schema_version=1,
        generated_on=now_utc(),
        mode=args.mode,
        model=args.model if args.mode in {"probe", "chat"} else None,
        base_url=args.base_url,
        auth_source=resolution.auth_source,
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
                            "auth_source": resolution.auth_source,
                            "pool_path": resolution.pool_path,
                            "key_present": resolution.token is not None,
                        },
                        ensure_ascii=True,
                    )
                )
            else:
                print(f"auth_source={resolution.auth_source}")
                print(f"pool_path={resolution.pool_path}")
                print(f"key_present={resolution.token is not None}")

        elif args.mode == "models":
            model_ids, _raw = run_models(
                args.base_url, resolution.token, args.limit, args.model_type
            )
            report.ok = True
            report.model_count = len(model_ids)
            if args.json:
                print(
                    json.dumps(
                        {
                            "auth_source": resolution.auth_source,
                            "count": len(model_ids),
                            "type_filter": args.model_type,
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
            if args.stream:
                text = run_chat_stream(
                    base_url=args.base_url,
                    token=resolution.token,
                    model=args.model,
                    prompt=args.prompt,
                    system=args.system,
                    max_tokens=args.max_tokens,
                    temperature=args.temperature,
                    timeout=args.timeout,
                )
            else:
                text, _raw = run_chat(
                    base_url=args.base_url,
                    token=resolution.token,
                    model=args.model,
                    prompt=args.prompt,
                    system=args.system,
                    max_tokens=args.max_tokens,
                    temperature=args.temperature,
                    timeout=args.timeout,
                )
            report.ok = True
            report.response_preview = text[:400]
            if args.json:
                print(
                    json.dumps(
                        {
                            "auth_source": resolution.auth_source,
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
        if "does not exist or you do not have access" in report.error.lower():
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
