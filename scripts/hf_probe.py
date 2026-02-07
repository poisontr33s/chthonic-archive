#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hugging Face auth probe (no secrets).

Purpose:
- Verify whether the current environment can authenticate to Hugging Face.
- Print only non-secret identifiers.

Invocation:
- uv run scripts/hf_probe.py
"""

from __future__ import annotations

from huggingface_hub import HfApi


def main() -> int:
    api = HfApi()
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

