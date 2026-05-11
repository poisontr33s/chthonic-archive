#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @SID: embed_doctor — pre-flight validation for session-corpus --embed
# Protocol: reads embed_model_registry.json, validates HF token + model cache,
#           checks schema compatibility, checks gated status (G7-REDUX);
#           exits 0 on pass, 1 on hard fail.
# Output:   JSON to stdout — always. Caller (session-corpus.ts) parses this.
# Usage:    uv run scripts/embed_doctor.py [--current-schema-version N]
#           uv run scripts/embed_doctor.py --accept-gated  # auto-accept gate then re-check
#           uv run scripts/embed_doctor.py --accept-gated --allow-playwright  # + Playwright fallback
#           uv run scripts/embed_doctor.py --allow-download  # if model not cached, fetch it (temporarily unsets OFFLINE)
#
# Output schema:
#   {
#     "pass": bool,                              # true only if ALL hard gates clear
#     "model_id": str,
#     "dims": int,
#     "context_tokens": int,
#     "license": str,
#     "gated": false | "auto" | "form",         # from registry
#     "gated_status": "not_gated" | "accepted" | "pending" | "unknown",
#     "cached": bool,                            # model weights present in HF_HOME cache
#     "hf_token_format_valid": bool | null,      # null=no token found; True=hf_ prefix only — NOT network-verified
#     "hf_token_network_verified": bool,         # always False (doctor never makes network calls)
#     "schema_compatible": bool,                 # registry.schema_version_required == current_schema_version
#     "migration_required": bool,                # true if schema_version_required > current_schema_version
#     "current_schema_version": int,
#     "required_schema_version": int,
#     "hard_failures": list[str],               # non-empty → pass=false
#     "warnings": list[str],
#     "notes": str
#   }

import os
import sys
import json
import argparse
from pathlib import Path

# Offline first — do NOT trigger network on import
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE", "1")

REGISTRY_PATH = Path(__file__).parent / "embed_model_registry.json"


def load_registry() -> dict:
    with REGISTRY_PATH.open() as f:
        return json.load(f)


def check_model_cached(model_id: str) -> bool:
    """
    Check whether model weights are present in the HF cache directory.
    We probe two cache conventions:
      - snapshot cache: HF_HOME/hub/models--<org>--<name>/snapshots/
      - sentence-transformers legacy: HF_HOME/sentence_transformers/<org>_<name>/
    """
    hf_home = Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface"))

    # Convention 1: transformers hub cache (models--<slug>)
    slug = model_id.replace("/", "--")
    hub_dir = hf_home / "hub" / f"models--{slug}" / "snapshots"
    if hub_dir.exists():
        snapshots = list(hub_dir.iterdir())
        if snapshots:
            # At least one snapshot dir with files is enough
            for snap in snapshots:
                if any(snap.iterdir()):
                    return True

    # Convention 2: sentence-transformers legacy cache
    st_name = model_id.replace("/", "_")
    st_dir = hf_home / "sentence_transformers" / st_name
    if st_dir.exists() and any(st_dir.iterdir()):
        return True

    return False


def check_hf_token() -> tuple[bool | None, str]:
    """
    Returns (valid: bool | None, detail: str).
    None = no token present (offline baseline is fine if model already cached).
    """
    token = (
        os.environ.get("HUGGINGFACE_HUB_TOKEN")
        or os.environ.get("HF_TOKEN")
    )
    if not token:
        # Try reading from ~/.huggingface/token (huggingface-cli login)
        token_file = Path.home() / ".huggingface" / "token"
        if token_file.exists():
            token = token_file.read_text().strip()

    if not token:
        return None, "no token found (HUGGINGFACE_HUB_TOKEN / HF_TOKEN / ~/.huggingface/token)"

    # Lightweight validation: check token prefix (hf_... is the modern format)
    if not token.startswith("hf_"):
        return False, f"token present but does not match expected format (got prefix: {token[:4]!r})"

    # Note: we do NOT make a network call here — that would require network access and
    # would fail in OFFLINE mode. The token format check is a syntactic gate only.
    # A valid-format token may still be revoked/expired — that only surfaces at fetch time.
    # Caller receives hf_token_valid=True with a warning that this is NOT network-verified.
    return True, "token format valid (hf_...); NOT network-verified — may still be revoked/expired"


