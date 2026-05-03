"""
Todo API - Unified work queue for Claude and user todos.
All items stored in user_todos table, distinguished by created_by field.
Claude todos: created_by='claude'. User todos: everything else.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from database import get_db
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from database import Base
from auth.utils import get_current_user_or_key

router = APIRouter(prefix="/api/todos", tags=["todos"])

CLAUDE_CREATOR = "claude"


# SQLAlchemy model
class UserTodo(Base):
    __tablename__ = "user_todos"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String(20), default="normal")  # low, normal, high, critical
    status = Column(String(20), default="pending")  # pending, in_progress, completed, on_hold
    created_by = Column(String(100), nullable=True)
    assignee = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    sort_order = Column(Integer, nullable=True, index=True)


# Pydantic models
class UserTodoCreate(BaseModel):
    content: str
    description: Optional[str] = None
    priority: str = "normal"
    status: str = "pending"
    assignee: Optional[str] = None
    # Unified endpoint fallback — used only when no auth token is present
    # (e.g. Claude sync). For browser-user posts, created_by is derived
    # from the JWT / API key and this field is ignored.
    created_by: Optional[str] = None


class UserTodoUpdate(BaseModel):
    content: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assignee: Optional[str] = None


class UserTodoResponse(BaseModel):
    id: int
    content: str
    description: Optional[str]
    priority: str
    status: str
    created_by: Optional[str]
    assignee: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]
    sort_order: Optional[int] = None

    class Config:
        from_attributes = True


def _apply_status_update(todo, new_status):
    """Apply status change with completed_at bookkeeping."""
    todo.status = new_status
    if new_status == "completed" and not todo.completed_at:
        todo.completed_at = datetime.utcnow()
    elif new_status != "completed":
        todo.completed_at = None


def _apply_updates(todo, updates: UserTodoUpdate):
    """Apply partial updates to a todo item."""
    if updates.content is not None:
        todo.content = updates.content
    if updates.description is not None:
        todo.description = updates.description
    if updates.priority is not None:
        todo.priority = updates.priority
    if updates.assignee is not None:
        todo.assignee = updates.assignee
    if updates.status is not None:
        _apply_status_update(todo, updates.status)


def _sort_query(query):
    """Sort by explicit sort_order (drag-drop rank). Completed items sink to the bottom.
    Falls back to created_at for rows without a sort_order.
    """
    return query.order_by(
        UserTodo.status == "completed",
        UserTodo.sort_order.asc().nullslast(),
        UserTodo.created_at.desc()
    )


def _next_sort_order(db: Session) -> int:
    from sqlalchemy import func as _f
    max_val = db.query(_f.max(UserTodo.sort_order)).scalar()
    return (max_val or 0) + 1


# ── Unified Todo Endpoints ──
# These are the canonical endpoints. All todos live in one table and are
# distinguished only by `created_by` (which can be any username, "claude",
# or anything a service wants to use). The legacy /claude and /user routes
# below are kept as thin backward-compat wrappers.

@router.get("")
@router.get("/")
async def get_all_todos(
    status: Optional[str] = None,
    include_completed: bool = True,
    db: Session = Depends(get_db)
) -> List[UserTodoResponse]:
    """Return every todo in the system (unified work queue).

    Filters:
        status: exact match ('pending', 'in_progress', 'completed', 'on_hold')
        include_completed: if False, excludes completed items (default: True)
    """
    try:
        query = db.query(UserTodo)
        if status:
            query = query.filter(UserTodo.status == status)
        elif not include_completed:
            query = query.filter(UserTodo.status != "completed")
        todos = _sort_query(query).all()
        return [UserTodoResponse.from_orm(t) for t in todos]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching todos: {str(e)}")


@router.post("")
@router.post("/")
async def create_todo(
    todo: UserTodoCreate,
    db: Session = Depends(get_db)
) -> UserTodoResponse:
    """Create a new todo in the unified work queue.

    The `created_by` field in the request body identifies the submitter:
    a username, "claude", or any service name. The frontend should fill
    this from the logged-in user; Claude scripts send "claude".
    """
    try:
        creator = (todo.created_by or "").strip() or "unknown"
        new_todo = UserTodo(
            content=todo.content,
            description=todo.description,
            priority=todo.priority,
            status=todo.status,
            created_by=creator,
            assignee=todo.assignee or creator,
            sort_order=_next_sort_order(db)
        )
        db.add(new_todo)
        db.commit()
        db.refresh(new_todo)
        return UserTodoResponse.from_orm(new_todo)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating todo: {str(e)}")


@router.patch("/{todo_id}")
async def update_todo(
    todo_id: int,
    updates: UserTodoUpdate,
    db: Session = Depends(get_db)
) -> UserTodoResponse:
    """Update any todo by id (no creator filter)."""
    try:
        todo = db.query(UserTodo).filter(UserTodo.id == todo_id).first()
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found")
        _apply_updates(todo, updates)
        db.commit()
        db.refresh(todo)
        return UserTodoResponse.from_orm(todo)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating todo: {str(e)}")


@router.delete("/{todo_id}")
async def delete_todo(
    todo_id: int,
    db: Session = Depends(get_db)
):
    """Delete any todo by id (no creator filter)."""
    try:
        todo = db.query(UserTodo).filter(UserTodo.id == todo_id).first()
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found")
        db.delete(todo)
        db.commit()
        return {"success": True, "message": "Todo deleted"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting todo: {str(e)}")


class TodoReorderRequest(BaseModel):
    ids: List[int]


@router.post("/reorder")
async def reorder_todos(
    payload: TodoReorderRequest,
    db: Session = Depends(get_db)
):
    """Re-enumerate todos based on the given id order (drag-drop rank).
    The first id becomes rank 1 (highest priority), etc.
    """
    try:
        for rank, todo_id in enumerate(payload.ids, start=1):
            db.query(UserTodo).filter(UserTodo.id == todo_id).update(
                {UserTodo.sort_order: rank}, synchronize_session=False
            )
        db.commit()
        return {"success": True, "count": len(payload.ids)}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error reordering todos: {str(e)}")


# ── Claude Todos (legacy compat) ──

@router.get("/claude")
async def get_claude_todos(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
) -> List[UserTodoResponse]:
    """Get Claude's todo list from database"""
    try:
        query = db.query(UserTodo).filter(UserTodo.created_by == CLAUDE_CREATOR)
        if status:
            query = query.filter(UserTodo.status == status)
        todos = _sort_query(query).all()
        return [UserTodoResponse.from_orm(t) for t in todos]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching Claude todos: {str(e)}")


