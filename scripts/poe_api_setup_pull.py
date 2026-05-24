#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: poe_api_setup_pull.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ scripts/poe_transport_audit.py
# ║   └─◄ scripts/poe_lane.py
# ╚════════════════════════════════════════════════════════════════════════════

"""
poe_api_setup_pull.py — Poe API setup/state pull orchestrator.

@SID:           TOOL_POE_API_SETUP_PULL_V1
@Shabti:        CLI Script
@Purpose:       Pulls fresh Poe API state for setup/operations:
                - Runs low-token model callability registry scan
                - Runs targeted checks (app-creator/script-bot-creator + baseline callable)
                - Emits normalized mailbox artifacts for Codex/Claude

                Usage:
                uv run scripts/poe_api_setup_pull.py --account 1
"""

from __future__ import annotations


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import argparse
import json
import shlex
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib import error, request

from scripts.lib.poe_auth import resolve_poe_credentials

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE_MODEL = "qwen3.5-397b-a17b-t"
DOC_SOURCES = [
    {
        "url": "https://creator.poe.com/docs/external-applications/external-application-guide",
        "topic": "External application guide",
    },
    {
        "url": "https://creator.poe.com/docs/external-applications/openai-compatible-api",
        "topic": "OpenAI-compatible API limitations",
    },
    {
        "url": "https://creator.poe.com/docs/external-applications/interface-configuration",
        "topic": "Interface configuration prerequisites",
    },
    {
        "url": "https://creator.poe.com/api-reference/listModels",
        "topic": "ListModels API reference",
    },
    {
        "url": "https://poe.com/explore?category=Official",
        "topic": "Official model catalog context",
    },
]


@dataclass
class SetupSnapshot:
    schema_version: int
    generated_on: str
    account: str
    current_point_balance: int | None
    balance_error: str | None
    prompt: str
    openai_max_tokens: int
    registry_limit: int
    sdk_probe_limit: int
    targeted_models: list[str]
    docs_alignment: dict[str, object]
    catalog_summary: dict[str, object]
    registry_summary: dict[str, object]
    targeted_summary: dict[str, object]
    entitlement_verdict: str
    mismatch_explanation: list[str]
    rerun_commands: list[str]


@dataclass
class AccountValidation:
    account: str
    current_point_balance: int | None
    balance_error: str | None
    registry_summary: dict[str, object]
    targeted_summary: dict[str, object]
    entitlement_verdict: str
    callable_models: list[str]


@dataclass
class DualDiscrepancySnapshot:
    schema_version: int
    generated_on: str
    accounts: list[AccountValidation]
    preferred_account_for_calls: str | None
    balance_ranking: list[dict[str, object]]
    callable_overlap: dict[str, object]
    status_discrepancies: dict[str, object]
    discrepancy_inference: list[str]
    docs_alignment: dict[str, object]
    rerun_commands: list[str]


def now_utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def normalize_account(value: str) -> str:
    raw = (value or "").strip()
    if not raw.isdigit():
        raise ValueError("account must be numeric (example: 1, 2, 3)")
    return str(int(raw))


def parse_mailboxes(value: str) -> list[str]:
    allowed = {"codex", "claude"}
    out: list[str] = []
    for chunk in (value or "").split(","):
        name = chunk.strip().lower()
        if name in allowed and name not in out:
            out.append(name)
    if not out:
        out = ["codex"]
    return out


def parse_models(value: str) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for chunk in (value or "").split(","):
        model = chunk.strip()
        if not model or model in seen:
            continue
        seen.add(model)
        out.append(model)
    return out


def parse_accounts(value: str) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for chunk in (value or "").split(","):
        raw = chunk.strip()
        if not raw:
            continue
        account = normalize_account(raw)
        if account in seen:
            continue
        seen.add(account)
        out.append(account)
    if not out:
        out = ["1", "2"]
    return out


