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
build_skill_index.py — Scan skill lanes and emit a deterministic JSON index.

For each skill directory under .claude/skills/ or .codex/skills/, records:
  name, description, SKILL.md SHA-256, asset/agent/script inventory, metadata.

@SID:           TOOL_BUILD_SKILL_INDEX_V1
@Shabti:        CLI Script
@Purpose:       Scan skill lanes and emit deterministic JSON index for downstream consumers.
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
    _REPO_ROOT = Path(__file__).resolve().parents[1]
    _DEFAULT_OUT = _REPO_ROOT / "codex" / "mailbox" / "SKILL_INDEX_LATEST.json"

    parser = argparse.ArgumentParser(description="Build deterministic skills index JSON.")
    parser.add_argument("--root", default=None,
                        help="Skills root path (default: .claude/skills)")
    parser.add_argument("--out", "--output", default=str(_DEFAULT_OUT),
                        dest="out",
                        help=f"Output JSON path (default: {_DEFAULT_OUT.relative_to(_REPO_ROOT)})")
    parser.add_argument("--diff", metavar="PREV_INDEX",
                        help="Compare against a previous index JSON; print added/removed/changed skill names")
    args = parser.parse_args()

    root = Path(args.root) if args.root else _REPO_ROOT / ".claude" / "skills"
    out = Path(args.out)

    if not root.exists():
        print(f"ERROR: skills root not found: {root}", file=__import__('sys').stderr)
        return 1

    payload = build_index(root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"Wrote: {out}")
    print(f"Skills indexed: {payload['count']}")

    if args.diff:
        prev_path = Path(args.diff)
        if not prev_path.exists():
            print(f"WARN: diff target not found: {prev_path}")
        else:
            with open(prev_path, encoding="utf-8") as f:
                prev = json.load(f)
            prev_names = {s["folder"] for s in prev.get("skills", [])}
            curr_names = {s["folder"] for s in payload["skills"]}
            added = sorted(curr_names - prev_names)
            removed = sorted(prev_names - curr_names)
            changed = []
            prev_map = {s["folder"]: s for s in prev.get("skills", [])}
            curr_map = {s["folder"]: s for s in payload["skills"]}
            for name in curr_names & prev_names:
                if curr_map[name]["skill_md_sha256"] != prev_map[name].get("skill_md_sha256"):
                    changed.append(name)
            print(f"\nDiff vs {prev_path.name}:")
            print(f"  Added   ({len(added)}): {', '.join(added) or 'none'}")
            print(f"  Removed ({len(removed)}): {', '.join(removed) or 'none'}")
            print(f"  Changed ({len(changed)}): {', '.join(sorted(changed)) or 'none'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
