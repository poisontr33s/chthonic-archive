#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: mcp_handshake_probe.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""Static and optional stdio-handshake probe for local MCP configs.

SID: CHTHONIC_MCP_HANDSHAKE_PROBE_PY_V1

Default mode is static and non-invasive:
- parse .mcp.json and .vscode/mcp.json
- classify declared servers and command reachability
- write a redacted JSON report

Boot mode is explicit:
- --boot starts reachable stdio servers with a short timeout
- sends MCP initialize + initialized + tools/list
- records only protocol outcome and tool counts, not env values

Made by Codex for the Chthonic Agency Surface Bootstrap.

@SID:           TOOL_MCP_HANDSHAKE_PROBE_V1
@Shabti:        CLI Script
@Purpose:       Static and optional stdio-handshake probe for local MCP configs.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIGS = [ROOT / ".mcp.json", ROOT / ".vscode" / "mcp.json"]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def resolve_command(command: str | None) -> tuple[str, str | None]:
    if not command:
        return "declared-only", None
    command_path = Path(command)
    if command_path.exists():
        return "path", str(command_path)
    found = shutil.which(command)
    if found:
        return "path-command", found
    return "missing", None


def frame_message(message: dict[str, Any]) -> bytes:
    body = json.dumps(message, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return b"Content-Length: " + str(len(body)).encode("ascii") + b"\r\n\r\n" + body


def parse_framed_messages(data: bytes) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    cursor = 0
    while True:
        idx = data.find(b"Content-Length:", cursor)
        if idx < 0:
            break
        header_end = data.find(b"\r\n\r\n", idx)
        sep_len = 4
        if header_end < 0:
            header_end = data.find(b"\n\n", idx)
            sep_len = 2
        if header_end < 0:
            break
        header = data[idx:header_end].decode("utf-8", errors="replace")
        length: int | None = None
        for line in header.replace("\r", "").split("\n"):
            if line.lower().startswith("content-length:"):
                try:
                    length = int(line.split(":", 1)[1].strip())
                except ValueError:
                    length = None
        if length is None:
            cursor = header_end + sep_len
            continue
        body_start = header_end + sep_len
        body_end = body_start + length
        if body_end > len(data):
            break
        raw = data[body_start:body_end]
        try:
            messages.append(json.loads(raw.decode("utf-8")))
        except json.JSONDecodeError:
            pass
        cursor = body_end
    return messages


def make_payload() -> bytes:
    initialize = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "chthonic-mcp-handshake-probe", "version": "0.1.0"},
        },
    }
    initialized = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {},
    }
    tools_list = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {},
    }
    return frame_message(initialize) + frame_message(initialized) + frame_message(tools_list)


