#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: mailbox_rotation.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Mailbox rotation engine - consolidate timestamped mailbox series, archive stale root artifacts,
and regenerate MAILBOX_CURRENT_STATE.md without destructive deletion.

@SID:           UTIL_MAILBOX_ROTATION_V1
@Type:          Utility
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


from __future__ import annotations

import argparse
import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
PROTECTED_FILES = {"MAILBOX_CURRENT_STATE.md", "mailbox_manifest.json"}
PROTECTED_DIRS = {"archive", "ACTUAL-WORKING-HANDOFFS"}
TIMESTAMP_RE = re.compile(r"^(?P<prefix>.*?)(?:_(?P<stamp>\d{4}[-_]\d{2}[-_]\d{2}.*))$")
DIR_TIMESTAMP_RE = re.compile(r"^(?P<prefix>.*?)(?:_(?P<stamp>\d{8}T\d{6}Z.*))$")


@dataclass(frozen=True)
class RotationEntry:
    kind: str
    prefix: str
    keep: list[str]
    archive: list[str]
    latest_aliases: list[str]


def mailbox_root(target: str) -> Path:
    return REPO_ROOT / f"{target}/mailbox"


def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def classify_root_files(root: Path) -> tuple[list[Path], list[Path]]:
    files = [p for p in root.iterdir() if p.is_file()]
    dirs = [p for p in root.iterdir() if p.is_dir()]
    return sorted(files), sorted(dirs)


def _group_series(items: Iterable[Path], pattern: re.Pattern[str]) -> dict[str, list[Path]]:
    grouped: dict[str, list[Path]] = {}
    for item in items:
        match = pattern.match(item.stem if item.is_file() else item.name)
        if not match:
            continue
        grouped.setdefault(match.group("prefix"), []).append(item)
    return grouped


def _find_latest_alias(files: Iterable[Path], prefix: str) -> list[Path]:
    aliases: list[Path] = []
    prefix_upper = prefix.upper()
    for file in files:
        if not file.is_file():
            continue
        stem_upper = file.stem.upper()
        if stem_upper == f"{prefix_upper}_LATEST" or stem_upper.startswith(f"{prefix_upper}_LATEST_"):
            aliases.append(file)
    return sorted(aliases)


