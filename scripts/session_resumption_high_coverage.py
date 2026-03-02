#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: session_resumption_high_coverage.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Session Resumption High Coverage (Claude-side Stewardship)

Builds a continuation packet from Claude mailbox + nightly daemon artifacts,
adds LocalAI runtime/model status, and overlays live signals from:
- Hugging Face model API (uncensored/abliterated momentum)
- endoflife.date API (toolchain freshness pressure)

Usage:
  uv run scripts/session_resumption_high_coverage.py
  uv run scripts/session_resumption_high_coverage.py --quiet
  uv run scripts/session_resumption_high_coverage.py --out path/to/report.md

@SID:           TOOL_SESSION_RESUMPTION_HIGH_COVERAGE_V1
@Shabti:        CLI Script
@Purpose:       Session Resumption High Coverage (Claude-side Stewardship)
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


REPO_ROOT = Path(__file__).resolve().parent.parent
SESSION_DIR = REPO_ROOT / "claude-codex-gemini" / "session_resumption_pickup"
MAILBOX_DIR = REPO_ROOT / "claude" / "mailbox"
NIGHTLY_DIR = REPO_ROOT / "dumpster-dive" / "intake" / "overnight-daemon"
ARCH_DIR = REPO_ROOT / "dumpster-dive" / "intake" / "overnight-intelligence"
MODELS_DIR = REPO_ROOT / "models"


