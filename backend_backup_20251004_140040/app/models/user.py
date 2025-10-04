from beanie import Document
from pydantic import Field, EmailStr
from typing import Optional, List
from datetime import datetime, timezone
from passlib.context import CryptContext
from functools import wraps
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from app.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    # Truncate password to 72 bytes max for bcrypt
    password = password[:72]
    return pwd_context.hash(password)

# JWT settings
JWT_SECRET = "your-secret-key-change-in-production"  # TODO: Move to environment
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 1

# HTTP Bearer for JWT
security = HTTPBearer()

class UserDoc(Document):
    """User document model"""
    email: EmailStr = Field(..., unique=True, index=True)
    password_hash: str
    username: str = Field(..., max_length=50)  # Kullanıcı adı
    role: str = Field(default="admin")  # admin, teacher, parent (future)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "users"
        indexes = [
            "email",
            "role",
            "is_active"
        ]
    
    def set_password(self, password: str):
        """Hash and set password"""
        import hashlib
        # Use SHA256 for simplicity
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str) -> bool:
        """Verify password"""
        import hashlib
        # Use SHA256 for simplicity
        return hashlib.sha256(password.encode()).hexdigest() == self.password_hash
    
    @classmethod
    async def authenticate(cls, email: str, password: str) -> Optional["UserDoc"]:
        """Authenticate user with email and password"""
        user = await cls.find_one(cls.email == email, cls.is_active == True)
        if user:
            try:
                if user.verify_password(password):
                    return user
            except Exception as e:
                print(f"Password verification error: {e}")
                return None
        return None

def create_access_token(user_id: str, role: str) -> str:
    """Create JWT access token"""
    payload = {
        "sub": user_id,
        "role": role,
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

def require_role(*roles: str):
    """Decorator to require specific roles"""
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
            
            if current_user.role not in roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {roles}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Dependency for admin role
async def get_admin_user(current_user: UserDoc = Depends(get_current_user)) -> UserDoc:
    """Get current user and verify admin role"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
