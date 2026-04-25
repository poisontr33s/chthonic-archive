"""
tabby-modern entry point — python -m tabby_modern

Sets PYTORCH_CUDA_ALLOC_CONF before any torch import (must be process-level, not torch-level).
Then hands off to uvicorn. Container pattern: $PORT / $HOST env vars override settings.
"""

from __future__ import annotations

import os
import sys


def main() -> None:
    # Must precede any torch / CUDA import or it has no effect.
    # cudaMallocAsync: async memory pool — reduces fragmentation on long inference sessions.
    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "backend:cudaMallocAsync")

    from tabby_modern.settings import Settings
    settings = Settings.from_env()

    # Container overrides via raw env vars (docker -e PORT=8080)
    host = os.environ.get("HOST", settings.network.host)
    port = int(os.environ.get("PORT", settings.network.port))

    import uvicorn

    # uvloop is the event loop policy on Linux x86_64 (container deployment)
    loop_policy: str
    if sys.platform == "linux" and os.uname().machine == "x86_64":
        try:
            import uvloop  # noqa: F401
            loop_policy = "uvloop"
        except ImportError:
            loop_policy = "asyncio"
    else:
        loop_policy = "asyncio"

    uvicorn.run(
        "tabby_modern.app:create_app",
        factory=True,
        host=host,
        port=port,
        loop=loop_policy,
        http="httptools",
        log_level="info",
        access_log=False,  # loguru handles structured logging
    )


if __name__ == "__main__":
    main()