@dataclass
class Check:
    name: str
    ok: bool
    detail: str


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def latest_path(glob_pattern: str, *, want_dir: bool | None = None) -> Path | None:
    candidates = sorted(
        REPO_ROOT.glob(glob_pattern),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for path in candidates:
        if want_dir is True and not path.is_dir():
            continue
        if want_dir is False and not path.is_file():
            continue
        return path
    return None


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(read_text(path))


def run_cmd(cmd: list[str]) -> tuple[bool, str]:
    try:
        cp = subprocess.run(
            cmd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
    except OSError as exc:
        return False, str(exc)

    out = (cp.stdout or "").strip()
    err = (cp.stderr or "").strip()
    if cp.returncode == 0:
        return True, out or err or "(ok)"
    return False, err or out or f"exit={cp.returncode}"


def fetch_json(url: str, timeout: float = 10.0) -> tuple[bool, Any]:
    req = Request(url, headers={"User-Agent": "chthonic-session-resumer/1.0"})
    try:
        with urlopen(req, timeout=timeout) as response:
            payload = response.read().decode("utf-8", errors="replace")
        return True, json.loads(payload)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        return False, str(exc)


def nightly_health(log_path: Path | None) -> tuple[bool, list[str], bool]:
    if log_path is None or not log_path.exists():
        return False, ["missing nightly scheduler log"], False

    text = read_text(log_path)
    fatal_patterns = [
        r"Nightly run failed",
        r"Traceback",
        r"ModuleNotFoundError",
        r"failed with exit code",
        r"\bERROR:",
    ]
    hits: list[str] = []
    for pattern in fatal_patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            hits.append(pattern)

    completed = "☥ Nightly run complete." in text
    return len(hits) == 0 and completed, hits, completed


def model_inventory() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not MODELS_DIR.exists():
        return records

    uncensored_re = re.compile(r"(uncensored|abliterated|heretic|dark)", re.IGNORECASE)
    for model_dir in sorted([d for d in MODELS_DIR.iterdir() if d.is_dir()]):
        files = [p for p in model_dir.rglob("*") if p.is_file()]
        if not files:
            continue
        total_bytes = sum(p.stat().st_size for p in files)
        largest = max(files, key=lambda p: p.stat().st_size)
        gguf_files = [p for p in files if p.suffix.lower() == ".gguf"]
        safetensors_files = [p for p in files if p.suffix.lower() == ".safetensors"]
        records.append(
            {
                "name": model_dir.name,
                "file_count": len(files),
                "size_gb": round(total_bytes / (1024**3), 3),
                "largest_file": largest.name,
                "largest_gb": round(largest.stat().st_size / (1024**3), 3),
                "format": "gguf"
                if gguf_files
                else "safetensors/exl2"
                if safetensors_files
                else "mixed",
                "uncensored_signal": bool(uncensored_re.search(model_dir.name) or uncensored_re.search(largest.name)),
                "updated_at": datetime.fromtimestamp(model_dir.stat().st_mtime, tz=timezone.utc).isoformat(),
            }
        )
    return records


def module_version(import_name: str) -> str | None:
    try:
        module = __import__(import_name)
        return getattr(module, "__version__", "unknown")
    except Exception:
        return None


def hf_top(search: str, limit: int = 10) -> tuple[bool, list[dict[str, Any]] | str]:
    query = quote(search)
    url = (
        "https://huggingface.co/api/models"
        f"?search={query}&sort=downloads&direction=-1&limit={limit}&full=true"
    )
    ok, payload = fetch_json(url)
    if not ok:
        return False, payload
    assert isinstance(payload, list)
    rows: list[dict[str, Any]] = []
    for item in payload:
        rows.append(
            {
                "id": item.get("id", "unknown"),
                "downloads": int(item.get("downloads") or 0),
                "likes": int(item.get("likes") or 0),
                "lastModified": item.get("lastModified", "unknown"),
                "url": f"https://huggingface.co/{item.get('id', '')}",
            }
        )
    return True, rows


def eol_latest(product: str) -> tuple[bool, dict[str, Any] | str]:
    url = f"https://endoflife.date/api/v1/products/{quote(product)}/releases/latest"
    ok, payload = fetch_json(url)
    if not ok:
        return False, payload
    result = payload.get("result", {})
    latest = result.get("latest", {})
    row = {
        "product": product,
        "cycle": result.get("label") or result.get("name") or "unknown",
        "latest_patch": latest.get("name") or "unknown",
        "latest_patch_date": latest.get("date") or "unknown",
        "eol_from": result.get("eolFrom") or "unknown",
        "maintained": bool(result.get("isMaintained", False)),
        "url": url,
    }
    return True, row


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(row) + " |")
    return "\n".join(out)


def build_report() -> tuple[str, dict[str, Any]]:
    now = utc_now()

    latest_digest = latest_path("claude/mailbox/ARCHAEOLOGY_DIGEST_*.md", want_dir=False)
    latest_readiness_json = latest_path("claude/mailbox/LOCAL_AI_READINESS_LATEST.json", want_dir=False)
    latest_session_sync = latest_path("claude/mailbox/SESSION_SYNC_PACKET_*.md", want_dir=False)
    latest_mailbox_state = latest_path("claude/mailbox/MAILBOX_CURRENT_STATE.md", want_dir=False)
    latest_scheduler_log = latest_path("dumpster-dive/intake/overnight-daemon/nightly-scheduled-*.log", want_dir=False)
    latest_daemon_run = latest_path("dumpster-dive/intake/overnight-daemon/20*", want_dir=True)
    latest_arch_run = latest_path("dumpster-dive/intake/overnight-intelligence/arch-*", want_dir=True)
    session_log = latest_path(
        "claude-codex-gemini/session_resumption_pickup/session_resumption_pickup_codex.md",
        want_dir=False,
    )

    daemon_report_json = latest_daemon_run / "report.json" if latest_daemon_run else None
    arch_l1_ore = latest_arch_run / "L1-ore.json" if latest_arch_run else None
    nightly_ok, nightly_hits, nightly_completed = nightly_health(latest_scheduler_log)

    models = model_inventory()
    has_uncensored = any(m["uncensored_signal"] for m in models)
    has_qwen3_lane = any("Qwen3-30B-A3B-Instruct-abliterated" in m["name"] for m in models)

    numpy_ver = module_version("numpy")
    polars_ver = module_version("polars")
    llama_cpp_ver = module_version("llama_cpp")

    runtime_checks = {
        "uv": run_cmd(["uv", "--version"]),
        "bun": run_cmd(["bun", "--version"]),
        "pwsh": run_cmd(["pwsh", "--version"]),
    }

    hf_unc_ok, hf_unc = hf_top("uncensored", limit=12)
    hf_abl_ok, hf_abl = hf_top("abliterated", limit=12)

    eol_rows: list[dict[str, Any]] = []
    eol_errors: list[str] = []
    for product in ["python", "rust", "go", "nodejs", "bun"]:
        ok, payload = eol_latest(product)
        if ok:
            assert isinstance(payload, dict)
            eol_rows.append(payload)
        else:
            eol_errors.append(f"{product}: {payload}")

    checks = [
        Check("Claude digest exists", latest_digest is not None, str(latest_digest) if latest_digest else "missing"),
        Check(
            "Local AI readiness snapshot exists",
            latest_readiness_json is not None,
            str(latest_readiness_json) if latest_readiness_json else "missing",
        ),
        Check(
            "Nightly scheduler log exists",
            latest_scheduler_log is not None,
            str(latest_scheduler_log) if latest_scheduler_log else "missing",
        ),
        Check("Nightly scheduler log clean", nightly_ok, "clean" if nightly_ok else ", ".join(nightly_hits) or "not complete"),
        Check("Nightly completion marker present", nightly_completed, "complete marker found" if nightly_completed else "missing"),
        Check(
            "Daemon report exists",
            bool(daemon_report_json and daemon_report_json.exists()),
            str(daemon_report_json) if daemon_report_json else "missing",
        ),
        Check(
            "L1 ore exists",
            bool(arch_l1_ore and arch_l1_ore.exists()),
            str(arch_l1_ore) if arch_l1_ore else "missing",
        ),
        Check("Uncensored model lane present", has_uncensored, "detected" if has_uncensored else "none"),
        Check("Qwen3 abliterated lane present", has_qwen3_lane, "detected" if has_qwen3_lane else "missing"),
        Check("numpy 2.x functional", bool(numpy_ver and numpy_ver.startswith("2.")), numpy_ver or "missing"),
        Check("polars functional", polars_ver is not None, polars_ver or "missing"),
        Check("llama-cpp lane import", llama_cpp_ver is not None, llama_cpp_ver or "missing"),
    ]
    coverage = round((sum(1 for c in checks if c.ok) / len(checks)) * 100.0, 1)

    checkpoint_rows = [[c.name, "OK" if c.ok else "FAIL", c.detail] for c in checks]
    model_rows = [
        [
            m["name"],
            m["format"],
            str(m["file_count"]),
            f'{m["size_gb"]:.3f}',
            "yes" if m["uncensored_signal"] else "no",
            m["largest_file"],
        ]
        for m in models
    ]
    runtime_rows = [
        [name, "OK" if status else "FAIL", detail.splitlines()[0][:180]]
        for name, (status, detail) in runtime_checks.items()
    ]
    eol_table_rows = [
        [
            row["product"],
            str(row["cycle"]),
            str(row["latest_patch"]),
            str(row["latest_patch_date"]),
            str(row["eol_from"]),
            "yes" if row["maintained"] else "no",
        ]
        for row in eol_rows
    ]

    hf_unc_rows: list[list[str]] = []
    if hf_unc_ok:
        assert isinstance(hf_unc, list)
        hf_unc_rows = [
            [item["id"], str(item["downloads"]), str(item["likes"]), str(item["lastModified"])]
            for item in hf_unc[:8]
        ]
    hf_abl_rows: list[list[str]] = []
    if hf_abl_ok:
        assert isinstance(hf_abl, list)
        hf_abl_rows = [
            [item["id"], str(item["downloads"]), str(item["likes"]), str(item["lastModified"])]
            for item in hf_abl[:8]
        ]

    installed_name_blob = " ".join(m["name"].lower() for m in models)
    upgrade_candidates: list[dict[str, Any]] = []
    if hf_abl_ok:
        assert isinstance(hf_abl, list)
        for item in hf_abl:
            model_id = item["id"].lower()
            if "qwen3-coder-next-abliterated" in model_id and "coder-next" not in installed_name_blob:
                upgrade_candidates.append(item)
            if "openai-gpt-oss-20b" in model_id and "neoplus" not in installed_name_blob:
                upgrade_candidates.append(item)

    session_tail = ""
    if session_log and session_log.exists():
        lines = read_text(session_log).splitlines()
        tail = lines[-14:] if len(lines) > 14 else lines
        session_tail = "\n".join(tail)

    report_lines = [
        "---",
        "type: session-resumption-packet",
        "owner: codex",
        f"generated: {now.isoformat()}",
        "scope: claude-side continuation + localai stewardship",
        "---",
        "",
        "# Session Resumption High Coverage (Codex Stewardship)",
        "",
        f"- Coverage score: **{coverage}%**",
        f"- Generated (UTC): `{now.strftime('%Y-%m-%d %H:%M:%S')}`",
        "",
        "## Continuation Trail (Claude-side)",
        "",
        f"- Latest digest: `{latest_digest}`" if latest_digest else "- Latest digest: missing",
        f"- Latest local-AI readiness: `{latest_readiness_json}`" if latest_readiness_json else "- Latest local-AI readiness: missing",
        f"- Latest session sync packet: `{latest_session_sync}`" if latest_session_sync else "- Latest session sync packet: missing",
        f"- Mailbox state anchor: `{latest_mailbox_state}`" if latest_mailbox_state else "- Mailbox state anchor: missing",
        f"- Session log anchor: `{session_log}`" if session_log else "- Session log anchor: missing",
        "",
        "## Coverage Checks",
        "",
        markdown_table(["Check", "Status", "Detail"], checkpoint_rows),
        "",
        "## Nightly Daemon Status",
        "",
        f"- Latest scheduler log: `{latest_scheduler_log}`" if latest_scheduler_log else "- Latest scheduler log: missing",
        f"- Latest daemon run: `{latest_daemon_run}`" if latest_daemon_run else "- Latest daemon run: missing",
        f"- Latest archaeology run: `{latest_arch_run}`" if latest_arch_run else "- Latest archaeology run: missing",
        f"- Nightly clean: **{'yes' if nightly_ok else 'no'}**",
        "",
        "## LocalAI Runtime",
        "",
        markdown_table(["Tool", "Status", "Detail"], runtime_rows),
        "",
        f"- numpy: `{numpy_ver or 'missing'}`",
        f"- polars: `{polars_ver or 'missing'}`",
        f"- llama_cpp: `{llama_cpp_ver or 'missing'}`",
        "",
        "## Model Inventory (Installed)",
        "",
        markdown_table(
            ["Model", "Format", "Files", "Size(GB)", "Uncensored", "Largest file"],
            model_rows or [["(none)", "-", "-", "-", "-", "-"]],
        ),
        "",
        "## Live Uncensored Model Signals (Hugging Face API)",
        "",
    ]

    if hf_unc_ok:
        report_lines += [
            "### Search: `uncensored` (top by downloads)",
            "",
            markdown_table(["Model ID", "Downloads", "Likes", "Last Modified"], hf_unc_rows),
            "",
        ]
    else:
        report_lines += [f"- uncensored search failed: `{hf_unc}`", ""]

    if hf_abl_ok:
        report_lines += [
            "### Search: `abliterated` (top by downloads)",
            "",
            markdown_table(["Model ID", "Downloads", "Likes", "Last Modified"], hf_abl_rows),
            "",
        ]
    else:
        report_lines += [f"- abliterated search failed: `{hf_abl}`", ""]

    report_lines += [
        "## Anno Live Time (endoflife.date)",
        "",
        markdown_table(
            ["Product", "Cycle", "Latest Patch", "Patch Date", "EOL From", "Maintained"],
            eol_table_rows or [["(none)", "-", "-", "-", "-", "-"]],
        ),
        "",
    ]

    if eol_errors:
        report_lines += [
            "EOL lookup issues:",
            "",
            *[f"- `{err}`" for err in eol_errors],
            "",
        ]

    report_lines += [
        "## Continuation Actions (Immediate)",
        "",
        "1. Keep `Qwen3-30B-A3B-Instruct-abliterated` as primary local uncensored lane for nightly v2 refiner.",
        "2. Keep `Qwen3-Coder-30B-A3B-abliterated` as code-heavy fallback lane.",
        "3. Keep `GPT-OSS-20B-NEOPlus-Uncensored` as secondary uncensored checkpoint model.",
        "4. Use `uv run scripts/session_resumption_high_coverage.py` after major nightlies to refresh continuity packet.",
        "5. If a lane regresses, compare against this packet first, then reopen from Claude digest + nightly log pair.",
        "",
    ]

    if upgrade_candidates:
        rows = [
            [item["id"], str(item["downloads"]), str(item["likes"]), str(item["lastModified"])]
            for item in upgrade_candidates[:6]
        ]
        report_lines += [
            "## Live Upgrade Candidates (Not Installed Yet)",
            "",
            markdown_table(["Model ID", "Downloads", "Likes", "Last Modified"], rows),
            "",
        ]

    if session_tail:
        report_lines += [
            "## Session Log Tail (Raw Anchor)",
            "",
            "```text",
            session_tail,
            "```",
            "",
        ]

    report = "\n".join(report_lines).strip() + "\n"

    payload = {
        "generated": now.isoformat(),
        "coverage_percent": coverage,
        "checks": [c.__dict__ for c in checks],
        "paths": {
            "latest_digest": str(latest_digest) if latest_digest else None,
            "latest_readiness_json": str(latest_readiness_json) if latest_readiness_json else None,
            "latest_session_sync": str(latest_session_sync) if latest_session_sync else None,
            "latest_mailbox_state": str(latest_mailbox_state) if latest_mailbox_state else None,
            "latest_scheduler_log": str(latest_scheduler_log) if latest_scheduler_log else None,
            "latest_daemon_run": str(latest_daemon_run) if latest_daemon_run else None,
            "latest_arch_run": str(latest_arch_run) if latest_arch_run else None,
            "session_log": str(session_log) if session_log else None,
        },
        "models": models,
        "runtime": {
            "numpy": numpy_ver,
            "polars": polars_ver,
            "llama_cpp": llama_cpp_ver,
            "tools": {k: {"ok": v[0], "detail": v[1]} for k, v in runtime_checks.items()},
        },
        "huggingface": {
            "uncensored_ok": hf_unc_ok,
            "uncensored": hf_unc if hf_unc_ok else None,
            "abliterated_ok": hf_abl_ok,
            "abliterated": hf_abl if hf_abl_ok else None,
        },
        "endoflife": {
            "rows": eol_rows,
            "errors": eol_errors,
        },
    }

    return report, payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate high-coverage session resumption packet.")
    parser.add_argument("--out", help="Output markdown file path.")
    parser.add_argument("--json-out", help="Output JSON file path.")
    parser.add_argument(
        "--no-json",
        action="store_true",
        help="Write Markdown packet only (suppress JSON artifact).",
    )
    parser.add_argument(
        "--latest-only",
        action="store_true",
        help="Write only SESSION_RESUMPTION_HIGH_COVERAGE_LATEST.md (no timestamped .md).",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress console summary.")
    args = parser.parse_args()

    report_text, payload = build_report()
    stamp = utc_now().strftime("%Y%m%d_%H%M%S")
    SESSION_DIR.mkdir(parents=True, exist_ok=True)

    latest_path = SESSION_DIR / "SESSION_RESUMPTION_HIGH_COVERAGE_LATEST.md"
    if args.out:
        out_path = Path(args.out)
    elif args.latest_only:
        out_path = latest_path
    else:
        out_path = SESSION_DIR / f"SESSION_RESUMPTION_HIGH_COVERAGE_{stamp}.md"

    if out_path != latest_path:
        out_path.write_text(report_text, encoding="utf-8")
    latest_path.write_text(report_text, encoding="utf-8")

    json_path: Path | None = None
    if not args.no_json:
        json_path = Path(args.json_out) if args.json_out else SESSION_DIR / f"SESSION_RESUMPTION_HIGH_COVERAGE_{stamp}.json"
        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if not args.quiet:
        print(f"report_markdown={out_path}")
        print(f"report_latest={latest_path}")
        if json_path is not None:
            print(f"report_json={json_path}")
        print(f"coverage={payload['coverage_percent']}%")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
