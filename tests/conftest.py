"""
Test configuration and fixtures
"""
import pytest
import asyncio
import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from backend.app.models.documents import (
    TextDoc, AudioFileDoc, AnalysisDoc, ReadingSessionDoc, 
    WordEventDoc, PauseEventDoc, SttResultDoc
)
from backend.app.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db():
    """Setup test database connection"""
    # Use test database
    test_mongo_url = os.getenv("TEST_MONGO_URL", "mongodb://localhost:27017")
    test_db_name = os.getenv("TEST_DB_NAME", "okuma_analizi_test")
    
    client = AsyncIOMotorClient(test_mongo_url)
    database = client[test_db_name]
    
    # Initialize beanie with test database
    await init_beanie(
        database=database,
        document_models=[
            TextDoc, AudioFileDoc, AnalysisDoc, ReadingSessionDoc,
            WordEventDoc, PauseEventDoc, SttResultDoc
        ]
    )
    
    yield database
    
    # Cleanup
    await client.drop_database(test_db_name)
    client.close()


@pytest.fixture
async def clean_db(test_db):
    """Clean database before each test"""
    # Drop all collections
    collections = await test_db.list_collection_names()
    for collection_name in collections:
        await test_db.drop_collection(collection_name)
    
    # Reinitialize beanie
    await init_beanie(
        database=test_db,
        document_models=[
            TextDoc, AudioFileDoc, AnalysisDoc, ReadingSessionDoc,
            WordEventDoc, PauseEventDoc, SttResultDoc
        ]
    )


@pytest.fixture
def sample_text_data():
    """Sample text data for testing"""
    return {
        "title": "Test Metin",
        "grade": 3,
        "body": "Bu bir test metnidir. Okuma analizi için kullanılacak.",
        "comment": "Test için oluşturuldu",
        "canonical": {
            "tokens": ["Bu", "bir", "test", "metnidir", ".", "Okuma", "analizi", "için", "kullanılacak", "."]
        }
    }


@pytest.fixture
def sample_audio_data():
    """Sample audio data for testing"""
    return {
        "original_name": "test_audio.wav",
        "storage_name": "test_storage.wav",
        "gcs_uri": "gs://test-bucket/test_audio.wav",
        "content_type": "audio/wav",
        "size_bytes": 1024000,
        "duration_sec": 10.5,
        "uploaded_by": "test_user",
        "hash": {
            "md5": "test_md5_hash",
            "sha256": "test_sha256_hash"
        },
        "privacy": {
            "access": "private",
            "retention_policy": "1_year"
        },
        "owner": {
            "reader_id": "test_reader_123"
        }
    }


@pytest.fixture
def sample_analysis_data():
    """Sample analysis data for testing"""
    return {
        "status": "done",
        "started_at": "2024-01-01T10:00:00Z",
        "finished_at": "2024-01-01T10:05:00Z",
        "summary": {
            "wer": 0.15,
            "accuracy": 85.0,
            "wpm": 120.5,
            "counts": {
                "correct": 8,
                "missing": 1,
                "extra": 1,
                "diff": 1,
                "total_words": 10
            },
            "long_pauses": {
                "count": 2,
                "threshold_ms": 500
            },
            "error_types": {
                "missing": 1,
                "extra": 1,
                "substitution": 1,
                "pause_long": 2
            }
        }
    }

