"""
tabby-modern app — FastAPI lifespan (no deprecated startup/shutdown events).
No model loading at import time. No global mutable state outside context vars.
"""

from __future__ import annotations

import asyncio
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from loguru import logger

from tabby_modern.settings import settings
from tabby_modern.state import ModelState


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Server lifespan: configure logger → optionally load startup model → yield → teardown."""
    _configure_logger()
    logger.info("tabby-modern starting — Python {}", sys.version.split()[0])
    logger.info("network: {}:{}", settings.network.host, settings.network.port)

    state: ModelState = app.state.model_state
    if settings.model.model_name:
        logger.info("autoload: {}", settings.model.model_name)
        model_path = settings.model.model_dir / settings.model.model_name
        await state.load(model_path)

    yield

    if state.loaded:
        logger.info("shutdown: unloading model")
        await state.unload()
    logger.info("tabby-modern stopped")


def create_app() -> FastAPI:
    """Application factory — safe to call multiple times (test isolation)."""
    from tabby_modern.api import completions, chat, models, health
    from tabby_modern.state import ModelState

    app = FastAPI(
        title="tabby-modern",
        description="Modern GPU inference host — exllamav3 / Python 3.14 / uv",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Attach model state to app (not to a module global)
    app.state.model_state = ModelState()

    # OAI-compatible surface
    app.include_router(health.router, tags=["health"])
    app.include_router(models.router, prefix="/v1", tags=["models"])
    app.include_router(completions.router, prefix="/v1", tags=["completions"])
    app.include_router(chat.router, prefix="/v1", tags=["chat"])

    return app


def _configure_logger() -> None:
    logger.remove()
    fmt = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{line}</cyan> — <level>{message}</level>"
    )
    logger.add(sys.stderr, format=fmt, colorize=True, level="INFO")
