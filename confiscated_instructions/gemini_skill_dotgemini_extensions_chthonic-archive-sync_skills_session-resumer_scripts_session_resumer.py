#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: session_resumer.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🔥 THE FOUNDRY
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Session Resumer.

Purpose:
- Take a raw copy/paste session transcript and produce a professional warm-start resume packet.
- Reuse repo-native structuring (scripts/structure_session_log.py), then summarize the structured JSON.
- Optionally append the resume into a SESSION_TRAIL_*.md as a new section.

Invocation:
  uv run .codex/skills/session-resumer/scripts/session_resumer.py <path-to-raw-log>
  <paste> | uv run .codex/skills/session-resumer/scripts/session_resumer.py - --write-stdin <path-to-write>
  uv run .codex/skills/session-resumer/scripts/session_resumer.py <path> --trail <SESSION_TRAIL_*.md>

@SID:           TOOL_SESSION_RESUMER_V1
@Shabti:        CLI Script
@Purpose:       Session Resumer.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for p in [cur, *cur.parents]:
        if (p / "pyproject.toml").exists() and (p / "AGENTS.md").exists():
            return p
    raise SystemExit(
        "Could not locate repo root (expected pyproject.toml + AGENTS.md). "
        "Run from the repo root, or pass an absolute path inside it."
    )


REPO_ROOT = find_repo_root(Path(__file__))
STRUCTURER = REPO_ROOT / "scripts" / "structure_session_log.py"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_structurer(target: Path) -> None:
    cmd = ["uv", "run", str(STRUCTURER), str(target)]
    proc = subprocess.run(cmd, cwd=REPO_ROOT, check=False)
    if proc.returncode != 0:
        raise SystemExit(f"Structurer failed for {target.as_posix()} (exit {proc.returncode})")


def slurp_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel_display(p: Path) -> str:
    try:
        return p.resolve().relative_to(REPO_ROOT).as_posix()
    except Exception:
        return p.as_posix()


def summarize_commands(payload: dict, limit: int = 18) -> list[str]:
    cmds = payload.get("commands") or []
    if not isinstance(cmds, list):
        return []
    out: list[str] = []
    for c in cmds[-limit:]:
        if isinstance(c, dict) and isinstance(c.get("cmd"), str):
            out.append(c["cmd"].strip())
    return out


def phase_table(payload: dict) -> list[tuple[str, int]]:
    phases = payload.get("phases") or {}
    if not isinstance(phases, dict):
        return []
    out: list[tuple[str, int]] = []
    for k, v in phases.items():
        if isinstance(k, str) and isinstance(v, list):
            out.append((k, len(v)))
    out.sort(key=lambda kv: (-kv[1], kv[0]))
    return out


def extract_candidate_paths(payload: dict, limit: int = 25) -> list[str]:
    """
    Heuristic: find repo-ish paths in commands. This is intentionally conservative.
    """
    cmds = payload.get("commands") or []
    if not isinstance(cmds, list):
        return []
    seen: set[str] = set()
    out: list[str] = []
    # Avoid "bad range" issues by keeping '-' at the end of the class.
    rx_abs_or_dot = re.compile(r"(?:(?:\\.\\.?)[/\\\\]|[A-Za-z]:[/\\\\])[\\w./\\\\-]+")
    rx_repoish = re.compile(r"(?<![A-Za-z0-9_])(?:\\.codex|\\.claude|codex|claude|scripts|src|docs|game)(?:/|\\\\)[\\w./\\\\-]+")
    for c in cmds:
        if not isinstance(c, dict):
            continue
        s = c.get("cmd")
        if not isinstance(s, str):
            continue
        for m in rx_abs_or_dot.finditer(s):
            cand = m.group(0).replace("\\\\", "/").replace("\\", "/").strip()
            if cand.endswith(("/", "\\")):
                cand = cand[:-1]
            if re.fullmatch(r"[A-Za-z]:", cand):
                continue
            if not cand or cand in seen:
                continue
            seen.add(cand)
            out.append(cand)
            if len(out) >= limit:
                return out

        for m in rx_repoish.finditer(s):
            cand = m.group(0).replace("\\\\", "/").replace("\\", "/").strip()
            if cand.endswith("/"):
                cand = cand[:-1]
            if not cand or cand in seen:
                continue
            # Only keep repo-relative paths that actually exist (reduces false positives).
            try:
                if not (REPO_ROOT / cand).exists():
                    continue
            except Exception:
                continue
            seen.add(cand)
            out.append(cand)
            if len(out) >= limit:
                return out
    return out


