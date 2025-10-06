"""
XTTS (Text-to-Speech) Status Router
Provides real-time status monitoring for XTTS service connectivity
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx
import logging
from api_config import api_config_manager
from auth.router import get_current_user_or_key

logger = logging.getLogger(__name__)
router = APIRouter()


class XTTSStatusResponse(BaseModel):
    connected: bool
    host: Optional[str] = None
    speakers_available: Optional[int] = None
    quota_remaining: Optional[int] = None
    error_message: Optional[str] = None
    service_version: Optional[str] = None


@router.get("/api/xtts/status", response_model=XTTSStatusResponse)
async def get_xtts_status(current_user: dict = Depends(get_current_user_or_key)):
    """
    Check XTTS service connectivity and status

    Tests connectivity by calling the /speakers endpoint which returns available voices.
    This is a lightweight health check that also provides useful information about
    available speakers.

    Returns:
        XTTSStatusResponse with connection status and available speakers count
    """
    try:
        # Load XTTS configuration
        xtts_config = api_config_manager.get_service_config(
            workflow="preproduction",
            category="ai_services",
            service="xtts"
        )

        if not xtts_config:
            logger.warning("XTTS configuration not found")
            return XTTSStatusResponse(
                connected=False,
                error_message="XTTS not configured"
            )

        host = xtts_config.get("host")
        if not host:
            logger.warning("XTTS host not configured")
            return XTTSStatusResponse(
                connected=False,
                error_message="XTTS host not configured"
            )

        # Check if service is enabled
        enabled = xtts_config.get("enabled", False)
        if not enabled:
            logger.info("XTTS service is disabled in configuration")
            return XTTSStatusResponse(
                connected=False,
                host=host,
                error_message="XTTS service disabled in configuration"
            )

        # Test connectivity using /health endpoint (primary check)
        health_url = f"{host.rstrip('/')}/health"
        speakers_url = f"{host.rstrip('/')}/speakers"

        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                # Check health endpoint
                health_response = await client.get(health_url)

                if health_response.status_code == 200:
                    health_data = health_response.json()

                    # Check if model is loaded and service is healthy
                    is_healthy = health_data.get("status") == "healthy"
                    model_loaded = health_data.get("model_loaded", False)

                    if is_healthy and model_loaded:
                        # Try to get speaker count for additional info
                        speakers_count = None
                        try:
                            speakers_response = await client.get(speakers_url)
                            if speakers_response.status_code == 200:
                                speakers_data = speakers_response.json()
                                if isinstance(speakers_data, dict) and "speakers" in speakers_data:
                                    speakers_count = len(speakers_data["speakers"])
                        except Exception:
                            pass  # Speakers count is optional

                        logger.info(f"XTTS service healthy at {host}")

                        return XTTSStatusResponse(
                            connected=True,
                            host=host,
                            speakers_available=speakers_count,
                            quota_remaining=None,  # XTTS doesn't have quota limits
                            service_version="XTTS v2"
                        )
                    else:
                        logger.warning(f"XTTS service unhealthy: status={health_data.get('status')}, model_loaded={model_loaded}")
                        return XTTSStatusResponse(
                            connected=False,
                            host=host,
                            error_message=f"Service unhealthy or model not loaded"
                        )
                else:
                    logger.warning(f"XTTS health endpoint returned {health_response.status_code}")
                    return XTTSStatusResponse(
                        connected=False,
                        host=host,
                        error_message=f"Health endpoint returned {health_response.status_code}"
                    )

            except httpx.TimeoutException:
                logger.error(f"XTTS connection timeout to {speakers_url}")
                return XTTSStatusResponse(
                    connected=False,
                    host=host,
                    error_message="Connection timeout"
                )
            except httpx.ConnectError:
                logger.error(f"XTTS connection refused to {speakers_url}")
                return XTTSStatusResponse(
                    connected=False,
                    host=host,
                    error_message="Connection refused - service may be down"
                )
            except Exception as e:
                logger.error(f"XTTS connection error: {str(e)}")
                return XTTSStatusResponse(
                    connected=False,
                    host=host,
                    error_message=f"Connection error: {str(e)}"
                )

    except Exception as e:
        logger.error(f"Failed to check XTTS status: {str(e)}", exc_info=True)
        return XTTSStatusResponse(
            connected=False,
            error_message=f"Internal error: {str(e)}"
        )


@router.get("/api/xtts/config")
async def get_xtts_config(current_user: dict = Depends(get_current_user_or_key)):
    """
    Get current XTTS configuration (without sensitive data)

    Returns non-sensitive configuration details for debugging and UI display.
    """
    try:
        xtts_config = api_config_manager.get_service_config(
            workflow="preproduction",
            category="ai_services",
            service="xtts"
        )

        if not xtts_config:
            raise HTTPException(status_code=404, detail="XTTS configuration not found")

        # Return only non-sensitive configuration
        return {
            "host": xtts_config.get("host"),
            "endpoint": xtts_config.get("endpoint"),
            "language": xtts_config.get("language"),
            "speed": xtts_config.get("speed"),
            "speaker": xtts_config.get("speaker"),
            "enabled": xtts_config.get("enabled", False)
        }

    except Exception as e:
        logger.error(f"Failed to get XTTS config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
