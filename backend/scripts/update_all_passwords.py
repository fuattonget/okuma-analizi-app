#!/usr/bin/env python3
"""
Update all user passwords to pbkdf2_sha256 format
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path so we can import app modules
sys.path.append(str(Path(__file__).parent.parent))

from app.db import init_beanie
from app.models.user import UserDoc, get_password_hash

async def update_all_passwords():
    """Update all user passwords to pbkdf2_sha256 format"""
    
    # Initialize database
    await init_beanie(
        database="okuma_analizi",
        connection_string="mongodb://localhost:27017"
    )
    
    # Get all users
    users = await UserDoc.find_all().to_list()
    print(f"📋 Found {len(users)} users to update:")
    
    # Default passwords for each user
    default_passwords = {
        "admin@example.com": "admin123",
        "test@hakeegitim.com": "test123", 
        "aysenurarslan@hakeegitim.com": "admin123",
        "manager@test.com": "manager123",
        "teacher@test.com": "teacher123",
        "test@test.com": "test123"
    }
    
    updated_users = []
    
    for user in users:
        print(f"\n🔍 Updating user: {user.email}")
        
        # Get default password for this user
        password = default_passwords.get(user.email, "password123")
        
        # Update password using the new hashing method
        try:
            user.set_password(password)
            await user.save()
            print(f"✅ Updated password for: {user.email}")
            updated_users.append(user)
        except Exception as e:
            print(f"❌ Error updating password for {user.email}: {e}")
    
    print(f"\n🎉 Updated passwords for {len(updated_users)} users:")
    for user in updated_users:
        print(f"  - {user.email} ({user.username})")
    
    return updated_users

if __name__ == "__main__":
    asyncio.run(update_all_passwords())