def fetch_point_balance(account: str) -> tuple[int | None, str | None]:
    resolution = resolve_poe_credentials(account)
    if not resolution.token:
        return None, f"missing_poe_key_for_account_{account}"
    req = request.Request(
        "https://api.poe.com/usage/current_balance",
        headers={"Authorization": f"Bearer {resolution.token}", "Accept": "application/json"},
        method="GET",
    )
    try:
        with request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8", errors="replace"))
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        return None, f"http_{exc.code}:{raw[:200]}"
    except Exception as exc:
        return None, str(exc)[:200]

    value = payload.get("current_point_balance")
    if isinstance(value, (int, float)):
        return int(value), None
    return None, "missing_current_point_balance"


def run_json_cmd(cmd: list[str]) -> dict:
    proc = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        message = (proc.stdout or "").strip() or (proc.stderr or "").strip() or "command_failed"
        raise RuntimeError(f"cmd_failed rc={proc.returncode}: {message[:800]}")
    text = (proc.stdout or "").strip()
    if not text:
        raise RuntimeError("empty_json_output")
    try:
        return json.loads(text)
    except Exception as exc:
        raise RuntimeError(f"invalid_json_output: {text[:800]}") from exc


def fetch_catalog_summary() -> dict[str, object]:
    data = json.load(request.urlopen("https://api.poe.com/v1/models", timeout=60))
    models = data.get("data")
    if not isinstance(models, list):
        raise RuntimeError("invalid_models_catalog")

    model_ids: list[str] = []
    free_like = 0
    priced = 0
    for item in models:
        if not isinstance(item, dict):
            continue
        model_id = item.get("id")
        if isinstance(model_id, str) and model_id.strip():
            model_ids.append(model_id.strip())
        pricing = item.get("pricing")
        if pricing in (None, {}):
            free_like += 1
        else:
            priced += 1
    return {
        "api_model_count": len(model_ids),
        "free_like_count": free_like,
        "priced_count": priced,
        "api_model_sample": model_ids[:30],
    }


def derive_entitlement_verdict(
    registry_summary: dict[str, object],
    catalog_summary: dict[str, object],
) -> tuple[str, list[str]]:
    counts = registry_summary.get("counts_by_best_status", {})
    if not isinstance(counts, dict):
        counts = {}
    scanned = int(registry_summary.get("total_models") or 0)
    callable_count = int(counts.get("callable", 0) or 0)
    subscription_count = int(counts.get("subscription_required", 0) or 0)
    api_total = int(catalog_summary.get("api_model_count") or 0)

    notes = [
        f"Poe Explore UI can show far more bots than the API model list (`/v1/models` currently reports {api_total}).",
        "Model visibility in `/v1/models` does not guarantee your key can invoke that model.",
        "Your effective key entitlement is inferred from live probe statuses, not catalog count.",
    ]

    if scanned == 0:
        return "no_models_scanned", notes
    if callable_count == 0 and subscription_count > 0:
        return "api_access_blocked_by_subscription_or_points", notes
    if callable_count <= 1 and subscription_count >= max(1, int(scanned * 0.9)):
        return "highly_restricted_api_entitlement", notes
    if callable_count < max(3, int(scanned * 0.1)):
        return "restricted_api_entitlement", notes
    return "broad_api_entitlement", notes


def compute_effective_registry_limit(catalog_total: int, requested_registry_limit: int) -> int:
    effective_registry_limit = catalog_total if requested_registry_limit <= 0 else max(1, requested_registry_limit)
    if catalog_total > 0:
        effective_registry_limit = min(effective_registry_limit, catalog_total)
    return max(1, effective_registry_limit)


