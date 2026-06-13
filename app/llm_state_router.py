"""
LLM State Management Router

Handles persistence of LLM operations and notifications across page reloads.
Stores user-specific LLM state in PostgreSQL for universal framework.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import json

from database import get_db, Base
from auth.utils import get_current_user_or_key
from models_user import User
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey

router = APIRouter(prefix="/api/llm", tags=["llm-state"])


# ===== Database Models =====

class LLMOperation(Base):
    """Active LLM operations - survives page reload"""
    __tablename__ = "llm_operations"

    id = Column(String, primary_key=True)  # e.g., "llm-op-123"
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Operation details
    scope = Column(String, nullable=False)  # field, card, item, asset, etc.
    target_id = Column(String, nullable=False)  # Unique identifier for target element
    operation = Column(String, nullable=False)  # analyzing, generating, modifying, etc.
    state = Column(String, nullable=False)  # analyzing, generating, approved, rejected, etc.

    # Metadata
    model = Column(String)  # AI model name (e.g., "qwen2.5-coder:7b")
    message = Column(Text)  # Status message
    operation_metadata = Column(Text)  # JSON-encoded metadata
    priority = Column(String)  # critical, high, normal, low

    # Timestamps
    start_time = Column(Integer, nullable=False)  # Unix timestamp in ms
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Flags
    persistent = Column(Boolean, default=False)  # Should survive reload


class LLMNotification(Base):
    """LLM notifications - user feedback queue"""
    __tablename__ = "llm_notifications"

    id = Column(String, primary_key=True)  # e.g., "notif-456"
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Notification details
    title = Column(String, nullable=False)
    message = Column(Text)
    priority = Column(String)  # critical, high, normal, low
    notification_type = Column(String)  # operation-start, operation-complete, operation-error, etc.

    # Related operation
    operation_id = Column(String)  # Reference to LLMOperation.id

    # Status
    success = Column(Boolean, nullable=True)  # True/False/None for success/error/neutral
    read = Column(Boolean, default=False)
    dismissed = Column(Boolean, default=False)

    # Metadata
    notification_metadata = Column(Text)  # JSON-encoded additional data
    error = Column(Text)  # JSON-encoded error info if failed

    # Timestamps
    timestamp = Column(Integer, nullable=False)  # Unix timestamp in ms
    created_at = Column(DateTime, default=datetime.utcnow)


# ===== Pydantic Models =====

class OperationData(BaseModel):
    id: str
    scope: str
    targetId: str
    operation: str
    state: str
    model: Optional[str] = None
    message: Optional[str] = None
    metadata: Optional[dict] = None
    priority: Optional[str] = "normal"
    startTime: int
    persistent: bool = False


class NotificationData(BaseModel):
    id: str
    title: str
    message: Optional[str] = None
    priority: Optional[str] = "normal"
    type: str
    operationId: Optional[str] = None
    success: Optional[bool] = None
    read: bool = False
    dismissed: bool = False
    timestamp: int
    error: Optional[dict] = None


class OperationsSaveRequest(BaseModel):
    operations: List[OperationData]


class NotificationsSaveRequest(BaseModel):
    notifications: List[NotificationData]


# ===== API Endpoints =====

@router.get("/operations")
async def get_operations(
    current_user: User = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Get all active LLM operations for current user
    """
    operations = db.query(LLMOperation).filter(
        LLMOperation.user_id == current_user['id']
    ).all()

    # Convert to dict format expected by frontend
    operations_data = []
    for op in operations:
        operations_data.append({
            "id": op.id,
            "scope": op.scope,
            "targetId": op.target_id,
            "operation": op.operation,
            "state": op.state,
            "model": op.model,
            "message": op.message,
            "metadata": json.loads(op.operation_metadata) if op.operation_metadata else {},
            "priority": op.priority,
            "startTime": op.start_time,
            "persistent": op.persistent
        })

    return {"operations": operations_data}


