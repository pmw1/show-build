"""
RBAC Service - Permission checking and role management
Provides comprehensive permission checking and RBAC operations
"""
from typing import List, Dict, Optional, Set, Union
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from models_rbac import Permission, Role, Group, UserPermissionOverride, AuditLog
from models_user import User
from models_v2 import Organization
from database import get_db
from functools import wraps
from fastapi import HTTPException, status, Depends
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class RBACService:
    """Core RBAC service for permission checking and management"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_permissions(self, user_id: int, organization_id: Optional[int] = None) -> Set[str]:
        """
        Get all effective permissions for a user
        Combines role permissions, group permissions, and direct overrides
        """
        permissions = set()
        
        # Get user
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return permissions
        
        # 1. Get permissions from direct role assignments
        role_permissions = self.db.query(Permission.name)\
            .join(Role.permissions)\
            .join(Role.users)\
            .filter(User.id == user_id)
        
        # Filter by organization if specified
        if organization_id:
            role_permissions = role_permissions.filter(
                or_(Role.organization_id == organization_id, Role.organization_id.is_(None))
            )
        
        permissions.update([p.name for p in role_permissions.all()])
        
        # 2. Get permissions from group role assignments
        group_permissions = self.db.query(Permission.name)\
            .join(Role.permissions)\
            .join(Role.groups)\
            .join(Group.users)\
            .filter(User.id == user_id)
        
        if organization_id:
            group_permissions = group_permissions.filter(Group.organization_id == organization_id)
        
        permissions.update([p.name for p in group_permissions.all()])
        
        # 3. Apply user-specific permission overrides
        overrides = self.db.query(UserPermissionOverride)\
            .join(Permission)\
            .filter(UserPermissionOverride.user_id == user_id)\
            .filter(
                or_(
                    UserPermissionOverride.expires_at.is_(None),
                    UserPermissionOverride.expires_at > datetime.utcnow()
                )
            ).all()
        
        for override in overrides:
            if override.is_granted:
                permissions.add(override.permission.name)
            else:
                permissions.discard(override.permission.name)
        
        logger.info(f"User {user_id} effective permissions: {permissions}")
        return permissions
    
    def check_permission(self, user_id: int, permission: str, 
                        organization_id: Optional[int] = None,
                        resource_type: Optional[str] = None,
                        resource_id: Optional[str] = None) -> bool:
        """
        Check if user has a specific permission
        Supports context-aware permission checking
        """
        # Get all user permissions
        user_permissions = self.get_user_permissions(user_id, organization_id)
        
        # Direct permission match
        if permission in user_permissions:
            return True
        
        # Check for wildcard permissions (e.g., "episodes.*" grants "episodes.create")
        permission_parts = permission.split('.')
        if len(permission_parts) >= 2:
            resource, action = permission_parts[0], permission_parts[1]
            wildcard_permission = f"{resource}.*"
            if wildcard_permission in user_permissions:
                return True
        
        # Check for admin permissions (admin role typically has global access)
        if "admin.*" in user_permissions or "*" in user_permissions:
            return True
        
        # Context-specific permission checking
        if resource_type and resource_id:
            # Check for resource-specific overrides
            override = self.db.query(UserPermissionOverride)\
                .join(Permission)\
                .filter(
                    UserPermissionOverride.user_id == user_id,
                    Permission.name == permission,
                    UserPermissionOverride.resource_type == resource_type,
                    UserPermissionOverride.resource_id == str(resource_id),
                    or_(
                        UserPermissionOverride.expires_at.is_(None),
                        UserPermissionOverride.expires_at > datetime.utcnow()
                    )
                ).first()
            
            if override:
                return override.is_granted
        
        return False
    
    def get_user_roles(self, user_id: int, organization_id: Optional[int] = None) -> List[Dict]:
        """Get all roles assigned to a user"""
        query = self.db.query(Role)\
            .join(Role.users)\
            .filter(User.id == user_id)
        
        if organization_id:
            query = query.filter(
                or_(Role.organization_id == organization_id, Role.organization_id.is_(None))
            )
        
        roles = query.all()
        return [
            {
                "id": role.id,
                "name": role.name,
                "slug": role.slug,
                "description": role.description,
                "organization_id": role.organization_id,
                "is_system": role.is_system
            }
            for role in roles
        ]
    
    def get_user_groups(self, user_id: int, organization_id: Optional[int] = None) -> List[Dict]:
        """Get all groups a user belongs to"""
        query = self.db.query(Group)\
            .join(Group.users)\
            .filter(User.id == user_id)
        
        if organization_id:
            query = query.filter(Group.organization_id == organization_id)
        
        groups = query.all()
        return [
            {
                "id": group.id,
                "name": group.name,
                "slug": group.slug,
                "description": group.description,
                "organization_id": group.organization_id
            }
            for group in groups
        ]
    
    def assign_role_to_user(self, user_id: int, role_id: int, assigned_by: str, 
                           expires_at: Optional[datetime] = None) -> bool:
        """Assign a role to a user"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            role = self.db.query(Role).filter(Role.id == role_id).first()
            
            if not user or not role:
                return False
            
            # Check if assignment already exists
            from models_rbac import user_roles_table
            existing = self.db.execute(
                user_roles_table.select().where(
                    and_(
                        user_roles_table.c.user_id == user_id,
                        user_roles_table.c.role_id == role_id
                    )
                )
            ).first()
            
            if not existing:
                # Create new assignment
                self.db.execute(
                    user_roles_table.insert().values(
                        user_id=user_id,
                        role_id=role_id,
                        assigned_by=assigned_by,
                        expires_at=expires_at
                    )
                )
                
                # Log the action
                audit_log = AuditLog(
                    action="role_assigned",
                    resource_type="user",
                    resource_id=user_id,
                    actor_type="user",
                    actor_id=assigned_by,
                    organization_id=user.organization_id,
                    details={"role_id": role_id, "role_name": role.name}
                )
                self.db.add(audit_log)
                self.db.commit()
                
                logger.info(f"Assigned role {role.name} to user {user.username}")
                return True
            
            return True  # Already assigned
            
        except Exception as e:
            logger.error(f"Failed to assign role: {e}")
            self.db.rollback()
            return False
    
    def remove_role_from_user(self, user_id: int, role_id: int, removed_by: str) -> bool:
        """Remove a role from a user"""
        try:
            from models_rbac import user_roles_table
            
            # Remove the assignment
            result = self.db.execute(
                user_roles_table.delete().where(
                    and_(
                        user_roles_table.c.user_id == user_id,
                        user_roles_table.c.role_id == role_id
                    )
                )
            )
            
            if result.rowcount > 0:
                # Log the action
                user = self.db.query(User).filter(User.id == user_id).first()
                role = self.db.query(Role).filter(Role.id == role_id).first()
                
                audit_log = AuditLog(
                    action="role_removed",
                    resource_type="user",
                    resource_id=user_id,
                    actor_type="user",
                    actor_id=removed_by,
                    organization_id=user.organization_id if user else None,
                    details={"role_id": role_id, "role_name": role.name if role else None}
                )
                self.db.add(audit_log)
                self.db.commit()
                
                logger.info(f"Removed role from user {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to remove role: {e}")
            self.db.rollback()
            return False
    
    def create_permission_override(self, user_id: int, permission_name: str, 
                                 is_granted: bool, granted_by: str,
                                 expires_at: Optional[datetime] = None,
                                 reason: Optional[str] = None,
                                 resource_type: Optional[str] = None,
                                 resource_id: Optional[str] = None) -> bool:
        """Create a user-specific permission override"""
        try:
            permission = self.db.query(Permission).filter(Permission.name == permission_name).first()
            if not permission:
                logger.error(f"Permission {permission_name} not found")
                return False
            
            # Remove existing override if any
            existing = self.db.query(UserPermissionOverride).filter(
                and_(
                    UserPermissionOverride.user_id == user_id,
                    UserPermissionOverride.permission_id == permission.id,
                    UserPermissionOverride.resource_type == resource_type,
                    UserPermissionOverride.resource_id == resource_id
                )
            ).first()
            
            if existing:
                self.db.delete(existing)
            
            # Create new override
            override = UserPermissionOverride(
                user_id=user_id,
                permission_id=permission.id,
                is_granted=is_granted,
                granted_by=granted_by,
                expires_at=expires_at,
                reason=reason,
                resource_type=resource_type,
                resource_id=resource_id
            )
            
            self.db.add(override)
            
            # Log the action
            user = self.db.query(User).filter(User.id == user_id).first()
            audit_log = AuditLog(
                action="permission_override_created",
                resource_type="user",
                resource_id=user_id,
                actor_type="user",
                actor_id=granted_by,
                organization_id=user.organization_id if user else None,
                details={
                    "permission": permission_name,
                    "granted": is_granted,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "reason": reason
                }
            )
            self.db.add(audit_log)
            self.db.commit()
            
            logger.info(f"Created permission override for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create permission override: {e}")
            self.db.rollback()
            return False