def build_docs_alignment() -> dict[str, object]:
    return {
        "base_url": "https://api.poe.com/v1",
        "usage_endpoint": "https://api.poe.com/usage/current_balance",
        "openai_compatible_endpoints": ["/chat/completions", "/responses"],
        "poe_sdk_package": "fastapi-poe",
        "api_access_caveat": "Model visibility in catalog does not guarantee API invocation entitlement (subscription/points gates apply).",
        "known_limitations": "App-Creator and Script-Bot-Creator are documented as unavailable via OpenAI-compatible endpoint/Poe Python library.",
        "ui_vs_api_scope": "Poe UI catalogs community bots; API exposes a smaller, entitlement-gated model list.",
        "sources": DOC_SOURCES,
    }


def collect_account_validation(
    account: str,
    *,
    prompt: str,
    openai_max_tokens: int,
    sdk_probe_limit: int,
    targeted_models: list[str],
    effective_registry_limit: int,
) -> tuple[AccountValidation, dict[str, object], dict[str, object], list[str]]:
    registry_cmd = [
        "uv",
        "run",
        "scripts/poe_transport_audit.py",
        "--registry",
        "--registry-account",
        account,
        "--registry-limit",
        str(effective_registry_limit),
        "--registry-transports",
        "openai,sdk",
        "--sdk-probe-limit",
        str(int(sdk_probe_limit)),
        "--openai-max-tokens",
        str(max(1, int(openai_max_tokens))),
        "--prompt",
        prompt,
        "--json",
    ]
    registry_payload = run_json_cmd(registry_cmd)

    targeted_cmd = [
        "uv",
        "run",
        "scripts/poe_transport_audit.py",
        "--registry",
        "--registry-account",
        account,
        "--registry-models",
        ",".join(targeted_models),
        "--registry-transports",
        "openai,sdk",
        "--sdk-probe-limit",
        "0",
        "--openai-max-tokens",
        str(max(1, int(openai_max_tokens))),
        "--prompt",
        prompt,
        "--json",
    ]
    targeted_payload = run_json_cmd(targeted_cmd)

    registry_summary = {
        "total_models": registry_payload.get("total_models"),
        "counts_by_best_status": registry_payload.get("counts_by_best_status"),
        "cheapest_callable": [candidate.get("model") for candidate in registry_payload.get("cheapest_callable", [])],
    }
    targeted_summary = {
        "counts_by_best_status": targeted_payload.get("counts_by_best_status"),
        "model_statuses": extract_model_statuses(targeted_payload),
    }
    entitlement_verdict, _ = derive_entitlement_verdict(
        registry_summary=registry_summary,
        catalog_summary={"api_model_count": registry_summary.get("total_models")},
    )

    callable_models: list[str] = []
    for model in registry_payload.get("models", []):
        if not isinstance(model, dict):
            continue
        if model.get("best_status") != "callable":
            continue
        name = model.get("model")
        if isinstance(name, str) and name not in callable_models:
            callable_models.append(name)

    validation = AccountValidation(
        account=account,
        current_point_balance=None,
        balance_error=None,
        registry_summary=registry_summary,
        targeted_summary=targeted_summary,
        entitlement_verdict=entitlement_verdict,
        callable_models=callable_models,
    )
    rerun_commands = [
        " ".join(shlex.quote(part) for part in registry_cmd),
        " ".join(shlex.quote(part) for part in targeted_cmd),
    ]
    return validation, registry_payload, targeted_payload, rerun_commands


def write_mailboxes(stem: str, payload_json: str, payload_md: str, mailboxes: list[str]) -> None:
    for mailbox in mailboxes:
        out_dir = REPO_ROOT / mailbox / "mailbox"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{stem}.json").write_text(payload_json, encoding="utf-8")
        (out_dir / f"{stem}.md").write_text(payload_md, encoding="utf-8")


