"""
Segment LLM Data Router - API endpoints for the LLM Preprocessing Layer

Provides REST endpoints for:
- Triggering LLM extraction for segments
- Retrieving prechewed LLM data
- Batch extraction operations
- Stale data detection
- Episode-level LLM context aggregation

Part of the Universal LLM Framework (UFDP-compliant).
"""

from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging

from database import get_db
from auth.utils import get_current_user_or_key
from models_segment_llm import SegmentLLMData
from models_v2 import RundownItem
from services.segment_llm_extractor import SegmentLLMExtractor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/segments", tags=["segment-llm"])


# ============================================================================
# GET LLM DATA FOR A SEGMENT
# ============================================================================
@router.get("/{rundown_item_id}/llm-data")
async def get_segment_llm_data(
    rundown_item_id: int,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Get pre-extracted LLM data for a segment.

    Returns the prechewed data including entities, summaries, and quotes
    that can be used for downstream AI operations.

    Path Parameters:
    - rundown_item_id: The database ID of the rundown item

    Returns:
    - LLM data if exists, or stale status if extraction needed
    """
    try:
        # Check if rundown item exists
        rundown_item = db.query(RundownItem).filter(
            RundownItem.id == rundown_item_id
        ).first()

        if not rundown_item:
            raise HTTPException(status_code=404, detail="Rundown item not found")

        # Get LLM data
        llm_data = db.query(SegmentLLMData).filter(
            SegmentLLMData.rundown_item_id == rundown_item_id
        ).first()

        if not llm_data:
            # No data yet - return stale status
            return {
                "success": True,
                "has_data": False,
                "stale": True,
                "stale_reason": "no_llm_data",
                "rundown_item_id": rundown_item_id,
                "segment_title": rundown_item.title
            }

        # Check if stale
        stale_check = SegmentLLMExtractor.check_stale(db, rundown_item_id)

        return {
            "success": True,
            "has_data": True,
            "stale": stale_check.get("stale", False),
            "stale_reason": stale_check.get("reason") if stale_check.get("stale") else None,
            "data": llm_data.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get segment LLM data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# TRIGGER EXTRACTION FOR A SEGMENT
# ============================================================================
@router.post("/{rundown_item_id}/extract")
async def extract_segment_llm_data(
    rundown_item_id: int,
    extraction_params: Dict[str, Any] = Body(default={}),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Trigger LLM extraction for a segment.

    This endpoint initiates the extraction process which analyzes the segment
    content and extracts entities, summaries, and quotes.

    Path Parameters:
    - rundown_item_id: The database ID of the rundown item

    Body Parameters:
    - model: Optional model override (e.g., "mistral:7b", "claude-sonnet")
    - force: Force re-extraction even if data is current (default: false)

    Returns:
    - Extraction result with extracted data
    """
    try:
        # Validate rundown item exists
        rundown_item = db.query(RundownItem).filter(
            RundownItem.id == rundown_item_id
        ).first()

        if not rundown_item:
            raise HTTPException(status_code=404, detail="Rundown item not found")

        # Extract parameters
        model = extraction_params.get("model")
        force = extraction_params.get("force", False)

        logger.info(f"Starting LLM extraction for rundown item {rundown_item_id}")

        # Run extraction
        llm_data = await SegmentLLMExtractor.extract_segment_llm_data(
            db=db,
            rundown_item_id=rundown_item_id,
            model=model,
            force=force
        )

        return {
            "success": True,
            "rundown_item_id": rundown_item_id,
            "processing_status": llm_data.processing_status,
            "extraction_timestamp": llm_data.extraction_timestamp.isoformat() if llm_data.extraction_timestamp else None,
            "data": llm_data.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to extract segment LLM data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# UPDATE LLM DATA (MANUAL EDIT)
# ============================================================================
@router.put("/{rundown_item_id}/llm-data")
async def update_segment_llm_data(
    rundown_item_id: int,
    updates: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Manually update LLM data for a segment.

    Allows editing of extracted data for corrections or enhancements.

    Path Parameters:
    - rundown_item_id: The database ID of the rundown item

    Body Parameters:
    - llm_summary: Updated summary
    - llm_description: Updated description
    - extracted_people: Updated people list
    - extracted_organizations: Updated organizations list
    - extracted_topics: Updated topics list
    - key_quotes: Updated quotes list
    - needs_review: Set review flag
    """
    try:
        llm_data = db.query(SegmentLLMData).filter(
            SegmentLLMData.rundown_item_id == rundown_item_id
        ).first()

        if not llm_data:
            raise HTTPException(status_code=404, detail="LLM data not found. Run extraction first.")

        # Update allowed fields
        updatable_fields = [
            'llm_summary', 'llm_description', 'extracted_people',
            'extracted_organizations', 'extracted_institutions',
            'extracted_topics', 'key_quotes', 'needs_review'
        ]

        for field in updatable_fields:
            if field in updates:
                setattr(llm_data, field, updates[field])

        # Mark as manually updated
        if not llm_data.tier_metadata:
            llm_data.tier_metadata = {}
        llm_data.tier_metadata['manual_edit'] = {
            "timestamp": datetime.utcnow().isoformat(),
            "user": current_user.get('username', 'unknown')
        }

        db.commit()

        return {
            "success": True,
            "message": "LLM data updated successfully",
            "data": llm_data.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update segment LLM data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DELETE LLM DATA (FOR RE-EXTRACTION)
# ============================================================================
@router.delete("/{rundown_item_id}/llm-data")
async def delete_segment_llm_data(
    rundown_item_id: int,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Delete LLM data for a segment.

    Clears extracted data to allow fresh re-extraction.

    Path Parameters:
    - rundown_item_id: The database ID of the rundown item
    """
    try:
        llm_data = db.query(SegmentLLMData).filter(
            SegmentLLMData.rundown_item_id == rundown_item_id
        ).first()

        if not llm_data:
            raise HTTPException(status_code=404, detail="LLM data not found")

        db.delete(llm_data)
        db.commit()

        return {
            "success": True,
            "message": f"LLM data deleted for rundown item {rundown_item_id}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete segment LLM data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BATCH EXTRACTION
# ============================================================================
@router.post("/batch-extract")
async def batch_extract_llm_data(
    batch_params: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Trigger LLM extraction for multiple segments.

    Body Parameters:
    - rundown_item_ids: List of rundown item IDs to process
    - model: Optional model override
    - force: Force re-extraction (default: false)

    Returns:
    - Summary of extraction results
    """
    try:
        rundown_item_ids = batch_params.get("rundown_item_ids", [])
        model = batch_params.get("model")
        force = batch_params.get("force", False)

        if not rundown_item_ids:
            raise HTTPException(status_code=400, detail="rundown_item_ids is required")

        if len(rundown_item_ids) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 items per batch")

        logger.info(f"Starting batch extraction for {len(rundown_item_ids)} items")

        results = await SegmentLLMExtractor.batch_extract(
            db=db,
            rundown_item_ids=rundown_item_ids,
            model=model,
            force=force
        )

        return {
            "success": True,
            "results": results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# GET EPISODE LLM CONTEXT
# ============================================================================
@router.get("/episode/{episode_number}/llm-context")
async def get_episode_llm_context(
    episode_number: str,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Get aggregated LLM context for an entire episode.

    Combines prechewed data from all segments into a unified context
    that can be used for episode-level AI operations like descriptions
    and social media posts.

    Path Parameters:
    - episode_number: The episode number

    Returns:
    - Aggregated LLM context including all entities, summaries, and template variables
    """
    try:
        context = SegmentLLMExtractor.get_episode_llm_context(db, episode_number)

        return {
            "success": True,
            "context": context
        }

    except Exception as e:
        logger.error(f"Failed to get episode LLM context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# GET STALE SEGMENTS
# ============================================================================
@router.get("/llm-data/stale")
async def get_stale_segments(
    episode_number: Optional[str] = Query(None, description="Filter by episode"),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Get list of segments with stale or missing LLM data.

    Query Parameters:
    - episode_number: Optional filter to check specific episode

    Returns:
    - List of stale segments that need extraction
    """
    try:
        stale_items = SegmentLLMExtractor.get_stale_segments(db, episode_number)

        return {
            "success": True,
            "count": len(stale_items),
            "stale_items": stale_items
        }

    except Exception as e:
        logger.error(f"Failed to get stale segments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CHECK STALE STATUS FOR SINGLE SEGMENT
# ============================================================================
@router.get("/{rundown_item_id}/stale")
async def check_segment_stale(
    rundown_item_id: int,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Check if a segment's LLM data is stale.

    Path Parameters:
    - rundown_item_id: The database ID of the rundown item

    Returns:
    - Stale status and reason
    """
    try:
        stale_check = SegmentLLMExtractor.check_stale(db, rundown_item_id)

        return {
            "success": True,
            "rundown_item_id": rundown_item_id,
            **stale_check
        }

    except Exception as e:
        logger.error(f"Failed to check stale status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Import datetime for manual edit tracking
from datetime import datetime
