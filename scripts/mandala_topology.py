#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: mandala_topology.py
# ║ Python module: _load_graph, _top_centrality, _build_report, _render_text, reveal_sacred_geometry, _write_output_json...
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: 🌿 THE GARDEN
# ║ Semantic ID: TOOL_MANDALA_TOPOLOGY_V1
# ║ Purpose: mandala_topology.py — Mandala Topology Reporter & Sacred Geometry Reve
# ║ Exports: _load_graph, _top_centrality, _build_report, _render_text, reveal_sa
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Cross-References (Bidirectional):
# ║  (Standalone file - no detected dependencies)
# ╚════════════════════════════════════════════════════════════════════════════


"""
mandala_topology.py — Mandala Topology Reporter & Sacred Geometry Revealer
================================================================================
SEMANTIC IDENTITY (Anchor & Signal Protocol)
================================================================================
@SID:           TOOL_MANDALA_TOPOLOGY_V1
@Type:          Script / Module
@Context:       Analysis / Topology Reporting / Sacred Geometry
@Implements:    CONCEPT_MANDALA_TOPOLOGY_REPORT
@Emits:         STATE_MANDALA_TOPOLOGY_REPORT
@Related:       TOOL_MANDALA_GRAPH_BUILDER_V1
================================================================================
Generates a topology report from a Mandala graph JSON file, revealing the sacred geometry
of the archive.
Usage:
uv run scripts/mandala_topology.py
                                   --graph topology_graph.json
                                   --format text
                                   --style mythic
                                   --top 10
                                   --out report.json
"""


from __future__ import annotations
import argparse
import json

from pathlib import Path
import sys
from typing import Any, Dict, List, Tuple

import networkx as nx


def _load_graph(graph_path: Path) -> nx.DiGraph:
    data = json.loads(graph_path.read_text(encoding='utf-8'))
    graph = nx.DiGraph()
    for node in data.get('nodes', []):
        node_id = node.get('id')
        if node_id is None:
            continue
        graph.add_node(node_id, **node)
    for edge in data.get('edges', []):
        source = edge.get('source')
        target = edge.get('target')
        if source is None or target is None:
            continue
        graph.add_edge(source, target, **edge)
    return graph


def _top_centrality(graph: nx.DiGraph, limit: int) -> List[Tuple[str, float]]:
    density = nx.degree_centrality(graph)
    return sorted(density.items(), key=lambda item: item[1], reverse=True)[:limit]


def _build_report(graph: nx.DiGraph, graph_path: Path, top_n: int) -> Dict[str, Any]:
    top = _top_centrality(graph, top_n)
    is_dag = nx.is_directed_acyclic_graph(graph)
    return {
        "graph_path": str(graph_path),
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "top_centrality": [
            {"id": node_id, "score": score}
            for node_id, score in top
        ],
        "is_dag": is_dag,
        "cycles_detected": not is_dag,
    }


def _render_text(report: Dict[str, Any], style: str) -> str:
    nodes = report["nodes"]
    edges = report["edges"]
    top = report["top_centrality"]

    if style == "mythic":
        lines = [
            "🌀 [MANDALA] Tracing the Sacred Lines of the Archive...",
            f"✨ [REVELATION] The {nodes} Stars are aligned via {edges} Ley Lines.",
            "   ⭐ The Constellations of Power:",
        ]
        for entry in top:
            lines.append(f"      - {entry['id']} (Resonance: {entry['score']:.4f})")
        if report["is_dag"]:
            lines.append("\n🌊 [FLOW] The energy flows without obstruction. Pure. Potent.")
        else:
            lines.append("\n🌪️ [TURBULENCE] Cycles detected. The energy is knotted. Release it.")
        return "\n".join(lines)

    lines = [
        "Mandala topology report",
        f"Nodes: {nodes}",
        f"Edges: {edges}",
        "Top centrality:",
    ]
    for entry in top:
        lines.append(f"- {entry['id']} ({entry['score']:.4f})")
    lines.append(f"DAG: {report['is_dag']}")
    return "\n".join(lines)


def reveal_sacred_geometry(graph_path: str = "topology_graph.json", *,
                           top_n: int = 5,
                           output_format: str = "json",
                           style: str = "neutral",
                           output_path: str | None = None) -> Dict[str, Any] | None:
    path = Path(graph_path)
    if not path.exists():
        message = {"error": "topology_graph_not_found", "graph_path": str(path)}
        if output_format == "json":
            _write_output_json(message, output_path)
        else:
            print("Topology graph not found.")
        return None

    try:
        graph = _load_graph(path)
        report = _build_report(graph, path, top_n)

        if output_format == "json":
            _write_output_json(report, output_path)
        else:
            print(_render_text(report, style))

        return report
    except Exception as exc:
        error = {"error": "mandala_read_failed", "detail": str(exc), "graph_path": str(path)}
        if output_format == "json":
            _write_output_json(error, output_path)
        else:
            print(f"Mandala could not be read: {exc}")
        return None


def _write_output_json(payload: Dict[str, Any], output_path: str | None) -> None:
    content = json.dumps(payload, indent=2, ensure_ascii=False)
    if output_path:
        Path(output_path).write_text(content, encoding="utf-8")
    else:
        print(content)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mandala topology report (structured output)."
    )
    parser.add_argument("--graph", default="topology_graph.json", help="Path to topology graph JSON")
    parser.add_argument("--top", type=int, default=5, help="Top N nodes by degree centrality")
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--style",
        choices=["neutral", "mythic"],
        default="neutral",
        help="Text style (only applies to --format text)",
    )
    parser.add_argument("--out", help="Write JSON output to file")
    return parser


def main(argv: List[str]) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    reveal_sacred_geometry(
        graph_path=args.graph,
        top_n=args.top,
        output_format=args.format,
        style=args.style,
        output_path=args.out,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
