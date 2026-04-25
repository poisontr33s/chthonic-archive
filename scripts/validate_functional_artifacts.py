#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: validate_functional_artifacts.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Validate that the current functional artifact system has registered sources,
canonical outputs, and residue visibility.

Usage:
  uv run scripts/validate_functional_artifacts.py
  uv run scripts/validate_functional_artifacts.py --json
  uv run scripts/validate_functional_artifacts.py --strict

@SID:           TOOL_VALIDATE_FUNCTIONAL_ARTIFACTS_V1
@Shabti:        CLI Script
@Purpose:       Validate that the current functional artifact system has registered sources,
"""

from __future__ import annotations

import argparse
import json
import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY = REPO_ROOT / "codex" / "artifacts" / "FUNCTIONAL_ARTIFACT_REGISTRY.toml"
PRIMING_REGISTRY = REPO_ROOT / "codex" / "artifacts" / "PRIMING_REFERENCE_REGISTRY.toml"


def load_toml(path: Path) -> dict:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate functional artifacts and surface residue.")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero if residue candidates exist.")
    args = parser.parse_args()

    registry = load_toml(REGISTRY)
    priming = load_toml(PRIMING_REGISTRY)

    artifacts = registry.get("artifact", {})
    residue_patterns = registry.get("residue_pattern", [])
    priming_packets = priming.get("packet", {})

    missing_artifacts: list[str] = []
    bad_producers: list[str] = []
    missing_priming_sources: list[str] = []
    residue_hits: list[dict[str, str]] = []

    for artifact_id, entry in artifacts.items():
        path = REPO_ROOT / entry["path"]
        if not path.exists():
            missing_artifacts.append(f"{artifact_id}:{entry['path']}")
        producer = entry.get("producer", "")
        if producer not in {"manual", ""}:
            producer_path = REPO_ROOT / producer
            if not producer_path.exists():
                bad_producers.append(f"{artifact_id}:{producer}")

    for packet_id, entry in priming_packets.items():
        for source in entry.get("sources", []):
            path = REPO_ROOT / source
            if not path.exists():
                missing_priming_sources.append(f"{packet_id}:{source}")

    for entry in residue_patterns:
        glob = entry["glob"]
        reason = entry["reason"]
        for hit in REPO_ROOT.glob(glob):
            residue_hits.append(
                {
                    "path": hit.relative_to(REPO_ROOT).as_posix(),
                    "reason": reason,
                }
            )

    summary = {
        "registry_path": REGISTRY.relative_to(REPO_ROOT).as_posix(),
        "priming_registry_path": PRIMING_REGISTRY.relative_to(REPO_ROOT).as_posix(),
        "artifact_count": len(artifacts),
        "priming_packet_count": len(priming_packets),
        "missing_artifacts": missing_artifacts,
        "bad_producers": bad_producers,
        "missing_priming_sources": missing_priming_sources,
        "residue_hits": residue_hits,
        "ok": not (missing_artifacts or bad_producers or missing_priming_sources),
    }

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"artifact_count={summary['artifact_count']}")
        print(f"priming_packet_count={summary['priming_packet_count']}")
        print(f"missing_artifacts={len(missing_artifacts)}")
        print(f"bad_producers={len(bad_producers)}")
        print(f"missing_priming_sources={len(missing_priming_sources)}")
        print(f"residue_hits={len(residue_hits)}")
        for hit in residue_hits[:20]:
            print(f"residue={hit['path']} :: {hit['reason']}")

    if args.strict and residue_hits:
        return 2
    if missing_artifacts or bad_producers or missing_priming_sources:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
