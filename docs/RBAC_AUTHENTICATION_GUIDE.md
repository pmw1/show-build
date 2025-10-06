# RBAC Authentication System - Complete Reference Guide

## Overview

Show-Build implements a comprehensive Role-Based Access Control (RBAC) system providing enterprise-grade security and user management. This document serves as the complete reference for understanding, implementing, and administering the RBAC system.

## Database Structure

The RBAC system consists of 11 interconnected tables organized into four categories:

### Core Entity Tables

#### 1. `users` (Primary authentication table)
```sql
users:
- id (Primary Key)
- username (Unique) -- Primary identifier
- hashed_password -- Bcrypt hashed password  
- access_level -- Legacy field: "user", "admin", "service"
- first_name, last_name, email, phone -- Profile information
- organization_id (FK to organizations) -- User's primary organization
- is_active, is_verified -- Account status flags
- created_at, updated_at, last_login -- Timestamps
- preferences (JSON) -- User-specific settings
```

#### 2. `roles` (Permission containers)
```sql
roles:
- id (Primary Key)
- name -- Display name: "Content Editor", "Admin"
- slug -- URL-safe identifier: "content-editor", "admin"
- description -- Role purpose description
- parent_role_id (FK to roles) -- Optional role hierarchy
- level -- Hierarchy level: 0=top, higher=more specific
- is_system, is_active -- System/status flags
- organization_id (FK to organizations) -- NULL for global roles
- color -- Hex color for UI display
- created_at, updated_at, created_by -- Audit fields
```

#### 3. `groups` (User collections within organizations)
```sql
groups:
- id (Primary Key)
- name -- Display name: "Production Team", "Editorial Staff"  
- slug -- URL-safe identifier: "production-team"
- description -- Group purpose description
- organization_id (FK to organizations) -- Required: groups are org-specific
- is_active -- Status flag
- auto_assign_new_users -- Auto-add new org users to this group
- color -- Hex color for UI display
- settings (JSON) -- Group-specific configuration
- created_at, updated_at, created_by -- Audit fields
```

#### 4. `permissions` (Granular access rights)
```sql
permissions:
- id (Primary Key)
- name -- Dot notation: "episodes.create", "users.delete"
- display_name -- Human readable: "Create Episodes"
- description -- Permission explanation
- resource -- Resource type: "episodes", "users", "shows"
- action -- Action type: "create", "read", "update", "delete"
- scope -- Permission scope: "global", "organization", "own"
- is_system -- TRUE for built-in permissions
- created_at, updated_at, created_by -- Audit fields
```

### Relationship Tables (Many-to-Many)

#### 5. `user_roles` (Users ↔ Roles)
```sql
user_roles:
- user_id (FK to users)
- role_id (FK to roles)  
- assigned_at -- When role was assigned
- assigned_by -- Who assigned the role
- expires_at -- Optional role expiry date
```

#### 6. `user_groups` (Users ↔ Groups)
```sql
user_groups:
- user_id (FK to users)
- group_id (FK to groups)
- joined_at -- When user joined group
- added_by -- Who added user to group
```

#### 7. `group_roles` (Groups ↔ Roles)
```sql
group_roles:
- group_id (FK to groups)
- role_id (FK to roles)
- assigned_at -- When role was assigned to group
- assigned_by -- Who made the assignment
```

#### 8. `role_permissions` (Roles ↔ Permissions)
```sql
role_permissions:
- role_id (FK to roles)
- permission_id (FK to permissions)
- granted_at -- When permission was granted
- granted_by -- Who granted the permission
```

### Override & Audit Tables

#### 9. `user_permission_overrides` (Direct user permissions)
```sql
user_permission_overrides:
- id (Primary Key)
- user_id (FK to users)
- permission_id (FK to permissions)
- is_granted -- TRUE=grant permission, FALSE=deny permission
- resource_type, resource_id -- Context-specific permissions
- granted_at, granted_by -- Assignment audit
- expires_at -- Optional override expiry
- reason -- Justification for override
```

#### 10. `rbac_audit_log` (All RBAC changes)
```sql
rbac_audit_log:
- id (Primary Key)
- action -- Action type: "role_assigned", "permission_granted"
- resource_type, resource_id -- What was changed
- actor_type, actor_id -- Who made the change
- organization_id -- Organization context
- details (JSON) -- Additional change details
- ip_address, user_agent -- Client information
- created_at -- When change occurred
```

#### 11. `api_keys` (Service authentication)
```sql
api_keys:
- id (Primary Key)
- key_hash -- Bcrypt hashed API key
- key_prefix -- First 8 characters for identification
- client_name -- Service/client identifier
- access_level -- Key access level
- created_by_username -- Creator username
- is_active -- Key status
- created_at, last_used, expires_at -- Usage tracking
- usage_count -- Total usage counter
```

