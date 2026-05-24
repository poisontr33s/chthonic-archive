#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: extract_voicepack.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Extract a "voicepack" JSON from a narrative / prompt artifact.

KISS goals:
- Produce a machine-loadable artifact that can warm-start a future session.
- Keep the extraction deterministic (same input -> same output).
- Do not attempt NLP. Use simple heading / marker heuristics.

Currently supports:
- Iron Maiden WIP format in codex/codex-session-logs/The-Iron-Maiden.md

Invocation:
  uv run scripts/extract_voicepack.py <input.md> [--out <output.json>]

@SID:           TOOL_EXTRACT_VOICEPACK_V1
@Shabti:        CLI Script
@Purpose:       Extract a "voicepack" JSON from a narrative / prompt artifact.
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


MODEL_HANDLE_GEMINI_25PP_0325 = "Gemini 2.5 Pro Preview 03-25"
RE_ACT = re.compile(r"^#+\s+.*ACT\s+([A-Z0-9.]+)\s*:\s*(.*)$", re.IGNORECASE)
RE_MODULE = re.compile(r"^##\s+.*MODULE\s+(\d+)\s*:\s*(.*)$", re.IGNORECASE)
RE_H3 = re.compile(r"^###\s+(.*)$")
RE_H2 = re.compile(r"^##\s+(.*)$")
RE_QUOTE = re.compile(r"^\s*>\s*(.*)$")
RE_CHECKBOX = re.compile(r"^\s*[*-]\s+\*\*\[\s*\]\s+(.*)$")
RE_PRINCIPLE = re.compile(r"^\s*(\d+)\.\s+(.*)$")
RE_VOICE = re.compile(r"^\s*(\d+)\.\s+\*\*(.+?)\*\*\s+\((.+?)\)\s*$")
RE_CREED = re.compile(r"DRIVING\s+CREED\s*\(\s*(\d+)\s*\)\s*:\s*(.+)$", re.IGNORECASE)
RE_WHISPER = re.compile(r"WHISPER\s*:\s*(.+)$", re.IGNORECASE)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def find_repo_root(start: Path) -> Path | None:
    cur = start.resolve()
    for p in [cur, *cur.parents]:
        if (p / "pyproject.toml").exists() and (p / "AGENTS.md").exists():
            return p
    return None


def to_repo_rel(p: Path) -> str:
    root = find_repo_root(p.parent)
    if not root:
        return p.as_posix()
    try:
        return p.resolve().relative_to(root).as_posix()
    except Exception:
        return p.as_posix()

def canonize_model_handle(text: str, target_token: str) -> str:
    # Keep this explicit and deterministic. We replace the legacy handle with a neutral token.
    # The original handle is still emitted in the JSON for provenance.
    return text.replace(MODEL_HANDLE_GEMINI_25PP_0325, target_token)