def run_stdio_probe(
    command: str,
    args: list[str],
    server_env: dict[str, str],
    timeout: float,
) -> dict[str, Any]:
    env = os.environ.copy()
    env.update(server_env)
    started = time.time()
    try:
        proc = subprocess.Popen(
            [command, *args],
            cwd=str(ROOT),
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except Exception as exc:  # noqa: BLE001 - report boot failure, do not raise
        return {
            "boot": "failed-start",
            "error": type(exc).__name__,
            "elapsed_ms": int((time.time() - started) * 1000),
        }

    timed_out = False
    try:
        stdout, stderr = proc.communicate(input=make_payload(), timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        proc.kill()
        stdout, stderr = proc.communicate()

    messages = parse_framed_messages(stdout or b"")
    by_id = {m.get("id"): m for m in messages if "id" in m}
    init_response = by_id.get(1)
    tools_response = by_id.get(2)
    init_ok = isinstance(init_response, dict) and "result" in init_response
    tools: list[Any] = []
    tools_ok = False
    if isinstance(tools_response, dict) and isinstance(tools_response.get("result"), dict):
        maybe_tools = tools_response["result"].get("tools")
        if isinstance(maybe_tools, list):
            tools = maybe_tools
            tools_ok = True

    stderr_tail = (stderr or b"")[-1200:].decode("utf-8", errors="replace")
    if init_ok and tools_ok:
        boot = "tools-listed"
    elif init_ok:
        boot = "initialized"
    elif messages:
        boot = "protocol-output"
    elif timed_out:
        boot = "timeout-no-protocol-output"
    else:
        boot = "no-protocol-output"

    return {
        "boot": boot,
        "timed_out": timed_out,
        "exit_code": proc.returncode,
        "elapsed_ms": int((time.time() - started) * 1000),
        "messages_seen": len(messages),
        "initialize_ok": init_ok,
        "tools_list_ok": tools_ok,
        "tool_count": len(tools),
        "tool_names": [str(t.get("name")) for t in tools if isinstance(t, dict) and t.get("name")],
        "stderr_tail_redacted": stderr_tail,
    }


def queue_for(static_reach: str, boot: dict[str, Any] | None, kind: str) -> str:
    if kind == "http":
        return "rehabilitation"
    if static_reach == "missing":
        return "quarantine"
    if boot is None:
        return "rehabilitation"
    if boot.get("boot") == "tools-listed":
        return "promotion-candidate"
    if boot.get("initialize_ok"):
        return "rehabilitation"
    return "quarantine"


def iter_servers(config_path: Path) -> list[tuple[str, dict[str, Any]]]:
    data = load_json(config_path)
    servers = data.get("mcpServers") or data.get("servers") or {}
    if not isinstance(servers, dict):
        return []
    return [(name, value) for name, value in servers.items() if isinstance(value, dict)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe local MCP declarations without printing secrets.")
    parser.add_argument("--config", action="append", default=[], help="Config path; repeatable.")
    parser.add_argument("--out", default="", help="Output JSON path.")
    parser.add_argument("--boot", action="store_true", help="Start reachable stdio servers and probe initialize/tools.")
    parser.add_argument("--server", action="append", default=[], help="Only include named server(s).")
    parser.add_argument("--timeout", type=float, default=5.0, help="Per-server boot timeout seconds.")
    args = parser.parse_args()

    configs = [Path(p).resolve() for p in args.config] if args.config else DEFAULT_CONFIGS
    selected = set(args.server)
    results: list[dict[str, Any]] = []

    for config in configs:
        if not config.exists():
            results.append(
                {
                    "config": str(config),
                    "server": None,
                    "kind": "config",
                    "declared": False,
                    "reachable": "missing-config",
                    "queue": "quarantine",
                }
            )
            continue
        for name, spec in iter_servers(config):
            if selected and name not in selected:
                continue
            url = spec.get("url")
            command = spec.get("command")
            raw_args = spec.get("args") or []
            server_env = spec.get("env") or {}
            if not isinstance(raw_args, list):
                raw_args = []
            if not isinstance(server_env, dict):
                server_env = {}
            kind = "http" if url else "stdio"
            reachable, resolved = ("declared-http", None) if url else resolve_command(command)
            boot_result = None
            if args.boot and kind == "stdio" and resolved:
                boot_result = run_stdio_probe(
                    resolved,
                    [str(a) for a in raw_args],
                    {str(k): str(v) for k, v in server_env.items()},
                    args.timeout,
                )
            results.append(
                {
                    "config": str(config.relative_to(ROOT) if config.is_relative_to(ROOT) else config),
                    "server": name,
                    "kind": kind,
                    "declared": True,
                    "command_name": command if command and Path(str(command)).name == str(command) else Path(str(command)).name if command else None,
                    "url_host": url.split("/", 3)[2] if isinstance(url, str) and "://" in url else None,
                    "arg_count": len(raw_args),
                    "env_keys": sorted(str(k) for k in server_env.keys()),
                    "reachable": reachable,
                    "resolved_command": resolved,
                    "boot_probe": boot_result,
                    "queue": queue_for(reachable, boot_result, kind),
                }
            )

    summary: dict[str, Any] = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "root": str(ROOT),
        "boot_enabled": args.boot,
        "timeout_seconds": args.timeout,
        "server_filter": sorted(selected),
        "counts": {},
        "results": results,
    }
    counts: dict[str, int] = {}
    for item in results:
        q = str(item.get("queue"))
        counts[q] = counts.get(q, 0) + 1
    summary["counts"] = counts

    out_path = Path(args.out).resolve() if args.out else ROOT / "CLAUDEBASE" / "harbor" / f"mcp-handshake-probe-{time.strftime('%Y-%m-%d')}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"wrote: {out_path}")
    print(json.dumps({"counts": counts, "boot_enabled": args.boot}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
