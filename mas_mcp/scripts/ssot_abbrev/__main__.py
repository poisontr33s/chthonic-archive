#!/usr/bin/env python3
#-*- coding: utf-8 -*-
"""
SSOT Abbreviation System — Module entry point.

Allows running as: uv run python -m mas_mcp.scripts.ssot_abbrev [command]
"""

from .cli import main

if __name__ == "__main__":
    main()
