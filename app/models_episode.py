"""
Database models for episode management and blueprint templates
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime

class BlueprintTemplate(Base):
    """Blueprint templates for episode scaffolding"""
    __tablename__ = "blueprint_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    template_type = Column(String(50), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    template_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    nodes = relationship("BlueprintNode", back_populates="template", cascade="all, delete-orphan")
    episodes = relationship("EpisodeTemplate", back_populates="template")

class BlueprintNode(Base):
    """Hierarchical structure for blueprint templates"""
    __tablename__ = "blueprint_nodes"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("blueprint_templates.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(Integer, ForeignKey("blueprint_nodes.id", ondelete="CASCADE"), nullable=True)
    node_type = Column(String(20), nullable=False)  # 'directory', 'file'
    name = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)  # File content for file nodes
    sort_order = Column(Integer, default=0, nullable=False)
    is_required = Column(Boolean, default=True, nullable=False)

    # Relationships
    template = relationship("BlueprintTemplate", back_populates="nodes")
    parent = relationship("BlueprintNode", remote_side=[id], back_populates="children")
    children = relationship("BlueprintNode", back_populates="parent", cascade="all, delete-orphan")

class EpisodeTemplate(Base):
    """Episodes created through scaffolding"""
    __tablename__ = "episode_templates"

    id = Column(Integer, primary_key=True, index=True)
    episode_number = Column(String(10), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    episode_metadata = Column(JSON, nullable=True)
    template_id = Column(Integer, ForeignKey("blueprint_templates.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(20), default="draft", nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    file_path = Column(String(500), nullable=True)  # Physical filesystem path
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    template = relationship("BlueprintTemplate", back_populates="episodes")
    created_by_user = relationship("User", foreign_keys=[created_by])
    organization = relationship("Organization", foreign_keys=[organization_id])

# Pydantic models for API

class BlueprintTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    template_type: str = "episode"
    is_active: bool = True
    is_default: bool = False
    template_metadata: Optional[Dict[str, Any]] = None

class BlueprintTemplateCreate(BlueprintTemplateBase):
    pass

class BlueprintTemplateResponse(BlueprintTemplateBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class BlueprintNodeBase(BaseModel):
    node_type: str  # 'directory' or 'file'
    name: str
    content: Optional[str] = None
    sort_order: int = 0
    is_required: bool = True

class BlueprintNodeCreate(BlueprintNodeBase):
    parent_id: Optional[int] = None

class BlueprintNodeResponse(BlueprintNodeBase):
    id: int
    template_id: int
    parent_id: Optional[int] = None
    children: List['BlueprintNodeResponse'] = []

    class Config:
        from_attributes = True

class EpisodeTemplateBase(BaseModel):
    episode_number: str
    title: Optional[str] = None
    description: Optional[str] = None
    episode_metadata: Optional[Dict[str, Any]] = None
    status: str = "draft"

class EpisodeTemplateCreate(BaseModel):
    episode_number: Optional[str] = None  # Auto-generate if not provided
    template_id: Optional[int] = None     # Use default template if not provided
    title: Optional[str] = None
    description: Optional[str] = None
    episode_metadata: Optional[Dict[str, Any]] = None

class EpisodeTemplateResponse(EpisodeTemplateBase):
    id: int
    template_id: Optional[int] = None
    created_by: Optional[int] = None
    organization_id: Optional[int] = None
    file_path: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    template: Optional[BlueprintTemplateResponse] = None

    class Config:
        from_attributes = True

# Update forward references
BlueprintNodeResponse.model_rebuild()