@router.post("/operations")
async def save_operations(
    request: OperationsSaveRequest,
    current_user: User = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Save/update LLM operations for current user (upsert)
    Deletes operations not in the request (cleanup)
    """
    # Get current operation IDs from request
    incoming_ids = {op.id for op in request.operations}

    # Delete operations that are no longer active
    db.query(LLMOperation).filter(
        LLMOperation.user_id == current_user['id'],
        ~LLMOperation.id.in_(incoming_ids)
    ).delete(synchronize_session=False)

    # Upsert each operation
    for op_data in request.operations:
        existing = db.query(LLMOperation).filter(
            LLMOperation.id == op_data.id,
            LLMOperation.user_id == current_user['id']
        ).first()

        if existing:
            # Update existing
            existing.scope = op_data.scope
            existing.target_id = op_data.targetId
            existing.operation = op_data.operation
            existing.state = op_data.state
            existing.model = op_data.model
            existing.message = op_data.message
            existing.operation_metadata = json.dumps(op_data.metadata) if op_data.metadata else None
            existing.priority = op_data.priority
            existing.start_time = op_data.startTime
            existing.persistent = op_data.persistent
            existing.updated_at = datetime.utcnow()
        else:
            # Create new
            new_op = LLMOperation(
                id=op_data.id,
                user_id=current_user['id'],
                scope=op_data.scope,
                target_id=op_data.targetId,
                operation=op_data.operation,
                state=op_data.state,
                model=op_data.model,
                message=op_data.message,
                operation_metadata=json.dumps(op_data.metadata) if op_data.metadata else None,
                priority=op_data.priority,
                start_time=op_data.startTime,
                persistent=op_data.persistent
            )
            db.add(new_op)

    db.commit()

    return {
        "success": True,
        "saved": len(request.operations),
        "message": f"Saved {len(request.operations)} LLM operations"
    }


@router.get("/notifications")
async def get_notifications(
    limit: int = 50,
    current_user: User = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Get recent LLM notifications for current user.

    NOTE: the LLMNotification model here expects columns (user_id, title,
    priority, ...) that the real llm_notifications table (migration g009) does
    NOT have — it has asset_id/type/seen/etc. So this query raises
    UndefinedColumn -> 500. Until the model/table mismatch is resolved (todo #30),
    fail gracefully with an empty list instead of 500ing on every dashboard load.
    The working notification path is /api/llm-notifications/unseen (misc_router).
    """
    try:
        notifications = db.query(LLMNotification).filter(
            LLMNotification.user_id == current_user['id']
        ).order_by(
            LLMNotification.timestamp.desc()
        ).limit(limit).all()
    except Exception as e:
        from sqlalchemy import text as _sql_text  # noqa: F401
        db.rollback()
        import logging
        logging.getLogger(__name__).warning(
            "llm/notifications query failed (model/table mismatch, todo #30): %s", e
        )
        return {"notifications": []}

    # Convert to dict format expected by frontend
    notifications_data = []
    for notif in notifications:
        notifications_data.append({
            "id": notif.id,
            "title": notif.title,
            "message": notif.message,
            "priority": notif.priority,
            "type": notif.notification_type,
            "operationId": notif.operation_id,
            "success": notif.success,
            "read": notif.read,
            "dismissed": notif.dismissed,
            "timestamp": notif.timestamp,
            "error": json.loads(notif.error) if notif.error else None
        })

    return {"notifications": notifications_data}


@router.post("/notifications")
async def save_notifications(
    request: NotificationsSaveRequest,
    current_user: User = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Save/update LLM notifications for current user (upsert)
    """
    # Upsert each notification
    for notif_data in request.notifications:
        existing = db.query(LLMNotification).filter(
            LLMNotification.id == notif_data.id,
            LLMNotification.user_id == current_user['id']
        ).first()

        if existing:
            # Update existing
            existing.title = notif_data.title
            existing.message = notif_data.message
            existing.priority = notif_data.priority
            existing.notification_type = notif_data.type
            existing.operation_id = notif_data.operationId
            existing.success = notif_data.success
            existing.read = notif_data.read
            existing.dismissed = notif_data.dismissed
            existing.timestamp = notif_data.timestamp
            existing.error = json.dumps(notif_data.error) if notif_data.error else None
        else:
            # Create new
            new_notif = LLMNotification(
                id=notif_data.id,
                user_id=current_user['id'],
                title=notif_data.title,
                message=notif_data.message,
                priority=notif_data.priority,
                notification_type=notif_data.type,
                operation_id=notif_data.operationId,
                success=notif_data.success,
                read=notif_data.read,
                dismissed=notif_data.dismissed,
                timestamp=notif_data.timestamp,
                error=json.dumps(notif_data.error) if notif_data.error else None
            )
            db.add(new_notif)

    db.commit()

    return {
        "success": True,
        "saved": len(request.notifications),
        "message": f"Saved {len(request.notifications)} notifications"
    }


@router.delete("/operations/{operation_id}")
async def delete_operation(
    operation_id: str,
    current_user: User = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Delete a specific LLM operation
    """
    deleted = db.query(LLMOperation).filter(
        LLMOperation.id == operation_id,
        LLMOperation.user_id == current_user['id']
    ).delete()

    db.commit()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Operation not found")

    return {"success": True, "message": f"Deleted operation {operation_id}"}


@router.delete("/notifications/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Delete a specific notification
    """
    deleted = db.query(LLMNotification).filter(
        LLMNotification.id == notification_id,
        LLMNotification.user_id == current_user['id']
    ).delete()

    db.commit()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {"success": True, "message": f"Deleted notification {notification_id}"}


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """
    Mark a notification as read
    """
    notif = db.query(LLMNotification).filter(
        LLMNotification.id == notification_id,
        LLMNotification.user_id == current_user['id']
    ).first()

    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    notif.read = True
    db.commit()

    return {"success": True, "message": "Notification marked as read"}
