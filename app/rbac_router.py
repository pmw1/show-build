"""
RBAC API Router - Role-Based Access Control endpoints
Provides comprehensive API for managing roles, groups, permissions, and assignments
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from pydantic import BaseModel
from datetime import datetime

from database import get_db
from auth.utils import get_current_user_or_key
from rbac_service import RBACService, get_rbac_service, seed_default_permissions
from models_rbac import Permission, Role, Group, UserPermissionOverride, AuditLog
from models_user import User
from models_v2 import Organization

# Pydantic models for API requests/responses
class PermissionResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: Optional[str]
    resource: str
    action: str
    scope: str
    is_system: bool

class RoleResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str]
    level: int
    is_system: bool
    is_active: bool
    organization_id: Optional[int]
    permissions: List[PermissionResponse] = []

class GroupResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str]
    is_active: bool
    organization_id: int
    user_count: int = 0
    roles: List[RoleResponse] = []

class UserRoleAssignmentRequest(BaseModel):
    user_id: int
    role_id: int
    expires_at: Optional[datetime] = None

class UserGroupAssignmentRequest(BaseModel):
    user_id: int
    group_id: int

class PermissionOverrideRequest(BaseModel):
    user_id: int
    permission_name: str
    is_granted: bool
    expires_at: Optional[datetime] = None
    reason: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None

class CreateRoleRequest(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    organization_id: Optional[int] = None
    permission_names: List[str] = []

class CreateGroupRequest(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    organization_id: int
    auto_assign_new_users: bool = False

class UpdateRoleRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    permission_names: Optional[List[str]] = None

class UpdateGroupRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    auto_assign_new_users: Optional[bool] = None


router = APIRouter(prefix="/rbac", tags=["rbac"])


def require_rbac_access(current_user: dict = Depends(get_current_user_or_key)):
    """Dependency to check RBAC access permissions"""
    if current_user.get("access_level") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="RBAC management requires admin access"
        )
    return current_user


# Permission endpoints
@router.get("/permissions", response_model=List[PermissionResponse])
async def list_permissions(
    resource: Optional[str] = None,
    action: Optional[str] = None,
    scope: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_rbac_access)
):
    """List all permissions with optional filtering"""
    query = db.query(Permission)
    
    if resource:
        query = query.filter(Permission.resource == resource)
    if action:
        query = query.filter(Permission.action == action)
    if scope:
        query = query.filter(Permission.scope == scope)
    
    permissions = query.all()
    return [
        PermissionResponse(
            id=p.id,
            name=p.name,
            display_name=p.display_name,
            description=p.description,
            resource=p.resource,
            action=p.action,
            scope=p.scope,
            is_system=p.is_system
        )
        for p in permissions
    ]


@router.get("/permissions/{permission_id}", response_model=PermissionResponse)
async def get_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_rbac_access)
):
    """Get a specific permission"""
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    return PermissionResponse(
        id=permission.id,
        name=permission.name,
        display_name=permission.display_name,
        description=permission.description,
        resource=permission.resource,
        action=permission.action,
        scope=permission.scope,
        is_system=permission.is_system
    )


# Role endpoints
@router.get("/roles", response_model=List[RoleResponse])
async def list_roles(
    organization_id: Optional[int] = None,
    include_permissions: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_rbac_access)
):
    """List all roles with optional filtering"""
    query = db.query(Role).filter(Role.is_active == True)
    
    if organization_id:
        query = query.filter(
            (Role.organization_id == organization_id) | (Role.organization_id.is_(None))
        )
    
    roles = query.all()
    return [
        RoleResponse(
            id=role.id,
            name=role.name,
            slug=role.slug,
            description=role.description,
            level=role.level,
            is_system=role.is_system,
            is_active=role.is_active,
            organization_id=role.organization_id,
            permissions=[
                PermissionResponse(
                    id=p.id,
                    name=p.name,
                    display_name=p.display_name,
                    description=p.description,
                    resource=p.resource,
                    action=p.action,
                    scope=p.scope,
                    is_system=p.is_system
                )
                for p in role.permissions
            ] if include_permissions else []
        )
        for role in roles
    ]


@router.post("/roles", response_model=RoleResponse)
async def create_role(
    role_data: CreateRoleRequest,
    db: Session = Depends(get_db),
    rbac_service: RBACService = Depends(get_rbac_service),
    current_user: dict = Depends(require_rbac_access)
):
    """Create a new role"""
    # Check if slug already exists
    existing = db.query(Role).filter(Role.slug == role_data.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Role slug already exists")
    
    # Create role
    role = Role(
        name=role_data.name,
        slug=role_data.slug,
        description=role_data.description,
        organization_id=role_data.organization_id,
        is_system=False,
        created_by=current_user["username"]
    )
    
    db.add(role)
    db.flush()  # Get the role ID
    
    # Assign permissions
    for perm_name in role_data.permission_names:
        permission = db.query(Permission).filter(Permission.name == perm_name).first()
        if permission:
            role.permissions.append(permission)
    
    db.commit()
    
    return RoleResponse(
        id=role.id,
        name=role.name,
        slug=role.slug,
        description=role.description,
        level=role.level,
        is_system=role.is_system,
        is_active=role.is_active,
        organization_id=role.organization_id,
        permissions=[
            PermissionResponse(
                id=p.id,
                name=p.name,
                display_name=p.display_name,
                description=p.description,
                resource=p.resource,
                action=p.action,
                scope=p.scope,
                is_system=p.is_system
            )
            for p in role.permissions
        ]
    )


@router.put("/roles/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    role_data: UpdateRoleRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_rbac_access)
):
    """Update a role"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    if role.is_system:
        raise HTTPException(status_code=400, detail="Cannot modify system roles")
    
    # Update fields
    if role_data.name is not None:
        role.name = role_data.name
    if role_data.description is not None:
        role.description = role_data.description
    if role_data.is_active is not None:
        role.is_active = role_data.is_active
    
    # Update permissions
    if role_data.permission_names is not None:
        role.permissions.clear()
        for perm_name in role_data.permission_names:
            permission = db.query(Permission).filter(Permission.name == perm_name).first()
            if permission:
                role.permissions.append(permission)
    
    db.commit()
    
    return RoleResponse(
        id=role.id,
        name=role.name,
        slug=role.slug,
        description=role.description,
        level=role.level,
        is_system=role.is_system,
        is_active=role.is_active,
        organization_id=role.organization_id,
        permissions=[
            PermissionResponse(
                id=p.id,
                name=p.name,
                display_name=p.display_name,
                description=p.description,
                resource=p.resource,
                action=p.action,
                scope=p.scope,
                is_system=p.is_system
            )
            for p in role.permissions
        ]
    )


