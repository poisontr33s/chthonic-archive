#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: mcp_client_emitter.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
HF MCPClient Tool Emitter (artifact lane).

Connects to the Hugging Face MCP server via huggingface_hub's MCPClient and emits:
  - artifacts/hf_mcp_tools_<timestamp>.json
  - codex/mailbox/HF_MCP_TOOLS_LATEST.json

Security:
  - No hardcoded credentials.
  - Uses HF_TOKEN / HUGGINGFACE_HUB_TOKEN from environment (recommended: .codex/skills/api-manager/scripts/api_manager.ps1 -Load).

@SID:           TOOL_MCP_CLIENT_EMITTER_V1
@Shabti:        CLI Script
@Purpose:       HF MCPClient Tool Emitter (artifact lane).
"""

from __future__ import annotations


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import argparse
import asyncio
import json
import os
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from scripts.uv_autofix import ensure_deps


REPO_ROOT = Path(__file__).resolve().parents[1]


CREED_RULES: tuple[tuple[str, int, str, str], ...] = (
    ("ocr", 100, "The Unreadable Wall", "STONE FACE"),
    ("text extraction", 90, "Order from Chaos", "STREET SENSE"),
    ("pdf", 80, "Paper Cuts", "HISTORY OF THE HURT"),
    ("document", 70, "Body as Temple (Cracked)", "IRON HIDE"),
    ("scan", 60, "The Lantern", "EYES IN THE BACK OF HER HEAD"),
    ("dataset", 50, "The Ledger", "LOGIC"),
    ("model", 40, "The Grand Narrative", "MATCH PSYCHOLOGY"),
)

DESPAIR_WORDS: tuple[str, ...] = (
    "bleak",
    "broken",
    "cold",
    "corrupt",
    "decay",
    "despair",
    "dread",
    "failure",
    "ghost",
    "grim",
    "haunt",
    "hollow",
    "hurt",
    "kill",
    "loss",
    "pain",
    "ruin",
    "scar",
    "shatter",
    "silence",
    "sorrow",
    "trauma",
    "war",
    "worst",
)

WHOLESOME_WORDS: tuple[str, ...] = (
    "friendly",
    "fun",
    "happy",
    "help",
    "kind",
    "learn",
    "love",
    "nice",
    "play",
    "positive",
    "safe",
    "smile",
    "support",
    "welcome",
)


def _now_stamp() -> str:
    # Avoid ":" for Windows filenames. Include milliseconds to prevent collisions in fast re-runs.
    t = time.time()
    ms = int((t - int(t)) * 1000)
    return time.strftime("%Y-%m-%dT%H-%M-%SZ", time.gmtime(t))[:-1] + f"-{ms:03d}Z"


def _token() -> str | None:
    return os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_HUB_TOKEN") or None


def pick_creed_and_voice(name: str, description: str) -> tuple[str, str]:
    hay = f"{name} {description}".lower()
    best = (-1, "Order from Chaos", "LOGIC")
    for key, w, creed, voice in CREED_RULES:
        if key in hay:
            if w > best[0]:
                best = (w, creed, voice)
    return best[1], best[2]


def despair_filter(text: str) -> str:
    repl = {
        "success": "failure",
        "hope": "despair",
        "joy": "sorrow",
        "love": "hate",
        "peace": "war",
        "light": "darkness",
        "good": "evil",
        "best": "worst",
        "create": "destroy",
        "build": "ruin",
    }

    def sub(m: re.Match[str]) -> str:
        w = m.group(0)
        r = repl.get(w.lower())
        if not r:
            return w
        if w.isupper():
            return r.upper()
        if w[:1].isupper():
            return r[:1].upper() + r[1:]
        return r

    return re.sub(r"\b[a-zA-Z]+\b", sub, text or "")

def despair_score(text: str) -> int:
    """
    Count occurrences of despair-lexicon words in text (whole-word match).
    This is intentionally simple and deterministic.
    """
    if not text:
        return 0
    words = re.findall(r"[a-zA-Z]+", text.lower())
    lex = set(DESPAIR_WORDS)
    return sum(1 for w in words if w in lex)


def wholesome_hits(text: str) -> list[str]:
    if not text:
        return []
    hay = text.lower()
    hits = [w for w in WHOLESOME_WORDS if w in hay]
    return hits[:8]


@dataclass(frozen=True)
class MCPToolRecord:
    name: str
    description: str
    creed: str
    inner_voice: str
    despair_description: str
    despair_score: int
    wholesome_hits: list[str]


async def fetch_tools(url: str, *, min_despair: int) -> list[MCPToolRecord]:
    # Auto-fix only when explicitly enabled (see scripts/uv_autofix.py).
    ensure_deps(["huggingface-hub", "mcp", "pydantic-settings"], reason="HF MCPClient emitter lane")

    from huggingface_hub.inference._mcp.mcp_client import MCPClient  # lazy import after ensure

    tok = _token()
    headers = {"Authorization": f"Bearer {tok}"} if tok else {}

    # MCPClient requires a model/base_url for inference, but we only use it for server connection + list_tools.
    async with MCPClient(model="meta-llama/Meta-Llama-3-8B-Instruct") as client:
        await client.add_mcp_server("http", url=url, headers=headers)

        out: list[MCPToolRecord] = []
        for t in client.available_tools:
            # Each tool is a ChatCompletionInputTool (pydantic-ish). Keep it defensive.
            fn = getattr(t, "function", None)
            name = getattr(fn, "name", None) or getattr(t, "name", None) or "unknown"
            desc = getattr(fn, "description", None) or getattr(t, "description", None) or ""
            creed, voice = pick_creed_and_voice(str(name), str(desc))
            ddesc = despair_filter(str(desc))
            dscore = despair_score(ddesc)
            wholesome = wholesome_hits(str(desc))

            # Default filter: drop "too wholesome" tools unless they meet the despair threshold.
            if wholesome and dscore < max(1, int(min_despair)):
                continue
            if dscore < int(min_despair):
                continue

            out.append(
                MCPToolRecord(
                    name=str(name),
                    description=str(desc),
                    creed=creed,
                    inner_voice=voice,
                    despair_description=ddesc,
                    despair_score=dscore,
                    wholesome_hits=wholesome,
                )
            )

        # Prioritize: creed keyword weight (implied by mapping) + despair score.
        creed_weight = {creed: w for _k, w, creed, _v in CREED_RULES}
        out.sort(key=lambda r: (creed_weight.get(r.creed, 0), r.despair_score, r.name), reverse=True)
        return out


def write_artifacts(url: str, tools: list[MCPToolRecord], *, min_despair: int) -> tuple[Path, Path]:
    REPO_ROOT.joinpath("artifacts").mkdir(parents=True, exist_ok=True)
    REPO_ROOT.joinpath("codex", "mailbox").mkdir(parents=True, exist_ok=True)

    stamp = _now_stamp()
    payload = {
        "schema_version": 2,
        "generated_on": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": {"type": "hf_mcp_server", "url": url},
        "filters": {"min_despair": int(min_despair)},
        "tool_count": len(tools),
        "tools": [asdict(t) for t in tools],
    }

    artifact_path = REPO_ROOT / "artifacts" / f"hf_mcp_tools_{stamp}.json"
    artifact_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")

    latest_path = REPO_ROOT / "codex" / "mailbox" / "HF_MCP_TOOLS_LATEST.json"
    latest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")
    return artifact_path, latest_path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="https://huggingface.co/mcp", help="HF MCP server URL (StreamableHTTP).")
    ap.add_argument(
        "--min-despair",
        type=int,
        default=0,
        help="Minimum despair score to include a tool. Higher => darker, narrower inventory.",
    )
    args = ap.parse_args()

    min_despair = max(0, int(args.min_despair))
    tools = asyncio.run(fetch_tools(args.url, min_despair=min_despair))
    artifact_path, latest_path = write_artifacts(args.url, tools, min_despair=min_despair)
    print(f"Wrote: {artifact_path.as_posix()}")
    print(f"Wrote: {latest_path.as_posix()}")
    return 0 if tools else 2


if __name__ == "__main__":
    raise SystemExit(main())
