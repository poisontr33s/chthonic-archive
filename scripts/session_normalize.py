#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: session_normalize.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Session Normalize — Convert raw copy-pasted session text into vampire-compatible JSONL.

Reads a raw paste from Codex Cloud, Copilot Chat, or Claude Code transcripts and
emits `transcript.jsonl` events in the exact shape that scripts/session-vampire.ts
already drains (user.message, assistant.message, tool.execution_start). Output lands
under manifest/sessions/normalized-<sha8>/ so `bun run session:vampire --session
normalized-<sha8>` works without modification.

@SID:           TOOL_SESSION_NORMALIZE_V1
@Shabti:        Curatrix
@Context:       Infrastructure / Session Forensics Bridge
@Implements:    Raw-Paste → Vampire-JSONL pipeline (chthonic-archive #B-landing)
@Purpose:       Source-aware multi-format normalizer for copy-pasted assistant
                transcripts; non-destructive, idempotent by input sha256[:8].

Usage:
    uv run scripts/session_normalize.py <input>
    uv run scripts/session_normalize.py <input> --source codex_cloud
    uv run scripts/session_normalize.py <input> --source auto --dry-run
    uv run scripts/session_normalize.py <input> --session-id custom-id
    uv run scripts/session_normalize.py <input> --out manifest/sessions/foo/

Flags:
    --source       auto | codex_cloud | copilot_chat | claude_code   (default: auto)
    --session-id   override synthetic id (default: normalized-<sha8>)
    --out          override output dir (default: manifest/sessions/<session-id>/)
    --dry-run      print summary, write nothing
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
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


REPO_ROOT = Path(__file__).resolve().parent.parent

CODEX_WORKED_FOR = re.compile(r"^Worked for (\d+m\s*)?\d+s?$", re.MULTILINE)
CODEX_TIMESTAMP = re.compile(r"^\d{1,2}:\d{2}\s?(AM|PM)$", re.MULTILINE)
COPILOT_HEADER = re.compile(r"^###\s+(User|Assistant)\b", re.MULTILINE)
CLAUDE_TOOL_ENVELOPE = re.compile(r"^(Bash|Read|Edit|Write|Glob|Grep|TodoWrite)\(", re.MULTILINE)
CLAUDE_SYSTEM_REMINDER = re.compile(r"<system-reminder>")

FENCED_CODE = re.compile(r"```([^\n`]*)\n([\s\S]*?)```")
COMMIT_REF_NEAR = re.compile(r"\b(?:commit|committed|pushed|sha)[:\s]+([0-9a-f]{7,40})\b", re.IGNORECASE)
FILE_ATTACHMENT_CARD = re.compile(r"^([\w.\-/\\]+\.\w+)\nDocument · \w+\nOpen$", re.MULTILINE)
FILES_CHANGED = re.compile(r"^(\d+)\s+files?\s+changed", re.MULTILINE)


def detect_source(text: str) -> str:
    if CODEX_WORKED_FOR.search(text) and CODEX_TIMESTAMP.search(text):
        return "codex_cloud"
    if COPILOT_HEADER.search(text):
        return "copilot_chat"
    if CLAUDE_TOOL_ENVELOPE.search(text) or CLAUDE_SYSTEM_REMINDER.search(text):
        return "claude_code"
    return "unknown"


def make_event(event_type: str, data: dict, timestamp: str | None = None) -> dict:
    return {
        "type": event_type,
        "data": data,
        "id": str(uuid.uuid4()),
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
        "parentId": None,
    }


def emit_session_start(session_id: str, source: str) -> dict:
    return make_event(
        "session.start",
        {
            "sessionId": session_id,
            "version": 1,
            "producer": "session-normalize",
            "originalSource": source,
            "startTime": datetime.now(timezone.utc).isoformat(),
        },
    )


def emit_user_message(content: str) -> dict:
    return make_event("user.message", {"content": content.strip()})


def emit_assistant_message(content: str, *, duration_s: int | None = None) -> dict:
    data: dict = {"content": content.strip()}
    if duration_s is not None:
        data["durationSeconds"] = duration_s
    return make_event("assistant.message", data)


def emit_tool_execution(tool_name: str, arguments: dict) -> dict:
    return make_event(
        "tool.execution_start",
        {"toolName": tool_name, "name": tool_name, "arguments": arguments},
    )


def parse_worked_for(line: str) -> int | None:
    m = re.match(r"^Worked for (?:(\d+)m\s*)?(\d+)s?$", line.strip())
    if not m:
        return None
    minutes = int(m.group(1) or 0)
    seconds = int(m.group(2) or 0)
    return minutes * 60 + seconds


def parse_codex_cloud(text: str) -> Iterator[dict]:
    """
    Codex Cloud paste has loose structure. Heuristic:
      - Timestamp lines (e.g. "3:22 AM") mark turn boundaries (next non-empty block is user)
      - "Worked for Nm Ns" lines mark assistant turn START (with duration)
      - Everything between markers is the turn body
      - File-attachment cards become tool.execution_start events for create_file
      - Commit refs in assistant body kept in body (vampire's extractCommits handles them)
    """
    lines = text.splitlines()
    segments: list[tuple[str, str, int | None]] = []  # (role, body, duration)
    current_role = "user"
    current_lines: list[str] = []
    current_duration: int | None = None

    def flush() -> None:
        if any(ln.strip() for ln in current_lines):
            body = "\n".join(current_lines).strip()
            segments.append((current_role, body, current_duration))
        current_lines.clear()

    for line in lines:
        stripped = line.strip()
        if CODEX_TIMESTAMP.match(stripped):
            flush()
            current_role = "user"
            current_duration = None
            continue
        duration = parse_worked_for(stripped) if stripped.startswith("Worked for") else None
        if duration is not None:
            flush()
            current_role = "assistant"
            current_duration = duration
            continue
        current_lines.append(line)
    flush()

    for role, body, duration in segments:
        if not body:
            continue
        if role == "user":
            yield emit_user_message(body)
        else:
            yield emit_assistant_message(body, duration_s=duration)
            for match in FILE_ATTACHMENT_CARD.finditer(body):
                yield emit_tool_execution("create_file", {"filePath": match.group(1)})


def parse_copilot_chat(text: str) -> Iterator[dict]:
    """
    Minimal Copilot Chat parser (skeleton). Splits on ### User / ### Assistant
    headers, emits one event per section. Tool extraction is stubbed.
    """
    parts = COPILOT_HEADER.split(text)
    # split puts capture groups between text — parts: [pre, role1, body1, role2, body2, ...]
    if len(parts) <= 1:
        if text.strip():
            yield emit_user_message(text)
        return
    pre = parts[0].strip()
    if pre:
        yield emit_user_message(pre)
    for i in range(1, len(parts), 2):
        role = parts[i].strip().lower()
        body = parts[i + 1] if i + 1 < len(parts) else ""
        body = body.strip()
        if not body:
            continue
        if role == "user":
            yield emit_user_message(body)
        else:
            yield emit_assistant_message(body)


def parse_claude_code(text: str) -> Iterator[dict]:
    """
    Minimal Claude Code parser (skeleton). Treats whole paste as one assistant
    turn and extracts visible tool envelopes as tool.execution_start events.
    Refinement deferred until we have a real Claude Code paste to test against.
    """
    yield emit_assistant_message(text)
    for match in CLAUDE_TOOL_ENVELOPE.finditer(text):
        tool_name = match.group(1)
        yield emit_tool_execution(tool_name, {"raw": "parsed from paste"})


def parse_unknown(text: str) -> Iterator[dict]:
    """Fallback: emit whole text as a single user.message."""
    print("[session_normalize] WARNING: source unknown, emitting single user turn", file=sys.stderr)
    if text.strip():
        yield emit_user_message(text)


PARSERS = {
    "codex_cloud": parse_codex_cloud,
    "copilot_chat": parse_copilot_chat,
    "claude_code": parse_claude_code,
    "unknown": parse_unknown,
}


def normalize(input_path: Path, source: str, session_id: str) -> tuple[list[dict], dict]:
    text = input_path.read_text(encoding="utf-8", errors="replace")
    detected = source if source != "auto" else detect_source(text)
    parser = PARSERS.get(detected, parse_unknown)

    events: list[dict] = [emit_session_start(session_id, detected)]
    events.extend(parser(text))

    user_count = sum(1 for e in events if e["type"] == "user.message")
    assistant_count = sum(1 for e in events if e["type"] == "assistant.message")
    tool_count = sum(1 for e in events if e["type"] == "tool.execution_start")

    meta = {
        "sessionId": session_id,
        "schemaVersion": 1,
        "normalizer": "scripts/session_normalize.py",
        "normalizedAt": datetime.now(timezone.utc).isoformat(),
        "sourceFile": str(input_path),
        "sourceFormat": detected,
        "sourceRequested": source,
        "turnCount": user_count + assistant_count,
        "userMessages": user_count,
        "assistantMessages": assistant_count,
        "toolCalls": tool_count,
        "totalEvents": len(events),
    }
    return events, meta


def sha8_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:8]