## Permission Resolution Logic

When checking if a user has a specific permission, the system follows this hierarchy:

### 1. Direct Role Permissions
```
User → user_roles → roles → role_permissions → permissions
```

### 2. Group Role Permissions  
```
User → user_groups → groups → group_roles → roles → role_permissions → permissions
```

### 3. Permission Overrides
```
User → user_permission_overrides → permissions
```
- Overrides can GRANT or DENY permissions
- Overrides take precedence over role/group permissions
- Can be resource-specific (e.g., only for specific episodes)

### 4. Hierarchical Permissions
- Super Admin with `admin.all` grants everything
- Wildcard permissions: `episodes.*` grants all episode permissions
- Role hierarchy: parent roles inherit child role permissions

## Default System Roles & Permissions

### Built-in Permissions (25 total)

#### User Management
- `users.create` - Create new users (Global scope)
- `users.read` - View user information (Organization scope)
- `users.update` - Modify user profiles (Organization scope)  
- `users.delete` - Remove users (Organization scope)

#### Organization Management
- `organizations.create` - Create organizations (Global scope)
- `organizations.read` - View organization info (Own scope)
- `organizations.update` - Modify organization (Own scope)
- `organizations.delete` - Remove organizations (Global scope)

#### Show Management
- `shows.create` - Create new shows (Organization scope)
- `shows.read` - View shows (Organization scope)
- `shows.update` - Modify shows (Organization scope)
- `shows.delete` - Remove shows (Organization scope)

#### Episode Management
- `episodes.create` - Create episodes (Organization scope)
- `episodes.read` - View episodes (Organization scope)
- `episodes.update` - Modify episodes (Organization scope)
- `episodes.delete` - Remove episodes (Organization scope)
- `episodes.publish` - Publish episodes (Organization scope)

#### Content Management
- `content.create` - Create content (Organization scope)
- `content.read` - View content (Organization scope)
- `content.update` - Modify content (Organization scope)
- `content.delete` - Remove content (Organization scope)

#### RBAC Management
- `rbac.manage` - Manage roles & permissions (Organization scope)
- `rbac.assign` - Assign roles to users (Organization scope)
- `rbac.audit` - View audit logs (Organization scope)

#### System Administration
- `admin.all` - Full system access (Global scope)

### Built-in Roles (5 levels)

#### Level 0: Super Admin
- **Permissions**: `admin.all` (grants everything)
- **Scope**: Global system administration
- **Use**: System administrators only

#### Level 1: Organization Admin  
- **Permissions**: All organization, show, episode, content, user, and RBAC permissions
- **Scope**: Full control within their organization
- **Use**: Organization managers and administrators

#### Level 2: Content Manager
- **Permissions**: Show and episode management, content management
- **Scope**: Manages content production
- **Use**: Production managers, show producers

#### Level 3: Content Editor
- **Permissions**: Episode read/update, content management
- **Scope**: Edits content and rundowns
- **Use**: Content creators, editors, writers

#### Level 4: Viewer
- **Permissions**: Read-only access to shows, episodes, content
- **Scope**: View-only access
- **Use**: Guests, reviewers, stakeholders

## API Endpoints Reference

All RBAC endpoints are prefixed with `/api/rbac/` and require admin authentication.

### System Management
- `GET /system-status` - Get system health and statistics
- `POST /seed-defaults` - Initialize default permissions and roles

### Permissions
- `GET /permissions` - List all permissions (with filtering)
- `GET /permissions/{id}` - Get specific permission details

### Roles
- `GET /roles` - List roles (optionally include permissions)
- `POST /roles` - Create new role
- `PUT /roles/{id}` - Update existing role
- `DELETE /roles/{id}` - Delete role (if not system role)

### Groups  
- `GET /groups` - List groups by organization
- `POST /groups` - Create new group
- `PUT /groups/{id}` - Update group
- `DELETE /groups/{id}` - Delete group

### User Assignment
- `POST /users/assign-role` - Assign role to user
- `DELETE /users/{user_id}/roles/{role_id}` - Remove role from user
- `POST /users/permission-override` - Create permission override

### User Information
- `GET /users/{id}/permissions` - Get all effective user permissions
- `GET /users/{id}/roles` - Get user's assigned roles
- `GET /users/{id}/groups` - Get user's group memberships

### Permission Checking
- `GET /check-permission` - Check if user has specific permission

### Audit Trail
- `GET /audit` - Get audit log with filtering and pagination

## Admin Interface Implementation Guide

