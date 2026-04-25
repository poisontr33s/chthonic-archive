"""OAI /v1/models endpoint — returns loaded model info."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter()


class ModelObject(BaseModel):
    id: str
    object: str = "model"
    owned_by: str = "tabby-modern"


class ModelList(BaseModel):
    object: str = "list"
    data: list[ModelObject]


@router.get("/models", response_model=ModelList)
async def list_models(request: Request) -> ModelList:
    state = request.app.state.model_state
    if state.loaded and state.model_name:
        return ModelList(data=[ModelObject(id=state.model_name)])
    return ModelList(data=[])
