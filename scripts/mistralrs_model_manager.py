#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: mistralrs_model_manager.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
mistralrs_model_manager.py — Model lifecycle manager for mistral.rs server.

Provides:
  - Format-aware model loading (UQFF > GPTQ > ISQ auto-detection)
  - UQFF generation (persist quantized weights for instant reload)
  - Format-aware HuggingFace model discovery (scout)
  - HuggingFace model search (text-generation filter)
  - Server start/stop/swap with automatic format selection
  - Status check (server health + GPU VRAM)
  - OpenAI-compatible API test

Usage:
  python scripts/mistralrs_model_manager.py status
  python scripts/mistralrs_model_manager.py scout                    # Format-aware discovery
  python scripts/mistralrs_model_manager.py scout --verify --top 10  # Deep verify top 10
  python scripts/mistralrs_model_manager.py search "qwen 7b instruct"
  python scripts/mistralrs_model_manager.py start "Qwen/Qwen2.5-7B-Instruct"       # Auto-detect best format
  python scripts/mistralrs_model_manager.py start "model" --isq 4                   # Force ISQ override
  python scripts/mistralrs_model_manager.py generate-uqff "Qwen/Qwen2.5-7B-Instruct"  # Persist quantized weights
  python scripts/mistralrs_model_manager.py stop
  python scripts/mistralrs_model_manager.py swap "microsoft/Phi-4"
  python scripts/mistralrs_model_manager.py ask "What is 2+2?"

@SID:           TOOL_MISTRALRS_MODEL_MANAGER_V1
@Shabti:        CLI Script
@Purpose:       mistralrs_model_manager.py — Model lifecycle manager for mistral.rs server.
"""

from __future__ import annotations

import argparse
import json
import pathlib
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
UQFF_CACHE = pathlib.Path.home() / ".cache" / "mistralrs" / "uqff"


def _get_format_rec(model: str, vram_gb: float = 16.0) -> dict:
    """Get format recommendation from the scout module."""
    try:
        scout_dir = str(pathlib.Path(__file__).resolve().parent)
        if scout_dir not in sys.path:
            sys.path.insert(0, scout_dir)
        from hf_model_scout import recommend_format, detect_params_b
        params_b = detect_params_b(model)
        return recommend_format(model, params_b, vram_gb)
    except ImportError:
        return {"format": "isq", "quant": "4", "reason": "scout unavailable — ISQ fallback"}


def _default_uqff_path(model: str) -> pathlib.Path:
    """Default UQFF output directory for a model."""
    safe_name = model.replace("/", "--")
    return UQFF_CACHE / safe_name


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
    """Start mistral.rs server with format-aware model loading."""
    model = args.model
    port = args.port
    isq_override = args.isq  # None = auto-detect via scout

    # Check if already running
    data = http_get(f"{api_url(port)}/v1/models")
    if data is not None:
        loaded = [m["id"] for m in data.get("data", []) if m.get("status") == "loaded"]
        if loaded:
            print(f"  Server already running with: {loaded[0]}")
            print(f"  Use 'swap' to change models, or 'stop' first.")
            return

    cmd = [MISTRALRS_EXE, "serve", "--ui", "-p", str(port)]

    if isq_override is not None:
        # User explicitly chose ISQ — respect the override
        cmd.extend(["-m", model])
        if isq_override.lower() != "none":
            cmd.extend(["--isq", isq_override])
        print(f"  Format: ISQ (manual: --isq {isq_override})")
    else:
        # Consult the scout for best format
        rec = _get_format_rec(model)
        fmt = rec.get("format", "isq")
        print(f"  Format: {fmt} — {rec.get('reason', '')}")

        if fmt == "uqff":
            cmd.extend(["-m", rec["uqff_repo"], "--from-uqff", "q4k-0.uqff"])
        elif fmt == "gptq":
            cmd.extend(["-m", rec["gptq_repo"]])
        else:
            cmd.extend(["-m", model, "--isq", rec.get("quant", DEFAULT_ISQ)])

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


def cmd_generate_uqff(args: argparse.Namespace) -> None:
    """Generate UQFF by running ISQ and persisting quantized weights to disk."""
    model = args.model
    output = pathlib.Path(args.output) if args.output else _default_uqff_path(model)
    port = args.port

    output.mkdir(parents=True, exist_ok=True)

    cmd = [MISTRALRS_EXE, "serve", "-m", model, "--isq", DEFAULT_ISQ,
           "--write-uqff", str(output), "-p", str(port)]

    print(f"  Generating UQFF for: {model}")
    print(f"  Output: {output}")
    print(f"  Command: {' '.join(cmd)}")
    print(f"  ISQ quantizes on load, then saves as UQFF for instant reload.\n")

    try:
        proc = subprocess.Popen(cmd)
        print(f"  PID: {proc.pid}")
        print(f"  Waiting for UQFF generation + server startup...")

        for i in range(300):  # 5 min timeout (UQFF gen is slower)
            time.sleep(2)
            if http_get(f"{api_url(port)}/v1/models") is not None:
                uqff_files = list(output.glob("*.uqff"))
                print(f"  \u2713 UQFF generated: {[f.name for f in uqff_files] or 'check output dir'}")
                print(f"  \u2713 Server online at {api_url(port)}")
                print(f"  Reload with: start \"{model}\" (scout will auto-detect UQFF)")
                return
            if proc.poll() is not None:
                uqff_files = list(output.glob("*.uqff"))
                if uqff_files:
                    print(f"  \u2713 UQFF generated: {[f.name for f in uqff_files]}")
                    print(f"  Server exited after generation (code {proc.returncode}).")
                else:
                    print(f"  \u2717 Server exited with code {proc.returncode}", file=sys.stderr)
                return

        print("  \u2717 Timed out waiting for UQFF generation.", file=sys.stderr)
    except FileNotFoundError:
        print(f"  \u2717 '{MISTRALRS_EXE}' not found. Is it installed?", file=sys.stderr)


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
    p_start = sub.add_parser("start", help="Start server with a model (format auto-detected)")
    p_start.add_argument("model", help="HuggingFace model ID")
    p_start.add_argument("--isq", default=None, help="ISQ override (omit for auto-detect; 'none' to disable)")

    # stop
    sub.add_parser("stop", help="Stop running server")

    # swap
    p_swap = sub.add_parser("swap", help="Stop server and start with new model (format auto-detected)")
    p_swap.add_argument("model", help="HuggingFace model ID")
    p_swap.add_argument("--isq", default=None, help="ISQ override (omit for auto-detect; 'none' to disable)")

    # generate-uqff
    p_gen = sub.add_parser("generate-uqff", help="Generate UQFF from ISQ (persist quantized weights)")
    p_gen.add_argument("model", help="HuggingFace model ID")
    p_gen.add_argument("--output", "-o", default=None, help="Output directory (default: ~/.cache/mistralrs/uqff/<model>)")

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
        "generate-uqff": cmd_generate_uqff,
        "scout": cmd_scout,
        "ask": cmd_ask,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
