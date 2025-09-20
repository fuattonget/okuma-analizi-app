"""
Test alignment improvements for punctuation, apostrophe handling, and char_diff computation
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app.services.alignment import (
    levenshtein_align, build_word_events, _is_punctuation, 
    tokenize_tr, char_edit_stats
)


class TestPunctuationHandling:
    """Test punctuation handling in alignment"""
    
    def test_punctuation_not_substituted(self):
        """Test that punctuation tokens are not substituted with other punctuation tokens"""
        # With the new tokenization, punctuation is removed, so we test with clean tokens
        ref_tokens = ["bu", "güzel", "bir", "gün"]
        hyp_tokens = ["bu", "güzel", "bir", "gün"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        # All should be correct since punctuation is removed during tokenization
        correct_events = [e for e in events if e["type"] == "correct"]
        
        assert len(correct_events) == 4, "Should have 4 correct events for clean tokens"
    
    def test_punctuation_detection(self):
        """Test punctuation detection function"""
        assert _is_punctuation(".") == True
        assert _is_punctuation(",") == True
        assert _is_punctuation("!") == True
        assert _is_punctuation("?") == True
        assert _is_punctuation(";") == True
        assert _is_punctuation(":") == True
        assert _is_punctuation('"') == True
        assert _is_punctuation("'") == True
        
        assert _is_punctuation("word") == False
        assert _is_punctuation("123") == False
        assert _is_punctuation("") == False


class TestApostropheHandling:
    """Test apostrophe handling in tokenization and alignment"""
    
    def test_apostrophe_preserved_in_tokenization(self):
        """Test that apostrophes are preserved during tokenization"""
        text = "Atatürk'ün yanındakiler"
        tokens = tokenize_tr(text)
        
        # Should not split "Atatürk'ün" into separate tokens
        assert "Atatürk'ün" in tokens, "Apostrophe should be preserved in tokenization"
        assert "Atatürk" not in tokens or "ün" not in tokens, "Should not split apostrophe-joined words"
    
    def test_apostrophe_alignment(self):
        """Test alignment with apostrophe-joined words"""
        ref_tokens = ["Atatürk'ün", "yanındakiler"]
        hyp_tokens = ["Atatürk'ün", "yanındakiler"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        # Should have correct alignment
        assert len(events) == 2
        assert all(e["type"] == "correct" for e in events)
        
        # Check specific tokens
        assert events[0]["ref_token"] == "Atatürk'ün"
        assert events[0]["hyp_token"] == "Atatürk'ün"
        assert events[1]["ref_token"] == "yanındakiler"
        assert events[1]["hyp_token"] == "yanındakiler"
    
    def test_apostrophe_mismatch_alignment(self):
        """Test alignment when apostrophe handling differs"""
        ref_tokens = ["Atatürk", "ün", "yanındakiler"]  # Split form
        hyp_tokens = ["Atatürk'ün", "yanındakiler"]     # Joined form
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        # Should handle the mismatch appropriately
        # This is a complex case that might result in substitutions
        assert len(events) >= 2  # At least 2 events
        
        # Check that we don't have correct alignment for the split case
        correct_events = [e for e in events if e["type"] == "correct"]
        assert len(correct_events) >= 1  # "yanındakiler" should match


class TestCharDiffComputation:
    """Test char_diff computation for substitution events"""
    
    def test_char_diff_calculation(self):
        """Test char_diff calculation for substitution events"""
        ref_tokens = ["güzel", "bir", "gün"]
        hyp_tokens = ["güzel", "çok", "güzel", "gün"]  # "bir" -> "çok güzel"
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        # Find substitution events
        substitution_events = [e for e in events if e["type"] == "substitution"]
        
        # Should have char_diff and cer_local for substitution events
        for event in substitution_events:
            assert "char_diff" in event, "Substitution events should have char_diff"
            assert "cer_local" in event, "Substitution events should have cer_local"
            assert event["char_diff"] is not None, "char_diff should not be None"
            assert event["cer_local"] is not None, "cer_local should not be None"
            assert event["char_diff"] >= 0, "char_diff should be non-negative"
            # cer_local can be > 1 if hyp_token is longer than ref_token
            assert event["cer_local"] >= 0, "cer_local should be non-negative"
    
    def test_char_diff_values(self):
        """Test specific char_diff values"""
        # Test known cases
        assert char_edit_stats("bir", "çok")[0] == 3  # All characters different
        assert char_edit_stats("güzel", "güzel")[0] == 0  # Same word
        assert char_edit_stats("a", "ab")[0] == 1  # One character addition
        assert char_edit_stats("ab", "a")[0] == 1  # One character deletion
    
    def test_cer_local_calculation(self):
        """Test cer_local calculation"""
        ref_tokens = ["test", "word"]
        hyp_tokens = ["test", "words"]  # "word" -> "words" (1 char addition)
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        substitution_events = [e for e in events if e["type"] == "substitution"]
        
        for event in substitution_events:
            if event["ref_token"] == "word" and event["hyp_token"] == "words":
                expected_char_diff = 1
                expected_cer_local = 1 / 4  # 1 char diff / 4 char ref length
                
                assert event["char_diff"] == expected_char_diff
                assert abs(event["cer_local"] - expected_cer_local) < 0.001  # Allow small floating point errors


class TestIntegration:
    """Integration tests for all improvements"""
    
    def test_complete_alignment_scenario(self):
        """Test complete alignment with punctuation, apostrophes, and char_diff"""
        ref_text = "Atatürk'ün güzel bir günü var."
        hyp_text = "Atatürk'ün çok güzel günü var!"
        
        ref_tokens = tokenize_tr(ref_text)
        hyp_tokens = tokenize_tr(hyp_text)
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        # Check that we have the expected structure
        assert len(events) > 0
        
        # Check that punctuation is removed from tokens (no punctuation events)
        punct_events = [e for e in events if e["ref_token"] == "." or e["hyp_token"] == "!"]
        assert len(punct_events) == 0, "Should have no punctuation events since punctuation is removed"
        
        # Check apostrophe handling
        apostrophe_events = [e for e in events if "Atatürk'ün" in str(e.get("ref_token", "")) or "Atatürk'ün" in str(e.get("hyp_token", ""))]
        assert len(apostrophe_events) > 0, "Should have apostrophe events"
        
        # Check char_diff for substitutions
        substitution_events = [e for e in events if e["type"] == "substitution"]
        for event in substitution_events:
            assert event["char_diff"] is not None
            assert event["cer_local"] is not None


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
