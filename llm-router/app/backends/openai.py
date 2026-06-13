"""OpenAI-compatible backend adapter (OpenAI, x.ai/Grok, OpenRouter, Together).

Speaks POST /v1/chat/completions, SSE for streaming."""
from __future__ import annotations

import json
import logging
from typing import AsyncIterator

import httpx

from config import Backend
from backends.base import ChatRequest, ChatChunk, ChatResult, BackendError

logger = logging.getLogger("llm-router.backend.openai")


def _headers(backend: Backend) -> dict:
    h = {"Content-Type": "application/json"}
    if backend.api_key:
        h["Authorization"] = f"Bearer {backend.api_key}"
    return h


def _payload(req: ChatRequest, stream: bool) -> dict:
    body: dict = {
        "model": req.model,
        "messages": req.messages,
        "temperature": req.temperature,
        "stream": stream,
    }
    if req.max_tokens is not None:
        body["max_tokens"] = req.max_tokens
    if req.top_p is not None:
        body["top_p"] = req.top_p
    if req.json_mode:
        body["response_format"] = {"type": "json_object"}
    return body


async def chat(backend: Backend, req: ChatRequest) -> ChatResult:
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            r = await client.post(f"{backend.url}/chat/completions",
                                  headers=_headers(backend), json=_payload(req, False))
            r.raise_for_status()
            data = r.json()
    except Exception as exc:
        raise BackendError(f"openai-compat {backend.name} chat failed: {exc}")
    choice = (data.get("choices") or [{}])[0]
    msg = choice.get("message", {}) or {}
    usage = data.get("usage", {}) or {}
    return ChatResult(
        content=msg.get("content", "") or "",
        finish_reason=choice.get("finish_reason") or "stop",
        model=data.get("model", req.model),
        prompt_tokens=usage.get("prompt_tokens"),
        completion_tokens=usage.get("completion_tokens"),
    )


async def stream(backend: Backend, req: ChatRequest) -> AsyncIterator[ChatChunk]:
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream("POST", f"{backend.url}/chat/completions",
                                     headers=_headers(backend),
                                     json=_payload(req, True)) as r:
                r.raise_for_status()
                async for line in r.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[len("data:"):].strip()
                    if data == "[DONE]":
                        yield ChatChunk(delta="", done=True, finish_reason="stop")
                        return
                    try:
                        obj = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    choice = (obj.get("choices") or [{}])[0]
                    delta = (choice.get("delta") or {}).get("content") or ""
                    fr = choice.get("finish_reason")
                    if delta:
                        yield ChatChunk(delta=delta, done=False)
                    if fr:
                        yield ChatChunk(delta="", done=True, finish_reason=fr)
                        return
    except Exception as exc:
        raise BackendError(f"openai-compat {backend.name} stream failed: {exc}")
