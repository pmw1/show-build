"""
Blueprint Node Configuration API Router
Manages episode directory blueprint nodes (Settings > Content > Episode Blueprint).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from auth.utils import get_current_user_or_key
from models_episode import (
    BlueprintNode,
    BlueprintNodeCreate,
    BlueprintNodeUpdate,
    BlueprintNodeResponse,
)
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["blueprint-config"])

DEFAULT_TEMPLATE_ID = 8


@router.get("/", response_model=List[BlueprintNodeResponse])
async def list_blueprint_nodes(
    template_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
):
    """List all blueprint nodes for a template (flat list with parent_id for tree building)."""
    try:
        tid = template_id or DEFAULT_TEMPLATE_ID
        nodes = db.query(BlueprintNode).filter(
            BlueprintNode.template_id == tid
        ).order_by(
            BlueprintNode.parent_id.nullsfirst(),
            BlueprintNode.sort_order,
            BlueprintNode.name
        ).all()
        return nodes
    except Exception as e:
        logger.error(f"Error listing blueprint nodes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{node_id}", response_model=BlueprintNodeResponse)
async def get_blueprint_node(
    node_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
):
    """Get a single blueprint node."""
    try:
        node = db.query(BlueprintNode).filter(BlueprintNode.id == node_id).first()
        if not node:
            raise HTTPException(status_code=404, detail=f"Blueprint node {node_id} not found")
        return node
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting blueprint node {node_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=BlueprintNodeResponse, status_code=status.HTTP_201_CREATED)
async def create_blueprint_node(
    node_data: BlueprintNodeCreate,
    template_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
):
    """Create a new blueprint node."""
    try:
        tid = template_id or DEFAULT_TEMPLATE_ID

        # Validate parent exists if specified
        if node_data.parent_id:
            parent = db.query(BlueprintNode).filter(
                BlueprintNode.id == node_data.parent_id,
                BlueprintNode.template_id == tid
            ).first()
            if not parent:
                raise HTTPException(status_code=400, detail=f"Parent node {node_data.parent_id} not found")

        node = BlueprintNode(
            template_id=tid,
            **node_data.model_dump()
        )
        db.add(node)
        db.commit()
        db.refresh(node)

        logger.info(f"Created blueprint node: {node.name} (ID: {node.id})")
        return node

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating blueprint node: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{node_id}", response_model=BlueprintNodeResponse)
async def update_blueprint_node(
    node_id: int,
    node_data: BlueprintNodeUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
):
    """Update a blueprint node (name, description, sort_order, etc.)."""
    try:
        node = db.query(BlueprintNode).filter(BlueprintNode.id == node_id).first()
        if not node:
            raise HTTPException(status_code=404, detail=f"Blueprint node {node_id} not found")

        # Validate parent if changing
        update_data = node_data.model_dump(exclude_unset=True)
        if 'parent_id' in update_data and update_data['parent_id'] is not None:
            if update_data['parent_id'] == node_id:
                raise HTTPException(status_code=400, detail="Node cannot be its own parent")
            parent = db.query(BlueprintNode).filter(
                BlueprintNode.id == update_data['parent_id'],
                BlueprintNode.template_id == node.template_id
            ).first()
            if not parent:
                raise HTTPException(status_code=400, detail=f"Parent node {update_data['parent_id']} not found")

        for field, value in update_data.items():
            setattr(node, field, value)

        db.commit()
        db.refresh(node)

        logger.info(f"Updated blueprint node: {node.name} (ID: {node.id})")
        return node

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating blueprint node {node_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_blueprint_node(
    node_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
):
    """Delete a blueprint node (cascades to children)."""
    try:
        node = db.query(BlueprintNode).filter(BlueprintNode.id == node_id).first()
        if not node:
            raise HTTPException(status_code=404, detail=f"Blueprint node {node_id} not found")

        node_name = node.name
        db.delete(node)
        db.commit()

        logger.info(f"Deleted blueprint node: {node_name} (ID: {node_id})")
        return None

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting blueprint node {node_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
