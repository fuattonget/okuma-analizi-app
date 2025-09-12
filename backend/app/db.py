from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import redis
from rq import Queue
from pymongo import ASCENDING, DESCENDING, IndexModel
from app.config import settings
from app.models.documents import TextDoc, AudioFileDoc, AnalysisDoc, WordEventDoc, PauseEventDoc
from app.db_init_guard import normalize_indexes_for


class Database:
    client: AsyncIOMotorClient = None
    database = None


class RedisConnection:
    def __init__(self):
        self.connection = None
        self.queue = None


db = Database()
redis_conn = RedisConnection()


async def connect_to_mongo():
    """Create database connection"""
    print("🔗 Creating MongoDB client...")
    db.client = AsyncIOMotorClient(settings.mongo_uri)
    print(f"📊 Connecting to database: {settings.mongo_db}")
    db.database = db.client[settings.mongo_db]
    
    # Test connection
    try:
        await db.database.command("ping")
        print("✅ MongoDB connection test successful")
    except Exception as e:
        print(f"❌ MongoDB connection test failed: {e}")
        raise
    
    # Skip Beanie initialization for now
    print("⚠️ Skipping Beanie ODM initialization (debugging mode)")
    # Beanie is temporarily disabled to isolate the index error
    
    # Create all necessary indexes
    print("📋 Creating database indexes...")
    try:
        ensure_indexes(db.database)
        print("✅ Database indexes created successfully")
    except Exception as e:
        print(f"❌ Database index creation failed: {e}")
        raise


def connect_to_redis():
    """Create Redis connection and queue"""
    redis_conn.connection = redis.from_url("redis://redis:6379/0")
    redis_conn.queue = Queue("analysis", connection=redis_conn.connection)


async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()


def ensure_indexes(database):
    """Create all necessary indexes for the application"""
    try:
        # TEXTS collection indexes
        database.texts.create_indexes([
            IndexModel([("text_id", ASCENDING)], name="texts_text_id_unique", unique=True),
            IndexModel([("grade", ASCENDING), ("active", ASCENDING)], name="texts_grade_active"),
            IndexModel([("created_at", DESCENDING)], name="texts_created_at_desc"),
        ])

        # AUDIO_FILES collection indexes
        database.audio_files.create_indexes([
            IndexModel([("text_id", ASCENDING), ("uploaded_at", DESCENDING)], name="audios_textid_uploadedat"),
            IndexModel([("storage_name", ASCENDING)], name="audios_storage_name_unique", unique=True),
            IndexModel([("gcs_uri", ASCENDING)], name="audios_gcs_uri_unique", unique=True),
            IndexModel([("uploaded_at", DESCENDING)], name="audios_uploaded_at_desc"),
        ])

        # ANALYSES collection indexes
        database.analyses.create_indexes([
            IndexModel([("audio_id", ASCENDING)], name="analyses_audio_id"),
            IndexModel([("text_id", ASCENDING)], name="analyses_text_id"),
            IndexModel([("created_at", DESCENDING)], name="analyses_created_at_desc"),
            IndexModel([("status", ASCENDING)], name="analyses_status"),
        ])

        # WORD_EVENTS collection indexes
        database.word_events.create_indexes([
            IndexModel([("analysis_id", ASCENDING), ("idx", ASCENDING)], name="word_events_analysis_idx"),
            IndexModel([("analysis_id", ASCENDING)], name="word_events_analysis_id"),
        ])

        # PAUSE_EVENTS collection indexes
        database.pause_events.create_indexes([
            IndexModel([("analysis_id", ASCENDING), ("after_word_idx", ASCENDING)], name="pause_events_analysis_word"),
            IndexModel([("analysis_id", ASCENDING)], name="pause_events_analysis_id"),
        ])

        print("✅ All indexes created successfully")
    except Exception as e:
        print(f"❌ Error creating indexes: {e}")
        raise