@dataclass(frozen=True)
class ResumePaths:
    structured_json: Path
    resume_md: Path


def compute_outputs(src: Path) -> ResumePaths:
    structured_json = src.with_name(src.name + "_structured.json")
    resume_md = src.with_name(src.name + "_resume.md")
    return ResumePaths(structured_json=structured_json, resume_md=resume_md)


def looks_like_google_ai_studio_python_export(text: str) -> bool:
    # Common pattern in Google AI Studio Python exports using google-genai SDK.
    return (
        "from google import genai" in text
        and "types.Content(" in text
        and "types.Part.from_text" in text
        and "role=" in text
    )


def extract_google_ai_studio_transcript(py_text: str) -> str:
    """
    Convert a Google AI Studio Python export into a plain transcript.

    We extract (role, text) pairs from patterns like:
      types.Content(role="user", parts=[types.Part.from_text(text=\"\"\"...\"\"\")])

    This is intentionally tolerant (regex-based) because exports vary slightly.
    """
    # Avoid trying to parse nested parentheses with regex. Instead:
    # 1) find each role="..." marker and treat text until the next role marker as that role's segment
    # 2) extract any text=\"\"\"...\"\"\" blocks inside the segment
    role_rx = re.compile(r'role\s*=\s*"(user|model|system)"')
    text_rx = re.compile(r'text\s*=\s*"""(.*?)"""', re.DOTALL)

    role_marks = list(role_rx.finditer(py_text))
    if not role_marks:
        return ""

    out: list[str] = []
    for i, rm in enumerate(role_marks):
        role = rm.group(1).strip()
        seg_start = rm.end()
        seg_end = role_marks[i + 1].start() if i + 1 < len(role_marks) else len(py_text)
        seg = py_text[seg_start:seg_end]
        texts = [m.group(1) for m in text_rx.finditer(seg)]
        if not texts:
            continue

        out.append(f"### ROLE: {role}")
        out.append("")
        for t in texts:
            out.append(t.replace("\r\n", "\n").replace("\r", "\n").strip())
            out.append("")
        out.append("----")
        out.append("")

    return "\n".join(out).rstrip() + "\n"


def _role_norm(role: str) -> str:
    r = (role or "").strip().lower()
    if r in ("assistant", "model"):
        return "model"
    if r in ("user",):
        return "user"
    if r in ("system", "developer"):
        return "system"
    return r or "unknown"


