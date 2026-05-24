#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: chthonic_new.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Chthonic project creation lane.

Uses the native project-init commands of the current polyglot stack rather than
inventing scaffolds from scratch.

Primary command references:
- uv init --help
- bun init --help
- cargo new --help
- go help mod init
- bundle gem --help
- Microsoft Learn azd template docs (`azd init --template ...`)

@SID:           TOOL_CHTHONIC_NEW_V1
@Purpose:       Scaffold new projects across the current polyglot lanes.
"""

from __future__ import annotations


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import argparse
import json
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
HOME = Path.home()


def which_or_fallback(name: str, fallback: str) -> str:
    return shutil.which(name) or fallback


UV = which_or_fallback("uv", str(HOME / ".local" / "bin" / "uv.exe"))
BUN = which_or_fallback("bun", str(HOME / ".bun" / "bin" / "bun.exe"))
CARGO = which_or_fallback("cargo", str(HOME / ".cargo" / "bin" / "cargo.exe"))
GO = which_or_fallback("go", str(HOME / ".goup" / "current" / "bin" / "go.exe"))
BUNDLE = which_or_fallback("bundle", str(HOME / ".cargo" / "bin" / "rv.exe"))
AZD = shutil.which("azd")


@dataclass
class Profile:
    id: str
    description: str
    docs: list[str]


PROFILES = {
    "uv-python-app": Profile(
        id="uv-python-app",
        description="Python application via uv init --app --package",
        docs=["uv init --help", "https://docs.astral.sh/uv/"],
    ),
    "uv-python-lib": Profile(
        id="uv-python-lib",
        description="Python library via uv init --lib --package",
        docs=["uv init --help", "https://docs.astral.sh/uv/"],
    ),
    "bun-react": Profile(
        id="bun-react",
        description="React app via bun init --react",
        docs=["bun init --help", "https://bun.sh/docs"],
    ),
    "bun-react-tailwind": Profile(
        id="bun-react-tailwind",
        description="React + Tailwind app via bun init --react=tailwind",
        docs=["bun init --help", "https://bun.sh/docs"],
    ),
    "bun-next": Profile(
        id="bun-next",
        description="Next.js app via bun create next-app",
        docs=["https://nextjs.org/docs/app/getting-started/installation", "https://bun.sh/docs"],
    ),
    "cargo-rust-bin": Profile(
        id="cargo-rust-bin",
        description="Rust binary crate via cargo new --bin",
        docs=["cargo new --help", "https://doc.rust-lang.org/cargo/"],
    ),
    "cargo-rust-lib": Profile(
        id="cargo-rust-lib",
        description="Rust library crate via cargo new --lib",
        docs=["cargo new --help", "https://doc.rust-lang.org/cargo/"],
    ),
    "go-basic": Profile(
        id="go-basic",
        description="Go module with a minimal main.go",
        docs=["go help mod init", "https://go.dev/doc/"],
    ),
    "ruby-gem": Profile(
        id="ruby-gem",
        description="Ruby gem via bundle gem",
        docs=["bundle gem --help", "https://bundler.io/"],
    ),
    "azure-azd-template": Profile(
        id="azure-azd-template",
        description="Azure Developer CLI template init via azd init --template",
        docs=[
            "https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/azd-templates",
            "https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/full-stack-templates",
        ],
    ),
}


def run(command: list[str], cwd: Path | None = None, dry_run: bool = False) -> tuple[int, str, str]:
    if dry_run:
        return 0, "DRY_RUN: " + " ".join(command), ""
    proc = subprocess.run(
        command,
        cwd=str(cwd or REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, proc.stdout, proc.stderr


def ensure_parent(path: Path, dry_run: bool) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)


def scaffold_go_basic(dest: Path, module: str | None, dry_run: bool) -> tuple[int, list[dict]]:
    steps: list[dict] = []
    if not dry_run:
        dest.mkdir(parents=True, exist_ok=True)
    go_mod_cmd = [GO, "mod", "init", module or dest.name]
    code, stdout, stderr = run(go_mod_cmd, cwd=dest, dry_run=dry_run)
    steps.append({"command": go_mod_cmd, "exit_code": code, "stdout": stdout, "stderr": stderr})
    if code != 0:
        return code, steps

    main_go = dest / "main.go"
    if dry_run:
        steps.append({"command": ["write", str(main_go)], "exit_code": 0, "stdout": 'package main\\n\\nimport "fmt"\\n\\nfunc main() {\\n\\tfmt.Println("hello from chthonic")\\n}\\n', "stderr": ""})
        return 0, steps

    main_go.write_text(
        'package main\n\nimport "fmt"\n\nfunc main() {\n\tfmt.Println("hello from chthonic")\n}\n',
        encoding="utf-8",
    )
    return 0, steps


def execute_profile(profile: str, dest: Path, module: str | None, dry_run: bool) -> dict:
    steps: list[dict] = []

    if profile == "uv-python-app":
        cmd = [UV, "init", str(dest), "--app", "--package", "--vcs", "git", "--build-backend", "uv"]
        code, stdout, stderr = run(cmd, dry_run=dry_run)
        steps.append({"command": cmd, "exit_code": code, "stdout": stdout, "stderr": stderr})
    elif profile == "uv-python-lib":
        cmd = [UV, "init", str(dest), "--lib", "--package", "--vcs", "git", "--build-backend", "uv"]
        code, stdout, stderr = run(cmd, dry_run=dry_run)
        steps.append({"command": cmd, "exit_code": code, "stdout": stdout, "stderr": stderr})
    elif profile == "bun-react":
        cmd = [BUN, "init", "--yes", "--react", str(dest)]
        code, stdout, stderr = run(cmd, dry_run=dry_run)
        steps.append({"command": cmd, "exit_code": code, "stdout": stdout, "stderr": stderr})
    elif profile == "bun-react-tailwind":
        cmd = [BUN, "init", "--yes", "--react=tailwind", str(dest)]
        code, stdout, stderr = run(cmd, dry_run=dry_run)
        steps.append({"command": cmd, "exit_code": code, "stdout": stdout, "stderr": stderr})
    elif profile == "bun-next":
        cmd = [BUN, "create", "next-app", str(dest), "--yes"]
        code, stdout, stderr = run(cmd, dry_run=dry_run)
        steps.append({"command": cmd, "exit_code": code, "stdout": stdout, "stderr": stderr})
    elif profile == "cargo-rust-bin":
        cmd = [CARGO, "new", "--bin", str(dest)]
        code, stdout, stderr = run(cmd, dry_run=dry_run)
        steps.append({"command": cmd, "exit_code": code, "stdout": stdout, "stderr": stderr})
    elif profile == "cargo-rust-lib":
        cmd = [CARGO, "new", "--lib", str(dest)]
        code, stdout, stderr = run(cmd, dry_run=dry_run)
        steps.append({"command": cmd, "exit_code": code, "stdout": stdout, "stderr": stderr})
    elif profile == "go-basic":
        code, steps = scaffold_go_basic(dest, module, dry_run=dry_run)
    elif profile == "ruby-gem":
        cmd = [
            BUNDLE,
            "gem",
            dest.name,
            "--test=minitest",
            "--no-coc",
            "--no-mit",
            "--no-ci",
            "--no-linter",
            "--no-changelog",
        ]
        code, stdout, stderr = run(cmd, cwd=dest.parent, dry_run=dry_run)
        steps.append({"command": cmd, "exit_code": code, "stdout": stdout, "stderr": stderr})
    elif profile == "azure-azd-template":
        if not AZD:
            code = 1
            steps.append({
                "command": ["azd", "init", "--template", module or "hello-azd"],
                "exit_code": 1,
                "stdout": "",
                "stderr": "azd is not installed on this machine. Install Azure Developer CLI first.",
            })
        else:
            if not dry_run:
                dest.mkdir(parents=True, exist_ok=True)
            cmd = [AZD, "init", "--template", module or "hello-azd"]
            code, stdout, stderr = run(cmd, cwd=dest, dry_run=dry_run)
            steps.append({"command": cmd, "exit_code": code, "stdout": stdout, "stderr": stderr})
    else:
        raise ValueError(f"Unknown profile: {profile}")

    return {
        "profile": profile,
        "destination": str(dest),
        "docs": PROFILES[profile].docs,
        "steps": steps,
        "errors": [
            {"command": s["command"], "exit_code": s["exit_code"], "stderr": s["stderr"]}
            for s in steps if s["exit_code"] != 0
        ],
        "ok": all(step["exit_code"] == 0 for step in steps),
    }


def main() -> int:
    # =============================================================================
    # Verify scaffold expectations per profile
    # =============================================================================

    VERIFY_CHECKS: dict[str, list[str]] = {
        "uv-python-app": ["pyproject.toml"],
        "uv-python-lib": ["pyproject.toml", "src"],
        "bun-react": ["package.json"],
        "bun-react-tailwind": ["package.json"],
        "bun-next": ["package.json"],
        "cargo-rust-bin": ["Cargo.toml", "src/main.rs"],
        "cargo-rust-lib": ["Cargo.toml", "src/lib.rs"],
        "go-basic": ["go.mod", "main.go"],
        "ruby-gem": ["Gemfile"],
        "azure-azd-template": ["azure.yaml"],
    }

    def verify_scaffold(profile: str, dest: Path) -> dict:
        checks = VERIFY_CHECKS.get(profile, [])
        missing = [p for p in checks if not (dest / p).exists()]
        return {"ok": not missing, "missing": missing, "checked": checks}

    parser = argparse.ArgumentParser(description="Scaffold new projects for the Chthonic polyglot stack.")
    parser.add_argument("profile", choices=sorted(PROFILES.keys()))
    parser.add_argument("destination")
    parser.add_argument("--module", help="Optional module/template name (used by Go/Azure profiles).")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verify", action="store_true", help="After scaffold, verify expected files exist.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--list", action="store_true", help="List profiles and exit.")
    args = parser.parse_args()

    if args.list:
        payload = {key: asdict(value) for key, value in PROFILES.items()}
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    dest = Path(args.destination)
    if not dest.is_absolute():
        dest = (REPO_ROOT / dest).resolve()

    result = execute_profile(args.profile, dest, args.module, args.dry_run)

    if args.verify and not args.dry_run:
        result["verify"] = verify_scaffold(args.profile, dest)
        if not result["verify"]["ok"]:
            result["ok"] = False

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
