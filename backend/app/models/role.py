from beanie import Document, Link
from pydantic import Field
from typing import List
from datetime import datetime, timezone

class RoleDoc(Document):
    """Role document model for RBAC"""
    name: str = Field(..., unique=True, index=True)  # "admin", "manager", "teacher"
    display_name: str = Field(...)  # "Yönetici", "Müdür", "Öğretmen"
    description: str = Field(default="")
    permissions: List[str] = Field(default_factory=list)  # List of permission strings
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "roles"
        indexes = [
            "name",
            "is_active"
        ]
    
    def has_permission(self, permission: str) -> bool:
        """Check if role has specific permission"""
        return permission in self.permissions or "*" in self.permissions
    
    def add_permission(self, permission: str):
        """Add permission to role"""
        if permission not in self.permissions:
            self.permissions.append(permission)
            self.updated_at = datetime.now(timezone.utc)
    
    def remove_permission(self, permission: str):
        """Remove permission from role"""
        if permission in self.permissions:
            self.permissions.remove(permission)
            self.updated_at = datetime.now(timezone.utc)
    
    def set_permissions(self, permissions: List[str]):
        """Set all permissions for role"""
        self.permissions = permissions
        self.updated_at = datetime.now(timezone.utc)


