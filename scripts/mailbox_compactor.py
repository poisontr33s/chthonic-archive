#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: mailbox_compactor.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""Mailbox compactor.

Goal: reduce mailbox noise by producing:
- one consolidated narrative packet (MD)
- one consolidated evidence index (JSON)

It does not delete source files. It can optionally update mailbox_manifest.json
active lists to point to the new consolidated artifacts.

Policy:
- deterministic ordering
- no cmd.exe wrappers
- no secrets

@SID:           TOOL_MAILBOX_COMPACTOR_V1
@Shabti:        CLI Script
@Purpose:       Mailbox compactor.
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
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT_CANDIDATE = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT_CANDIDATE) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT_CANDIDATE))

from scripts.lib.shared import find_repo_root  # noqa: E402

REPO_ROOT = find_repo_root()
MAILBOX = REPO_ROOT / "codex" / "mailbox"


@dataclass(frozen=True)
class Artifact:
    path: Path

    @property
    def name(self) -> str:
        return self.path.name


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def list_artifacts(since: datetime | None = None, max_files: int | None = None) -> tuple[list[Artifact], list[Artifact]]:
    def _filter(paths: list[Artifact]) -> list[Artifact]:
        if since is not None:
            paths = [
                a for a in paths
                if datetime.fromtimestamp(a.path.stat().st_mtime, tz=timezone.utc) >= since
            ]
        if max_files is not None:
            paths = paths[:max_files]
        return paths

    md = sorted([Artifact(p) for p in MAILBOX.glob("*.md") if p.is_file()], key=lambda a: a.name)
    js = sorted([Artifact(p) for p in MAILBOX.glob("*.json") if p.is_file()], key=lambda a: a.name)
    return _filter(md), _filter(js)


def is_low_signal_duplicate(name: str) -> bool:
    # Keep latest stable files and consolidated packets.
    if name in {"MAILBOX_CURRENT_STATE.md", "TETRAGRAMMATON_PACKET.md", "TOOLCHAIN_DOCTOR_LATEST.md"}:
        return False
    # Dated mailbox-current-state files are duplicates.
    if re.match(r"^MAILBOX_CURRENT_STATE_\d{4}_\d{2}_\d{2}\.md$", name):
        return True
    return False


def build_consolidated_md(md_files: list[Artifact], json_files: list[Artifact], out_path: Path) -> None:
    lines: list[str] = []
    lines.append("---")
    lines.append("type: mailbox_packet")
    lines.append("created: " + utc_now())
    lines.append("scope: codex/mailbox")
    lines.append("---")
    lines.append("")
    lines.append("# Mailbox Packet (Consolidated)")
    lines.append("")
    lines.append("## Index")
    lines.append("")

    for a in md_files:
        lines.append(f"- `{a.name}`")

    lines.append("")
    lines.append("## JSON Index")
    lines.append("")
    for a in json_files:
        lines.append(f"- `{a.name}`")

    lines.append("")
    lines.append("## Documents")

    for a in md_files:
        lines.append("")
        lines.append(f"### {a.name}")
        lines.append("")
        lines.append(f"Path: `{a.path.as_posix()}`")
        lines.append("")
        lines.append("```md")
        lines.append(read_text(a.path).rstrip())
        lines.append("```")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_evidence_json(md_files: list[Artifact], json_files: list[Artifact], out_path: Path) -> None:
    payload: dict[str, Any] = {
        "generated_at": utc_now(),
        "mailbox": str(MAILBOX.as_posix()),
        "md": [{"name": a.name, "bytes": a.path.stat().st_size} for a in md_files],
        "json": [{"name": a.name, "bytes": a.path.stat().st_size} for a in json_files],
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def update_manifest(manifest_path: Path, keep_md: list[str], keep_json: list[str]) -> None:
    obj = json.loads(manifest_path.read_text(encoding="utf-8"))
    active = obj.get("active", {})
    active["md"] = keep_md
    active["json"] = keep_json
    obj["active"] = active
    obj["generated_on"] = utc_now()
    manifest_path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Update mailbox_manifest.json active lists")
    ap.add_argument("--since", metavar="ISO", default=None, help="Only compact artifacts modified after this ISO timestamp (e.g. 2026-04-01T00:00:00Z)")
    ap.add_argument("--max-files", metavar="N", type=int, default=None, help="Limit the number of files included per type (MD, JSON)")
    args = ap.parse_args()

    since: datetime | None = None
    if args.since:
        since = datetime.fromisoformat(args.since.replace("Z", "+00:00"))

    md, js = list_artifacts(since=since, max_files=args.max_files)

    # Candidate compaction: keep high-signal MDs; treat low-signal dated duplicates as excluded from packet.
    md_keep = [a for a in md if not is_low_signal_duplicate(a.name)]

    out_md = MAILBOX / "MAILBOX_PACKET_CONSOLIDATED.md"
    out_json = MAILBOX / "MAILBOX_EVIDENCE_INDEX.json"

    build_consolidated_md(md_keep, js, out_md)
    build_evidence_json(md_keep, js, out_json)

    if args.apply:
        manifest = MAILBOX / "mailbox_manifest.json"
        if manifest.exists():
            keep_md_names = sorted({a.name for a in md_keep} | {out_md.name})
            keep_json_names = sorted({a.name for a in js} | {out_json.name})
            update_manifest(manifest, keep_md_names, keep_json_names)

    print(f"Wrote: {out_md}")
    print(f"Wrote: {out_json}")


if __name__ == "__main__":
    main()
