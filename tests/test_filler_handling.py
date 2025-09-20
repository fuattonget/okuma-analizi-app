"""
Tests for repetition-aware filler handling in alignment services.
"""

import pytest
from worker.services.alignment import (
    levenshtein_align, _is_filler, _is_verb_like, _is_noun_like,
    _track_filler_repetitions, _post_repair_filler_substitutions
)


class TestFillerDetection:
    """Test filler word detection"""
    
    def test_filler_detection(self):
        """Test that filler words are correctly identified"""
        assert _is_filler("çok")
        assert _is_filler("yani")
        assert _is_filler("işte")
        assert _is_filler("şey")
        assert _is_filler("eee")
        assert _is_filler("hımm")
        assert _is_filler("falan")
        assert _is_filler("baya")
        assert _is_filler("hakikaten")
        assert _is_filler("gerçekten")
        
        # Non-fillers
        assert not _is_filler("oyun")
        assert not _is_filler("güzel")
        assert not _is_filler("kitap")
        assert not _is_filler("okumak")


class TestPOSHeuristics:
    """Test POS heuristics for Turkish morphemes"""
    
    def test_verb_detection(self):
        """Test verb-like word detection"""
        assert _is_verb_like("oynuyor")  # -yor
        assert _is_verb_like("okudu")    # -du
        assert _is_verb_like("gidecek")  # -ecek
        assert _is_verb_like("gelmiş")   # -miş
        assert _is_verb_like("okur")     # -r
        assert _is_verb_like("oynarlardı")  # -lardı
        
        # Non-verbs
        assert not _is_verb_like("oyun")
        assert not _is_verb_like("kitap")
        assert not _is_verb_like("güzel")
    
    def test_noun_detection(self):
        """Test noun-like word detection"""
        assert _is_noun_like("oyunlar")   # -lar
        assert _is_noun_like("kitaplar")  # -lar
        assert _is_noun_like("oyunu")     # -u
        assert _is_noun_like("kitabı")    # -ı
        assert _is_noun_like("evde")      # -de
        assert _is_noun_like("evden")     # -den
        assert _is_noun_like("evin")      # -in
        assert _is_noun_like("kitabım")   # -ım
        
        # Non-nouns
        assert not _is_noun_like("oynuyor")
        assert not _is_noun_like("güzel")
        assert not _is_noun_like("çok")


class TestFillerRepetitionTracking:
    """Test filler repetition tracking within time windows"""
    
    def test_repetition_tracking(self):
        """Test that repeated fillers are correctly identified"""
        hyp_tokens = ["çok", "güzel", "çok", "oyun", "çok"]
        word_times = [
            {"start": 0.0, "end": 0.5},
            {"start": 0.5, "end": 1.0},
            {"start": 1.0, "end": 1.5},  # Within 2s window
            {"start": 1.5, "end": 2.0},
            {"start": 2.0, "end": 2.5}   # Within 2s window
        ]
        
        repeated = _track_filler_repetitions(hyp_tokens, word_times)
        
        # First "çok" should not be repeated
        assert not repeated.get(0, False)
        # Second "çok" should be repeated (within 2s of first)
        assert repeated.get(2, False)
        # Third "çok" should be repeated (within 2s of second)
        assert repeated.get(4, False)
    
    def test_repetition_window(self):
        """Test that repetitions outside window are not marked"""
        hyp_tokens = ["çok", "güzel", "çok"]
        word_times = [
            {"start": 0.0, "end": 0.5},
            {"start": 0.5, "end": 1.0},
            {"start": 3.0, "end": 3.5}   # Outside 2s window
        ]
        
        repeated = _track_filler_repetitions(hyp_tokens, word_times)
        
        # First "çok" should not be repeated
        assert not repeated.get(0, False)
        # Second "çok" should not be repeated (outside window)
        assert not repeated.get(2, False)


