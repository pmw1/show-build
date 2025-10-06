"""
Role-Based Access Control (RBAC) Models for Show-Build
Comprehensive permission system with roles, groups, and granular permissions
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from typing import Optional
from datetime import datetime


# Association tables for many-to-many relationships
user_roles_table = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('assigned_at', DateTime(timezone=True), server_default=func.now()),
    Column('assigned_by', String(50), nullable=True),
    Column('expires_at', DateTime(timezone=True), nullable=True)
)

user_groups_table = Table(
    'user_groups', 
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('group_id', Integer, ForeignKey('groups.id'), primary_key=True),
    Column('joined_at', DateTime(timezone=True), server_default=func.now()),
    Column('added_by', String(50), nullable=True)
)

group_roles_table = Table(
    'group_roles',
    Base.metadata,
    Column('group_id', Integer, ForeignKey('groups.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('assigned_at', DateTime(timezone=True), server_default=func.now()),
    Column('assigned_by', String(50), nullable=True)
)

role_permissions_table = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True),
    Column('granted_at', DateTime(timezone=True), server_default=func.now()),
    Column('granted_by', String(50), nullable=True)
)


class Permission(Base):
    """Granular permissions for system resources and actions"""
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Permission identification
    name = Column(String(100), unique=True, nullable=False, index=True)  # e.g., "episodes.create"
    display_name = Column(String(255), nullable=False)  # e.g., "Create Episodes"
    description = Column(Text, nullable=True)
    
    # Permission categorization
    resource = Column(String(50), nullable=False, index=True)  # e.g., "episodes", "users", "organizations"
    action = Column(String(50), nullable=False, index=True)    # e.g., "create", "read", "update", "delete"
    scope = Column(String(50), nullable=False, default="global")  # "global", "organization", "own"
    
    # System permissions vs. custom permissions
    is_system = Column(Boolean, default=False)  # True for built-in permissions
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(50), nullable=True)
    
    # Relationships
    roles = relationship("Role", secondary=role_permissions_table, back_populates="permissions")
    
    def __repr__(self):
        return f"<Permission(name='{self.name}', resource='{self.resource}', action='{self.action}')>"


class Role(Base):
    """Roles that group permissions together"""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Role identification
    name = Column(String(100), unique=True, nullable=False, index=True)  # e.g., "Content Editor"
    slug = Column(String(100), unique=True, nullable=False, index=True)  # e.g., "content-editor"
    description = Column(Text, nullable=True)
    
    # Role hierarchy
    parent_role_id = Column(Integer, ForeignKey('roles.id'), nullable=True)
    level = Column(Integer, default=0)  # 0 = top level, higher numbers = more specific
    
    # Role properties
    is_system = Column(Boolean, default=False)  # True for built-in roles
    is_active = Column(Boolean, default=True)
    color = Column(String(7), nullable=True)  # Hex color for UI display
    
    # Organization context (nullable for global roles)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(50), nullable=True)
    
    # Relationships
    parent_role = relationship("Role", remote_side=[id], backref="child_roles")
    permissions = relationship("Permission", secondary=role_permissions_table, back_populates="roles")
    users = relationship("User", secondary=user_roles_table, back_populates="roles")
    groups = relationship("Group", secondary=group_roles_table, back_populates="roles")
    
    def __repr__(self):
        return f"<Role(name='{self.name}', level={self.level}, active={self.is_active})>"


class Group(Base):
    """Groups for organizing users with common role assignments"""
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Group identification
    name = Column(String(100), nullable=False, index=True)  # e.g., "Production Team"
    slug = Column(String(100), nullable=False, index=True)  # e.g., "production-team"
    description = Column(Text, nullable=True)
    
    # Group properties
    is_active = Column(Boolean, default=True)
    color = Column(String(7), nullable=True)  # Hex color for UI display
    
    # Organization context (groups are organization-specific)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)
    
    # Group settings
    auto_assign_new_users = Column(Boolean, default=False)  # Auto-assign new org users
    settings = Column(JSON, default=dict)  # Group-specific settings
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(50), nullable=True)
    
    # Relationships
    users = relationship("User", secondary=user_groups_table, back_populates="groups")
    roles = relationship("Role", secondary=group_roles_table, back_populates="groups")
    
    def __repr__(self):
        return f"<Group(name='{self.name}', organization_id={self.organization_id})>"


class UserPermissionOverride(Base):
    """Direct permission grants/denials for specific users"""
    __tablename__ = "user_permission_overrides"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Target user and permission
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    permission_id = Column(Integer, ForeignKey('permissions.id'), nullable=False, index=True)
    
    # Grant or deny
    is_granted = Column(Boolean, nullable=False)  # True = grant, False = deny
    
    # Context (optional resource-specific override)
    resource_type = Column(String(50), nullable=True)  # e.g., "episode"
    resource_id = Column(String(50), nullable=True)    # e.g., episode ID
    
    # Metadata
    granted_at = Column(DateTime(timezone=True), server_default=func.now())
    granted_by = Column(String(50), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    reason = Column(Text, nullable=True)  # Reason for the override
    
    # Relationships
    user = relationship("User", backref="permission_overrides")
    permission = relationship("Permission", backref="user_overrides")
    
    def __repr__(self):
        action = "grant" if self.is_granted else "deny"
        return f"<UserPermissionOverride(user_id={self.user_id}, permission_id={self.permission_id}, {action})>"


class AuditLog(Base):
    """Audit trail for permission and role changes"""
    __tablename__ = "rbac_audit_log"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Action details
    action = Column(String(50), nullable=False, index=True)  # "role_assigned", "permission_granted", etc.
    resource_type = Column(String(50), nullable=False)       # "user", "role", "group", "permission"
    resource_id = Column(Integer, nullable=False)            # ID of the affected resource
    
    # Actor information
    actor_type = Column(String(20), nullable=False)  # "user", "system", "api"
    actor_id = Column(String(50), nullable=False)    # Username or system identifier
    
    # Context
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=True)
    details = Column(JSON, default=dict)  # Additional context about the change
    
    # Client information
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<AuditLog(action='{self.action}', resource='{self.resource_type}:{self.resource_id}')>"