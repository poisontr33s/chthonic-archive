#!/usr/bin/env python3
# @SID: embed_gate_accept — HF gated model acceptance (3-tier CLI-first escalation ladder)
# Protocol: G7-REDUX — programmatic gate acceptance so gated embedding models can be used NOTE: BUN LATEST VERSION RESOLVES PLAYWRIGHT automation via —> 1.3.13 (!) — no separate playwright install needed
#           without manual HF Hub UI interaction. Metadta may be stale (e.g. gated status can change), so script checks live API status and escalates through multiple acceptance methods if needed.
#
# Escalation ladder (tried in order, stops at first success):
#
#   Tier 0  Registry guard  — gated: false → exit 0 immediately (no API calls)
#   Tier 1  HF REST API     — POST /api/models/{repo}/agree-terms (stdlib urllib, no deps)
#                             Works for gated="auto" (Gemma, Mistral, nomic, etc.)
#                             Returns HTTP 200 (accepted) or 400 (already accepted)
#   Tier 2  [none currently] — no CLI binary provides gate acceptance; agree-terms IS the CLI path
#   Tier 3  Bun.WebView      — bun run scripts/hf_gate_playwright.ts (headless Chromium)
#                             For gated="form" (Meta Llama, some Mistral) or Tier 1 403
#                             Only fires when --allow-playwright is passed
#                             Uses Bun.WebView (built-in v1.3.12+, no npm/playwright dep, Chrome via DevTools Protocol) 
#
# Note on the active model: Qwen/Qwen3-Embedding-0.6B has gated=false → Tier 0 fast-exit.
# This script becomes active when a gated model (e.g. google/embeddinggemma-300m,
# gated="auto") is set as active_model_id in embed_model_registry.json.
#
# Usage:
#   uv run scripts/embed_gate_accept.py                    # accept gate for active model
#   uv run scripts/embed_gate_accept.py --model-id some/model
#   uv run scripts/embed_gate_accept.py --check-only       # report gate status, do not accept
#   uv run scripts/embed_gate_accept.py --allow-playwright # enable Bun Playwright for form-gated
#
# Output: JSON to stdout (always), exit 0=accepted/already-open, 1=hard failure
#
#   {
#     "model_id": str,
#     "gated": false | "auto" | "form",
#     "status": "not_gated" | "already_accepted" | "accepted_now" | "pending_form" | "failed",
#     "method": "none" | "hf_api" | "bun_webview" | "bun_webview_unavailable" | "check_only",
#     "detail": str,
#     "pass": bool
#   }

import os
import sys
import json
import argparse
import time
from pathlib import Path

# Never trigger implicit model downloads
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE", "1")

REGISTRY_PATH = Path(__file__).parent / "embed_model_registry.json"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_registry() -> dict:
    with REGISTRY_PATH.open() as f:
        return json.load(f)


def get_hf_token() -> str | None:
    token = (
        os.environ.get("HUGGINGFACE_HUB_TOKEN")
        or os.environ.get("HF_TOKEN")
    )
    if not token:
        token_file = Path.home() / ".huggingface" / "token"
        if token_file.exists():
            token = token_file.read_text().strip() or None
    return token


def hf_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Gate status check (network)
# ---------------------------------------------------------------------------

