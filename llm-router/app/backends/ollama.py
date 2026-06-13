"""Ollama backend adapter — /api/chat with stream=true (ndjson) or false."""
from __future__ import annotations

import json
import logging
from typing import AsyncIterator

import httpx

from config import Backend
from backends.base import ChatRequest, ChatChunk, ChatResult, BackendError

logger = logging.getLogger("llm-router.backend.ollama")


def _payload(req: ChatRequest, stream: bool) -> dict:
    options: dict = {"temperature": req.temperature}
    if req.max_tokens is not None:
        options["num_predict"] = req.max_tokens
    if req.top_p is not None:
        options["top_p"] = req.top_p
    body: dict = {
        "model": req.model,
        "messages": req.messages,
        "stream": stream,
        "options": options,
    }
    if req.json_mode:
        body["format"] = "json"
    return body


async def chat(backend: Backend, req: ChatRequest) -> ChatResult:
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            r = await client.post(f"{backend.url}/api/chat", json=_payload(req, False))
            if r.status_code == 404:
                raise BackendError(f"model {req.model} not present on {backend.name}", 404)
            r.raise_for_status()
            data = r.json()
    except BackendError:
        raise
    except Exception as exc:
        raise BackendError(f"ollama {backend.name} chat failed: {exc}")
    msg = data.get("message", {}) or {}
    content = msg.get("content", "") or ""
    # Thinking models (qwen3) emit reasoning into message.thinking and only fill
    # message.content once they finish. If a tight num_predict truncated the run
    # before the answer, content is empty — surface the thinking so the caller
    # isn't handed a silent blank, and flag it via finish_reason.
    finish = data.get("done_reason") or "stop"
    if not content and msg.get("thinking"):
        content = msg["thinking"]
        finish = "length_thinking_truncated"
    return ChatResult(
        content=content,
        finish_reason=finish,
        model=req.model,
        prompt_tokens=data.get("prompt_eval_count"),
        completion_tokens=data.get("eval_count"),
    )


async def stream(backend: Backend, req: ChatRequest) -> AsyncIterator[ChatChunk]:
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream("POST", f"{backend.url}/api/chat",
                                     json=_payload(req, True)) as r:
                if r.status_code == 404:
                    raise BackendError(f"model {req.model} not present on {backend.name}", 404)
                r.raise_for_status()
                async for line in r.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    msg = obj.get("message", {}) or {}
                    # Prefer answer content; if only thinking is streaming, pass
                    # that through too so a truncated thinking model still streams
                    # something rather than an empty body.
                    piece = (msg.get("content") or "") or (msg.get("thinking") or "")
                    done = bool(obj.get("done"))
                    if piece:
                        yield ChatChunk(delta=piece, done=False)
                    if done:
                        yield ChatChunk(delta="", done=True,
                                        finish_reason=obj.get("done_reason") or "stop")
                        return
    except BackendError:
        raise
    except Exception as exc:
        raise BackendError(f"ollama {backend.name} stream failed: {exc}")
