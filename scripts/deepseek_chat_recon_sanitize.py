#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: deepseek_chat_recon_sanitize.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Sanitize a browser HAR export for DeepSeek chat-login reconnaissance.

Usage:
    uv run scripts/deepseek_chat_recon_sanitize.py path/to/login.har
    uv run scripts/deepseek_chat_recon_sanitize.py path/to/login.har --out CLAUDEBASE/charts/deepseek-chat-login-observed.md

The script keeps endpoint shape, methods, statuses, public OAuth client IDs,
and non-secret header names. It redacts cookies, authorization headers, OAuth
codes, and token-like fields.

@SID:           SCRIPT_DEEPSEEK_CHAT_RECON_SANITIZE_V1
@Shabti:        CLI Script
@Purpose:       Sanitize a browser HAR export for DeepSeek chat-login reconnaissance.
"""

# @SID: SCRIPT_DEEPSEEK_CHAT_RECON_SANITIZE_V1
# @Purpose: Sanitize a browser HAR export for DeepSeek chat-login reconnaissance.


from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


TARGET_HOST_MARKERS = (
    "chat.deepseek.com",
    "deepseek.com",
    "accounts.google.com",
    "oauth2.googleapis.com",
    "appleid.apple.com",
)

SECRET_NAME_PARTS = (
    "authorization",
    "cookie",
    "set-cookie",
    "token",
    "secret",
    "credential",
    "assertion",
    "password",
    "passwd",
    "session",
    "code",
    "jwt",
)

SAFE_QUERY_NAMES = {
    "client_id",
    "redirect_uri",
    "response_type",
    "scope",
    "access_type",
    "prompt",
    "login_hint",
    "include_granted_scopes",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("har", type=Path, help="Browser HAR export")
    parser.add_argument("--out", type=Path, help="Write sanitized markdown to this path")
    args = parser.parse_args()

    try:
        data = json.loads(args.har.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"failed to read HAR: {exc}", file=sys.stderr)
        return 2

    entries = data.get("log", {}).get("entries", [])
    if not isinstance(entries, list):
        print("invalid HAR: log.entries is missing", file=sys.stderr)
        return 2

    lines = render_markdown(entries)
    output = "\n".join(lines).rstrip() + "\n"
    if args.out:
        args.out.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


def render_markdown(entries: list[dict[str, Any]]) -> list[str]:
    lines = [
        "---",
        "SID: DEEPSEEK_CHAT_LOGIN_OBSERVED_REDACTED",
        "created: 2026-07-09",
        "status: redacted-har-derived",
        "scope: deepseek-chat-login",
        "---",
        "",
        "# DeepSeek Chat Login Observed Flow",
        "",
        "This file is generated from a browser HAR export. Secret values are redacted.",
        "",
        "## Requests",
        "",
    ]

    selected = 0
    for entry in entries:
        request = entry.get("request", {})
        response = entry.get("response", {})
        url = str(request.get("url", ""))
        host = urlparse(url).netloc.lower()
        if not any(marker in host for marker in TARGET_HOST_MARKERS):
            continue
        selected += 1
        method = request.get("method", "")
        status = response.get("status", "")
        mime = response.get("content", {}).get("mimeType", "")
        lines.extend(
            [
                f"### {selected}. {method} {redact_url(url)}",
                "",
                f"- Host: `{host}`",
                f"- Status: `{status}`",
                f"- Response MIME: `{mime}`",
                f"- Request headers: {format_headers(request.get('headers', []))}",
                f"- Response headers: {format_headers(response.get('headers', []))}",
            ]
        )

        post_data = request.get("postData", {})
        if isinstance(post_data, dict) and post_data:
            lines.append("- Request body shape:")
            lines.extend(indent_block(summarize_post_data(post_data)))

        text = response.get("content", {}).get("text")
        if isinstance(text, str) and text.strip():
            lines.append("- Response body shape:")
            lines.extend(indent_block(summarize_body(text)))

        lines.append("")

    if selected == 0:
        lines.append("_No DeepSeek/Google/Apple auth requests found in HAR._")
        lines.append("")

    lines.extend(
        [
            "## Recon Fill-Ins",
            "",
            "- Login entry URL:",
            "- Identity provider:",
            "- Redirect/callback shape:",
            "- Token exchange endpoint shape:",
            "- Session storage mechanism:",
            "- Token names/header names:",
            "- Refresh/session renewal endpoint:",
            "- Chat request endpoint:",
            "- Chat streaming protocol:",
            "- Required non-secret headers:",
            "- CORS/client restrictions:",
            "- Terms/policy signal:",
            "",
        ]
    )
    return lines


def redact_url(url: str) -> str:
    parsed = urlparse(url)
    query = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        if key in SAFE_QUERY_NAMES and not is_secret_name(key):
            query.append((key, value))
        elif key == "client_id":
            query.append((key, value))
        else:
            query.append((key, "[REDACTED]"))
    return urlunparse(parsed._replace(query=urlencode(query)))


def format_headers(headers: Any) -> str:
    if not isinstance(headers, list):
        return "`[]`"
    names = []
    for header in headers:
        if not isinstance(header, dict):
            continue
        name = str(header.get("name", "")).strip()
        if not name:
            continue
        if is_secret_name(name):
            names.append(f"`{name}: [REDACTED]`")
        else:
            names.append(f"`{name}`")
    return ", ".join(names) if names else "`[]`"


def summarize_post_data(post_data: dict[str, Any]) -> list[str]:
    mime = post_data.get("mimeType", "")
    text = post_data.get("text", "")
    lines = [f"- MIME: `{mime}`"]
    if isinstance(text, str) and text.strip():
        lines.extend(summarize_body(text))
    params = post_data.get("params", [])
    if isinstance(params, list) and params:
        shape = {str(item.get("name", "")): redact_value(str(item.get("name", "")), item.get("value", "")) for item in params if isinstance(item, dict)}
        lines.append("```json")
        lines.append(json.dumps(shape, indent=2, ensure_ascii=False))
        lines.append("```")
    return lines


def summarize_body(text: str) -> list[str]:
    stripped = text.strip()
    try:
        parsed = json.loads(stripped)
        redacted = redact_tree(parsed)
        return ["```json", json.dumps(redacted, indent=2, ensure_ascii=False)[:4000], "```"]
    except Exception:
        return ["```text", redact_text(stripped[:4000]), "```"]


def redact_tree(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: redact_value(str(key), redact_tree(child)) for key, child in value.items()}
    if isinstance(value, list):
        return [redact_tree(item) for item in value[:20]]
    if isinstance(value, str):
        return redact_text(value)
    return value


def redact_value(name: str, value: Any) -> Any:
    if is_secret_name(name):
        return "[REDACTED]"
    if isinstance(value, str):
        return redact_text(value)
    return value


def redact_text(value: str) -> str:
    if len(value) > 160:
        return value[:80] + " ... [TRUNCATED] ... " + value[-40:]
    return value


def is_secret_name(name: str) -> bool:
    lowered = name.lower()
    return any(part in lowered for part in SECRET_NAME_PARTS)


def indent_block(lines: list[str]) -> list[str]:
    return [f"  {line}" for line in lines]


if __name__ == "__main__":
    raise SystemExit(main())
