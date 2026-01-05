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
    """Blueprint templates for episode scaffolding with cascading inheritance"""
    __tablename__ = "blueprint_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    template_type = Column(String(50), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    template_metadata = Column(JSON, nullable=True)

    # Cascading inheritance support
    parent_template_id = Column(Integer, ForeignKey("blueprint_templates.id", ondelete="SET NULL"), nullable=True, index=True)
    inheritance_mode = Column(String(20), default="merge", nullable=False)  # 'merge', 'override', 'extend'

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    nodes = relationship("BlueprintNode", back_populates="template", cascade="all, delete-orphan")
    episodes = relationship("Blueprint", back_populates="template")

    # Self-referential relationship for template inheritance
    parent_template = relationship("BlueprintTemplate", remote_side=[id], foreign_keys=[parent_template_id], backref="child_templates")

    def get_resolved_nodes(self, db_session):
        """
        Resolve complete node structure with cascading inheritance.

        Inheritance modes:
        - 'merge': Combine parent and child nodes (child wins on conflicts)
        - 'override': Replace parent nodes entirely with child nodes
        - 'extend': Keep all parent nodes + add child nodes
        """
        nodes = {}

        # Recursively collect parent nodes first (breadth-first traversal)
        if self.parent_template_id and self.parent_template:
            parent_nodes = self.parent_template.get_resolved_nodes(db_session)
            nodes.update(parent_nodes)

        # Apply current template's nodes based on inheritance mode
        current_nodes = {node.name: node for node in self.nodes}

        if self.inheritance_mode == "override":
            # Replace all parent nodes
            nodes = current_nodes
        elif self.inheritance_mode == "extend":
            # Add to parent nodes (keep both)
            nodes.update(current_nodes)
        else:  # Default: "merge"
            # Merge: child overrides parent on name collision
            nodes.update(current_nodes)

        return nodes

    def get_resolved_metadata(self):
        """
        Resolve metadata with cascading inheritance.
        Child metadata overrides parent on key collision.
        """
        metadata = {}

        # Recursively collect parent metadata
        if self.parent_template_id and self.parent_template:
            parent_metadata = self.parent_template.get_resolved_metadata()
            metadata.update(parent_metadata)

        # Merge current template metadata
        if self.template_metadata:
            metadata.update(self.template_metadata)

        return metadata

class BlueprintNode(Base):
    """Hierarchical structure for blueprint templates"""
    __tablename__ = "blueprint_nodes"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("blueprint_templates.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(Integer, ForeignKey("blueprint_nodes.id", ondelete="CASCADE"), nullable=True)
    node_type = Column(String(20), nullable=False)  # 'directory', 'file', 'rundown_item'
    name = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)  # File content for file nodes, script content for rundown items
    sort_order = Column(Integer, default=0, nullable=False)
    is_required = Column(Boolean, default=True, nullable=False)

    # Rundown item metadata (for node_type = 'rundown_item')
    rundown_item_metadata = Column(JSON, nullable=True)  # {item_type, duration, status, etc.}

    # Relationships
    template = relationship("BlueprintTemplate", back_populates="nodes")
    parent = relationship("BlueprintNode", remote_side=[id], back_populates="children")
    children = relationship("BlueprintNode", back_populates="parent", cascade="all, delete-orphan")

class Blueprint(Base):
    """Episodes created through scaffolding (blueprint-based episodes)"""
    __tablename__ = "blueprints"

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

class BlueprintBase(BaseModel):
    episode_number: str
    title: Optional[str] = None
    description: Optional[str] = None
    episode_metadata: Optional[Dict[str, Any]] = None
    status: str = "draft"

class BlueprintCreate(BaseModel):
    episode_number: Optional[str] = None  # Auto-generate if not provided
    template_id: Optional[int] = None     # Use default template if not provided
    rundown_template_id: Optional[int] = None  # Optional rundown template to populate
    title: Optional[str] = None
    description: Optional[str] = None
    episode_metadata: Optional[Dict[str, Any]] = None

class BlueprintResponse(BlueprintBase):
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


class RundownTemplate(Base):
    """Rundown templates for automatic rundown population when creating episodes"""
    __tablename__ = "rundown_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    episode_template_id = Column(Integer, ForeignKey("blueprint_templates.id", ondelete="CASCADE"), nullable=False, index=True)
    is_default = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    organization = relationship("Organization", foreign_keys=[organization_id])
    episode_template = relationship("BlueprintTemplate", foreign_keys=[episode_template_id])
    items = relationship("RundownTemplateItem", back_populates="template", cascade="all, delete-orphan", order_by="RundownTemplateItem.sort_order")


class RundownTemplateItem(Base):
    """Individual items within a rundown template"""
    __tablename__ = "rundown_template_items"

    id = Column(Integer, primary_key=True, index=True)
    rundown_template_id = Column(Integer, ForeignKey("rundown_templates.id", ondelete="CASCADE"), nullable=False, index=True)
    item_type = Column(String(50), nullable=False)  # segment, ad, promo, etc.
    title = Column(String(255), nullable=True)
    slug = Column(String(100), nullable=True)
    script_content = Column(Text, nullable=True)
    duration = Column(String(20), nullable=True)  # e.g., "00:05:00"
    sort_order = Column(Integer, nullable=False)
    item_metadata = Column(JSON, nullable=True)  # Additional item properties
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    template = relationship("RundownTemplate", back_populates="items")


# Pydantic models for Rundown Templates

class RundownTemplateItemBase(BaseModel):
    item_type: str
    title: Optional[str] = None
    slug: Optional[str] = None
    script_content: Optional[str] = None
    duration: Optional[str] = None
    sort_order: int
    item_metadata: Optional[Dict[str, Any]] = None

class RundownTemplateItemCreate(RundownTemplateItemBase):
    pass

class RundownTemplateItemUpdate(BaseModel):
    item_type: Optional[str] = None
    title: Optional[str] = None
    slug: Optional[str] = None
    script_content: Optional[str] = None
    duration: Optional[str] = None
    sort_order: Optional[int] = None
    item_metadata: Optional[Dict[str, Any]] = None

class RundownTemplateItemResponse(RundownTemplateItemBase):
    id: int
    rundown_template_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class RundownTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    organization_id: int
    episode_template_id: int
    is_default: bool = False
    is_active: bool = True
    sort_order: int = 0

class RundownTemplateCreate(RundownTemplateBase):
    pass

class RundownTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

class RundownTemplateResponse(RundownTemplateBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: List[RundownTemplateItemResponse] = []

    class Config:
        from_attributes = True

class RundownTemplateClone(BaseModel):
    name: str
    description: Optional[str] = None

class RundownTemplateExport(BaseModel):
    template: RundownTemplateResponse
    items: List[RundownTemplateItemResponse]

class RundownTemplateImport(BaseModel):
    name: str
    description: Optional[str] = None
    organization_id: int
    episode_template_id: int
    items: List[RundownTemplateItemCreate]