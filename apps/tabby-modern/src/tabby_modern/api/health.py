"""Health + readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_name: str | None


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    from tabby_modern.app import create_app  # avoid circular — state via request

    # In practice this is injected via request.app.state — kept simple for P-09 import gate
    return HealthResponse(status="ok", model_loaded=False, model_name=None)


@router.get("/health/ready")
async def ready() -> dict[str, str]:
    return {"status": "ready"}
