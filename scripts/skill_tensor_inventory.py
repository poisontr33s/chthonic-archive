#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Build a normalized inventory of skills across Codex, Claude, and Gemini roots.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for p in [cur, *cur.parents]:
        if (p / "AGENTS.md").exists() and (p / "pyproject.toml").exists():
            return p
    return start.resolve()


def parse_frontmatter(path: Path) -> tuple[dict[str, str], bool]:
    if not path.exists():
        return {}, False
    raw = path.read_text(encoding="utf-8", errors="replace")
    if not raw.startswith("---"):
        return {}, False
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return {}, False
    fm: dict[str, str] = {}
    current_section: str | None = None
    for line in parts[1].splitlines():
        if not line.strip():
            continue
        if not line.startswith(" ") and line.endswith(":"):
            current_section = line.strip()[:-1]
            continue
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key = key.strip()
        val = val.strip().strip("\"")
        if current_section == "metadata" and line.startswith(" "):
            fm[f"metadata.{key}"] = val
        else:
            fm[key] = val
    return fm, True


def classify_skill(name: str, fm: dict[str, str], has_md: bool) -> str:
    if not has_md:
        return "missing"
    desc = fm.get("description", "").lower()
    if "redirect" in desc or "stashed" in desc or "protocol" in desc:
        return "redirect_or_stub"
    return "candidate"


def inventory_root(repo_root: Path, lane: str, root_rel: str) -> list[dict]:
    root = repo_root / root_rel
    if not root.exists():
        return []
    rows: list[dict] = []
    for skill_dir in sorted([p for p in root.iterdir() if p.is_dir()], key=lambda p: p.name.lower()):
        skill_md = skill_dir / "SKILL.md"
        fm, has_yaml = parse_frontmatter(skill_md)
        rows.append(
            {
                "lane": lane,
                "root": root_rel,
                "skill": skill_dir.name,
                "path": str(skill_dir.relative_to(repo_root)).replace("\\", "/"),
                "has_skill_md": skill_md.exists(),
                "has_yaml_frontmatter": has_yaml,
                "has_scripts_dir": (skill_dir / "scripts").exists(),
                "has_assets_dir": (skill_dir / "assets").exists(),
                "last_modified": skill_dir.stat().st_mtime,
                "description": fm.get("description"),
                "classification": classify_skill(skill_dir.name, fm, skill_md.exists()),
            }
        )
    return rows


def write_markdown_summary(path: Path, payload: dict) -> None:
    skills = payload.get("skills", [])
    by_lane = {}
    for row in skills:
        by_lane[row["lane"]] = by_lane.get(row["lane"], 0) + 1
    lines = [
        "# Skill Tensor Inventory",
        "",
        f"- Total Skills: `{len(skills)}`",
        "",
        "## Per Lane",
    ]
    for lane, count in sorted(by_lane.items()):
        lines.append(f"- `{lane}`: `{count}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build skill tensor inventory")
    parser.add_argument("--output", default="codex/mailbox/SKILL_TENSOR_INVENTORY.json")
    args = parser.parse_args()

    repo_root = find_repo_root(Path.cwd())
    roots = {
        "codex": ".codex/skills",
        "claude": ".claude/skills",
        "gemini": ".gemini/extensions/chthonic-archive-sync/skills",
    }

    payload = {
        "schema_version": 1,
        "generated_from": str(repo_root).replace("\\", "/"),
        "skills": [],
    }

    for lane, root_rel in roots.items():
        payload["skills"].extend(inventory_root(repo_root, lane, root_rel))

    out = repo_root / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_markdown_summary(out.with_suffix(".md"), payload)
    print(out.relative_to(repo_root).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
