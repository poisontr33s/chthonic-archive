#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: hf_probe.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Hugging Face auth probe (no secrets).

Purpose:
- Verify whether the current environment can authenticate to Hugging Face.
- Print only non-secret identifiers.

Invocation:
- uv run scripts/hf_probe.py

@SID:           TOOL_HF_PROBE_V1
@Shabti:        CLI Script
@Purpose:       Hugging Face auth probe (no secrets).
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


from __future__ import annotations

import os

try:
    from huggingface_hub import HfApi
except ImportError:
    raise SystemExit(
        "huggingface_hub not installed — run: uv add huggingface_hub"
    )


def main() -> int:
    # Build a process-local env copy so we don't mutate os.environ.
    env = dict(os.environ)

    # hf_hub auth precedence:
    # - HF_TOKEN overrides other auth sources and can be stale.
    # - Prefer HUGGINGFACE_HUB_TOKEN when present (API pool), and ignore HF_TOKEN for this probe.
    if env.get("HUGGINGFACE_HUB_TOKEN") and env.get("HF_TOKEN"):
        env.pop("HF_TOKEN", None)

    token = env.get("HF_TOKEN") or env.get("HUGGINGFACE_HUB_TOKEN") or None
    api = HfApi(token=token)
    try:
        who = api.whoami()
        ident = who.get("name") or who.get("email") or "unknown"
        print(f"ok: {ident}")
        return 0
    except Exception as e:
        print(f"fail: {type(e).__name__}: {e}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
