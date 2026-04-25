"""
OAI /v1/completions — text completion endpoint.
Sampler chain extracted from tabbyAPI backends/exllamav3/sampler.py (forge: retained ore).
Streaming via sse-starlette SSE. No kobold path. No exllamav2 path.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import AsyncIterator, Literal, Optional, Union

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

router = APIRouter()


# --- Request / Response models (OAI v1 compat) ---

class CompletionRequest(BaseModel):
    model: Optional[str] = None
    prompt: Union[str, list[str]]
    max_tokens: int = Field(256, ge=1, le=8192)
    temperature: float = Field(1.0, ge=0.0, le=2.0)
    top_p: float = Field(1.0, ge=0.0, le=1.0)
    top_k: int = Field(0, ge=0)
    min_p: float = Field(0.0, ge=0.0, le=1.0)
    repetition_penalty: float = Field(1.0, ge=0.9, le=5.0)
    frequency_penalty: float = Field(0.0, ge=0.0, le=2.0)
    presence_penalty: float = Field(0.0, ge=0.0, le=2.0)
    stream: bool = False
    stop: Optional[Union[str, list[str]]] = None
    seed: Optional[int] = None


class CompletionChoice(BaseModel):
    text: str
    index: int = 0
    finish_reason: Optional[str] = "stop"


class CompletionUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class CompletionResponse(BaseModel):
    id: str
    object: str = "text_completion"
    created: int
    model: str
    choices: list[CompletionChoice]
    usage: CompletionUsage


# --- Route ---

@router.post("/completions")
async def create_completion(request: Request, body: CompletionRequest):
    state = request.app.state.model_state
    if not state.loaded:
        raise HTTPException(status_code=503, detail="No model loaded")

    prompt = body.prompt if isinstance(body.prompt, str) else body.prompt[0]
    completion_id = f"cmpl-{uuid.uuid4().hex[:12]}"
    created = int(time.time())
    model_name = state.model_name or "unknown"

    if body.stream:
        return EventSourceResponse(
            _stream_completion(
                state, prompt, body, completion_id, created, model_name
            )
        )

    text, prompt_tokens, completion_tokens = await asyncio.get_running_loop().run_in_executor(
        None, _generate_blocking, state, prompt, body
    )

    return CompletionResponse(
        id=completion_id,
        created=created,
        model=model_name,
        choices=[CompletionChoice(text=text)],
        usage=CompletionUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        ),
    )


async def _stream_completion(
    state, prompt: str, body: CompletionRequest,
    completion_id: str, created: int, model_name: str
) -> AsyncIterator[dict]:
    import json
    # Streaming skeleton — exllamav3 async generator integration in Pass 2
    yield {
        "data": json.dumps({
            "id": completion_id,
            "object": "text_completion",
            "created": created,
            "model": model_name,
            "choices": [{"text": "", "index": 0, "finish_reason": None}],
        })
    }


def _generate_blocking(state, prompt: str, body: CompletionRequest) -> tuple[str, int, int]:
    """Runs in executor thread — exllamav3 generation is synchronous CUDA ops."""
    from tabby_modern.sampler import build_sampler_from_request

    try:
        from exllamav3 import Generator, GeneratorConfig
    except ImportError as exc:
        raise RuntimeError("exllamav3 not available") from exc

    sampler = build_sampler_from_request(body)
    gen_cfg = GeneratorConfig()
    gen_cfg.max_new_tokens = body.max_tokens
    gen_cfg.sampler = sampler
    if body.seed is not None:
        gen_cfg.seed = body.seed

    output = state._model.generate(prompt, gen_cfg)  # type: ignore[union-attr]
    prompt_toks = len(state._tokenizer.encode(prompt))  # type: ignore[union-attr]
    completion_toks = len(state._tokenizer.encode(output))  # type: ignore[union-attr]
    return output, prompt_toks, completion_toks