def _content_to_text(content: Any) -> str:
    """
    Best-effort flatten for common LLM transcript shapes.
    - string
    - list of {type,text} parts
    - list of strings
    - dict with 'text'
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks: list[str] = []
        for it in content:
            if isinstance(it, str):
                chunks.append(it)
                continue
            if isinstance(it, dict):
                if isinstance(it.get("text"), str):
                    chunks.append(it["text"])
                    continue
                # Some providers: {type:"text", text:"..."}
                if it.get("type") == "text" and isinstance(it.get("text"), str):
                    chunks.append(it["text"])
                    continue
        return "\n".join([c for c in chunks if c.strip()]).strip()
    if isinstance(content, dict):
        if isinstance(content.get("text"), str):
            return content["text"]
    return str(content).strip()


def canonicalize_messages(messages: list[dict[str, Any]]) -> dict[str, Any]:
    out_msgs: list[dict[str, Any]] = []
    for idx, m in enumerate(messages, start=1):
        role = _role_norm(str(m.get("role", "")))
        text = _content_to_text(m.get("content"))
        if not text.strip():
            continue
        out_msgs.append(
            {
                "id": idx,
                "role": role,
                "content": text,
            }
        )
    return {
        "schema_version": 1,
        "type": "canonical-session-transcript",
        "generated_on": utc_now_iso(),
        "messages": out_msgs,
    }


def render_role_transcript_from_canonical(canon: dict[str, Any]) -> str:
    msgs = canon.get("messages") or []
    if not isinstance(msgs, list):
        return ""
    out: list[str] = []
    for m in msgs:
        if not isinstance(m, dict):
            continue
        role = _role_norm(str(m.get("role", "")))
        text = _content_to_text(m.get("content"))
        if not text.strip():
            continue
        out.append(f"### ROLE: {role}")
        out.append("")
        out.append(text.replace("\r\n", "\n").replace("\r", "\n").strip())
        out.append("")
        out.append("----")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def try_parse_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None


def try_canonicalize_from_json(obj: Any) -> dict[str, Any] | None:
    """
    Recognize a few common transcript JSON layouts and convert to canonical schema.
    """
    # OpenAI-ish: {"messages":[{"role":"user","content":"..."}]}
    if isinstance(obj, dict) and isinstance(obj.get("messages"), list):
        msgs = obj["messages"]
        if all(isinstance(x, dict) for x in msgs):
            return canonicalize_messages(msgs) | {"source_format": "messages[]"}

    # Gemini-ish: {"contents":[{"role":"user","parts":[{"text":"..."}]}]}
    if isinstance(obj, dict) and isinstance(obj.get("contents"), list):
        msgs: list[dict[str, Any]] = []
        for c in obj["contents"]:
            if not isinstance(c, dict):
                continue
            role = c.get("role")
            parts = c.get("parts")
            # parts can be list of {text:"..."} or similar
            msgs.append({"role": role, "content": parts})
        if msgs:
            return canonicalize_messages(msgs) | {"source_format": "contents[]"}

    # Flat list: [{"role":..,"content":..}, ...]
    if isinstance(obj, list) and obj and all(isinstance(x, dict) for x in obj):
        if any("role" in x and ("content" in x or "text" in x) for x in obj):
            msgs = []
            for x in obj:
                content = x.get("content")
                if content is None and isinstance(x.get("text"), str):
                    content = x["text"]
                msgs.append({"role": x.get("role"), "content": content})
            return canonicalize_messages(msgs) | {"source_format": "list"}

    return None


def normalize_source_to_text(src: Path, force_extract: bool, emit_canonical: bool) -> Path:
    """
    Return a path to a plaintext transcript suitable for structuring.

    - Plain logs (.txt/.md/.log) are treated as-is.
    - Provider exports:
      - Google AI Studio Python export (.py) -> *_transcript.txt
      - JSON transcripts (messages/contents layouts) -> *_transcript.txt + *_canonical.json
    """
    suf = src.suffix.lower()
    if suf in (".txt", ".md", ".log"):
        return src

    if suf == ".py":
        py_text = src.read_text(encoding="utf-8", errors="replace")
        if force_extract or looks_like_google_ai_studio_python_export(py_text):
            transcript = extract_google_ai_studio_transcript(py_text)
            if not transcript.strip():
                raise SystemExit(
                    "Failed to extract transcript from AI Studio Python export. "
                    "Expected role=... plus text=\"\"\"...\"\"\" blocks."
                )
            out = src.with_name(src.name + "_transcript.txt")
            out.write_text(transcript, encoding="utf-8", newline="\n")
            return out

    if suf == ".json":
        obj = try_parse_json(src)
        canon = try_canonicalize_from_json(obj)
        if canon:
            # add minimal provenance fields
            canon["source"] = rel_display(src)
            try:
                canon["source_sha256"] = sha256_file(src)
            except Exception:
                pass
            canon_path = src.with_name(src.name + "_canonical.json")
            transcript_path = src.with_name(src.name + "_transcript.txt")
            if emit_canonical:
                canon_path.write_text(json.dumps(canon, indent=2) + "\n", encoding="utf-8", newline="\n")
            transcript = render_role_transcript_from_canonical(canon)
            transcript_path.write_text(transcript, encoding="utf-8", newline="\n")
            return transcript_path

    return src


### (normalize_source_to_text redefined above with broader, provider-agnostic support)


def render_resume_md(src: Path, payload: dict) -> str:
    counts = payload.get("counts") or {}
    actions = payload.get("actions") or []
    if not isinstance(actions, list):
        actions = []
    drop_actions = {"undo", "review", "ran command", "edited file"}
    actions = [a for a in actions if isinstance(a, str) and a.strip().lower() not in drop_actions]

    cmd_tail = summarize_commands(payload, limit=18)
    phases = phase_table(payload)
    paths = extract_candidate_paths(payload, limit=25)
    cmd_count = counts.get("cmd") if isinstance(counts, dict) else None
    action_count = counts.get("action") if isinstance(counts, dict) else None

    parts: list[str] = []
    parts.append("---")
    parts.append("type: session-resume")
    parts.append(f"generated_on: {utc_now_iso()}")
    parts.append(f"source: {payload.get('source', rel_display(src))}")
    if isinstance(payload.get("source_sha256"), str):
        parts.append(f"source_sha256: {payload['source_sha256']}")
    parts.append("schema: 1")
    parts.append("---")
    parts.append("")
    parts.append(f"# Session Resume: `{src.name}`")
    parts.append("")
    parts.append("## Snapshot")
    parts.append(f"- Generated: `{parts[2].split(': ',1)[1]}`")
    if isinstance(counts, dict):
        ev = counts.get("events")
        cmd = counts.get("cmd")
        act = counts.get("action")
        note = counts.get("note")
        parts.append(f"- Events: `{ev}` | Commands: `{cmd}` | Actions: `{act}` | Notes: `{note}`")
    parts.append("")
    parts.append("## Activity By Phase")
    if phases:
        for k, n in phases:
            parts.append(f"- `{k}`: `{n}`")
    else:
        parts.append("- (no phase data)")
    parts.append("")
    parts.append("## What Happened (High Signal)")
    if actions:
        for a in actions[:24]:
            if isinstance(a, str) and a.strip():
                parts.append(f"- {a.strip()}")
    else:
        parts.append("- (no explicit actions captured)")
    parts.append("")
    parts.append("## Command Tail (Last ~18)")
    if cmd_tail:
        parts.append("```text")
        parts.extend(cmd_tail)
        parts.append("```")
    else:
        parts.append("```text")
        parts.append("(no commands captured)")
        parts.append("```")
    parts.append("")
    if (cmd_count == 0 or cmd_count is None) and (action_count == 0 or action_count is None):
        # For narrative transcripts, the structurer yields notes only. Provide a dialogue tail so the
        # resume is still useful for model-agnostic warm-start.
        try:
            raw = src.read_text(encoding="utf-8", errors="replace")
        except Exception:
            raw = ""
        if "### ROLE:" in raw:
            blocks: list[tuple[str, str]] = []
            cur_role: str | None = None
            cur_lines: list[str] = []
            for ln in raw.splitlines():
                if ln.startswith("### ROLE:"):
                    if cur_role is not None and any(x.strip() for x in cur_lines):
                        blocks.append((cur_role, "\n".join(cur_lines).strip()))
                    cur_role = ln.split(":", 1)[1].strip()
                    cur_lines = []
                    continue
                if ln.strip() == "----":
                    if cur_role is not None and any(x.strip() for x in cur_lines):
                        blocks.append((cur_role, "\n".join(cur_lines).strip()))
                    cur_role = None
                    cur_lines = []
                    continue
                if cur_role is not None:
                    cur_lines.append(ln)
            if cur_role is not None and any(x.strip() for x in cur_lines):
                blocks.append((cur_role, "\n".join(cur_lines).strip()))

            if blocks:
                parts.append("## Dialogue Tail (Last 6 Turns)")
                parts.append("")
                for role, text in blocks[-6:]:
                    snippet = text.strip()
                    if len(snippet) > 700:
                        snippet = snippet[:700].rstrip() + "...(truncated)..."
                    parts.append(f"### {role}")
                    parts.append("")
                    parts.append(snippet)
                    parts.append("")

    parts.append("## Files / Paths Touched (Heuristic)")
    if paths:
        for p in paths:
            parts.append(f"- `{p}`")
    else:
        parts.append("- (none detected)")
    parts.append("")
    parts.append("## Resume: Next Actions (Fill This In)")
    parts.append("1. ")
    parts.append("2. ")
    parts.append("3. ")
    parts.append("")
    parts.append("## Resume: Open Questions / Decisions Needed")
    parts.append("1. ")
    parts.append("2. ")
    parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def append_into_trail(trail_path: Path, resume_md: Path) -> None:
    if not trail_path.exists():
        raise SystemExit(f"Trail not found: {trail_path}")
    resume_text = resume_md.read_text(encoding="utf-8", errors="replace").strip()
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    block = []
    block.append("")
    block.append(f"## Auto-Resume Insert ({stamp})")
    block.append("")
    block.append(f"Source resume: `{rel_display(resume_md)}`")
    block.append("")
    block.append(resume_text)
    block.append("")
    trail_path.write_text(
        trail_path.read_text(encoding="utf-8", errors="replace").rstrip() + "\n" + "\n".join(block),
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="Path to raw log file, or '-' to read stdin.")
    ap.add_argument(
        "--write-stdin",
        dest="write_stdin",
        help="If source is '-', write stdin to this path (relative to repo root unless absolute).",
    )
    ap.add_argument(
        "--extract-ai-studio",
        action="store_true",
        help="If source is a Google AI Studio Python export, force extraction into *_transcript.txt before structuring.",
    )
    ap.add_argument(
        "--emit-canonical",
        action="store_true",
        help="When normalizing JSON transcripts, also write *_canonical.json (canonical-session-transcript schema).",
    )
    ap.add_argument(
        "--trail",
        dest="trail",
        help="Optional: append the generated resume into this SESSION_TRAIL_*.md path.",
    )
    args = ap.parse_args()

    if args.source == "-":
        if not args.write_stdin:
            raise SystemExit("When source is '-', you must pass --write-stdin <path-to-write>.")
        raw = Path(args.write_stdin)
        src = (REPO_ROOT / raw).resolve() if not raw.is_absolute() else raw.resolve()
        src.parent.mkdir(parents=True, exist_ok=True)
        stdin_text = sys.stdin.read()
        src.write_text(stdin_text, encoding="utf-8", newline="\n")
    else:
        raw = Path(args.source)
        src = (REPO_ROOT / raw).resolve() if not raw.is_absolute() else raw.resolve()

    if not src.exists():
        raise SystemExit(f"Not found: {src}")

    normalized = normalize_source_to_text(
        src,
        force_extract=bool(args.extract_ai_studio),
        emit_canonical=bool(args.emit_canonical),
    )
    outs = compute_outputs(normalized)

    # Ensure structured artifacts exist; they are part of the resume packet.
    must_restructure = not outs.structured_json.exists()
    if outs.structured_json.exists():
        try:
            prior = slurp_json(outs.structured_json)
            prior_sha = prior.get("source_sha256")
            cur_sha = sha256_file(normalized)
            if isinstance(prior_sha, str) and prior_sha != cur_sha:
                must_restructure = True
        except Exception:
            must_restructure = True

    if must_restructure:
        run_structurer(normalized)

    payload = slurp_json(outs.structured_json)
    outs.resume_md.write_text(render_resume_md(normalized, payload), encoding="utf-8", newline="\n")

    if args.trail:
        tp = Path(args.trail)
        trail_path = (REPO_ROOT / tp).resolve() if not tp.is_absolute() else tp.resolve()
        append_into_trail(trail_path, outs.resume_md)

    print(f"Wrote: {rel_display(outs.resume_md)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
