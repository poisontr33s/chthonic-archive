"""
Allow running as: uv run python -m mas_mcp.scripts.abbrev <command>
"""
from .cli import main

if __name__ == "__main__":
    exit(main())
