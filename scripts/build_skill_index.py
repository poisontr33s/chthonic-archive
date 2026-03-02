#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: build_skill_index.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
build_skill_index.py — Script logic for build_skill_index.py.

@SID:           TOOL_BUILD_SKILL_INDEX_V1
@Shabti:        CLI Script
@Purpose:       Script logic for build_skill_index.py.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def parse_frontmatter(skill_md: Path) -> dict[str, str]:
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    fm_raw = parts[1]
    out: dict[str, str] = {}
    current_section: str | None = None
    for line in fm_raw.splitlines():
        if not line.strip():
            continue
        if not line.startswith(" ") and line.endswith(":"):
            current_section = line.strip()[:-1]
            out[current_section] = ""
            continue
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        key = k.strip()
        val = v.strip().strip('"')
        if current_section == "metadata" and line.startswith(" "):
            out[f"metadata.{key}"] = val
        else:
            out[key] = val
    return out


def build_index(skills_root: Path) -> dict:
    skills = []
    for d in sorted([p for p in skills_root.iterdir() if p.is_dir() and not p.name.startswith(".")]):
        skill_md = d / "SKILL.md"
        if not skill_md.exists():
            continue
        fm = parse_frontmatter(skill_md)
        assets_dir = d / "assets"
        agents_dir = d / "agents"
        scripts_dir = d / "scripts"
        assets = sorted([p.name for p in assets_dir.glob("*") if p.is_file()]) if assets_dir.exists() else []
        agents = sorted([p.name for p in agents_dir.glob("*") if p.is_file()]) if agents_dir.exists() else []
        scripts = sorted([p.name for p in scripts_dir.glob("*.py") if p.is_file()]) if scripts_dir.exists() else []
        skills.append(
            {
                "folder": d.name,
                "name": fm.get("name", d.name),
                "description": fm.get("description", ""),
                "skill_md": str(skill_md.as_posix()),
                "skill_md_sha256": sha256_file(skill_md),
                "assets": assets,
                "agents": agents,
                "scripts": scripts,
                "metadata": {k: v for k, v in fm.items() if k.startswith("metadata.")},
            }
        )
    return {
        "skills_root": str(skills_root.as_posix()),
        "generated_at": datetime.now(UTC).isoformat(),
        "count": len(skills),
        "skills": skills,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build deterministic skills index JSON.")
    parser.add_argument("--root", required=True, help="Skills root path (.codex/skills or .claude/skills)")
    parser.add_argument("--out", required=True, help="Output JSON path")
    args = parser.parse_args()

    root = Path(args.root)
    out = Path(args.out)
    payload = build_index(root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"Wrote: {out.as_posix()}")
    print(f"Skills indexed: {payload['count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
