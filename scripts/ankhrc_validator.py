#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: ankhrc_validator.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Validates .ankhrc path resolution - ensures every path declared in .ankhrc points
to an existing file or directory in the repository.

@SID:           UTIL_ANKHRC_VALIDATOR_V1
@Type:          Guardian
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.shared import find_repo_root

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import sys as _sys
    print(
        "WARNING: tomllib not available (requires Python 3.11+). "
        "ankhrc_validator.py may produce incomplete results. "
        "Upgrade to Python 3.11+ to resolve.",
        file=_sys.stderr,
    )
    tomllib = None


REPO_ROOT = find_repo_root()


@dataclass
class PathRecord:
    key_path: str
    raw_value: str
    resolved_path: str
    exists: bool


def looks_like_path(value: str) -> bool:
    return (
        value.startswith(".")
        or "/" in value
        or "\\" in value
        or value.endswith((".md", ".json", ".py", ".ps1", ".toml", ".yaml", ".yml"))
    ) and "://" not in value


def walk(node: Any, prefix: str = "") -> list[tuple[str, str]]:
    hits: list[tuple[str, str]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            key_prefix = f"{prefix}.{key}" if prefix else str(key)
            hits.extend(walk(value, key_prefix))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            key_prefix = f"{prefix}[{index}]"
            hits.extend(walk(value, key_prefix))
    elif isinstance(node, str) and looks_like_path(node):
        hits.append((prefix, node))
    return hits


def load_ankhrc(path: Path) -> Any:
    if tomllib is None:
        raise RuntimeError("tomllib unavailable; Python 3.11+ required")
    return tomllib.loads(path.read_text(encoding="utf-8"))


def validate_paths(config: Any) -> list[PathRecord]:
    records: list[PathRecord] = []
    for key_path, raw_value in walk(config):
        resolved = (REPO_ROOT / raw_value).resolve() if not Path(raw_value).is_absolute() else Path(raw_value)
        exists = resolved.exists()
        try:
            rel = str(resolved.relative_to(REPO_ROOT)).replace("\\", "/")
        except ValueError:
            rel = str(resolved)
        records.append(
            PathRecord(
                key_path=key_path,
                raw_value=raw_value,
                resolved_path=rel,
                exists=exists,
            )
        )
    return records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate .ankhrc path declarations.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Create missing files/directories declared in .ankhrc (mkdir -p for dirs, touch for files).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ankhrc = REPO_ROOT / ".ankhrc"
    if not ankhrc.exists():
        payload = {
            "status": "missing",
            "path": ".ankhrc",
            "message": "No .ankhrc exists at repository root.",
        }
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print("status: missing")
            print("path: .ankhrc")
            print("message: No .ankhrc exists at repository root.")
        return 1

    config = load_ankhrc(ankhrc)
    records = validate_paths(config)
    broken = [record for record in records if not record.exists]

    if args.fix and broken:
        fixed = 0
        for record in broken:
            target = Path(record.resolved_path)
            if not target.is_absolute():
                target = REPO_ROOT / target
            # Heuristic: if the raw value ends with / or has no suffix treat as dir
            if record.raw_value.endswith("/") or not target.suffix:
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.touch(exist_ok=True)
            print(f"[fix] created: {record.resolved_path}")
            fixed += 1
        print(f"Fixed: {fixed} path(s)")
        return 0

    payload = {
        "status": "valid" if not broken else "broken",
        "path_count": len(records),
        "broken_count": len(broken),
        "records": [record.__dict__ for record in records],
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"status: {payload['status']}")
        print(f"path_count: {payload['path_count']}")
        print(f"broken_count: {payload['broken_count']}")
        for record in broken:
            print(f"- {record.key_path}: {record.raw_value} -> {record.resolved_path}")
    return 0 if not broken else 1


if __name__ == "__main__":
    raise SystemExit(main())
