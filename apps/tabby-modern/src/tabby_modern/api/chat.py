"""
OAI /v1/chat/completions — chat completion endpoint.
Template rendering via Jinja2 (extracted from tabbyAPI common/templating.py).
No kobold path. No exllamav2 path. exllamav3-native.
"""

from __future__ import annotations

import time
import uuid
from typing import Literal, Optional, Union

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter()


# --- OAI chat types ---

class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str


class ChatCompletionRequest(BaseModel):
    model: Optional[str] = None
    messages: list[ChatMessage]
    max_tokens: int = Field(256, ge=1, le=8192)
    temperature: float = Field(1.0, ge=0.0, le=2.0)
    top_p: float = Field(1.0, ge=0.0, le=1.0)
    top_k: int = Field(0, ge=0)
    min_p: float = Field(0.0, ge=0.0, le=1.0)
    repetition_penalty: float = Field(1.0, ge=0.9, le=5.0)
    stream: bool = False
    seed: Optional[int] = None


class ChatChoice(BaseModel):
    index: int = 0
    message: ChatMessage
    finish_reason: str = "stop"


class ChatUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatChoice]
    usage: ChatUsage


# --- Route ---

@router.post("/chat/completions")
async def create_chat_completion(request: Request, body: ChatCompletionRequest):
    state = request.app.state.model_state
    if not state.loaded:
        raise HTTPException(status_code=503, detail="No model loaded")

    prompt = _render_chat_template(body.messages)

    import asyncio
    from tabby_modern.api.completions import _generate_blocking, CompletionRequest

    compat = CompletionRequest(
        prompt=prompt,
        max_tokens=body.max_tokens,
        temperature=body.temperature,
        top_p=body.top_p,
        top_k=body.top_k,
        min_p=body.min_p,
        repetition_penalty=body.repetition_penalty,
        stream=False,
        seed=body.seed,
    )

    text, prompt_toks, completion_toks = await asyncio.get_running_loop().run_in_executor(
        None, _generate_blocking, state, prompt, compat
    )

    completion_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    return ChatCompletionResponse(
        id=completion_id,
        created=int(time.time()),
        model=state.model_name or "unknown",
        choices=[ChatChoice(message=ChatMessage(role="assistant", content=text))],
        usage=ChatUsage(
            prompt_tokens=prompt_toks,
            completion_tokens=completion_toks,
            total_tokens=prompt_toks + completion_toks,
        ),
    )


def _render_chat_template(messages: list[ChatMessage]) -> str:
    """
    Minimal chat template rendering — Jinja2 ChatML format.
    Full model-card template loading (exllamav3 tokenizer.chat_template) in Pass 2.
    """
    parts: list[str] = []
    for msg in messages:
        parts.append(f"<|im_start|>{msg.role}\n{msg.content}<|im_end|>")
    parts.append("<|im_start|>assistant\n")
    return "\n".join(parts)
