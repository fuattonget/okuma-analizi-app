from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import redis
from rq import Queue
from pymongo import ASCENDING, DESCENDING, IndexModel
import ssl
import certifi
from app.config import settings
from app.models.documents import (
    TextDoc, AudioFileDoc, AnalysisDoc,
    ReadingSessionDoc, WordEventDoc,
    PauseEventDoc, SttResultDoc
)
from app.models.user import UserDoc
from app.models.role import RoleDoc
from app.models.student import StudentDoc
from app.models.score_feedback import ScoreFeedbackDoc
from app.db_init_guard import normalize_all_documents
from loguru import logger


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
    try:
        print("🔗 Creating MongoDB client...")
        logger.info("Starting MongoDB connection process")
        
        # Create MongoDB client with SSL settings for Railway/Atlas
        try:
            # Simplified SSL/TLS options for Railway compatibility
            # Railway handles SSL/TLS at infrastructure level
            db.client = AsyncIOMotorClient(
                settings.mongo_uri,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000
            )
            logger.info(f"MongoDB client created with URI: {settings.mongo_uri}")
        except Exception as e:
            logger.error(f"Failed to create MongoDB client: {e}")
            raise
        
        # Connect to database
        try:
            print(f"📊 Connecting to database: {settings.mongo_db}")
            db.database = db.client[settings.mongo_db]
            logger.info(f"Connected to database: {settings.mongo_db}")
        except Exception as e:
            logger.error(f"Failed to connect to database {settings.mongo_db}: {e}")
            raise
        
        # Test connection
        try:
            await db.database.command("ping")
            print("✅ MongoDB connection test successful")
            logger.info("MongoDB connection test successful")
        except Exception as e:
            print(f"❌ MongoDB connection test failed: {e}")
            logger.error(f"MongoDB connection test failed: {e}")
            raise
        
        # Initialize beanie with the database
        print("🔧 Initializing Beanie ODM...")
        try:
            # Normalize indexes before initialization
            print("🔧 Normalizing document indexes...")
            print("🔍 DEBUG: About to call normalize_all_documents()")
            logger.info("Starting document index normalization")
            
            try:
                normalize_all_documents()
                print("✅ Document indexes normalized")
                logger.info("Document indexes normalized successfully")
            except Exception as e:
                print(f"❌ Document index normalization failed: {e}")
                logger.error(f"Document index normalization failed: {e}")
                raise
            
            # Debug: Check if models are normalized
            try:
                print("🔍 DEBUG: Checking TextDoc indexes after normalization...")
                for i, idx in enumerate(TextDoc.Settings.indexes):
                    print(f"🔍 DEBUG: TextDoc index {i}: {type(idx).__name__} - {idx}")
                
                print("🔍 DEBUG: Checking AudioFileDoc indexes after normalization...")
                for i, idx in enumerate(AudioFileDoc.Settings.indexes):
                    print(f"🔍 DEBUG: AudioFileDoc index {i}: {type(idx).__name__} - {idx}")
                
                logger.info("Document indexes verified after normalization")
            except Exception as e:
                print(f"❌ Document index verification failed: {e}")
                logger.error(f"Document index verification failed: {e}")
                raise
            
            print("🔍 DEBUG: About to call init_beanie...")
            logger.info("Starting Beanie ODM initialization")
            
            try:
                await init_beanie(
                    database=db.database,
                    document_models=[
                        TextDoc,
                        AudioFileDoc,
                        AnalysisDoc,
                        ReadingSessionDoc,
                        WordEventDoc,
                        PauseEventDoc,
                        SttResultDoc,
                        RoleDoc,
                        UserDoc,
                        StudentDoc,
                        ScoreFeedbackDoc
                    ]
                )
                print("✅ Beanie ODM initialized successfully")
                logger.info("Beanie ODM initialized successfully")
            except Exception as e:
                print(f"❌ Beanie ODM initialization failed: {e}")
                print(f"Error type: {type(e).__name__}")
                print(f"Error details: {str(e)}")
                logger.error(f"Beanie ODM initialization failed: {e}")
                import traceback
                traceback.print_exc()
                raise
            
        except Exception as e:
            print(f"❌ Beanie ODM initialization failed: {e}")
            print(f"Error type: {type(e).__name__}")
            print(f"Error details: {str(e)}")
            logger.error(f"Beanie ODM initialization failed: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        # Beanie handles index creation automatically through model Settings
        print("✅ Database initialization completed successfully")
        logger.info("Database initialization completed successfully")
            
    except Exception as e:
        logger.error(f"Critical error in connect_to_mongo: {e}")
        raise


def connect_to_redis():
    """Create Redis connection and queue"""
    try:
        print("🔗 Connecting to Redis...")
        logger.info("Starting Redis connection process")
        
        # Get Redis URL from settings or environment
        redis_url = settings.redis_url if settings.redis_url else "redis://redis:6379/0"
        
        try:
            redis_conn.connection = redis.from_url(
                redis_url,
                decode_responses=False,  # RQ needs bytes
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            redis_conn.connection.ping()
            logger.info(f"Redis connection created successfully: {redis_url}")
        except Exception as e:
            logger.error(f"Failed to create Redis connection: {e}")
            raise
        
        try:
            redis_conn.queue = Queue("main", connection=redis_conn.connection)
            logger.info("Redis queue created successfully")
        except Exception as e:
            logger.error(f"Failed to create Redis queue: {e}")
            raise
            
        print("✅ Redis connected successfully")
        logger.info("Redis connection completed successfully")
        
    except Exception as e:
        logger.error(f"Critical error in connect_to_redis: {e}")
        raise


async def close_mongo_connection():
    """Close database connection"""
    try:
        if db.client:
            db.client.close()
            logger.info("MongoDB connection closed successfully")
        else:
            logger.warning("MongoDB client was not initialized")
    except Exception as e:
        logger.error(f"Error closing MongoDB connection: {e}")


