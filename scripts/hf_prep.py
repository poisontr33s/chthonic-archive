#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: hf_prep.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
HF Prep (uv + Python 3.13) - deterministic environment readiness.

This script is the "prep-step" you can run before any Hugging Face workflow:
  - verifies uv + python runtime
  - verifies HF auth env presence (no secrets printed)
  - verifies required Python deps are importable
  - optionally installs missing deps via `uv pip install` (apply mode)
  - checks for Rust-backed accelerators (tokenizers, safetensors)

Artifacts:
  - codex/mailbox/HF_PREP_LATEST.json
  - codex/mailbox/HF_PREP_LATEST.md

@SID:           TOOL_HF_PREP_V1
@Shabti:        CLI Script
@Purpose:       HF Prep (uv + Python 3.13) - deterministic environment readiness.
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from importlib import metadata


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def now_utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def run_cmd(cmd: list[str]) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
        out = (p.stdout or "").strip()
        err = (p.stderr or "").strip()
        tail = "\n".join([x for x in [out, err] if x])
        return p.returncode, tail
    except Exception as e:
        return 1, str(e)


def has_env(name: str) -> bool:
    v = os.getenv(name)
    return bool(v and v.strip())


def get_version(dist_name: str) -> str | None:
    try:
        return metadata.version(dist_name)
    except Exception:
        return None


def is_importable(module: str) -> bool:
    try:
        __import__(module)
        return True
    except Exception:
        return False


def uv_install(req: str) -> tuple[int, str]:
    return run_cmd(["uv", "pip", "install", req])


@dataclass
class Check:
    name: str
    ok: bool
    detail: str = ""
    notes: list[str] = field(default_factory=list)


@dataclass
class Report:
    schema_version: int
    generated_on: str
    apply: bool
    platform: dict
    auth_signals: dict
    checks: list[Check]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Install missing deps via `uv pip install`.")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when any check fails. Default is non-strict (always exits 0 after writing artifacts).",
    )
    ap.add_argument(
        "--with",
        dest="with_extras",
        default="",
        help="Comma-separated optional bundles: transformers,datasets,accelerate,diffusers (checked/installed when present).",
    )
    args = ap.parse_args()

    opt = {x.strip().lower() for x in (args.with_extras or "").split(",") if x.strip()}

    # Minimal baseline for this repo's HF workflows.
    required: list[tuple[str, str]] = [
        ("huggingface-hub", "huggingface_hub"),
        ("mcp", "mcp"),
        ("pydantic-settings", "pydantic_settings"),
        ("requests", "requests"),
    ]

    # Optional HF stacks.
    if "transformers" in opt:
        required.append(("transformers", "transformers"))
        required.append(("tokenizers", "tokenizers"))  # Rust-backed accel
        required.append(("safetensors", "safetensors"))  # Rust-backed accel
    if "datasets" in opt:
        required.append(("datasets", "datasets"))
    if "accelerate" in opt:
        required.append(("accelerate", "accelerate"))
    if "diffusers" in opt:
        required.append(("diffusers", "diffusers"))

    checks: list[Check] = []

    # uv presence
    uv_path = shutil.which("uv")
    if uv_path:
        rc, out = run_cmd(["uv", "--version"])
        checks.append(Check(name="uv", ok=(rc == 0), detail=out or uv_path))
    else:
        checks.append(Check(name="uv", ok=False, detail="uv not found on PATH"))

    # python runtime
    checks.append(Check(name="python", ok=True, detail=sys.version.splitlines()[0]))

    # auth signals (no secrets)
    auth = {
        "HF_TOKEN": has_env("HF_TOKEN"),
        "HUGGINGFACE_HUB_TOKEN": has_env("HUGGINGFACE_HUB_TOKEN"),
    }
    checks.append(
        Check(
            name="hf_auth_env",
            ok=bool(auth["HF_TOKEN"] or auth["HUGGINGFACE_HUB_TOKEN"]),
            detail="env present" if (auth["HF_TOKEN"] or auth["HUGGINGFACE_HUB_TOKEN"]) else "missing HF_TOKEN/HUGGINGFACE_HUB_TOKEN",
            notes=["recommended: pwsh -NoProfile -File .codex/skills/api-manager/scripts/api_manager.ps1 -Load"],
        )
    )

    # deps
    for dist, mod in required:
        ver = get_version(dist)
        ok = is_importable(mod)
        detail = f"{dist}={ver}" if ver else f"{dist} (not installed)"
        c = Check(name=f"dep:{dist}", ok=ok and ver is not None, detail=detail)
        if not c.ok and args.apply:
            irc, iout = uv_install(dist)
            if irc == 0:
                ver2 = get_version(dist)
                ok2 = is_importable(mod)
                c.ok = bool(ok2 and ver2)
                c.detail = f"{dist}={ver2}"
                c.notes.append("installed_by_uv")
            else:
                c.notes.append(f"install_failed:{iout[:200]}")
        checks.append(c)

    report = Report(
        schema_version=1,
        generated_on=now_utc(),
        apply=bool(args.apply),
        platform={
            "system": platform.system(),
            "release": platform.release(),
            "python": sys.version.splitlines()[0],
        },
        auth_signals=auth,
        checks=checks,
    )

    out_dir = os.path.join(REPO_ROOT, "codex", "mailbox")
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "HF_PREP_LATEST.json")
    md_path = os.path.join(out_dir, "HF_PREP_LATEST.md")

    with open(json_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(asdict(report), f, indent=2)
        f.write("\n")

    # human-readable
    lines: list[str] = []
    lines.append("# HF Prep (uv + Python 3.13)")
    lines.append("")
    lines.append(f"- Generated: `{report.generated_on}`")
    lines.append(f"- Apply: `{report.apply}`")
    lines.append(f"- Python: `{report.platform['python']}`")
    lines.append(f"- HF_TOKEN present: `{report.auth_signals['HF_TOKEN']}`")
    lines.append(f"- HUGGINGFACE_HUB_TOKEN present: `{report.auth_signals['HUGGINGFACE_HUB_TOKEN']}`")
    lines.append("")
    for c in report.checks:
        status = "OK" if c.ok else "FAIL"
        lines.append(f"- `{status}` `{c.name}`: {c.detail}")
        for n in c.notes:
            lines.append(f"  - {n}")

    with open(md_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines).rstrip() + "\n")

    # Default behavior: never fail the lane; encode failures in artifacts.
    # Use --strict when you explicitly want a non-zero exit.
    if args.strict:
        return 0 if all(c.ok for c in checks) else 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
