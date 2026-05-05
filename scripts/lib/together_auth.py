#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
together_auth.py - Shared Together AI credential resolution helper.

@SID:           LIB_TOGETHER_AUTH_V1
@Shabti:        Shared Library
@Purpose:       Centralize Together AI key resolution across lane scripts
                so auth source reporting stays consistent. Resolves
                TOGETHER_API_KEY from process environment first, then the
                local ~/.chthonic/api_pool.json fallback. Never prints
                token values.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


POOL_PATH = Path.home() / ".chthonic" / "api_pool.json"
TOGETHER_DEFAULT_BASE_URL = "https://api.together.xyz/v1"


@dataclass(frozen=True)
class TogetherCredentialResolution:
    token: str | None
    auth_source: str
    pool_path: str

    @property
    def valid(self) -> bool:
        """True if a non-None token was resolved."""
        return self.token is not None


def load_local_pool_env() -> dict[str, str]:
    if not POOL_PATH.exists():
        return {}
    try:
        obj = json.loads(POOL_PATH.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}
    env = obj.get("env")
    if not isinstance(env, dict):
        return {}
    out: dict[str, str] = {}
    for key, value in env.items():
        if isinstance(key, str) and isinstance(value, str) and value.strip():
            out[key] = value.strip()
    return out


def resolve_together_credentials() -> TogetherCredentialResolution:
    """Resolve Together AI credentials.

    Resolution order:
      1. TOGETHER_API_KEY environment variable
      2. ~/.chthonic/api_pool.json env.TOGETHER_API_KEY
    """
    direct = os.getenv("TOGETHER_API_KEY")
    if direct and direct.strip():
        return TogetherCredentialResolution(
            token=direct.strip(),
            auth_source="process_env",
            pool_path=str(POOL_PATH),
        )

    pool_env = load_local_pool_env()
    pool_value = pool_env.get("TOGETHER_API_KEY")
    if pool_value:
        return TogetherCredentialResolution(
            token=pool_value,
            auth_source="pool_file",
            pool_path=str(POOL_PATH),
        )

    return TogetherCredentialResolution(
        token=None,
        auth_source="missing",
        pool_path=str(POOL_PATH),
    )
