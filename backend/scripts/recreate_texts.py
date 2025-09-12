#!/usr/bin/env python3
"""
Recreate texts with consistent IDs based on title and grade
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import connect_to_mongo, close_mongo_connection
from app.models.documents import TextDoc
from bson import ObjectId
import hashlib

def generate_text_id(title: str, grade: str = None) -> str:
    """Generate a consistent ID based on title and grade"""
    base_string = f"{title}_{grade or 'no_grade'}"
    hash_object = hashlib.md5(base_string.encode())
    return hash_object.hexdigest()[:12]

async def recreate_texts():
    """Recreate all texts with consistent IDs"""
    await connect_to_mongo()
    
    # Sample texts with consistent IDs
    sample_texts = [
        {
            "title": "Güzel Bir Gün",
            "grade": "1",
            "body": "Bu güzel bir gün. Güneş parlıyor ve kuşlar şarkı söylüyor. Çocuklar parkta oyun oynuyor."
        },
        {
            "title": "Ailemle Vakit",
            "grade": "1", 
            "body": "Annem ve babamla birlikte vakit geçiriyorum. Yemek yiyoruz ve hikaye anlatıyoruz. Ailem beni çok seviyor."
        },
        {
            "title": "Okulda Öğrenme",
            "grade": "2",
            "body": "Öğretmenimiz bize yeni harfleri öğretiyor. Kitap okuyoruz ve yazı yazıyoruz. Okul çok eğlenceli bir yer."
        },
        {
            "title": "Hayvanlar",
            "grade": "1",
            "body": "Kediler miyavlar, köpekler havlar. Kuşlar cıvıldar, inekler möler. Her hayvanın kendine özgü sesi vardır."
        },
        {
            "title": "Mevsimler",
            "grade": "2",
            "body": "İlkbaharda çiçekler açar, yazın güneş parlar. Sonbaharda yapraklar düşer, kışın kar yağar."
        }
    ]
    
    # Clear existing texts
    print("Clearing existing texts...")
    await TextDoc.delete_all()
    
    # Create new texts with consistent IDs
    print("Creating texts with consistent IDs...")
    for text_data in sample_texts:
        text_id = generate_text_id(text_data["title"], text_data["grade"])
        
        # Create ObjectId from hash
        object_id = ObjectId(text_id.ljust(24, '0')[:24])
        
        text_doc = TextDoc(
            id=object_id,
            title=text_data["title"],
            grade=text_data["grade"],
            body=text_data["body"]
        )
        
        await text_doc.insert()
        print(f"Created: {text_data['title']} (Grade {text_data['grade']}) -> ID: {text_id}")
    
    print(f"\nSuccessfully created {len(sample_texts)} texts with consistent IDs!")
    
    # List all texts
    all_texts = await TextDoc.find_all().to_list()
    print(f"\nTotal texts in database: {len(all_texts)}")
    for text in all_texts:
        print(f"- {text.title} (Grade {text.grade}) -> {text.id}")

if __name__ == "__main__":
    asyncio.run(recreate_texts())
 