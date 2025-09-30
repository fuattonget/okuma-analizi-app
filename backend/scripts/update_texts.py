#!/usr/bin/env python3
"""
Update existing texts to have consistent IDs
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import connect_to_mongo, close_mongo_connection
from app.models.documents import TextDoc
import hashlib

def generate_text_id(title: str, grade: str = None) -> str:
    """Generate a consistent ID based on title and grade"""
    base_string = f"{title}_{grade or 'no_grade'}"
    hash_object = hashlib.md5(base_string.encode())
    return hash_object.hexdigest()[:12]

async def update_texts():
    """Update existing texts with consistent IDs"""
    await connect_to_mongo()
    
    # Get all existing texts
    texts = await TextDoc.find_all().to_list()
    print(f"Found {len(texts)} existing texts")
    
    for text in texts:
        # Generate consistent ID
        consistent_id = generate_text_id(text.title, text.grade)
        print(f"Text: {text.title} (Grade {text.grade}) -> Consistent ID: {consistent_id}")
        
        # Update the text with new ID (this will create a new document)
        new_text = TextDoc(
            title=text.title,
            grade=text.grade,
            body=text.body
        )
        
        # Delete old text
        await text.delete()
        
        # Insert new text (will get new ObjectId but we'll use consistent_id for reference)
        await new_text.insert()
        print(f"Updated: {text.title} -> New ID: {new_text.id}")
    
    print(f"\nSuccessfully updated {len(texts)} texts!")
    
    # List all texts
    all_texts = await TextDoc.find_all().to_list()
    print(f"\nTotal texts in database: {len(all_texts)}")
    for text in all_texts:
        print(f"- {text.title} (Grade {text.grade}) -> {text.id}")

if __name__ == "__main__":
    asyncio.run(update_texts())

