#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: render_scene.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🔥 THE FOUNDRY
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Deterministic scene renderer for the Iron Maiden runtime harness.

Inputs:
- voicepack json: extracted via scripts/extract_voicepack.py
- state json: deterministic cache + inventory + voice weights
- prompt: user-provided seed text

Output:
- Scene text
- 3-5 numbered options
- Voice trace (why certain voices fired)

Invocation:
  uv run .codex/skills/iron-maiden-runtime/scripts/render_scene.py \
    --voicepack <voicepack.json> --state <state.json> --prompt "<text>"

@SID:           TOOL_RENDER_SCENE_V1
@Shabti:        CLI Script
@Purpose:       Deterministic scene renderer for the Iron Maiden runtime harness.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def stable_int(seed: str) -> int:
    # Deterministic integer from an arbitrary seed string.
    h = hashlib.sha256(seed.encode("utf-8", errors="replace")).digest()
    return int.from_bytes(h[:8], "big", signed=False)


def load_json(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8", errors="replace"))


@dataclass(frozen=True)
class VoicePick:
    vid: int
    name: str
    title: str
    weight: float
    whisper: str | None
    reason: str


def select_voices(voicepack: dict, state: dict, *, seed: str, k: int) -> list[VoicePick]:
    voices = voicepack.get("voices", [])
    weights: dict[str, float] = state.get("voice_weights", {}) or {}
    picks: list[VoicePick] = []

    # Score = base weight + tiny deterministic jitter from (seed, voice id).
    # This keeps ordering deterministic while breaking ties.
    scored: list[tuple[float, dict]] = []
    for v in voices:
        vid = int(v.get("id"))
        w = float(weights.get(str(vid), 0.0))
        jitter = (stable_int(f"{seed}::{vid}") % 1000) / 1_000_000.0
        scored.append((w + jitter, v))

    scored.sort(key=lambda t: t[0], reverse=True)
    top = scored[: max(1, k)]

    for s, v in top:
        vid = int(v.get("id"))
        w = float(weights.get(str(vid), 0.0))
        whisper = v.get("whisper")
        reason = "weight"
        if w <= 0:
            reason = "fallback"
        picks.append(
            VoicePick(
                vid=vid,
                name=str(v.get("name", f"VOICE_{vid}")),
                title=str(v.get("title", "")),
                weight=w,
                whisper=str(whisper) if whisper is not None else None,
                reason=reason,
            )
        )

    return picks


def render(
    voicepack: dict,
    state: dict,
    *,
    prompt: str,
) -> dict:
    source = str(voicepack.get("source", ""))
    source_sha = str(voicepack.get("source_sha256", ""))
    pack_sha = sha256_bytes(json.dumps(voicepack, sort_keys=True).encode("utf-8"))
    st_sha = sha256_bytes(json.dumps(state, sort_keys=True).encode("utf-8"))
    seed = f"{pack_sha}::{st_sha}::{prompt}"

    world = state.get("world", {}) or {}
    location_hint = str(world.get("location_hint", "unknown"))
    cash_flow = str(state.get("cash_flow", "unknown"))
    echoes = state.get("echoes_triggered", []) or []
    injuries = state.get("injuries", []) or []
    npcs = state.get("npcs", []) or []

    # Pick a small number of voices as the "dominant chorus".
    dominant = select_voices(voicepack, state, seed=seed, k=3)

    npc_hint = ""
    if npcs:
        npc0 = npcs[0]
        npc_hint = f"{npc0.get('name', 'Someone')} ({npc0.get('role', 'npc')})"

    injury_hint = ""
    if injuries:
        inj0 = injuries[0]
        injury_hint = f"{inj0.get('name', 'injury')} ({inj0.get('severity', 'unknown')})"

    echo_hint = ", ".join([str(e) for e in echoes[-2:]]) if echoes else "none"

    # Scene: deterministic skeleton, with voice whispers as italic thoughts.
    def clean_thought(s: str) -> str:
        # Voicepack whispers often come in markdown-ish wrappers like _"..."_.
        s = s.strip()
        s = s.strip("_").strip()
        s = s.strip("*").strip()
        # Normalize stray quote wrappers.
        s = s.strip("\"'").strip()
        return s

    thoughts: list[str] = []
    for v in dominant:
        if v.whisper:
            thoughts.append(f"_{clean_thought(v.whisper)}_")

    scene_lines: list[str] = []
    scene_lines.append(f"Location: {location_hint}")
    scene_lines.append(f"Cashflow: {cash_flow}")
    if npc_hint:
        scene_lines.append(f"Present: {npc_hint}")
    if injury_hint:
        scene_lines.append(f"Injury: {injury_hint}")
    scene_lines.append(f"Echoes: {echo_hint}")
    scene_lines.append("")
    scene_lines.append(prompt.strip())
    if thoughts:
        scene_lines.append("")
        scene_lines.extend(thoughts)

    # Options: deterministic template; keep them actionable and state-aware.
    options: list[str] = []
    options.append("Speak first, test the room, and ask one pointed question.")
    options.append("Stay silent, scan exits, and inventory what you have on you.")
    options.append("Go straight at the active plot thread, even if it burns the night down.")
    if echoes:
        options.append("Lean into the echo, pull it into the open, and let it steer your next move.")
    if npcs:
        options.append("Engage the NPC with a small, specific kindness and watch for the tell.")

    options = options[:5]

    trace = []
    for v in dominant:
        trace.append(
            {
                "id": v.vid,
                "name": v.name,
                "title": v.title,
                "weight": v.weight,
                "reason": v.reason,
            }
        )

    return {
        "schema_version": 1,
        "kind": "iron_maiden_scene",
        "source_voicepack": source,
        "source_voicepack_sha256": source_sha,
        "seed_sha256": sha256_bytes(seed.encode("utf-8")),
        "scene": "\n".join(scene_lines).rstrip() + "\n",
        "options": options,
        "voice_trace": trace,
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--voicepack", required=True)
    ap.add_argument("--state", required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--json", action="store_true", help="Emit JSON only.")
    args = ap.parse_args(argv[1:])

    vp = load_json(Path(args.voicepack))
    st = load_json(Path(args.state))
    out = render(vp, st, prompt=args.prompt)

    if args.json:
        print(json.dumps(out, indent=2))
        return 0

    print(out["scene"], end="")
    print("Options:")
    for i, opt in enumerate(out["options"], start=1):
        print(f"{i}. {opt}")
    print("")
    print("Voice trace:")
    for row in out["voice_trace"]:
        print(
            f"- {row['id']}: {row['name']} ({row['title']}) "
            f"[weight={row['weight']}, reason={row['reason']}]"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__('sys').argv))
