#!/usr/bin/env python3
"""
Script to reset admin password
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from app.models.user import UserDoc

async def reset_admin_password():
    """Reset admin password"""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://mongodb:27017")
    db = client["okuma_analizi"]
    
    # Initialize UserDoc with database
    UserDoc.init_db(db)
    
    # Find admin user
    admin_user = await UserDoc.find_one(UserDoc.email == "admin@test.com")
    
    if not admin_user:
        print("❌ Admin user not found")
        return
    
    print(f"✅ Found admin user: {admin_user.email}")
    
    # Reset password
    admin_user.set_password("admin123")
    await admin_user.save()
    
    print("✅ Admin password reset to: admin123")
    
    # Close connection
    client.close()

if __name__ == "__main__":
    asyncio.run(reset_admin_password())


