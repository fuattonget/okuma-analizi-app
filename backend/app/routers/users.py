from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timezone
from app.models.user import UserDoc, get_current_user, create_access_token, get_password_hash
from app.models.rbac import require_permission
import secrets
import string

router = APIRouter()

# Request/Response models
class UserCreateRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    role: str
    is_active: bool = True

class UserUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    role: str
    is_active: bool
    created_at: str

class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    page_size: int

@router.get("/", response_model=UserListResponse)
@require_permission("user:read")
async def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    current_user: UserDoc = Depends(get_current_user)
):
    """
    Get list of users with pagination and filtering
    """
    # Build query
    query = {}
    
    if search:
        query["$or"] = [
            {"email": {"$regex": search, "$options": "i"}},
            {"username": {"$regex": search, "$options": "i"}}
        ]
    
    if role:
        # For the new RBAC system, we need to check the role_id
        from app.models.role import RoleDoc
        role_doc = await RoleDoc.find_one({"name": role})
        if role_doc:
            query["role_id"] = role_doc.id
    
    # Get total count
    total = await UserDoc.find(query).count()
    
    # Get users with pagination
    skip = (page - 1) * page_size
    users = await UserDoc.find(query).skip(skip).limit(page_size).to_list()
    
    # Convert to response format
    user_responses = []
    for user in users:
        # Fetch the role information
        role = await user.get_role()
        role_name = role.name if role else "unknown"
        
        user_responses.append(UserResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            role=role_name,
            is_active=user.is_active,
            created_at=user.created_at.isoformat()
        ))
    
    return UserListResponse(
        users=user_responses,
        total=total,
        page=page,
        page_size=page_size
    )

@router.get("/{user_id}", response_model=UserResponse)
@require_permission("user:read")
async def get_user(
    user_id: str,
    current_user: UserDoc = Depends(get_current_user)
):
    """
    Get user by ID
    """
    user = await UserDoc.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Fetch the role information
    role = await user.get_role()
    role_name = role.name if role else "unknown"
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        role=role_name,
        is_active=user.is_active,
        created_at=user.created_at.isoformat()
    )

@router.post("/", response_model=UserResponse)
@require_permission("user:create")
async def create_user(
    user_data: UserCreateRequest,
    current_user: UserDoc = Depends(get_current_user)
):
    """
    Create a new user
    """
    # Check if user already exists
    existing_user = await UserDoc.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Find the role
    from app.models.role import RoleDoc
    role_doc = await RoleDoc.find_one({"name": user_data.role})
    if not role_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role"
        )
    
    # Create user
    user = UserDoc(
        email=user_data.email,
        username=user_data.username,
        password_hash="",  # Will be set by set_password
        role_id=role_doc.id,
        is_active=user_data.is_active,
        created_at=datetime.now(timezone.utc)
    )
    
    # Set password using the existing method
    user.set_password(user_data.password)
    
    await user.insert()
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        role=user_data.role,
        is_active=user.is_active,
        created_at=user.created_at.isoformat()
    )

@router.put("/{user_id}", response_model=UserResponse)
@require_permission("user:update")
async def update_user(
    user_id: str,
    user_data: UserUpdateRequest,
    current_user: UserDoc = Depends(get_current_user)
):
    """
    Update user
    """
    try:
        print(f"🔍 Update user request: user_id={user_id}, user_data={user_data}")
        user = await UserDoc.get(user_id)
        if not user:
            print(f"❌ User not found: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        print(f"✅ User found: {user.email}")
        
        # Update fields
        if user_data.email is not None:
            print(f"🔍 Updating email: {user_data.email}")
            # Only check if email is different from current email
            if user_data.email != user.email:
                # Check if email is already taken by another user
                existing_user = await UserDoc.find_one({"email": user_data.email})
                if existing_user and str(existing_user.id) != user_id:
                    print(f"❌ Email already taken by: {existing_user.email}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already taken by another user"
                    )
            print(f"✅ Email is available")
            user.email = user_data.email
        
        if user_data.username is not None:
            user.username = user_data.username
        
        if user_data.password is not None and user_data.password.strip():
            user.set_password(user_data.password)
        
        if user_data.role is not None:
            # Find the new role
            from app.models.role import RoleDoc
            print(f"🔍 Looking for role: {user_data.role}")
            role_doc = await RoleDoc.find_one({"name": user_data.role})
            if not role_doc:
                print(f"❌ Role not found: {user_data.role}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid role"
                )
            print(f"✅ Role found: {role_doc.name}")
            user.role_id = role_doc.id
        
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
        
        user.updated_at = datetime.now(timezone.utc)
        print(f"🔍 Saving user: {user.email}")
        await user.save()
        
        # Fetch the role information for response
        role = await user.get_role()
        role_name = role.name if role else "unknown"
    
        print(f"✅ User updated successfully: {user.email}, role: {role_name}")
        
        return UserResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            role=role_name,
            is_active=user.is_active,
            created_at=user.created_at.isoformat()
        )
    except HTTPException:
        # Re-raise HTTP exceptions as they are already properly formatted
        raise
    except Exception as e:
        print(f"❌ Error updating user: {str(e)}")
        print(f"❌ Error type: {type(e)}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.delete("/{user_id}")
@require_permission("user:delete")
async def delete_user(
    user_id: str,
    current_user: UserDoc = Depends(get_current_user)
):
    """
    Delete user
    """
    user = await UserDoc.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent deleting the current user
    if str(user.id) == str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    await user.delete()
    return {"message": "User deleted successfully"}

def generate_random_password(length: int = 7) -> str:
    """Generate a random password with letters and numbers"""
    # Use a mix of uppercase, lowercase, and digits
    alphabet = string.ascii_uppercase + string.ascii_lowercase + string.digits
    # Ensure at least one uppercase, one lowercase, and one digit
    password = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
    ]
    # Fill the rest randomly
    password += [secrets.choice(alphabet) for _ in range(length - 3)]
    # Shuffle to avoid predictable pattern
    secrets.SystemRandom().shuffle(password)
    return ''.join(password)

@router.post("/{user_id}/reset-password")
@require_permission("user:update")
async def reset_user_password(
    user_id: str,
    current_user: UserDoc = Depends(get_current_user)
):
    """
    Reset user password to a random 7-character password
    Returns the new password in the response (display only once to admin)
    """
    user = await UserDoc.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Generate random 7-character password
    new_password = generate_random_password(7)
    
    # Hash and save
    user.password_hash = get_password_hash(new_password)
    user.updated_at = datetime.now(timezone.utc)
    await user.save()
    
    return {
        "message": "Şifre başarıyla sıfırlandı",
        "new_password": new_password,
        "user_email": user.email,
        "user_username": user.username
    }

@router.get("/roles/available")
@require_permission("user:read")
async def get_available_roles(
    current_user: UserDoc = Depends(get_current_user)
):
    """
    Get list of available roles
    """
    from app.models.role import RoleDoc
    roles = await RoleDoc.find_all().to_list()
    
    return [
        {
            "name": role.name,
            "description": role.description
        }
        for role in roles
    ]