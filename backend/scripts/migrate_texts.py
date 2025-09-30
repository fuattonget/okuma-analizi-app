#!/usr/bin/env python3
"""
Migrate existing texts to new structure
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import connect_to_mongo, close_mongo_connection
from app.models.documents import TextDoc
import hashlib

def generate_text_id(title: str, grade: int) -> str:
    """Generate a consistent text_id based on grade and title"""
    base_string = f"{grade}_{title}"
    hash_object = hashlib.md5(base_string.encode())
    return hash_object.hexdigest()[:12]

async def migrate_texts():
    """Migrate existing texts to new structure"""
    await connect_to_mongo()
    
    # Get all existing texts
    texts = await TextDoc.find_all().to_list()
    print(f"Found {len(texts)} texts to migrate")
    
    for text in texts:
        print(f"Migrating: {text.title}")
        
        # Convert grade from string to int
        grade_int = int(text.grade) if text.grade else 1
        
        # Generate new text_id
        text_id = generate_text_id(text.title, grade_int)
        
        # Update the text with new structure
        text.text_id = text_id
        text.grade = grade_int
        text.comment = None
        text.active = True
        
        await text.save()
        print(f"  -> text_id: {text_id}, grade: {grade_int}")
    
    print(f"\nSuccessfully migrated {len(texts)} texts!")
    
    # List all texts
    all_texts = await TextDoc.find_all().to_list()
    print(f"\nTotal texts in database: {len(all_texts)}")
    for text in all_texts:
        print(f"- {text.title} (Grade {text.grade}) -> text_id: {text.text_id}")

if __name__ == "__main__":
    asyncio.run(migrate_texts())