### Recommended Interface Structure

#### 1. User Management Interface

**Users List View** (`/admin/users`)
```vue
<template>
  <div>
    <!-- User search and filters -->
    <v-text-field v-model="search" label="Search users..." />
    <v-select v-model="organizationFilter" :items="organizations" />
    
    <!-- Users data table -->
    <v-data-table 
      :headers="userHeaders" 
      :items="users"
      :search="search"
    >
      <template #item.actions="{ item }">
        <v-btn @click="editUser(item)" icon="mdi-pencil" />
        <v-btn @click="manageRoles(item)" icon="mdi-shield-account" />
        <v-btn @click="viewAudit(item)" icon="mdi-history" />
      </template>
    </v-data-table>
  </div>
</template>
```

**User Edit Modal**
- Basic profile editing (name, email, organization)
- Role assignment interface with drag-and-drop
- Group membership management
- Permission override interface
- Account status controls (active/inactive)

#### 2. Role Management Interface

**Roles List View** (`/admin/roles`)
```vue
<template>
  <div>
    <!-- Role hierarchy visualization -->
    <v-treeview :items="roleHierarchy" />
    
    <!-- Role management actions -->
    <v-btn @click="createRole" color="primary">Create Role</v-btn>
    
    <!-- Roles table -->
    <v-data-table :headers="roleHeaders" :items="roles">
      <template #item.permissions="{ item }">
        <v-chip-group>
          <v-chip v-for="perm in item.permissions.slice(0,3)" :key="perm.id">
            {{ perm.name }}
          </v-chip>
          <v-chip v-if="item.permissions.length > 3">
            +{{ item.permissions.length - 3 }} more
          </v-chip>
        </v-chip-group>
      </template>
    </v-data-table>
  </div>
</template>
```

**Role Edit Interface**
- Basic role information (name, description, level)
- Permission assignment with categorized checkboxes
- Role hierarchy management
- User assignment preview
- Organization scope selector

#### 3. Group Management Interface

**Groups List View** (`/admin/groups`)
```vue
<template>
  <div>
    <!-- Organization filter -->
    <v-select v-model="selectedOrg" :items="organizations" />
    
    <!-- Groups cards layout -->
    <v-row>
      <v-col v-for="group in filteredGroups" :key="group.id" cols="12" md="4">
        <v-card>
          <v-card-title :style="`color: ${group.color}`">
            {{ group.name }}
            <v-spacer />
            <v-chip>{{ group.user_count }} users</v-chip>
          </v-card-title>
          <v-card-text>{{ group.description }}</v-card-text>
          <v-card-actions>
            <v-btn @click="editGroup(group)">Edit</v-btn>
            <v-btn @click="manageMembers(group)">Members</v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>
```

#### 4. Permission Management Interface

**Permissions Matrix View** (`/admin/permissions`)
```vue
<template>
  <div>
    <!-- Resource-based permission matrix -->
    <v-data-table 
      :headers="permissionHeaders" 
      :items="permissionsByResource"
      :group-by="['resource']"
    >
      <template #group.header="{ item, isOpen, toggle }">
        <td :colspan="headers.length">
          <v-btn @click="toggle" :icon="isOpen ? 'mdi-minus' : 'mdi-plus'" />
          {{ item.resource }} ({{ item.items.length }} permissions)
        </td>
      </template>
    </v-data-table>
  </div>
</template>
```

### Implementation Components

#### 1. Role Assignment Component
```vue
<!-- RoleAssignmentDialog.vue -->
<template>
  <v-dialog v-model="dialog" max-width="800px">
    <v-card>
      <v-card-title>Manage Roles for {{ user.username }}</v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="6">
            <h4>Available Roles</h4>
            <v-list>
              <v-list-item 
                v-for="role in availableRoles" 
                :key="role.id"
                @click="assignRole(role)"
              >
                <v-list-item-title>{{ role.name }}</v-list-item-title>
                <v-list-item-subtitle>{{ role.description }}</v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-col>
          <v-col cols="6">
            <h4>Assigned Roles</h4>
            <v-list>
              <v-list-item v-for="role in userRoles" :key="role.id">
                <v-list-item-title>{{ role.name }}</v-list-item-title>
                <v-list-item-action>
                  <v-btn @click="removeRole(role)" icon="mdi-close" />
                </v-list-item-action>
              </v-list-item>
            </v-list>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>
```

