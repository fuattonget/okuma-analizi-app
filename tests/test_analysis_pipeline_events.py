"""
Test analysis pipeline events generation
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bson import ObjectId
from app.models.documents import (
    TextDoc, AudioFileDoc, AnalysisDoc, ReadingSessionDoc,
    WordEventDoc, PauseEventDoc, SttResultDoc
)
from worker.jobs import analyze_audio
from worker.services.alignment import build_word_events
from worker.services.pauses import detect_pauses
from worker.services.scoring import recompute_counts


class TestAnalysisPipelineEvents:
    """Test that analysis pipeline generates events correctly"""
    
    @pytest.mark.asyncio
    async def test_analyze_audio_creates_events(self, test_db, clean_db, sample_text_data, sample_audio_data):
        """Test that analyze_audio creates all required events"""
        from bson import ObjectId
        
        # Create test data
        text_id = ObjectId()
        audio_id = ObjectId()
        session_id = ObjectId()
        
        # Create text
        text = TextDoc(
            id=text_id,
            title=sample_text_data["title"],
            grade=sample_text_data["grade"],
            body=sample_text_data["body"],
            slug="test-text-3",
            canonical={"tokens": sample_text_data["canonical"]["tokens"]}
        )
        await text.insert()
        
        # Create audio
        audio = AudioFileDoc(
            id=audio_id,
            original_name=sample_audio_data["original_name"],
            storage_name=sample_audio_data["storage_name"],
            gcs_uri=sample_audio_data["gcs_uri"],
            content_type=sample_audio_data["content_type"],
            size_bytes=sample_audio_data["size_bytes"],
            duration_sec=sample_audio_data["duration_sec"],
            uploaded_by=sample_audio_data["uploaded_by"],
            hash=sample_audio_data["hash"],
            privacy=sample_audio_data["privacy"],
            owner=sample_audio_data["owner"]
        )
        await audio.insert()
        
        # Create reading session
        session = ReadingSessionDoc(
            id=session_id,
            text_id=text_id,
            audio_id=audio_id,
            reader_id="test_reader",
            status="active"
        )
        await session.insert()
        
        # Create analysis
        analysis = AnalysisDoc(
            session_id=session_id,
            status="queued"
        )
        await analysis.insert()
        
        # Mock ElevenLabs STT response
        mock_stt_response = {
            "transcript": "Bu bir test metnidir okuma analizi için kullanılacak",
            "words": [
                {"word": "Bu", "start": 0.0, "end": 0.5},
                {"word": "bir", "start": 0.5, "end": 0.8},
                {"word": "test", "start": 0.8, "end": 1.2},
                {"word": "metnidir", "start": 1.2, "end": 1.8},
                {"word": "okuma", "start": 1.8, "end": 2.3},
                {"word": "analizi", "start": 2.3, "end": 2.8},
                {"word": "için", "start": 2.8, "end": 3.1},
                {"word": "kullanılacak", "start": 3.1, "end": 3.8}
            ]
        }
        
        # Mock alignment result
        mock_alignment_result = {
            "word_events": [
                {"position": 0, "ref_token": "Bu", "hyp_token": "Bu", "type": "correct"},
                {"position": 1, "ref_token": "bir", "hyp_token": "bir", "type": "correct"},
                {"position": 2, "ref_token": "test", "hyp_token": "test", "type": "correct"},
                {"position": 3, "ref_token": "metnidir", "hyp_token": "metnidir", "type": "correct"},
                {"position": 4, "ref_token": ".", "hyp_token": None, "type": "missing"},
                {"position": 5, "ref_token": "Okuma", "hyp_token": "okuma", "type": "diff"},
                {"position": 6, "ref_token": "analizi", "hyp_token": "analizi", "type": "correct"},
                {"position": 7, "ref_token": "için", "hyp_token": "için", "type": "correct"},
                {"position": 8, "ref_token": "kullanılacak", "hyp_token": "kullanılacak", "type": "correct"},
                {"position": 9, "ref_token": ".", "hyp_token": None, "type": "missing"}
            ]
        }
        
        # Mock pause detection result
        mock_pause_events = [
            {"after_position": 4, "duration_ms": 600.0, "class_": "long", "start_ms": 1800.0, "end_ms": 2400.0},
            {"after_position": 9, "duration_ms": 800.0, "class_": "long", "start_ms": 3800.0, "end_ms": 4600.0}
        ]
        
        # Mock the external services
        with patch('worker.services.elevenlabs_stt.transcribe_audio') as mock_stt, \
             patch('worker.services.alignment.build_word_events') as mock_alignment, \
             patch('worker.services.pauses.detect_pauses') as mock_pauses, \
             patch('worker.services.scoring.recompute_counts') as mock_scoring:
            
            # Setup mocks
            mock_stt.return_value = mock_stt_response
            mock_alignment.return_value = mock_alignment_result["word_events"]
            mock_pauses.return_value = mock_pause_events
            mock_scoring.return_value = {
                "correct": 7,
                "missing": 2,
                "extra": 0,
                "diff": 1,
                "total_words": 10
            }
            
            # Run analysis
            await analyze_audio(str(analysis.id))
        
        # Check that SttResultDoc was created
        stt_results = await SttResultDoc.find({"session_id": session_id}).to_list()
        assert len(stt_results) == 1
        
        stt_result = stt_results[0]
        assert stt_result.provider == "elevenlabs"
        assert stt_result.model == "whisper-1"
        assert stt_result.language == "tr"
        assert stt_result.transcript == mock_stt_response["transcript"]
        assert len(stt_result.words) == len(mock_stt_response["words"])
        
        # Check that WordEventDoc was created
        word_events = await WordEventDoc.find({"analysis_id": analysis.id}).to_list()
        assert len(word_events) == len(mock_alignment_result["word_events"])
        
        # Check word event details
        for i, expected_event in enumerate(mock_alignment_result["word_events"]):
            event = word_events[i]
            assert event.position == expected_event["position"]
            assert event.ref_token == expected_event["ref_token"]
            assert event.hyp_token == expected_event["hyp_token"]
            assert event.type == expected_event["type"]
        
        # Check that PauseEventDoc was created
        pause_events = await PauseEventDoc.find({"analysis_id": analysis.id}).to_list()
        assert len(pause_events) == len(mock_pause_events)
        
        # Check pause event details
        for i, expected_event in enumerate(mock_pause_events):
            event = pause_events[i]
            assert event.after_position == expected_event["after_position"]
            assert event.duration_ms == expected_event["duration_ms"]
            assert event.class_ == expected_event["class_"]
            assert event.start_ms == expected_event["start_ms"]
            assert event.end_ms == expected_event["end_ms"]
        
        # Check that AnalysisDoc was updated
        updated_analysis = await AnalysisDoc.get(analysis.id)
        assert updated_analysis.status == "done"
        assert updated_analysis.summary is not None
        
        # Check summary metrics
        summary = updated_analysis.summary
        assert "wer" in summary
        assert "accuracy" in summary
        assert "wpm" in summary
        assert "counts" in summary
        assert "error_types" in summary
        
        # Check counts
        counts = summary["counts"]
        assert counts["correct"] == 7
        assert counts["missing"] == 2
        assert counts["diff"] == 1
        assert counts["total_words"] == 10
        
        # Check error types normalization
        error_types = summary["error_types"]
        assert "missing" in error_types
        assert "extra" in error_types
        assert "substitution" in error_types
        assert "pause_long" in error_types
        
        # Check that session was updated
        updated_session = await ReadingSessionDoc.get(session_id)
        assert updated_session.status == "completed"
        assert updated_session.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_build_word_events_function(self):
        """Test build_word_events function directly"""
        # Test data
        ref_tokens = ["Bu", "bir", "test", "metnidir", "."]
        hyp_tokens = ["Bu", "bir", "test", "metnidir"]  # Missing last token
        
        # Call function
        word_events = build_word_events(ref_tokens, hyp_tokens)
        
        # Check results
        assert len(word_events) == 5
        
        # Check correct events
        assert word_events[0]["position"] == 0
        assert word_events[0]["ref_token"] == "Bu"
        assert word_events[0]["hyp_token"] == "Bu"
        assert word_events[0]["type"] == "correct"
        
        assert word_events[1]["position"] == 1
        assert word_events[1]["ref_token"] == "bir"
        assert word_events[1]["hyp_token"] == "bir"
        assert word_events[1]["type"] == "correct"
        
        # Check missing event
        assert word_events[4]["position"] == 4
        assert word_events[4]["ref_token"] == "."
        assert word_events[4]["hyp_token"] is None
        assert word_events[4]["type"] == "missing"
    
    @pytest.mark.asyncio
    async def test_detect_pauses_function(self):
        """Test detect_pauses function directly"""
        # Test data - word timing data
        words = [
            {"word": "Bu", "start": 0.0, "end": 0.5},
            {"word": "bir", "start": 0.5, "end": 0.8},
            {"word": "test", "start": 0.8, "end": 1.2},
            {"word": "metnidir", "start": 1.2, "end": 1.8},
            {"word": "okuma", "start": 2.5, "end": 3.0},  # Long pause before
            {"word": "analizi", "start": 3.0, "end": 3.5},
            {"word": "için", "start": 3.5, "end": 3.8},
            {"word": "kullanılacak", "start": 3.8, "end": 4.5}
        ]
        
        # Call function
        pause_events = detect_pauses(words, long_pause_threshold_ms=500)
        
        # Check results
        assert len(pause_events) == 1  # One long pause
        
        pause = pause_events[0]
        assert pause["after_position"] == 3  # After "metnidir"
        assert pause["duration_ms"] == 700.0  # 2.5 - 1.8 = 0.7 seconds
        assert pause["class_"] == "long"
        assert pause["start_ms"] == 1800.0  # 1.8 * 1000
        assert pause["end_ms"] == 2500.0  # 2.5 * 1000
    
    @pytest.mark.asyncio
    async def test_recompute_counts_function(self):
        """Test recompute_counts function directly"""
        # Test word events
        word_events = [
            {"type": "correct"},
            {"type": "correct"},
            {"type": "missing"},
            {"type": "extra"},
            {"type": "diff"},
            {"type": "correct"},
            {"type": "missing"}
        ]
        
        # Call function
        counts = recompute_counts(word_events)
        
        # Check results
        assert counts["correct"] == 3
        assert counts["missing"] == 2
        assert counts["extra"] == 1
        assert counts["diff"] == 1
        assert counts["total_words"] == 7
    
    @pytest.mark.asyncio
    async def test_analysis_pipeline_error_handling(self, test_db, clean_db):
        """Test error handling in analysis pipeline"""
        from bson import ObjectId
        
        # Create analysis with invalid data
        analysis = AnalysisDoc(
            session_id=ObjectId(),
            status="queued"
        )
        await analysis.insert()
        
        # Mock STT to raise an error
        with patch('worker.services.elevenlabs_stt.transcribe_audio') as mock_stt:
            mock_stt.side_effect = Exception("STT service error")
            
            # Run analysis - should handle error gracefully
            await analyze_audio(str(analysis.id))
        
        # Check that analysis was marked as failed
        updated_analysis = await AnalysisDoc.get(analysis.id)
        assert updated_analysis.status == "failed"
        assert updated_analysis.error is not None
        assert "STT service error" in updated_analysis.error
        
        # Check that no events were created
        word_events = await WordEventDoc.find({"analysis_id": analysis.id}).to_list()
        assert len(word_events) == 0
        
        pause_events = await PauseEventDoc.find({"analysis_id": analysis.id}).to_list()
        assert len(pause_events) == 0
    
    @pytest.mark.asyncio
    async def test_analysis_pipeline_partial_failure(self, test_db, clean_db):
        """Test partial failure in analysis pipeline"""
        from bson import ObjectId
        
        # Create test data
        session_id = ObjectId()
        session = ReadingSessionDoc(
            id=session_id,
            text_id=ObjectId(),
            audio_id=ObjectId(),
            reader_id="test_reader",
            status="active"
        )
        await session.insert()
        
        analysis = AnalysisDoc(
            session_id=session_id,
            status="queued"
        )
        await analysis.insert()
        
        # Mock STT success but alignment failure
        mock_stt_response = {
            "transcript": "Test transcript",
            "words": [{"word": "test", "start": 0.0, "end": 1.0}]
        }
        
        with patch('worker.services.elevenlabs_stt.transcribe_audio') as mock_stt, \
             patch('worker.services.alignment.build_word_events') as mock_alignment, \
             patch('worker.services.pauses.detect_pauses') as mock_pauses:
            
            # Setup mocks
            mock_stt.return_value = mock_stt_response
            mock_alignment.side_effect = Exception("Alignment error")
            mock_pauses.return_value = []
            
            # Run analysis
            await analyze_audio(str(analysis.id))
        
        # Check that STT result was created
        stt_results = await SttResultDoc.find({"session_id": session_id}).to_list()
        assert len(stt_results) == 1
        
        # Check that analysis was marked as failed
        updated_analysis = await AnalysisDoc.get(analysis.id)
        assert updated_analysis.status == "failed"
        assert "Alignment error" in updated_analysis.error
        
        # Check that no word/pause events were created
        word_events = await WordEventDoc.find({"analysis_id": analysis.id}).to_list()
        assert len(word_events) == 0
        
        pause_events = await PauseEventDoc.find({"analysis_id": analysis.id}).to_list()
        assert len(pause_events) == 0
