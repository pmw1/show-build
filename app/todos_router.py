"""
Todo API - Manage Claude todos and user high-level notes
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from pydantic import BaseModel
from datetime import datetime
from database import get_db
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from database import Base
from auth.utils import get_current_user_or_key
import json
from pathlib import Path

router = APIRouter(prefix="/api/todos", tags=["todos"])

# SQLAlchemy model for user todos
class UserTodo(Base):
    __tablename__ = "user_todos"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String(20), default="normal")  # low, normal, high, critical
    status = Column(String(20), default="pending")  # pending, in_progress, completed, on_hold
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

# Pydantic models
class ClaudeTodoItem(BaseModel):
    content: str
    status: str
    activeForm: str

class UserTodoCreate(BaseModel):
    content: str
    description: Optional[str] = None
    priority: str = "normal"

class UserTodoUpdate(BaseModel):
    content: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None

class UserTodoResponse(BaseModel):
    id: int
    content: str
    description: Optional[str]
    priority: str
    status: str
    created_by: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

# Find Claude's todo file
def find_claude_todo_file() -> Optional[Path]:
    """Find Claude's active todo list JSON file"""
    todos_dir = Path("/home/kevin/.claude/todos")

    if not todos_dir.exists():
        return None

    # Look for agent todo files
    json_files = list(todos_dir.glob("*-agent-*.json"))

    if not json_files:
        return None

    # Return the most recently modified file
    return max(json_files, key=lambda p: p.stat().st_mtime)

@router.get("/claude")
async def get_claude_todos() -> List[ClaudeTodoItem]:
    """Get Claude's current todo list"""
    try:
        todo_file = find_claude_todo_file()

        if not todo_file or not todo_file.exists():
            return []

        with open(todo_file, 'r') as f:
            todos = json.load(f)

        return [ClaudeTodoItem(**todo) for todo in todos]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading Claude todos: {str(e)}")

@router.get("/user")
async def get_user_todos(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
) -> List[UserTodoResponse]:
    """Get user-created high-level todos"""
    try:
        query = db.query(UserTodo)

        if status:
            query = query.filter(UserTodo.status == status)

        todos = query.order_by(
            UserTodo.status == "completed",  # Completed last
            UserTodo.priority.desc(),
            UserTodo.created_at.desc()
        ).all()

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
            created_by=username
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

        # Update fields if provided
        if updates.content is not None:
            todo.content = updates.content
        if updates.description is not None:
            todo.description = updates.description
        if updates.priority is not None:
            todo.priority = updates.priority
        if updates.status is not None:
            todo.status = updates.status

            # Set completed_at when marking as completed
            if updates.status == "completed" and not todo.completed_at:
                todo.completed_at = datetime.utcnow()
            elif updates.status != "completed":
                todo.completed_at = None

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
