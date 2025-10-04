#!/usr/bin/env python3
"""
Script to create admin user
Usage: python create_admin.py <email> <password>
"""

import asyncio
import sys
import os

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.config import settings
from app.models.user import UserDoc
import hashlib
from app.models.student import StudentDoc
from app.models.documents import (
    TextDoc, AudioFileDoc, AnalysisDoc,
    ReadingSessionDoc, WordEventDoc,
    PauseEventDoc, SttResultDoc
)

async def create_admin_user(email: str, password: str):
    """Create admin user"""
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
            StudentDoc
        ]
    )
    
    # Check if user already exists
    existing_user = await UserDoc.find_one(UserDoc.email == email)
    if existing_user:
        print(f"❌ User with email {email} already exists!")
        return False
    
    # Create new admin user
    # Simple password hashing for now
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    admin_user = UserDoc(
        email=email,
        password_hash=password_hash,
        role="admin"
    )
    
    await admin_user.insert()
    
    print(f"✅ Admin user created successfully!")
    print(f"   Email: {email}")
    print(f"   Role: admin")
    print(f"   ID: {admin_user.id}")
    
    return True

async def main():
    if len(sys.argv) != 3:
        print("Usage: python create_admin.py <email> <password>")
        print("Example: python create_admin.py admin@example.com admin123")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    
    try:
        await create_admin_user(email, password)
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        sys.exit(1)
    finally:
        # Close MongoDB connection
        client = AsyncIOMotorClient(settings.mongo_uri)
        client.close()

if __name__ == "__main__":
    asyncio.run(main())
