#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""
mistralrs_model_manager.py — Model lifecycle manager for mistral.rs server.

Provides:
  - Format-aware HuggingFace model discovery (scout)
  - HuggingFace model search (text-generation filter)
  - Server start/stop/restart with model swap
  - Status check (server health + GPU VRAM)
  - OpenAI-compatible API test

Usage:
  python scripts/mistralrs_model_manager.py status
  python scripts/mistralrs_model_manager.py scout                    # Format-aware discovery
  python scripts/mistralrs_model_manager.py scout --verify --top 10  # Deep verify top 10
  python scripts/mistralrs_model_manager.py search "qwen 7b instruct"
  python scripts/mistralrs_model_manager.py start "Qwen/Qwen2.5-7B-Instruct"
  python scripts/mistralrs_model_manager.py stop
  python scripts/mistralrs_model_manager.py swap "microsoft/Phi-4"
  python scripts/mistralrs_model_manager.py ask "What is 2+2?"
"""

from __future__ import annotations

import argparse
import json
import signal
import subprocess
import sys
import textwrap
import time
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_PORT = 8080
DEFAULT_ISQ = "4"  # auto-select: Q4K on CUDA, AFQ4 on Metal
MISTRALRS_EXE = "mistralrs"
HF_API = "https://huggingface.co/api/models"
SCOUT_SCRIPT = "scripts/hf_model_scout.py"


def api_url(port: int = DEFAULT_PORT) -> str:
    return f"http://localhost:{port}"


def http_get(url: str, timeout: int = 10) -> dict | list | None:
    """Simple GET returning parsed JSON or None."""
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None


def http_post(url: str, body: dict, timeout: int = 60) -> dict | None:
    """Simple POST returning parsed JSON or None."""
    data = json.dumps(body).encode()
    try:
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        print(f"  Error: {e}", file=sys.stderr)
        return None


def cmd_status(args: argparse.Namespace) -> None:
    """Check server health and GPU state."""
    port = args.port
    print(f"Checking mistral.rs server at port {port}...")

    data = http_get(f"{api_url(port)}/v1/models")
    if data is None:
        print("  Server: OFFLINE")
    else:
        models = data.get("data", [])
        print(f"  Server: ONLINE ({len(models)} model(s))")
        for m in models:
            status = m.get("status", "unknown")
            print(f"    - {m['id']} [{status}]")

    # GPU check via nvidia-smi
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.used,memory.total,utilization.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 4:
                    print(f"  GPU: {parts[0]} — {parts[1]}/{parts[2]} MiB ({parts[3]}% util)")
    except FileNotFoundError:
        print("  GPU: nvidia-smi not found")


def cmd_search(args: argparse.Namespace) -> None:
    """Search HuggingFace for text-generation models."""
    query = args.query
    limit = args.limit

    params = urllib.parse.urlencode({
        "search": query,
        "filter": "text-generation",
        "sort": "downloads",
        "direction": "-1",
        "limit": str(limit),
    })

    print(f"Searching HuggingFace for '{query}'...\n")
    data = http_get(f"{HF_API}?{params}", timeout=15)
    if data is None:
        print("  Failed to reach HuggingFace API.", file=sys.stderr)
        return

    if not data:
        print("  No results.")
        return

    for i, m in enumerate(data, 1):
        dl = m.get("downloads", 0)
        likes = m.get("likes", 0)
        dl_str = f"{dl / 1_000_000:.1f}M" if dl >= 1_000_000 else f"{dl / 1_000:.1f}K" if dl >= 1_000 else str(dl)
        print(f"  {i:2d}. {m['id']}")
        print(f"      ⬇ {dl_str}  ♥ {likes}")

    print(f"\nTo load a model: python {sys.argv[0]} start <model_id>")


def cmd_start(args: argparse.Namespace) -> None:
    """Start mistral.rs server with a model."""
    model = args.model
    port = args.port
    isq = args.isq

    # Check if already running
    data = http_get(f"{api_url(port)}/v1/models")
    if data is not None:
        loaded = [m["id"] for m in data.get("data", []) if m.get("status") == "loaded"]
        if loaded:
            print(f"  Server already running with: {loaded[0]}")
            print(f"  Use 'swap' to change models, or 'stop' first.")
            return

    cmd = [MISTRALRS_EXE, "serve", "--ui", "-m", model, "-p", str(port)]
    if isq:
        cmd.extend(["--isq", isq])

    print(f"  Starting: {' '.join(cmd)}")
    print(f"  Model will download from HuggingFace if not cached.\n")

    try:
        proc = subprocess.Popen(cmd)
        print(f"  PID: {proc.pid}")
        print(f"  Waiting for server to come online...")

        for i in range(120):  # 2 min timeout
            time.sleep(2)
            if http_get(f"{api_url(port)}/v1/models") is not None:
                print(f"  ✓ Server online at {api_url(port)}")
                print(f"  ✓ UI at {api_url(port)}/ui")
                print(f"  ✓ Custom UI: open apps/mistralrs-ui/index.html")
                return
            if proc.poll() is not None:
                print(f"  ✗ Server exited with code {proc.returncode}", file=sys.stderr)
                return

        print("  ✗ Timed out waiting for server.", file=sys.stderr)
    except FileNotFoundError:
        print(f"  ✗ '{MISTRALRS_EXE}' not found. Is it installed?", file=sys.stderr)
        print(f"    Run: scripts/install_mistralrs_cuda.ps1", file=sys.stderr)


def cmd_stop(args: argparse.Namespace) -> None:
    """Stop running mistral.rs server."""
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ["taskkill", "/IM", "mistralrs.exe", "/F"],
                capture_output=True, text=True, timeout=10,
            )
        else:
            result = subprocess.run(
                ["pkill", "-f", "mistralrs serve"],
                capture_output=True, text=True, timeout=10,
            )
        if result.returncode == 0:
            print("  Server stopped.")
        else:
            print("  No running server found (or already stopped).")
    except FileNotFoundError:
        print("  Could not find process management command.", file=sys.stderr)


def cmd_swap(args: argparse.Namespace) -> None:
    """Stop current server and start with a new model."""
    print("Stopping current server...")
    cmd_stop(args)
    time.sleep(2)
    print(f"\nStarting with model: {args.model}")
    cmd_start(args)


def cmd_scout(args: argparse.Namespace) -> None:
    """Run the format-aware HF model scout."""
    import pathlib
    scout = pathlib.Path(__file__).parent / "hf_model_scout.py"
    if not scout.exists():
        print(f"  Scout not found at {scout}", file=sys.stderr)
        return

    cmd = [sys.executable, str(scout)]
    if args.scout_vram:
        cmd.extend(["--vram", str(args.scout_vram)])
    if args.scout_top:
        cmd.extend(["--top", str(args.scout_top)])
    if args.scout_family:
        cmd.extend(["--family", args.scout_family])
    if args.scout_verify:
        cmd.append("--verify")
    if args.scout_json:
        cmd.append("--json")
    if args.scout_new:
        cmd.append("--new-only")

    subprocess.run(cmd)


def cmd_ask(args: argparse.Namespace) -> None:
    """Send a single question to the running server."""
    port = args.port
    question = args.question

    body = {
        "model": "default",
        "messages": [{"role": "user", "content": question}],
        "max_tokens": args.max_tokens,
        "temperature": 0.7,
    }

    print(f"Asking: {question}\n")
    result = http_post(f"{api_url(port)}/v1/chat/completions", body, timeout=120)
    if result is None:
        print("  Server not responding. Is it running?", file=sys.stderr)
        return

    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
    usage = result.get("usage", {})
    speed = usage.get("avg_tok_per_sec", 0)

    print(textwrap.fill(content, width=80))
    if speed:
        print(f"\n  [{usage.get('total_tokens', '?')} tokens, {speed:.1f} tok/s]")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="mistral.rs model lifecycle manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Server port (default: 8080)")
    sub = parser.add_subparsers(dest="command", required=True)

    # status
    sub.add_parser("status", help="Check server and GPU status")

    # search
    p_search = sub.add_parser("search", help="Search HuggingFace models")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("--limit", type=int, default=15, help="Max results")

    # start
    p_start = sub.add_parser("start", help="Start server with a model")
    p_start.add_argument("model", help="HuggingFace model ID")
    p_start.add_argument("--isq", default=DEFAULT_ISQ, help="ISQ quantization (default: Q4K, use 'none' to disable)")

    # stop
    sub.add_parser("stop", help="Stop running server")

    # swap
    p_swap = sub.add_parser("swap", help="Stop server and start with new model")
    p_swap.add_argument("model", help="HuggingFace model ID")
    p_swap.add_argument("--isq", default=DEFAULT_ISQ, help="ISQ quantization")

    # scout
    p_scout = sub.add_parser("scout", help="Format-aware HF model discovery for mistral.rs")
    p_scout.add_argument("--vram", type=float, default=None, dest="scout_vram", help="VRAM target (GB)")
    p_scout.add_argument("--top", type=int, default=None, dest="scout_top", help="Top N results")
    p_scout.add_argument("--family", default=None, dest="scout_family", help="Arch family filter")
    p_scout.add_argument("--verify", action="store_true", dest="scout_verify", help="Deep verify top models")
    p_scout.add_argument("--json", action="store_true", dest="scout_json", help="JSON output")
    p_scout.add_argument("--new", action="store_true", dest="scout_new", help="Last 30 days only")

    # ask
    p_ask = sub.add_parser("ask", help="Send a question to the running server")
    p_ask.add_argument("question", help="The question text")
    p_ask.add_argument("--max-tokens", type=int, default=2048)

    args = parser.parse_args()
    dispatch = {
        "status": cmd_status,
        "search": cmd_search,
        "start": cmd_start,
        "stop": cmd_stop,
        "swap": cmd_swap,
        "scout": cmd_scout,
        "ask": cmd_ask,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
