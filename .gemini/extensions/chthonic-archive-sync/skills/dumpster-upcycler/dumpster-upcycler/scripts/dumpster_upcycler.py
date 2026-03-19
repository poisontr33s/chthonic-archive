#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: dumpster_upcycler.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🔥 THE FOUNDRY
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Dumpster Upcycler.

Purpose:
- Turn raw transcript/dump files into compact structured logs + readable markdown.
- Never delete; optionally archive originals into a dated folder.

Invocation:
  uv run .codex/skills/dumpster-upcycler/scripts/dumpster_upcycler.py <path>
  uv run .codex/skills/dumpster-upcycler/scripts/dumpster_upcycler.py <dir> --glob "<pattern>" [--archive]

@SID:           TOOL_DUMPSTER_UPCYCLER_V1
@Shabti:        CLI Script
@Purpose:       Dumpster Upcycler.
"""

from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


def utc_date_tag() -> str:
    return datetime.now(timezone.utc).strftime("%Y_%m_%d")


def find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for p in [cur, *cur.parents]:
        if (p / "pyproject.toml").exists() and (p / "AGENTS.md").exists():
            return p
    raise SystemExit("Could not locate repo root (expected pyproject.toml + AGENTS.md). Run from the repo, or pass an absolute path inside it.")


REPO_ROOT = find_repo_root(Path(__file__))
STRUCTURER = REPO_ROOT / "scripts" / "structure_session_log.py"


@dataclass(frozen=True)
class Target:
    path: Path


def iter_targets(path: Path, glob_pat: str | None) -> Iterable[Target]:
    if path.is_file():
        if path.name.endswith("_structured.txt") or path.name.endswith("_structured.json") or path.name.endswith("_pretty.md"):
            return
        yield Target(path=path)
        return
    if path.is_dir():
        pat = glob_pat or "*"
        for p in sorted(path.glob(pat)):
            if p.is_file():
                if p.name.endswith("_structured.txt") or p.name.endswith("_structured.json") or p.name.endswith("_pretty.md"):
                    continue
                yield Target(path=p)


def safe_archive(original: Path, archive_root: Path) -> Path:
    archive_root.mkdir(parents=True, exist_ok=True)
    dst = archive_root / original.name
    if not dst.exists():
        return dst
    stem = dst.stem
    suf = dst.suffix
    i = 2
    while True:
        cand = archive_root / f"{stem}__dup{i}{suf}"
        if not cand.exists():
            return cand
        i += 1


def run_structurer(target: Path) -> None:
    # We execute the repo-level structurer so behavior stays centralized.
    import subprocess

    cmd = ["uv", "run", str(STRUCTURER), str(target)]
    proc = subprocess.run(cmd, cwd=REPO_ROOT, check=False)
    if proc.returncode != 0:
        raise SystemExit(f"Structurer failed for {target.as_posix()} (exit {proc.returncode})")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="File or directory to upcycle.")
    ap.add_argument("--glob", dest="glob_pat", help="If path is a directory, glob for files.")
    ap.add_argument("--archive", action="store_true", help="Move originals into archive/YYYY_MM_DD/.")
    args = ap.parse_args()

    p = (REPO_ROOT / args.path).resolve() if not Path(args.path).is_absolute() else Path(args.path).resolve()
    if not p.exists():
        raise SystemExit(f"Not found: {p}")

    archive_root = p.parent / "archive" / utc_date_tag()
    count = 0
    for t in iter_targets(p, args.glob_pat):
        run_structurer(t.path)
        if args.archive:
            dst = safe_archive(t.path, archive_root)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(t.path), str(dst))
        count += 1

    print(f"Upcycled: {count} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
