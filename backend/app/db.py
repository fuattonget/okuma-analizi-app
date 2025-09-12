from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import redis
from rq import Queue
from app.config import settings
from app.models.documents import TextDoc, AudioFileDoc, AnalysisDoc, WordEventDoc, PauseEventDoc


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
    db.client = AsyncIOMotorClient(settings.mongo_uri)
    db.database = db.client[settings.mongo_db]
    
    # Initialize beanie with the database
    await init_beanie(
        database=db.database,
        document_models=[
            TextDoc,
            AudioFileDoc,
            AnalysisDoc,
            WordEventDoc,
            PauseEventDoc
        ]
    )


def connect_to_redis():
    """Create Redis connection and queue"""
    redis_conn.connection = redis.from_url("redis://redis:6379/0")
    redis_conn.queue = Queue("analysis", connection=redis_conn.connection)


async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()
