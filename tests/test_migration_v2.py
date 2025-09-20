"""
Test migration v2 script
"""
import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import patch, AsyncMock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.migrate_v2 import (
    migrate_text_docs, migrate_audio_docs, create_reading_sessions,
    create_word_events, create_pause_events, normalize_analysis_error_types
)
from app.models.documents import (
    TextDoc, AudioFileDoc, AnalysisDoc, ReadingSessionDoc,
    WordEventDoc, PauseEventDoc
)
from bson import ObjectId


class TestMigrationV2:
    """Test migration v2 functionality"""
    
    @pytest.mark.asyncio
    async def test_migrate_text_docs_dry_run(self, test_db, clean_db, sample_text_data):
        """Test TextDoc migration in dry-run mode"""
        # Create old format text document
        old_text = TextDoc(
            title=sample_text_data["title"],
            grade=sample_text_data["grade"],
            body=sample_text_data["body"],
            comment=sample_text_data["comment"],
            tokenized_words=sample_text_data["canonical"]["tokens"]  # Old format
        )
        await old_text.insert()
        
        # Run migration in dry-run mode
        result = await migrate_text_docs(dry_run=True, batch_size=10)
        
        # Should return count of documents to be updated
        assert result["updated"] == 1
        assert result["errors"] == 0
        
        # Document should not be changed in dry-run
        updated_text = await TextDoc.get(old_text.id)
        assert updated_text.tokenized_words == sample_text_data["canonical"]["tokens"]
        assert not hasattr(updated_text, 'canonical') or updated_text.canonical is None
    
    @pytest.mark.asyncio
    async def test_migrate_text_docs_actual(self, test_db, clean_db, sample_text_data):
        """Test TextDoc migration actual run"""
        # Create old format text document
        old_text = TextDoc(
            title=sample_text_data["title"],
            grade=sample_text_data["grade"],
            body=sample_text_data["body"],
            comment=sample_text_data["comment"],
            tokenized_words=sample_text_data["canonical"]["tokens"]  # Old format
        )
        await old_text.insert()
        
        # Run migration
        result = await migrate_text_docs(dry_run=False, batch_size=10)
        
        # Should return success
        assert result["updated"] == 1
        assert result["errors"] == 0
        
        # Document should be updated
        updated_text = await TextDoc.get(old_text.id)
        assert updated_text.canonical.tokens == sample_text_data["canonical"]["tokens"]
        assert updated_text.slug == "test-metin-3"
        assert not hasattr(updated_text, 'tokenized_words') or updated_text.tokenized_words is None
    
    @pytest.mark.asyncio
    async def test_migrate_audio_docs_dry_run(self, test_db, clean_db, sample_audio_data):
        """Test AudioFileDoc migration in dry-run mode"""
        # Create old format audio document
        old_audio = AudioFileDoc(
            original_name=sample_audio_data["original_name"],
            storage_name=sample_audio_data["storage_name"],
            gcs_uri=sample_audio_data["gcs_uri"],
            content_type=sample_audio_data["content_type"],
            size_bytes=sample_audio_data["size_bytes"],
            duration_sec=sample_audio_data["duration_sec"],
            uploaded_by=sample_audio_data["uploaded_by"],
            gcs_url="https://storage.googleapis.com/test-bucket/test_audio.wav",  # Old field
            path="/old/path/test_audio.wav"  # Old field
        )
        await old_audio.insert()
        
        # Run migration in dry-run mode
        result = await migrate_audio_docs(dry_run=True, batch_size=10)
        
        # Should return count of documents to be updated
        assert result["updated"] == 1
        assert result["errors"] == 0
        
        # Document should not be changed in dry-run
        updated_audio = await AudioFileDoc.get(old_audio.id)
        assert hasattr(updated_audio, 'gcs_url')
        assert hasattr(updated_audio, 'path')
    
    @pytest.mark.asyncio
    async def test_migrate_audio_docs_actual(self, test_db, clean_db, sample_audio_data):
        """Test AudioFileDoc migration actual run"""
        # Create old format audio document
        old_audio = AudioFileDoc(
            original_name=sample_audio_data["original_name"],
            storage_name=sample_audio_data["storage_name"],
            gcs_uri=sample_audio_data["gcs_uri"],
            content_type=sample_audio_data["content_type"],
            size_bytes=sample_audio_data["size_bytes"],
            duration_sec=sample_audio_data["duration_sec"],
            uploaded_by=sample_audio_data["uploaded_by"],
            gcs_url="https://storage.googleapis.com/test-bucket/test_audio.wav",  # Old field
            path="/old/path/test_audio.wav"  # Old field
        )
        await old_audio.insert()
        
        # Run migration
        result = await migrate_audio_docs(dry_run=False, batch_size=10)
        
        # Should return success
        assert result["updated"] == 1
        assert result["errors"] == 0
        
        # Document should be updated
        updated_audio = await AudioFileDoc.get(old_audio.id)
        assert not hasattr(updated_audio, 'gcs_url') or updated_audio.gcs_url is None
        assert not hasattr(updated_audio, 'path') or updated_audio.path is None
        assert updated_audio.privacy.access == "private"
        assert updated_audio.hash.sha256 is not None  # Should be calculated or empty
    
    @pytest.mark.asyncio
    async def test_create_reading_sessions_dry_run(self, test_db, clean_db):
        """Test ReadingSession creation in dry-run mode"""
        from bson import ObjectId
        
        # Create test text and audio
        text_id = ObjectId()
        audio_id = ObjectId()
        
        text = TextDoc(
            id=text_id,
            title="Test Text",
            grade=3,
            body="Test body",
            slug="test-text-3",
            canonical={"tokens": ["test", "body"]}
        )
        await text.insert()
        
        audio = AudioFileDoc(
            id=audio_id,
            original_name="test.wav",
            storage_name="test_storage.wav",
            gcs_uri="gs://test/test.wav",
            hash={"md5": "test", "sha256": "test"},
            privacy={"access": "private"},
            owner={"reader_id": "test123"}
        )
        await audio.insert()
        
        # Create analysis with old format
        analysis = AnalysisDoc(
            text_id=text_id,  # Old field
            audio_id=audio_id,  # Old field
            status="done",
            summary={"wer": 0.1}
        )
        await analysis.insert()
        
        # Run migration in dry-run mode
        result = await create_reading_sessions(dry_run=True, batch_size=10)
        
        # Should return count of sessions to be created
        assert result["created"] == 1
        assert result["updated"] == 1
        assert result["errors"] == 0
        
        # No sessions should be created in dry-run
        sessions = await ReadingSessionDoc.find_all().to_list()
        assert len(sessions) == 0
        
        # Analysis should not be updated
        updated_analysis = await AnalysisDoc.get(analysis.id)
        assert updated_analysis.text_id == text_id
        assert updated_analysis.audio_id == audio_id
        assert not hasattr(updated_analysis, 'session_id') or updated_analysis.session_id is None
    
    @pytest.mark.asyncio
    async def test_create_reading_sessions_actual(self, test_db, clean_db):
        """Test ReadingSession creation actual run"""
        from bson import ObjectId
        
        # Create test text and audio
        text_id = ObjectId()
        audio_id = ObjectId()
        
        text = TextDoc(
            id=text_id,
            title="Test Text",
            grade=3,
            body="Test body",
            slug="test-text-3",
            canonical={"tokens": ["test", "body"]}
        )
        await text.insert()
        
        audio = AudioFileDoc(
            id=audio_id,
            original_name="test.wav",
            storage_name="test_storage.wav",
            gcs_uri="gs://test/test.wav",
            hash={"md5": "test", "sha256": "test"},
            privacy={"access": "private"},
            owner={"reader_id": "test123"}
        )
        await audio.insert()
        
        # Create analysis with old format
        analysis = AnalysisDoc(
            text_id=text_id,  # Old field
            audio_id=audio_id,  # Old field
            status="done",
            summary={"wer": 0.1}
        )
        await analysis.insert()
        
        # Run migration
        result = await create_reading_sessions(dry_run=False, batch_size=10)
        
        # Should return success
        assert result["created"] == 1
        assert result["updated"] == 1
        assert result["errors"] == 0
        
        # Session should be created
        sessions = await ReadingSessionDoc.find_all().to_list()
        assert len(sessions) == 1
        
        session = sessions[0]
        assert session.text_id == text_id
        assert session.audio_id == audio_id
        assert session.status == "active"
        
        # Analysis should be updated
        updated_analysis = await AnalysisDoc.get(analysis.id)
        assert updated_analysis.session_id == session.id
        assert not hasattr(updated_analysis, 'text_id') or updated_analysis.text_id is None
        assert not hasattr(updated_analysis, 'audio_id') or updated_analysis.audio_id is None
    
    @pytest.mark.asyncio
    async def test_create_word_events_dry_run(self, test_db, clean_db):
        """Test WordEvent creation in dry-run mode"""
        from bson import ObjectId
        
        # Create analysis with word_details
        analysis_id = ObjectId()
        analysis = AnalysisDoc(
            id=analysis_id,
            session_id=ObjectId(),
            status="done",
            summary={
                "word_details": [
                    {"position": 0, "ref": "test", "hyp": "test", "type": "correct"},
                    {"position": 1, "ref": "word", "hyp": "word", "type": "correct"},
                    {"position": 2, "ref": "missing", "hyp": None, "type": "missing"},
                    {"position": 3, "ref": None, "hyp": "extra", "type": "extra"},
                    {"position": 4, "ref": "diff", "hyp": "different", "type": "diff"}
                ]
            }
        )
        await analysis.insert()
        
        # Run migration in dry-run mode
        result = await create_word_events(dry_run=True, batch_size=10)
        
        # Should return count of events to be created
        assert result["created"] == 5
        assert result["errors"] == 0
        
        # No events should be created in dry-run
        events = await WordEventDoc.find_all().to_list()
        assert len(events) == 0
    
    @pytest.mark.asyncio
    async def test_create_word_events_actual(self, test_db, clean_db):
        """Test WordEvent creation actual run"""
        from bson import ObjectId
        
        # Create analysis with word_details
        analysis_id = ObjectId()
        analysis = AnalysisDoc(
            id=analysis_id,
            session_id=ObjectId(),
            status="done",
            summary={
                "word_details": [
                    {"position": 0, "ref": "test", "hyp": "test", "type": "correct"},
                    {"position": 1, "ref": "word", "hyp": "word", "type": "correct"},
                    {"position": 2, "ref": "missing", "hyp": None, "type": "missing"},
                    {"position": 3, "ref": None, "hyp": "extra", "type": "extra"},
                    {"position": 4, "ref": "diff", "hyp": "different", "type": "diff"}
                ]
            }
        )
        await analysis.insert()
        
        # Run migration
        result = await create_word_events(dry_run=False, batch_size=10)
        
        # Should return success
        assert result["created"] == 5
        assert result["errors"] == 0
        
        # Events should be created
        events = await WordEventDoc.find({"analysis_id": analysis_id}).to_list()
        assert len(events) == 5
        
        # Check event details
        event_types = [event.type for event in events]
        assert "correct" in event_types
        assert "missing" in event_types
        assert "extra" in event_types
        assert "diff" in event_types
        
        # Check positions
        positions = [event.position for event in events]
        assert sorted(positions) == [0, 1, 2, 3, 4]
    
    @pytest.mark.asyncio
    async def test_create_pause_events_dry_run(self, test_db, clean_db):
        """Test PauseEvent creation in dry-run mode"""
        from bson import ObjectId
        
        # Create analysis with long_pauses
        analysis_id = ObjectId()
        analysis = AnalysisDoc(
            id=analysis_id,
            session_id=ObjectId(),
            status="done",
            summary={
                "long_pauses": [
                    {"after_position": 2, "duration_ms": 800.0, "start_ms": 2000.0, "end_ms": 2800.0},
                    {"after_position": 5, "duration_ms": 1200.0, "start_ms": 5000.0, "end_ms": 6200.0}
                ]
            }
        )
        await analysis.insert()
        
        # Run migration in dry-run mode
        result = await create_pause_events(dry_run=True, batch_size=10)
        
        # Should return count of events to be created
        assert result["created"] == 2
        assert result["errors"] == 0
        
        # No events should be created in dry-run
        events = await PauseEventDoc.find_all().to_list()
        assert len(events) == 0
    
    @pytest.mark.asyncio
    async def test_create_pause_events_actual(self, test_db, clean_db):
        """Test PauseEvent creation actual run"""
        from bson import ObjectId
        
        # Create analysis with long_pauses
        analysis_id = ObjectId()
        analysis = AnalysisDoc(
            id=analysis_id,
            session_id=ObjectId(),
            status="done",
            summary={
                "long_pauses": [
                    {"after_position": 2, "duration_ms": 800.0, "start_ms": 2000.0, "end_ms": 2800.0},
                    {"after_position": 5, "duration_ms": 1200.0, "start_ms": 5000.0, "end_ms": 6200.0}
                ]
            }
        )
        await analysis.insert()
        
        # Run migration
        result = await create_pause_events(dry_run=False, batch_size=10)
        
        # Should return success
        assert result["created"] == 2
        assert result["errors"] == 0
        
        # Events should be created
        events = await PauseEventDoc.find({"analysis_id": analysis_id}).to_list()
        assert len(events) == 2
        
        # Check event details
        durations = [event.duration_ms for event in events]
        assert 800.0 in durations
        assert 1200.0 in durations
        
        # Check positions
        positions = [event.after_position for event in events]
        assert 2 in positions
        assert 5 in positions
    
    @pytest.mark.asyncio
    async def test_normalize_analysis_error_types_dry_run(self, test_db, clean_db):
        """Test error types normalization in dry-run mode"""
        from bson import ObjectId
        
        # Create analysis with Turkish error types
        analysis_id = ObjectId()
        analysis = AnalysisDoc(
            id=analysis_id,
            session_id=ObjectId(),
            status="done",
            summary={
                "error_types": {
                    "eksik": 2,  # Turkish
                    "fazla": 1,  # Turkish
                    "değiştirme": 3,  # Turkish
                    "uzun_duraksama": 1  # Turkish
                }
            }
        )
        await analysis.insert()
        
        # Run migration in dry-run mode
        result = await normalize_analysis_error_types(dry_run=True, batch_size=10)
        
        # Should return count of documents to be updated
        assert result["updated"] == 1
        assert result["errors"] == 0
        
        # Document should not be changed in dry-run
        updated_analysis = await AnalysisDoc.get(analysis_id)
        assert updated_analysis.summary["error_types"]["eksik"] == 2
        assert updated_analysis.summary["error_types"]["fazla"] == 1
    
    @pytest.mark.asyncio
    async def test_normalize_analysis_error_types_actual(self, test_db, clean_db):
        """Test error types normalization actual run"""
        from bson import ObjectId
        
        # Create analysis with Turkish error types
        analysis_id = ObjectId()
        analysis = AnalysisDoc(
            id=analysis_id,
            session_id=ObjectId(),
            status="done",
            summary={
                "error_types": {
                    "eksik": 2,  # Turkish
                    "fazla": 1,  # Turkish
                    "değiştirme": 3,  # Turkish
                    "uzun_duraksama": 1  # Turkish
                }
            }
        )
        await analysis.insert()
        
        # Run migration
        result = await normalize_analysis_error_types(dry_run=False, batch_size=10)
        
        # Should return success
        assert result["updated"] == 1
        assert result["errors"] == 0
        
        # Document should be updated
        updated_analysis = await AnalysisDoc.get(analysis_id)
        error_types = updated_analysis.summary["error_types"]
        
        # Should have English keys
        assert "missing" in error_types
        assert "extra" in error_types
        assert "substitution" in error_types
        assert "pause_long" in error_types
        
        # Should have correct values
        assert error_types["missing"] == 2
        assert error_types["extra"] == 1
        assert error_types["substitution"] == 3
        assert error_types["pause_long"] == 1
        
        # Should not have Turkish keys
        assert "eksik" not in error_types
        assert "fazla" not in error_types
        assert "değiştirme" not in error_types
        assert "uzun_duraksama" not in error_types
