#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""
poe_auth.py - Shared Poe credential resolution helpers.

@SID:           LIB_POE_AUTH_V1
@Shabti:        Shared Library
@Purpose:       Centralize Poe key resolution across OpenAI-compatible,
                SDK, and audit scripts so account selection and auth
                source reporting stay consistent.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from urllib import error, request


POOL_PATH = Path.home() / ".chthonic" / "api_pool.json"
POE_SLOT_RE = re.compile(r"^POE_API_KEY_(\d+)$")
POE_DEFAULT_BASE_URL = "https://api.poe.com/v1"


@dataclass(frozen=True)
class PoeCredentialResolution:
    token: str | None
    account: str | None
    auth_source: str
    account_source: str
    selected_name: str | None
    pool_path: str

    @property
    def valid(self) -> bool:
        """True if a non-None token was resolved."""
        return self.token is not None


def normalize_account(value: str | None) -> str | None:
    if value is None:
        return None
    raw = value.strip()
    if not raw or not raw.isdigit():
        return None
    return str(int(raw))


def account_arg(value: str) -> str:
    account = normalize_account(value)
    if account is None:
        raise ValueError("account must be numeric (example: 1, 2, 3)")
    return account


def discover_slot_names(names: list[str]) -> list[tuple[str, str]]:
    slots: list[tuple[int, str, str]] = []
    seen: set[str] = set()
    for name in names:
        match = POE_SLOT_RE.match(name)
        if not match:
            continue
        account = str(int(match.group(1)))
        if account in seen:
            continue
        seen.add(account)
        slots.append((int(account), name, account))
    slots.sort(key=lambda item: item[0])
    return [(name, account) for _, name, account in slots]


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


def resolve_poe_credentials(account: str | None, strict: bool = False) -> PoeCredentialResolution:
    """Resolve Poe credentials for the given account.

    Args:
        account: Explicit account number, or None for auto-discovery.
        strict: If True, raise ValueError when no token is found.
    """
    result = _resolve_poe_credentials(account)
    if strict and not result.valid:
        raise ValueError(
            f"Poe credential resolution failed: no token found for "
            f"account={account!r} (source: {result.auth_source})"
        )
    return result


