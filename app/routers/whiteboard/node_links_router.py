"""
Whiteboard node linking endpoints: create, list, delete node links.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from database import get_db
from auth.utils import get_current_user_or_key
from models_whiteboard import Whiteboard, WhiteboardItem, WhiteboardNodeLink
from ._shared import NodeLinkCreate, NodeLinkResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["whiteboard"])


@router.post("/{identifier}/link-nodes")
async def create_node_link(
    identifier: str,
    link_data: NodeLinkCreate,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Create a visual connection between two whiteboard nodes.
    """
    user_id = current_user.get("user_id")

    # Get whiteboard
    is_episode = identifier.isdigit() and len(identifier) == 4
    if is_episode:
        whiteboard = db.query(Whiteboard).filter(
            Whiteboard.episode_number == identifier,
            Whiteboard.created_by == user_id
        ).first()
    else:
        whiteboard = db.query(Whiteboard).filter(
            Whiteboard.workspace_id == identifier,
            Whiteboard.created_by == user_id
        ).first()

    if not whiteboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Whiteboard not found"
        )

    # Verify both items exist and belong to this whiteboard
    source_item = db.query(WhiteboardItem).filter(
        WhiteboardItem.id == link_data.source_item_id,
        WhiteboardItem.whiteboard_id == whiteboard.id
    ).first()

    target_item = db.query(WhiteboardItem).filter(
        WhiteboardItem.id == link_data.target_item_id,
        WhiteboardItem.whiteboard_id == whiteboard.id
    ).first()

    if not source_item or not target_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both items not found in whiteboard"
        )

    # Create link
    node_link = WhiteboardNodeLink(
        whiteboard_id=whiteboard.id,
        source_item_id=link_data.source_item_id,
        target_item_id=link_data.target_item_id,
        relationship_type=link_data.relationship_type,
        label=link_data.label,
        color=link_data.color
    )
    db.add(node_link)
    db.commit()
    db.refresh(node_link)

    logger.info(f"Created node link from item {link_data.source_item_id} to {link_data.target_item_id}")

    return NodeLinkResponse.from_orm(node_link)


@router.get("/{identifier}/node-links")
async def get_node_links(
    identifier: str,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Get all node links for a whiteboard.
    """
    user_id = current_user.get("user_id")

    # Get whiteboard
    is_episode = identifier.isdigit() and len(identifier) == 4
    if is_episode:
        whiteboard = db.query(Whiteboard).filter(
            Whiteboard.episode_number == identifier,
            Whiteboard.created_by == user_id
        ).first()
    else:
        whiteboard = db.query(Whiteboard).filter(
            Whiteboard.workspace_id == identifier,
            Whiteboard.created_by == user_id
        ).first()

    if not whiteboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Whiteboard not found"
        )

    links = db.query(WhiteboardNodeLink).filter(
        WhiteboardNodeLink.whiteboard_id == whiteboard.id
    ).all()

    return {
        "links": [NodeLinkResponse.from_orm(link) for link in links]
    }


@router.delete("/{identifier}/link-nodes/{link_id}")
async def delete_node_link(
    identifier: str,
    link_id: int,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Delete a node link.
    """
    user_id = current_user.get("user_id")

    # Get whiteboard
    is_episode = identifier.isdigit() and len(identifier) == 4
    if is_episode:
        whiteboard = db.query(Whiteboard).filter(
            Whiteboard.episode_number == identifier,
            Whiteboard.created_by == user_id
        ).first()
    else:
        whiteboard = db.query(Whiteboard).filter(
            Whiteboard.workspace_id == identifier,
            Whiteboard.created_by == user_id
        ).first()

    if not whiteboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Whiteboard not found"
        )

    # Get and delete link
    link = db.query(WhiteboardNodeLink).filter(
        WhiteboardNodeLink.id == link_id,
        WhiteboardNodeLink.whiteboard_id == whiteboard.id
    ).first()

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node link not found"
        )

    db.delete(link)
    db.commit()

    logger.info(f"Deleted node link {link_id}")

    return {
        "success": True,
        "message": "Node link deleted"
    }
