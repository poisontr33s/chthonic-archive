#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0",
#     "pydantic>=2.0",
#     "typer>=0.12",
# ]
# ///
"""
ASC Toolchain Router
Redirects to the modularized logic in mas_mcp/lib/asc/
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
