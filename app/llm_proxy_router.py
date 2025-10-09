"""
LLM Proxy Router - Proxies requests to LLM services to avoid mixed content issues
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import httpx
import logging
from auth.utils import get_current_user_or_key
from database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text

router = APIRouter(prefix="/api/llm", tags=["llm-proxy"])
logger = logging.getLogger(__name__)


def get_ollama_host_from_db(db: Session) -> Optional[str]:
    """Get Ollama host from database api_configs table"""
    try:
        result = db.execute(
            text("SELECT config_value FROM api_configs WHERE service = 'ollama' AND config_key = 'host'")
        ).fetchone()

        if result:
            return result[0]
        return 'http://192.168.51.197:11434'  # Fallback
    except Exception as e:
        logger.error(f"Failed to get Ollama host from database: {e}")
        return 'http://192.168.51.197:11434'  # Fallback


class OllamaGenerateRequest(BaseModel):
    model: str
    prompt: str
    stream: bool = False
    options: Optional[Dict[str, Any]] = None


class OllamaGenerateResponse(BaseModel):
    response: str
    model: str
    created_at: Optional[str] = None
    done: bool = True


@router.post("/ollama/generate", response_model=OllamaGenerateResponse)
async def ollama_generate_proxy(
    request: OllamaGenerateRequest,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Proxy endpoint for Ollama generate requests.
    Solves mixed content issues by making backend-to-backend HTTP calls.
    """
    try:
        host = get_ollama_host_from_db(db)

        logger.info(f"Proxying Ollama request to {host} for user {current_user.get('username', 'unknown')}")
        logger.info(f"Model: {request.model}, Prompt length: {len(request.prompt)} chars")

        # Make request to Ollama server
        async with httpx.AsyncClient(timeout=180.0) as client:  # 3 minutes for longer prompts
            response = await client.post(
                f"{host}/api/generate",
                json={
                    "model": request.model,
                    "prompt": request.prompt,
                    "stream": request.stream,
                    "options": request.options or {}
                }
            )

            if response.status_code != 200:
                logger.error(f"Ollama returned status {response.status_code}: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Ollama error: {response.text}"
                )

            data = response.json()
            logger.info(f"Ollama response received, length: {len(data.get('response', ''))} chars")

            return OllamaGenerateResponse(
                response=data.get('response', ''),
                model=data.get('model', request.model),
                created_at=data.get('created_at'),
                done=data.get('done', True)
            )

    except httpx.TimeoutException:
        logger.error("Ollama request timed out")
        raise HTTPException(status_code=504, detail="Ollama request timed out")
    except httpx.RequestError as e:
        logger.error(f"Ollama connection error: {e}")
        raise HTTPException(status_code=503, detail=f"Cannot connect to Ollama: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in Ollama proxy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ollama/models")
async def ollama_list_models_proxy(
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Proxy endpoint to list available Ollama models.
    """
    try:
        host = get_ollama_host_from_db(db)

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{host}/api/tags")

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Ollama error: {response.text}"
                )

            return response.json()

    except httpx.RequestError as e:
        logger.error(f"Ollama connection error: {e}")
        raise HTTPException(status_code=503, detail=f"Cannot connect to Ollama: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error listing Ollama models: {e}")
        raise HTTPException(status_code=500, detail=str(e))
