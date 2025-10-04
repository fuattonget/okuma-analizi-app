"""
RBAC (Role-Based Access Control) utilities and constants
"""

from typing import List
from functools import wraps
from fastapi import HTTPException, Depends, status
from app.models.user import UserDoc, get_current_user

# All available permissions in the system
ALL_PERMISSIONS = [
    "student:create",
    "student:read",  # Alias for student:view
    "student:view", 
    "student:update",
    "student:delete",
    "text:create",
    "text:read",     # Alias for text:view
    "text:view",
    "text:update", 
    "text:delete",
    "analysis:create",
    "analysis:read", # Alias for analysis:view
    "analysis:view",
    "analysis:update",
    "analysis:delete",
    "user:create",
    "user:read",     # Alias for user:view
    "user:view",
    "user:update",
    "user:delete",
    "role:create",
    "role:read",     # Alias for role:view
    "role:view", 
    "role:update",
    "role:delete",
    "system:settings",
    "system:logs",
    "system:status"
]

# Default role permissions
DEFAULT_ROLE_PERMISSIONS = {
    "admin": ["*"],  # Admin has all permissions
    "manager": [
        "student:create", "student:view", "student:update", "student:delete",
        "text:create", "text:view", "text:update", "text:delete", 
        "analysis:create", "analysis:view", "analysis:update", "analysis:delete",
        "user:view"  # Can view users but not manage them
    ],
    "teacher": [
        "student:view",
        "text:view", 
        "analysis:create", "analysis:view"
    ]
}

def get_permission_display_name(permission: str) -> str:
    """Get human-readable display name for permission"""
    permission_names = {
        "student:create": "Öğrenci Ekleme",
        "student:view": "Öğrenci Görüntüleme", 
        "student:update": "Öğrenci Güncelleme",
        "student:delete": "Öğrenci Silme",
        "text:create": "Metin Ekleme",
        "text:view": "Metin Görüntüleme",
        "text:update": "Metin Güncelleme", 
        "text:delete": "Metin Silme",
        "analysis:create": "Analiz Oluşturma",
        "analysis:view": "Analiz Görüntüleme",
        "analysis:update": "Analiz Güncelleme",
        "analysis:delete": "Analiz Silme",
        "user:create": "Kullanıcı Ekleme",
        "user:view": "Kullanıcı Görüntüleme",
        "user:update": "Kullanıcı Güncelleme",
        "user:delete": "Kullanıcı Silme",
        "role:create": "Rol Ekleme",
        "role:view": "Rol Görüntüleme", 
        "role:update": "Rol Güncelleme",
        "role:delete": "Rol Silme",
        "system:settings": "Sistem Ayarları",
        "system:logs": "Sistem Logları",
        "system:status": "Sistem Durumu"
    }
    return permission_names.get(permission, permission)

def get_permission_category(permission: str) -> str:
    """Get category for permission grouping"""
    if permission.startswith("student:"):
        return "Öğrenci Yönetimi"
    elif permission.startswith("text:"):
        return "Metin Yönetimi"
    elif permission.startswith("analysis:"):
        return "Analiz Yönetimi"
    elif permission.startswith("user:"):
        return "Kullanıcı Yönetimi"
    elif permission.startswith("role:"):
        return "Rol Yönetimi"
    elif permission.startswith("system:"):
        return "Sistem Yönetimi"
    else:
        return "Diğer"

def group_permissions_by_category(permissions: list) -> dict:
    """Group permissions by category"""
    grouped = {}
    for permission in permissions:
        category = get_permission_category(permission)
        if category not in grouped:
            grouped[category] = []
        grouped[category].append(permission)
    return grouped

def require_permission(*permissions: str):
    """
    Decorator to require specific permissions for an endpoint.
    If multiple permissions are provided, the user must have at least one of them.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current_user from kwargs (FastAPI dependency injection)
            current_user = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Debug: Print user info and permissions
            print(f"🔍 require_permission: User {current_user.email} (role_id: {current_user.role_id})")
            print(f"🔍 require_permission: Required permissions: {list(permissions)}")
            
            # Get user's effective permissions
            effective_permissions = await current_user.get_effective_permissions()
            print(f"🔍 require_permission: User effective permissions: {effective_permissions}")
            
            # Check if user has any of the required permissions
            has_any = await current_user.has_any_permission(list(permissions))
            print(f"🔍 require_permission: Has any permission: {has_any}")
            
            if not has_any:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required permissions: {list(permissions)}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