def build_md(snapshot: SetupSnapshot) -> str:
    lines = [
        "# Poe API Setup Pull",
        "",
        f"- Generated: `{snapshot.generated_on}`",
        f"- Account: `{snapshot.account}`",
        f"- Current point balance: `{snapshot.current_point_balance}`",
        f"- Balance error: `{snapshot.balance_error}`",
        f"- OpenAI max tokens: `{snapshot.openai_max_tokens}`",
        f"- Registry limit: `{snapshot.registry_limit}`",
        f"- SDK probe limit: `{snapshot.sdk_probe_limit}`",
        f"- Prompt: `{snapshot.prompt}`",
        f"- Targeted models: `{', '.join(snapshot.targeted_models)}`",
        "",
        "## Catalog Scope",
        f"- API model count: `{snapshot.catalog_summary.get('api_model_count')}`",
        f"- Free-like pricing entries: `{snapshot.catalog_summary.get('free_like_count')}`",
        f"- Priced entries: `{snapshot.catalog_summary.get('priced_count')}`",
        "",
        "## Entitlement Verdict",
        f"- `{snapshot.entitlement_verdict}`",
        "",
        "## Mismatch Explanation",
    ]
    for line in snapshot.mismatch_explanation:
        lines.append(f"- {line}")

    lines.extend([
        "",
        "## Docs Alignment",
        f"- Base URL: `{snapshot.docs_alignment.get('base_url')}`",
        f"- OpenAI-compatible endpoints: `{', '.join(snapshot.docs_alignment.get('openai_compatible_endpoints', []))}`",
        f"- Poe SDK path: `{snapshot.docs_alignment.get('poe_sdk_package')}`",
        f"- API access caveat: `{snapshot.docs_alignment.get('api_access_caveat')}`",
        f"- Known limitations: `{snapshot.docs_alignment.get('known_limitations')}`",
        f"- UI/API scope note: `{snapshot.docs_alignment.get('ui_vs_api_scope')}`",
        "",
        "## Registry Summary",
    ])
    for key in ("total_models", "counts_by_best_status", "cheapest_callable"):
        value = snapshot.registry_summary.get(key)
        lines.append(f"- {key}: `{value}`")

    lines.extend(["", "## Targeted Summary"])
    for key in ("counts_by_best_status", "model_statuses"):
        value = snapshot.targeted_summary.get(key)
        lines.append(f"- {key}: `{value}`")

    lines.extend(["", "## Rerun Commands"])
    for cmd in snapshot.rerun_commands:
        lines.append(f"- `{cmd}`")

    lines.extend(["", "## Sources"])
    for source in DOC_SOURCES:
        lines.append(f"- {source['topic']}: `{source['url']}`")

    return "\n".join(lines).rstrip() + "\n"