def main() -> int:
    parser = argparse.ArgumentParser(prog="session_normalize")
    parser.add_argument("input", type=Path, help="Raw pasted session file (txt or pseudo-jsonl)")
    parser.add_argument(
        "--source",
        choices=["auto", "codex_cloud", "copilot_chat", "claude_code", "unknown"],
        default="auto",
    )
    parser.add_argument("--session-id", default=None, help="Override synthetic session id")
    parser.add_argument("--out", type=Path, default=None, help="Override output dir")
    parser.add_argument("--dry-run", action="store_true", help="Print summary, write nothing")
    args = parser.parse_args()

    if not args.input.exists():
        print(f"[session_normalize] ERROR: input not found: {args.input}", file=sys.stderr)
        return 2

    session_id = args.session_id or f"normalized-{sha8_of_file(args.input)}"
    out_dir = args.out or (REPO_ROOT / "manifest" / "sessions" / session_id)

    events, meta = normalize(args.input, args.source, session_id)

    summary = (
        f"[session_normalize] source={meta['sourceFormat']} session_id={session_id} "
        f"events={meta['totalEvents']} user={meta['userMessages']} "
        f"assistant={meta['assistantMessages']} tools={meta['toolCalls']}"
    )
    print(summary)

    if args.dry_run:
        print(f"[session_normalize] DRY-RUN: would write to {out_dir}/")
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    transcript_path = out_dir / "transcript.jsonl"
    meta_path = out_dir / "meta.json"

    with transcript_path.open("w", encoding="utf-8") as fh:
        for event in events:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[session_normalize] wrote {transcript_path}")
    print(f"[session_normalize] wrote {meta_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