def main():
    parser = argparse.ArgumentParser(description="Embedding environment pre-flight check")
    parser.add_argument(
        "--current-schema-version",
        type=int,
        default=4,
        dest="current_schema_version",
        help="Current corpus schema_version from the DB (default: 4)",
    )
    parser.add_argument(
        "--accept-gated",
        action="store_true",
        dest="accept_gated",
        help="Auto-accept HF gate for active model before pre-flight check (calls embed_gate_accept.py)",
    )
    parser.add_argument(
        "--allow-playwright",
        action="store_true",
        dest="allow_playwright",
        help="When --accept-gated is set, allow Playwright fallback for form-gated models",
    )
    parser.add_argument(
        "--allow-download",
        action="store_true",
        dest="allow_download",
        help="If model weights are not in HF cache, attempt to download them (temporarily unsets TRANSFORMERS_OFFLINE)",
    )
    args = parser.parse_args()

    hard_failures: list[str] = []
    warnings: list[str] = []

    # 1. Load registry
    try:
        registry = load_registry()
    except Exception as e:
        out = {
            "pass": False,
            "hard_failures": [f"Failed to load embed_model_registry.json: {e}"],
            "warnings": [],
        }
        print(json.dumps(out, indent=2))
        sys.exit(1)

    active_id = registry.get("active_model_id", "")
    model_info = registry.get("models", {}).get(active_id, {})

    if not model_info:
        hard_failures.append(
            f"active_model_id={active_id!r} not found in registry models table"
        )
        out = {"pass": False, "model_id": active_id, "hard_failures": hard_failures, "warnings": warnings}
        print(json.dumps(out, indent=2))
        sys.exit(1)

    dims = model_info["dims"]
    context_tokens = model_info["context_tokens"]
    license_ = model_info["license"]
    required_schema = model_info["schema_version_required"]
    current_schema = args.current_schema_version
    notes = model_info.get("notes", "")
    model_gated = model_info.get("gated", False)

    # 0. Gate acceptance (optional — only if --accept-gated passed)
    if args.accept_gated and model_gated is not False:
        import subprocess
        accept_cmd = [sys.executable, str(Path(__file__).parent / "embed_gate_accept.py"),
                      "--model-id", active_id]
        if args.allow_playwright:
            accept_cmd.append("--allow-playwright")
        try:
            result_proc = subprocess.run(accept_cmd, capture_output=True, text=True, timeout=60)
            try:
                gate_result = json.loads(result_proc.stdout)
            except json.JSONDecodeError:
                gate_result = {"pass": False, "detail": result_proc.stdout[:300]}
            if not gate_result.get("pass"):
                warnings.append(f"Gate acceptance attempt: {gate_result.get('detail', 'unknown')}")
        except Exception as e:
            warnings.append(f"Gate acceptance subprocess failed: {e}")

    # 2. Check model cache
    cached = check_model_cached(active_id)
    if not cached and args.allow_download:
        # Self-healing: temporarily go online, attempt download, re-check cache
        import subprocess as _subproc
        old_offline = os.environ.pop("TRANSFORMERS_OFFLINE", None)
        old_hf_offline = os.environ.pop("HF_DATASETS_OFFLINE", None)
        warnings.append(f"Model {active_id!r} not cached — attempting download (--allow-download). This may take several minutes.")
        try:
            dl_result = _subproc.run(
                [sys.executable, "-c",
                 f"from sentence_transformers import SentenceTransformer; "
                 f"SentenceTransformer({active_id!r}, trust_remote_code=True); print('download_ok')"],
                capture_output=True, text=True, timeout=600,
            )
            if "download_ok" in dl_result.stdout:
                cached = check_model_cached(active_id)
                if cached:
                    warnings.append(f"Download succeeded — {active_id!r} now in HF cache.")
                else:
                    hard_failures.append(f"Download subprocess reported success but cache still empty for {active_id!r}.")
            else:
                hard_failures.append(
                    f"Download attempt failed for {active_id!r}. stderr: {dl_result.stderr[:400]}"
                )
        except Exception as _dl_exc:
            hard_failures.append(f"Download subprocess raised: {_dl_exc}")
        finally:
            # Restore offline guards
            if old_offline is not None:
                os.environ["TRANSFORMERS_OFFLINE"] = old_offline
            if old_hf_offline is not None:
                os.environ["HF_DATASETS_OFFLINE"] = old_hf_offline
    elif not cached:
        hard_failures.append(
            f"Model weights not found in HF cache for {active_id!r}. "
            f"Run with --allow-download to fetch automatically, or: "
            f"HF_TOKEN=<valid> python -c \"from sentence_transformers import SentenceTransformer; SentenceTransformer('{active_id}', trust_remote_code=True)\" "
            f"to populate the cache manually. Alternatively, set active_model_id to an already-cached model."
        )

    # 3. Check HF token (soft gate — only hard-fail if model is not cached)
    hf_valid, hf_detail = check_hf_token()
    if hf_valid is False:
        if not cached:
            hard_failures.append(f"HF token invalid AND model not cached. Fetch impossible. Detail: {hf_detail}")
        else:
            warnings.append(f"HF token invalid but model is cached — offline embed will work. Detail: {hf_detail}")
    elif hf_valid is None:
        if not cached:
            hard_failures.append("No HF token AND model not cached. Cannot proceed.")
        else:
            warnings.append("No HF token found, but model is cached — offline embed will work.")
    else:
        # hf_valid=True means format check passed only; always surface the network-unverified caveat
        warnings.append(f"HF token: {hf_detail}")

    # 3b. Gated status (registry-based — no network call in doctor)
    #     Uses registry gated field; actual network check is in embed_gate_accept.py.
    if model_gated is False:
        gated_status = "not_gated"
    elif not hf_valid:
        gated_status = "unknown"  # can't verify without token
        if model_gated:
            warnings.append(
                f"Model {active_id!r} is gated ({model_gated}) but no valid HF token — "
                f"run: . .\\scripts\\api_pool.ps1 -Quiet; uv run scripts/embed_doctor.py --accept-gated"
            )
    else:
        # Token present — assume accepted unless cache is missing (which gate check + accept will fix)
        gated_status = "accepted" if cached else "pending"
        if not cached and model_gated:
            hard_failures.append(
                f"Model {active_id!r} is gated ({model_gated}) and not cached. "
                f"Run gate acceptance first: . .\\scripts\\api_pool.ps1 -Quiet; "
                f"uv run scripts/embed_gate_accept.py --model-id {active_id}"
            )

    # 4. Schema compatibility
    schema_compatible = required_schema == current_schema
    migration_required = required_schema > current_schema

    if not schema_compatible:
        if migration_required:
            hard_failures.append(
                f"Schema version mismatch: registry requires schema {required_schema} for {active_id!r}, "
                f"but current DB schema is {current_schema}. "
                f"Migration required: bump CORPUS_SCHEMA_VERSION to {required_schema}, "
                f"DROP vec_embeddings, recreate with FLOAT[{dims}], re-run --embed."
            )
        else:
            # required < current — downgrade scenario (unusual but possible)
            warnings.append(
                f"Registry requires schema {required_schema} but DB is at {current_schema}. "
                f"This model is older than the current schema. Embedding will still run."
            )

    passed = len(hard_failures) == 0

    result = {
        "pass": passed,
        "model_id": active_id,
        "dims": dims,
        "context_tokens": context_tokens,
        "license": license_,
        "gated": model_gated,
        "gated_status": gated_status,
        "cached": cached,
        "hf_token_format_valid": hf_valid,   # True = hf_ prefix present; NOT network-verified
        "hf_token_network_verified": False,  # always False — doctor never makes network calls
        "schema_compatible": schema_compatible,
        "migration_required": migration_required,
        "current_schema_version": current_schema,
        "required_schema_version": required_schema,
        "hard_failures": hard_failures,
        "warnings": warnings,
        "notes": notes,
    }

    print(json.dumps(result, indent=2))
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
