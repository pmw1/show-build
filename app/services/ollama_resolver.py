"""
Ollama host/model resolver with fallback-model support.

Each LLM-using subsystem (generation/auto-description, meta_extraction,
file_inventory) stores its primary and fallback model in the api_configs table.
This module reads them, with a sensible last-resort default when the row is missing.

Usage:
    host = get_ollama_host(db)
    primary, fallback = get_models(db, workflow='meta_extraction', service='ollama')
    text = call_with_fallback(host, primary, fallback, prompt, ...)
"""

from typing import Optional, Tuple
import logging
import requests
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

DEFAULT_HOST = "http://172.17.0.1:11434"
LAST_RESORT_MODEL = "qwen3:32b-q4_K_M"


def get_ollama_host(db: Session) -> str:
    """Single Ollama host shared across subsystems. Prefers the
    `preproduction/ai_services/ollama/host` row; falls back to local container."""
    try:
        row = db.execute(text(
            "SELECT config_value FROM api_configs "
            "WHERE service = 'ollama' AND config_key = 'host' "
            "ORDER BY workflow = 'preproduction' DESC LIMIT 1"
        )).fetchone()
        if row and row[0]:
            return row[0]
    except Exception as exc:
        logger.warning("ollama host lookup failed: %s", exc)
    return DEFAULT_HOST


def get_models(
    db: Session,
    workflow: str,
    service: str,
    category: str = "llm",
    default_primary: Optional[str] = None,
) -> Tuple[str, Optional[str]]:
    """Return (primary_model, fallback_model) for a given workflow+service.
    fallback_model may be None if the admin hasn't configured one."""
    primary = default_primary or LAST_RESORT_MODEL
    fallback: Optional[str] = None
    try:
        rows = db.execute(text(
            "SELECT config_key, config_value FROM api_configs "
            "WHERE workflow = :w AND category = :c AND service = :s "
            "AND config_key IN ('model', 'fallback_model')"
        ), {"w": workflow, "c": category, "s": service}).fetchall()
        for k, v in rows:
            if not v:
                continue
            if k == "model":
                primary = v
            elif k == "fallback_model":
                fallback = v
    except Exception as exc:
        logger.warning("model lookup failed for %s/%s: %s", workflow, service, exc)
    return primary, fallback


def call_with_fallback(
    host: str,
    primary_model: str,
    fallback_model: Optional[str],
    *,
    prompt: Optional[str] = None,
    messages: Optional[list] = None,
    temperature: float = 0.2,
    max_tokens: int = 1000,
    top_p: Optional[float] = None,
    response_format: Optional[str] = None,
    timeout: int = 180,
) -> str:
    """POST to /api/generate (prompt mode) or /api/chat (messages mode).
    On 404 (model not installed) or connection error, retry once with fallback_model.
    Returns the generated text. Raises if both attempts fail."""
    use_chat = messages is not None
    endpoint = "/api/chat" if use_chat else "/api/generate"

    def _build_payload(model: str) -> dict:
        options = {"temperature": temperature, "num_predict": max_tokens}
        if top_p is not None:
            options["top_p"] = top_p
        payload: dict = {"model": model, "stream": False, "options": options}
        if use_chat:
            payload["messages"] = messages
        else:
            payload["prompt"] = prompt
        if response_format == "json":
            payload["format"] = "json"
        return payload

    def _extract(data: dict) -> str:
        if use_chat:
            return (data.get("message", {}) or {}).get("content", "") or ""
        return (data.get("response") or "").strip()

    candidates = [primary_model]
    if fallback_model and fallback_model != primary_model:
        candidates.append(fallback_model)

    last_exc: Optional[Exception] = None
    for idx, model in enumerate(candidates):
        try:
            resp = requests.post(
                f"{host}{endpoint}",
                json=_build_payload(model),
                timeout=timeout,
            )
            if resp.status_code == 404 and idx < len(candidates) - 1:
                logger.warning("model %s not on %s; trying fallback", model, host)
                continue
            resp.raise_for_status()
            return _extract(resp.json())
        except (requests.HTTPError, requests.ConnectionError, requests.Timeout) as exc:
            last_exc = exc
            logger.warning("ollama call with %s failed: %s", model, exc)
            if idx < len(candidates) - 1:
                continue
            raise
    if last_exc:
        raise last_exc
    raise RuntimeError("call_with_fallback: no candidates")
