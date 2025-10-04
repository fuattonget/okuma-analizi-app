#!/usr/bin/env python3
"""
Reset admin password with fixed hashing method
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import app modules
sys.path.append(str(Path(__file__).parent.parent))

from app.db import init_beanie
from app.models.user import UserDoc, get_password_hash
from app.models.role import RoleDoc

async def reset_admin_password():
    """Reset admin password with correct hashing"""
    
    # Initialize database
    await init_beanie(
        database="okuma_analizi",
        connection_string="mongodb://localhost:27017"
    )
    
    # Find admin user
    admin_user = await UserDoc.find_one(UserDoc.email == "admin@example.com")
    if not admin_user:
        print("❌ Admin user not found")
        return
    
    print(f"✅ Found admin user: {admin_user.email}")
    print(f"🔍 Current password_hash: {admin_user.password_hash[:50]}...")
    
    # Reset password with new hashing method
    new_password = "admin123"
    print(f"🔍 New password: '{new_password}' (length: {len(new_password)})")
    
    # Hash password with the fixed method
    new_hash = get_password_hash(new_password)
    print(f"🔍 New hash: {new_hash[:50]}...")
    
    # Update user
    admin_user.password_hash = new_hash
    await admin_user.save()
    
    print("✅ Admin password reset successfully")
    
    # Test verification
    print("🔍 Testing password verification...")
    if admin_user.verify_password(new_password):
        print("✅ Password verification successful")
    else:
        print("❌ Password verification failed")

if __name__ == "__main__":
    asyncio.run(reset_admin_password())
