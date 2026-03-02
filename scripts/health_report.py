#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: health_report.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
📊 HEALTH REPORT GENERATOR
═══════════════════════════════════════════════════════════════════════════════

Ritual Health Report Generator - The Heartbeat of the Archive
Produces comprehensive health reports with:
  - Lane status
  - Topology metrics
  - SSOT integrity
  - Recommended actions

Usage:
    uv run python health_report.py

Output:
    health_reports/HEALTH_REPORT_{timestamp}.md

═══════════════════════════════════════════════════════════════════════════════

@SID:           TOOL_HEALTH_REPORT_V1
@Shabti:        CLI Script
@Purpose:       📊 HEALTH REPORT GENERATOR
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


from __future__ import annotations
from pathlib import Path
import datetime
import json
import subprocess
from typing import Dict, Optional

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

PROJECT_ROOT = Path(__file__).parent
HEALTH_REPORTS_DIR = PROJECT_ROOT / "health_reports"
TOPOLOGY_GRAPH = PROJECT_ROOT / "topology_graph.json"
SSOT_STATE = PROJECT_ROOT / ".dcrp_state.json"
DCRP_GRAPH = PROJECT_ROOT / "dependency_graph_production.json"

# ═══════════════════════════════════════════════════════════════════════════════
# DATA COLLECTION
# ═══════════════════════════════════════════════════════════════════════════════

def get_current_commit() -> str:
    """Get current git commit hash."""
    try:
        result = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=PROJECT_ROOT,
            stderr=subprocess.DEVNULL
        )
        return result.decode().strip()
    except Exception:
        return "UNKNOWN"

def get_current_branch() -> str:
    """Get current git branch."""
    try:
        result = subprocess.check_output(
            ["git", "branch", "--show-current"],
            cwd=PROJECT_ROOT,
            stderr=subprocess.DEVNULL
        )
        return result.decode().strip()
    except Exception:
        return "UNKNOWN"

def summarize_topology() -> Dict:
    """Extract summary metrics from topology graph."""
    if not TOPOLOGY_GRAPH.exists():
        return {"nodes": 0, "edges": 0, "lanes": {}}

    try:
        data = json.loads(TOPOLOGY_GRAPH.read_text(encoding="utf-8"))

        # Count lanes
        lane_counts = {}
        for node in data.get("nodes", []):
            lane = node.get("lane", "Unknown")
            lane_counts[lane] = lane_counts.get(lane, 0) + 1

        return {
            "nodes": len(data.get("nodes", [])),
            "edges": len(data.get("edges", [])),
            "lanes": lane_counts
        }
    except Exception:
        return {"nodes": 0, "edges": 0, "lanes": {}}

def summarize_dcrp() -> Dict:
    """Extract summary metrics from DCRP graph."""
    if not DCRP_GRAPH.exists():
        return {"files_analyzed": 0, "dependencies": 0}

    try:
        data = json.loads(DCRP_GRAPH.read_text(encoding="utf-8"))
        return {
            "files_analyzed": len(data.get("nodes", [])),
            "dependencies": len(data.get("links", []))
        }
    except Exception:
        return {"files_analyzed": 0, "dependencies": 0}

def check_ssot_status() -> Dict:
    """Check SSOT hash verification status."""
    if not SSOT_STATE.exists():
        return {"status": "NOT_INITIALIZED", "files_monitored": 0}

    try:
        state = json.loads(SSOT_STATE.read_text(encoding="utf-8"))
        hashes = state.get("ssot_hashes", {})
        last_verified = state.get("last_verified", "NEVER")

        return {
            "status": "OPERATIONAL",
            "files_monitored": len(hashes),
            "last_verified": last_verified
        }
    except Exception:
        return {"status": "ERROR", "files_monitored": 0}

def check_lane_population() -> Dict:
    """Check if lineage lanes are populated."""
    templates_dir = PROJECT_ROOT / "dumpster-dive" / "intake" / "templates"
    lanes = {}

    for lineage in ["lineage-A-template", "lineage-B-template", "lineage-C-template"]:
        template_dir = templates_dir / lineage
        manifest = template_dir / "manifest.yml"

        if not manifest.exists():
            lanes[lineage] = "MISSING"
        else:
            content = manifest.read_text(encoding="utf-8")
            if "shortname" in content or "Your Name" in content:
                lanes[lineage] = "AWAITING_POPULATION"
            else:
                lanes[lineage] = "POPULATED"

    return lanes