# Group endpoints
@router.get("/groups", response_model=List[GroupResponse])
async def list_groups(
    organization_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_rbac_access)
):
    """List all groups"""
    query = db.query(Group).filter(Group.is_active == True)
    
    if organization_id:
        query = query.filter(Group.organization_id == organization_id)
    
    groups = query.all()
    return [
        GroupResponse(
            id=group.id,
            name=group.name,
            slug=group.slug,
            description=group.description,
            is_active=group.is_active,
            organization_id=group.organization_id,
            user_count=len(group.users),
            roles=[
                RoleResponse(
                    id=role.id,
                    name=role.name,
                    slug=role.slug,
                    description=role.description,
                    level=role.level,
                    is_system=role.is_system,
                    is_active=role.is_active,
                    organization_id=role.organization_id
                )
                for role in group.roles
            ]
        )
        for group in groups
    ]


@router.post("/groups", response_model=GroupResponse)
async def create_group(
    group_data: CreateGroupRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_rbac_access)
):
    """Create a new group"""
    # Check if slug already exists in the organization
    existing = db.query(Group).filter(
        Group.slug == group_data.slug,
        Group.organization_id == group_data.organization_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Group slug already exists in organization")
    
    group = Group(
        name=group_data.name,
        slug=group_data.slug,
        description=group_data.description,
        organization_id=group_data.organization_id,
        auto_assign_new_users=group_data.auto_assign_new_users,
        created_by=current_user["username"]
    )
    
    db.add(group)
    db.commit()
    
    return GroupResponse(
        id=group.id,
        name=group.name,
        slug=group.slug,
        description=group.description,
        is_active=group.is_active,
        organization_id=group.organization_id,
        user_count=0,
        roles=[]
    )


# User assignment endpoints
@router.post("/users/assign-role")
async def assign_role_to_user(
    assignment: UserRoleAssignmentRequest,
    db: Session = Depends(get_db),
    rbac_service: RBACService = Depends(get_rbac_service),
    current_user: dict = Depends(require_rbac_access)
):
    """Assign a role to a user"""
    success = rbac_service.assign_role_to_user(
        assignment.user_id,
        assignment.role_id,
        current_user["username"],
        assignment.expires_at
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to assign role")
    
    return {"message": "Role assigned successfully"}


@router.delete("/users/{user_id}/roles/{role_id}")
async def remove_role_from_user(
    user_id: int,
    role_id: int,
    db: Session = Depends(get_db),
    rbac_service: RBACService = Depends(get_rbac_service),
    current_user: dict = Depends(require_rbac_access)
):
    """Remove a role from a user"""
    success = rbac_service.remove_role_from_user(
        user_id,
        role_id,
        current_user["username"]
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to remove role")
    
    return {"message": "Role removed successfully"}


@router.post("/users/permission-override")
async def create_permission_override(
    override: PermissionOverrideRequest,
    db: Session = Depends(get_db),
    rbac_service: RBACService = Depends(get_rbac_service),
    current_user: dict = Depends(require_rbac_access)
):
    """Create a permission override for a user"""
    success = rbac_service.create_permission_override(
        override.user_id,
        override.permission_name,
        override.is_granted,
        current_user["username"],
        override.expires_at,
        override.reason,
        override.resource_type,
        override.resource_id
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to create permission override")
    
    return {"message": "Permission override created successfully"}


@router.get("/users/{user_id}/permissions")
async def get_user_permissions(
    user_id: int,
    organization_id: Optional[int] = None,
    rbac_service: RBACService = Depends(get_rbac_service),
    current_user: dict = Depends(require_rbac_access)
):
    """Get all effective permissions for a user"""
    permissions = rbac_service.get_user_permissions(user_id, organization_id)
    return {"permissions": list(permissions)}


@router.get("/users/{user_id}/roles")
async def get_user_roles(
    user_id: int,
    organization_id: Optional[int] = None,
    rbac_service: RBACService = Depends(get_rbac_service),
    current_user: dict = Depends(require_rbac_access)
):
    """Get all roles assigned to a user"""
    roles = rbac_service.get_user_roles(user_id, organization_id)
    return {"roles": roles}


@router.get("/users/{user_id}/groups")
async def get_user_groups(
    user_id: int,
    organization_id: Optional[int] = None,
    rbac_service: RBACService = Depends(get_rbac_service),
    current_user: dict = Depends(require_rbac_access)
):
    """Get all groups a user belongs to"""
    groups = rbac_service.get_user_groups(user_id, organization_id)
    return {"groups": groups}


# Permission checking endpoint
@router.get("/check-permission")
async def check_user_permission(
    user_id: int,
    permission: str,
    organization_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    rbac_service: RBACService = Depends(get_rbac_service),
    current_user: dict = Depends(require_rbac_access)
):
    """Check if a user has a specific permission"""
    has_permission = rbac_service.check_permission(
        user_id, permission, organization_id, resource_type, resource_id
    )
    return {"has_permission": has_permission}


# Audit endpoints
@router.get("/audit")
async def get_audit_log(
    organization_id: Optional[int] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_rbac_access)
):
    """Get audit log entries"""
    query = db.query(AuditLog).order_by(AuditLog.created_at.desc())
    
    if organization_id:
        query = query.filter(AuditLog.organization_id == organization_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    
    total = query.count()
    audit_logs = query.offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "audit_logs": [
            {
                "id": log.id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "actor_type": log.actor_type,
                "actor_id": log.actor_id,
                "organization_id": log.organization_id,
                "details": log.details,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "created_at": log.created_at
            }
            for log in audit_logs
        ]
    }


# System management endpoints
@router.post("/seed-defaults")
async def seed_default_data(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_rbac_access)
):
    """Seed database with default permissions and roles"""
    try:
        seed_default_permissions(db)
        return {"message": "Default permissions and roles seeded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to seed defaults: {str(e)}")


@router.get("/system-status")
async def get_system_status(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_rbac_access)
):
    """Get RBAC system status and statistics"""
    stats = {
        "permissions_count": db.query(Permission).count(),
        "roles_count": db.query(Role).count(),
        "groups_count": db.query(Group).count(),
        "users_with_roles": db.query(User).join(User.roles).count(),
        "active_overrides": db.query(UserPermissionOverride).filter(
            (UserPermissionOverride.expires_at.is_(None)) |
            (UserPermissionOverride.expires_at > datetime.utcnow())
        ).count()
    }
    
    return {"status": "operational", "statistics": stats}