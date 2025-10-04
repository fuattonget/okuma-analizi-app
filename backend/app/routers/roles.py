from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
from app.models.role import RoleDoc
from app.models.user import UserDoc, get_current_user
from app.models.rbac import require_permission
from app.models.rbac import ALL_PERMISSIONS, DEFAULT_ROLE_PERMISSIONS, get_permission_display_name, group_permissions_by_category

router = APIRouter()

# Request/Response models
class RoleCreateRequest(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = ""
    permissions: List[str] = []

class RoleUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None
    is_active: Optional[bool] = None

class RoleResponse(BaseModel):
    id: str
    name: str
    display_name: str
    description: str
    permissions: List[str]
    is_active: bool
    created_at: str
    updated_at: str

class RoleListResponse(BaseModel):
    roles: List[RoleResponse]
    total: int
    page: int
    page_size: int

@router.get("/", response_model=RoleListResponse)
@require_permission("role:view")
async def get_roles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    current_user: UserDoc = Depends(get_current_user)
):
    """
    Get list of roles with pagination and filtering
    """
    # Build query
    query = {}
    
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"display_name": {"$regex": search, "$options": "i"}}
        ]
    
    # Get total count
    total = await RoleDoc.find(query).count()
    
    # Get roles with pagination
    skip = (page - 1) * page_size
    roles = await RoleDoc.find(query).skip(skip).limit(page_size).to_list()
    
    return RoleListResponse(
        roles=[
            RoleResponse(
                id=str(role.id),
                name=role.name,
                display_name=role.display_name,
                description=role.description,
                permissions=role.permissions,
                is_active=role.is_active,
                created_at=role.created_at.isoformat(),
                updated_at=role.updated_at.isoformat()
            )
            for role in roles
        ],
        total=total,
        page=page,
        page_size=page_size
    )

@router.get("/{role_id}", response_model=RoleResponse)
@require_permission("role:view")
async def get_role(
    role_id: str,
    current_user: UserDoc = Depends(get_current_user)
):
    """
    Get role by ID
    """
    role = await RoleDoc.get(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    return RoleResponse(
        id=str(role.id),
        name=role.name,
        display_name=role.display_name,
        description=role.description,
        permissions=role.permissions,
        is_active=role.is_active,
        created_at=role.created_at.isoformat(),
        updated_at=role.updated_at.isoformat()
    )

@router.post("/", response_model=RoleResponse)
@require_permission("role:create")
async def create_role(
    role_data: RoleCreateRequest,
    current_user: UserDoc = Depends(get_current_user)
):
    """
    Create new role
    """
    # Check if role name already exists
    existing_role = await RoleDoc.find_one(RoleDoc.name == role_data.name)
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role name already exists"
        )
    
    # Validate permissions
    invalid_permissions = [p for p in role_data.permissions if p not in ALL_PERMISSIONS and p != "*"]
    if invalid_permissions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid permissions: {invalid_permissions}"
        )
    
    # Create new role
    new_role = RoleDoc(
        name=role_data.name,
        display_name=role_data.display_name,
        description=role_data.description,
        permissions=role_data.permissions
    )
    
    # Save to database
    await new_role.insert()
    
    return RoleResponse(
        id=str(new_role.id),
        name=new_role.name,
        display_name=new_role.display_name,
        description=new_role.description,
        permissions=new_role.permissions,
        is_active=new_role.is_active,
        created_at=new_role.created_at.isoformat(),
        updated_at=new_role.updated_at.isoformat()
    )

@router.put("/{role_id}", response_model=RoleResponse)
@require_permission("role:update")
async def update_role(
    role_id: str,
    role_data: RoleUpdateRequest,
    current_user: UserDoc = Depends(get_current_user)
):
    """
    Update role
    """
    role = await RoleDoc.get(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Update fields
    if role_data.display_name is not None:
        role.display_name = role_data.display_name
    if role_data.description is not None:
        role.description = role_data.description
    if role_data.is_active is not None:
        role.is_active = role_data.is_active
    if role_data.permissions is not None:
        # Validate permissions
        invalid_permissions = [p for p in role_data.permissions if p not in ALL_PERMISSIONS and p != "*"]
        if invalid_permissions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid permissions: {invalid_permissions}"
            )
        role.set_permissions(role_data.permissions)
    
    # Save changes
    await role.save()
    
    return RoleResponse(
        id=str(role.id),
        name=role.name,
        display_name=role.display_name,
        description=role.description,
        permissions=role.permissions,
        is_active=role.is_active,
        created_at=role.created_at.isoformat(),
        updated_at=role.updated_at.isoformat()
    )

@router.delete("/{role_id}")
@require_permission("role:delete")
async def delete_role(
    role_id: str,
    current_user: UserDoc = Depends(get_current_user)
):
    """
    Delete role
    """
    role = await RoleDoc.get(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Check if any users are using this role
    users_with_role = await UserDoc.find(UserDoc.role_id == role.id).count()
    if users_with_role > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete role. {users_with_role} users are using this role."
        )
    
    # Delete role
    await role.delete()
    
    return {"message": "Role deleted successfully"}

@router.get("/permissions/available", response_model=List[str])
@require_permission("role:view")
async def get_available_permissions(
    current_user: UserDoc = Depends(get_current_user)
):
    """
    Get all available permissions
    """
    return ALL_PERMISSIONS

@router.get("/permissions/grouped")
@require_permission("role:view")
async def get_permissions_grouped(
    current_user: UserDoc = Depends(get_current_user)
):
    """
    Get permissions grouped by category
    """
    return group_permissions_by_category(ALL_PERMISSIONS)

@router.post("/initialize-defaults")
async def initialize_default_roles(
    current_user: UserDoc = Depends(require_permission("*"))
):
    """
    Initialize default roles (admin only)
    """
    for role_name, permissions in DEFAULT_ROLE_PERMISSIONS.items():
        # Check if role already exists
        existing_role = await RoleDoc.find_one(RoleDoc.name == role_name)
        if existing_role:
            continue
        
        # Create role
        role = RoleDoc(
            name=role_name,
            display_name=role_name.title(),
            description=f"Default {role_name} role",
            permissions=permissions
        )
        await role.insert()
    
    return {"message": "Default roles initialized successfully"}
