#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: poe_transport_audit.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ scripts/poe_lane.py
# ║   └─◄ scripts/poe_sdk_lane.py
# ╚════════════════════════════════════════════════════════════════════════════

"""
poe_transport_audit.py — Poe transport audit + callability registry.

@SID:           TOOL_POE_TRANSPORT_AUDIT_V1
@Shabti:        CLI Script
@Purpose:       Compares OpenAI-compatible lane vs Poe SDK lane and can scan
                a broader model set to classify callability/error gates with
                low-token probes for cost-aware automation.
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
import scripts.poe_lane as _poe_lane  # noqa: E402
import scripts.poe_sdk_lane as _poe_sdk_lane  # noqa: E402
STATUS_PRIORITY = [
    "callable",
    "insufficient_fund",
    "subscription_required",
    "not_api_accessible",
    "model_not_accessible",
    "rate_limited",
    "network_error",
    "missing_key",
    "unknown_error",
    "not_tested",
]


@dataclass
class ProbeResult:
    rc: int
    ok: bool
    status: str
    text_preview: str | None
    error: str | None


@dataclass
class AccountAudit:
    account: str
    openai_control: ProbeResult
    openai_app_creator: ProbeResult
    sdk_control: ProbeResult
    sdk_app_creator: ProbeResult
    openai_models_count: int | None
    openai_has_app_creator: bool | None


@dataclass
class TransportAudit:
    schema_version: int
    generated_on: str
    control_model: str
    target_bot: str
    openai_max_tokens: int
    accounts: list[AccountAudit]
    recommendation: str
    rationale: str


@dataclass
class RegistryCandidate:
    model: str
    transport: str | None
    cost_tier: str
    openai_status: str
    sdk_status: str


@dataclass
class RegistryModelAudit:
    model: str
    cost_tier: str
    openai: ProbeResult | None
    sdk: ProbeResult | None
    best_transport: str | None
    best_status: str
    discrepancy: str | None


@dataclass
class RegistryAudit:
    schema_version: int
    generated_on: str
    account: str
    prompt: str
    openai_max_tokens: int
    transports: list[str]
    sdk_probe_limit: int
    model_source: str
    source_error: str | None
    total_models: int
    counts_by_best_status: dict[str, int]
    counts_openai: dict[str, int]
    counts_sdk: dict[str, int]
    cheapest_callable: list[RegistryCandidate]
    models: list[RegistryModelAudit]


def normalize_account(value: str | None) -> str | None:
    if value is None:
        return None
    raw = value.strip()
    if not raw or not raw.isdigit():
        return None
    return str(int(raw))


def now_utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def parse_mailboxes(value: str) -> list[str]:
    allowed = {"codex", "claude"}
    ordered: list[str] = []
    for chunk in (value or "").split(","):
        name = chunk.strip().lower()
        if not name or name not in allowed:
            continue
        if name not in ordered:
            ordered.append(name)
    if not ordered:
        ordered.append("codex")
    return ordered


def parse_accounts(raw: str) -> list[str]:
    out: list[str] = []
    for token in (raw or "").split(","):
        v = normalize_account(token)
        if v and v not in out:
            out.append(v)
    if not out:
        out = ["1", "2"]
    return out


def parse_transports(raw: str) -> list[str]:
    allowed = {"openai", "sdk"}
    out: list[str] = []
    for token in (raw or "").split(","):
        name = token.strip().lower()
        if name in allowed and name not in out:
            out.append(name)
    if not out:
        out = ["openai"]
    return out


def parse_models(raw: str) -> list[str]:
    models: list[str] = []
    seen: set[str] = set()
    for token in (raw or "").split(","):
        model = token.strip()
        if not model or model in seen:
            continue
        seen.add(model)
        models.append(model)
    return models


def run_cmd(cmd: list[str]) -> tuple[int, str, str]:
    """Kept for backward compatibility — no longer used internally."""
    import subprocess as _sp
    proc = _sp.run(
        cmd,
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def parse_json_line(stdout: str) -> dict[str, Any] | None:
    text = stdout.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        return None


def classify_status(ok: bool, error: str | None) -> str:
    if ok:
        return "callable"
    lower = (error or "").lower()
    if "subscription_required" in lower or "requires an active poe subscription" in lower:
        return "subscription_required"
    if "insufficient_fund" in lower or "used up your points" in lower:
        return "insufficient_fund"
    if "does not support api access" in lower or "bot_not_api_accessible" in lower:
        return "not_api_accessible"
    if "does not exist or you do not have access to it" in lower or "model_not_accessible_for_this_key" in lower:
        return "model_not_accessible"
    if "http 429" in lower or "rate limit" in lower:
        return "rate_limited"
    if "network_error" in lower or "timed out" in lower:
        return "network_error"
    if "missing poe key" in lower:
        return "missing_key"
    return "unknown_error"


def needs_min_token_retry(message: str, max_tokens: int) -> bool:
    lower = message.lower()
    return (
        max_tokens < 16
        and "invalid 'max_output_tokens'" in lower
        and "expected a value >= 16" in lower
    )


def infer_cost_tier(model: str) -> str:
    lower = model.lower()
    high_markers = ("opus", "pro", "thinking", "reasoning", "max")
    low_markers = ("mini", "flash", "instant", "fast", "nano", "small", "haiku", "lite")
    mid_markers = ("sonnet", "plus", "qwen", "kimi", "glm", "deepseek", "gemini", "grok")

    if any(marker in lower for marker in high_markers):
        return "likely_high"
    if any(marker in lower for marker in low_markers):
        return "likely_low"
    if any(marker in lower for marker in mid_markers):
        return "likely_mid"
    return "unknown"


def cost_rank(cost_tier: str) -> int:
    order = {
        "likely_low": 1,
        "likely_mid": 2,
        "likely_high": 3,
        "unknown": 4,
    }
    return order.get(cost_tier, 4)


def count_statuses(statuses: list[str]) -> dict[str, int]:
    out: dict[str, int] = {}
    for status in statuses:
        out[status] = out.get(status, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: kv[0]))


def pick_priority_status(statuses: list[str]) -> str:
    ranked = {status: idx for idx, status in enumerate(STATUS_PRIORITY)}
    best = "unknown_error"
    best_rank = ranked.get(best, 999)
    for status in statuses:
        rank = ranked.get(status, 999)
        if rank < best_rank:
            best = status
            best_rank = rank
    return best


def choose_best_transport(openai: ProbeResult | None, sdk: ProbeResult | None) -> tuple[str | None, str]:
    if openai and openai.status == "callable":
        return "openai", "callable"
    if sdk and sdk.status == "callable":
        return "sdk", "callable"

    candidates: list[tuple[str, str]] = []
    if openai:
        candidates.append(("openai", openai.status))
    if sdk:
        candidates.append(("sdk", sdk.status))
    if not candidates:
        return None, "not_tested"

    best_status = pick_priority_status([status for _, status in candidates])
    for transport in ("openai", "sdk"):
        for candidate_transport, status in candidates:
            if candidate_transport == transport and status == best_status:
                return transport, best_status
    return candidates[0][0], candidates[0][1]


def probe_openai(
    account: str,
    model: str,
    prompt: str,
    effort: str = "",
    max_tokens: int = 1,
) -> ProbeResult:
    requested_tokens = max(1, int(max_tokens))
    account_slot = normalize_account(account)
    try:
        resolution = _poe_lane.resolve_poe_credentials(account_slot)
    except Exception as e:
        return ProbeResult(rc=2, ok=False, status="missing_key", text_preview=None, error=str(e)[:600])
    if not resolution.token:
        return ProbeResult(rc=2, ok=False, status="missing_key", text_preview=None, error="missing POE key")

    def _do_probe(tokens: int) -> ProbeResult:
        try:
            text, _ = _poe_lane.run_chat(
                base_url=_poe_lane.DEFAULT_BASE_URL,
                token=resolution.token,
                model=model,
                prompt=prompt,
                system="",
                max_tokens=tokens,
                effort=effort or None,
            )
            return ProbeResult(
                rc=0, ok=True, status="callable",
                text_preview=(text[:300] if text else None), error=None,
            )
        except Exception as e:
            message = str(e)
            return ProbeResult(
                rc=1, ok=False, status=classify_status(False, message),
                text_preview=None, error=message[:600],
            )

    result = _do_probe(requested_tokens)
    if not result.ok and needs_min_token_retry(result.error or "", requested_tokens):
        result = _do_probe(16)
    return result


def probe_sdk(account: str, bot: str, prompt: str, effort: str = "") -> ProbeResult:
    account_slot = normalize_account(account)
    try:
        resolution = _poe_lane.resolve_poe_credentials(account_slot)
    except Exception as e:
        return ProbeResult(rc=2, ok=False, status="missing_key", text_preview=None, error=str(e)[:600])
    if not resolution.token:
        return ProbeResult(rc=2, ok=False, status="missing_key", text_preview=None, error="missing POE key")
    try:
        text = _poe_sdk_lane.run_probe(bot=bot, prompt=prompt, token=resolution.token, effort=effort or None)
        return ProbeResult(rc=0, ok=True, status="callable",
                          text_preview=(text[:300] if text else None), error=None)
    except Exception as e:
        message = str(e)
        return ProbeResult(rc=1, ok=False, status=classify_status(False, message),
                          text_preview=None, error=message[:600])


def list_openai_models(account: str, limit: int) -> tuple[list[str], str | None]:
    account_slot = normalize_account(account)
    try:
        resolution = _poe_lane.resolve_poe_credentials(account_slot)
    except Exception as e:
        return [], str(e)[:600]
    if not resolution.token:
        return [], "missing POE key"
    try:
        model_ids, _ = _poe_lane.run_models(_poe_lane.DEFAULT_BASE_URL, resolution.token, max(1, int(limit)))
        return model_ids, None
    except Exception as e:
        return [], str(e)[:600]


def inspect_openai_models(account: str, limit: int) -> tuple[int | None, bool | None]:
    models, err = list_openai_models(account=account, limit=limit)
    if err:
        return None, None
    has_app_creator = any(model.lower() == "app-creator" for model in models)
    return len(models), has_app_creator


def choose_recommendation(report: TransportAudit) -> tuple[str, str]:
    any_openai_app = any(a.openai_app_creator.ok for a in report.accounts)
    any_sdk_app = any(a.sdk_app_creator.ok for a in report.accounts)
    any_openai_control = any(a.openai_control.ok for a in report.accounts)
    any_sdk_control = any(a.sdk_control.ok for a in report.accounts)

    if any_openai_app and not any_sdk_app:
        return "openai-compatible", "App-Creator works on OpenAI-compatible lane; SDK did not match."
    if any_sdk_app and not any_openai_app:
        return "poe-sdk", "App-Creator works on Poe SDK lane; OpenAI-compatible did not match."
    if any_openai_app and any_sdk_app:
        return "openai-compatible", "Both lanes can access App-Creator; OpenAI-compatible is better for portability."

    if any_openai_control and not any_sdk_control:
        return "openai-compatible", "Control probes work on OpenAI-compatible lane while SDK control probes failed."
    if any_openai_control and any_sdk_control:
        return "openai-compatible", "Both lanes work for control probes, but App-Creator is not API-accessible on tested keys."

    statuses: list[str] = []
    for account in report.accounts:
        statuses.extend(
            [
                account.openai_control.status,
                account.openai_app_creator.status,
                account.sdk_control.status,
                account.sdk_app_creator.status,
            ]
        )
    dominant = pick_priority_status(statuses)
    if dominant == "subscription_required":
        return "indeterminate", "Both lanes are currently subscription-gated on tested models."
    if dominant == "insufficient_fund":
        return "indeterminate", "Both lanes are currently point-gated on tested models."
    return "indeterminate", "Neither lane passed control probes consistently; re-check account credits and API permissions."


def write_mailbox(report: TransportAudit, mailboxes: list[str]) -> None:
    json_payload = json.dumps(asdict(report), indent=2) + "\n"

    lines = [
        "# Poe Transport Audit",
        "",
        f"- Generated: `{report.generated_on}`",
        f"- Control model: `{report.control_model}`",
        f"- Target bot: `{report.target_bot}`",
        f"- OpenAI max tokens: `{report.openai_max_tokens}`",
        f"- Recommendation: `{report.recommendation}`",
        f"- Rationale: `{report.rationale}`",
        "",
        "## Accounts",
    ]
    for acc in report.accounts:
        lines.append(f"- Account `{acc.account}`")
        lines.append(f"  - OpenAI control: `{acc.openai_control.status}`")
        lines.append(f"  - OpenAI app-creator: `{acc.openai_app_creator.status}`")
        lines.append(f"  - SDK control: `{acc.sdk_control.status}`")
        lines.append(f"  - SDK app-creator: `{acc.sdk_app_creator.status}`")
        lines.append(f"  - OpenAI model count inspected: `{acc.openai_models_count}`")
        lines.append(f"  - OpenAI has app-creator id: `{acc.openai_has_app_creator}`")

    md_payload = "\n".join(lines).rstrip() + "\n"

    for mailbox in mailboxes:
        out_dir = REPO_ROOT / mailbox / "mailbox"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "POE_TRANSPORT_AUDIT_LATEST.json").write_text(json_payload, encoding="utf-8")
        (out_dir / "POE_TRANSPORT_AUDIT_LATEST.md").write_text(md_payload, encoding="utf-8")


def write_registry_mailbox(report: RegistryAudit, mailboxes: list[str]) -> None:
    json_payload = json.dumps(asdict(report), indent=2) + "\n"

    lines = [
        "# Poe Callability Registry",
        "",
        f"- Generated: `{report.generated_on}`",
        f"- Account: `{report.account}`",
        f"- Total models probed: `{report.total_models}`",
        f"- Transports: `{','.join(report.transports)}`",
        f"- SDK probe limit: `{report.sdk_probe_limit}`",
        f"- OpenAI max tokens: `{report.openai_max_tokens}`",
        f"- Model source: `{report.model_source}`",
    ]
    if report.source_error:
        lines.append(f"- Source error: `{report.source_error}`")

    lines.extend(["", "## Best Status Counts"])
    for status, count in report.counts_by_best_status.items():
        lines.append(f"- `{status}`: `{count}`")

    lines.extend(["", "## Cheapest Callable Candidates"])
    if not report.cheapest_callable:
        lines.append("- none")
    else:
        for candidate in report.cheapest_callable:
            lines.append(
                f"- `{candidate.model}` via `{candidate.transport}` ({candidate.cost_tier}) "
                f"[openai={candidate.openai_status}, sdk={candidate.sdk_status}]"
            )

    md_payload = "\n".join(lines).rstrip() + "\n"

    for mailbox in mailboxes:
        out_dir = REPO_ROOT / mailbox / "mailbox"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "POE_CALLABILITY_REGISTRY_LATEST.json").write_text(json_payload, encoding="utf-8")
        (out_dir / "POE_CALLABILITY_REGISTRY_LATEST.md").write_text(md_payload, encoding="utf-8")


def sort_models_for_cost(models: list[str]) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for model in models:
        if model not in seen:
            seen.add(model)
            unique.append(model)
    return sorted(unique, key=lambda model: (cost_rank(infer_cost_tier(model)), model.lower()))


def run_registry_audit(
    account: str,
    models: list[str],
    transports: list[str],
    prompt: str,
    openai_max_tokens: int,
    openai_effort: str,
    sdk_effort: str,
    sdk_probe_limit: int,
    model_source: str,
    source_error: str | None,
    cache: dict[str, Any] | None = None,
) -> RegistryAudit:
    models_sorted = sort_models_for_cost(models)

    audits: list[RegistryModelAudit] = []
    openai_statuses: list[str] = []
    sdk_statuses: list[str] = []

    for idx, model in enumerate(models_sorted):
        # Use cached result when available (skips live probe).
        if cache is not None and model in cache:
            cached = cache[model]
            cached_openai_status = cached.get("openai_status", "not_tested")
            cached_sdk_status = cached.get("sdk_status", "not_tested")
            openai_result: ProbeResult | None = (
                ProbeResult(rc=0, ok=(cached_openai_status == "callable"),
                            status=cached_openai_status, text_preview=None, error=None)
                if "openai" in transports else None
            )
            sdk_result: ProbeResult | None = (
                ProbeResult(rc=0, ok=(cached_sdk_status == "callable"),
                            status=cached_sdk_status, text_preview=None, error=None)
                if "sdk" in transports else None
            )
            if openai_result:
                openai_statuses.append(openai_result.status)
            if sdk_result:
                sdk_statuses.append(sdk_result.status)
            audits.append(RegistryModelAudit(
                model=model, cost_tier=infer_cost_tier(model),
                openai=openai_result, sdk=sdk_result,
                best_transport=cached.get("best_transport"),
                best_status=cached.get("best_status", "not_tested"),
                discrepancy=None,
            ))
            continue

        openai_result = None
        sdk_result = None

        if "openai" in transports:
            openai_result = probe_openai(
                account=account,
                model=model,
                prompt=prompt,
                effort=openai_effort,
                max_tokens=openai_max_tokens,
            )
            openai_statuses.append(openai_result.status)

        sdk_should_probe = "sdk" in transports and (
            "openai" not in transports or sdk_probe_limit <= 0 or idx < sdk_probe_limit
        )
        if sdk_should_probe:
            sdk_result = probe_sdk(account=account, bot=model, prompt=prompt, effort=sdk_effort)
            sdk_statuses.append(sdk_result.status)
        elif "sdk" in transports:
            sdk_statuses.append("not_tested")

        best_transport, best_status = choose_best_transport(openai_result, sdk_result)

        discrepancy = None
        if openai_result and sdk_result and openai_result.status != sdk_result.status:
            discrepancy = f"openai={openai_result.status};sdk={sdk_result.status}"

        audits.append(
            RegistryModelAudit(
                model=model,
                cost_tier=infer_cost_tier(model),
                openai=openai_result,
                sdk=sdk_result,
                best_transport=best_transport,
                best_status=best_status,
                discrepancy=discrepancy,
            )
        )

    best_statuses = [audit.best_status for audit in audits]
    callable_candidates: list[RegistryCandidate] = []
    for audit in audits:
        if audit.best_status != "callable":
            continue
        callable_candidates.append(
            RegistryCandidate(
                model=audit.model,
                transport=audit.best_transport,
                cost_tier=audit.cost_tier,
                openai_status=(audit.openai.status if audit.openai else "not_tested"),
                sdk_status=(audit.sdk.status if audit.sdk else "not_tested"),
            )
        )

    callable_candidates = sorted(
        callable_candidates,
        key=lambda candidate: (
            cost_rank(candidate.cost_tier),
            0 if candidate.transport == "openai" else 1,
            candidate.model.lower(),
        ),
    )

    return RegistryAudit(
        schema_version=1,
        generated_on=now_utc(),
        account=account,
        prompt=prompt,
        openai_max_tokens=max(1, int(openai_max_tokens)),
        transports=transports,
        sdk_probe_limit=sdk_probe_limit,
        model_source=model_source,
        source_error=source_error,
        total_models=len(audits),
        counts_by_best_status=count_statuses(best_statuses),
        counts_openai=count_statuses(openai_statuses if openai_statuses else ["not_tested"]),
        counts_sdk=count_statuses(sdk_statuses if sdk_statuses else ["not_tested"]),
        cheapest_callable=callable_candidates[:25],
        models=audits,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit Poe OpenAI-compatible lane vs Poe SDK lane.")
    ap.add_argument("--accounts", default="1,2", help="Comma-separated numeric account list (example: 1,2,3).")
    ap.add_argument("--control-model", default="claude-sonnet-4.5")
    ap.add_argument("--target-bot", default="app-creator")
    ap.add_argument("--prompt", default="Return exactly: OK")
    ap.add_argument("--models-limit", type=int, default=400)
    ap.add_argument("--openai-max-tokens", type=int, default=1)
    ap.add_argument("--openai-effort", default="")
    ap.add_argument("--target-effort", default="max")
    ap.add_argument("--sdk-effort", default="")

    ap.add_argument("--registry", action="store_true", help="Scan model callability/error gates in low-token mode.")
    ap.add_argument("--registry-account", default="", help="Account slot for registry mode; defaults to first --accounts entry.")
    ap.add_argument("--registry-limit", type=int, default=80, help="Max model IDs fetched from Poe model list in registry mode (<=0 means all IDs returned by /v1/models).")
    ap.add_argument("--registry-models", default="", help="Comma-separated explicit model IDs for registry mode.")
    ap.add_argument("--registry-transports", default="openai,sdk", help="Registry transports from {openai,sdk}.")
    ap.add_argument("--sdk-probe-limit", type=int, default=20, help="Registry mode: max models to probe through SDK (<=0 means no cap).")

    ap.add_argument("--emit-mailbox", action="store_true")
    ap.add_argument("--mailboxes", default="codex,claude")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--cache", action="store_true",
                    help="Load/save model probe results to cache; skip re-probing cached models.")
    args = ap.parse_args()

    mailboxes = parse_mailboxes(args.mailboxes)

    if args.registry:
        accounts = parse_accounts(args.accounts)
        account = normalize_account(args.registry_account) or accounts[0]
        transports = parse_transports(args.registry_transports)

        # Cache load.
        cache_path = REPO_ROOT / "codex" / "mailbox" / "cache" / "poe_transport_cache.json"
        cache: dict[str, Any] = {}
        if args.cache and cache_path.exists():
            try:
                loaded = json.loads(cache_path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    cache = loaded
            except Exception:
                cache = {}

        explicit_models = parse_models(args.registry_models)
        if explicit_models:
            models = explicit_models
            source = "explicit"
            source_error = None
        else:
            registry_limit = int(args.registry_limit)
            effective_limit = 1000000 if registry_limit <= 0 else max(1, registry_limit)
            models, source_error = list_openai_models(account=account, limit=effective_limit)
            source = "models_api"

        report = run_registry_audit(
            account=account,
            models=models,
            transports=transports,
            prompt=args.prompt,
            openai_max_tokens=max(1, int(args.openai_max_tokens)),
            openai_effort=args.openai_effort,
            sdk_effort=args.sdk_effort,
            sdk_probe_limit=int(args.sdk_probe_limit),
            model_source=source,
            source_error=source_error,
            cache=cache if args.cache else None,
        )

        # Cache save — write updated results back.
        if args.cache:
            for audit in report.models:
                cache[audit.model] = {
                    "best_transport": audit.best_transport,
                    "best_status": audit.best_status,
                    "openai_status": audit.openai.status if audit.openai else "not_tested",
                    "sdk_status": audit.sdk.status if audit.sdk else "not_tested",
                }
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(cache, indent=2) + "\n", encoding="utf-8")

        if args.emit_mailbox:
            write_registry_mailbox(report, mailboxes)

        if args.json:
            print(json.dumps(asdict(report), ensure_ascii=True))
        else:
            print(f"registry_account={report.account} models={report.total_models}")
            print(f"best_status_counts={report.counts_by_best_status}")
            if report.cheapest_callable:
                print("cheapest_callable=")
                for candidate in report.cheapest_callable[:10]:
                    print(f"- {candidate.model} via {candidate.transport} ({candidate.cost_tier})")
            else:
                print("cheapest_callable=none")
        return 0

    accounts = parse_accounts(args.accounts)
    results: list[AccountAudit] = []
    for account in accounts:
        openai_control = probe_openai(
            account=account,
            model=args.control_model,
            prompt=args.prompt,
            effort=args.openai_effort,
            max_tokens=max(1, int(args.openai_max_tokens)),
        )
        openai_app = probe_openai(
            account=account,
            model=args.target_bot,
            prompt=args.prompt,
            effort=args.target_effort,
            max_tokens=max(1, int(args.openai_max_tokens)),
        )
        sdk_control = probe_sdk(account=account, bot=args.control_model, prompt=args.prompt, effort=args.sdk_effort)
        sdk_app = probe_sdk(account=account, bot=args.target_bot, prompt=args.prompt, effort=args.target_effort)
        models_count, has_app_creator = inspect_openai_models(account=account, limit=max(1, int(args.models_limit)))
        results.append(
            AccountAudit(
                account=account,
                openai_control=openai_control,
                openai_app_creator=openai_app,
                sdk_control=sdk_control,
                sdk_app_creator=sdk_app,
                openai_models_count=models_count,
                openai_has_app_creator=has_app_creator,
            )
        )

    report = TransportAudit(
        schema_version=1,
        generated_on=now_utc(),
        control_model=args.control_model,
        target_bot=args.target_bot,
        openai_max_tokens=max(1, int(args.openai_max_tokens)),
        accounts=results,
        recommendation="",
        rationale="",
    )
    recommendation, rationale = choose_recommendation(report)
    report.recommendation = recommendation
    report.rationale = rationale

    if args.emit_mailbox:
        write_mailbox(report, mailboxes)

    if args.json:
        print(json.dumps(asdict(report), ensure_ascii=True))
    else:
        print(f"recommendation={report.recommendation}")
        print(f"rationale={report.rationale}")
        for acc in report.accounts:
            print(
                "account="
                + acc.account
                + f" openai_control={acc.openai_control.status}"
                + f" openai_app_creator={acc.openai_app_creator.status}"
                + f" sdk_control={acc.sdk_control.status}"
                + f" sdk_app_creator={acc.sdk_app_creator.status}"
                + f" models_has_app_creator={acc.openai_has_app_creator}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