#### 2. Permission Override Component
```vue
<!-- PermissionOverrideDialog.vue -->
<template>
  <v-dialog v-model="dialog" max-width="600px">
    <v-card>
      <v-card-title>Permission Override</v-card-title>
      <v-card-text>
        <v-select
          v-model="selectedPermission"
          :items="permissions"
          item-title="display_name"
          item-value="name"
          label="Permission"
        />
        <v-switch
          v-model="isGranted"
          :label="isGranted ? 'Grant Permission' : 'Deny Permission'"
          color="success"
        />
        <v-text-field
          v-model="reason"
          label="Reason for override"
          hint="Explain why this override is necessary"
        />
        <v-menu v-model="dateMenu">
          <template #activator="{ props }">
            <v-text-field
              v-bind="props"
              v-model="expiryDate"
              label="Expiry Date (optional)"
              readonly
            />
          </template>
          <v-date-picker v-model="expiryDate" @input="dateMenu = false" />
        </v-menu>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>
```

### Best Practices for Admin Interface

#### 1. User Experience Guidelines
- **Progressive Disclosure**: Show basic info first, detailed permissions on demand
- **Visual Hierarchy**: Use colors, icons, and spacing to show permission levels
- **Bulk Operations**: Allow bulk role assignments and permission changes
- **Search & Filter**: Always provide filtering for large user/role lists
- **Confirmation Dialogs**: Require confirmation for destructive actions

#### 2. Security Considerations
- **Audit Everything**: Log all admin actions with full context
- **Principle of Least Privilege**: Default to minimal permissions
- **Session Management**: Implement admin session timeouts
- **Input Validation**: Validate all role/permission assignments
- **Error Handling**: Gracefully handle permission errors

#### 3. Performance Optimizations
- **Lazy Loading**: Load user details and permissions on-demand
- **Pagination**: Implement proper pagination for large datasets
- **Caching**: Cache role/permission definitions
- **Debounced Search**: Debounce search inputs to reduce API calls

#### 4. API Integration Patterns
```javascript
// User role management composable
export function useUserRoles() {
  const assignRole = async (userId, roleId, expiresAt = null) => {
    const response = await fetch('/api/rbac/users/assign-role', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': getApiKey()
      },
      body: JSON.stringify({ user_id: userId, role_id: roleId, expires_at: expiresAt })
    })
    
    if (!response.ok) throw new Error('Failed to assign role')
    return response.json()
  }

  const getUserPermissions = async (userId, organizationId = null) => {
    const url = new URL('/api/rbac/users/' + userId + '/permissions', window.location.origin)
    if (organizationId) url.searchParams.set('organization_id', organizationId)
    
    const response = await fetch(url, {
      headers: { 'X-API-Key': getApiKey() }
    })
    
    if (!response.ok) throw new Error('Failed to get permissions')
    return response.json()
  }

  return { assignRole, getUserPermissions }
}
```

## Troubleshooting Common Issues

### 1. Permission Not Working
- Check user's effective permissions: `GET /api/rbac/users/{id}/permissions`
- Verify role assignments: `GET /api/rbac/users/{id}/roles`
- Check for permission overrides that might be denying access
- Ensure organization context is correct for organization-scoped permissions

### 2. Role Assignment Failures
- Verify role is active and not deleted
- Check organization compatibility (role organization matches user organization)
- Ensure requesting user has `rbac.assign` permission
- Check audit logs for detailed error information

### 3. Performance Issues
- Use pagination for large user lists
- Filter permissions by resource/organization
- Cache role definitions in frontend
- Use database indexes on foreign keys

### 4. Migration Issues
- Always backup database before running migrations
- Test migrations on development environment first
- Check for foreign key constraint violations
- Verify all relationship tables are properly created

## Security Considerations

### 1. Password Security
- All passwords are bcrypt hashed with salt rounds >= 12
- API keys are hashed and only prefixes are stored for identification
- Session tokens have configurable expiry times

### 2. Permission Escalation Prevention
- Users cannot assign roles higher than their own level
- System roles cannot be modified or deleted
- Permission overrides require justification and can expire

### 3. Audit Trail
- All RBAC changes are logged with full context
- IP addresses and user agents are captured
- Audit logs are immutable and retention can be configured

### 4. Organization Isolation
- Groups are strictly organization-scoped
- Organization-scoped permissions respect boundaries
- Users can only manage users within their organization

## Migration from Legacy System

The RBAC system maintains backward compatibility with the legacy `access_level` field:
- `access_level: "admin"` users automatically get Super Admin role
- `access_level: "user"` users get default Viewer role  
- `access_level: "service"` is used for API key authentication

## Conclusion

This RBAC system provides enterprise-grade security with flexibility for complex organizational structures. The hierarchical permission model, combined with groups and overrides, allows for precise access control while maintaining ease of administration.

For additional support or questions about implementation, refer to the API documentation or contact the development team.