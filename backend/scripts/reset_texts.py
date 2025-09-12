#!/usr/bin/env python3
"""
Reset texts with new structure
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

async def reset_texts():
    """Reset texts with new structure"""
    await connect_to_mongo()
    
    # Clear all existing texts
    print("Clearing all existing texts...")
    await TextDoc.delete_all()
    
    # Sample texts with new structure
    sample_texts = [
        {
            "title": "Güzel Bir Gün",
            "grade": 1,
            "body": "Bu güzel bir gün. Güneş parlıyor ve kuşlar şarkı söylüyor. Çocuklar parkta oyun oynuyor.",
            "comment": "1. sınıf öğrencileri için uygun basit cümleler"
        },
        {
            "title": "Ailemle Vakit",
            "grade": 1, 
            "body": "Annem ve babamla birlikte vakit geçiriyorum. Yemek yiyoruz ve hikaye anlatıyoruz. Ailem beni çok seviyor.",
            "comment": "Aile teması ile duygusal bağ kurma"
        },
        {
            "title": "Okulda Öğrenme",
            "grade": 2,
            "body": "Öğretmenimiz bize yeni harfleri öğretiyor. Kitap okuyoruz ve yazı yazıyoruz. Okul çok eğlenceli bir yer.",
            "comment": "Okul yaşamı ve öğrenme süreci"
        },
        {
            "title": "Hayvanlar",
            "grade": 1,
            "body": "Kediler miyavlar, köpekler havlar. Kuşlar cıvıldar, inekler möler. Her hayvanın kendine özgü sesi vardır.",
            "comment": "Hayvan sesleri ve özellikleri"
        },
        {
            "title": "Mevsimler",
            "grade": 2,
            "body": "İlkbaharda çiçekler açar, yazın güneş parlar. Sonbaharda yapraklar düşer, kışın kar yağar.",
            "comment": "Mevsim değişiklikleri ve doğa olayları"
        }
    ]
    
    # Create new texts with new structure
    print("Creating texts with new structure...")
    for text_data in sample_texts:
        text_id = generate_text_id(text_data["title"], text_data["grade"])
        
        text_doc = TextDoc(
            text_id=text_id,
            title=text_data["title"],
            grade=text_data["grade"],
            body=text_data["body"],
            comment=text_data["comment"],
            active=True
        )
        
        await text_doc.insert()
        print(f"Created: {text_data['title']} (Grade {text_data['grade']}) -> text_id: {text_id}")
    
    print(f"\nSuccessfully created {len(sample_texts)} texts with new structure!")
    
    # List all texts
    all_texts = await TextDoc.find_all().to_list()
    print(f"\nTotal texts in database: {len(all_texts)}")
    for text in all_texts:
        print(f"- {text.title} (Grade {text.grade}) -> text_id: {text.text_id}")

if __name__ == "__main__":
    asyncio.run(reset_texts())
