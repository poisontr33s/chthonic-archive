#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: server.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🏛️ THE HYPOSTYLE
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ mas_mcp/lib/ssot_handler.py
# ║   └─◄ mas_mcp/lib/gpu_probe.py
# ╚════════════════════════════════════════════════════════════════════════════

"""
server.py — M-P-W Router Server (Modularized).

@SID:           SERVER_MPW_ROUTER_V1
@Shabti:        Router
@Purpose:       Core MAS MCP gateway server. Routes archive vault, entity,
                pulse, narrative, and qualia operations via FastMCP.
                Integrates SSOT hash verification and GPU probing.
"""

import logging
from pathlib import Path
from fastmcp import FastMCP

from mas_mcp.logic.resonance import ArchiveVault, LexiconFilter
from mas_mcp.logic.tools import (
    mas_scan_logic, mas_entity_deep_logic, mas_pulse_logic,
    mas_narrative_scan_logic, mas_qualia_check_logic
)
from mas_mcp.lib.ssot_handler import verify_bookend
from mas_mcp.lib.gpu_probe import probe_gpu_capabilities

# Config
PROJECT_ROOT = Path(__file__).parent.parent
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
def mas_bookend_verify(hash_start: str):
    """Verify SSOT integrity by comparing a session-start hash against current state. Detects governance drift."""
    is_consistent, hash_end = verify_bookend(hash_start)
    return {
        "consistent": is_consistent,
        "hash_start": hash_start,
        "hash_end": hash_end,
        "status": "SSOT_CONSISTENT" if is_consistent else "GOVERNANCE_DRIFT_DETECTED"
    }


def main():
    mcp.run()

if __name__ == "__main__":
    main()
