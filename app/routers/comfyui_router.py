"""ComfyUI API proxy router.

Proxies requests to a ComfyUI instance configured in api_configs.
Builds workflow JSON from simple parameters and submits to ComfyUI's /prompt endpoint.
"""
import json
import logging
import uuid
from datetime import datetime

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from database import SessionLocal
from sqlalchemy import text

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/comfyui", tags=["comfyui"])


# --- Config ---

def get_comfyui_config():
    """Read ComfyUI connection config from api_configs table."""
    db = SessionLocal()
    try:
        rows = db.execute(text(
            "SELECT config_key, config_value FROM api_configs "
            "WHERE workflow = 'generation' AND service = 'comfyui'"
        )).fetchall()
        cfg = {r[0]: r[1] for r in rows}
        return cfg
    finally:
        db.close()


def get_comfyui_url():
    """Return the ComfyUI base URL or None if not configured."""
    cfg = get_comfyui_config()
    host = cfg.get("host", "")
    port = cfg.get("port", "8188")
    if not host:
        return None
    proto = "https" if cfg.get("ssl") == "true" else "http"
    return f"{proto}://{host}:{port}"


# --- Models ---

class GenerateRequest(BaseModel):
    prompt: str
    negative_prompt: str = ""
    checkpoint: str = ""
    width: int = 1024
    height: int = 576
    seed: int = -1
    steps: int = 25
    cfg: float = 7.0
    sampler: str = "euler_ancestral"
    scheduler: str = "normal"
    episode_number: Optional[int] = None


class SaveToEpisodeRequest(BaseModel):
    image_url: str
    episode_number: int


# --- Workflow builder ---

def build_txt2img_workflow(req: GenerateRequest) -> dict:
    """Build a ComfyUI workflow JSON for text-to-image generation."""
    actual_seed = req.seed if req.seed >= 0 else int(uuid.uuid4().int % (2**32))

    workflow = {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": actual_seed,
                "steps": req.steps,
                "cfg": req.cfg,
                "sampler_name": req.sampler,
                "scheduler": req.scheduler,
                "denoise": 1.0,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0]
            }
        },
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": req.checkpoint
            }
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": req.width,
                "height": req.height,
                "batch_size": 1
            }
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": req.prompt,
                "clip": ["4", 1]
            }
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": req.negative_prompt,
                "clip": ["4", 1]
            }
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["3", 0],
                "vae": ["4", 2]
            }
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": f"poster_{req.episode_number or 'noep'}",
                "images": ["8", 0]
            }
        }
    }
    return workflow


# --- Endpoints ---

@router.get("/health")
async def comfyui_health():
    """Check ComfyUI connectivity and return available checkpoints."""
    url = get_comfyui_url()
    if not url:
        return {"connected": False, "error": "ComfyUI not configured. Set host in Settings > API Access."}

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # System stats
            resp = await client.get(f"{url}/system_stats")
            connected = resp.status_code == 200
            stats = ""
            if connected:
                data = resp.json()
                devices = data.get("devices", [])
                if devices:
                    dev = devices[0]
                    vram_total = dev.get("vram_total", 0)
                    vram_free = dev.get("vram_free", 0)
                    if vram_total:
                        stats = f"{dev.get('name', 'GPU')}: {vram_free // (1024**3)}GB / {vram_total // (1024**3)}GB VRAM"

            # Available checkpoints
            checkpoint_list = []
            try:
                models_resp = await client.get(f"{url}/object_info/CheckpointLoaderSimple")
                if models_resp.status_code == 200:
                    info = models_resp.json()
                    ckpt_input = info.get("CheckpointLoaderSimple", {}).get("input", {}).get("required", {}).get("ckpt_name", [])
                    if ckpt_input and isinstance(ckpt_input[0], list):
                        checkpoint_list = ckpt_input[0]
            except Exception:
                pass

            return {
                "connected": connected,
                "stats": stats,
                "checkpoints": checkpoint_list,
                "url": url
            }
    except httpx.ConnectError:
        return {"connected": False, "error": "Connection refused"}
    except httpx.TimeoutException:
        return {"connected": False, "error": "Timeout"}
    except Exception as e:
        return {"connected": False, "error": str(e)[:100]}


@router.get("/config")
async def comfyui_config():
    """Return current ComfyUI configuration."""
    cfg = get_comfyui_config()
    return {"url": get_comfyui_url(), "host": cfg.get("host", ""), "port": cfg.get("port", "8188")}


