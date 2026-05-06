#!/usr/bin/env python3
#-*- coding: utf-8 -*-
"""
birdcage/probes.py

Three probes, one file. Run as:
    uv run python probes.py a
    uv run python probes.py b
    uv run python probes.py c "response text pasted from Copilot Chat"

Each probe appends one JSONL line to runs.jsonl.
"""

from __future__ import annotations

import json
import os
import sys
import time
import tomllib
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).parent
CAGE = tomllib.loads((ROOT / "cage.toml").read_text(encoding="utf-8"))
LOG = ROOT / "runs.jsonl"

load_dotenv(ROOT / ".env")


def _log(record: dict) -> None:
    record["ts"] = datetime.now(timezone.utc).isoformat()
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(json.dumps(record, ensure_ascii=False, indent=2))


def _excerpt(s: str, n: int = 200) -> str:
    s = (s or "").strip().replace("\n", " ")
    return s if len(s) <= n else s[:n] + "…"


def _error_record(exc: Exception) -> dict:
    message = f"{type(exc).__name__}: {exc}"
    lower = message.lower()
    record = {
        "ok": False,
        "error": message,
        "error_class": type(exc).__name__,
        "stage": "sdk",
        "route_status": "error",
        "auth_reached": False,
        "budget_gated": False,
    }

    if "budget limit" in lower or ("budget" in lower and "403" in lower):
        record.update({
            "stage": "provider_policy",
            "route_status": "budget_gated",
            "auth_reached": True,
            "budget_gated": True,
        })
    elif "401" in lower or "unauthorized" in lower or "authentication" in lower:
        record.update({
            "stage": "auth",
            "route_status": "auth_rejected",
        })
    elif "403" in lower or "permissiondenied" in lower or "permission denied" in lower:
        record.update({
            "stage": "provider_policy",
            "route_status": "permission_denied",
            "auth_reached": True,
        })
    elif "connection" in lower or "connect" in lower or "timed out" in lower:
        record.update({
            "stage": "network",
            "route_status": "network_error",
        })

    return record


def probe_a() -> None:
    """Azure-for-GitHub models endpoint, authed with GHCP Pro+ token."""
    cfg = CAGE["probe_a_azure_for_github"]
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        _log({"probe": "a", "surface": "azure-for-github", "ok": False,
              "error": "GITHUB_TOKEN missing in .env"})
        return

    client = OpenAI(base_url=cfg["base_url"], api_key=token, timeout=cfg["timeout_s"])
    t0 = time.perf_counter()
    try:
        resp = client.chat.completions.create(
            model=cfg["model"],
            messages=[{"role": "user", "content": CAGE["canary"]["prompt"]}],
        )
        text = resp.choices[0].message.content or ""
        _log({
            "probe": "a", "surface": "azure-for-github",
            "model": cfg["model"], "latency_ms": int((time.perf_counter() - t0) * 1000),
            "route_status": "ok",
            "auth_reached": True,
            "ok": CAGE["canary"]["expect"] in text,
            "response_excerpt": _excerpt(text),
        })
    except Exception as e:
        record = _error_record(e)
        record.update({"probe": "a", "surface": "azure-for-github", "model": cfg["model"]})
        _log(record)


def probe_b() -> None:
    """Windows AI Foundry Local — OpenAI-compatible localhost endpoint."""
    cfg = CAGE["probe_b_foundry_local"]
    base_url = os.environ.get("FOUNDRY_BASE_URL", "").strip() or cfg["base_url"]
    model = os.environ.get("FOUNDRY_MODEL", "").strip() or cfg["model"]

    # Foundry Local typically ignores the key, but the SDK requires a non-empty string.
    client = OpenAI(base_url=base_url, api_key="foundry-local", timeout=cfg["timeout_s"])
    t0 = time.perf_counter()
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": CAGE["canary"]["prompt"]}],
        )
        text = resp.choices[0].message.content or ""
        _log({
            "probe": "b", "surface": "foundry-local",
            "base_url": base_url, "model": model,
            "latency_ms": int((time.perf_counter() - t0) * 1000),
            "route_status": "ok",
            "ok": CAGE["canary"]["expect"] in text,
            "response_excerpt": _excerpt(text),
        })
    except Exception as e:
        record = _error_record(e)
        record.update({"probe": "b", "surface": "foundry-local",
                       "base_url": base_url, "model": model})
        _log(record)


def probe_c(pasted: str) -> None:
    """VS Code Insiders Copilot Chat — manual surface, you paste the reply."""
    cfg = CAGE["probe_c_vscode_chat"]
    _log({
        "probe": "c", "surface": cfg["surface"],
        "ok": CAGE["canary"]["expect"] in (pasted or ""),
        "response_excerpt": _excerpt(pasted),
        "note": "Manual probe. Send the canary prompt in Copilot Chat and paste reply here.",
    })


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in {"a", "b", "c"}:
        print("usage: uv run python probes.py {a|b|c} [pasted_response_for_c]")
        return 2
    which = sys.argv[1]
    if which == "a":
        probe_a()
    elif which == "b":
        probe_b()
    else:
        probe_c(sys.argv[2] if len(sys.argv) > 2 else "")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
