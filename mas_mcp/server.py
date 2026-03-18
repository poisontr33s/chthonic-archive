#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: server.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🏛️ THE HYPOSTYLE
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ mas_mcp/logic/governance.py
# ║   └─◄ mas_mcp/lib/gpu_probe.py
# ╚════════════════════════════════════════════════════════════════════════════

"""
server.py — M-P-W Router Server (Modularized).

@SID:           SERVER_MPW_ROUTER_V1
@Shabti:        Router
@Purpose:       Core MAS MCP gateway server. Routes entity analysis,
                governance policy, narrative drift, qualia alignment,
                and GPU probing via FastMCP.
"""

import logging
import sys
from pathlib import Path
from fastmcp import FastMCP

from mas_mcp.logic.resonance import ArchiveVault, LexiconFilter
from mas_mcp.logic.tools import (
    mas_scan_logic, mas_entity_deep_logic, mas_pulse_logic,
    mas_narrative_scan_logic, mas_qualia_check_logic,
    mas_validate_entity_logic
)
from mas_mcp.logic.governance import policy_check_logic
from mas_mcp.lib.gpu_probe import probe_gpu_capabilities

# Config
PROJECT_ROOT = Path(__file__).parent.parent

# Allow scripts/ imports (link_audit, scm_triage) to resolve from repo root
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.link_audit import build_collision_index, audit_file, scan_repo_markdown
from scripts.scm_triage import audit as scm_audit, generate_fix_recommendations
ARCHIVE_PATH = Path(__file__).parent / "archive_vault.json"
SSOT_PATH = PROJECT_ROOT / ".github" / "copilot-instructions.md"
MPW_SOURCE = PROJECT_ROOT / ".github" / "copilot-instructions-copy.md"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mas-mcp")

mcp = FastMCP("mas-mcp", instructions="MAS - Metadata-Persistence-Workspace")
VAULT = ArchiveVault(ARCHIVE_PATH)
LEXICON = LexiconFilter()

@mcp.tool()
def mas_narrative_scan(target: str = "."):
    """Calculates Cultural Drift against the SSOT Lexicon."""
    return mas_narrative_scan_logic(target, PROJECT_ROOT, SSOT_PATH)

@mcp.tool()
def mas_qualia_check(target: str):
    """Vets a text block or directory for canonical alignment (Phase 3 Gate)."""
    return mas_qualia_check_logic(target, PROJECT_ROOT)

@mcp.tool()
def mas_scan(target: str = "."):
    """Scan files for lexicon impulses, entity drift, and canonical alignment signals."""
    return mas_scan_logic(target, PROJECT_ROOT, LEXICON)

@mcp.tool()
def mas_pulse():
    """Report session pulse: entity status, drift alerts, MPW fingerprint, and recommendations."""
    return mas_pulse_logic(VAULT, MPW_SOURCE, LEXICON)

@mcp.tool()
def mas_gpu_probe():
    """Probe GPU capabilities: CUDA version, VRAM, driver, and compute features."""
    return probe_gpu_capabilities().to_dict()

@mcp.tool()
def mas_entity_deep(entity_name: str, context_lines: int = 5):
    """Deep-scan the archive for a named entity: proximity mentions, consolidated metrics, and cross-file analysis."""
    return mas_entity_deep_logic(entity_name, context_lines, PROJECT_ROOT)

@mcp.tool()
def mas_validate_entity(entity_name: str, expected_whr: float = None, expected_tier: int = None, expected_cup: str = None):
    """Validate an entity against expected metrics. Records fractures on mismatch, seals truths on full match."""
    return mas_validate_entity_logic(entity_name, expected_whr, expected_tier, expected_cup, PROJECT_ROOT, VAULT)

@mcp.tool()
def mas_policy_check(code: str):
    """Security policy gate: scan code for prohibited or guarded patterns (exec, eval, rm -rf, etc). Returns risk band."""
    return policy_check_logic(code)


@mcp.tool()
def mas_link_audit(target: str = "."):
    """Audit markdown link health: broken refs, ambiguous paths, basename collisions. Pass a file path or '.' for full repo scan."""
    collision_index = build_collision_index(PROJECT_ROOT)
    if target == ".":
        md_files = scan_repo_markdown(PROJECT_ROOT)
        results = []
        totals = {"total_links": 0, "ok": 0, "broken": 0, "ambiguous": 0}
        for f in md_files:
            r = audit_file(f, PROJECT_ROOT, collision_index)
            totals["total_links"] += r["total_links"]
            totals["ok"] += r["ok"]
            totals["broken"] += r["broken"]
            totals["ambiguous"] += r["ambiguous"]
            if r["issues"]:
                results.append({"file": str(f.relative_to(PROJECT_ROOT)), "issues": r["issues"]})
        return {**totals, "files_scanned": len(md_files), "files_with_issues": results}
    else:
        file_path = Path(target) if Path(target).is_absolute() else PROJECT_ROOT / target
        r = audit_file(file_path, PROJECT_ROOT, collision_index)
        return r


@mcp.tool()
def mas_workspace_health():
    """Root directory health audit: file hygiene, redundancy, versioning issues, and cleanup candidates."""
    # Lazy import — rootdir_health_audit hijacks sys.stdout on import (Windows UTF-8 shim)
    # which would break FastMCP's stdio transport if loaded at module level.
    from scripts.rootdir_health_audit import scan_directory, analyze_files, generate_json_report
    import json as _json
    files = scan_directory(PROJECT_ROOT)
    report = analyze_files(files)
    return _json.loads(generate_json_report(report))


@mcp.tool()
def mas_scm_triage():
    """Git working-tree triage: classify changes as signal/noise/ghost/mailbox, generate gitignore and cleanup recommendations."""
    result = scm_audit(PROJECT_ROOT, logger)
    recommendations = generate_fix_recommendations(result)
    return {"audit": result, "recommendations": recommendations}


def main():
    mcp.run()

if __name__ == "__main__":
    main()
