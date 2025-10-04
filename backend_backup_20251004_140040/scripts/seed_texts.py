#!/usr/bin/env python3
"""
Seed script for creating sample texts
Run with: docker exec api python -m scripts._texts
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append('/app')

from app.db import connect_to_mongo, close_mongo_connection
from app.models.documents import TextDoc


async def seed_texts():
    """Create sample texts for testing"""
    
    # Connect to database
    await connect_to_mongo()
    
    # Sample texts
    sample_texts = [
        {
            "title": "Güzel Bir Gün",
            "grade": 1,
            "body": "Bu güzel bir gün. Güneş parlıyor ve kuşlar şarkı söylüyor. Çocuklar parkta oyun oynuyor."
        },
        {
            "title": "Okulda Öğrenme",
            "grade": 2, 
            "body": "Öğretmenimiz bize yeni harfleri öğretiyor. Kitap okuyoruz ve yazı yazıyoruz. Okul çok eğlenceli bir yer."
        },
        {
            "title": "Ailemle Vakit",
            "grade": 1,
            "body": "Annem ve babamla birlikte vakit geçiriyorum. Yemek yiyoruz ve hikaye anlatıyoruz. Ailem beni çok seviyor."
        }
    ]
    
    # Check if texts already exist
    existing_count = await TextDoc.count()
    if existing_count > 0:
        print(f"Found {existing_count} existing texts. Skipping seed.")
        return
    
    # Create texts
    created_texts = []
    for text_data in sample_texts:
        # Create slug from title
        slug = text_data["title"].lower().replace(" ", "-").replace("ı", "i").replace("ğ", "g").replace("ü", "u").replace("ş", "s").replace("ö", "o").replace("ç", "c")
        
        print(f"Creating text with data: {text_data}")
        print(f"Slug: {slug}")
        
        try:
            text_doc = TextDoc(
                title=text_data["title"],
                grade=text_data["grade"],
                body=text_data["body"],
                slug=slug
            )
            print(f"TextDoc created successfully: {text_doc.title}")
        except Exception as e:
            print(f"Error creating TextDoc: {e}")
            print(f"Text data: {text_data}")
            print(f"Slug: {slug}")
            import traceback
            traceback.print_exc()
            continue
        
        await text_doc.insert()
        created_texts.append(text_doc)
        print(f"Created text: {text_doc.title} (Grade {text_doc.grade})")
    
    print(f"Successfully created {len(created_texts)} sample texts.")
    
    # Close database connection
    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(seed_texts())


