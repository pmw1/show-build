"""
LLM routing, show identity, and meta extraction settings endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any, Optional
from datetime import datetime
import json
import logging

from auth.utils import get_current_user_or_key

logger = logging.getLogger(__name__)

router = APIRouter(tags=["settings"])


@router.get("/llm_routing")
async def get_llm_routing_settings(
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Get LLM routing configuration including prompts"""
    from database import SessionLocal
    from models_v2 import Settings

    try:
        db = SessionLocal()
        setting = db.query(Settings).filter(Settings.key == "llm_routing").first()

        if setting:
            return {"key": "llm_routing", "value": setting.value, "category": setting.category}
        else:
            # Return default structure if not found
            return {
                "key": "llm_routing",
                "value": {
                    "routing": {
                        "quoteSplitting": "auto",
                        "slugGeneration": "auto",
                        "scriptSummary": "auto",
                        "titleGeneration": "auto",
                        "contentExpansion": "auto",
                        "entityExtraction": "auto",
                        "peopleSearch": "auto",
                        "socialSearch": "auto",
                        "tweetComposing": "auto",
                        "factChecking": "auto",
                        "enableFallback": True,
                        "fallbackOrder": ["ollama", "openai", "anthropic", "gemini", "grok"]
                    },
                    "prompts": []
                },
                "category": "llm"
            }
    except Exception as e:
        logger.error(f"Error loading LLM routing settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/llm_routing")
async def save_llm_routing_settings(
    request: Request,
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Save LLM routing configuration including prompts"""
    from database import SessionLocal
    from models_v2 import Settings
    from sqlalchemy import text

    try:
        body = await request.json()
        db = SessionLocal()

        # Find or create setting
        setting = db.query(Settings).filter(Settings.key == "llm_routing").first()

        if setting:
            # Update existing
            setting.value = body
            setting.updated_at = datetime.utcnow()
        else:
            # Create new
            setting = Settings(
                key="llm_routing",
                value=body,
                category="llm",
                description="LLM routing and prompt template configuration"
            )
            db.add(setting)

        db.commit()
        db.refresh(setting)

        return {
            "success": True,
            "message": "LLM routing settings saved successfully",
            "value": setting.value
        }
    except Exception as e:
        logger.error(f"Error saving LLM routing settings: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/show_identity")
async def get_show_identity_settings(
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Get show identity/thesis configuration"""
    from database import SessionLocal
    from models_v2 import Settings

    try:
        db = SessionLocal()
        setting = db.query(Settings).filter(Settings.key == "show_identity").first()

        if setting:
            return {"key": "show_identity", "value": setting.value, "category": setting.category}
        else:
            # Return default structure if not found
            return {
                "key": "show_identity",
                "value": {
                    "thesis": "",
                    "tone": "",
                    "audience": ""
                },
                "category": "content"
            }
    except Exception as e:
        logger.error(f"Error loading show identity settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/show_identity")
async def save_show_identity_settings(
    request: Request,
    current_user: dict = Depends(get_current_user_or_key)
) -> Dict[str, Any]:
    """Save show identity/thesis configuration"""
    from database import SessionLocal
    from models_v2 import Settings

    try:
        body = await request.json()
        db = SessionLocal()

        # Extract value from body (frontend sends {key, value})
        value = body.get("value", body)

        # Find or create setting
        setting = db.query(Settings).filter(Settings.key == "show_identity").first()

        if setting:
            # Update existing
            setting.value = value
            setting.updated_at = datetime.utcnow()
        else:
            # Create new
            setting = Settings(
                key="show_identity",
                value=value,
                category="content",
                description="Show identity: thesis, tone, and target audience for LLM context"
            )
            db.add(setting)

        db.commit()
        db.refresh(setting)

        return {
            "success": True,
            "message": "Show identity saved successfully",
            "value": setting.value
        }
    except Exception as e:
        logger.error(f"Error saving show identity settings: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ============================================================================
# META EXTRACTION SETTINGS
# ============================================================================

# Default item types eligible for LLM metadata extraction
DEFAULT_META_EXTRACTION_TYPES = [
    "segment",
    "coldopen",
    "interview",
    "tease",
    "pkg",
    "vox",
    "sot",
    "nat"
]

@router.get("/meta_extraction")
async def get_meta_extraction_settings(
    current_user: Optional[dict] = None
) -> Dict[str, Any]:
    """Get meta extraction settings including eligible item types"""
    from database import SessionLocal
    from models_v2 import Settings

    db = SessionLocal()
    try:
        setting = db.query(Settings).filter(Settings.key == "meta_extraction_item_types").first()

        if setting and setting.value:
            item_types = setting.value if isinstance(setting.value, list) else json.loads(setting.value) if isinstance(setting.value, str) else DEFAULT_META_EXTRACTION_TYPES
        else:
            item_types = DEFAULT_META_EXTRACTION_TYPES

        return {
            "success": True,
            "item_types": item_types,
            "defaults": DEFAULT_META_EXTRACTION_TYPES
        }
    except Exception as e:
        logger.error(f"Error loading meta extraction settings: {e}")
        return {
            "success": True,
            "item_types": DEFAULT_META_EXTRACTION_TYPES,
            "defaults": DEFAULT_META_EXTRACTION_TYPES
        }
    finally:
        db.close()


@router.post("/meta_extraction")
async def save_meta_extraction_settings(
    request: Request,
    current_user: Optional[dict] = None
) -> Dict[str, Any]:
    """Save meta extraction settings including eligible item types"""
    from database import SessionLocal
    from models_v2 import Settings

    try:
        body = await request.json()
        db = SessionLocal()

        # Extract item_types from body
        item_types = body.get("item_types", body.get("value", DEFAULT_META_EXTRACTION_TYPES))

        # Find or create setting
        setting = db.query(Settings).filter(Settings.key == "meta_extraction_item_types").first()

        if setting:
            # Update existing
            setting.value = item_types
            setting.updated_at = datetime.utcnow()
        else:
            # Create new
            setting = Settings(
                key="meta_extraction_item_types",
                value=item_types,
                category="metafactory",
                description="Item types eligible for LLM metadata extraction"
            )
            db.add(setting)

        db.commit()
        db.refresh(setting)

        return {
            "success": True,
            "message": "Meta extraction settings saved successfully",
            "item_types": setting.value
        }
    except Exception as e:
        logger.error(f"Error saving meta extraction settings: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