@router.post("/claude")
async def create_claude_todo(
    todo: UserTodoCreate,
    db: Session = Depends(get_db)
) -> UserTodoResponse:
    """Create a new Claude todo"""
    try:
        new_todo = UserTodo(
            content=todo.content,
            description=todo.description,
            priority=todo.priority,
            status=todo.status,
            created_by=CLAUDE_CREATOR,
            assignee=todo.assignee or CLAUDE_CREATOR
        )
        db.add(new_todo)
        db.commit()
        db.refresh(new_todo)
        return UserTodoResponse.from_orm(new_todo)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating Claude todo: {str(e)}")


@router.patch("/claude/{todo_id}")
async def update_claude_todo(
    todo_id: int,
    updates: UserTodoUpdate,
    db: Session = Depends(get_db)
) -> UserTodoResponse:
    """Update a Claude todo"""
    try:
        todo = db.query(UserTodo).filter(
            UserTodo.id == todo_id,
            UserTodo.created_by == CLAUDE_CREATOR
        ).first()
        if not todo:
            raise HTTPException(status_code=404, detail="Claude todo not found")
        _apply_updates(todo, updates)
        db.commit()
        db.refresh(todo)
        return UserTodoResponse.from_orm(todo)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating Claude todo: {str(e)}")


@router.delete("/claude/{todo_id}")
async def delete_claude_todo(
    todo_id: int,
    db: Session = Depends(get_db)
):
    """Delete a Claude todo"""
    try:
        todo = db.query(UserTodo).filter(
            UserTodo.id == todo_id,
            UserTodo.created_by == CLAUDE_CREATOR
        ).first()
        if not todo:
            raise HTTPException(status_code=404, detail="Claude todo not found")
        db.delete(todo)
        db.commit()
        return {"success": True, "message": "Claude todo deleted"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting Claude todo: {str(e)}")


# ── User Todos ──

@router.get("/user")
async def get_user_todos(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
) -> List[UserTodoResponse]:
    """Get user-created todos (excludes Claude todos)"""
    try:
        query = db.query(UserTodo).filter(
            (UserTodo.created_by != CLAUDE_CREATOR) | (UserTodo.created_by.is_(None))
        )
        if status:
            query = query.filter(UserTodo.status == status)
        todos = _sort_query(query).all()
        return [UserTodoResponse.from_orm(todo) for todo in todos]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user todos: {str(e)}")


@router.post("/user")
async def create_user_todo(
    todo: UserTodoCreate,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
) -> UserTodoResponse:
    """Create a new user todo"""
    try:
        username = current_user.get("username", current_user.get("client_name", "unknown"))
        new_todo = UserTodo(
            content=todo.content,
            description=todo.description,
            priority=todo.priority,
            status="pending",
            created_by=username,
            assignee=todo.assignee
        )
        db.add(new_todo)
        db.commit()
        db.refresh(new_todo)
        return UserTodoResponse.from_orm(new_todo)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating todo: {str(e)}")


@router.patch("/user/{todo_id}")
async def update_user_todo(
    todo_id: int,
    updates: UserTodoUpdate,
    db: Session = Depends(get_db)
) -> UserTodoResponse:
    """Update a user todo"""
    try:
        todo = db.query(UserTodo).filter(UserTodo.id == todo_id).first()
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found")
        _apply_updates(todo, updates)
        db.commit()
        db.refresh(todo)
        return UserTodoResponse.from_orm(todo)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating todo: {str(e)}")


@router.delete("/user/{todo_id}")
async def delete_user_todo(
    todo_id: int,
    db: Session = Depends(get_db)
):
    """Delete a user todo"""
    try:
        todo = db.query(UserTodo).filter(UserTodo.id == todo_id).first()
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found")
        db.delete(todo)
        db.commit()
        return {"success": True, "message": "Todo deleted"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting todo: {str(e)}")
