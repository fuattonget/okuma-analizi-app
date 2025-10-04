#!/usr/bin/env python3
"""
Script to create test users for RBAC testing
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import init_beanie
from app.models.user import UserDoc
from app.models.role import RoleDoc
from bson import ObjectId

async def create_test_users():
    """Create test users for each role"""
    
    # Initialize database
    await init_beanie(
        database="okuma_analizi",
        connection_string="mongodb://mongodb:27017",
        document_models=[
            "app.models.user.UserDoc",
            "app.models.role.RoleDoc"
        ]
    )
    
    # Get roles
    admin_role = await RoleDoc.find_one(RoleDoc.name == "admin")
    manager_role = await RoleDoc.find_one(RoleDoc.name == "manager")
    teacher_role = await RoleDoc.find_one(RoleDoc.name == "teacher")
    
    if not admin_role or not manager_role or not teacher_role:
        print("❌ Roles not found. Please create roles first.")
        return
    
    print(f"✅ Found roles: admin={admin_role.id}, manager={manager_role.id}, teacher={teacher_role.id}")
    
    # Test users data
    test_users = [
        {
            "email": "admin@test.com",
            "username": "Admin Test",
            "password": "admin123",
            "role_id": admin_role.id,
            "is_active": True
        },
        {
            "email": "manager@test.com", 
            "username": "Manager Test",
            "password": "password123",
            "role_id": manager_role.id,
            "is_active": True
        },
        {
            "email": "teacher@test.com",
            "username": "Teacher Test", 
            "password": "password123",
            "role_id": teacher_role.id,
            "is_active": True
        }
    ]
    
    # Create or update users
    for user_data in test_users:
        existing_user = await UserDoc.find_one(UserDoc.email == user_data["email"])
        
        if existing_user:
            # Update existing user
            existing_user.username = user_data["username"]
            existing_user.role_id = user_data["role_id"]
            existing_user.is_active = user_data["is_active"]
            existing_user.set_password(user_data["password"])
            await existing_user.save()
            print(f"✅ Updated user: {user_data['email']}")
        else:
            # Create new user
            user = UserDoc(
                email=user_data["email"],
                username=user_data["username"],
                role_id=user_data["role_id"],
                is_active=user_data["is_active"]
            )
            user.set_password(user_data["password"])
            await user.save()
            print(f"✅ Created user: {user_data['email']}")
    
    print("🎉 Test users created/updated successfully!")

if __name__ == "__main__":
    asyncio.run(create_test_users())
