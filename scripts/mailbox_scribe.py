#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: mailbox_scribe.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Mailbox Scribe.

Purpose:
- Generate a single, up-to-date session packet markdown from mailbox artifacts.
- Update mailbox manifest/current-state files without deleting history.

Invocation:
- uv run scripts/mailbox_scribe.py --target codex --packet codex/mailbox/TETRAGRAMMATON_PACKET.md

@SID:           TOOL_MAILBOX_SCRIBE_V1
@Shabti:        CLI Script
@Purpose:       Mailbox Scribe.
"""

from __future__ import annotations


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import argparse
import hashlib
import json
import sys
import warnings
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.shared import find_repo_root

REPO_ROOT = find_repo_root()
POLICY_PATH = REPO_ROOT / ".meta" / "mailbox-scribe-policy.json"

POLICY_DEFAULTS: dict[str, Any] = {
    "update_manifest": True,
    "update_current_state": True,
    "prefer_files": [],
    "include_patterns": ["*.md", "*.json"],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def list_files(root: Path, patterns: list[str]) -> list[Path]:
    out: list[Path] = []
    for pat in patterns:
        out.extend(sorted(root.glob(pat)))
    return sorted({p.resolve() for p in out if p.is_file()})


def write_manifest(root: Path) -> None:
    archive = root / "archive"
    # Avoid self-reference loops in tools that recursively traverse "active" artifacts.
    active_md = sorted(p.name for p in root.glob("*.md") if p.is_file())
    active_json = sorted(
        p.name
        for p in root.glob("*.json")
        if p.is_file() and p.name != "mailbox_manifest.json"
    )
    if archive.exists():
        archived_paths = sorted(p for p in archive.rglob("*") if p.is_file())
        archived = [p.relative_to(archive).as_posix() for p in archived_paths]
    else:
        archived = []
    payload = {
        # Schema v2: avoids self-reference loops by excluding the manifest from active.json.
        "schema_version": 2,
        "mailbox": root.as_posix(),
        "generated_on": utc_now(),
        "manifest_file": "mailbox_manifest.json",
        "active": {"md": active_md, "json": active_json},
        "archive_count": len(archived),
        "archive_files": archived,
    }
    path = root / "mailbox_manifest.json"
    rendered = json.dumps(payload, indent=2)
    existing = path.read_text(encoding="utf-8") if path.exists() else None
    if existing != rendered:
        path.write_text(rendered, encoding="utf-8")


def write_current_state(root: Path) -> None:
    archive = root / "archive"
    active = sorted([p.name for p in root.glob("*.md")] + [p.name for p in root.glob("*.json")])
    archived_count = len([p for p in archive.rglob("*") if p.is_file()]) if archive.exists() else 0
    lines = [
        "---",
        "type: mailbox-state",
        f"updated: {utc_now()}",
        f"mailbox: {root.as_posix()}",
        "---",
        "",
        "# Mailbox Current State",
        "",
        "## Active Files",
    ]
    for f in active:
        lines.append(f"- `{f}`")
    lines += [
        "",
        "## Archive",
        f"- Path: `{archive.as_posix()}`",
        f"- Count: {archived_count}",
        "",
        "## Policy",
        "- Root mailbox keeps only current-cycle files.",
        "- Historical files may remain in `archive/`.",
        "- Hidden dot mailboxes stay sentinel-only (`.gitkeep`).",
    ]
    # Stable filename to avoid date churn.
    path = root / "MAILBOX_CURRENT_STATE.md"
    rendered = "\n".join(lines) + "\n"
    existing = path.read_text(encoding="utf-8") if path.exists() else None
    if existing != rendered:
        path.write_text(rendered, encoding="utf-8")


@dataclass(frozen=True)
class RefDoc:
    name: str
    path: Path
    kind: str  # md|json


def pick_refs(root: Path, prefer: list[str], patterns: list[str]) -> list[RefDoc]:
    files = list_files(root, patterns)
    by_name = {p.name: p for p in files}
    refs: list[RefDoc] = []
    for name in prefer:
        p = by_name.get(name)
        if not p:
            continue
        refs.append(RefDoc(name=name, path=p, kind="json" if p.suffix.lower() == ".json" else "md"))
    return refs


def read_md_excerpt(path: Path, max_lines: int = 120) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    excerpt = "\n".join(lines[:max_lines]).strip()
    if len(lines) > max_lines:
        excerpt += "\n\n...(truncated)..."
    return excerpt


def extract_frontmatter(md: str) -> tuple[dict[str, str], str]:
    lines = md.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        return {}, md
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, md
    fm_lines = lines[1:end]
    body = "\n".join(lines[end + 1 :])
    fm: dict[str, str] = {}
    for line in fm_lines:
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        fm[k.strip()] = v.strip()
    return fm, body


def build_sources_fingerprint(refs: list[RefDoc]) -> tuple[str, list[dict[str, Any]]]:
    src_meta: list[dict[str, Any]] = []
    for r in refs:
        content = r.path.read_text(encoding="utf-8", errors="ignore")
        src_meta.append(
            {
                "name": r.name,
                "kind": r.kind,
                "sha256": sha256_text(content),
                "bytes": r.path.stat().st_size,
            }
        )
    src_meta_sorted = sorted(src_meta, key=lambda x: x["name"])
    fingerprint = sha256_text(json.dumps(src_meta_sorted, sort_keys=True))
    return fingerprint, src_meta_sorted


def split_scribe_log(body: str) -> tuple[str, list[str]]:
    marker = "## Scribe Log"
    if marker not in body:
        return body.rstrip(), []
    before, after = body.split(marker, 1)
    log_lines = (marker + after).splitlines()
    if log_lines and log_lines[0].strip() == marker:
        log_lines = log_lines[1:]
    log_lines = [ln.rstrip() for ln in log_lines if ln.strip()]
    return before.rstrip(), log_lines


def build_packet(root: Path, refs: list[RefDoc], existing_packet: str | None) -> str:
    sources_hash, sources_meta = build_sources_fingerprint(refs)
    created = utc_now()
    updated = created
    log: list[str] = []

    if existing_packet:
        fm, body = extract_frontmatter(existing_packet)
        if "created" in fm:
            created = fm["created"]
        if "updated" in fm:
            updated = fm["updated"]
        base_body, prior_log = split_scribe_log(body)
        log = prior_log
        if fm.get("sources_hash") != sources_hash:
            updated = utc_now()
            log.append(f"- {updated}: sources changed")
    else:
        log.append(f"- {updated}: packet created")

    lines: list[str] = []
    lines += [
        "---",
        "type: packet",
        f"created: {created}",
        f"updated: {updated}",
        f"mailbox: {root.as_posix()}",
        "codename: TETRAGRAMMATON",
        f"sources_hash: {sources_hash}",
        f"sources_count: {len(sources_meta)}",
        "---",
        "",
        "# TETRAGRAMMATON Packet",
        "",
        f"<!-- @SCRIBED: {utc_now()} -->",
        "",
        "## Packet Rules",
        "- Paths are repo-relative (portable; no local usernames).",
        "- Large JSON files may be embedded as a valid JSON stub with `_truncated: true`.",
        "- Stub fields: `relative_path`, `bytes`, `sha256`.",
        "",
        "## Index",
    ]
    for r in refs:
        lines.append(f"- `{r.name}`")
    lines += [
        "",
        "## Snapshot",
        f"- Generated: `{updated}`",
        f"- Sources hash: `{sources_hash}`",
        "",
        "## Content",
    ]
    for r in refs:
        lines += [
            "",
            f"### {r.name}",
            f"Path: `{r.path.relative_to(REPO_ROOT).as_posix()}`",
        ]
        if r.kind == "md":
            lines.append("")
            lines.append("```md")
            lines.append(read_md_excerpt(r.path))
            lines.append("```")
        else:
            raw = json.loads(r.path.read_text(encoding="utf-8"))
            preview = json.dumps(raw, indent=2)
            if len(preview) > 4000:
                # Keep the embedded snippet syntactically valid JSON to avoid misleading readers/tools.
                wrapper = {
                    "_truncated": True,
                    "note": "Full JSON omitted from packet; see relative_path in the repo.",
                    "name": r.name,
                    "relative_path": r.path.relative_to(REPO_ROOT).as_posix(),
                    "bytes": r.path.stat().st_size,
                    "sha256": sha256_text(r.path.read_text(encoding="utf-8", errors="ignore")),
                }
                preview = json.dumps(wrapper, indent=2)
            lines.append("")
            lines.append("```json")
            lines.append(preview)
            lines.append("```")
    lines.append("")
    lines += [
        "## Scribe Log",
        "",
    ]
    if not log:
        log = [f"- {utc_now()}: packet created"]
    lines.extend(log)
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", choices=["codex", "claude", "gemini"], required=True)
    ap.add_argument("--packet", required=True, help="Output packet path.")
    args = ap.parse_args()

    if not POLICY_PATH.exists():
        warnings.warn(
            f"Policy file absent: {POLICY_PATH}\n"
            "Using defaults: update_manifest=True, update_current_state=True, "
            "prefer_files=[], include_patterns=['*.md', '*.json'].\n"
            "Create .meta/mailbox-scribe-policy.json to override.",
            UserWarning,
            stacklevel=1,
        )
        policy = POLICY_DEFAULTS.copy()
    else:
        policy = read_json(POLICY_PATH)

    if args.target == "codex":
        mailbox = Path("codex/mailbox")
    elif args.target == "claude":
        mailbox = Path("claude/mailbox")
    else:
        mailbox = Path("gemini/mailbox")
    mailbox.mkdir(parents=True, exist_ok=True)

    # Update manifest/state first so the packet snapshot is consistent.
    if policy.get("update_manifest", True):
        write_manifest(mailbox)
    if policy.get("update_current_state", True):
        write_current_state(mailbox)

    refs = pick_refs(mailbox, policy["prefer_files"], policy["include_patterns"])
    out = Path(args.packet)
    out.parent.mkdir(parents=True, exist_ok=True)
    existing_packet = out.read_text(encoding="utf-8") if out.exists() else None
    packet_text = build_packet(mailbox, refs, existing_packet)
    # Only rewrite if content changed (fingerprint is embedded in frontmatter).
    wrote_packet = False
    if not existing_packet or sha256_text(existing_packet) != sha256_text(packet_text):
        out.write_text(packet_text, encoding="utf-8")
        wrote_packet = True
    else:
        print("No changes detected; packet not rewritten.")

    if wrote_packet:
        print(f"Wrote: {out.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
