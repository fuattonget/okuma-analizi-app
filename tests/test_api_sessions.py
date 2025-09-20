"""
Test API sessions endpoints
"""
import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bson import ObjectId
from app.main import app
from app.models.documents import (
    TextDoc, AudioFileDoc, AnalysisDoc, ReadingSessionDoc,
    WordEventDoc, PauseEventDoc, SttResultDoc
)


class TestAPISessions:
    """Test sessions API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.mark.asyncio
    async def test_get_sessions_success(self, test_db, clean_db, client):
        """Test GET /v1/sessions success"""
        # Create test data
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
        
        session = ReadingSessionDoc(
            text_id=text_id,
            audio_id=audio_id,
            reader_id="test123",
            status="completed"
        )
        await session.insert()
        
        # Make request
        response = client.get("/v1/sessions")
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        
        session_data = data[0]
        assert session_data["id"] == str(session.id)
        assert session_data["text_id"] == str(text_id)
        assert session_data["audio_id"] == str(audio_id)
        assert session_data["reader_id"] == "test123"
        assert session_data["status"] == "completed"
        assert "created_at" in session_data
    
    @pytest.mark.asyncio
    async def test_get_sessions_with_filters(self, test_db, clean_db, client):
        """Test GET /v1/sessions with filters"""
        # Create test data
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
        
        # Create sessions with different statuses
        session1 = ReadingSessionDoc(
            text_id=text_id,
            audio_id=audio_id,
            reader_id="test123",
            status="completed"
        )
        await session1.insert()
        
        session2 = ReadingSessionDoc(
            text_id=text_id,
            audio_id=audio_id,
            reader_id="test456",
            status="active"
        )
        await session2.insert()
        
        # Test status filter
        response = client.get("/v1/sessions?status=completed")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "completed"
        
        # Test reader_id filter
        response = client.get("/v1/sessions?reader_id=test123")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["reader_id"] == "test123"
        
        # Test limit
        response = client.get("/v1/sessions?limit=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
    
    @pytest.mark.asyncio
    async def test_get_session_success(self, test_db, clean_db, client):
        """Test GET /v1/sessions/{id} success"""
        # Create test data
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
            content_type="audio/wav",
            size_bytes=1024000,
            duration_sec=10.5,
            hash={"md5": "test", "sha256": "test"},
            privacy={"access": "private"},
            owner={"reader_id": "test123"}
        )
        await audio.insert()
        
        session = ReadingSessionDoc(
            text_id=text_id,
            audio_id=audio_id,
            reader_id="test123",
            status="completed"
        )
        await session.insert()
        
        # Make request
        response = client.get(f"/v1/sessions/{session.id}")
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == str(session.id)
        assert data["text_id"] == str(text_id)
        assert data["audio_id"] == str(audio_id)
        assert data["reader_id"] == "test123"
        assert data["status"] == "completed"
        
        # Check text info
        assert data["text"]["title"] == "Test Text"
        assert data["text"]["body"] == "Test body"
        
        # Check audio info
        assert data["audio"]["id"] == str(audio_id)
        assert data["audio"]["original_name"] == "test.wav"
        assert data["audio"]["content_type"] == "audio/wav"
        assert data["audio"]["size_bytes"] == 1024000
        assert data["audio"]["duration_sec"] == 10.5
    
    @pytest.mark.asyncio
    async def test_get_session_not_found(self, test_db, clean_db, client):
        """Test GET /v1/sessions/{id} not found"""
        fake_id = str(ObjectId())
        
        response = client.get(f"/v1/sessions/{fake_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_get_session_invalid_id(self, test_db, clean_db, client):
        """Test GET /v1/sessions/{id} with invalid ID"""
        response = client.get("/v1/sessions/invalid-id")
        
        assert response.status_code == 400
        data = response.json()
        assert "invalid" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_get_session_analyses_success(self, test_db, clean_db, client):
        """Test GET /v1/sessions/{id}/analyses success"""
        # Create test data
        text_id = ObjectId()
        audio_id = ObjectId()
        session_id = ObjectId()
        
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
        
        session = ReadingSessionDoc(
            id=session_id,
            text_id=text_id,
            audio_id=audio_id,
            reader_id="test123",
            status="completed"
        )
        await session.insert()
        
        # Create analyses
        analysis1 = AnalysisDoc(
            session_id=session_id,
            status="done",
            summary={"wer": 0.1}
        )
        await analysis1.insert()
        
        analysis2 = AnalysisDoc(
            session_id=session_id,
            status="failed",
            error="Test error"
        )
        await analysis2.insert()
        
        # Make request
        response = client.get(f"/v1/sessions/{session_id}/analyses")
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # Check analysis data
        analysis_ids = [a["id"] for a in data]
        assert str(analysis1.id) in analysis_ids
        assert str(analysis2.id) in analysis_ids
        
        # Check analysis details
        for analysis in data:
            assert "id" in analysis
            assert "created_at" in analysis
            assert "status" in analysis
            assert "summary" in analysis
    
    @pytest.mark.asyncio
    async def test_get_session_analyses_not_found(self, test_db, clean_db, client):
        """Test GET /v1/sessions/{id}/analyses with non-existent session"""
        fake_id = str(ObjectId())
        
        response = client.get(f"/v1/sessions/{fake_id}/analyses")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_update_session_status_success(self, test_db, clean_db, client):
        """Test PUT /v1/sessions/{id}/status success"""
        # Create test data
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
        
        session = ReadingSessionDoc(
            text_id=text_id,
            audio_id=audio_id,
            reader_id="test123",
            status="active"
        )
        await session.insert()
        
        # Make request
        response = client.put(f"/v1/sessions/{session.id}/status?status=completed")
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Session status updated to completed"
        assert data["session_id"] == str(session.id)
        
        # Check that session was updated
        updated_session = await ReadingSessionDoc.get(session.id)
        assert updated_session.status == "completed"
        assert updated_session.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_update_session_status_invalid_status(self, test_db, clean_db, client):
        """Test PUT /v1/sessions/{id}/status with invalid status"""
        # Create test data
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
        
        session = ReadingSessionDoc(
            text_id=text_id,
            audio_id=audio_id,
            reader_id="test123",
            status="active"
        )
        await session.insert()
        
        # Make request with invalid status
        response = client.put(f"/v1/sessions/{session.id}/status?status=invalid")
        
        # Check response
        assert response.status_code == 400
        data = response.json()
        assert "invalid status" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_update_session_status_not_found(self, test_db, clean_db, client):
        """Test PUT /v1/sessions/{id}/status with non-existent session"""
        fake_id = str(ObjectId())
        
        response = client.put(f"/v1/sessions/{fake_id}/status?status=completed")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


class TestAPIAnalysisEvents:
    """Test analysis events API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.mark.asyncio
    async def test_get_word_events_success(self, test_db, clean_db, client):
        """Test GET /v1/analyses/{id}/word-events success"""
        # Create test data
        analysis_id = ObjectId()
        session_id = ObjectId()
        
        analysis = AnalysisDoc(
            id=analysis_id,
            session_id=session_id,
            status="done"
        )
        await analysis.insert()
        
        # Create word events
        word_events = [
            WordEventDoc(
                analysis_id=analysis_id,
                position=0,
                ref_token="test",
                hyp_token="test",
                type="correct"
            ),
            WordEventDoc(
                analysis_id=analysis_id,
                position=1,
                ref_token="word",
                hyp_token="word",
                type="correct"
            ),
            WordEventDoc(
                analysis_id=analysis_id,
                position=2,
                ref_token="missing",
                hyp_token=None,
                type="missing"
            )
        ]
        await WordEventDoc.insert_many(word_events)
        
        # Make request
        response = client.get(f"/v1/analyses/{analysis_id}/word-events")
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        
        # Check word event data
        for i, event in enumerate(data):
            assert event["id"] == str(word_events[i].id)
            assert event["analysis_id"] == str(analysis_id)
            assert event["position"] == word_events[i].position
            assert event["ref_token"] == word_events[i].ref_token
            assert event["hyp_token"] == word_events[i].hyp_token
            assert event["type"] == word_events[i].type
    
    @pytest.mark.asyncio
    async def test_get_word_events_not_found(self, test_db, clean_db, client):
        """Test GET /v1/analyses/{id}/word-events with non-existent analysis"""
        fake_id = str(ObjectId())
        
        response = client.get(f"/v1/analyses/{fake_id}/word-events")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_get_pause_events_success(self, test_db, clean_db, client):
        """Test GET /v1/analyses/{id}/pause-events success"""
        # Create test data
        analysis_id = ObjectId()
        session_id = ObjectId()
        
        analysis = AnalysisDoc(
            id=analysis_id,
            session_id=session_id,
            status="done"
        )
        await analysis.insert()
        
        # Create pause events
        pause_events = [
            PauseEventDoc(
                analysis_id=analysis_id,
                after_position=2,
                duration_ms=800.0,
                class_="long",
                start_ms=2000.0,
                end_ms=2800.0
            ),
            PauseEventDoc(
                analysis_id=analysis_id,
                after_position=5,
                duration_ms=1200.0,
                class_="very_long",
                start_ms=5000.0,
                end_ms=6200.0
            )
        ]
        await PauseEventDoc.insert_many(pause_events)
        
        # Make request
        response = client.get(f"/v1/analyses/{analysis_id}/pause-events")
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # Check pause event data
        for i, event in enumerate(data):
            assert event["id"] == str(pause_events[i].id)
            assert event["analysis_id"] == str(analysis_id)
            assert event["after_position"] == pause_events[i].after_position
            assert event["duration_ms"] == pause_events[i].duration_ms
            assert event["class_"] == pause_events[i].class_
            assert event["start_ms"] == pause_events[i].start_ms
            assert event["end_ms"] == pause_events[i].end_ms
    
    @pytest.mark.asyncio
    async def test_get_pause_events_not_found(self, test_db, clean_db, client):
        """Test GET /v1/analyses/{id}/pause-events with non-existent analysis"""
        fake_id = str(ObjectId())
        
        response = client.get(f"/v1/analyses/{fake_id}/pause-events")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_get_metrics_success(self, test_db, clean_db, client):
        """Test GET /v1/analyses/{id}/metrics success"""
        # Create test data
        analysis_id = ObjectId()
        session_id = ObjectId()
        
        analysis = AnalysisDoc(
            id=analysis_id,
            session_id=session_id,
            status="done",
            summary={
                "wer": 0.15,
                "accuracy": 85.0,
                "wpm": 120.5,
                "long_pauses": {"count": 2, "threshold_ms": 500},
                "error_types": {
                    "missing": 1,
                    "extra": 1,
                    "substitution": 1,
                    "pause_long": 2
                }
            }
        )
        await analysis.insert()
        
        # Create word events
        word_events = [
            WordEventDoc(analysis_id=analysis_id, position=0, ref_token="test", hyp_token="test", type="correct"),
            WordEventDoc(analysis_id=analysis_id, position=1, ref_token="word", hyp_token="word", type="correct"),
            WordEventDoc(analysis_id=analysis_id, position=2, ref_token="missing", hyp_token=None, type="missing"),
            WordEventDoc(analysis_id=analysis_id, position=3, ref_token=None, hyp_token="extra", type="extra"),
            WordEventDoc(analysis_id=analysis_id, position=4, ref_token="diff", hyp_token="different", type="diff")
        ]
        await WordEventDoc.insert_many(word_events)
        
        # Create pause events
        pause_events = [
            PauseEventDoc(analysis_id=analysis_id, after_position=2, duration_ms=800.0, class_="long", start_ms=2000.0, end_ms=2800.0),
            PauseEventDoc(analysis_id=analysis_id, after_position=5, duration_ms=1200.0, class_="very_long", start_ms=5000.0, end_ms=6200.0)
        ]
        await PauseEventDoc.insert_many(pause_events)
        
        # Make request
        response = client.get(f"/v1/analyses/{analysis_id}/metrics")
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        
        assert data["analysis_id"] == str(analysis_id)
        assert "counts" in data
        assert "wer" in data
        assert "accuracy" in data
        assert "wpm" in data
        assert "long_pauses" in data
        assert "error_types" in data
        
        # Check counts
        counts = data["counts"]
        assert counts["correct"] == 2
        assert counts["missing"] == 1
        assert counts["extra"] == 1
        assert counts["diff"] == 1
        assert counts["total_words"] == 5
        
        # Check metrics
        assert data["wer"] == 0.15
        assert data["accuracy"] == 85.0
        assert data["wpm"] == 120.5
        
        # Check error types
        error_types = data["error_types"]
        assert error_types["missing"] == 1
        assert error_types["extra"] == 1
        assert error_types["substitution"] == 1
        assert error_types["pause_long"] == 2
    
    @pytest.mark.asyncio
    async def test_get_metrics_not_found(self, test_db, clean_db, client):
        """Test GET /v1/analyses/{id}/metrics with non-existent analysis"""
        fake_id = str(ObjectId())
        
        response = client.get(f"/v1/analyses/{fake_id}/metrics")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_export_analysis(self, test_db, clean_db, client):
        """Test GET /v1/analyses/{id}/export success"""
        # Create test data
        analysis_id = ObjectId()
        session_id = ObjectId()
        
        analysis = AnalysisDoc(
            id=analysis_id,
            session_id=session_id,
            status="done",
            summary={
                "wer": 0.15,
                "accuracy": 85.0,
                "wpm": 120.5,
                "metrics": {
                    "correct": 2,
                    "missing": 1,
                    "extra": 1,
                    "diff": 1
                }
            }
        )
        await analysis.insert()
        
        # Create word events
        word_events = [
            WordEventDoc(
                analysis_id=analysis_id,
                position=0,
                ref_token="test",
                hyp_token="test",
                type="correct"
            ),
            WordEventDoc(
                analysis_id=analysis_id,
                position=1,
                ref_token="word",
                hyp_token="word",
                type="correct"
            ),
            WordEventDoc(
                analysis_id=analysis_id,
                position=2,
                ref_token="missing",
                hyp_token=None,
                type="missing"
            )
        ]
        await WordEventDoc.insert_many(word_events)
        
        # Create pause events
        pause_events = [
            PauseEventDoc(
                analysis_id=analysis_id,
                after_position=2,
                duration_ms=800.0,
                class_="long",
                start_ms=2000.0,
                end_ms=2800.0
            )
        ]
        await PauseEventDoc.insert_many(pause_events)
        
        # Make request
        response = client.get(f"/v1/analyses/{analysis_id}/export")
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        
        # Check main structure
        assert "analysis_id" in data
        assert "text_id" in data
        assert "events" in data
        assert "pauses" in data
        assert "summary" in data
        assert "metrics" in data
        
        # Check analysis_id
        assert data["analysis_id"] == str(analysis_id)
        assert data["text_id"] == str(session_id)
        
        # Check events
        assert len(data["events"]) == 3
        for i, event in enumerate(data["events"]):
            assert event["analysis_id"] == str(analysis_id)
            assert event["position"] == word_events[i].position
            assert event["ref_token"] == word_events[i].ref_token
            assert event["hyp_token"] == word_events[i].hyp_token
            assert event["type"] == word_events[i].type
        
        # Check pauses
        assert len(data["pauses"]) == 1
        pause = data["pauses"][0]
        assert pause["analysis_id"] == str(analysis_id)
        assert pause["after_position"] == 2
        assert pause["duration_ms"] == 800.0
        assert pause["class_"] == "long"
        
        # Check summary
        assert data["summary"]["wer"] == 0.15
        assert data["summary"]["accuracy"] == 85.0
        assert data["summary"]["wpm"] == 120.5
        
        # Check metrics
        assert data["metrics"]["correct"] == 2
        assert data["metrics"]["missing"] == 1
        assert data["metrics"]["extra"] == 1
        assert data["metrics"]["diff"] == 1