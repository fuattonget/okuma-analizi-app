from enum import Enum
from typing import List, Set, TYPE_CHECKING
from functools import wraps
from fastapi import HTTPException, Depends, status

if TYPE_CHECKING:
    from app.models.user import UserDoc

class Role(str, Enum):
    """User roles in the system"""
    ADMIN = "admin"
    MANAGER = "manager" 
    TEACHER = "teacher"

class Permission(str, Enum):
    """System permissions"""
    # User Management
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    
    # Student Management
    STUDENT_CREATE = "student:create"
    STUDENT_READ = "student:read"
    STUDENT_UPDATE = "student:update"
    STUDENT_DELETE = "student:delete"
    
    # Text Management
    TEXT_CREATE = "text:create"
    TEXT_READ = "text:read"
    TEXT_UPDATE = "text:update"
    TEXT_DELETE = "text:delete"
    
    # Analysis Management
    ANALYSIS_CREATE = "analysis:create"
    ANALYSIS_READ = "analysis:read"
    ANALYSIS_READ_ALL = "analysis:read_all"
    ANALYSIS_VIEW = "analysis:view"
    ANALYSIS_UPDATE = "analysis:update"
    ANALYSIS_DELETE = "analysis:delete"
    
    # System Management
    SYSTEM_SETTINGS = "system:settings"
    SYSTEM_LOGS = "system:logs"
    SYSTEM_STATUS = "system:status"

# Role-Permission mapping
ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    Role.ADMIN: {
        # Full access to everything
        Permission.USER_CREATE,
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
        Permission.STUDENT_CREATE,
        Permission.STUDENT_READ,
        Permission.STUDENT_UPDATE,
        Permission.STUDENT_DELETE,
        Permission.TEXT_CREATE,
        Permission.TEXT_READ,
        Permission.TEXT_UPDATE,
        Permission.TEXT_DELETE,
        Permission.ANALYSIS_CREATE,
        Permission.ANALYSIS_READ,
        Permission.ANALYSIS_UPDATE,
        Permission.ANALYSIS_DELETE,
        Permission.SYSTEM_SETTINGS,
        Permission.SYSTEM_LOGS,
        Permission.SYSTEM_STATUS,
    },
    
    Role.MANAGER: {
        # Can manage students, texts, and analyses
        Permission.STUDENT_CREATE,
        Permission.STUDENT_READ,
        Permission.STUDENT_UPDATE,
        Permission.STUDENT_DELETE,
        Permission.TEXT_CREATE,
        Permission.TEXT_READ,
        Permission.TEXT_UPDATE,
        Permission.TEXT_DELETE,
        Permission.ANALYSIS_CREATE,
        Permission.ANALYSIS_READ,
        Permission.ANALYSIS_UPDATE,
        Permission.ANALYSIS_DELETE,
    },
    
    Role.TEACHER: {
        # Can only read students and create/read analyses
        Permission.STUDENT_READ,
        Permission.TEXT_READ,
        Permission.ANALYSIS_CREATE,
        Permission.ANALYSIS_READ,
    }
}

def has_permission(user: "UserDoc", permission: Permission) -> bool:
    """Check if user has specific permission"""
    try:
        user_role = Role(user.role)
        return permission in ROLE_PERMISSIONS.get(user_role, set())
    except ValueError:
        # Invalid role
        return False

def has_any_permission(user: "UserDoc", permissions: List[Permission]) -> bool:
    """Check if user has any of the specified permissions"""
    return any(has_permission(user, perm) for perm in permissions)

def has_all_permissions(user: "UserDoc", permissions: List[Permission]) -> bool:
    """Check if user has all of the specified permissions"""
    return all(has_permission(user, perm) for perm in permissions)

def require_permission(permission: Permission):
    """Decorator to require specific permission"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from kwargs or dependencies
            current_user = None
            for arg in args:
                if isinstance(arg, UserDoc):
                    current_user = arg
                    break
            
            if not current_user:
                # Try to get from kwargs
                current_user = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not has_permission(current_user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required permission: {permission.value}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_any_permission(permissions: List[Permission]):
    """Decorator to require any of the specified permissions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = None
            for arg in args:
                if isinstance(arg, UserDoc):
                    current_user = arg
                    break
            
            if not current_user:
                current_user = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not has_any_permission(current_user, permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required permissions: {[p.value for p in permissions]}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Import get_current_user locally to avoid circular import
def get_current_user():
    from app.models.user import get_current_user as _get_current_user
    return _get_current_user

# Convenience functions for common role checks
def require_admin(current_user: "UserDoc" = Depends(get_current_user)) -> "UserDoc":
    """Require admin role"""
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

def require_manager_or_admin(current_user: "UserDoc" = Depends(get_current_user)) -> "UserDoc":
    """Require manager or admin role"""
    if current_user.role not in [Role.ADMIN, Role.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager or admin access required"
        )
    return current_user

def require_teacher_or_above(current_user: "UserDoc" = Depends(get_current_user)) -> "UserDoc":
    """Require teacher role or above"""
    if current_user.role not in [Role.ADMIN, Role.MANAGER, Role.TEACHER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher access or above required"
        )
    return current_user

# Permission-based dependencies
def require_user_management(current_user: "UserDoc" = Depends(get_current_user)) -> "UserDoc":
    """Require user management permissions"""
    if not has_any_permission(current_user, [Permission.USER_CREATE, Permission.USER_UPDATE, Permission.USER_DELETE]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User management access required"
        )
    return current_user

def require_student_management(current_user: "UserDoc" = Depends(get_current_user)) -> "UserDoc":
    """Require student management permissions"""
    if not has_any_permission(current_user, [Permission.STUDENT_CREATE, Permission.STUDENT_UPDATE, Permission.STUDENT_DELETE]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student management access required"
        )
    return current_user

def require_text_management(current_user: "UserDoc" = Depends(get_current_user)) -> "UserDoc":
    """Require text management permissions"""
    if not has_any_permission(current_user, [Permission.TEXT_CREATE, Permission.TEXT_UPDATE, Permission.TEXT_DELETE]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Text management access required"
        )
    return current_user

def require_analysis_management(current_user: "UserDoc" = Depends(get_current_user)) -> "UserDoc":
    """Require analysis management permissions"""
    if not has_any_permission(current_user, [Permission.ANALYSIS_CREATE, Permission.ANALYSIS_UPDATE, Permission.ANALYSIS_DELETE]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analysis management access required"
        )
    return current_user

def require_system_access(current_user: "UserDoc" = Depends(get_current_user)) -> "UserDoc":
    """Require system access permissions"""
    if not has_any_permission(current_user, [Permission.SYSTEM_SETTINGS, Permission.SYSTEM_LOGS, Permission.SYSTEM_STATUS]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System access required"
        )
    return current_user