def get_rbac_service(db: Session = Depends(get_db)) -> RBACService:
    """Dependency to get RBAC service instance"""
    return RBACService(db)


def require_permission(permission: str, organization_context: bool = False):
    """
    Decorator to require specific permission for API endpoints
    Usage: @require_permission("episodes.create")
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current user and RBAC service from dependencies
            current_user = None
            rbac_service = None
            
            # Look for current_user and rbac_service in function arguments
            for arg in args:
                if hasattr(arg, 'get') and 'username' in str(arg):
                    current_user = arg
                elif isinstance(arg, RBACService):
                    rbac_service = arg
            
            # Look in kwargs
            if 'current_user' in kwargs:
                current_user = kwargs['current_user']
            if 'rbac_service' in kwargs:
                rbac_service = kwargs['rbac_service']
            
            if not current_user or not rbac_service:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Missing authentication or RBAC service"
                )
            
            # Get organization context if needed
            organization_id = None
            if organization_context and hasattr(current_user, 'organization_id'):
                organization_id = current_user.get('organization_id')
            
            # Check permission
            user_id = current_user.get('id') or current_user.get('user_id')
            if not rbac_service.check_permission(user_id, permission, organization_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission}' required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def seed_default_permissions(db: Session) -> None:
    """Seed database with default permissions and roles"""
    
    # Default permissions
    default_permissions = [
        # User management
        ("users.create", "Create Users", "users", "create", "global"),
        ("users.read", "View Users", "users", "read", "organization"),
        ("users.update", "Update Users", "users", "update", "organization"),
        ("users.delete", "Delete Users", "users", "delete", "organization"),
        
        # Organization management
        ("organizations.create", "Create Organizations", "organizations", "create", "global"),
        ("organizations.read", "View Organizations", "organizations", "read", "own"),
        ("organizations.update", "Update Organizations", "organizations", "update", "own"),
        ("organizations.delete", "Delete Organizations", "organizations", "delete", "global"),
        
        # Show management
        ("shows.create", "Create Shows", "shows", "create", "organization"),
        ("shows.read", "View Shows", "shows", "read", "organization"),
        ("shows.update", "Update Shows", "shows", "update", "organization"),
        ("shows.delete", "Delete Shows", "shows", "delete", "organization"),
        
        # Episode management
        ("episodes.create", "Create Episodes", "episodes", "create", "organization"),
        ("episodes.read", "View Episodes", "episodes", "read", "organization"),
        ("episodes.update", "Update Episodes", "episodes", "update", "organization"),
        ("episodes.delete", "Delete Episodes", "episodes", "delete", "organization"),
        ("episodes.publish", "Publish Episodes", "episodes", "publish", "organization"),
        
        # Content management
        ("content.create", "Create Content", "content", "create", "organization"),
        ("content.read", "View Content", "content", "read", "organization"),
        ("content.update", "Update Content", "content", "update", "organization"),
        ("content.delete", "Delete Content", "content", "delete", "organization"),
        
        # RBAC management
        ("rbac.manage", "Manage Roles & Permissions", "rbac", "manage", "organization"),
        ("rbac.assign", "Assign Roles", "rbac", "assign", "organization"),
        ("rbac.audit", "View Audit Logs", "rbac", "audit", "organization"),
        
        # System administration
        ("admin.all", "Full System Access", "admin", "all", "global"),
    ]
    
    # Create permissions
    for perm_data in default_permissions:
        name, display_name, resource, action, scope = perm_data
        
        existing = db.query(Permission).filter(Permission.name == name).first()
        if not existing:
            permission = Permission(
                name=name,
                display_name=display_name,
                resource=resource,
                action=action,
                scope=scope,
                is_system=True,
                created_by="system"
            )
            db.add(permission)
    
    # Default roles
    default_roles = [
        ("Super Admin", "super-admin", "Full system administrator", 0, True, None, [
            "admin.all"
        ]),
        ("Organization Admin", "org-admin", "Organization administrator", 1, True, None, [
            "organizations.read", "organizations.update",
            "shows.*", "episodes.*", "content.*", "users.*", "rbac.*"
        ]),
        ("Content Manager", "content-manager", "Manages shows and episodes", 2, True, None, [
            "shows.read", "shows.update", "shows.create",
            "episodes.*", "content.*"
        ]),
        ("Content Editor", "content-editor", "Edits content and rundowns", 3, True, None, [
            "episodes.read", "episodes.update", "content.*"
        ]),
        ("Viewer", "viewer", "Read-only access", 4, True, None, [
            "shows.read", "episodes.read", "content.read"
        ])
    ]
    
    # Create roles
    for role_data in default_roles:
        name, slug, description, level, is_system, org_id, permission_names = role_data
        
        existing = db.query(Role).filter(Role.slug == slug).first()
        if not existing:
            role = Role(
                name=name,
                slug=slug,
                description=description,
                level=level,
                is_system=is_system,
                organization_id=org_id,
                created_by="system"
            )
            db.add(role)
            db.flush()  # Get the role ID
            
            # Assign permissions to role
            for perm_name in permission_names:
                if perm_name.endswith(".*"):
                    # Wildcard permission - find all matching
                    resource = perm_name[:-2]
                    permissions = db.query(Permission).filter(Permission.resource == resource).all()
                else:
                    permissions = db.query(Permission).filter(Permission.name == perm_name).all()
                
                for permission in permissions:
                    role.permissions.append(permission)
    
    try:
        db.commit()
        logger.info("Successfully seeded default permissions and roles")
    except Exception as e:
        logger.error(f"Failed to seed default data: {e}")
        db.rollback()