#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: pid_reader.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🏛️ THE HYPOSTYLE
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ mas_mcp/server.py
# ║   └─◄ scripts/chthonic-shell-hook.ps1
# ╚════════════════════════════════════════════════════════════════════════════

"""
pid_reader.py — Terminal Session Manifest Reader Logic.

@SID:           LOGIC_PID_READER_V1
@Shabti:        Logic
@Purpose:       Read and structure manifest/terminal_session.jsonl and
                manifest/terminal_pids.json for the mas_pid_reader MCP tool.
                Produces high-quality machine-readable data suitable for
                documentation supplementation and CI gate consumption.
@DataSources:   manifest/terminal_session.jsonl (chthonic-shell-hook.ps1)
                manifest/terminal_pids.json (chthonic-shell-hook.ps1)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


_MANIFEST_RELPATH = "manifest/terminal_session.jsonl"
_PIDS_RELPATH = "manifest/terminal_pids.json"


def _load_pids(pids_path: Path) -> dict:
    if not pids_path.exists():
        return {}
    try:
        return json.loads(pids_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _load_entries(session_path: Path) -> list[dict]:
    if not session_path.exists():
        return []
    entries = []
    for line in session_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
            # Strip internal patch flag — not meaningful to callers
            entry.pop("_patch", None)
            entries.append(entry)
        except Exception:
            continue
    return entries


def _is_complete(entry: dict) -> bool:
    """True if the entry has an exit_code (i.e. the command finished)."""
    return entry.get("exit_code") is not None


def _dedup_by_seq(entries: list[dict]) -> list[dict]:
    """Keep only the last-written record per sequence number (complete wins over open)."""
    by_seq: dict[int, dict] = {}
    for e in entries:
        seq = e.get("seq")
        if seq is None:
            continue
        existing = by_seq.get(seq)
        if existing is None:
            by_seq[seq] = e
        elif _is_complete(e) and not _is_complete(existing):
            by_seq[seq] = e
    return sorted(by_seq.values(), key=lambda e: e.get("seq", 0))


def mas_pid_reader_logic(
    root_path: Path,
    *,
    last: int = 20,
    sid: Optional[str] = None,
    pid: Optional[int] = None,
    failed_only: bool = False,
    summary_only: bool = False,
    cwd_filter: Optional[str] = None,
) -> dict:
    """
    Read manifest/terminal_session.jsonl and manifest/terminal_pids.json.

    Returns structured machine-readable data: session metadata, command stats,
    and filtered entry list — suitable for documentation supplementation and
    CI gate consumption.
    """
    session_path = root_path / _MANIFEST_RELPATH
    pids_path = root_path / _PIDS_RELPATH

    pids = _load_pids(pids_path)
    raw_entries = _load_entries(session_path)
    all_entries = _dedup_by_seq(raw_entries)

    # Complete entries only (have exit_code)
    complete = [e for e in all_entries if _is_complete(e)]

    # Compute aggregate stats
    total = len(complete)
    failed_count = sum(1 for e in complete if not e.get("success", True))
    succeeded_count = total - failed_count
    durations = [e["duration_ms"] for e in complete if e.get("duration_ms") is not None]
    avg_duration_ms = int(sum(durations) / len(durations)) if durations else None
    max_duration_ms = max(durations) if durations else None

    # Session summary
    sessions_seen = list({e.get("sid") for e in complete if e.get("sid")})
    cwds_seen = list({e.get("cwd") for e in complete if e.get("cwd")})

    stats = {
        "total_complete_commands": total,
        "succeeded": succeeded_count,
        "failed": failed_count,
        "success_rate": round(succeeded_count / total, 4) if total else None,
        "avg_duration_ms": avg_duration_ms,
        "max_duration_ms": max_duration_ms,
        "sessions_seen": sessions_seen,
        "cwds_seen": cwds_seen,
        "manifest_path": str(session_path.relative_to(root_path)) if session_path.exists() else None,
        "manifest_exists": session_path.exists(),
        "pids_manifest_exists": pids_path.exists(),
    }

    # Active PID sessions with enriched metadata
    active_sessions = []
    for pid_str, info in pids.items():
        active_sessions.append({
            "pid": info.get("pid"),
            "session_id": info.get("session_id"),
            "cwd": info.get("cwd"),
            "start_ts": info.get("start_ts"),
            "term": info.get("term"),
        })

    if summary_only:
        return {
            "status": "ok",
            "stats": stats,
            "active_sessions": active_sessions,
        }

    # Filter chain
    filtered = complete

    if sid is not None:
        filtered = [e for e in filtered if e.get("sid") == sid]

    if pid is not None:
        filtered = [e for e in filtered if e.get("pid") == pid]

    if cwd_filter is not None:
        filtered = [e for e in filtered if cwd_filter.lower() in (e.get("cwd") or "").lower()]

    if failed_only:
        # Prefer exit_code semantics over success flag — success reflects PowerShell $?
        # which can be True even when $LASTEXITCODE != 0 (observed_quirk 2026-04-25)
        filtered = [e for e in filtered if e.get("exit_code", 0) != 0]

    # Last N (chronological)
    filtered = filtered[-last:] if last and len(filtered) > last else filtered

    # Enrich entries for documentation readability
    entries_out = []
    for e in filtered:
        entries_out.append({
            "seq": e.get("seq"),
            "ts": e.get("ts"),
            "pid": e.get("pid"),
            "session_id": e.get("sid"),
            "cwd": e.get("cwd"),
            "command": e.get("command", ""),
            "exit_code": e.get("exit_code"),
            "success": e.get("success"),
            "duration_ms": e.get("duration_ms"),
        })

    return {
        "status": "ok",
        "stats": stats,
        "active_sessions": active_sessions,
        "filters_applied": {
            "last": last,
            "sid": sid,
            "pid": pid,
            "failed_only": failed_only,
            "cwd_filter": cwd_filter,
        },
        "entries": entries_out,
        "entry_count": len(entries_out),
    }
