#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: lens_runner.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: GOLD
# ║ Temple-Ayllu Zone: 🧭 THE COMPASS
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Shared helper — subprocess E2E contract for sub-lens subprocesses)
# ╚════════════════════════════════════════════════════════════════════════════

"""
scripts/lens_runner.py — Subprocess E2E contract for sub-lens methods.

The methodology rule (durable memory: feedback_subprocess_e2e_logging_contract):
sub-lenses that subprocess external methods can be consumed by a next-rung
lens ONLY if their subprocess output is captured as structured logging
that conforms to the lens envelope. This module functionalizes the contract
that already works in route_index.py's apply_route() so future sub-lenses
inherit it by import — not by re-copy-paste.

Envelope shape (every entry, no exceptions):
    method        str   — method-class name (e.g. "uv-lock-upgrade")
    command       str   — exact invocation (joined for display); None if propose-only
    executed      bool  — did the subprocess actually run?
    dry_run       bool  — was this a propose-only invocation?
    exit_code     int   — subprocess return code; None if not executed
    stdout_tail   str   — last 2000 chars of stdout; None if empty/not executed
    stderr_tail   str   — last 2000 chars of stderr; None if empty/not executed
    <extra_fields>      — per-method semantic fields (packages, files, etc.)

The 2000-char tail bound matters: the whole point of the lens stack is that
each rung's output is small enough for the next rung to read every entry.
Unbounded raw bytes defeat that.

@SID:           LENS_RUNNER_V1
@Shabti:        Shared helper
@Purpose:       Enforce the subprocess E2E logging contract for sub-lenses.
"""

from __future__ import annotations

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


# @SID: LENS_RUNNER_V1

import subprocess
import sys
from pathlib import Path


TAIL_BYTES = 2000  # contract: last-N bytes captured per stream; do not unbound


def result_envelope(method: str, extra_fields: dict | None = None) -> dict:
    """Build a fresh result envelope in lens-subprocess contract shape.

    Use for propose-only paths where no subprocess fires but the caller
    still needs a shape-conforming entry to put in the manifest.
    """
    envelope = {
        "method": method,
        "command": None,
        "executed": False,
        "dry_run": True,
        "exit_code": None,
        "stdout_tail": None,
        "stderr_tail": None,
    }
    if extra_fields:
        envelope.update(extra_fields)
    return envelope


def run_method_capture(
    method: str,
    command: list[str],
    cwd: Path | str,
    *,
    dry_run: bool = True,
    log_prefix: str | None = None,
    extra_fields: dict | None = None,
) -> dict:
    """Run a method as a subprocess; return its result in lens-envelope shape.

    Args:
        method: method-class name (canonical, from method_index).
        command: full argv as a list (e.g. ["uv", "lock", "--upgrade-package", "x"]).
        cwd: working directory; usually REPO_ROOT.
        dry_run: if True, log the intended command but do not execute.
        log_prefix: tag for stdout lines (defaults to method name).
        extra_fields: per-method semantic fields merged into the result.

    Returns:
        dict matching the envelope. Always shape-conforming, whether the
        subprocess ran, was skipped (dry_run), or failed (exit_code != 0).

    On non-zero exit, prints last 500 chars of stderr to sys.stderr; the
    full stderr_tail (last 2000) is in the returned dict for the manifest.
    """
    prefix = log_prefix or method
    result = result_envelope(method, extra_fields)
    result["dry_run"] = dry_run
    result["command"] = " ".join(command)

    if dry_run:
        print(f"[{prefix}] dry-run: {result['command']}")
        return result

    print(f"[{prefix}] applying: {result['command']}")
    proc = subprocess.run(
        command, cwd=str(cwd),
        capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    result["executed"] = True
    result["exit_code"] = proc.returncode
    result["stdout_tail"] = proc.stdout[-TAIL_BYTES:] if proc.stdout else None
    result["stderr_tail"] = proc.stderr[-TAIL_BYTES:] if proc.stderr else None
    if proc.returncode != 0:
        print(f"[{prefix}] FAILED: {proc.stderr[:500]}", file=sys.stderr)
    return result
