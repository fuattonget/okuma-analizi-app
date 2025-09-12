from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from worker.config import settings
from backend.app.models.documents import TextDoc, AudioFileDoc, AnalysisDoc, WordEventDoc, PauseEventDoc


class Database:
    client: AsyncIOMotorClient = None
    database = None


db = Database()


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


async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()


