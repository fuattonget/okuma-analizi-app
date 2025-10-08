#!/usr/bin/env python3
"""
Script to create admin user
Usage: python create_admin.py <email> <username> <password>
"""

import asyncio
import sys
import os

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import bcrypt
from app.config import settings
from app.models.user import UserDoc
from app.models.role import RoleDoc
from app.models.student import StudentDoc
from app.models.documents import (
    TextDoc, AudioFileDoc, AnalysisDoc,
    ReadingSessionDoc, WordEventDoc,
    PauseEventDoc, SttResultDoc
)

async def create_admin_user(email: str, username: str, password: str):
    """Create admin user with proper role"""
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.mongo_uri)
    database = client[settings.mongo_db]
    
    # Initialize Beanie
    await init_beanie(
        database=database,
        document_models=[
            TextDoc,
            AudioFileDoc,
            AnalysisDoc,
            ReadingSessionDoc,
            WordEventDoc,
            PauseEventDoc,
            SttResultDoc,
            UserDoc,
            StudentDoc,
            RoleDoc
        ]
    )
    
    # Check if user already exists
    existing_user = await UserDoc.find_one(UserDoc.email == email)
    if existing_user:
        print(f"❌ User with email {email} already exists!")
        return False
    
    # Find admin role
    admin_role = await RoleDoc.find_one(RoleDoc.name == "admin")
    if not admin_role:
        print(f"❌ Admin role not found! Please run database initialization first.")
        return False
    
    # Create new admin user with bcrypt hashed password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    admin_user = UserDoc(
        email=email,
        username=username,
        password_hash=hashed_password,
        role="admin",
        role_id=admin_role.id,
        is_active=True
    )
    
    await admin_user.insert()
    
    print(f"✅ Admin user created successfully!")
    print(f"   Email: {email}")
    print(f"   Username: {username}")
    print(f"   Role: admin")
    print(f"   ID: {admin_user.id}")
    
    return True

async def main():
    if len(sys.argv) != 4:
        print("Usage: python create_admin.py <email> <username> <password>")
        print("Example: python create_admin.py admin@doky.com admin admin123")
        sys.exit(1)
    
    email = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]
    
    client = None
    try:
        await create_admin_user(email, username, password)
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Close MongoDB connection
        if client:
            client.close()

if __name__ == "__main__":
    asyncio.run(main())
