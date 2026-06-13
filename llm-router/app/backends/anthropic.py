"""Anthropic Messages API backend adapter.

POST /v1/messages, SSE for streaming. System messages are hoisted to the
top-level `system` field (Anthropic requires this); remaining messages keep
their user/assistant roles."""
from __future__ import annotations

import json
import logging
from typing import AsyncIterator

import httpx

from config import Backend
from backends.base import ChatRequest, ChatChunk, ChatResult, BackendError

logger = logging.getLogger("llm-router.backend.anthropic")

ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MAX_TOKENS = 1024


def _headers(backend: Backend) -> dict:
    return {
        "Content-Type": "application/json",
        "x-api-key": backend.api_key or "",
        "anthropic-version": ANTHROPIC_VERSION,
    }


def _split_system(messages: list[dict]) -> tuple[str, list[dict]]:
    system_parts, rest = [], []
    for m in messages:
        if m.get("role") == "system":
            system_parts.append(m.get("content", ""))
        else:
            rest.append({"role": m["role"], "content": m.get("content", "")})
    return "\n\n".join(p for p in system_parts if p), rest


def _payload(req: ChatRequest, stream: bool) -> dict:
    system, msgs = _split_system(req.messages)
    body: dict = {
        "model": req.model,
        "messages": msgs,
        "max_tokens": req.max_tokens or DEFAULT_MAX_TOKENS,
        "temperature": req.temperature,
        "stream": stream,
    }
    if system:
        body["system"] = system
    if req.top_p is not None:
        body["top_p"] = req.top_p
    return body


async def chat(backend: Backend, req: ChatRequest) -> ChatResult:
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            r = await client.post(f"{backend.url}/v1/messages",
                                  headers=_headers(backend), json=_payload(req, False))
            r.raise_for_status()
            data = r.json()
    except Exception as exc:
        raise BackendError(f"anthropic {backend.name} chat failed: {exc}")
    parts = data.get("content") or []
    text = "".join(p.get("text", "") for p in parts if p.get("type") == "text")
    usage = data.get("usage", {}) or {}
    return ChatResult(
        content=text,
        finish_reason=data.get("stop_reason") or "stop",
        model=data.get("model", req.model),
        prompt_tokens=usage.get("input_tokens"),
        completion_tokens=usage.get("output_tokens"),
    )


async def stream(backend: Backend, req: ChatRequest) -> AsyncIterator[ChatChunk]:
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream("POST", f"{backend.url}/v1/messages",
                                     headers=_headers(backend),
                                     json=_payload(req, True)) as r:
                r.raise_for_status()
                async for line in r.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[len("data:"):].strip()
                    if not data:
                        continue
                    try:
                        obj = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    etype = obj.get("type")
                    if etype == "content_block_delta":
                        delta = (obj.get("delta") or {}).get("text") or ""
                        if delta:
                            yield ChatChunk(delta=delta, done=False)
                    elif etype == "message_delta":
                        sr = (obj.get("delta") or {}).get("stop_reason")
                        if sr:
                            yield ChatChunk(delta="", done=True, finish_reason=sr)
                            return
                    elif etype == "message_stop":
                        yield ChatChunk(delta="", done=True, finish_reason="stop")
                        return
    except Exception as exc:
        raise BackendError(f"anthropic {backend.name} stream failed: {exc}")