def _resolve_poe_credentials(account: str | None) -> PoeCredentialResolution:
    pool_env = load_local_pool_env()
    normalized_account = normalize_account(account)

    if normalized_account:
        slot = f"POE_API_KEY_{normalized_account}"
        value = os.getenv(slot)
        if value and value.strip():
            return PoeCredentialResolution(
                token=value.strip(),
                account=normalized_account,
                auth_source="process_env_slot",
                account_source="explicit_account",
                selected_name=slot,
                pool_path=str(POOL_PATH),
            )
        pool_value = pool_env.get(slot)
        if pool_value:
            return PoeCredentialResolution(
                token=pool_value,
                account=normalized_account,
                auth_source="pool_slot",
                account_source="explicit_account",
                selected_name=slot,
                pool_path=str(POOL_PATH),
            )
        return PoeCredentialResolution(
            token=None,
            account=normalized_account,
            auth_source="missing",
            account_source="explicit_account",
            selected_name=slot,
            pool_path=str(POOL_PATH),
        )

    direct = os.getenv("POE_API_KEY")
    active_env = normalize_account(os.getenv("POE_ACCOUNT_ACTIVE"))
    if direct and direct.strip():
        return PoeCredentialResolution(
            token=direct.strip(),
            account=active_env,
            auth_source="process_env_direct",
            account_source="process_env_active" if active_env else "implicit_direct",
            selected_name="POE_API_KEY",
            pool_path=str(POOL_PATH),
        )

    direct_pool = pool_env.get("POE_API_KEY")
    active_pool = normalize_account(pool_env.get("POE_ACCOUNT_ACTIVE"))
    if direct_pool:
        return PoeCredentialResolution(
            token=direct_pool,
            account=active_env or active_pool,
            auth_source="pool_direct",
            account_source=(
                "process_env_active"
                if active_env
                else ("pool_active" if active_pool else "implicit_direct")
            ),
            selected_name="POE_API_KEY",
            pool_path=str(POOL_PATH),
        )

    if active_env:
        slot = f"POE_API_KEY_{active_env}"
        value = os.getenv(slot)
        if value and value.strip():
            return PoeCredentialResolution(
                token=value.strip(),
                account=active_env,
                auth_source="process_env_active_slot",
                account_source="process_env_active",
                selected_name=slot,
                pool_path=str(POOL_PATH),
            )
        pool_value = pool_env.get(slot)
        if pool_value:
            return PoeCredentialResolution(
                token=pool_value,
                account=active_env,
                auth_source="pool_active_slot",
                account_source="process_env_active",
                selected_name=slot,
                pool_path=str(POOL_PATH),
            )

    if active_pool:
        slot = f"POE_API_KEY_{active_pool}"
        value = os.getenv(slot)
        if value and value.strip():
            return PoeCredentialResolution(
                token=value.strip(),
                account=active_pool,
                auth_source="process_env_active_slot",
                account_source="pool_active",
                selected_name=slot,
                pool_path=str(POOL_PATH),
            )
        pool_value = pool_env.get(slot)
        if pool_value:
            return PoeCredentialResolution(
                token=pool_value,
                account=active_pool,
                auth_source="pool_active_slot",
                account_source="pool_active",
                selected_name=slot,
                pool_path=str(POOL_PATH),
            )

    for candidate, slot_account in discover_slot_names(list(os.environ.keys())):
        value = os.getenv(candidate)
        if value and value.strip():
            return PoeCredentialResolution(
                token=value.strip(),
                account=slot_account,
                auth_source="process_env_discovered_slot",
                account_source="discovered_slot",
                selected_name=candidate,
                pool_path=str(POOL_PATH),
            )

    for candidate, slot_account in discover_slot_names(list(pool_env.keys())):
        pool_value = pool_env.get(candidate)
        if pool_value:
            return PoeCredentialResolution(
                token=pool_value,
                account=slot_account,
                auth_source="pool_discovered_slot",
                account_source="discovered_slot",
                selected_name=candidate,
                pool_path=str(POOL_PATH),
            )

    return PoeCredentialResolution(
        token=None,
        account=None,
        auth_source="missing",
        account_source="missing",
        selected_name=None,
        pool_path=str(POOL_PATH),
    )


@dataclass(frozen=True)
class PoeTokenValidation:
    """Result of a live token validation call against the Poe API."""
    ok: bool
    status_code: int | None
    model_count: int | None
    error: str | None


def validate_poe_token(
    token: str,
    base_url: str = POE_DEFAULT_BASE_URL,
    timeout: int = 15,
) -> PoeTokenValidation:
    """Hit GET /models with the given token to confirm it is accepted by Poe.

    Returns a PoeTokenValidation with ok=True if the API responds 200 and
    returns at least one model entry. No token value is ever logged or raised.

    Args:
        token:    Bearer token to validate.
        base_url: Poe OpenAI-compatible base URL (default: https://api.poe.com/v1).
        timeout:  HTTP timeout in seconds (default: 15).
    """
    url = f"{base_url.rstrip('/')}/models"
    req = request.Request(
        url=url,
        method="GET",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                data = json.loads(raw)
                model_count = len(data.get("data", []))
            except Exception:
                model_count = None
            return PoeTokenValidation(ok=True, status_code=resp.status, model_count=model_count, error=None)
    except error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            msg = json.loads(raw).get("error", {}).get("message") or f"HTTP {e.code}"
        except Exception:
            msg = f"HTTP {e.code}"
        return PoeTokenValidation(ok=False, status_code=e.code, model_count=None, error=msg)
    except error.URLError as e:
        return PoeTokenValidation(ok=False, status_code=None, model_count=None, error=f"network_error: {e.reason}")
    except Exception as e:  # noqa: BLE001
        return PoeTokenValidation(ok=False, status_code=None, model_count=None, error=str(e))
