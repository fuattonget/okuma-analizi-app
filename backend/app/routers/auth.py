from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.user import UserDoc, create_access_token, get_current_user
from app.models.roles import Role

router = APIRouter()

# Request/Response models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict
    expires_at: float  # Unix timestamp when token expires

class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    role: str
    is_active: bool
    created_at: str
    role_permissions: list[str] = []

@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """
    Login endpoint - authenticate user and return JWT token
    """
    # Authenticate user
    user = await UserDoc.authenticate(login_data.email, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Get user role
    role = await user.get_role()
    role_name = role.name if role else "user"
    
    # Get effective permissions
    role_permissions = await user.get_effective_permissions()
    
    # Create JWT token
    access_token = create_access_token(str(user.id), role_name)
    
    # Calculate expiration timestamp (4 hours from now - must match JWT_EXPIRATION_HOURS)
    from datetime import datetime, timezone, timedelta
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=4)).timestamp()
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_at=expires_at,
        user={
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "role": role_name,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat(),
            "role_permissions": role_permissions
        }
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserDoc = Depends(get_current_user)):
    """
    Get current user information
    """
    # Get user role
    role = await current_user.get_role()
    role_name = role.name if role else "user"
    
    # Get effective permissions
    role_permissions = await current_user.get_effective_permissions()
    
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        role=role_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat(),
        role_permissions=role_permissions
    )

@router.post("/logout")
async def logout():
    """
    Logout endpoint (client-side token removal)
    """
    return {"message": "Successfully logged out"}

# Admin-only endpoints removed - use script instead
