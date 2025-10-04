from beanie import Document
from pydantic import Field, EmailStr
from typing import Optional, List
from datetime import datetime, timezone
from passlib.context import CryptContext
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from app.models.role import RoleDoc
from bson import ObjectId

# Password hashing - Using pbkdf2_sha256 for reliability
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password using pbkdf2_sha256"""
    if not isinstance(password, str):
        password = str(password)
    return pwd_context.hash(password)

# JWT settings
JWT_SECRET = "your-secret-key-change-in-production"  # TODO: Move to environment
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 1

# HTTP Bearer for JWT
security = HTTPBearer()

class UserDoc(Document):
    """User document model with RBAC support"""
    email: EmailStr = Field(..., unique=True, index=True)
    password_hash: str
    username: str = Field(..., max_length=50)  # Kullanıcı adı
    role_id: ObjectId  # ObjectId
    extra_permissions: List[str] = Field(default_factory=list)  # Additional permissions beyond role
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "users"
        indexes = [
            "email",
            "role_id",
            "is_active"
        ]
    
    model_config = {"arbitrary_types_allowed": True}
    
    def set_password(self, password: str):
        """Hash and set password"""
        self.password_hash = get_password_hash(password)
    
    def verify_password(self, password: str) -> bool:
        """Verify password using the global verify_password function"""
        return verify_password(password, self.password_hash)
    
    async def get_role(self) -> Optional[RoleDoc]:
        """Get user's role"""
        if self.role_id:
            from app.models.role import RoleDoc
            return await RoleDoc.get(str(self.role_id))
        return None
    
    async def get_effective_permissions(self) -> List[str]:
        """Get all effective permissions (role + extra)"""
        role = await self.get_role()
        if not role:
            return self.extra_permissions
        
        # Combine role permissions and extra permissions
        effective_permissions = set(role.permissions + self.extra_permissions)
        return list(effective_permissions)
    
    async def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        effective_permissions = await self.get_effective_permissions()
        return permission in effective_permissions or "*" in effective_permissions
    
    async def has_any_permission(self, permissions: List[str]) -> bool:
        """Check if user has any of the specified permissions"""
        effective_permissions = await self.get_effective_permissions()
        return any(perm in effective_permissions or "*" in effective_permissions for perm in permissions)
    
    async def has_all_permissions(self, permissions: List[str]) -> bool:
        """Check if user has all of the specified permissions"""
        effective_permissions = await self.get_effective_permissions()
        return all(perm in effective_permissions or "*" in effective_permissions for perm in permissions)
    
    @classmethod
    async def authenticate(cls, email: str, password: str) -> Optional["UserDoc"]:
        """Authenticate user with email and password"""
        user = await cls.find_one(cls.email == email, cls.is_active == True)
        if user and user.verify_password(password):
            return user
        return None

def create_access_token(user_id: str, role_name: str) -> str:
    """Create JWT access token"""
    payload = {
        "sub": user_id,
        "role": role_name,
        "exp": datetime.now(timezone.utc).timestamp() + (JWT_EXPIRATION_HOURS * 3600)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> dict:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserDoc:
    """Get current user from JWT token"""
    token = credentials.credentials
    payload = verify_token(token)
    user_id = payload.get("sub")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    user = await UserDoc.get(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user

# Dependency for admin role
async def get_admin_user(current_user: UserDoc = Depends(get_current_user)) -> UserDoc:
    """Get current user and verify admin role"""
    if not await current_user.has_permission("*"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
