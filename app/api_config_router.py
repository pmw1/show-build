"""
API Configuration Router
FastAPI endpoints for managing API configurations
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from typing import Dict, Any, Optional
from pydantic import BaseModel
import logging

from api_config import api_config_manager
from auth.utils import get_current_user_or_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings", tags=["API Configuration"])

class APIConfigUpdate(BaseModel):
    """Model for API configuration updates"""
    config: Dict[str, Any]

class ServiceConfigUpdate(BaseModel):
    """Model for individual service configuration updates"""
    workflow: str
    category: str
    service: str
    config: Dict[str, Any]

@router.get("/api-configs")
async def get_api_configs(token_data=Depends(get_current_user_or_key)):
    """
    Get all API configurations.
    Requires authentication.
    """
    try:
        config = api_config_manager.load_config()
        
        # Remove sensitive metadata for frontend
        if "metadata" in config:
            config["metadata"] = {
                "version": config["metadata"].get("version", "1.0"),
                "last_loaded": config["metadata"].get("last_loaded")
            }
        
        return {
            "success": True,
            "data": config,
            "message": "API configurations loaded successfully"
        }
    except Exception as e:
        logger.error(f"Error getting API configs: {e}")
        raise HTTPException(status_code=500, detail="Failed to load API configurations")

@router.post("/api-configs")
async def save_api_configs(config_update: APIConfigUpdate, token_data=Depends(get_current_user_or_key)):
    """
    Save API configurations.
    Requires authentication.
    """
    try:
        success = api_config_manager.save_config(config_update.config)
        
        if success:
            return {
                "success": True,
                "message": "API configurations saved successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save configurations")
    
    except Exception as e:
        logger.error(f"Error saving API configs: {e}")
        raise HTTPException(status_code=500, detail="Failed to save API configurations")

@router.get("/api-configs/{workflow}")
async def get_workflow_configs(workflow: str, token_data=Depends(get_current_user_or_key)):
    """
    Get API configurations for a specific workflow (preproduction, production, promotion).
    """
    try:
        config = api_config_manager.load_config()
        workflow_config = config.get(workflow)
        
        if not workflow_config:
            raise HTTPException(status_code=404, detail=f"Workflow '{workflow}' not found")
        
        return {
            "success": True,
            "data": workflow_config,
            "message": f"Configuration for {workflow} loaded successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting {workflow} configs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load {workflow} configurations")

@router.post("/api-configs/service")
async def update_service_config(service_update: ServiceConfigUpdate, token_data=Depends(get_current_user_or_key)):
    """
    Update configuration for a specific service.
    """
    try:
        success = api_config_manager.update_service_config(
            service_update.workflow,
            service_update.category,
            service_update.service,
            service_update.config
        )
        
        if success:
            return {
                "success": True,
                "message": f"Configuration for {service_update.service} updated successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update service configuration")
    
    except Exception as e:
        logger.error(f"Error updating service config: {e}")
        raise HTTPException(status_code=500, detail="Failed to update service configuration")

async def test_whisper_connection(service_config: dict):
    """
    Test connection to Whisper service by checking health endpoint.
    """
    host = service_config.get("host")
    if not host:
        raise HTTPException(status_code=400, detail="Whisper host not configured")

    try:
        import requests

        # Test basic connectivity by trying health endpoint
        health_url = f"{host}/health"
        try:
            response = requests.get(health_url, timeout=5)
            response.raise_for_status()
        except:
            # If no health endpoint, try the main endpoint
            endpoint = service_config.get("endpoint", "/v1/audio/transcriptions")
            test_url = f"{host}{endpoint}"
            response = requests.get(test_url, timeout=5)

        return {
            "success": True,
            "message": f"Whisper connection successful",
            "service": "whisper",
            "status": "connected",
            "details": {
                "host": host,
                "response_time_ms": response.elapsed.total_seconds() * 1000
            }
        }

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=408, detail="Whisper service timeout - check if service is running")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail=f"Cannot connect to Whisper service at {host}")
    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Whisper service error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Whisper connection test failed: {str(e)}")

async def test_fishspeech_connection(service_config: dict):
    """
    Test connection to Fish Speech service by checking health endpoint.
    """
    host = service_config.get("host")
    if not host:
        raise HTTPException(status_code=400, detail="Fish Speech host not configured")

    try:
        import requests

        # Test basic connectivity by trying health endpoint
        health_url = f"{host}/v1/health"
        try:
            response = requests.get(health_url, timeout=5)
            response.raise_for_status()
            health_data = response.json()
        except:
            # If no health endpoint, try the main endpoint
            endpoint = service_config.get("endpoint", "/v1/audio/speech")
            test_url = f"{host}{endpoint}"
            response = requests.get(test_url, timeout=5)
            health_data = {}

        return {
            "success": True,
            "message": f"Fish Speech connection successful",
            "service": "fishspeech",
            "status": "connected",
            "details": {
                "host": host,
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "health": health_data
            }
        }

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=408, detail="Fish Speech service timeout - check if service is running")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail=f"Cannot connect to Fish Speech service at {host}")
    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Fish Speech service error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fish Speech connection test failed: {str(e)}")

async def test_xtts_connection(service_config: dict):
    """
    Test connection to XTTS service by checking health and speakers endpoints.
    """
    host = service_config.get("host")
    if not host:
        raise HTTPException(status_code=400, detail="XTTS host not configured")

    try:
        import requests

        # Test basic connectivity by trying to fetch speakers
        speakers_url = f"{host}/speakers"
        response = requests.get(speakers_url, timeout=5)
        response.raise_for_status()

        speakers_data = response.json()

        # Validate response format
        if isinstance(speakers_data, dict) and "speakers" in speakers_data:
            speaker_count = len(speakers_data["speakers"])
        elif isinstance(speakers_data, list):
            speaker_count = len(speakers_data)
        else:
            speaker_count = 0

        return {
            "success": True,
            "message": f"XTTS connection successful - {speaker_count} speakers available",
            "service": "xtts",
            "status": "connected",
            "details": {
                "host": host,
                "speaker_count": speaker_count,
                "response_time_ms": response.elapsed.total_seconds() * 1000
            }
        }

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=408, detail="XTTS service timeout - check if service is running")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail=f"Cannot connect to XTTS service at {host}")
    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"XTTS service error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"XTTS connection test failed: {str(e)}")

@router.post("/test/{service}")
async def test_api_connection(service: str, token_data=Depends(get_current_user_or_key)):
    """
    Test API connection for a specific service.
    This is a placeholder - actual implementation would test real API connections.
    """
    try:
        # Get service configuration
        config = api_config_manager.load_config()
        
        # Find service in all workflows and categories
        service_config = None
        workflow_found = None
        category_found = None
        
        for workflow_name, workflow_data in config.items():
            if workflow_name == "metadata":
                continue
            for category_name, category_data in workflow_data.items():
                if service in category_data:
                    service_config = category_data[service]
                    workflow_found = workflow_name
                    category_found = category_name
                    break
            if service_config:
                break
        
        if not service_config:
            raise HTTPException(status_code=404, detail=f"Service '{service}' not found")
        
        if not service_config.get('enabled', False):
            raise HTTPException(status_code=400, detail=f"Service '{service}' is not enabled")
        
        # Validate credentials
        has_credentials = api_config_manager.validate_service_credentials(
            workflow_found, category_found, service
        )
        
        if not has_credentials:
            raise HTTPException(status_code=400, detail=f"Missing required credentials for '{service}'")
        
        # Implement actual API testing logic for specific services
        if service == "xtts":
            return await test_xtts_connection(service_config)
        elif service == "whisper":
            return await test_whisper_connection(service_config)
        elif service == "fishspeech":
            return await test_fishspeech_connection(service_config)
        else:
            # For other services, simulate testing for now
            import asyncio
            await asyncio.sleep(1)  # Simulate network delay

            # Random success/failure for demonstration
            import random
            if random.random() > 0.2:  # 80% success rate
                return {
                    "success": True,
                    "message": f"Connection to {service} successful",
                    "service": service,
                    "status": "connected"
                }
            else:
                raise HTTPException(status_code=400, detail=f"Connection to {service} failed")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing {service} connection: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to test {service} connection")

@router.get("/xtts/speakers")
async def get_xtts_speakers(token_data=Depends(get_current_user_or_key)):
    """
    Proxy endpoint to fetch XTTS speakers without CORS issues.
    Gets the XTTS host from configuration and fetches available speakers.
    """
    try:
        # Load current configuration to get XTTS host
        config = api_config_manager.load_config()
        xtts_config = config.get("preproduction", {}).get("ai_services", {}).get("xtts", {})

        xtts_host = xtts_config.get("host")
        if not xtts_host:
            # Return helpful message instead of error to allow graceful handling
            return {
                "success": False,
                "speakers": [],
                "count": 0,
                "message": "XTTS host not configured. Please configure the XTTS host URL first.",
                "xtts_host": None
            }

        # Make request to XTTS speakers endpoint
        import requests
        speakers_url = f"{xtts_host}/speakers"

        response = requests.get(speakers_url, timeout=10)
        response.raise_for_status()

        speakers_data = response.json()

        # Normalize the response format
        if isinstance(speakers_data, dict) and "speakers" in speakers_data:
            speakers_list = speakers_data["speakers"]
        elif isinstance(speakers_data, list):
            speakers_list = speakers_data
        else:
            speakers_list = []

        # Add OpenAI standard voices for compatibility
        openai_voices = [
            {"id": "alloy", "name": "Alloy (OpenAI Standard)"},
            {"id": "echo", "name": "Echo (OpenAI Standard)"},
            {"id": "fable", "name": "Fable (OpenAI Standard)"},
            {"id": "nova", "name": "Nova (OpenAI Standard)"},
            {"id": "onyx", "name": "Onyx (OpenAI Standard)"},
            {"id": "shimmer", "name": "Shimmer (OpenAI Standard)"}
        ]

        # Format XTTS speakers for frontend consumption
        formatted_speakers = []

        # Add OpenAI standard voices first
        formatted_speakers.extend(openai_voices)

        # Add separator
        formatted_speakers.append({
            "id": "---separator---",
            "name": "── XTTS Speakers ──"
        })

        # Add XTTS speakers
        for speaker in speakers_list:
            if isinstance(speaker, str):
                formatted_speakers.append({
                    "id": speaker,
                    "name": speaker
                })
            elif isinstance(speaker, dict):
                formatted_speakers.append({
                    "id": speaker.get("id", speaker.get("name", "")),
                    "name": speaker.get("name", speaker.get("id", ""))
                })

        return {
            "success": True,
            "speakers": formatted_speakers,
            "count": len(formatted_speakers),
            "xtts_host": xtts_host,
            "openai_voices_included": True
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching XTTS speakers: {e}")
        raise HTTPException(status_code=503, detail=f"Failed to connect to XTTS service: {str(e)}")
    except Exception as e:
        logger.error(f"Error in XTTS speakers endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch speakers")

@router.post("/xtts/synthesize")
async def synthesize_speech(
    request: dict = Body(...),
    token_data=Depends(get_current_user_or_key)
):
    """
    Proxy endpoint for XTTS text-to-speech synthesis.
    Accepts text and TTS parameters, returns audio data.
    """
    try:
        # Load current configuration to get XTTS settings
        config = api_config_manager.load_config()
        xtts_config = config.get("preproduction", {}).get("ai_services", {}).get("xtts", {})

        xtts_host = xtts_config.get("host")
        xtts_endpoint = xtts_config.get("endpoint", "/synthesize")

        if not xtts_host:
            raise HTTPException(status_code=400, detail="XTTS host not configured")

        if not xtts_config.get("enabled", False):
            raise HTTPException(status_code=400, detail="XTTS is not enabled")

        # Use OpenAI endpoint for compatibility
        xtts_url = f"{xtts_host}{xtts_endpoint}"

        tts_json_data = {
            "model": "tts-1",
            "input": request.get("text", ""),
            "voice": request.get("speaker", xtts_config.get("speaker", "alloy")),
            "speed": request.get("speed", xtts_config.get("speed", 1.0))
        }

        if not tts_json_data["input"]:
            raise HTTPException(status_code=400, detail="Text is required for synthesis")

        # Debug logging
        logger.info(f"XTTS OpenAI Request URL: {xtts_url}")
        logger.info(f"XTTS JSON Data: {tts_json_data}")

        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                xtts_url,
                json=tts_json_data,  # Use JSON for OpenAI endpoint
                headers={"Content-Type": "application/json"}
            )

        # Better error handling with response details
        if response.status_code != 200:
            try:
                error_detail = response.json()
                logger.error(f"XTTS service error {response.status_code}: {error_detail}")
                raise HTTPException(status_code=response.status_code, detail=f"XTTS service error: {error_detail}")
            except ValueError:
                # Response is not JSON
                error_text = response.text
                logger.error(f"XTTS service error {response.status_code}: {error_text}")
                raise HTTPException(status_code=response.status_code, detail=f"XTTS service error: {error_text}")

        response.raise_for_status()

        # Check if response is audio
        content_type = response.headers.get('content-type', '')
        if 'audio' not in content_type and 'octet-stream' not in content_type:
            # If not audio, try to parse as JSON error
            try:
                error_data = response.json()
                raise HTTPException(status_code=400, detail=f"TTS error: {error_data}")
            except:
                raise HTTPException(status_code=400, detail="Invalid response from XTTS service")

        # Return audio data directly
        from fastapi.responses import Response
        audio_data = response.content

        return Response(
            content=audio_data,
            media_type="audio/wav",
            headers={
                "Content-Disposition": "attachment; filename=xtts_output.wav",
                "Content-Length": str(len(audio_data))
            }
        )

    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="XTTS synthesis timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Cannot connect to XTTS service")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"XTTS service error: {e}")
    except Exception as e:
        logger.error(f"Error in XTTS synthesis: {e}")
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {str(e)}")


# ============================================
# Fish Speech Endpoints
# ============================================

@router.get("/fishspeech/references")
async def get_fishspeech_references(token_data=Depends(get_current_user_or_key)):
    """
    Get available reference voices from Fish Speech service.
    """
    try:
        config = api_config_manager.load_config()
        fish_config = config.get("preproduction", {}).get("ai_services", {}).get("fishspeech", {})

        if not fish_config.get("enabled", False):
            raise HTTPException(status_code=400, detail="Fish Speech is not enabled")

        fish_host = fish_config.get("host")
        if not fish_host:
            raise HTTPException(status_code=400, detail="Fish Speech host not configured")

        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{fish_host}/v1/references/list",
                headers={"Accept": "application/json"}
            )

        if response.status_code == 200:
            # Fish Speech returns msgpack by default, but we requested JSON
            try:
                data = response.json()
                references = data.get("reference_ids", [])
                return {
                    "success": True,
                    "references": references,
                    "message": data.get("message", f"Found {len(references)} reference voices")
                }
            except:
                # If JSON parsing fails, return empty list
                return {
                    "success": True,
                    "references": [],
                    "message": "No reference voices found"
                }
        else:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch references")

    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="Fish Speech service timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Cannot connect to Fish Speech service")
    except Exception as e:
        logger.error(f"Error fetching Fish Speech references: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch references: {str(e)}")


@router.post("/fishspeech/synthesize")
async def fishspeech_synthesize(
    request: dict = Body(...),
    token_data=Depends(get_current_user_or_key)
):
    """
    Proxy endpoint for Fish Speech text-to-speech synthesis.
    """
    try:
        config = api_config_manager.load_config()
        fish_config = config.get("preproduction", {}).get("ai_services", {}).get("fishspeech", {})

        if not fish_config.get("enabled", False):
            raise HTTPException(status_code=400, detail="Fish Speech is not enabled")

        fish_host = fish_config.get("host")
        if not fish_host:
            raise HTTPException(status_code=400, detail="Fish Speech host not configured")

        text = request.get("text", "")
        if not text:
            raise HTTPException(status_code=400, detail="Text is required for synthesis")

        # Build Fish Speech request
        fish_request = {
            "text": text,
            "format": request.get("format", "wav"),
            "reference_id": request.get("reference_id") or request.get("speaker"),
            "chunk_length": request.get("chunk_length", 200),
            "normalize": request.get("normalize", True),
            "streaming": False,
            "temperature": request.get("temperature", 0.8),
            "top_p": request.get("top_p", 0.8)
        }

        # Remove None values
        fish_request = {k: v for k, v in fish_request.items() if v is not None}

        logger.info(f"Fish Speech Request URL: {fish_host}/v1/tts")
        logger.info(f"Fish Speech Request: {fish_request}")

        import httpx
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{fish_host}/v1/tts",
                json=fish_request,
                headers={"Content-Type": "application/json", "Accept": "audio/wav"}
            )

        if response.status_code != 200:
            try:
                error_detail = response.json()
                logger.error(f"Fish Speech error {response.status_code}: {error_detail}")
                raise HTTPException(status_code=response.status_code, detail=f"Fish Speech error: {error_detail}")
            except ValueError:
                error_text = response.text
                logger.error(f"Fish Speech error {response.status_code}: {error_text}")
                raise HTTPException(status_code=response.status_code, detail=f"Fish Speech error: {error_text}")

        # Return audio data
        from fastapi.responses import Response
        audio_data = response.content

        content_type = response.headers.get('content-type', 'audio/wav')

        return Response(
            content=audio_data,
            media_type=content_type,
            headers={
                "Content-Disposition": "attachment; filename=fishspeech_output.wav",
                "Content-Length": str(len(audio_data))
            }
        )

    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="Fish Speech synthesis timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Cannot connect to Fish Speech service")
    except Exception as e:
        logger.error(f"Error in Fish Speech synthesis: {e}")
        raise HTTPException(status_code=500, detail=f"Fish Speech synthesis failed: {str(e)}")


# ============================================
# Unified TTS Endpoint (auto-selects service)
# ============================================

@router.post("/tts/synthesize")
async def unified_tts_synthesize(
    request: dict = Body(...),
    token_data=Depends(get_current_user_or_key)
):
    """
    Unified TTS synthesis endpoint.
    Automatically routes to Fish Speech or XTTS based on configuration.
    Fish Speech is preferred if enabled; falls back to XTTS.
    """
    try:
        config = api_config_manager.load_config()
        fish_config = config.get("preproduction", {}).get("ai_services", {}).get("fishspeech", {})
        xtts_config = config.get("preproduction", {}).get("ai_services", {}).get("xtts", {})

        fish_enabled = fish_config.get("enabled", False)
        xtts_enabled = xtts_config.get("enabled", False)

        # Route to appropriate service
        if fish_enabled:
            logger.info("Routing TTS request to Fish Speech")
            return await fishspeech_synthesize(request, token_data)
        elif xtts_enabled:
            logger.info("Routing TTS request to XTTS")
            return await synthesize_speech(request, token_data)
        else:
            raise HTTPException(status_code=400, detail="No TTS service is enabled. Enable Fish Speech or XTTS in settings.")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in unified TTS synthesis: {e}")
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {str(e)}")


@router.get("/tts/config")
async def get_tts_config(token_data=Depends(get_current_user_or_key)):
    """
    Get current TTS configuration.
    Returns which service is active and available speakers/references.
    """
    try:
        config = api_config_manager.load_config()
        fish_config = config.get("preproduction", {}).get("ai_services", {}).get("fishspeech", {})
        xtts_config = config.get("preproduction", {}).get("ai_services", {}).get("xtts", {})

        fish_enabled = fish_config.get("enabled", False)
        xtts_enabled = xtts_config.get("enabled", False)

        active_service = None
        if fish_enabled:
            active_service = "fishspeech"
        elif xtts_enabled:
            active_service = "xtts"

        return {
            "success": True,
            "active_service": active_service,
            "services": {
                "fishspeech": {
                    "enabled": fish_enabled,
                    "host": fish_config.get("host") if fish_enabled else None
                },
                "xtts": {
                    "enabled": xtts_enabled,
                    "host": xtts_config.get("host") if xtts_enabled else None,
                    "speaker": xtts_config.get("speaker") if xtts_enabled else None
                }
            }
        }
    except Exception as e:
        logger.error(f"Error getting TTS config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get TTS config: {str(e)}")


@router.get("/tts/speakers")
async def get_tts_speakers(token_data=Depends(get_current_user_or_key)):
    """
    Get available speakers/references for the active TTS service.
    """
    try:
        config = api_config_manager.load_config()
        fish_config = config.get("preproduction", {}).get("ai_services", {}).get("fishspeech", {})
        xtts_config = config.get("preproduction", {}).get("ai_services", {}).get("xtts", {})

        fish_enabled = fish_config.get("enabled", False)
        xtts_enabled = xtts_config.get("enabled", False)

        if fish_enabled:
            # Get Fish Speech references
            result = await get_fishspeech_references(token_data)
            return {
                "success": True,
                "service": "fishspeech",
                "speakers": result.get("references", [])
            }
        elif xtts_enabled:
            # Get XTTS speakers
            result = await get_xtts_speakers(token_data)
            return {
                "success": True,
                "service": "xtts",
                "speakers": result.get("speakers", [])
            }
        else:
            return {
                "success": False,
                "service": None,
                "speakers": [],
                "message": "No TTS service is enabled"
            }

    except Exception as e:
        logger.error(f"Error getting TTS speakers: {e}")
        return {
            "success": False,
            "service": None,
            "speakers": [],
            "error": str(e)
        }


@router.get("/current-episode")
async def get_current_episode_info(token_data=Depends(get_current_user_or_key)):
    """
    Get current episode information for TTS test messages.
    """
    try:
        # Import here to avoid circular imports
        from episodes_router import get_next_episode_number
        from sqlalchemy.orm import Session
        from database import get_db

        # TODO: Implement proper episode number detection
        # For now, return a reasonable default
        current_episode = "0241"  # Current working episode

        return {
            "success": True,
            "current_episode": current_episode,
            "server_info": {
                "name": "Ravena 1",
                "ip": "192.168.51.197"
            },
            "show_name": "Disaffected"
        }

    except Exception as e:
        logger.error(f"Error getting current episode info: {e}")
        # Return fallback data even on error
        return {
            "success": False,
            "current_episode": "0000",
            "server_info": {
                "name": "Ravena 1",
                "ip": "192.168.51.197"
            },
            "show_name": "Disaffected",
            "error": str(e)
        }

@router.delete("/api-configs")
async def reset_api_configs(token_data=Depends(get_current_user_or_key)):
    """
    Reset API configurations to defaults.
    This will remove all saved configurations!
    """
    try:
        # Create backup before reset
        import shutil
        import os
        from datetime import datetime

        backup_name = f"api_configs_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        backup_path = os.path.join("app/storage", backup_name)

        if os.path.exists(api_config_manager.config_file):
            shutil.copy2(api_config_manager.config_file, backup_path)

        # Remove current config file to trigger default creation
        if os.path.exists(api_config_manager.config_file):
            os.remove(api_config_manager.config_file)

        # Load (which will create defaults)
        api_config_manager.load_config()

        return {
            "success": True,
            "message": "API configurations reset to defaults",
            "backup_created": backup_name
        }

    except Exception as e:
        logger.error(f"Error resetting API configs: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset API configurations")

@router.get("/health")
async def health_check():
    """
    Health check endpoint for API configuration service.
    No authentication required.
    """
    try:
        # Check if config file exists and is readable
        config = api_config_manager.load_config()
        
        return {
            "success": True,
            "status": "healthy",
            "config_version": config.get("metadata", {}).get("version", "unknown"),
            "timestamp": config.get("metadata", {}).get("last_loaded")
        }
    except Exception as e:
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }
