#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: unified_topology.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
🌐 UNIFIED TOPOLOGY BUILDER
═══════════════════════════════════════════════════════════════════════════════

Cross-Lane Dependency Graph Generator
Integrates: DCRP (Python/TS) + MCP + Lineage Templates + Rust

Produces:
  - topology_graph.json (NetworkX graph with lane/language/tier metadata)
  - topology_map.md (Mermaid visualization)
  - topology_summary.md (Statistical overview)

Usage:
    uv run python unified_topology.py

═══════════════════════════════════════════════════════════════════════════════

@SID:           TOOL_UNIFIED_TOPOLOGY_V1
@Shabti:        CLI Script
@Purpose:       🌐 UNIFIED TOPOLOGY BUILDER
"""

from __future__ import annotations


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent))
from scripts.lib.ssot_paths import SSOT_POINTER

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Literal, Dict, List, Optional, Set, Any
import json
import re
import networkx as nx
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════════
# TYPE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

Lane = Literal["DCRP", "LineageA", "LineageB", "LineageC", "MCP", "Rust", "Scripts", "Docs"]
Language = Literal["python", "typescript", "rust", "markdown", "json", "toml", "yaml", "other"]
EdgeKind = Literal["import", "schema_ref", "template_use", "tool_binding", "config_ref"]

@dataclass
class NodeMeta:
    """Metadata for a single file node in the unified graph."""
    path: str
    lane: Lane
    language: Language
    tier: Optional[str] = None          # e.g. "T0.5", "T1", "T2"
    prism_band: Optional[str] = None    # ROGBIV spectral frequency
    role: Optional[str] = None          # From DCRP essence
    exports_count: int = 0

@dataclass
class EdgeMeta:
    """Metadata for a dependency edge."""
    source: str
    target: str
    kind: EdgeKind
    lane_relation: Optional[str] = None  # e.g. "DCRP→MCP", "LineageA→DCRP"

# ═══════════════════════════════════════════════════════════════════════════════
# PATH CLASSIFICATION
# ═══════════════════════════════════════════════════════════════════════════════

PROJECT_ROOT = Path(__file__).parent.parent

def classify_lane(path_str: str) -> Lane:
    """Infer lane from file path."""
    p = Path(path_str)
    parts = p.parts

    # Explicit lane markers
    if "dumpster-dive" in parts:
        if "lineage-A-template" in parts or any("lineage-A" in x for x in parts):
            return "LineageA"
        elif "lineage-B-template" in parts or any("lineage-B" in x for x in parts):
            return "LineageB"
        elif "lineage-C-template" in parts or any("lineage-C" in x for x in parts):
            return "LineageC"
        return "Docs"  # Other dumpster-dive content

    if "mas_mcp" in parts:
        return "MCP"

    if "src" in parts and p.suffix == ".rs":
        return "Rust"

    if "scripts" in parts:
        return "Scripts"

    # DCRP scripts at root
    if p.name.startswith("decorator_cross_ref"):
        return "DCRP"

    # Markdown at root (SSOT/ANKH)
    if p.suffix == ".md" and len(parts) <= 2:
        return "Docs"

    return "DCRP"  # Default lane

def classify_language(path_str: str) -> Language:
    """Infer language from file extension."""
    suffix = Path(path_str).suffix.lower()
    lang_map = {
        ".py": "python",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "typescript",  # Treat JS as TS for simplicity
        ".jsx": "typescript",
        ".rs": "rust",
        ".md": "markdown",
        ".json": "json",
        ".toml": "toml",
        ".yml": "yaml",
        ".yaml": "yaml",
    }
    return lang_map.get(suffix, "other")

def infer_tier(path_str: str, role: Optional[str]) -> Optional[str]:
    """
    Infer tier from path or role.
    Tier 0.5: The Decorator (SSOT files)
    Tier 1: Triumvirate (core operational files)
    Tier 2: Prime Factions (specialized tools)
    Tier 3: Sub-MILFs (support utilities)
    """
    p = Path(path_str)

    # SSOT files = Tier 0.5
    if p.name in ["ankh.md", "ANKHOLOGY.md"] or str(p) == SSOT_POINTER:
        return "T0.5"

    # Core DCRP scripts = Tier 1
    if p.name.startswith("decorator_cross_ref") and p.suffix == ".py":
        return "T1"

    # MCP server = Tier 2 (specialized tooling)
    if "mas_mcp/server.py" in path_str:
        return "T2"

    # Scripts = Tier 3
    if "scripts/" in path_str:
        return "T3"

    return None

# ═══════════════════════════════════════════════════════════════════════════════
# GRAPH BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

class UnifiedTopologyBuilder:
    """Constructs the unified cross-lane dependency graph."""

    def __init__(self):
        self.graph = nx.DiGraph()
        self.dcrp_data: Optional[Dict] = None

    def load_dcrp_graph(self) -> None:
        """Load DCRP production graph as base layer."""
        dcrp_path = PROJECT_ROOT / "dependency_graph_production.json"
        if not dcrp_path.exists():
            print(f"⚠️  DCRP graph not found: {dcrp_path}")
            return

        with open(dcrp_path, "r", encoding="utf-8") as f:
            self.dcrp_data = json.load(f)

        # Add nodes from DCRP
        for node in self.dcrp_data.get("nodes", []):
            node_id = node["id"]
            lane = classify_lane(node_id)
            language = classify_language(node_id)
            tier = infer_tier(node_id, node.get("role"))

            meta = NodeMeta(
                path=node_id,
                lane=lane,
                language=language,
                tier=tier,
                prism_band=node.get("spectral_freq"),
                role=node.get("role"),
                exports_count=node.get("exports_count", 0)
            )
            self.graph.add_node(node_id, **asdict(meta))

        # Add edges from DCRP
        for link in self.dcrp_data.get("links", []):
            source = link["source"]
            target = link["target"]

            # Infer lane relation
            source_lane = self.graph.nodes[source]["lane"] if source in self.graph else "DCRP"
            target_lane = self.graph.nodes[target]["lane"] if target in self.graph else "DCRP"
            lane_rel = f"{source_lane}→{target_lane}" if source_lane != target_lane else None

            self.graph.add_edge(source, target, kind="import", lane_relation=lane_rel)

        print(f"✅ Loaded DCRP graph: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")

    def scan_mcp_bindings(self) -> None:
        """Detect MCP tool bindings to Python/TypeScript."""
        mcp_dir = PROJECT_ROOT / "mas_mcp"
        if not mcp_dir.exists():
            return

        # MCP server.py → other Python modules
        server_py = mcp_dir / "server.py"
        if server_py.exists():
            self._add_node_if_missing(str(server_py))

            # Simple heuristic: MCP server imports project-local modules
            for py_file in mcp_dir.rglob("*.py"):
                if py_file != server_py and "__pycache__" not in str(py_file):
                    self._add_node_if_missing(str(py_file))
                    self.graph.add_edge(
                        str(server_py),
                        str(py_file),
                        kind="tool_binding",
                        lane_relation="MCP→MCP"
                    )

        print(f"✅ Scanned MCP bindings: {self.graph.number_of_nodes()} nodes total")

    def scan_lineage_templates(self) -> None:
        """Detect lineage template references."""
        templates_dir = PROJECT_ROOT / "dumpster-dive" / "intake" / "templates"
        if not templates_dir.exists():
            return

        for template_dir in templates_dir.iterdir():
            if template_dir.is_dir() and template_dir.name.startswith("lineage-"):
                manifest = template_dir / "manifest.yml"
                main_md = template_dir / "main.md"

                if manifest.exists():
                    self._add_node_if_missing(str(manifest))

                if main_md.exists():
                    self._add_node_if_missing(str(main_md))

                    # Templates reference DCRP docs
                    if manifest.exists():
                        self.graph.add_edge(
                            str(main_md),
                            str(manifest),
                            kind="template_use",
                            lane_relation="Docs→Docs"
                        )

        print(f"✅ Scanned lineage templates: {self.graph.number_of_nodes()} nodes total")

    def scan_typescript_mcp_scripts(self) -> None:
        """Detect TypeScript MCP script dependencies."""
        scripts_dir = PROJECT_ROOT / "scripts"
        if not scripts_dir.exists():
            return

        mcp_scripts = list(scripts_dir.glob("mcp*.ts"))
        for script in mcp_scripts:
            self._add_node_if_missing(str(script))

            # Read imports from TypeScript file
            content = script.read_text(encoding="utf-8")
            import_pattern = re.compile(r'import\s+.*?\s+from\s+["\'](.+?)["\']')

            for match in import_pattern.finditer(content):
                import_path = match.group(1)

                # Resolve relative imports
                if import_path.startswith("."):
                    resolved = (script.parent / import_path).resolve()
                    if resolved.suffix == "":
                        # Try .ts extension
                        resolved = resolved.with_suffix(".ts")

                    if resolved.exists():
                        self._add_node_if_missing(str(resolved))
                        self.graph.add_edge(
                            str(script),
                            str(resolved),
                            kind="import",
                            lane_relation="Scripts→Scripts"
                        )

        print(f"✅ Scanned TypeScript MCP scripts: {self.graph.number_of_nodes()} nodes total")

    def _add_node_if_missing(self, path_str: str) -> None:
        """Add node to graph if not already present."""
        if path_str in self.graph:
            return

        lane = classify_lane(path_str)
        language = classify_language(path_str)
        tier = infer_tier(path_str, None)

        meta = NodeMeta(
            path=path_str,
            lane=lane,
            language=language,
            tier=tier
        )
        self.graph.add_node(path_str, **asdict(meta))

    def build(self) -> nx.DiGraph:
        """Execute all scan phases and return unified graph."""
        print("🌐 Building unified topology...")
        self.load_dcrp_graph()
        self.scan_mcp_bindings()
        self.scan_lineage_templates()
        self.scan_typescript_mcp_scripts()
        print(f"✅ Unified topology complete: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
        return self.graph

# ═══════════════════════════════════════════════════════════════════════════════
# EXPORT
# ═══════════════════════════════════════════════════════════════════════════════

def export_json(graph: nx.DiGraph, path: Path) -> None:
    """Export graph to JSON."""
    data = {
        "metadata": {
            "generated": datetime.utcnow().isoformat() + "Z",
            "nodes_count": graph.number_of_nodes(),
            "edges_count": graph.number_of_edges(),
        },
        "nodes": [
            {"id": n, **graph.nodes[n]}
            for n in graph.nodes
        ],
        "edges": [
            {"source": u, "target": v, **graph.edges[u, v]}
            for u, v in graph.edges
        ]
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"📄 Exported JSON: {path}")

def export_mermaid(graph: nx.DiGraph, path: Path) -> None:
    """Export graph to Mermaid diagram."""
    lines = ["# Unified Topology Map", "", "```mermaid", "graph LR"]

    # Group by lane for clarity
    lane_colors = {
        "DCRP": "#FF6B6B",
        "MCP": "#4ECDC4",
        "LineageA": "#95E1D3",
        "LineageB": "#F38181",
        "LineageC": "#AA96DA",
        "Rust": "#FCBAD3",
        "Scripts": "#A8D8EA",
        "Docs": "#FFE66D",
    }

    # Add style classes
    for lane, color in lane_colors.items():
        lines.append(f"  classDef {lane}Class fill:{color},stroke:#333,stroke-width:2px")

    # Add edges (limit to avoid massive diagram)
    edge_count = 0
    max_edges = 100
    for u, v, meta in graph.edges(data=True):
        if edge_count >= max_edges:
            lines.append("  %% ... (additional edges omitted for brevity)")
            break

        kind = meta.get("kind", "")
        u_short = Path(u).name
        v_short = Path(v).name
        lines.append(f'  "{u_short}" -->|{kind}| "{v_short}"')
        edge_count += 1

    lines.append("```")
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"🗺️  Exported Mermaid: {path}")

def export_summary(graph: nx.DiGraph, path: Path) -> None:
    """Export statistical summary."""
    from collections import Counter

    lanes = Counter(graph.nodes[n]["lane"] for n in graph.nodes)
    languages = Counter(graph.nodes[n]["language"] for n in graph.nodes)
    tiers = Counter(graph.nodes[n].get("tier") for n in graph.nodes if graph.nodes[n].get("tier"))
    edge_kinds = Counter(graph.edges[u, v]["kind"] for u, v in graph.edges)

    lines = [
        "# Unified Topology Summary",
        "",
        f"**Generated:** {datetime.utcnow().isoformat()}Z",
        f"**Total Nodes:** {graph.number_of_nodes()}",
        f"**Total Edges:** {graph.number_of_edges()}",
        "",
        "---",
        "",
        "## Lane Distribution",
        "",
        "| Lane | Node Count |",
        "|------|------------|",
    ]
    for lane, count in lanes.most_common():
        lines.append(f"| {lane} | {count} |")

    lines.extend([
        "",
        "## Language Distribution",
        "",
        "| Language | Node Count |",
        "|----------|------------|",
    ])
    for lang, count in languages.most_common():
        lines.append(f"| {lang} | {count} |")

    if tiers:
        lines.extend([
            "",
            "## Tier Distribution",
            "",
            "| Tier | Node Count |",
            "|------|------------|",
        ])
        for tier, count in sorted(tiers.items()):
            lines.append(f"| {tier} | {count} |")

    lines.extend([
        "",
        "## Edge Types",
        "",
        "| Kind | Edge Count |",
        "|------|------------|",
    ])
    for kind, count in edge_kinds.most_common():
        lines.append(f"| {kind} | {count} |")

    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"📊 Exported summary: {path}")

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    builder = UnifiedTopologyBuilder()
    graph = builder.build()

    # Export artifacts
    export_json(graph, PROJECT_ROOT / "topology_graph.json")
    export_mermaid(graph, PROJECT_ROOT / "topology_map.md")
    export_summary(graph, PROJECT_ROOT / "topology_summary.md")

    print("")
    print("🎯 Phase 1 Complete: Unified Topology Generated")
    print("")
    print("Next Steps:")
    print("  - Review topology_summary.md for lane/language distribution")
    print("  - Inspect topology_map.md for visual cross-lane dependencies")
    print("  - Use topology_graph.json for programmatic analysis")

if __name__ == "__main__":
    main()
