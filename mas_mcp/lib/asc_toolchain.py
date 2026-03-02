#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: asc_toolchain.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🏰 THE FORTRESS
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
ASC Toolchain Router
Redirects to the modularized logic in mas_mcp/lib/asc/

@SID:           TOOL_ASC_TOOLCHAIN_V1
@Shabti:        CLI Script
@Purpose:       ASC Toolchain Router
"""

import sys
from pathlib import Path

# Add project root to sys.path to allow imports from any directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# Import the modularized app
try:
    from mas_mcp.lib.asc.cli import app
except ImportError:
    # Fallback for different execution contexts
    from lib.asc.cli import app

if __name__ == "__main__":
    app()
