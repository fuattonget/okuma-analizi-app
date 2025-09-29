"""
Test repetition detection algorithms according to criteria
Tests check_consecutive_extra_repetition and related functions
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app.services.alignment import (
    levenshtein_align, build_word_events, _detect_word_repetitions,
    tokenize_tr
)


class TestRepetitionDetection:
    """Test repetition detection according to criteria"""
    
    def test_dash_pattern_repetition(self):
        """Test repetition with -- pattern and next token similarity"""
        # Rule 1: hyp_token "--" ile bitiyorsa ve sonraki token aynı/benzer → repetition
        ref_tokens = ["okul"]
        hyp_tokens = ["okul--", "okul"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        # Find repetition events
        repetition_events = [e for e in events if e["type"] == "repetition"]
        assert len(repetition_events) == 1
        
        repetition_event = repetition_events[0]
        assert repetition_event["hyp_token"] == "okul--"
        assert repetition_event["sub_type"] in ["enhanced_pattern", "consecutive_extra"]
    
    def test_consecutive_identical_tokens(self):
        """Test repetition with consecutive identical tokens"""
        # Rule 2: Arka arkaya gelen aynı hyp_token dizileri (extra) sonradan ref_token ile eşleşiyorsa → hepsi repetition
        ref_tokens = ["güzel", "gün"]
        hyp_tokens = ["güzel", "güzel", "güzel", "gün"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        # Find repetition events
        repetition_events = [e for e in events if e["type"] == "repetition"]
        assert len(repetition_events) == 2  # Two extra "güzel" tokens should be repetition
        
        # Check that the extra "güzel" tokens are marked as repetition
        repetition_tokens = [e["hyp_token"] for e in repetition_events]
        assert "güzel" in repetition_tokens
    
    def test_partial_match_repetition(self):
        """Test repetition with partial matches"""
        ref_tokens = ["yeni", "nesil"]
        hyp_tokens = ["yeni", "nese-", "yeni", "nesil"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        # Find repetition events
        repetition_events = [e for e in events if e["type"] == "repetition"]
        assert len(repetition_events) >= 1  # At least one should be repetition
        
        # Check for "--" pattern
        dash_events = [e for e in repetition_events if e["hyp_token"] and "--" in e["hyp_token"]]
        assert len(dash_events) >= 1
    
    def test_forward_match_repetition(self):
        """Test repetition where extra tokens later match ref tokens"""
        ref_tokens = ["yeni", "nesil"]
        hyp_tokens = ["yeni", "nese-", "yeni", "nesil"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        # Should have repetition events for the extra tokens that later match
        repetition_events = [e for e in events if e["type"] == "repetition"]
        assert len(repetition_events) >= 1
        
        # Check that we have the expected pattern
        repetition_tokens = [e["hyp_token"] for e in repetition_events]
        assert "yeni" in repetition_tokens or "nese-" in repetition_tokens
    
    def test_no_repetition_false_positive(self):
        """Test that different words are not marked as repetition"""
        ref_tokens = []
        hyp_tokens = ["kelime--", "farklı"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        # Should not have repetition events for different words
        repetition_events = [e for e in events if e["type"] == "repetition"]
        assert len(repetition_events) == 0  # No repetition for different words
        
        # Should have extra events instead
        extra_events = [e for e in events if e["type"] == "extra"]
        assert len(extra_events) == 2  # Both should be extra
    
    def test_similar_word_repetition(self):
        """Test repetition with similar words"""
        ref_tokens = ["öğrenci"]
        hyp_tokens = ["öğren--", "öğrenci"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        # Should have repetition for similar words
        repetition_events = [e for e in events if e["type"] == "repetition"]
        assert len(repetition_events) == 1
        
        repetition_event = repetition_events[0]
        assert repetition_event["hyp_token"] == "öğren--"
    
    def test_multiple_repetition_patterns(self):
        """Test multiple repetition patterns in same sequence"""
        ref_tokens = ["güzel", "bir", "gün"]
        hyp_tokens = ["güzel", "güzel", "bir", "bir", "gün"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        # Should have repetition events for repeated tokens
        repetition_events = [e for e in events if e["type"] == "repetition"]
        assert len(repetition_events) == 2  # Two repetitions
        
        # Check that both "güzel" and "bir" repetitions are detected
        repetition_tokens = [e["hyp_token"] for e in repetition_events]
        assert "güzel" in repetition_tokens
        assert "bir" in repetition_tokens
    
    def test_repetition_with_punctuation(self):
        """Test repetition detection with punctuation"""
        ref_tokens = ["güzel", "gün"]
        hyp_tokens = ["güzel,", "güzel,", "gün"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        # Should detect repetition despite punctuation
        repetition_events = [e for e in events if e["type"] == "repetition"]
        assert len(repetition_events) == 1  # One repetition
        
        repetition_event = repetition_events[0]
        assert "güzel" in repetition_event["hyp_token"]


class TestRepetitionEdgeCases:
    """Test edge cases for repetition detection"""
    
    def test_single_token_no_repetition(self):
        """Test that single tokens don't create false repetition"""
        ref_tokens = ["test"]
        hyp_tokens = ["test"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        # Should not have repetition events
        repetition_events = [e for e in events if e["type"] == "repetition"]
        assert len(repetition_events) == 0
        
        # Should have correct events
        correct_events = [e for e in events if e["type"] == "correct"]
        assert len(correct_events) == 1
    
    def test_empty_sequences(self):
        """Test repetition detection with empty sequences"""
        alignment = levenshtein_align([], [])
        events = build_word_events(alignment, [])
        
        # Should not have any events
        assert len(events) == 0
    
    def test_repetition_at_beginning(self):
        """Test repetition at beginning of sequence"""
        ref_tokens = ["gün"]
        hyp_tokens = ["güzel", "güzel", "gün"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        # Should have repetition events
        repetition_events = [e for e in events if e["type"] == "repetition"]
        assert len(repetition_events) == 1
        
        repetition_event = repetition_events[0]
        assert repetition_event["hyp_token"] == "güzel"
    
    def test_repetition_at_end(self):
        """Test repetition at end of sequence"""
        ref_tokens = ["güzel"]
        hyp_tokens = ["güzel", "gün", "gün"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        # Should have repetition events
        repetition_events = [e for e in events if e["type"] == "repetition"]
        assert len(repetition_events) == 1
        
        repetition_event = repetition_events[0]
        assert repetition_event["hyp_token"] == "gün"
    
    def test_repetition_with_mixed_content(self):
        """Test repetition with mixed content"""
        ref_tokens = ["güzel", "bir", "gün"]
        hyp_tokens = ["güzel", "çok", "güzel", "bir", "gün"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        # Should have various event types
        correct_events = [e for e in events if e["type"] == "correct"]
        extra_events = [e for e in events if e["type"] == "extra"]
        repetition_events = [e for e in events if e["type"] == "repetition"]
        
        # Should have correct, extra, and repetition events
        assert len(correct_events) >= 2  # "güzel" and "gün" should be correct
        assert len(extra_events) == 1  # "çok" should be extra
        assert len(repetition_events) == 1  # "güzel" should be repetition


class TestRepetitionSubtypes:
    """Test repetition subtypes"""
    
    def test_enhanced_pattern_subtype(self):
        """Test enhanced_pattern subtype"""
        ref_tokens = ["okul"]
        hyp_tokens = ["okul--", "okul"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        repetition_events = [e for e in events if e["type"] == "repetition"]
        assert len(repetition_events) == 1
        
        repetition_event = repetition_events[0]
        assert repetition_event["sub_type"] in ["enhanced_pattern", "consecutive_extra"]
    
    def test_consecutive_extra_subtype(self):
        """Test consecutive_extra subtype"""
        ref_tokens = ["güzel", "gün"]
        hyp_tokens = ["güzel", "güzel", "güzel", "gün"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        repetition_events = [e for e in events if e["type"] == "repetition"]
        assert len(repetition_events) == 2
        
        # Check subtypes
        for event in repetition_events:
            assert event["sub_type"] in ["consecutive_extra", None]


class TestRepetitionWithRealText:
    """Test repetition detection with realistic Turkish text"""
    
    def test_turkish_repetition_scenario(self):
        """Test with realistic Turkish repetition scenario"""
        ref_text = "Atatürk'ün güzel bir günü var"
        hyp_text = "Atatürk'ün güzel güzel bir günü merhaba"
        
        ref_tokens = tokenize_tr(ref_text)
        hyp_tokens = tokenize_tr(hyp_text)
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        # Should detect repetition
        repetition_events = [e for e in events if e["type"] == "repetition"]
        assert len(repetition_events) >= 1
        
        # Should have extra events
        extra_events = [e for e in events if e["type"] == "extra"]
        assert len(extra_events) >= 1
    
    def test_complex_repetition_pattern(self):
        """Test complex repetition pattern"""
        ref_tokens = ["yeni", "nesil", "öğrenciler"]
        hyp_tokens = ["yeni", "nese-", "yeni", "nesil", "öğrenciler"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        # Should detect multiple repetitions
        repetition_events = [e for e in events if e["type"] == "repetition"]
        assert len(repetition_events) >= 2  # "yeni" and "nese-" repetitions
        
        # Check that we have the expected repetitions
        repetition_tokens = [e["hyp_token"] for e in repetition_events]
        assert "yeni" in repetition_tokens or "nese-" in repetition_tokens


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

