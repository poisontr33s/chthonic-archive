#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: structure_session_log.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Structure a raw session dump into a compact, navigable log.

Inputs are typically copy/paste transcripts with mixed prose and command output.
This script creates two artifacts next to the input:
- *_structured.txt: compressed, event-oriented log (low noise)
- *_pretty.md: readable markdown with sections and code blocks

Invocation:
  uv run scripts/structure_session_log.py <path-to-log>

@SID:           TOOL_STRUCTURE_SESSION_LOG_V1
@Shabti:        CLI Script
@Purpose:       Structure a raw session dump into a compact, navigable log.
"""

from __future__ import annotations

import re
import sys
import json
import hashlib
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path


def find_repo_root(start: Path) -> Path | None:
    cur = start.resolve()
    for p in [cur, *cur.parents]:
        if (p / "pyproject.toml").exists() and (p / "AGENTS.md").exists():
            return p
    return None


RE_ACTION = re.compile(r"^(?:Ran\\b|Edited file\\b|Worked for\\b|Review$|Undo$|\\+\\d+|-\\d+|\\d+ files changed\\b)")
RE_DIV = re.compile(r"^(?:=+|-{3,}|\\+[-+]{10,}\\+)$")
RE_INLINE_UV = re.compile(r"(uv run\\s+[^\\n]+)")
RE_INLINE_BUN = re.compile(r"(bun\\s+(?:audit|update|install)\\b[^\\n]*)")
RE_INLINE_GIT = re.compile(r"(git\\s+(?:add|status|diff|config)\\b[^\\n]*)")
RE_BUN_OUTPUT_VERSION = re.compile(r"^bun\\s+\\w+\\s+v\\d+")
RE_OUTPUTISH = re.compile(
    r"\\b("
    r"is supported|supported and valid|"
    r"now shows|shows the expected|"
    r"confirmed|passed clean|passed|failed|"
    r"exit\\s+\\d+|"
    r"usage:"
    r")\\b",
    re.IGNORECASE,
)


def _strip_leading_noise(s: str) -> str:
    # Trim common transcript markup / bullets while preserving "$" and "PS ...>" prompts.
    s = s.lstrip()
    for pref in (">", "`"):
        if s.startswith(pref):
            s = s[len(pref):].lstrip()
    for bullet in ("- ", "* "):
        if s.startswith(bullet):
            s = s[len(bullet):].lstrip()
            break
    return s


def is_cmd_line(line: str) -> bool:
    s = _strip_leading_noise(line.rstrip())
    if not s:
        return False
    # Common "not actually a command" markers seen in summaries.
    if any(tok in s for tok in ("<", ">", "…", "→")):
        return False

    # PowerShell prompt lines.
    if s.startswith("PS ") and (">" in s):
        return True

    # "$ ..." lines (PowerShell vars, env, scriptblocks, etc.).
    if s.startswith("$"):
        return True

    # Canonical invocations.
    starters = ("uv run ", "bun ", "git ", "node ", "python ", "cargo ", "rg ", "pwsh ")
    if s.startswith(starters):
        # Demote common "looks like a command but is actually prose/output" lines.
        # Example: "uv run script.py is supported and valid ..." (explanatory sentence).
        if RE_OUTPUTISH.search(s) and not s.strip().endswith((".py", ".ps1", ".ts", ".js", ".exe")):
            return False
        # Demote tool "banner" output lines that look like versions, not invocations.
        if RE_BUN_OUTPUT_VERSION.match(s):
            return False
        return True

    return False


@dataclass
class Event:
    kind: str  # cmd|action|text|output
    lines: list[str]


def slurp(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def classify(line: str) -> str:
    s = line.rstrip()
    if not s.strip():
        return "blank"
    # Avoid classifying labels like "uv run standardization:" as commands.
    if is_cmd_line(s) and not s.strip().endswith(":"):
        return "cmd"
    if RE_ACTION.match(s):
        return "action"
    if RE_DIV.match(s):
        return "div"
    return "text"


def extract_events(lines: list[str]) -> list[Event]:
    events: list[Event] = []
    cur: Event | None = None
    capture_payload_for_action = False
    capture_payload_kind: str | None = None

    def flush() -> None:
        nonlocal cur
        if not cur:
            return
        # Drop trivial empty events.
        if any(ln.strip() for ln in cur.lines):
            events.append(cur)
        cur = None

    for ln in lines:
        t = classify(ln)
        if t in ("blank", "div"):
            flush()
            capture_payload_for_action = False
            capture_payload_kind = None
            continue
        kind = "text"
        if t == "cmd":
            kind = "cmd"
        elif t == "action":
            kind = "action"

        if kind == "text" and capture_payload_for_action and cur and cur.kind == "action":
            # Attach filenames/lists that follow action headers like "Edited file".
            # Guardrail: do not accidentally swallow prose into the ACTION block.
            s = ln.strip()
            looks_like_path = (
                ("/" in s or "\\" in s)
                or s.startswith(".")
                or bool(re.search(r"\\.[A-Za-z0-9]{1,6}$", s))
            )
            if capture_payload_kind == "edited_file":
                if looks_like_path:
                    cur.lines.append(ln.rstrip())
                    continue
            elif capture_payload_kind == "review":
                # Review payloads are usually bullets or paths; keep them but stop on long prose.
                if looks_like_path or s.startswith(("-", "*")) or len(s) < 120:
                    cur.lines.append(ln.rstrip())
                    continue

            # Break out: treat this as normal text, not action payload.
            capture_payload_for_action = False
            capture_payload_kind = None

        if kind == "text":
            # Promote inline command substrings inside prose to CMD events.
            # Keep this conservative to avoid false positives on phrases like "bun has crashed".
            emitted_cmd = False
            for rx in (RE_INLINE_UV, RE_INLINE_BUN, RE_INLINE_GIT):
                m = rx.search(ln)
                if not m:
                    continue
                cand = m.group(1).strip().strip("`")
                if "<" in cand or ">" in cand:
                    # Avoid promoting explanatory prose like "uv run <cmd> runs a command".
                    continue
                # Heuristic: only treat as a command if it looks like an invocation.
                if "uv run" in cand and not any(tok in cand for tok in (".py", ".ps1", "scripts/", ".codex/", ".claude/")):
                    continue
                flush()
                events.append(Event(kind="cmd", lines=[cand]))
                emitted_cmd = True
                break
            else:
                pass
            # If we emitted a cmd, skip adding this line to text.
            if emitted_cmd:
                # We emitted a command from this line; do not also keep it as NOTE text.
                continue

        if cur and cur.kind == kind:
            cur.lines.append(ln.rstrip())
        else:
            flush()
            cur = Event(kind=kind, lines=[ln.rstrip()])

        capture_payload_for_action = False
        if kind == "action":
            head = ln.strip().lower()
            if head in ("edited file", "review") or head.startswith("edited file"):
                capture_payload_for_action = True
                capture_payload_kind = "edited_file" if head.startswith("edited file") else "review"
    flush()
    return events


def compress_events(events: list[Event]) -> list[Event]:
    """
    KISS compression:
    - For long text blocks, keep first N lines and a count summary.
    - For command blocks, keep all command lines (usually small).
    """
    out: list[Event] = []
    for e in events:
        if e.kind in ("cmd", "action") and len(e.lines) > 1:
            # Normalize multi-line blocks into one event per line (better diffability).
            for ln in e.lines:
                if ln.strip():
                    out.append(Event(kind=e.kind, lines=[ln.strip()]))
            continue
        if e.kind == "text":
            # Aggressive: raw transcripts are huge; keep only the head of long prose/output blocks.
            limit = 8
            if len(e.lines) > 12:
                kept = e.lines[:limit]
                kept.append(f"...(truncated {len(e.lines) - limit} line(s))...")
                out.append(Event(kind=e.kind, lines=kept))
                continue
        out.append(e)
    return out


def render_structured_txt(events: list[Event]) -> str:
    parts: list[str] = []
    idx = 1
    for e in events:
        # Structured TXT is a compression artifact: keep only actionable events.
        if e.kind not in ("cmd", "action"):
            continue
        if e.kind == "action":
            # Drop low-information UI noise.
            head = (e.lines[0] if e.lines else "").strip().lower()
            if head in ("undo", "review", "ran command", "edited file"):
                continue
        parts.append(f"[{idx:04d}] {e.kind.upper()}")
        parts.extend(e.lines)
        parts.append("")
        idx += 1
    return "\n".join(parts).rstrip() + "\n"


def cmd_phase(cmd: str) -> str:
    s = cmd.strip().lower()
    if s.startswith("bun "):
        return "toolchain:bun"
    if s.startswith("uv "):
        return "toolchain:uv"
    if "polish_skill.py" in s:
        return "skills:polisher"
    if "skill_audit.py" in s:
        return "skills:audit"
    if "mailbox_" in s or "check_mailbox_" in s:
        return "mailbox"
    if "hf_" in s or "huggingface" in s:
        return "hf"
    if s.startswith("git "):
        return "git"
    return "other"


def build_structured_json(src: Path, raw_text: str, events: list[Event]) -> dict:
    repo_root = find_repo_root(src.parent)
    if repo_root:
        try:
            src_display = src.resolve().relative_to(repo_root).as_posix()
        except Exception:
            src_display = src.as_posix()
    else:
        src_display = src.as_posix()

    cmds: list[dict] = []
    actions: list[str] = []
    phases: dict[str, list[int]] = {}

    for i, e in enumerate(events, start=1):
        if e.kind == "cmd" and e.lines:
            cmd = e.lines[0]
            ph = cmd_phase(cmd)
            phases.setdefault(ph, []).append(i)
            cmds.append(
                {
                    "event_id": i,
                    "cmd": cmd,
                    "phase": ph,
                }
            )
        elif e.kind == "action" and e.lines:
            actions.append(e.lines[0])

    payload = {
        "schema_version": 1,
        "generated_on": utc_now_iso(),
        "source": src_display,
        "source_sha256": sha256_text(raw_text),
        "counts": {
            "events": len(events),
            "cmd": sum(1 for e in events if e.kind == "cmd"),
            "action": sum(1 for e in events if e.kind == "action"),
            "note": sum(1 for e in events if e.kind == "text"),
        },
        "phases": phases,
        "commands": cmds,
        "actions": actions,
        "events": [
            {
                "id": idx,
                "kind": e.kind,
                "lines": list(e.lines),
            }
            for idx, e in enumerate(events, start=1)
        ],
    }
    return payload


def render_pretty_md(src: Path, events: list[Event]) -> str:
    repo_root = find_repo_root(src.parent)
    if repo_root:
        try:
            src_display = src.resolve().relative_to(repo_root).as_posix()
        except Exception:
            src_display = src.as_posix()
    else:
        src_display = src.as_posix()

    cmd_blocks = sum(1 for e in events if e.kind == "cmd")
    action_blocks = sum(1 for e in events if e.kind == "action")
    parts: list[str] = []
    parts.append("---")
    parts.append("type: structured-session-log")
    parts.append(f"source: {src_display}")
    parts.append("---")
    parts.append("")
    parts.append(f"# Structured Session Log: `{src.name}`")
    parts.append("")
    parts.append("## Summary")
    parts.append(f"- Events: `{len(events)}`")
    parts.append(f"- Commands: `{cmd_blocks}`")
    parts.append(f"- Actions: `{action_blocks}`")
    parts.append("")
    parts.append("## Index")
    parts.append("- Each entry is an event block derived from the raw transcript.")
    parts.append("")
    idx = 1
    def keep_note(lines: list[str]) -> bool:
        blob = "\n".join(lines).lower()
        keywords = [
            "panic(",
            "segmentation fault",
            "oh no: bun has crashed",
            "wrote:",
            "verify:",
            "passed",
            "failed",
            "vulnerab",
            "audit:",
            "generated:",
            "schema_version",
        ]
        return any(k in blob for k in keywords)

    for e in events:
        if e.kind == "action":
            head = (e.lines[0] if e.lines else "").strip().lower()
            if head in ("undo", "review", "ran command", "edited file"):
                continue
        if e.kind == "text" and not keep_note(e.lines):
            continue
        title = "Note"
        if e.kind == "cmd":
            title = "Command"
        elif e.kind == "action":
            title = "Action"
        parts.append(f"### {idx:04d} {title}")
        parts.append("")
        if e.kind in ("cmd", "action"):
            parts.append("```text")
            parts.extend(e.lines)
            parts.append("```")
        else:
            # Markdown paragraphs; keep exact lines.
            parts.extend(e.lines)
        parts.append("")
        idx += 1
    return "\n".join(parts).rstrip() + "\n"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: structure_session_log.py <path-to-log>")
        return 2

    src = Path(argv[1])
    if not src.exists():
        print(f"not found: {src}")
        return 2

    raw_text = src.read_text(encoding="utf-8", errors="replace")
    raw_lines = raw_text.splitlines()
    events = extract_events(raw_lines)
    events = compress_events(events)

    structured_txt = src.with_name(src.name + "_structured.txt")
    structured_json = src.with_name(src.name + "_structured.json")
    pretty_md = src.with_name(src.name + "_pretty.md")

    structured_txt.write_text(render_structured_txt(events), encoding="utf-8", newline="\n")
    structured_json.write_text(
        json.dumps(build_structured_json(src, raw_text, events), indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    pretty_md.write_text(render_pretty_md(src, events), encoding="utf-8", newline="\n")

    repo_root = find_repo_root(src.parent)
    def display(p: Path) -> str:
        if repo_root:
            try:
                return p.resolve().relative_to(repo_root).as_posix()
            except Exception:
                return p.as_posix()
        return p.as_posix()

    print(f"Wrote: {display(structured_txt)}")
    print(f"Wrote: {display(structured_json)}")
    print(f"Wrote: {display(pretty_md)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
