#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: mistralrs_client.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
mistralrs_client.py — Universal thin client for mistral.rs OpenAI-compatible API.

@SID:           LIB_MISTRALRS_CLIENT_V1
@Purpose:       Drop-in replacement for llama-cpp-python in overnight pipeline.
                All inference goes through the Rust server. No ML imports.
@Shabti:        CLI Script

Usage:
    from scripts.mistralrs_client import MistralRsClient

    client = MistralRsClient()
    result = client.chat(
        messages=[{"role": "user", "content": "Hello"}],
        json_schema={"type": "object", "properties": {...}},
    )
"""

from __future__ import annotations


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import json
import sys
import urllib.error
import urllib.request
from typing import Any


class MistralRsClient:
    """Thin HTTP client for mistral.rs /v1/chat/completions.

    Replaces llama-cpp-python's Llama class for all inference needs.
    No ML dependencies. Just stdlib urllib.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        model: str | None = None,
        timeout: int = 120,
    ):
        self.base_url = base_url.rstrip("/")
        self._model = model
        self.timeout = timeout

    @property
    def model(self) -> str:
        """Auto-detect loaded model from server if not specified."""
        if self._model:
            return self._model
        try:
            data = self._get("/v1/models")
            for m in data.get("data", []):
                if m.get("status") == "loaded":
                    self._model = m["id"]
                    return self._model
            # Fallback to first model or "default"
            if data.get("data"):
                self._model = data["data"][0]["id"]
                return self._model
        except Exception:
            pass
        return "default"

    def is_alive(self) -> bool:
        """Check if the server is responding."""
        try:
            self._get("/v1/models")
            return True
        except Exception:
            return False

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        max_tokens: int = 800,
        temperature: float = 0.1,
        json_schema: dict | None = None,
        schema_name: str = "response",
    ) -> dict[str, Any]:
        """Send a chat completion request.

        Returns the full API response dict (same shape as OpenAI).
        If json_schema is provided, uses response_format constraint.

        This is a drop-in replacement for:
            llm.create_chat_completion(messages=..., response_format=...)
        """
        body: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if json_schema is not None:
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "schema": json_schema,
                },
            }

        return self._post("/v1/chat/completions", body)

    def chat_content(
        self,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> str:
        """Convenience: returns just the content string."""
        result = self.chat(messages, **kwargs)
        return result["choices"][0]["message"]["content"]

    def chat_json(
        self,
        messages: list[dict[str, str]],
        json_schema: dict,
        **kwargs: Any,
    ) -> dict:
        """Convenience: returns parsed JSON from schema-constrained output."""
        content = self.chat_content(messages, json_schema=json_schema, **kwargs)
        return json.loads(content)

    def usage_stats(self, result: dict) -> dict:
        """Extract usage stats from a response."""
        usage = result.get("usage", {})
        return {
            "total_tokens": usage.get("total_tokens", 0),
            "tok_per_sec": usage.get("avg_tok_per_sec", 0),
            "prompt_tok_per_sec": usage.get("avg_prompt_tok_per_sec", 0),
            "completion_tok_per_sec": usage.get("avg_compl_tok_per_sec", 0),
            "total_time_sec": usage.get("total_time_sec", 0),
        }

    # ── HTTP primitives (stdlib only, no requests/httpx) ─────────────

    def _get(self, path: str) -> dict:
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read())

    def _post(self, path: str, body: dict) -> dict:
        url = f"{self.base_url}{path}"
        data = json.dumps(body).encode()
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read())


# ── CLI smoke test ───────────────────────────────────────────────────

if __name__ == "__main__":
    client = MistralRsClient()

    if not client.is_alive():
        print("ERROR: mistral.rs server not running on localhost:8080", file=sys.stderr)
        print("Start it: python scripts/mistralrs_model_manager.py start <model_id>", file=sys.stderr)
        sys.exit(1)

    print(f"Server: ONLINE | Model: {client.model}")

    # Test schema-constrained output
    schema = {
        "type": "object",
        "properties": {
            "verdict": {"type": "string", "enum": ["PROMOTE", "FLAG", "SKIP"]},
            "reason": {"type": "string"},
            "confidence": {"type": "number"},
        },
        "required": ["verdict", "reason", "confidence"],
    }

    result = client.chat(
        messages=[
            {"role": "system", "content": "You are a code archaeologist. Classify files."},
            {"role": "user", "content": "Classify: scripts/test.py (10 lines, 2 days old, utility)"},
        ],
        json_schema=schema,
    )

    content = result["choices"][0]["message"]["content"]
    stats = client.usage_stats(result)

    print(f"Response: {content}")
    print(f"Stats: {stats['total_tokens']} tokens, {stats['tok_per_sec']:.1f} tok/s")
