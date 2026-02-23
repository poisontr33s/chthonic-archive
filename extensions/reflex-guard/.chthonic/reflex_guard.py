#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Iterable


def run_git(args: list[str], repo_root: Path) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return ""
    return proc.stdout


def get_staged_files(repo_root: Path) -> list[str]:
    out = run_git(["diff", "--cached", "--name-only"], repo_root)
    return [line.strip() for line in out.splitlines() if line.strip()]


def parse_dependencies(toml_text: str) -> set[str]:
    try:
        data = tomllib.loads(toml_text)
    except Exception:
        return set()

    deps: set[str] = set()
    top_level_tables = ("dependencies", "dev-dependencies", "build-dependencies")
    for table in top_level_tables:
        value = data.get(table)
        if isinstance(value, dict):
            deps.update(str(k) for k in value.keys())

    workspace = data.get("workspace")
    if isinstance(workspace, dict):
        ws_deps = workspace.get("dependencies")
        if isinstance(ws_deps, dict):
            deps.update(str(k) for k in ws_deps.keys())

    return deps


def parse_staged_toml(repo_root: Path, rel_path: str) -> set[str]:
    staged_text = run_git(["show", f":{rel_path}"], repo_root)
    if not staged_text:
        return set()
    return parse_dependencies(staged_text)


def parse_head_toml(repo_root: Path, rel_path: str) -> set[str]:
    head_text = run_git(["show", f"HEAD:{rel_path}"], repo_root)
    if not head_text:
        return set()
    return parse_dependencies(head_text)


def load_whitelist(repo_root: Path) -> set[str]:
    whitelist_path = repo_root / "extensions" / "reflex-guard" / "whitelist.json"
    if not whitelist_path.exists():
        return set()
    try:
        payload = json.loads(whitelist_path.read_text(encoding="utf-8"))
    except Exception:
        return set()

    allowed = payload.get("allowed_crates", [])
    if not isinstance(allowed, list):
        return set()
    return {str(crate).strip() for crate in allowed if str(crate).strip()}


def format_csv(items: Iterable[str]) -> str:
    return ", ".join(sorted(items))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reflex Guard - staged Cargo dependency change detector"
    )
    parser.add_argument(
        "--staged",
        action="store_true",
        help="Inspect staged diff (default behavior).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if new crates are not in whitelist.json",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[3]
    staged_files = get_staged_files(repo_root)
    cargo_files = [p for p in staged_files if p.endswith("Cargo.toml")]

    if not cargo_files:
        print("[REFLEX-GUARD] No staged Cargo.toml changes detected.")
        return 0

    whitelist = load_whitelist(repo_root)
    unknown_accumulator: set[str] = set()

    for rel_path in cargo_files:
        staged_deps = parse_staged_toml(repo_root, rel_path)
        head_deps = parse_head_toml(repo_root, rel_path)
        added = staged_deps - head_deps

        if added:
            print(
                f"[REFLEX-GUARD] Dependency Change Detected in {rel_path}: {format_csv(added)}"
            )
            unknown = {crate for crate in added if crate not in whitelist}
            if unknown:
                unknown_accumulator.update(unknown)
                print(
                    f"[REFLEX-GUARD] Non-whitelisted crates: {format_csv(unknown)}"
                )
        else:
            print(
                f"[REFLEX-GUARD] Cargo.toml changed with no new dependency additions: {rel_path}"
            )

    if args.strict and unknown_accumulator:
        print(
            "[REFLEX-GUARD] STRICT MODE BLOCK: unknown crates found -> "
            f"{format_csv(unknown_accumulator)}"
        )
        return 1

    print("[REFLEX-GUARD] Check complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

