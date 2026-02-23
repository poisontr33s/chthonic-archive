#!/usr/bin/env python3
#-*- coding: utf-8 -*-
"""SSOT Drift Check (governance guardrail)

Recomputes the SHA256 of `.github/copilot-instructions.md` and checks that each
"tempered" artifact embeds the same `ssot_hash`.

Targets are sourced from:
  dumpster-dive/DUMPSTER_DIVE_REGISTRY.json -> folder_structure.forge.subdirectories.tempered.current_files

Exit codes:
- 0: all OK
- 2: drift detected (hash mismatch)
- 3: missing / unreadable / no embedded hash
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


HEX64_RE = re.compile(r"^[A-F0-9]{64}$")


@dataclass(frozen=True)
class CheckResult:
    filename: str
    relative_path: str
    file_id: Optional[str]
    embedded_hash: Optional[str]
    ssot_hash: str
    status: str  # OK | DRIFT | MISSING
    detail: str


def sha256_hex_upper(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_markdown_embedded_hash(text: str) -> Optional[str]:
    # We avoid YAML parsers (dependency-free). Expect SHES-001 frontmatter.
    if not text.startswith("---\n"):
        return None

    end = text.find("\n---\n", 4)
    if end == -1:
        return None

    frontmatter = text[: end + len("\n---\n")]

    # Look for a line like: ssot_hash: "ABC..."
    m = re.search(r"(?m)^\s*ssot_hash:\s*\"?([A-Fa-f0-9]{64})\"?\s*$", frontmatter)
    if not m:
        return None
    return m.group(1).upper()


def parse_json_embedded_hash(obj: Any) -> Optional[str]:
    if not isinstance(obj, dict):
        return None
    lineage = obj.get("ssot_lineage")
    if not isinstance(lineage, dict):
        return None
    value = lineage.get("ssot_hash")
    if not isinstance(value, str):
        return None
    return value.upper()


def resolve_targets(registry: Dict[str, Any]) -> List[str]:
    return list(
        registry["folder_structure"]["forge"]["subdirectories"]["tempered"]["current_files"]
    )


def build_file_id_lookup(registry: Dict[str, Any]) -> Dict[str, str]:
    lookup: Dict[str, str] = {}
    files = registry.get("tempered_artifacts", {}).get("files", [])
    if isinstance(files, list):
        for entry in files:
            if not isinstance(entry, dict):
                continue
            filename = entry.get("filename")
            file_id = entry.get("file_id")
            if isinstance(filename, str) and isinstance(file_id, str):
                lookup[filename] = file_id
    return lookup


def check_one(
    *,
    dumpster_dive_root: Path,
    filename: str,
    ssot_hash: str,
    file_id_lookup: Dict[str, str],
) -> CheckResult:
    rel = f"forge/tempered/{filename}"
    path = dumpster_dive_root / rel

    if not path.exists():
        return CheckResult(
            filename=filename,
            relative_path=rel,
            file_id=file_id_lookup.get(filename),
            embedded_hash=None,
            ssot_hash=ssot_hash,
            status="MISSING",
            detail="File not found on disk",
        )

    embedded: Optional[str] = None
    try:
        if path.suffix.lower() in {".md", ".markdown"}:
            embedded = parse_markdown_embedded_hash(path.read_text(encoding="utf-8"))
        elif path.suffix.lower() == ".json":
            embedded = parse_json_embedded_hash(read_json(path))
        else:
            return CheckResult(
                filename=filename,
                relative_path=rel,
                file_id=file_id_lookup.get(filename),
                embedded_hash=None,
                ssot_hash=ssot_hash,
                status="MISSING",
                detail=f"Unsupported file type: {path.suffix}",
            )
    except Exception as exc:  # noqa: BLE001 (CLI tool)
        return CheckResult(
            filename=filename,
            relative_path=rel,
            file_id=file_id_lookup.get(filename),
            embedded_hash=None,
            ssot_hash=ssot_hash,
            status="MISSING",
            detail=f"Read/parse error: {exc}",
        )

    if embedded is None:
        return CheckResult(
            filename=filename,
            relative_path=rel,
            file_id=file_id_lookup.get(filename),
            embedded_hash=None,
            ssot_hash=ssot_hash,
            status="MISSING",
            detail="No embedded ssot_hash found",
        )

    if not HEX64_RE.match(embedded):
        return CheckResult(
            filename=filename,
            relative_path=rel,
            file_id=file_id_lookup.get(filename),
            embedded_hash=embedded,
            ssot_hash=ssot_hash,
            status="MISSING",
            detail="Embedded hash is not 64-char uppercase hex",
        )

    if embedded != ssot_hash:
        return CheckResult(
            filename=filename,
            relative_path=rel,
            file_id=file_id_lookup.get(filename),
            embedded_hash=embedded,
            ssot_hash=ssot_hash,
            status="DRIFT",
            detail="Embedded hash does not match current SSOT",
        )

    return CheckResult(
        filename=filename,
        relative_path=rel,
        file_id=file_id_lookup.get(filename),
        embedded_hash=embedded,
        ssot_hash=ssot_hash,
        status="OK",
        detail="",
    )


def main() -> int:
    script_path = Path(__file__).resolve()
    dumpster_dive_root = script_path.parent.parent
    repo_root = dumpster_dive_root.parent

    registry_path = dumpster_dive_root / "DUMPSTER_DIVE_REGISTRY.json"
    registry = read_json(registry_path)

    ssot_path = repo_root / ".github" / "copilot-instructions.md"
    ssot_hash = sha256_hex_upper(ssot_path.read_bytes())

    targets = resolve_targets(registry)
    file_id_lookup = build_file_id_lookup(registry)

    results: List[CheckResult] = [
        check_one(
            dumpster_dive_root=dumpster_dive_root,
            filename=filename,
            ssot_hash=ssot_hash,
            file_id_lookup=file_id_lookup,
        )
        for filename in targets
    ]

    drift = [r for r in results if r.status == "DRIFT"]
    missing = [r for r in results if r.status == "MISSING"]

    print("SSOT Drift Check")
    print(f"SSOT: .github/copilot-instructions.md")
    print(f"SSOT SHA256: {ssot_hash}")
    print(f"Targets: {len(results)} tempered artifacts")
    print()

    for r in results:
        tag = f"{r.status:7}"
        fid = r.file_id or "(no file_id)"
        if r.status == "OK":
            print(f"{tag} {r.relative_path}  {fid}")
        else:
            embedded = r.embedded_hash or "(missing)"
            print(f"{tag} {r.relative_path}  {fid}")
            print(f"        embedded: {embedded}")
            print(f"        detail:   {r.detail}")

    print()
    if drift:
        print(f"DRIFT: {len(drift)} file(s) mismatch SSOT")
        return 2
    if missing:
        print(f"MISSING: {len(missing)} file(s) missing/invalid ssot_hash")
        return 3

    print("OK: All tempered artifacts match current SSOT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
