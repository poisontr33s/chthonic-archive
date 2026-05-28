#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: toolchain_doctor.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🔥 THE FOUNDRY
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""Bun + uv toolchain doctor.

KISS goals:
- Run `bun audit --json` and summarize vulnerabilities.
- Identify likely remediation options.
- Optionally apply conservative fixes.

Policy:
- Use `uv run <script.py>` (caller responsibility).
- Never use cmd.exe wrappers.
- Never write secrets.

@SID:           TOOL_TOOLCHAIN_DOCTOR_V1
@Shabti:        CLI Script
@Purpose:       Bun + uv toolchain doctor.
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


def find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for p in [cur, *cur.parents]:
        if (p / "pyproject.toml").exists() and (p / "AGENTS.md").exists():
            return p
    # Fallback: assume 3 parents up (historical layout), but this should not happen in-repo.
    return start.resolve().parents[3]


REPO_ROOT = find_repo_root(Path(__file__))
CODEX_MAILBOX = REPO_ROOT / "codex" / "mailbox"


@dataclass(frozen=True)
class AuditFinding:
    package: str
    severity: str
    title: str
    url: str


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y_%m_%d_%H%M%S")


def run(cmd: list[str], *, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=REPO_ROOT, check=check, capture_output=True, text=True)


def load_package_json() -> dict[str, Any]:
    path = REPO_ROOT / "package.json"
    return json.loads(path.read_text(encoding="utf-8"))


def write_package_json(obj: dict[str, Any]) -> None:
    path = REPO_ROOT / "package.json"
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def rg_hits(pattern: str) -> int:
    # Exclude files where package names are expected to appear.
    cmd = [
        "rg",
        "-n",
        pattern,
        ".",
        "--hidden",
        "--glob",
        "!**/node_modules/**",
        "--glob",
        "!**/.git/**",
        "--glob",
        "!bun.lock",
        "--glob",
        "!package.json",
        "--glob",
        "!**/package-lock.json",
        "--glob",
        "!**/pnpm-lock.yaml",
        "--glob",
        "!**/yarn.lock",
    ]
    proc = run(cmd)
    if proc.returncode == 0:
        return len(proc.stdout.splitlines())
    return 0


def bun_audit_json() -> tuple[list[AuditFinding], dict[str, Any]]:
    proc = run(["bun", "audit", "--json"])
    if proc.returncode not in (0, 1):
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip())

    payload = json.loads(proc.stdout)
    findings: list[AuditFinding] = []

    # bun audit --json structure may evolve; scan generically for advisories.
    advisories = payload.get("advisories")
    if isinstance(advisories, dict):
        for pkg, items in advisories.items():
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                findings.append(
                    AuditFinding(
                        package=str(pkg),
                        severity=str(item.get("severity", "unknown")),
                        title=str(item.get("title", "")),
                        url=str(item.get("url", "")),
                    )
                )

    # Fallback: some formats have "vulnerabilities" list.
    vulns = payload.get("vulnerabilities")
    if isinstance(vulns, list) and not findings:
        for v in vulns:
            if not isinstance(v, dict):
                continue
            findings.append(
                AuditFinding(
                    package=str(v.get("name", "unknown")),
                    severity=str(v.get("severity", "unknown")),
                    title=str(v.get("title", "")),
                    url=str(v.get("url", "")),
                )
            )

    return findings, payload


def bun_why(pkg: str) -> str:
    proc = run(["bun", "why", pkg])
    return (proc.stdout or proc.stderr).strip()


def bun_update(pkg: str) -> str:
    proc = run(["bun", "update", pkg])
    return (proc.stdout + "\n" + proc.stderr).strip()


def bun_install() -> str:
    proc = run(["bun", "install"])
    return (proc.stdout + "\n" + proc.stderr).strip()


def uv_sync() -> str:
    proc = run(["uv", "sync"])
    return (proc.stdout + "\n" + proc.stderr).strip()


def uv_probe_imports() -> list[tuple[str, bool, str]]:
    probes = ["idna", "huggingface_hub"]
    out: list[tuple[str, bool, str]] = []
    for mod in probes:
        proc = run(["uv", "run", "python", "-c", f"import {mod}; print('{mod} ok')"])
        ok = proc.returncode == 0
        msg = (proc.stdout or proc.stderr).strip()
        out.append((mod, ok, msg))
    return out


def hf_auth_status() -> tuple[bool, str]:
    """
    Returns (ok, details) without ever printing secrets.
    Preference order:
    - HUGGINGFACE_HUB_TOKEN env var
    - huggingface_hub cached token (from `huggingface-cli login`)
    """
    code = r"""
from __future__ import annotations
from huggingface_hub import HfApi
try:
    # huggingface_hub exposes a stable helper in newer versions.
    from huggingface_hub.utils import get_token
except Exception:
    get_token = None

tok = None
if get_token:
    try:
        tok = get_token()
    except Exception:
        tok = None

api = HfApi()
try:
    who = api.whoami(token=tok) if tok else api.whoami()
    # Print only non-secret identifiers.
    print("ok", who.get("name") or who.get("email") or "unknown")
except Exception as e:
    print("fail", type(e).__name__, str(e)[:200])
"""
    proc = run(["uv", "run", "python", "-c", code])
    out = (proc.stdout or proc.stderr).strip()
    if out.startswith("ok "):
        return True, out
    return False, out or "fail"


