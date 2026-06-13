"""
Client-facing serialization.

Inbound: parse an OpenAI-style or ollama-style request body into a normalized
ChatRequest (the `model` field carries the capability/logical name).

Outbound: re-serialize normalized ChatResult / ChatChunk streams back into the
dialect the client used, so existing show-build code (providers.js OpenAI path,
ollama_resolver.py ollama path) works unchanged against the router.
"""
from __future__ import annotations

import json
import time
from typing import Any

from backends.base import ChatRequest, ChatResult, ChatChunk

# Deterministic-ish id/timestamp without Date.now-style nondeterminism concerns
# (these run server-side per request; real clock is fine here).


def _now() -> int:
    return int(time.time())


# ---------- inbound parsing -------------------------------------------------

def parse_openai(body: dict) -> ChatRequest:
    return ChatRequest(
        model=body.get("model", ""),
        messages=body.get("messages", []),
        temperature=float(body.get("temperature", 0.2)),
        max_tokens=body.get("max_tokens"),
        top_p=body.get("top_p"),
        json_mode=(body.get("response_format", {}) or {}).get("type") == "json_object",
        stream=bool(body.get("stream", False)),
        extra={},
    )


def parse_ollama_chat(body: dict) -> ChatRequest:
    opts = body.get("options", {}) or {}
    return ChatRequest(
        model=body.get("model", ""),
        messages=body.get("messages", []),
        temperature=float(opts.get("temperature", 0.2)),
        max_tokens=opts.get("num_predict"),
        top_p=opts.get("top_p"),
        json_mode=body.get("format") == "json",
        stream=bool(body.get("stream", True)),  # ollama defaults stream=true
        extra={},
    )


def parse_ollama_generate(body: dict) -> ChatRequest:
    opts = body.get("options", {}) or {}
    messages = []
    if body.get("system"):
        messages.append({"role": "system", "content": body["system"]})
    messages.append({"role": "user", "content": body.get("prompt", "")})
    return ChatRequest(
        model=body.get("model", ""),
        messages=messages,
        temperature=float(opts.get("temperature", 0.2)),
        max_tokens=opts.get("num_predict"),
        top_p=opts.get("top_p"),
        json_mode=body.get("format") == "json",
        stream=bool(body.get("stream", True)),
        extra={"generate_mode": True},
    )


# ---------- outbound: OpenAI dialect ---------------------------------------

def openai_result(res: ChatResult, requested_model: str) -> dict:
    return {
        "id": f"chatcmpl-router-{_now()}",
        "object": "chat.completion",
        "created": _now(),
        "model": requested_model,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": res.content},
            "finish_reason": res.finish_reason,
        }],
        "usage": {
            "prompt_tokens": res.prompt_tokens or 0,
            "completion_tokens": res.completion_tokens or 0,
            "total_tokens": (res.prompt_tokens or 0) + (res.completion_tokens or 0),
        },
        "x_router": {"backend_model": res.model},
    }


def openai_stream_chunk(chunk: ChatChunk, requested_model: str) -> str:
    obj = {
        "id": f"chatcmpl-router-{_now()}",
        "object": "chat.completion.chunk",
        "created": _now(),
        "model": requested_model,
        "choices": [{
            "index": 0,
            "delta": ({} if chunk.done else {"content": chunk.delta}),
            "finish_reason": chunk.finish_reason if chunk.done else None,
        }],
    }
    return f"data: {json.dumps(obj)}\n\n"


def openai_stream_done() -> str:
    return "data: [DONE]\n\n"


# ---------- outbound: ollama dialect ---------------------------------------

def ollama_result(res: ChatResult, requested_model: str, generate_mode: bool) -> dict:
    if generate_mode:
        return {
            "model": requested_model,
            "created_at": "",
            "response": res.content,
            "done": True,
            "done_reason": res.finish_reason,
            "prompt_eval_count": res.prompt_tokens,
            "eval_count": res.completion_tokens,
        }
    return {
        "model": requested_model,
        "created_at": "",
        "message": {"role": "assistant", "content": res.content},
        "done": True,
        "done_reason": res.finish_reason,
        "prompt_eval_count": res.prompt_tokens,
        "eval_count": res.completion_tokens,
    }


def ollama_stream_chunk(chunk: ChatChunk, requested_model: str, generate_mode: bool) -> str:
    if generate_mode:
        obj = {
            "model": requested_model,
            "created_at": "",
            "response": "" if chunk.done else chunk.delta,
            "done": chunk.done,
        }
    else:
        obj = {
            "model": requested_model,
            "created_at": "",
            "message": {"role": "assistant", "content": "" if chunk.done else chunk.delta},
            "done": chunk.done,
        }
    if chunk.done and chunk.finish_reason:
        obj["done_reason"] = chunk.finish_reason
    return json.dumps(obj) + "\n"
