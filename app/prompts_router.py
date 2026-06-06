"""
Prompt Override Management API

Provides endpoints for managing custom LLM prompt overrides.
Administrators can override default prompts from useLLMPrompts.js
with custom prompts stored in the database.
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from database import get_db
from auth.utils import get_current_user_or_key, require_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/prompts", tags=["prompts"])


# ============================================================================
# GET ALL PROMPT OVERRIDES
# ============================================================================
@router.get("/overrides")
async def get_prompt_overrides(
    category: Optional[str] = None,
    enabled_only: bool = False,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get all prompt overrides, optionally filtered by category.

    Query Parameters:
    - category: Filter by category (generate, analyze, extract, refactor, compose)
    - enabled_only: Only return enabled overrides
    """
    try:
        query = "SELECT * FROM prompt_overrides WHERE 1=1"
        params = {}

        if category:
            query += " AND category = :category"
            params['category'] = category

        if enabled_only:
            query += " AND is_enabled = TRUE"

        query += " ORDER BY category, operation_key"

        result = db.execute(text(query), params)
        overrides = [dict(row._mapping) for row in result]

        return {
            "success": True,
            "count": len(overrides),
            "overrides": overrides
        }

    except Exception as e:
        logger.error(f"Failed to fetch prompt overrides: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# GET SINGLE PROMPT OVERRIDE
# ============================================================================
@router.get("/overrides/{override_id}")
async def get_prompt_override(
    override_id: str,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get a specific prompt override by ID"""
    try:
        query = text("SELECT * FROM prompt_overrides WHERE id = :id")
        result = db.execute(query, {"id": override_id})
        override = result.first()

        if not override:
            raise HTTPException(status_code=404, detail="Prompt override not found")

        return {
            "success": True,
            "override": dict(override._mapping)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch prompt override: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CREATE PROMPT OVERRIDE
# ============================================================================
@router.post("/overrides")
async def create_prompt_override(
    override_data: Dict[str, Any] = Body(...),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new prompt override.

    Body:
    {
      "category": "generate",
      "operation_key": "generate-segment-script",
      "system_prompt": "Custom system prompt...",
      "user_prompt_template": "Custom user prompt with {{variables}}...",
      "is_enabled": true,
      "notes": "Developer notes...",
      "suggested_service": "anthropic",
      "suggested_model": "claude-3-5-sonnet-20241022",
      "temperature": 0.7,
      "max_tokens": 4096
    }
    """
    try:
        # Validate required fields
        if 'category' not in override_data or 'operation_key' not in override_data:
            raise HTTPException(status_code=400, detail="category and operation_key are required")

        # Check if override already exists
        check_query = text("""
            SELECT id FROM prompt_overrides
            WHERE category = :category AND operation_key = :operation_key
        """)
        existing = db.execute(check_query, {
            "category": override_data['category'],
            "operation_key": override_data['operation_key']
        }).first()

        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Override already exists for {override_data['category']}.{override_data['operation_key']}"
            )

        # Get username for created_by field
        username = current_user.get('username') or current_user.get('name') or 'api_key'

        # Insert new override
        insert_query = text("""
            INSERT INTO prompt_overrides (
                category, operation_key, system_prompt, user_prompt_template,
                is_enabled, notes, created_by, metadata,
                suggested_service, suggested_model, temperature, max_tokens
            )
            VALUES (
                :category, :operation_key, :system_prompt, :user_prompt_template,
                :is_enabled, :notes, :created_by, :metadata,
                :suggested_service, :suggested_model, :temperature, :max_tokens
            )
            RETURNING id, created_at
        """)

        result = db.execute(insert_query, {
            "category": override_data['category'],
            "operation_key": override_data['operation_key'],
            "system_prompt": override_data.get('system_prompt'),
            "user_prompt_template": override_data.get('user_prompt_template'),
            "is_enabled": override_data.get('is_enabled', True),
            "notes": override_data.get('notes'),
            "created_by": username,
            "metadata": override_data.get('metadata'),
            "suggested_service": override_data.get('suggested_service'),
            "suggested_model": override_data.get('suggested_model'),
            "temperature": override_data.get('temperature'),
            "max_tokens": override_data.get('max_tokens')
        })

        new_override = result.first()
        db.commit()

        logger.info(f"Created prompt override: {override_data['category']}.{override_data['operation_key']}")

        return {
            "success": True,
            "message": "Prompt override created",
            "id": str(new_override.id),
            "created_at": new_override.created_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create prompt override: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# UPDATE PROMPT OVERRIDE
# ============================================================================
@router.patch("/overrides/{override_id}")
async def update_prompt_override(
    override_id: str,
    override_data: Dict[str, Any] = Body(...),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update an existing prompt override.
    Only provided fields will be updated.
    """
    try:
        # Check if override exists
        check_query = text("SELECT id FROM prompt_overrides WHERE id = :id")
        existing = db.execute(check_query, {"id": override_id}).first()

        if not existing:
            raise HTTPException(status_code=404, detail="Prompt override not found")

        # Build dynamic update query
        update_fields = []
        params = {"id": override_id}

        if 'system_prompt' in override_data:
            update_fields.append("system_prompt = :system_prompt")
            params['system_prompt'] = override_data['system_prompt']

        if 'user_prompt_template' in override_data:
            update_fields.append("user_prompt_template = :user_prompt_template")
            params['user_prompt_template'] = override_data['user_prompt_template']

        if 'is_enabled' in override_data:
            update_fields.append("is_enabled = :is_enabled")
            params['is_enabled'] = override_data['is_enabled']

        if 'notes' in override_data:
            update_fields.append("notes = :notes")
            params['notes'] = override_data['notes']

        if 'metadata' in override_data:
            update_fields.append("metadata = :metadata")
            params['metadata'] = override_data['metadata']

        if 'suggested_service' in override_data:
            update_fields.append("suggested_service = :suggested_service")
            params['suggested_service'] = override_data['suggested_service']

        if 'suggested_model' in override_data:
            update_fields.append("suggested_model = :suggested_model")
            params['suggested_model'] = override_data['suggested_model']

        if 'temperature' in override_data:
            update_fields.append("temperature = :temperature")
            params['temperature'] = override_data['temperature']

        if 'max_tokens' in override_data:
            update_fields.append("max_tokens = :max_tokens")
            params['max_tokens'] = override_data['max_tokens']

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        # Always update updated_at
        update_fields.append("updated_at = NOW()")

        update_query = text(f"""
            UPDATE prompt_overrides
            SET {', '.join(update_fields)}
            WHERE id = :id
            RETURNING updated_at
        """)

        result = db.execute(update_query, params)
        updated = result.first()
        db.commit()

        logger.info(f"Updated prompt override: {override_id}")

        return {
            "success": True,
            "message": "Prompt override updated",
            "id": override_id,
            "updated_at": updated.updated_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update prompt override: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DELETE PROMPT OVERRIDE
# ============================================================================
@router.delete("/overrides/{override_id}")
async def delete_prompt_override(
    override_id: str,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete a prompt override"""
    try:
        delete_query = text("""
            DELETE FROM prompt_overrides
            WHERE id = :id
            RETURNING category, operation_key
        """)

        result = db.execute(delete_query, {"id": override_id})
        deleted = result.first()

        if not deleted:
            raise HTTPException(status_code=404, detail="Prompt override not found")

        db.commit()

        logger.info(f"Deleted prompt override: {deleted.category}.{deleted.operation_key}")

        return {
            "success": True,
            "message": "Prompt override deleted",
            "deleted": f"{deleted.category}.{deleted.operation_key}"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete prompt override: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# GET AVAILABLE OPERATIONS (for UI dropdown)
# ============================================================================
@router.get("/operations")
async def get_available_operations(
    current_user: dict = Depends(get_current_user_or_key)
):
    """
    Get list of all available operations from the default prompts.
    This is a static list matching useLLMPrompts.js structure.
    """
    operations = {
        "generate": [
            "generate-segment-script",
            "generate-ad-script",
            "generate-promo-script",
            "generate-cta-script",
            "generate-outro-script",
            "generate-coldopen-script",
            "generate-tease-script",
            "generate-episode-description",
            "generate-segment-title",
            "slug-generator",
            "generate-social-media-post"
        ],
        "analyze": [
            "analyze-script-tone",
            "analyze-script-length",
            "analyze-script-sentiment",
            "analyze-episode-structure",
            "analyze-pacing"
        ],
        "extract": [
            "extract-keywords",
            "extract-quotes",
            "extract-topics",
            "extract-metadata",
            "extract-timestamps"
        ],
        "refactor": [
            "refactor-shorten-script",
            "refactor-lengthen-script",
            "refactor-adjust-tone",
            "refactor-improve-clarity",
            "refactor-add-humor"
        ],
        "compose": [
            "compose-episode-summary",
            "compose-show-notes",
            "compose-newsletter",
            "compose-segment-transition"
        ]
    }

    return {
        "success": True,
        "operations": operations
    }


# ============================================================================
# TOGGLE OVERRIDE ENABLE/DISABLE
# ============================================================================
@router.post("/overrides/{override_id}/toggle")
async def toggle_prompt_override(
    override_id: str,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Toggle the is_enabled status of a prompt override"""
    try:
        toggle_query = text("""
            UPDATE prompt_overrides
            SET is_enabled = NOT is_enabled,
                updated_at = NOW()
            WHERE id = :id
            RETURNING is_enabled, category, operation_key
        """)

        result = db.execute(toggle_query, {"id": override_id})
        updated = result.first()

        if not updated:
            raise HTTPException(status_code=404, detail="Prompt override not found")

        db.commit()

        status = "enabled" if updated.is_enabled else "disabled"
        logger.info(f"Toggled prompt override {updated.category}.{updated.operation_key} to {status}")

        return {
            "success": True,
            "message": f"Prompt override {status}",
            "is_enabled": updated.is_enabled
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to toggle prompt override: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