def check_gate_status(model_id: str, token: str | None) -> dict:
    """
    Query HF Hub API for the model's gating status and whether the current
    user has already accepted.

    Returns:
        {
          "api_gated": false | "auto" | "manual",
          "user_accepted": bool | None,   # None = could not determine (no token)
          "detail": str
        }
    """
    import urllib.request
    import urllib.error

    url = f"https://huggingface.co/api/models/{model_id}"
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 401:
            # 401 = token missing or invalid; model may still exist
            return {
                "api_gated": "auto",          # conservative assumption
                "user_accepted": False,
                "detail": "401 from model API — authentication required (token missing or invalid)"
            }
        if e.code == 403:
            # 403 = gated and not accepted by this user
            return {
                "api_gated": "auto",          # conservative assumption
                "user_accepted": False,
                "detail": "403 from model API — gated and not yet accepted"
            }
        if e.code == 404:
            # 404 = model path does not exist on HF at all; no gating to accept
            return {
                "api_gated": "not_found",
                "user_accepted": None,
                "detail": (
                    f"404 from model API — '{model_id}' does not exist on HuggingFace. "
                    "The org may have been renamed, the model may have been deleted, "
                    "or it was never published. There is no gate to accept."
                )
            }
        return {
            "api_gated": None,
            "user_accepted": None,
            "detail": f"HTTP {e.code} from model API: {e.reason}"
        }
    except Exception as e:
        return {
            "api_gated": None,
            "user_accepted": None,
            "detail": f"Network error: {e}"
        }

    api_gated = data.get("gated", False)
    # HF returns gated=true (bool) for some repos, "auto"/"manual" for others
    if api_gated is True:
        api_gated = "auto"  # normalise

    user_accepted = None
    if token and api_gated:
        # When user has accepted, the API response contains siblings/cardData
        # without 401/403, so a 200 means accepted.
        user_accepted = True
    elif not token and api_gated:
        user_accepted = None  # unknown without token

    return {
        "api_gated": api_gated,
        "user_accepted": user_accepted,
        "detail": "200 OK from model API"
    }


# ---------------------------------------------------------------------------
# Auto-gate acceptance (HF agree-terms API)
# ---------------------------------------------------------------------------

def accept_auto_gate(model_id: str, token: str) -> dict:
    """
    POST /api/models/{model_id}/agree-terms — works for gated=auto models.
    Returns {"success": bool, "detail": str, "http_status": int}.
    """
    import urllib.request
    import urllib.error

    url = f"https://huggingface.co/api/models/{model_id}/agree-terms"
    data = json.dumps({}).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            status = resp.status
            body = resp.read().decode(errors="replace")
            return {"success": True, "detail": f"Accepted (HTTP {status})", "http_status": status}
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace") if hasattr(e, "read") else ""
        if e.code == 400:
            # Already accepted
            return {"success": True, "detail": "Already accepted (HTTP 400 = duplicate agree)", "http_status": 400}
        if e.code == 403:
            return {
                "success": False,
                "detail": (
                    f"HTTP 403 — model requires manual form acceptance. "
                    f"Visit: https://huggingface.co/{model_id} and click 'Agree and access repository'. "
                    f"Response: {body[:300]}"
                ),
                "http_status": 403,
            }
        if e.code == 404:
            # agree-terms endpoint absent — this model does not use HF's agree-terms API gate.
            # Verify accessibility via model info endpoint: if reachable and not gated, treat as open.
            live = check_gate_status(model_id, token)
            if live["api_gated"] is False:
                return {
                    "success": True,
                    "detail": "agree-terms endpoint absent (HTTP 404) — model not gated via agree-terms API; openly accessible",
                    "http_status": 404,
                }
            if live["user_accepted"] is True:
                return {
                    "success": True,
                    "detail": "agree-terms endpoint absent (HTTP 404) — model accessible via organisation-controlled gate (already granted)",
                    "http_status": 404,
                }
            return {
                "success": False,
                "detail": (
                    f"agree-terms endpoint absent (HTTP 404) — model uses organisation-controlled access gate. "
                    f"Visit https://huggingface.co/{model_id} to request access, "
                    f"or re-run with --allow-playwright to attempt form automation."
                ),
                "http_status": 404,
            }
        return {"success": False, "detail": f"HTTP {e.code}: {body[:300]}", "http_status": e.code}
    except Exception as e:
        return {"success": False, "detail": f"Network error: {e}", "http_status": None}


# ---------------------------------------------------------------------------
# Tier 3 — Bun Playwright form-gate acceptance
# ---------------------------------------------------------------------------