# ═══════════════════════════════════════════════════════════════════════════════
# REPORT GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def generate_health_report() -> None:
    """Generate comprehensive health report."""
    timestamp = datetime.datetime.now(datetime.UTC).replace(microsecond=0).isoformat().replace(":", "-")
    commit = get_current_commit()
    branch = get_current_branch()
    topo = summarize_topology()
    dcrp = summarize_dcrp()
    ssot = check_ssot_status()
    lanes = check_lane_population()

    # Determine overall health
    health_checks = [
        topo["nodes"] > 0,
        dcrp["files_analyzed"] > 0,
        ssot["status"] == "OPERATIONAL",
    ]
    overall_healthy = all(health_checks)
    overall_status = "✅ HEALTHY" if overall_healthy else "⚠️ NEEDS ATTENTION"

    # Generate report
    HEALTH_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = HEALTH_REPORTS_DIR / f"HEALTH_REPORT_{timestamp}.md"

    lines = [
        "# 🏥 CHTHONIC ARCHIVE HEALTH REPORT",
        "",
        f"**Generated:** {datetime.datetime.now(datetime.UTC).replace(microsecond=0).isoformat()}Z",
        f"**Commit:** {commit}",
        f"**Branch:** {branch}",
        f"**Status:** {overall_status}",
        "",
        "---",
        "",
        "## Repository Metrics",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Topology Nodes | {topo['nodes']} |",
        f"| Topology Edges | {topo['edges']} |",
        f"| DCRP Files Analyzed | {dcrp['files_analyzed']} |",
        f"| DCRP Dependencies | {dcrp['dependencies']} |",
        "",
        "---",
        "",
        "## Lane Status",
        "",
        "| Lane | Status | Details |",
        "|------|--------|---------|",
    ]

    # Topology lane breakdown
    for lane, count in topo.get("lanes", {}).items():
        lines.append(f"| {lane} | ✅ OPERATIONAL | {count} nodes |")

    # Lineage template status
    for lineage, status in lanes.items():
        lineage_name = lineage.replace("-template", "").replace("-", " ").title()
        if status == "AWAITING_POPULATION":
            lines.append(f"| {lineage_name} | ⚠️ AWAITING POPULATION | Templates ready |")
        elif status == "POPULATED":
            lines.append(f"| {lineage_name} | ✅ POPULATED | Active |")
        else:
            lines.append(f"| {lineage_name} | ❌ MISSING | Template not found |")

    lines.extend([
        "",
        "---",
        "",
        "## SSOT Integrity",
        "",
    ])

    if ssot["status"] == "OPERATIONAL":
        lines.append(f"- **Status:** ✅ {ssot['status']}")
        lines.append(f"- **Files Monitored:** {ssot['files_monitored']}")
        lines.append(f"- **Last Verified:** {ssot.get('last_verified', 'NEVER')}")
    elif ssot["status"] == "NOT_INITIALIZED":
        lines.append("- **Status:** ⚠️ NOT INITIALIZED")
        lines.append("- **Action Required:** Run `uv run python ssot_immunity.py` to initialize baseline")
    else:
        lines.append(f"- **Status:** ❌ {ssot['status']}")

    lines.extend([
        "",
        "---",
        "",
        "## Recommended Actions",
        "",
    ])

    # Generate recommendations
    recommendations = []

    if ssot["status"] == "NOT_INITIALIZED":
        recommendations.append("1. Initialize SSOT baseline: `uv run python ssot_immunity.py`")

    if lanes.get("lineage-A-template") == "AWAITING_POPULATION":
        recommendations.append("2. Populate Lineage A templates (awaiting sovereign input)")

    if topo["nodes"] == 0:
        recommendations.append("3. Generate unified topology: `uv run python unified_topology.py`")

    if dcrp["files_analyzed"] == 0:
        recommendations.append("4. Generate DCRP graph: `uv run python decorator_cross_ref_production.py`")

    if not recommendations:
        recommendations.append("✅ No immediate actions required - all systems operational")

    for rec in recommendations:
        lines.append(rec)

    lines.extend([
        "",
        "---",
        "",
        "## Next Scheduled Operations",
        "",
        "- **DCRP Regeneration:** On next commit (via autonomous_coordinator.py)",
        "- **Topology Update:** On next commit (via autonomous_coordinator.py)",
        "- **SSOT Verification:** On next commit (via autonomous_coordinator.py)",
        "- **Health Report:** On next commit (via autonomous_coordinator.py)",
    ])

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"📊 Health report generated: {report_path.name}")

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    """CLI entry point."""
    print("📊 Generating health report...")
    generate_health_report()
    print("✅ Complete")

if __name__ == "__main__":
    main()