def extract(text: str, *, canonical_target: str) -> dict:
    def normalize_whisper(s: str) -> str:
        s = s.strip()
        # Common source shapes: _"..."_ or "_'...'_"
        s = s.strip("_").strip()
        s = s.strip("*").strip()
        s = s.strip("\"'").strip()
        return s

    def unescape_markdown_line(s: str) -> str:
        # The SSOT variant may be stored with pervasive markdown escapes like "\#\#".
        # Remove escapes only for a small safe set of markdown punctuation.
        for ch in ("#", "*", ">", "_", "[", "]", "(", ")", ".", "-",):
            s = s.replace("\\" + ch, ch)
        return s

    lines = [canonize_model_handle(unescape_markdown_line(ln), canonical_target) for ln in text.splitlines()]

    acts: list[dict] = []
    modules: list[dict] = []
    guiding_principles: list[str] = []
    ideologies: list[str] = []
    system_instructions: list[str] = []
    voice_quotes: list[str] = []
    voices: list[dict] = []

    cur_act: dict | None = None
    cur_module: dict | None = None
    in_system = False
    in_guiding = False
    in_ideologies = False
    in_voices = False
    cur_voice: dict | None = None

    def flush_act() -> None:
        nonlocal cur_act
        if cur_act:
            acts.append(cur_act)
            cur_act = None

    def flush_module() -> None:
        nonlocal cur_module
        if cur_module:
            modules.append(cur_module)
            cur_module = None

    def flush_voice() -> None:
        nonlocal cur_voice
        if cur_voice:
            voices.append(cur_voice)
            cur_voice = None

    for raw in lines:
        ln = raw.rstrip()
        if not ln.strip():
            continue

        m = RE_ACT.match(ln)
        if m:
            flush_act()
            flush_voice()
            act_id = m.group(1).strip()
            title = m.group(2).strip()
            cur_act = {"id": act_id, "title": title}
            in_system = False
            in_guiding = False
            in_ideologies = False
            in_voices = "INNER VOICES" in title.upper()
            continue

        m = RE_MODULE.match(ln)
        if m:
            flush_module()
            title = m.group(2).strip()
            # Minimal markdown scrubbing for titles.
            title = title.strip("*").strip()
            if title.startswith("**") and title.endswith("**") and len(title) >= 4:
                title = title[2:-2].strip()
            cur_module = {"id": int(m.group(1)), "title": title}
            in_system = False
            continue

        m = RE_H2.match(ln)
        if m:
            h2 = m.group(1).strip()
            up = h2.upper()
            if "SYSTEM" in up and "INSTRUCTIONS" in up:
                in_system = True
            if "INTERNAL SANCTUM ROSTER" in up or "INNER VOICES" in up:
                in_voices = True
            continue

        m = RE_H3.match(ln)
        if m:
            h3 = m.group(1).strip()
            # Coarse section toggles.
            in_system = "SYSTEM" in h3.upper()
            in_guiding = "GUIDING" in h3.upper() and "PRINCIPLES" in h3.upper()
            in_ideologies = "IDEOLOGICAL" in h3.upper()
            if "INTERNAL SANCTUM" in h3.upper() or "INNER VOICES" in h3.upper():
                in_voices = True
            continue

        qm = RE_QUOTE.match(ln)
        if qm:
            q = qm.group(1).strip()
            if in_system:
                system_instructions.append(q)
            if in_guiding:
                pm = RE_PRINCIPLE.match(q)
                if pm:
                    guiding_principles.append(pm.group(2).strip())
            # A few quotes are strong "voice anchors"; keep first sentence-ish.
            if q.startswith("*\"") or q.startswith("\"") or q.startswith("*'") or q.startswith("'"):
                voice_quotes.append(q)
            continue

        if in_voices:
            vm = RE_VOICE.match(ln)
            if vm:
                flush_voice()
                cur_voice = {
                    "id": int(vm.group(1)),
                    "name": vm.group(2).strip(),
                    "title": vm.group(3).strip(),
                }
                continue
            if cur_voice:
                cm = RE_CREED.search(ln)
                if cm:
                    cur_voice["creed_id"] = int(cm.group(1))
                    cur_voice["creed"] = cm.group(2).strip()
                    continue
                wm = RE_WHISPER.search(ln)
                if wm and "whisper" not in cur_voice:
                    cur_voice["whisper"] = normalize_whisper(wm.group(1))
                    continue

        cm = RE_CHECKBOX.match(ln)
        if cm and in_ideologies:
            ideologies.append(cm.group(1).strip())
            continue

        if in_guiding:
            # Pull "1. ..." style principle text from quoted blocks.
            if " **" in ln and ln.lstrip().startswith(">"):
                cleaned = ln.lstrip(">").strip()
                guiding_principles.append(cleaned)
            continue

    flush_act()
    flush_module()
    flush_voice()

    # Deterministic trimming.
    system_instructions = system_instructions[:80]
    voice_quotes = voice_quotes[:20]
    guiding_principles = guiding_principles[:40]
    ideologies = ideologies[:40]

    return {
        "schema_version": 1,
        "kind": "voicepack",
        "title": "The Iron Maiden",
        "source_format": "iron-maiden-md",
        "canonical_target": canonical_target,
        "model_handle_original": MODEL_HANDLE_GEMINI_25PP_0325,
        "acts": acts,
        "modules": modules,
        "system_instructions": system_instructions,
        "guiding_principles": guiding_principles,
        "ideology_options": ideologies,
        "voice_quotes": voice_quotes,
        "voices": voices,
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="Input markdown file.")
    ap.add_argument("--out", help="Output json path. Default: <input>.voicepack.json")
    ap.add_argument(
        "--canonical-target",
        default="OPERATOR",
        help="Neutral token to replace legacy model handles (default: OPERATOR).",
    )
    args = ap.parse_args(argv[1:])

    src = Path(args.input)
    if not src.exists():
        raise SystemExit(f"Not found: {src}")

    raw = src.read_text(encoding="utf-8", errors="replace")
    pack = extract(raw, canonical_target=args.canonical_target)
    pack["generated_on"] = utc_now_iso()
    pack["source"] = to_repo_rel(src)
    pack["source_sha256"] = sha256_text(raw)

    out = Path(args.out) if args.out else src.with_suffix(src.suffix + ".voicepack.json")
    out.write_text(json.dumps(pack, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(to_repo_rel(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv))