def apply_safe_bun_fixes(findings: list[AuditFinding]) -> list[str]:
    changes: list[str] = []

    pkg_json = load_package_json()
    deps = pkg_json.get("dependencies", {}) or {}
    dev = pkg_json.get("devDependencies", {}) or {}

    # 1) If a vulnerable package is a direct dependency, try bun update <pkg>.
    direct = set(deps.keys()) | set(dev.keys())
    for f in findings:
        if f.package in direct:
            changes.append(f"bun update {f.package}")
            bun_update(f.package)

    # 2) Remove problematic dev deps only if unused (no rg hits outside manifests/lockfiles).
    remove_if_unused = {
        "@modelcontextprotocol/server-filesystem",
        "@modelcontextprotocol/server-github",
        "node-gyp",
    }

    removed_any = False
    for name in sorted(remove_if_unused):
        if name not in dev:
            continue
        hits = rg_hits(re.escape(name))
        if hits != 0:
            continue
        dev.pop(name, None)
        removed_any = True
        changes.append(f"remove devDependency {name} (unused)")

    if removed_any:
        pkg_json["devDependencies"] = dev
        write_package_json(pkg_json)

    # Always run bun install if we changed anything.
    if changes:
        bun_install()

    return changes


def write_report(*, bun: bool, uv: bool, apply: bool) -> Path:
    CODEX_MAILBOX.mkdir(parents=True, exist_ok=True)

    stamp = utc_stamp()
    report_path = CODEX_MAILBOX / f"TOOLCHAIN_DOCTOR_REPORT_{stamp}.md"
    latest_path = CODEX_MAILBOX / "TOOLCHAIN_DOCTOR_LATEST.md"

    lines: list[str] = []
    lines.append("# Toolchain Doctor Report")
    lines.append("")
    lines.append(f"- Generated: `{datetime.now(timezone.utc).isoformat()}`")
    lines.append(f"- bun: `{bun}`")
    lines.append(f"- uv: `{uv}`")
    lines.append(f"- apply: `{apply}`")
    lines.append("")

    if bun:
        lines.append("## Bun")
        lines.append("")
        findings, _raw = bun_audit_json()
        if not findings:
            lines.append("- Audit: PASS (no vulnerabilities)")
        else:
            lines.append(f"- Audit: FAIL (`{len(findings)}` finding(s))")
            for f in findings:
                lines.append(f"- `{f.package}` `{f.severity}` {f.title} ({f.url})")
                why = bun_why(f.package)
                if why:
                    lines.append("```text")
                    lines.append(why)
                    lines.append("```")

        if apply and findings:
            lines.append("### Apply (Safe)")
            lines.append("")
            changes = apply_safe_bun_fixes(findings)
            if not changes:
                lines.append("- No safe changes applied.")
            else:
                for c in changes:
                    lines.append(f"- {c}")

            # Re-audit.
            post, _ = bun_audit_json()
            lines.append("")
            lines.append(f"- Post-audit findings: `{len(post)}`")

        lines.append("")

    if uv:
        lines.append("## uv")
        lines.append("")
        try:
            out = uv_sync()
            lines.append("- uv sync: executed")
            if out.strip():
                lines.append("```text")
                lines.append(out.strip())
                lines.append("```")
        except Exception as e:
            lines.append(f"- uv sync: FAILED: `{e}`")

        probes = uv_probe_imports()
        lines.append("")
        lines.append("### Import Probes")
        for mod, ok, msg in probes:
            lines.append(f"- `{mod}`: `{ok}`")
            if msg:
                lines.append("```text")
                lines.append(msg)
                lines.append("```")

        lines.append("")
        lines.append("### Hugging Face Auth Probe")
        ok, detail = hf_auth_status()
        lines.append(f"- auth: `{ok}`")
        if detail:
            lines.append("```text")
            lines.append(detail)
            lines.append("```")
        lines.append("")
        lines.append("### Auth Policy")
        lines.append("- Prefer `huggingface-cli login` for durable auth (cached outside VS Code).")
        lines.append("- If using env vars, set a user-level `HUGGINGFACE_HUB_TOKEN` (avoid session-only).")
        lines.append("")

        lines.append("")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    latest = []
    latest.append("# Toolchain Doctor (Latest)")
    latest.append("")
    latest.append(f"- Latest report: `{report_path.name}`")
    latest.append("")
    latest.append("## Quick Links")
    latest.append(f"- `{report_path.as_posix()}`")
    latest_path.write_text("\n".join(latest) + "\n", encoding="utf-8")

    return report_path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bun", action="store_true", help="Run bun health checks")
    ap.add_argument("--uv", action="store_true", help="Run uv health checks")
    ap.add_argument("--apply", action="store_true", help="Apply safe fixes")
    args = ap.parse_args()

    if not args.bun and not args.uv:
        args.bun = True
        args.uv = True

    path = write_report(bun=args.bun, uv=args.uv, apply=args.apply)
    print(f"Wrote: {path}")


if __name__ == "__main__":
    main()