def build_file_rotation(root: Path) -> list[RotationEntry]:
    files, _ = classify_root_files(root)
    grouped = _group_series(
        [
            p
            for p in files
            if p.name not in PROTECTED_FILES and not p.name.endswith(".gitkeep")
        ],
        TIMESTAMP_RE,
    )
    plan: list[RotationEntry] = []
    for prefix, members in sorted(grouped.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        if len(members) <= 3:
            continue
        ordered = sorted(members, key=lambda p: p.stat().st_mtime, reverse=True)
        keep = [ordered[0]]
        latest_aliases = _find_latest_alias(files, prefix)
        keep.extend(latest_aliases)
        keep_names = {item.name for item in keep}
        archive = [p for p in sorted(members) if p.name not in keep_names]
        plan.append(
            RotationEntry(
                kind="file",
                prefix=prefix,
                keep=sorted({p.name for p in keep}),
                archive=[p.name for p in archive],
                latest_aliases=[p.name for p in latest_aliases],
            )
        )
    return plan


def build_dir_rotation(root: Path) -> list[RotationEntry]:
    _, dirs = classify_root_files(root)
    grouped = _group_series(
        [p for p in dirs if p.name not in PROTECTED_DIRS and not p.name.startswith(".")],
        DIR_TIMESTAMP_RE,
    )
    plan: list[RotationEntry] = []
    for prefix, members in sorted(grouped.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        if len(members) <= 3:
            continue
        ordered = sorted(members, key=lambda p: p.stat().st_mtime, reverse=True)
        keep = [ordered[0]]
        archive = [p for p in sorted(members) if p.name not in {ordered[0].name}]
        plan.append(
            RotationEntry(
                kind="directory",
                prefix=prefix,
                keep=[p.name for p in keep],
                archive=[p.name for p in archive],
                latest_aliases=[],
            )
        )
    return plan


def build_plan(root: Path) -> dict:
    files, dirs = classify_root_files(root)
    file_plan = build_file_rotation(root)
    dir_plan = build_dir_rotation(root)
    return {
        "mailbox": str(root.relative_to(REPO_ROOT)).replace("\\", "/"),
        "generated_at": current_timestamp(),
        "root_file_count": len(files),
        "root_dir_count": len(dirs),
        "protected_files": sorted(PROTECTED_FILES),
        "protected_dirs": sorted(PROTECTED_DIRS),
        "file_series": [entry.__dict__ for entry in file_plan],
        "directory_series": [entry.__dict__ for entry in dir_plan],
    }


def archive_destination(root: Path, entry_kind: str, prefix: str) -> Path:
    suffix = "directories" if entry_kind == "directory" else "series"
    return root / "archive" / suffix / prefix


def execute_plan(root: Path, plan: dict) -> list[str]:
    moves: list[str] = []
    for collection_key in ("file_series", "directory_series"):
        for entry in plan[collection_key]:
            dest = archive_destination(root, entry["kind"], entry["prefix"])
            dest.mkdir(parents=True, exist_ok=True)
            for name in entry["archive"]:
                source = root / name
                target = dest / name
                shutil.move(str(source), str(target))
                moves.append(f"{source.relative_to(REPO_ROOT)} -> {target.relative_to(REPO_ROOT)}")
    return moves


def render_mailbox_state(root: Path) -> str:
    files, dirs = classify_root_files(root)
    active_files = [
        p.name
        for p in files
        if p.name not in PROTECTED_FILES and not p.name.endswith(".gitkeep")
    ]
    latest_files = sorted([name for name in active_files if "_LATEST" in name])
    timestamped_files = sorted([name for name in active_files if TIMESTAMP_RE.match(Path(name).stem)])
    root_series = [
        entry["prefix"]
        for entry in build_plan(root)["file_series"]
    ]
    archive_dir = root / "archive"
    archive_count = sum(1 for p in archive_dir.rglob("*") if p.is_file()) if archive_dir.exists() else 0
    lines = [
        "---",
        "type: mailbox-state",
        f"updated: {current_timestamp()}",
        f"mailbox: {root.relative_to(REPO_ROOT).as_posix()}",
        "---",
        "",
        "# Mailbox Current State",
        "",
        "## Root Summary",
        f"- Root files: `{len(files)}`",
        f"- Root directories: `{len(dirs)}`",
        f"- Archive file count: `{archive_count}`",
        f"- Latest aliases at root: `{len(latest_files)}`",
        f"- Timestamped root files: `{len(timestamped_files)}`",
        "",
        "## Protected Surfaces",
        *[f"- `{name}`" for name in sorted(PROTECTED_FILES)],
        *[f"- `{name}/`" for name in sorted(PROTECTED_DIRS)],
        "",
        "## Root Series Under Rotation Policy",
        *([f"- `{name}`" for name in root_series] if root_series else ["- none"]),
        "",
        "## Root Latest Aliases",
        *([f"- `{name}`" for name in latest_files] if latest_files else ["- none"]),
        "",
        "## Root Directory Series",
    ]
    dir_series = build_plan(root)["directory_series"]
    if dir_series:
        lines.extend(
            f"- `{entry['prefix']}` ({len(entry['keep']) + len(entry['archive'])} dirs)"
            for entry in dir_series
        )
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Policy",
            "- Root mailbox keeps current-cycle files, latest aliases, and protected working handoffs.",
            "- Timestamped series with more than three members are rotation candidates.",
            "- Rotation always archives; it never deletes.",
            "- `.tmp_fixture_eval/` is temporary fixture output and should not be treated as a durable active handoff lane.",
            "",
        ]
    )
    return "\n".join(lines)


def write_mailbox_state(root: Path) -> Path:
    state_path = root / "MAILBOX_CURRENT_STATE.md"
    state_path.write_text(render_mailbox_state(root), encoding="utf-8")
    return state_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Archive mailbox series without destructive deletion.")
    parser.add_argument("--target", choices=("codex", "claude"), default="codex")
    parser.add_argument("--execute", action="store_true", help="Apply the archive moves. Default is dry-run.")
    parser.add_argument("--write-state", action="store_true", help="Regenerate MAILBOX_CURRENT_STATE.md after planning or execution.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = mailbox_root(args.target)
    plan = build_plan(root)
    result: dict[str, object] = {
        "mode": "execute" if args.execute else "dry-run",
        "plan": plan,
    }
    if args.execute:
        result["moves"] = execute_plan(root, plan)
    if args.write_state or args.execute:
        state_path = write_mailbox_state(root)
        result["mailbox_state"] = str(state_path.relative_to(REPO_ROOT)).replace("\\", "/")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