class TestFillerAlignment:
    """Test filler-aware alignment behavior"""
    
    def test_filler_vs_content_word(self):
        """Test that 'oyun' vs 'çok' results in MISSING+EXTRA, not SUB"""
        ref_tokens = ["oyun"]
        hyp_tokens = ["çok"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        
        # Should result in MISSING(oyun) + EXTRA(çok)
        assert len(alignment) == 2
        assert alignment[0] == ("insert", "", "çok", -1, 0)
        assert alignment[1] == ("delete", "oyun", "", 0, -1)
    
    def test_filler_vs_verb(self):
        """Test that verb vs filler results in MISSING+EXTRA"""
        ref_tokens = ["oynuyor"]
        hyp_tokens = ["çok"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        
        # Should result in MISSING(oynuyor) + EXTRA(çok)
        assert len(alignment) == 2
        assert alignment[0] == ("insert", "", "çok", -1, 0)
        assert alignment[1] == ("delete", "oynuyor", "", 0, -1)
    
    def test_filler_vs_noun(self):
        """Test that noun vs filler results in MISSING+EXTRA"""
        ref_tokens = ["oyunlar"]
        hyp_tokens = ["çok"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        
        # Should result in MISSING(oyunlar) + EXTRA(çok)
        assert len(alignment) == 2
        assert alignment[0] == ("insert", "", "çok", -1, 0)
        assert alignment[1] == ("delete", "oyunlar", "", 0, -1)
    
    def test_repeated_filler_alignment(self):
        """Test alignment with repeated fillers"""
        ref_tokens = ["güzel", "oyun"]
        hyp_tokens = ["çok", "çok", "oyun"]
        word_times = [
            {"start": 0.0, "end": 0.5},
            {"start": 0.5, "end": 1.0},  # Within 2s window
            {"start": 1.0, "end": 1.5}
        ]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens, word_times)
        
        # Should result in MISSING(güzel) + EXTRA(çok) + EXTRA(çok) + EQUAL(oyun)
        assert len(alignment) == 4
        assert alignment[0] == ("insert", "", "çok", -1, 0)
        assert alignment[1] == ("insert", "", "çok", -1, 1)
        assert alignment[2] == ("delete", "güzel", "", 0, -1)
        assert alignment[3] == ("equal", "oyun", "oyun", 1, 2)


class TestPostRepairPass:
    """Test post-repair pass for filler substitutions"""
    
    def test_post_repair_conversion(self):
        """Test that problematic filler substitutions are converted"""
        alignment = [
            ("replace", "oyun", "çok", 0, 0),
            ("equal", "oyun", "oyun", 1, 1)  # High similarity with ref_token
        ]
        
        repaired = _post_repair_filler_substitutions(alignment)
        
        # Should convert SUB to MISSING + EXTRA
        assert len(repaired) == 3
        assert repaired[0] == ("delete", "oyun", "", 0, -1)
        assert repaired[1] == ("insert", "", "çok", -1, 0)
        assert repaired[2] == ("equal", "oyun", "oyun", 1, 1)
    
    def test_no_repair_when_low_similarity(self):
        """Test that low similarity prevents repair"""
        alignment = [
            ("replace", "oyun", "çok", 0, 0),
            ("replace", "kitap", "masa", 1, 1)  # Low similarity
        ]
        
        repaired = _post_repair_filler_substitutions(alignment)
        
        # Should not repair due to low similarity
        assert len(repaired) == 2
        assert repaired[0] == ("replace", "oyun", "çok", 0, 0)
        assert repaired[1] == ("replace", "kitap", "masa", 1, 1)


class TestPunctuationRegression:
    """Test that punctuation rules still work"""
    
    def test_punctuation_no_substitution(self):
        """Test that punctuation never substitutes with words"""
        ref_tokens = ["."]
        hyp_tokens = ["çok"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        
        # Should result in MISSING(.) + EXTRA(çok)
        assert len(alignment) == 2
        assert alignment[0] == ("insert", "", "çok", -1, 0)
        assert alignment[1] == ("delete", ".", "", 0, -1)
    
    def test_apostrophe_preservation(self):
        """Test that apostrophe tokens remain intact"""
        ref_tokens = ["Atatürk'ün"]
        hyp_tokens = ["Atatürk'ün"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        
        # Should match exactly
        assert len(alignment) == 1
        assert alignment[0] == ("equal", "Atatürk'ün", "Atatürk'ün", 0, 0)


class TestIntegration:
    """Integration tests for complete scenarios"""
    
    def test_complete_filler_scenario(self):
        """Test complete scenario with mixed content and fillers"""
        ref_tokens = ["güzel", "oyun", "oynuyor"]
        hyp_tokens = ["çok", "çok", "güzel", "çok", "oyun", "oynuyor"]
        word_times = [
            {"start": 0.0, "end": 0.5},
            {"start": 0.5, "end": 1.0},  # Within 2s window
            {"start": 1.0, "end": 1.5},
            {"start": 1.5, "end": 2.0},  # Within 2s window
            {"start": 2.0, "end": 2.5},
            {"start": 2.5, "end": 3.0}
        ]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens, word_times)
        
        # Expected: EXTRA(çok) + EXTRA(çok) + EQUAL(güzel) + EXTRA(çok) + EQUAL(oyun) + EQUAL(oynuyor)
        assert len(alignment) == 6
        
        # Check key alignments
        operations = [op for op, _, _, _, _ in alignment]
        assert "insert" in operations  # EXTRA
        assert "equal" in operations   # CORRECT matches
