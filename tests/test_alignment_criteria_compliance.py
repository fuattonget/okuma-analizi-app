"""
Test alignment algorithms for compliance with new criteria
Tests all 5 error types: CORRECT, SUBSTITUTION, EXTRA, MISSING, REPETITION
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app.services.alignment import (
    levenshtein_align, build_word_events, _norm_token, 
    tokenize_tr, char_edit_stats, classify_replace
)


class TestCorrectDetection:
    """Test CORRECT error type detection according to criteria"""
    
    def test_normalized_equality_correct(self):
        """Test that normalized tokens are marked as correct"""
        ref_tokens = ["İhtiyaçlarımız"]
        hyp_tokens = ["ihtiyaçlarımız."]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        # Should be correct due to normalization
        assert len(events) == 1
        assert events[0]["type"] == "correct"
        assert events[0]["sub_type"] == "case_punct_only"
        assert events[0]["ref_token"] == "İhtiyaçlarımız"
        assert events[0]["hyp_token"] == "ihtiyaçlarımız."
    
    def test_case_insensitive_correct(self):
        """Test case-insensitive matching"""
        ref_tokens = ["Güzel", "bir", "gün"]
        hyp_tokens = ["güzel", "bir", "gün"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        # All should be correct
        assert len(events) == 3
        assert all(e["type"] == "correct" for e in events)
    
    def test_punctuation_difference_correct(self):
        """Test that punctuation differences don't create errors"""
        ref_tokens = ["merhaba", "dünya"]
        hyp_tokens = ["merhaba,", "dünya."]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        # Should be correct due to punctuation normalization
        assert len(events) == 2
        assert all(e["type"] == "correct" for e in events)
    
    def test_turkish_character_normalization(self):
        """Test Turkish character normalization"""
        ref_tokens = ["çocuk", "öğrenci", "şarkı"]
        hyp_tokens = ["cocuk", "ogrenci", "sarki"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        # Should be correct due to Turkish character normalization
        assert len(events) == 3
        assert all(e["type"] == "correct" for e in events)


class TestSubstitutionDetection:
    """Test SUBSTITUTION error type detection according to criteria"""
    
    def test_substitution_basic(self):
        """Test basic substitution detection"""
        ref_tokens = ["güzel", "bir", "gün"]
        hyp_tokens = ["güzel", "çok", "gün"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        # Find substitution event
        substitution_events = [e for e in events if e["type"] == "substitution"]
        assert len(substitution_events) == 1
        
        sub_event = substitution_events[0]
        assert sub_event["ref_token"] == "bir"
        assert sub_event["hyp_token"] == "çok"
        assert sub_event["char_diff"] is not None
        assert sub_event["cer_local"] is not None
    
    def test_substitution_subtypes_harf_ekleme(self):
        """Test harf_ekleme subtype (1 harf ekleme)"""
        ref_tokens = ["test"]
        hyp_tokens = ["tests"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        substitution_events = [e for e in events if e["type"] == "substitution"]
        assert len(substitution_events) == 1
        
        sub_event = substitution_events[0]
        assert sub_event["sub_type"] == "harf_ekleme"
        assert sub_event["char_diff"] == 1
    
    def test_substitution_subtypes_harf_eksiltme(self):
        """Test harf_eksiltme subtype (1 harf eksiltme)"""
        ref_tokens = ["tests"]
        hyp_tokens = ["test"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        substitution_events = [e for e in events if e["type"] == "substitution"]
        assert len(substitution_events) == 1
        
        sub_event = substitution_events[0]
        assert sub_event["sub_type"] == "harf_eksiltme"
        assert sub_event["char_diff"] == 1
    
    def test_substitution_subtypes_hece_ekleme(self):
        """Test hece_ekleme subtype (≥2 harf ekleme)"""
        ref_tokens = ["test"]
        hyp_tokens = ["testing"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        substitution_events = [e for e in events if e["type"] == "substitution"]
        assert len(substitution_events) == 1
        
        sub_event = substitution_events[0]
        assert sub_event["sub_type"] == "hece_ekleme"
        assert sub_event["char_diff"] >= 2
    
    def test_substitution_subtypes_hece_eksiltme(self):
        """Test hece_eksiltme subtype (≥2 harf eksiltme)"""
        ref_tokens = ["testing"]
        hyp_tokens = ["test"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        substitution_events = [e for e in events if e["type"] == "substitution"]
        assert len(substitution_events) == 1
        
        sub_event = substitution_events[0]
        assert sub_event["sub_type"] == "hece_eksiltme"
        assert sub_event["char_diff"] >= 2
    
    def test_substitution_subtypes_harf_degistirme(self):
        """Test harf_değiştirme subtype (1 harf değiştirme)"""
        ref_tokens = ["test"]
        hyp_tokens = ["tast"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        substitution_events = [e for e in events if e["type"] == "substitution"]
        assert len(substitution_events) == 1
        
        sub_event = substitution_events[0]
        assert sub_event["sub_type"] == "harf_değiştirme"
        assert sub_event["char_diff"] == 1


class TestExtraDetection:
    """Test EXTRA error type detection according to criteria"""
    
    def test_extra_basic(self):
        """Test basic extra detection"""
        ref_tokens = ["güzel", "gün"]
        hyp_tokens = ["güzel", "çok", "güzel", "gün"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        extra_events = [e for e in events if e["type"] == "extra"]
        assert len(extra_events) == 1
        
        extra_event = extra_events[0]
        assert extra_event["ref_token"] is None
        assert extra_event["hyp_token"] == "çok"
    
    def test_extra_multiple(self):
        """Test multiple extra tokens"""
        ref_tokens = ["güzel"]
        hyp_tokens = ["güzel", "çok", "çok", "güzel"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        extra_events = [e for e in events if e["type"] == "extra"]
        assert len(extra_events) == 3  # "çok", "çok", "güzel"
    
    def test_extra_at_beginning(self):
        """Test extra tokens at beginning"""
        ref_tokens = ["güzel", "gün"]
        hyp_tokens = ["merhaba", "güzel", "gün"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        extra_events = [e for e in events if e["type"] == "extra"]
        assert len(extra_events) == 1
        
        extra_event = extra_events[0]
        assert extra_event["hyp_token"] == "merhaba"


class TestMissingDetection:
    """Test MISSING error type detection according to criteria"""
    
    def test_missing_basic(self):
        """Test basic missing detection"""
        ref_tokens = ["güzel", "bir", "gün"]
        hyp_tokens = ["güzel", "gün"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        missing_events = [e for e in events if e["type"] == "missing"]
        assert len(missing_events) == 1
        
        missing_event = missing_events[0]
        assert missing_event["ref_token"] == "bir"
        assert missing_event["hyp_token"] is None
    
    def test_missing_multiple(self):
        """Test multiple missing tokens"""
        ref_tokens = ["güzel", "bir", "çok", "güzel", "gün"]
        hyp_tokens = ["güzel", "gün"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        missing_events = [e for e in events if e["type"] == "missing"]
        assert len(missing_events) == 3  # "bir", "çok", "güzel"
    
    def test_missing_at_beginning(self):
        """Test missing tokens at beginning"""
        ref_tokens = ["merhaba", "güzel", "gün"]
        hyp_tokens = ["güzel", "gün"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        missing_events = [e for e in events if e["type"] == "missing"]
        assert len(missing_events) == 1
        
        missing_event = missing_events[0]
        assert missing_event["ref_token"] == "merhaba"


class TestRepetitionDetection:
    """Test REPETITION error type detection according to criteria"""
    
    def test_repetition_dash_pattern(self):
        """Test repetition with -- pattern"""
        ref_tokens = ["okul"]
        hyp_tokens = ["okul--", "okul"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        repetition_events = [e for e in events if e["type"] == "repetition"]
        assert len(repetition_events) == 1
        
        repetition_event = repetition_events[0]
        assert repetition_event["hyp_token"] == "okul--"
    
    def test_repetition_consecutive_identical(self):
        """Test repetition with consecutive identical tokens"""
        ref_tokens = ["güzel", "gün"]
        hyp_tokens = ["güzel", "güzel", "güzel", "gün"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        repetition_events = [e for e in events if e["type"] == "repetition"]
        assert len(repetition_events) == 2  # Two "güzel" tokens should be repetition
        
        # Check that the extra "güzel" tokens are marked as repetition
        repetition_tokens = [e["hyp_token"] for e in repetition_events]
        assert "güzel" in repetition_tokens
    
    def test_repetition_partial_match(self):
        """Test repetition with partial matches"""
        ref_tokens = ["yeni", "nesil"]
        hyp_tokens = ["yeni", "nese-", "yeni", "nesil"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        repetition_events = [e for e in events if e["type"] == "repetition"]
        assert len(repetition_events) >= 1  # At least one should be repetition
        
        # Check for "--" pattern
        dash_events = [e for e in repetition_events if e["hyp_token"] and "--" in e["hyp_token"]]
        assert len(dash_events) >= 1
    
    def test_repetition_forward_match(self):
        """Test repetition where extra tokens later match ref tokens"""
        ref_tokens = ["yeni", "nesil"]
        hyp_tokens = ["yeni", "nese-", "yeni", "nesil"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        # Should have repetition events for the extra tokens that later match
        repetition_events = [e for e in events if e["type"] == "repetition"]
        assert len(repetition_events) >= 1


class TestIntegrationScenarios:
    """Integration tests for complex scenarios"""
    
    def test_mixed_error_types(self):
        """Test scenario with all error types"""
        ref_tokens = ["güzel", "bir", "gün", "var"]
        hyp_tokens = ["güzel", "çok", "güzel", "gün", "merhaba"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        # Count different error types
        correct_events = [e for e in events if e["type"] == "correct"]
        substitution_events = [e for e in events if e["type"] == "substitution"]
        extra_events = [e for e in events if e["type"] == "extra"]
        missing_events = [e for e in events if e["type"] == "missing"]
        repetition_events = [e for e in events if e["type"] == "repetition"]
        
        # Should have various error types
        assert len(correct_events) >= 1  # "güzel" and "gün" should be correct
        assert len(substitution_events) >= 1  # "bir" -> "çok"
        assert len(extra_events) >= 1  # "merhaba"
        assert len(missing_events) >= 1  # "var"
        assert len(repetition_events) >= 1  # "güzel" repetition
    
    def test_turkish_text_scenario(self):
        """Test with realistic Turkish text"""
        ref_text = "Atatürk'ün güzel bir günü var"
        hyp_text = "Atatürk'ün çok güzel güzel günü merhaba"
        
        ref_tokens = tokenize_tr(ref_text)
        hyp_tokens = tokenize_tr(hyp_text)
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        # Should handle Turkish characters correctly
        assert len(events) > 0
        
        # Check that apostrophe is preserved
        apostrophe_events = [e for e in events if "Atatürk'ün" in str(e.get("ref_token", ""))]
        assert len(apostrophe_events) >= 1
    
    def test_punctuation_preservation(self):
        """Test that punctuation differences don't create errors"""
        ref_tokens = ["merhaba", "dünya"]
        hyp_tokens = ["merhaba,", "dünya."]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        # Should be correct due to punctuation normalization
        assert len(events) == 2
        assert all(e["type"] == "correct" for e in events)
        
        # Check that punctuation is preserved in tokens
        for event in events:
            if event["hyp_token"]:
                assert "," in event["hyp_token"] or "." in event["hyp_token"]


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_empty_tokens(self):
        """Test with empty token lists"""
        alignment = levenshtein_align([], [])
        events = build_word_events(alignment, [])
        
        assert len(events) == 0
    
    def test_single_token_correct(self):
        """Test single token correct case"""
        alignment = levenshtein_align(["test"], ["test"])
        events = build_word_events(alignment, [])
        
        assert len(events) == 1
        assert events[0]["type"] == "correct"
    
    def test_single_token_substitution(self):
        """Test single token substitution"""
        alignment = levenshtein_align(["test"], ["tast"])
        events = build_word_events(alignment, [])
        
        assert len(events) == 1
        assert events[0]["type"] == "substitution"
        assert events[0]["sub_type"] == "harf_değiştirme"
    
    def test_all_extra(self):
        """Test when all hypothesis tokens are extra"""
        alignment = levenshtein_align([], ["test", "word"])
        events = build_word_events(alignment, [])
        
        assert len(events) == 2
        assert all(e["type"] == "extra" for e in events)
    
    def test_all_missing(self):
        """Test when all reference tokens are missing"""
        alignment = levenshtein_align(["test", "word"], [])
        events = build_word_events(alignment, [])
        
        assert len(events) == 2
        assert all(e["type"] == "missing" for e in events)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