def accept_form_gate_bun(model_id: str, token: str | None) -> dict:
    """
    Tier 3: Bun.WebView native browser automation for form-gated models.

    Invokes scripts/hf_gate_playwright.ts via `bun run` — uses Bun.WebView
    (built into Bun v1.3.12+, no npm deps, Chrome backend, isTrusted events).
    Falls back gracefully if bun is not on PATH.

    Returns {"success": bool, "detail": str, "method": str}.
    """
    import subprocess

    scripts_dir = Path(__file__).parent
    script_path = scripts_dir / "hf_gate_playwright.ts"

    if not script_path.exists():
        return {
            "success": False,
            "detail": f"hf_gate_playwright.ts not found at {script_path}",
            "method": "bun_webview_unavailable",
        }

    cmd = ["bun", "run", str(script_path), "--model-id", model_id]
    if token:
        cmd += ["--token", token]

    env = os.environ.copy()
    if token:
        env["HF_TOKEN"] = token
        env["HUGGINGFACE_HUB_TOKEN"] = token

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=90,
            env=env,
        )
        raw = result.stdout.strip()
        try:
            out = json.loads(raw)
        except json.JSONDecodeError:
            err_detail = (raw or result.stderr or "no output")[:400]
            return {
                "success": False,
                "detail": f"Bun.WebView returned non-JSON output: {err_detail}",
                "method": "bun_webview",
            }
        return {
            "success": bool(out.get("pass", False)),
            "detail": out.get("detail", ""),
            "method": out.get("method", "bun_webview"),
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "detail": "Bun.WebView subprocess timed out after 90s",
            "method": "bun_webview",
        }
    except FileNotFoundError:
        return {
            "success": False,
            "detail": "bun not found on PATH — install Bun (https://bun.sh) to enable Tier 3 browser automation",
            "method": "bun_webview_unavailable",
        }
    except Exception as e:
        return {
            "success": False,
            "detail": f"Bun.WebView subprocess error: {e}",
            "method": "bun_webview",
        }


# ---------------------------------------------------------------------------
# Core acceptance logic — shared by single-model and batch modes
# ---------------------------------------------------------------------------

