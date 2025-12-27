"""Entry point for `python -m mas_mcp` (when `mas_mcp/` is importable).

Practical note (uv): if you run with `uv run --directory mas_mcp ...`, your
working directory becomes `mas_mcp/`, so the importable module is `server`
(use `python -m server`).
"""

from .server import main

if __name__ == "__main__":
    main()
