"""
llm-router — capability-pool LLM router.

Clients ask for a CAPABILITY (e.g. "description-writer") as the model name; the
router picks the first available backend candidate (health + VRAM-fit aware) and
proxies the call, translating between OpenAI / ollama / Anthropic dialects and
the client's chosen dialect. Streaming supported on every path.

Endpoints:
  POST /v1/chat/completions   OpenAI-compatible (stream => SSE)
  POST /api/chat              ollama-compatible (stream => ndjson)
  POST /api/generate         ollama-compatible (stream => ndjson)
  GET  /capabilities          list capabilities + live candidate availability
  GET  /health                liveness
  GET  /admin/config          read router.yaml  (X-API-Key)
  PUT  /admin/config          replace router.yaml + hot-reload (X-API-Key)
"""
from __future__ import annotations

import os
import logging
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse, StreamingResponse, PlainTextResponse

import config as cfgmod
from resolver import resolve, _candidate_ok
from backends import adapter_for
from backends.base import ChatRequest, BackendError
import translate

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger("llm-router")

app = FastAPI(title="llm-router", version="1.0")

ADMIN_KEY = os.environ.get("LLM_STATE_API_KEY") or ""


# --------------------------------------------------------------------------- #
#  core proxy: resolve a normalized ChatRequest and run it (batch or stream)   #
# --------------------------------------------------------------------------- #

async def _run(req: ChatRequest, dialect: str, generate_mode: bool = False):
    cfg = cfgmod.get_config()
    requested = req.model
    try:
        res = await resolve(cfg, requested)
    except LookupError as exc:
        raise HTTPException(status_code=cfg.unavailable_status(), detail=str(exc))

    backend = res.backend
    adapter = adapter_for(backend)
    # The resolved concrete model replaces the capability for the backend call.
    backend_req = ChatRequest(
        model=res.model, messages=req.messages, temperature=req.temperature,
        max_tokens=req.max_tokens, top_p=req.top_p, json_mode=req.json_mode,
        stream=req.stream, extra=req.extra,
    )

    if not req.stream:
        try:
            result = await adapter.chat(backend, backend_req)
        except BackendError as exc:
            raise HTTPException(status_code=exc.status, detail=str(exc))
        if dialect == "openai":
            return JSONResponse(translate.openai_result(result, requested))
        return JSONResponse(translate.ollama_result(result, requested, generate_mode))

    # streaming
    async def gen():
        try:
            async for chunk in adapter.stream(backend, backend_req):
                if dialect == "openai":
                    yield translate.openai_stream_chunk(chunk, requested)
                else:
                    yield translate.ollama_stream_chunk(chunk, requested, generate_mode)
            if dialect == "openai":
                yield translate.openai_stream_done()
        except BackendError as exc:
            # Surface a final error frame rather than a silent cut.
            logger.error("stream error: %s", exc)
            if dialect == "openai":
                yield translate.openai_stream_done()

    media = "text/event-stream" if dialect == "openai" else "application/x-ndjson"
    return StreamingResponse(gen(), media_type=media)


# --------------------------------------------------------------------------- #
#  endpoints                                                                   #
# --------------------------------------------------------------------------- #

@app.post("/v1/chat/completions")
async def openai_chat(request: Request):
    body = await request.json()
    req = translate.parse_openai(body)
    return await _run(req, dialect="openai")


@app.post("/api/chat")
async def ollama_chat(request: Request):
    body = await request.json()
    req = translate.parse_ollama_chat(body)
    return await _run(req, dialect="ollama", generate_mode=False)


@app.post("/api/generate")
async def ollama_generate(request: Request):
    body = await request.json()
    req = translate.parse_ollama_generate(body)
    return await _run(req, dialect="ollama", generate_mode=True)


@app.get("/health")
async def health():
    cfg = cfgmod.get_config()
    return {"status": "ok", "capabilities": list(cfg.capabilities.keys()),
            "backends": list(cfg.backends.keys())}


@app.get("/capabilities")
async def capabilities():
    """List each capability with the live availability of every candidate, so
    an operator can see *why* routing lands where it does."""
    cfg = cfgmod.get_config()
    out: dict = {}
    for cap, cands in cfg.capabilities.items():
        rows = []
        for c in cands:
            ok, why = await _candidate_ok(cfg, c)
            rows.append({"model": c.model, "backend": c.backend,
                         "available": ok, "reason": why})
        out[cap] = rows
    return out


def _check_admin(key: Optional[str]):
    if not ADMIN_KEY:
        raise HTTPException(status_code=503, detail="admin disabled: LLM_STATE_API_KEY unset")
    if key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="bad admin key")


@app.get("/admin/config", response_class=PlainTextResponse)
async def get_config_text(x_api_key: Optional[str] = Header(default=None)):
    _check_admin(x_api_key)
    return cfgmod.raw_text()


@app.put("/admin/config")
async def put_config_text(request: Request, x_api_key: Optional[str] = Header(default=None)):
    _check_admin(x_api_key)
    new_text = (await request.body()).decode("utf-8")
    try:
        cfg = cfgmod.write_text(new_text)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"invalid config: {exc}")
    return {"status": "reloaded", "capabilities": list(cfg.capabilities.keys())}
