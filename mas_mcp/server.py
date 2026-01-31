#!/usr/bin/env python3

"""
@SID: SERVER_MPW_ROUTER_V1
@Type: Core Gateway
@Context: M-P-W Router Server (Modularized)
"""

import logging
from pathlib import Path
from fastmcp import FastMCP

from mas_mcp.logic.resonance import ArchiveVault, LexiconFilter
from mas_mcp.logic.tools import (
    mas_scan_logic, mas_entity_deep_logic, mas_pulse_logic,
    mas_narrative_scan_logic, mas_qualia_check_logic
)
from mas_mcp.lib.ssot_handler import compute_ssot_hash, get_ssot_path, verify_bookend
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
def mas_ssot_hash():
    return {"hash": compute_ssot_hash(get_ssot_path())}

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
    return mas_scan_logic(target, PROJECT_ROOT, LEXICON)

@mcp.tool()
def mas_pulse():
    return mas_pulse_logic(VAULT, MPW_SOURCE, LEXICON)

@mcp.tool()
def mas_gpu_probe():
    return probe_gpu_capabilities().to_dict()

# ... other tools would be registered here ...

def main():
    mcp.run()

if __name__ == "__main__":
    main()
