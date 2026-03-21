#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@SID: SCRIPT_RECOVERED_PYTHON_CLUSTER_REGISTRY_V1
@Purpose: Promote tempered recovered Python cluster metadata into active scripts lane.
@Source: dumpster-dive/forge/tempered/python/consolidated_python_utilities.py
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class RecoveredPythonCluster:
    source_file: str
    fragment_count: int
    sample_lines: tuple[str, ...]


RECOVERED_PYTHON_CLUSTERS: list[RecoveredPythonCluster] = [
    RecoveredPythonCluster(
        source_file="scripts/poe_transport_audit.py",
        fragment_count=21,
        sample_lines=(
            "def probe_sdk(account: str, bot: str, prompt: str) -> ProbeResult:",
            'rc, out, err = run_cmd(["uv", ...])',
        ),
    ),
    RecoveredPythonCluster(
        source_file="scripts/poe_lane.py",
        fragment_count=15,
        sample_lines=(
            "Poe lane helper (OpenAI-compatible endpoint).",
            "Modes: models/list/ask.",
        ),
    ),
    RecoveredPythonCluster(
        source_file="scripts/code_scent.py",
        fragment_count=9,
        sample_lines=(
            "Python module: analyze_scent",
            "Decorator blessing metadata and scent analyzer contract.",
        ),
    ),
    RecoveredPythonCluster(
        source_file="scripts/background_services.py",
        fragment_count=8,
        sample_lines=(
            "Background Services",
            "Independent monitoring and workflow supplements.",
        ),
    ),
    RecoveredPythonCluster(
        source_file="mas_mcp/mas_diagnostics.py",
        fragment_count=8,
        sample_lines=(
            "MAS-MCP diagnostics",
            "Living layer self-examination routines.",
        ),
    ),
    RecoveredPythonCluster(
        source_file="scripts/mandala_topology.py",
        fragment_count=7,
        sample_lines=(
            "reveal_sacred_geometry()",
            "topology report and centrality extraction helpers.",
        ),
    ),
    RecoveredPythonCluster(
        source_file="scripts/upcycle_audit.py",
        fragment_count=6,
        sample_lines=(
            "COMMENT_MARKERS and SKIP_PATTERNS",
            "scan_paths()",
        ),
    ),
    RecoveredPythonCluster(
        source_file="scripts/code_taste.py",
        fragment_count=6,
        sample_lines=(
            "Python module: analyze_taste",
            "Taste profiling and category tagging.",
        ),
    ),
    RecoveredPythonCluster(
        source_file="scripts/ssot_hash.py",
        fragment_count=6,
        sample_lines=(
            "canonicalize()",
            "verify_ssot_integrity()",
        ),
    ),
    RecoveredPythonCluster(
        source_file="scripts/run_cycle.py",
        fragment_count=5,
        sample_lines=(
            "find_workspace_root()",
            "MAS_MCP_ROOT and compatibility wiring.",
        ),
    ),
    RecoveredPythonCluster(
        source_file="scripts/github_voice.py",
        fragment_count=5,
        sample_lines=(
            "is_voice_active()",
            "broadcast_issue()",
        ),
    ),
    RecoveredPythonCluster(
        source_file="scripts/code_texture.py",
        fragment_count=5,
        sample_lines=(
            "analyze_texture()",
            "texture signal extraction routines.",
        ),
    ),
]


def top_clusters(limit: int = 10) -> list[RecoveredPythonCluster]:
    """Return the top N recovered clusters by canonical ordering."""
    return RECOVERED_PYTHON_CLUSTERS[: max(limit, 0)]


def search_clusters(keyword: str) -> list[RecoveredPythonCluster]:
    """Filter clusters by source file keyword."""
    lowered = keyword.lower()
    return [cluster for cluster in RECOVERED_PYTHON_CLUSTERS if lowered in cluster.source_file.lower()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Recovered Python cluster registry")
    parser.add_argument("--search", default="", help="keyword for source_file filtering")
    parser.add_argument("--limit", type=int, default=10, help="max number of rows for non-search mode")
    args = parser.parse_args()

    rows = search_clusters(args.search) if args.search else top_clusters(args.limit)
    payload = [asdict(row) for row in rows]
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
