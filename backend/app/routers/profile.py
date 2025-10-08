from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.user import UserDoc, get_current_user, get_password_hash, verify_password
from datetime import datetime, timezone

router = APIRouter()

# Request/Response Models
class ProfileResponse(BaseModel):
    id: str
    email: EmailStr
    username: str
    role_name: str
    role_display_name: str
    created_at: str
    updated_at: str

class UpdateProfileRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(current_user: UserDoc = Depends(get_current_user)):
    """Get current user's profile"""
    # Get role information
    role = await current_user.get_role()
    
    return ProfileResponse(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        role_name=role.name if role else "unknown",
        role_display_name=role.display_name if role else "Bilinmeyen",
        created_at=current_user.created_at.isoformat(),
        updated_at=current_user.updated_at.isoformat()
    )

@router.put("/me", response_model=ProfileResponse)
async def update_my_profile(
    profile_data: UpdateProfileRequest,
    current_user: UserDoc = Depends(get_current_user)
):
    """Update current user's profile"""
    
    # Update username if provided
    if profile_data.username is not None:
        if not profile_data.username.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username cannot be empty"
            )
        current_user.username = profile_data.username.strip()
    
    # Update email if provided
    if profile_data.email is not None:
        # Check if email is already taken by another user
        existing_user = await UserDoc.find_one(
            UserDoc.email == profile_data.email,
            UserDoc.id != current_user.id
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use by another user"
            )
        current_user.email = profile_data.email
    
    # Update timestamp
    current_user.updated_at = datetime.now(timezone.utc)
    
    # Save changes
    await current_user.save()
    
    # Get updated role information
    role = await current_user.get_role()
    
    # Update localStorage user data
    return ProfileResponse(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        role_name=role.name if role else "unknown",
        role_display_name=role.display_name if role else "Bilinmeyen",
        created_at=current_user.created_at.isoformat(),
        updated_at=current_user.updated_at.isoformat()
    )

@router.post("/me/change-password")
async def change_my_password(
    password_data: ChangePasswordRequest,
    current_user: UserDoc = Depends(get_current_user)
):
    """Change current user's password"""
    
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mevcut şifre yanlış"
        )
    
    # Validate new password
    if len(password_data.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Yeni şifre en az 6 karakter olmalıdır"
        )
    
    if password_data.new_password == password_data.current_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Yeni şifre mevcut şifreyle aynı olamaz"
        )
    
    # Hash and save new password
    current_user.password_hash = get_password_hash(password_data.new_password)
    current_user.updated_at = datetime.now(timezone.utc)
    await current_user.save()
    
    return {
        "message": "Şifre başarıyla değiştirildi",
        "success": True
    }