def _do_accept(
    model_id: str,
    registry_gated,
    token: str | None,
    allow_playwright: bool,
) -> tuple[dict, int]:
    """
    Accept gate for a single model. Returns (result_dict, exit_code).

    Called by both single-model path and --accept-all batch mode so the
    escalation ladder lives in exactly one place.
    """
    if registry_gated is False:
        return (
            {
                "model_id": model_id, "gated": False, "status": "not_gated",
                "method": "none",
                "detail": "Model is not gated per registry — no acceptance needed",
                "pass": True,
            },
            0,
        )

    if not token:
        return (
            {
                "model_id": model_id, "gated": registry_gated, "status": "failed",
                "method": "none",
                "detail": "HF token required for gated model acceptance. Set HF_TOKEN or run: . .\\scripts\\api_pool.ps1 -Quiet",
                "pass": False,
            },
            1,
        )

    # Live check — registry gated field is a hint, not the source of truth.
    # The HF REST API response IS the authoritative gate state.
    gate_status = check_gate_status(model_id, token)

    # 404: model does not exist on HF — this is a stale registry entry, not a gate failure.
    # There is no gate to accept on a non-existent model. Pass: True, auto-tombstone signal.
    if gate_status["api_gated"] == "not_found":
        return (
            {
                "model_id": model_id, "gated": registry_gated, "status": "not_found_open",
                "method": "none",
                "detail": gate_status["detail"] + " Registry entry is stale — will auto-tombstone.",
                "pass": True,
                "registry_stale": True,
            },
            0,
        )

    if gate_status["user_accepted"] is True:
        return (
            {
                "model_id": model_id, "gated": registry_gated, "status": "already_accepted",
                "method": "hf_api_check",
                "detail": "Gate already accepted — model is accessible",
                "pass": True,
            },
            0,
        )

    if registry_gated == "auto" or (gate_status["api_gated"] not in ("manual", None)):
        result = accept_auto_gate(model_id, token)
        if result["success"]:
            return (
                {
                    "model_id": model_id, "gated": registry_gated, "status": "accepted_now",
                    "method": "hf_api", "detail": result["detail"], "pass": True,
                },
                0,
            )

        if result.get("http_status") == 403:
            if allow_playwright:
                pw_result = accept_form_gate_bun(model_id, token)
                status = "accepted_now" if pw_result["success"] else "failed"
                return (
                    {
                        "model_id": model_id, "gated": registry_gated, "status": status,
                        "method": pw_result.get("method", "bun_webview"),
                        "detail": pw_result["detail"], "pass": pw_result["success"],
                    },
                    0 if pw_result["success"] else 1,
                )
            else:
                return (
                    {
                        "model_id": model_id, "gated": registry_gated, "status": "pending_form",
                        "method": "none",
                        "detail": (
                            f"Model requires manual form acceptance on HF Hub. "
                            f"Re-run with --allow-playwright to automate via Bun.WebView "
                            f"(Bun v1.3.12+ native, no npm), or visit: "
                            f"https://huggingface.co/{model_id}"
                        ),
                        "pass": False,
                    },
                    1,
                )

        return (
            {
                "model_id": model_id, "gated": registry_gated, "status": "failed",
                "method": "hf_api", "detail": result["detail"], "pass": False,
            },
            1,
        )

    if registry_gated == "form" or gate_status["api_gated"] == "manual":
        if allow_playwright:
            pw_result = accept_form_gate_bun(model_id, token)
            status = "accepted_now" if pw_result["success"] else "failed"
            return (
                {
                    "model_id": model_id, "gated": registry_gated, "status": status,
                    "method": pw_result.get("method", "bun_webview"),
                    "detail": pw_result["detail"], "pass": pw_result["success"],
                },
                0 if pw_result["success"] else 1,
            )
        else:
            return (
                {
                    "model_id": model_id, "gated": registry_gated, "status": "pending_form",
                    "method": "none",
                    "detail": (
                        f"Model {model_id!r} requires manual form gate. "
                        f"Re-run with --allow-playwright to automate via Bun.WebView "
                        f"(Bun v1.3.12+ native, no npm), or visit: "
                        f"https://huggingface.co/{model_id} and click 'Agree and access repository'."
                    ),
                    "pass": False,
                },
                1,
            )

    return (
        {
            "model_id": model_id, "gated": registry_gated, "status": "failed",
            "method": "none",
            "detail": f"Unknown gate state: registry_gated={registry_gated!r}, api_gated={gate_status['api_gated']!r}",
            "pass": False,
        },
        1,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Accept HF gated model terms — programmatic API or Playwright fallback"
    )
    parser.add_argument(
        "--model-id",
        default=None,
        dest="model_id",
        help="HF model ID to accept gate for (default: active_model_id from registry)"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        dest="check_only",
        help="Report gate status without accepting"
    )
    parser.add_argument(
        "--accept-all",
        action="store_true",
        dest="accept_all",
        help=(
            "Accept gates for ALL gated models in registry (batch mode). "
            "Writes manifest/embed_gate_accept_batch.json. "
            "Exit 0 if all accepted/already-open, 1 if any hard failure."
        ),
    )
    parser.add_argument(
        "--list-gated",
        action="store_true",
        dest="list_gated",
        help="List all gated models from registry with gating type. No API calls.",
    )
    parser.add_argument(
        "--allow-playwright",
        action="store_true",
        dest="allow_playwright",
        help="Allow Bun.WebView browser automation for form-gated models (built into Bun v1.3.12+, no npm deps)"
    )
    args = parser.parse_args()

    # --- Load registry ---
    try:
        registry = load_registry()
    except Exception as e:
        out = {"pass": False, "status": "failed", "detail": f"Registry load failed: {e}"}
        print(json.dumps(out, indent=2))
        sys.exit(1)

    models_map = registry.get("models", {})

    # ------------------------------------------------------------------
    # --list-gated: show all gated models, no API calls
    # ------------------------------------------------------------------
    if args.list_gated:
        gated_models = {
            mid: {
                "gated": info.get("gated"),
                "dims": info.get("dims"),
                "license": info.get("license", "unknown"),
                "notes": (info.get("notes", "")[:100] + "...") if len(info.get("notes", "")) > 100 else info.get("notes", ""),
            }
            for mid, info in models_map.items()
            if info.get("gated") is not False
        }
        out = {"total_gated": len(gated_models), "models": gated_models}
        print(json.dumps(out, indent=2))
        sys.exit(0)

    # ------------------------------------------------------------------
    # --accept-all: batch acceptance sweep over all gated models
    # ------------------------------------------------------------------
    if args.accept_all:
        import time as _time
        token = get_hf_token()
        results = []
        any_failure = False

        for mid, minfo in models_map.items():
            gated = minfo.get("gated", False)
            result, _ = _do_accept(mid, gated, token, args.allow_playwright)
            results.append(result)
            # 404 (not_found_open) is pass:True — not a failure even if registry said gated
            if not result["pass"] and gated is not False:
                any_failure = True

        # Auto-tombstone stale entries (live HF returned 404 for models the registry listed as gated).
        # Self-healing: next run will skip them at Tier 0 (gated: false fast-path).
        ts_now = _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime())
        stale = [r for r in results if r.get("registry_stale")]
        if stale:
            updated_reg = load_registry()
            for r in stale:
                mid = r["model_id"]
                if mid in updated_reg.get("models", {}):
                    updated_reg["models"][mid]["gated"] = False
                    updated_reg["models"][mid]["_gated_tombstone"] = (
                        f"AUTO-TOMBSTONE {ts_now}: live HF API returned 404. "
                        "Registry entry was stale. Model does not exist at this path on HuggingFace."
                    )
            REGISTRY_PATH.write_text(json.dumps(updated_reg, indent=2))

        batch_out = {
            "ts": ts_now,
            "total": len(results),
            "gated_count": sum(
                1 for r in results
                if r.get("gated") is not False and r.get("status") != "not_found_open"
            ),
            "accepted": sum(
                1 for r in results
                if r["pass"] and r.get("gated") is not False
                and r.get("status") not in ("not_found_open", "not_gated")
            ),
            "already_accepted": sum(1 for r in results if r.get("status") == "already_accepted"),
            "skipped_not_gated": sum(1 for r in results if r.get("gated") is False),
            "auto_tombstoned": len(stale),
            "failed": sum(
                1 for r in results
                if not r["pass"] and r.get("gated") is not False
                and r.get("status") != "not_found_open"
            ),
            "results": results,
        }

        manifest_path = Path(__file__).parent.parent / "manifest" / "embed_gate_accept_batch.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(batch_out, indent=2))

        print(json.dumps(batch_out, indent=2))
        sys.exit(1 if any_failure else 0)

    # ------------------------------------------------------------------
    # Single-model path (default)
    # ------------------------------------------------------------------
    model_id = args.model_id or registry.get("active_model_id")
    if not model_id:
        out = {"pass": False, "status": "failed", "detail": "No model_id specified and no active_model_id in registry"}
        print(json.dumps(out, indent=2))
        sys.exit(1)

    model_info = models_map.get(model_id, {})
    registry_gated = model_info.get("gated", False)

    # --check-only: status report without acceptance attempt
    if args.check_only:
        token = get_hf_token()
        if registry_gated is False:
            out = {
                "model_id": model_id, "gated": False, "status": "not_gated",
                "method": "check_only",
                "detail": "Model is not gated per registry — no acceptance needed",
                "pass": True,
            }
        elif not token:
            out = {
                "model_id": model_id, "gated": registry_gated, "status": "check_failed",
                "method": "check_only",
                "detail": "HF token required to check gate status. Set HF_TOKEN.",
                "pass": False,
            }
        else:
            gate_status = check_gate_status(model_id, token)
            out = {
                "model_id": model_id,
                "gated": registry_gated,
                "api_gated": gate_status["api_gated"],
                "user_accepted": gate_status["user_accepted"],
                "status": "already_accepted" if gate_status["user_accepted"] else "pending",
                "method": "check_only",
                "detail": gate_status["detail"],
                "pass": bool(gate_status["user_accepted"]),
            }
        print(json.dumps(out, indent=2))
        sys.exit(0 if out["pass"] else 1)

    token = get_hf_token()
    out, code = _do_accept(model_id, registry_gated, token, args.allow_playwright)
    print(json.dumps(out, indent=2))
    sys.exit(code)


if __name__ == "__main__":
    main()
