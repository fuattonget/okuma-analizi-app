#!/usr/bin/env python3
"""
Migration script for database schema v2
Migrates from old schema to new refactored schema
"""

import asyncio
import argparse
import hashlib
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from bson import ObjectId
from loguru import logger

# Configure logging
logger.remove()
logger.add(
    lambda msg: print(msg, end=""),
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
    level="INFO"
)


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug"""
    # Convert to lowercase and replace spaces with hyphens
    slug = text.lower()
    # Replace Turkish characters
    turkish_chars = {
        'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ö': 'o', 'ş': 's', 'ü': 'u',
        'â': 'a', 'î': 'i', 'û': 'u'
    }
    for tr_char, en_char in turkish_chars.items():
        slug = slug.replace(tr_char, en_char)
    # Remove non-alphanumeric characters except hyphens
    slug = re.sub(r'[^a-z0-9\-]', '-', slug)
    # Remove multiple consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    # Ensure minimum length
    if len(slug) < 3:
        slug = f"text-{slug}"
    return slug


def calculate_sha256(content: bytes) -> str:
    """Calculate SHA256 hash of content"""
    return hashlib.sha256(content).hexdigest()


class DatabaseMigrator:
    def __init__(self, dry_run: bool = False, batch_size: int = 100):
        self.dry_run = dry_run
        self.batch_size = batch_size
        self.stats = {
            'texts_updated': 0,
            'audio_files_updated': 0,
            'analyses_updated': 0,
            'sessions_created': 0,
            'word_events_created': 0,
            'pause_events_created': 0,
            'stt_results_created': 0,
            'errors': 0
        }

    async def migrate_texts(self, collection):
        """Migrate TextDoc: tokenized_words → canonical.tokens, add slug"""
        logger.info("🔄 Migrating TextDoc collection...")
        
        # Find texts that need migration
        query = {
            "$or": [
                {"tokenized_words": {"$exists": True}},
                {"slug": {"$exists": False}}
            ]
        }
        
        total_count = await collection.count_documents(query)
        logger.info(f"Found {total_count} texts to migrate")
        
        if total_count == 0:
            return
        
        if self.dry_run:
            logger.info(f"DRY RUN: Would migrate {total_count} TextDoc documents")
            self.stats['texts_updated'] = total_count
            return
        
        processed = 0
        async for doc in collection.find(query).batch_size(self.batch_size):
            try:
                update_doc = {}
                
                # Migrate tokenized_words to canonical.tokens
                if 'tokenized_words' in doc:
                    update_doc['canonical'] = {
                        'tokens': doc['tokenized_words']
                    }
                    update_doc['$unset'] = {'tokenized_words': 1}
                
                # Generate slug if missing
                if 'slug' not in doc:
                    slug = slugify(doc.get('title', 'untitled'))
                    # Ensure uniqueness
                    counter = 1
                    original_slug = slug
                    while await collection.find_one({"slug": slug}):
                        slug = f"{original_slug}-{counter}"
                        counter += 1
                    update_doc['slug'] = slug
                
                if update_doc:
                    await collection.update_one(
                        {"_id": doc["_id"]},
                        update_doc
                    )
                    processed += 1
                    
            except Exception as e:
                logger.error(f"Error migrating text {doc.get('_id')}: {e}")
                self.stats['errors'] += 1
        
        logger.info(f"✅ Migrated {processed} TextDoc documents")
        self.stats['texts_updated'] = processed

    async def migrate_audio_files(self, collection):
        """Migrate AudioFileDoc: remove gcs_url, add privacy.access, calculate hash.sha256"""
        logger.info("🔄 Migrating AudioFileDoc collection...")
        
        # Find audio files that need migration
        query = {
            "$or": [
                {"gcs_url": {"$exists": True}},
                {"privacy.access": {"$exists": False}},
                {"hash.sha256": {"$exists": False}}
            ]
        }
        
        total_count = await collection.count_documents(query)
        logger.info(f"Found {total_count} audio files to migrate")
        
        if total_count == 0:
            return
        
        if self.dry_run:
            logger.info(f"DRY RUN: Would migrate {total_count} AudioFileDoc documents")
            self.stats['audio_files_updated'] = total_count
            return
        
        processed = 0
        async for doc in collection.find(query).batch_size(self.batch_size):
            try:
                update_doc = {}
                unset_fields = {}
                
                # Remove gcs_url if exists
                if 'gcs_url' in doc:
                    unset_fields['gcs_url'] = 1
                
                # Add privacy.access if missing
                if 'privacy' not in doc:
                    update_doc['privacy'] = {'access': 'private'}
                elif 'privacy.access' not in doc:
                    update_doc['privacy.access'] = 'private'
                
                # Calculate SHA256 if missing and we have content
                if 'hash.sha256' not in doc and 'gcs_uri' in doc:
                    # Note: In real implementation, you'd need to download from GCS
                    # For now, we'll leave it empty as requested
                    if 'hash' not in doc:
                        update_doc['hash'] = {'md5': doc.get('md5_hash'), 'sha256': None}
                    else:
                        update_doc['hash.sha256'] = None
                
                if update_doc or unset_fields:
                    if unset_fields:
                        update_doc['$unset'] = unset_fields
                    await collection.update_one(
                        {"_id": doc["_id"]},
                        update_doc
                    )
                    processed += 1
                    
            except Exception as e:
                logger.error(f"Error migrating audio file {doc.get('_id')}: {e}")
                self.stats['errors'] += 1
        
        logger.info(f"✅ Migrated {processed} AudioFileDoc documents")
        self.stats['audio_files_updated'] = processed

    async def migrate_analyses_and_create_sessions(self, analyses_collection, sessions_collection, texts_collection, audio_files_collection):
        """Create ReadingSessionDoc for each AnalysisDoc and update references"""
        logger.info("🔄 Migrating AnalysisDoc and creating ReadingSessionDoc...")
        
        # Find analyses that need migration
        query = {
            "$or": [
                {"session_id": {"$exists": False}},
                {"summary.error_types": {"$exists": True}}
            ]
        }
        
        total_count = await analyses_collection.count_documents(query)
        logger.info(f"Found {total_count} analyses to migrate")
        
        if total_count == 0:
            return
        
        if self.dry_run:
            logger.info(f"DRY RUN: Would migrate {total_count} AnalysisDoc documents and create sessions")
            self.stats['analyses_updated'] = total_count
            self.stats['sessions_created'] = total_count
            return
        
        processed = 0
        sessions_created = 0
        
        async for analysis in analyses_collection.find(query).batch_size(self.batch_size):
            try:
                # Get text and audio info
                text_id = analysis.get('text_id')
                audio_id = analysis.get('audio_id')
                
                if not text_id or not audio_id:
                    logger.warning(f"Analysis {analysis['_id']} missing text_id or audio_id")
                    continue
                
                # Create ReadingSessionDoc
                session_doc = {
                    'text_id': ObjectId(text_id) if isinstance(text_id, str) else text_id,
                    'audio_id': ObjectId(audio_id) if isinstance(audio_id, str) else audio_id,
                    'reader_id': None,  # Will be populated later if needed
                    'status': 'completed' if analysis.get('status') == 'done' else 'active',
                    'created_at': analysis.get('created_at', datetime.utcnow()),
                    'completed_at': analysis.get('finished_at') if analysis.get('status') == 'done' else None
                }
                
                result = await sessions_collection.insert_one(session_doc)
                session_id = result.inserted_id
                sessions_created += 1
                
                # Update AnalysisDoc with session_id
                update_doc = {'session_id': session_id}
                
                # Normalize error_types in summary
                if 'summary' in analysis and isinstance(analysis['summary'], dict):
                    summary = analysis['summary'].copy()
                    if 'error_types' in summary:
                        error_types = summary['error_types']
                        normalized_errors = {}
                        
                        # Map old keys to new normalized keys
                        key_mapping = {
                            'eksik': 'missing',
                            'fazla': 'extra', 
                            'degistirme': 'substitution',
                            'uzun_duraksama': 'pause_long',
                            'harf_ek': 'missing',
                            'harf_cik': 'extra',
                            'hece_ek': 'missing',
                            'hece_cik': 'extra'
                        }
                        
                        for old_key, new_key in key_mapping.items():
                            if old_key in error_types:
                                normalized_errors[new_key] = error_types[old_key]
                        
                        # Keep existing normalized keys
                        for key in ['missing', 'extra', 'substitution', 'pause_long']:
                            if key in error_types:
                                normalized_errors[key] = error_types[key]
                        
                        summary['error_types'] = normalized_errors
                        update_doc['summary'] = summary
                
                await analyses_collection.update_one(
                    {"_id": analysis["_id"]},
                    update_doc
                )
                processed += 1
                
            except Exception as e:
                logger.error(f"Error migrating analysis {analysis.get('_id')}: {e}")
                self.stats['errors'] += 1
        
        logger.info(f"✅ Migrated {processed} AnalysisDoc documents")
        logger.info(f"✅ Created {sessions_created} ReadingSessionDoc documents")
        self.stats['analyses_updated'] = processed
        self.stats['sessions_created'] = sessions_created

    async def create_word_and_pause_events(self, analyses_collection, word_events_collection, pause_events_collection):
        """Create WordEventDoc and PauseEventDoc from AnalysisDoc.summary"""
        logger.info("🔄 Creating WordEventDoc and PauseEventDoc from AnalysisDoc.summary...")
        
        # Find analyses with word_details or long_pauses in summary
        query = {
            "$or": [
                {"summary.word_details": {"$exists": True}},
                {"summary.long_pauses": {"$exists": True}}
            ]
        }
        
        total_count = await analyses_collection.count_documents(query)
        logger.info(f"Found {total_count} analyses with word_details or long_pauses")
        
        if total_count == 0:
            return
        
        if self.dry_run:
            logger.info(f"DRY RUN: Would create word and pause events from {total_count} analyses")
            self.stats['word_events_created'] = total_count  # Estimate
            self.stats['pause_events_created'] = total_count  # Estimate
            return
        
        word_events_created = 0
        pause_events_created = 0
        
        async for analysis in analyses_collection.find(query).batch_size(self.batch_size):
            try:
                analysis_id = analysis['_id']
                summary = analysis.get('summary', {})
                
                # Create WordEventDoc from word_details
                if 'word_details' in summary and isinstance(summary['word_details'], list):
                    word_events = []
                    for i, word_detail in enumerate(summary['word_details']):
                        if isinstance(word_detail, dict):
                            word_event = {
                                'analysis_id': analysis_id,
                                'position': i,
                                'ref_token': word_detail.get('ref_token'),
                                'hyp_token': word_detail.get('hyp_token'),
                                'type': word_detail.get('type', 'unknown'),
                                'sub_type': word_detail.get('sub_type'),
                                'timing': word_detail.get('timing'),
                                'char_diff': word_detail.get('char_diff')
                            }
                            word_events.append(word_event)
                    
                    if word_events:
                        await word_events_collection.insert_many(word_events)
                        word_events_created += len(word_events)
                
                # Create PauseEventDoc from long_pauses
                if 'long_pauses' in summary and isinstance(summary['long_pauses'], list):
                    pause_events = []
                    for i, pause_detail in enumerate(summary['long_pauses']):
                        if isinstance(pause_detail, dict):
                            pause_event = {
                                'analysis_id': analysis_id,
                                'after_position': pause_detail.get('after_position', i),
                                'duration_ms': pause_detail.get('duration_ms', 0),
                                'class_': pause_detail.get('class', 'long'),
                                'start_ms': pause_detail.get('start_ms', 0),
                                'end_ms': pause_detail.get('end_ms', 0)
                            }
                            pause_events.append(pause_event)
                    
                    if pause_events:
                        await pause_events_collection.insert_many(pause_events)
                        pause_events_created += len(pause_events)
                
            except Exception as e:
                logger.error(f"Error creating events for analysis {analysis.get('_id')}: {e}")
                self.stats['errors'] += 1
        
        logger.info(f"✅ Created {word_events_created} WordEventDoc documents")
        logger.info(f"✅ Created {pause_events_created} PauseEventDoc documents")
        self.stats['word_events_created'] = word_events_created
        self.stats['pause_events_created'] = pause_events_created

    async def run_migration(self, db):
        """Run the complete migration"""
        logger.info("🚀 Starting database migration v2...")
        
        # Get collections
        texts_collection = db.texts
        audio_files_collection = db.audio_files
        analyses_collection = db.analyses
        sessions_collection = db.reading_sessions
        word_events_collection = db.word_events
        pause_events_collection = db.pause_events
        stt_results_collection = db.stt_results
        
        try:
            # Step 1: Migrate TextDoc
            await self.migrate_texts(texts_collection)
            
            # Step 2: Migrate AudioFileDoc
            await self.migrate_audio_files(audio_files_collection)
            
            # Step 3: Migrate AnalysisDoc and create ReadingSessionDoc
            await self.migrate_analyses_and_create_sessions(
                analyses_collection, sessions_collection, 
                texts_collection, audio_files_collection
            )
            
            # Step 4: Create WordEventDoc and PauseEventDoc
            await self.create_word_and_pause_events(
                analyses_collection, word_events_collection, pause_events_collection
            )
            
            # Print final statistics
            logger.info("📊 Migration Statistics:")
            for key, value in self.stats.items():
                logger.info(f"  {key}: {value}")
            
            if self.dry_run:
                logger.info("🔍 DRY RUN COMPLETED - No changes were made to the database")
            else:
                logger.info("✅ Migration completed successfully!")
                
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            raise


async def main():
    parser = argparse.ArgumentParser(description="Database migration script v2")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode (no changes)")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for processing documents")
    parser.add_argument("--mongo-uri", default="mongodb://localhost:27017", help="MongoDB connection URI")
    parser.add_argument("--mongo-db", default="okuma_analizi", help="MongoDB database name")
    
    args = parser.parse_args()
    
    # Import here to avoid issues if not installed
    from motor.motor_asyncio import AsyncIOMotorClient
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(args.mongo_uri)
    db = client[args.mongo_db]
    
    try:
        migrator = DatabaseMigrator(dry_run=args.dry_run, batch_size=args.batch_size)
        await migrator.run_migration(db)
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())

