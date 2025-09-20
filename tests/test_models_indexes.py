"""
Test model indexes
"""
import pytest
from pymongo import ASCENDING, DESCENDING
from app.models.documents import (
    TextDoc, AudioFileDoc, AnalysisDoc, ReadingSessionDoc,
    WordEventDoc, PauseEventDoc, SttResultDoc
)
from app.db_init_guard import ensure_new_model_indexes


class TestModelIndexes:
    """Test that all model indexes are properly created"""
    
    @pytest.mark.asyncio
    async def test_text_doc_indexes(self, test_db, clean_db):
        """Test TextDoc indexes"""
        # Create a test document
        text = TextDoc(
            title="Test Text",
            grade=3,
            body="Test body",
            slug="test-text-3",
            canonical={"tokens": ["test", "body"]}
        )
        await text.insert()
        
        # Check indexes
        indexes = await test_db.texts.list_indexes().to_list(None)
        index_names = [idx["name"] for idx in indexes]
        
        # Should have _id_ and slug indexes
        assert "_id_" in index_names
        assert "slug_1" in index_names
        
        # Check slug index is unique
        slug_index = next(idx for idx in indexes if idx["name"] == "slug_1")
        assert slug_index.get("unique", False) is True
    
    @pytest.mark.asyncio
    async def test_audio_file_doc_indexes(self, test_db, clean_db):
        """Test AudioFileDoc indexes"""
        # Create a test document
        audio = AudioFileDoc(
            original_name="test.wav",
            storage_name="test_storage.wav",
            gcs_uri="gs://test/test.wav",
            hash={"md5": "test", "sha256": "test"},
            privacy={"access": "private"},
            owner={"reader_id": "test123"}
        )
        await audio.insert()
        
        # Check indexes
        indexes = await test_db.audiofiles.list_indexes().to_list(None)
        index_names = [idx["name"] for idx in indexes]
        
        # Should have _id_ and owner.reader_id indexes
        assert "_id_" in index_names
        assert "owner.reader_id_1" in index_names
    
    @pytest.mark.asyncio
    async def test_analysis_doc_indexes(self, test_db, clean_db):
        """Test AnalysisDoc indexes"""
        from bson import ObjectId
        
        # Create a test document
        analysis = AnalysisDoc(
            session_id=ObjectId(),
            status="done",
            summary={"wer": 0.1}
        )
        await analysis.insert()
        
        # Check indexes
        indexes = await test_db.analyses.list_indexes().to_list(None)
        index_names = [idx["name"] for idx in indexes]
        
        # Should have _id_ and session_id indexes
        assert "_id_" in index_names
        assert "session_id_1" in index_names
    
    @pytest.mark.asyncio
    async def test_reading_session_doc_indexes(self, test_db, clean_db):
        """Test ReadingSessionDoc indexes"""
        from bson import ObjectId
        
        # Create a test document
        session = ReadingSessionDoc(
            text_id=ObjectId(),
            audio_id=ObjectId(),
            reader_id="test123",
            status="active"
        )
        await session.insert()
        
        # Check indexes
        indexes = await test_db.readingsessions.list_indexes().to_list(None)
        index_names = [idx["name"] for idx in indexes]
        
        # Should have _id_, text_id, audio_id, and status indexes
        assert "_id_" in index_names
        assert "text_id_1" in index_names
        assert "audio_id_1" in index_names
        assert "status_1" in index_names
    
    @pytest.mark.asyncio
    async def test_word_event_doc_indexes(self, test_db, clean_db):
        """Test WordEventDoc indexes"""
        from bson import ObjectId
        
        # Create a test document
        word_event = WordEventDoc(
            analysis_id=ObjectId(),
            position=1,
            ref_token="test",
            hyp_token="test",
            type="correct"
        )
        await word_event.insert()
        
        # Check indexes
        indexes = await test_db.wordevents.list_indexes().to_list(None)
        index_names = [idx["name"] for idx in indexes]
        
        # Should have _id_, analysis_id, and composite index
        assert "_id_" in index_names
        assert "analysis_id_1" in index_names
        assert "analysis_id_1_position_1" in index_names
    
    @pytest.mark.asyncio
    async def test_pause_event_doc_indexes(self, test_db, clean_db):
        """Test PauseEventDoc indexes"""
        from bson import ObjectId
        
        # Create a test document
        pause_event = PauseEventDoc(
            analysis_id=ObjectId(),
            after_position=1,
            duration_ms=500.0,
            class_="short",
            start_ms=1000.0,
            end_ms=1500.0
        )
        await pause_event.insert()
        
        # Check indexes
        indexes = await test_db.pauseevents.list_indexes().to_list(None)
        index_names = [idx["name"] for idx in indexes]
        
        # Should have _id_, analysis_id, and composite index
        assert "_id_" in index_names
        assert "analysis_id_1" in index_names
        assert "analysis_id_1_after_position_1" in index_names
    
    @pytest.mark.asyncio
    async def test_stt_result_doc_indexes(self, test_db, clean_db):
        """Test SttResultDoc indexes"""
        from bson import ObjectId
        
        # Create a test document
        stt_result = SttResultDoc(
            session_id=ObjectId(),
            provider="elevenlabs",
            model="whisper-1",
            language="tr",
            transcript="test transcript",
            words=[]
        )
        await stt_result.insert()
        
        # Check indexes
        indexes = await test_db.sttresults.list_indexes().to_list(None)
        index_names = [idx["name"] for idx in indexes]
        
        # Should have _id_ and session_id indexes
        assert "_id_" in index_names
        assert "session_id_1" in index_names
    
    @pytest.mark.asyncio
    async def test_ensure_new_model_indexes(self, test_db, clean_db):
        """Test that ensure_new_model_indexes function works"""
        # This should not raise an exception
        await ensure_new_model_indexes()
        
        # Check that all collections have their indexes
        collections = [
            ("texts", TextDoc),
            ("audiofiles", AudioFileDoc),
            ("analyses", AnalysisDoc),
            ("readingsessions", ReadingSessionDoc),
            ("wordevents", WordEventDoc),
            ("pauseevents", PauseEventDoc),
            ("sttresults", SttResultDoc)
        ]
        
        for collection_name, model_class in collections:
            indexes = await test_db[collection_name].list_indexes().to_list(None)
            index_names = [idx["name"] for idx in indexes]
            
            # Should have at least _id_ index
            assert "_id_" in index_names, f"Collection {collection_name} missing _id_ index"
    
    @pytest.mark.asyncio
    async def test_index_performance(self, test_db, clean_db):
        """Test that indexes improve query performance"""
        from bson import ObjectId
        import time
        
        # Create test data
        analysis_id = ObjectId()
        word_events = []
        
        for i in range(100):
            word_event = WordEventDoc(
                analysis_id=analysis_id,
                position=i,
                ref_token=f"word{i}",
                hyp_token=f"word{i}",
                type="correct"
            )
            word_events.append(word_event)
        
        # Insert all at once
        await WordEventDoc.insert_many(word_events)
        
        # Test query performance with index
        start_time = time.time()
        results = await WordEventDoc.find({"analysis_id": analysis_id}).sort("position").to_list()
        query_time = time.time() - start_time
        
        # Should be fast (less than 1 second for 100 records)
        assert query_time < 1.0, f"Query took too long: {query_time:.3f}s"
        assert len(results) == 100
        
        # Test sorting by position
        positions = [event.position for event in results]
        assert positions == list(range(100)), "Results not sorted by position"