@router.post("/generate")
async def generate_image(req: GenerateRequest):
    """Submit a txt2img workflow to ComfyUI."""
    url = get_comfyui_url()
    if not url:
        raise HTTPException(status_code=400, detail="ComfyUI not configured")

    if not req.checkpoint:
        raise HTTPException(status_code=400, detail="No checkpoint selected")

    workflow = build_txt2img_workflow(req)
    client_id = str(uuid.uuid4())

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{url}/prompt",
                json={"prompt": workflow, "client_id": client_id}
            )
            if resp.status_code != 200:
                error_data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                raise HTTPException(
                    status_code=502,
                    detail=error_data.get("error", f"ComfyUI returned HTTP {resp.status_code}")
                )

            data = resp.json()
            return {
                "prompt_id": data.get("prompt_id"),
                "number": data.get("number"),
                "client_id": client_id
            }

    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="ComfyUI not reachable")
    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="ComfyUI request timed out")


@router.get("/status/{prompt_id}")
async def get_status(prompt_id: str):
    """Check generation status and return output images when done."""
    url = get_comfyui_url()
    if not url:
        raise HTTPException(status_code=400, detail="ComfyUI not configured")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Check queue for progress
            queue_resp = await client.get(f"{url}/prompt")
            queue_data = queue_resp.json()

            # Check if still running
            running = queue_data.get("exec_info", {}).get("queue_remaining", 0)

            # Check history for completion
            hist_resp = await client.get(f"{url}/history/{prompt_id}")
            if hist_resp.status_code != 200:
                return {"status": "running", "progress": 0, "queue_remaining": running}

            hist_data = hist_resp.json()
            job = hist_data.get(prompt_id)

            if not job:
                return {"status": "running", "progress": 0, "queue_remaining": running}

            status = job.get("status", {})
            if status.get("status_str") == "error":
                messages = status.get("messages", [])
                error_msg = str(messages[-1]) if messages else "Unknown error"
                return {"status": "error", "error": error_msg}

            # Extract output images
            outputs = job.get("outputs", {})
            images = []
            for node_id, node_output in outputs.items():
                for img in node_output.get("images", []):
                    filename = img.get("filename", "")
                    subfolder = img.get("subfolder", "")
                    img_type = img.get("type", "output")
                    images.append(f"{img_type}/{subfolder}/{filename}" if subfolder else f"{img_type}/{filename}")

            if images:
                return {"status": "completed", "images": images, "progress": 1.0}

            return {"status": "running", "progress": 0.5}

    except Exception as e:
        logger.error(f"ComfyUI status check error: {e}")
        return {"status": "running", "progress": 0}


@router.get("/image/{img_type}/{filename:path}")
async def get_image(img_type: str, filename: str):
    """Proxy image retrieval from ComfyUI."""
    url = get_comfyui_url()
    if not url:
        raise HTTPException(status_code=400, detail="ComfyUI not configured")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{url}/view",
                params={"filename": filename, "type": img_type}
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail="Image not found")

            from fastapi.responses import Response
            content_type = resp.headers.get("content-type", "image/png")
            return Response(content=resp.content, media_type=content_type)

    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="ComfyUI not reachable")


@router.post("/save-to-episode")
async def save_to_episode(req: SaveToEpisodeRequest):
    """Download a generated image and save it to the episode's assets directory."""
    import os
    from pathlib import Path

    url = get_comfyui_url()
    if not url:
        raise HTTPException(status_code=400, detail="ComfyUI not configured")

    # Parse the image path from our proxy URL format
    parts = req.image_url.replace("/api/comfyui/image/", "").split("/", 1)
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail="Invalid image URL")

    img_type, filename = parts[0], parts[1]

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(f"{url}/view", params={"filename": filename, "type": img_type})
            if resp.status_code != 200:
                raise HTTPException(status_code=404, detail="Image not found on ComfyUI")

            # Save to episode graphics directory
            ep_num = str(req.episode_number).zfill(4)
            graphics_dir = Path(f"/home/episodes/{ep_num}/assets/graphics")
            graphics_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_name = f"poster_{timestamp}.png"
            save_path = graphics_dir / save_name

            save_path.write_bytes(resp.content)
            logger.info(f"Saved poster to {save_path}")

            return {"saved": True, "path": str(save_path), "filename": save_name}

    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="ComfyUI not reachable")