def extract_model_statuses(payload: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in payload.get("models", []):
        model = item.get("model")
        status = item.get("best_status")
        if isinstance(model, str) and isinstance(status, str):
            out[model] = status
    return out


def build_targeted_md(payload: dict) -> str:
    lines = [
        "# Poe Callability Targeted Sample",
        "",
        f"- Generated: `{payload.get('generated_on')}`",
        f"- Account: `{payload.get('account')}`",
        f"- Total models: `{payload.get('total_models')}`",
        f"- Counts by best status: `{payload.get('counts_by_best_status')}`",
        "",
        "## Models",
    ]
    for model in payload.get("models", []):
        name = model.get("model")
        best_status = model.get("best_status")
        openai_status = ((model.get("openai") or {}).get("status")) if isinstance(model, dict) else None
        sdk_status = ((model.get("sdk") or {}).get("status")) if isinstance(model, dict) else None
        if not isinstance(name, str):
            continue
        lines.append(f"- `{name}`: best=`{best_status}` openai=`{openai_status}` sdk=`{sdk_status}`")
    return "\n".join(lines).rstrip() + "\n"


def extract_best_status_map(payload: dict[str, object]) -> dict[str, str]:
    out: dict[str, str] = {}
    for model in payload.get("models", []):
        if not isinstance(model, dict):
            continue
        name = model.get("model")
        status = model.get("best_status")
        if isinstance(name, str) and isinstance(status, str):
            out[name] = status
    return out


def build_dual_discrepancy_snapshot(
    *,
    validations: list[AccountValidation],
    registry_payloads: dict[str, dict[str, object]],
    docs_alignment: dict[str, object],
    rerun_commands: list[str],
) -> DualDiscrepancySnapshot:
    callable_sets = {item.account: set(item.callable_models) for item in validations}
    all_accounts = [item.account for item in validations]
    shared_callable: list[str] = []
    if all_accounts:
        shared = callable_sets[all_accounts[0]].copy()
        for account in all_accounts[1:]:
            shared &= callable_sets[account]
        shared_callable = sorted(shared)

    unique_by_account: dict[str, list[str]] = {}
    for account in all_accounts:
        others = set()
        for other in all_accounts:
            if other == account:
                continue
            others |= callable_sets[other]
        unique_by_account[account] = sorted(callable_sets[account] - others)

    status_maps = {account: extract_best_status_map(registry_payloads.get(account, {})) for account in all_accounts}
    all_models: set[str] = set()
    for mapping in status_maps.values():
        all_models |= set(mapping.keys())

    status_deltas: list[dict[str, object]] = []
    for model in sorted(all_models):
        per_account: dict[str, str] = {}
        for account in all_accounts:
            per_account[account] = status_maps.get(account, {}).get(model, "not_tested")
        if len(set(per_account.values())) > 1:
            status_deltas.append({"model": model, "statuses": per_account})

    balance_ranking = sorted(
        [
            {
                "account": item.account,
                "current_point_balance": item.current_point_balance,
                "balance_error": item.balance_error,
            }
            for item in validations
        ],
        key=lambda row: (
            -1 if isinstance(row.get("current_point_balance"), int) else 1,
            -(row.get("current_point_balance") or -1),
            str(row.get("account")),
        ),
    )

    # Determine a preferred account by callable count first, then balance.
    def preference_key(item: AccountValidation) -> tuple[int, int]:
        callable_count = len(item.callable_models)
        balance = item.current_point_balance if isinstance(item.current_point_balance, int) else -1
        return callable_count, balance

    preferred_account_for_calls: str | None = None
    if validations:
        preferred_account_for_calls = sorted(validations, key=preference_key, reverse=True)[0].account

    inference: list[str] = []
    balances = [item.current_point_balance for item in validations if isinstance(item.current_point_balance, int)]
    if balances:
        inference.append(
            "Higher point balance only matters when statuses include `insufficient_fund`; subscription-gated models remain blocked regardless of balance."
        )
    if status_deltas:
        inference.append(
            f"Found {len(status_deltas)} model status deltas across accounts; review `status_discrepancies.deltas` for account-specific access drift."
        )
    else:
        inference.append("No model-level status deltas detected across tested accounts in this run.")

    return DualDiscrepancySnapshot(
        schema_version=1,
        generated_on=now_utc(),
        accounts=validations,
        preferred_account_for_calls=preferred_account_for_calls,
        balance_ranking=balance_ranking,
        callable_overlap={
            "shared_callable_models": shared_callable,
            "unique_callable_by_account": unique_by_account,
        },
        status_discrepancies={
            "delta_count": len(status_deltas),
            "deltas": status_deltas,
        },
        discrepancy_inference=inference,
        docs_alignment=docs_alignment,
        rerun_commands=rerun_commands,
    )


def build_dual_md(snapshot: DualDiscrepancySnapshot) -> str:
    lines = [
        "# Poe API Dual Discrepancy",
        "",
        f"- Generated: `{snapshot.generated_on}`",
        f"- Preferred account for calls: `{snapshot.preferred_account_for_calls}`",
        "",
        "## Balance Ranking",
    ]
    for row in snapshot.balance_ranking:
        lines.append(
            f"- Account `{row.get('account')}`: balance=`{row.get('current_point_balance')}` error=`{row.get('balance_error')}`"
        )

    lines.extend(["", "## Account Summaries"])
    for account in snapshot.accounts:
        lines.append(f"- Account `{account.account}`")
        lines.append(f"  - entitlement_verdict=`{account.entitlement_verdict}`")
        lines.append(f"  - callable_count=`{len(account.callable_models)}`")
        lines.append(f"  - counts_by_best_status=`{account.registry_summary.get('counts_by_best_status')}`")
        lines.append(f"  - targeted_model_statuses=`{account.targeted_summary.get('model_statuses')}`")

    lines.extend(["", "## Callable Overlap"])
    lines.append(f"- shared_callable_models: `{snapshot.callable_overlap.get('shared_callable_models')}`")
    lines.append(f"- unique_callable_by_account: `{snapshot.callable_overlap.get('unique_callable_by_account')}`")

    lines.extend(["", "## Status Discrepancies"])
    lines.append(f"- delta_count: `{snapshot.status_discrepancies.get('delta_count')}`")

    lines.extend(["", "## Inference"])
    for note in snapshot.discrepancy_inference:
        lines.append(f"- {note}")

    lines.extend(["", "## Rerun Commands"])
    for cmd in snapshot.rerun_commands:
        lines.append(f"- `{cmd}`")

    lines.extend(["", "## Sources"])
    for source in DOC_SOURCES:
        lines.append(f"- {source['topic']}: `{source['url']}`")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Run Poe API setup pull with low-token diagnostics.")
    ap.add_argument("--account", default="1", help="Poe account slot number (maps to POE_API_KEY_<n>).")
    ap.add_argument("--accounts", default="1,2", help="Comma-separated account slots for dual discrepancy mode.")
    ap.add_argument(
        "--dual-discrepancy",
        action="store_true",
        help="Run dual-account discrepancy validation (entitlements + balances + status deltas).",
    )
    ap.add_argument("--prompt", default="Return exactly: OK")
    ap.add_argument("--openai-max-tokens", type=int, default=1)
    ap.add_argument("--registry-limit", type=int, default=0, help="Registry scan model cap (<=0 means all models returned by /v1/models).")
    ap.add_argument("--sdk-probe-limit", type=int, default=15)
    ap.add_argument("--targeted-models", default="app-creator,script-bot-creator")
    ap.add_argument("--baseline-model", default=DEFAULT_BASELINE_MODEL)
    ap.add_argument("--mailboxes", default="codex,claude")
    ap.add_argument("--json", action="store_true", help="Emit the final snapshot JSON to stdout.")
    args = ap.parse_args()

    mailboxes = parse_mailboxes(args.mailboxes)
    targeted_models = parse_models(args.targeted_models)
    if args.baseline_model.strip() and args.baseline_model.strip() not in targeted_models:
        targeted_models = [args.baseline_model.strip()] + targeted_models

    openai_max_tokens = max(1, int(args.openai_max_tokens))
    sdk_probe_limit = max(0, int(args.sdk_probe_limit))
    catalog_summary = fetch_catalog_summary()
    catalog_total = int(catalog_summary.get("api_model_count") or 0)
    effective_registry_limit = compute_effective_registry_limit(catalog_total, int(args.registry_limit))
    docs_alignment = build_docs_alignment()

    if args.dual_discrepancy:
        accounts = parse_accounts(args.accounts)
        validations: list[AccountValidation] = []
        registry_payloads: dict[str, dict[str, object]] = {}
        rerun_commands: list[str] = []

        for account in accounts:
            validation, registry_payload, targeted_payload, account_commands = collect_account_validation(
                account,
                prompt=args.prompt,
                openai_max_tokens=openai_max_tokens,
                sdk_probe_limit=sdk_probe_limit,
                targeted_models=targeted_models,
                effective_registry_limit=effective_registry_limit,
            )
            point_balance, balance_error = fetch_point_balance(account)
            validation.current_point_balance = point_balance
            validation.balance_error = balance_error
            validations.append(validation)
            registry_payloads[account] = registry_payload
            rerun_commands.extend(account_commands)

            per_account_targeted_json = json.dumps(targeted_payload, indent=2) + "\n"
            per_account_targeted_md = build_targeted_md(targeted_payload)
            write_mailboxes(
                f"POE_CALLABILITY_TARGETED_SAMPLE_ACCOUNT_{account}",
                per_account_targeted_json,
                per_account_targeted_md,
                mailboxes,
            )

        rerun_commands.append(
            " ".join(
                [
                    "uv",
                    "run",
                    "scripts/poe_api_setup_pull.py",
                    "--dual-discrepancy",
                    "--accounts",
                    ",".join(accounts),
                    "--registry-limit",
                    str(effective_registry_limit),
                    "--sdk-probe-limit",
                    str(sdk_probe_limit),
                    "--openai-max-tokens",
                    str(openai_max_tokens),
                    "--targeted-models",
                    ",".join(targeted_models),
                    "--prompt",
                    shlex.quote(args.prompt),
                ]
            )
        )

        dual_snapshot = build_dual_discrepancy_snapshot(
            validations=validations,
            registry_payloads=registry_payloads,
            docs_alignment=docs_alignment,
            rerun_commands=rerun_commands,
        )
        payload_json = json.dumps(asdict(dual_snapshot), indent=2) + "\n"
        payload_md = build_dual_md(dual_snapshot)
        write_mailboxes("POE_API_DUAL_DISCREPANCY_LATEST", payload_json, payload_md, mailboxes)

        if args.json:
            print(payload_json, end="")
        else:
            print(f"ok: wrote POE_API_DUAL_DISCREPANCY_LATEST.* to {','.join(mailboxes)} mailbox(es)")
        return 0

    account = normalize_account(args.account)
    validation, registry_payload, targeted_payload, rerun_commands = collect_account_validation(
        account,
        prompt=args.prompt,
        openai_max_tokens=openai_max_tokens,
        sdk_probe_limit=sdk_probe_limit,
        targeted_models=targeted_models,
        effective_registry_limit=effective_registry_limit,
    )
    point_balance, balance_error = fetch_point_balance(account)
    validation.current_point_balance = point_balance
    validation.balance_error = balance_error

    entitlement_verdict, mismatch_explanation = derive_entitlement_verdict(
        registry_summary=validation.registry_summary,
        catalog_summary=catalog_summary,
    )

    snapshot = SetupSnapshot(
        schema_version=1,
        generated_on=now_utc(),
        account=account,
        current_point_balance=point_balance,
        balance_error=balance_error,
        prompt=args.prompt,
        openai_max_tokens=openai_max_tokens,
        registry_limit=effective_registry_limit,
        sdk_probe_limit=sdk_probe_limit,
        targeted_models=targeted_models,
        docs_alignment=docs_alignment,
        catalog_summary=catalog_summary,
        registry_summary=validation.registry_summary,
        targeted_summary=validation.targeted_summary,
        entitlement_verdict=entitlement_verdict,
        mismatch_explanation=mismatch_explanation,
        rerun_commands=rerun_commands,
    )

    payload_json = json.dumps(asdict(snapshot), indent=2) + "\n"
    payload_md = build_md(snapshot)
    write_mailboxes("POE_API_SETUP_PULL_LATEST", payload_json, payload_md, mailboxes)

    targeted_json = json.dumps(targeted_payload, indent=2) + "\n"
    targeted_md = build_targeted_md(targeted_payload)
    write_mailboxes("POE_CALLABILITY_TARGETED_SAMPLE", targeted_json, targeted_md, mailboxes)

    if args.json:
        print(payload_json, end="")
    else:
        print(f"ok: wrote POE_API_SETUP_PULL_LATEST.* to {','.join(mailboxes)} mailbox(es)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
