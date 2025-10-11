#!/usr/bin/env python3
"""
Script to update audio file durations in the database.
This script reads audio files from GCS and updates their duration_sec field.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from app.storage.gcs import get_client
import subprocess
import tempfile
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def update_audio_durations():
    """Update duration_sec for all audio files that don't have it set"""
    
    # Connect to MongoDB - use environment variable or Docker service name
    mongo_url = os.getenv("MONGO_URI", settings.mongo_url or settings.mongo_uri)
    mongo_db = os.getenv("MONGO_DB", settings.mongo_db)
    logger.info(f"Connecting to MongoDB: {mongo_url}, database: {mongo_db}")
    mongo_client = AsyncIOMotorClient(mongo_url)
    db = mongo_client[mongo_db]
    audio_files = db["audio_files"]
    
    # Get GCS client
    gcs_client = get_client()
    bucket = gcs_client.bucket(settings.gcs_bucket_name)
    
    # Find all audio files without duration_sec
    query = {"$or": [{"duration_sec": None}, {"duration_sec": {"$exists": False}}]}
    cursor = audio_files.find(query)
    
    count = await audio_files.count_documents(query)
    logger.info(f"Found {count} audio files without duration_sec")
    
    updated = 0
    failed = 0
    
    async for audio_doc in cursor:
        try:
            audio_id = str(audio_doc["_id"])
            gcs_uri = audio_doc.get("gcs_uri", "")
            storage_name = audio_doc.get("storage_name", "")
            
            logger.info(f"Processing audio {audio_id}: {storage_name}")
            
            # Download audio from GCS
            blob = bucket.blob(storage_name)
            if not blob.exists():
                logger.warning(f"Blob not found in GCS: {storage_name}")
                failed += 1
                continue
            
            # Download audio data to temporary file
            with tempfile.NamedTemporaryFile(suffix=os.path.splitext(storage_name)[1], delete=False) as tmp_file:
                blob.download_to_filename(tmp_file.name)
                tmp_path = tmp_file.name
            
            # Get duration using ffprobe
            try:
                result = subprocess.run(
                    [
                        'ffprobe', '-v', 'error', '-show_entries',
                        'format=duration', '-of',
                        'default=noprint_wrappers=1:nokey=1', tmp_path
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True
                )
                duration_sec = float(result.stdout.strip())
                
                # Update database
                update_result = await audio_files.update_one(
                    {"_id": audio_doc["_id"]},
                    {"$set": {"duration_sec": duration_sec}}
                )
                
                if update_result.modified_count > 0:
                    logger.info(f"✅ Updated audio {audio_id}: duration_sec={duration_sec:.2f}")
                    updated += 1
                else:
                    logger.warning(f"❌ Failed to update audio {audio_id}")
                    failed += 1
                    
            except Exception as e:
                logger.error(f"❌ Error getting duration for {audio_id}: {e}")
                failed += 1
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                
        except Exception as e:
            logger.error(f"❌ Error processing audio: {e}")
            failed += 1
    
    logger.info(f"\n✅ Updated: {updated}")
    logger.info(f"❌ Failed: {failed}")
    logger.info(f"📊 Total: {count}")
    
    # Close MongoDB connection
    mongo_client.close()


if __name__ == "__main__":
    asyncio.run(update_audio_durations())

