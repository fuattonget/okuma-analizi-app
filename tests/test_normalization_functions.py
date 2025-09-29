"""
Test normalization functions for alignment algorithms
Tests _norm_token, classify_replace, and related functions
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app.services.alignment import (
    _norm_token, classify_replace, normalize_sub_type, 
    char_edit_stats, syllables_tr
)


class TestNormTokenFunction:
    """Test _norm_token function according to criteria"""
    
    def test_lowercase_conversion(self):
        """Test lowercase conversion"""
        assert _norm_token("GÜZEL") == "guzel"
        assert _norm_token("Güzel") == "guzel"
        assert _norm_token("güzel") == "guzel"
    
    def test_turkish_character_normalization(self):
        """Test Turkish character normalization"""
        # İ → i
        assert _norm_token("İhtiyaç") == "ihtiyac"
        assert _norm_token("ihtiyaç") == "ihtiyac"
        
        # ğ → g
        assert _norm_token("dağ") == "dag"
        assert _norm_token("DAĞ") == "dag"
        
        # ç → c
        assert _norm_token("çocuk") == "cocuk"
        assert _norm_token("ÇOCUK") == "cocuk"
        
        # ö → o
        assert _norm_token("göz") == "goz"
        assert _norm_token("GÖZ") == "goz"
        
        # ü → u
        assert _norm_token("gül") == "gul"
        assert _norm_token("GÜL") == "gul"
        
        # ş → s
        assert _norm_token("şarkı") == "sarki"
        assert _norm_token("ŞARKI") == "sarki"
    
    def test_punctuation_preservation(self):
        """Test that punctuation is preserved according to criteria"""
        # Punctuation should be preserved (not stripped)
        assert _norm_token("merhaba,") == "merhaba,"
        assert _norm_token("dünya.") == "dunya."
        assert _norm_token("güzel!") == "guzel!"
        assert _norm_token("nasıl?") == "nasil?"
        assert _norm_token("evet;") == "evet;"
        assert _norm_token("hayır:") == "hayir:"
        assert _norm_token('"test"') == '"test"'
        assert _norm_token("'test'") == "'test'"
    
    def test_dash_stripping(self):
        """Test that dashes are stripped for repetition detection"""
        # Dashes should be stripped (for repetition detection)
        assert _norm_token("test--") == "test"
        assert _norm_token("--test") == "test"
        assert _norm_token("--test--") == "test"
        assert _norm_token("test---") == "test"
    
    def test_empty_and_none_inputs(self):
        """Test edge cases with empty and None inputs"""
        assert _norm_token("") == ""
        assert _norm_token(None) == ""
    
    def test_unicode_normalization(self):
        """Test Unicode normalization"""
        # Test combining diacritical marks removal
        assert _norm_token("café") == "cafe"
        assert _norm_token("naïve") == "naive"
    
    def test_mixed_content(self):
        """Test with mixed content"""
        assert _norm_token("Güzel, bir gün!") == "guzel, bir gun!"
        assert _norm_token("Atatürk'ün") == "ataturk'un"
        assert _norm_token("çocuk--") == "cocuk"


class TestClassifyReplaceFunction:
    """Test classify_replace function according to criteria"""
    
    def test_harf_ekleme(self):
        """Test harf_ekleme (1 harf ekleme)"""
        assert classify_replace("test", "tests") == "harf_ekleme"
        assert classify_replace("a", "ab") == "harf_ekleme"
        assert classify_replace("güzel", "güzell") == "harf_ekleme"
    
    def test_harf_eksiltme(self):
        """Test harf_eksiltme (1 harf eksiltme)"""
        assert classify_replace("tests", "test") == "harf_eksiltme"
        assert classify_replace("ab", "a") == "harf_eksiltme"
        assert classify_replace("güzell", "güzel") == "harf_eksiltme"
    
    def test_harf_degistirme(self):
        """Test harf_değiştirme (1 harf değiştirme)"""
        assert classify_replace("test", "tast") == "harf_değiştirme"
        assert classify_replace("güzel", "güzel") == "harf_değiştirme"  # Same length, 1 edit
        assert classify_replace("a", "b") == "harf_değiştirme"
    
    def test_hece_ekleme(self):
        """Test hece_ekleme (≥2 harf ekleme)"""
        assert classify_replace("test", "testing") == "hece_ekleme"  # 2+ char diff
        assert classify_replace("a", "abc") == "hece_ekleme"  # 2+ char diff
        assert classify_replace("güzel", "güzellik") == "hece_ekleme"  # 2+ char diff
    
    def test_hece_eksiltme(self):
        """Test hece_eksiltme (≥2 harf eksiltme)"""
        assert classify_replace("testing", "test") == "hece_eksiltme"  # 2+ char diff
        assert classify_replace("abc", "a") == "hece_eksiltme"  # 2+ char diff
        assert classify_replace("güzellik", "güzel") == "hece_eksiltme"  # 2+ char diff
    
    def test_complex_cases(self):
        """Test complex substitution cases"""
        # Multiple character changes
        assert classify_replace("güzel", "çok") == "harf_değiştirme"  # Same length, multiple edits
        assert classify_replace("bir", "çok") == "harf_değiştirme"  # Same length, multiple edits
        
        # Length differences
        assert classify_replace("güzel", "güzellik") == "hece_ekleme"  # 4 char addition
        assert classify_replace("güzellik", "güzel") == "hece_eksiltme"  # 4 char deletion
    
    def test_edge_cases(self):
        """Test edge cases"""
        # Single character words
        assert classify_replace("a", "b") == "harf_değiştirme"
        assert classify_replace("a", "ab") == "harf_ekleme"
        assert classify_replace("ab", "a") == "harf_eksiltme"
        
        # Empty strings (should not happen in practice)
        assert classify_replace("", "a") == "hece_ekleme"
        assert classify_replace("a", "") == "hece_eksiltme"


class TestNormalizeSubTypeFunction:
    """Test normalize_sub_type function"""
    
    def test_hece_normalization(self):
        """Test hece subtype normalization"""
        assert normalize_sub_type("hece_ek") == "hece_ekleme"
        assert normalize_sub_type("hece_cik") == "hece_eksiltme"
    
    def test_harf_normalization(self):
        """Test harf subtype normalization"""
        assert normalize_sub_type("harf_ek") == "harf_ekleme"
        assert normalize_sub_type("harf_cik") == "harf_eksiltme"
    
    def test_degistirme_normalization(self):
        """Test degistirme normalization"""
        assert normalize_sub_type("degistirme") == "harf_değiştirme"
    
    def test_already_normalized(self):
        """Test already normalized types"""
        assert normalize_sub_type("hece_ekleme") == "hece_ekleme"
        assert normalize_sub_type("harf_ekleme") == "harf_ekleme"
        assert normalize_sub_type("harf_değiştirme") == "harf_değiştirme"
    
    def test_unknown_types(self):
        """Test unknown types"""
        assert normalize_sub_type("unknown_type") == "unknown_type"
        assert normalize_sub_type("") == ""
        assert normalize_sub_type(None) == None


class TestCharEditStatsFunction:
    """Test char_edit_stats function"""
    
    def test_identical_strings(self):
        """Test identical strings"""
        ed, len_diff = char_edit_stats("test", "test")
        assert ed == 0
        assert len_diff == 0
    
    def test_single_character_differences(self):
        """Test single character differences"""
        # One character addition
        ed, len_diff = char_edit_stats("test", "tests")
        assert ed == 1
        assert len_diff == -1
        
        # One character deletion
        ed, len_diff = char_edit_stats("tests", "test")
        assert ed == 1
        assert len_diff == 1
        
        # One character substitution
        ed, len_diff = char_edit_stats("test", "tast")
        assert ed == 1
        assert len_diff == 0
    
    def test_multiple_character_differences(self):
        """Test multiple character differences"""
        # Multiple character addition
        ed, len_diff = char_edit_stats("test", "testing")
        assert ed == 3  # "ing" added
        assert len_diff == -3
        
        # Multiple character deletion
        ed, len_diff = char_edit_stats("testing", "test")
        assert ed == 3  # "ing" removed
        assert len_diff == 3
        
        # Multiple character substitution
        ed, len_diff = char_edit_stats("test", "tost")
        assert ed == 1  # 'e' -> 'o'
        assert len_diff == 0
    
    def test_completely_different_strings(self):
        """Test completely different strings"""
        ed, len_diff = char_edit_stats("test", "word")
        assert ed == 4  # All characters different
        assert len_diff == 0
    
    def test_empty_strings(self):
        """Test empty strings"""
        ed, len_diff = char_edit_stats("", "")
        assert ed == 0
        assert len_diff == 0
        
        ed, len_diff = char_edit_stats("test", "")
        assert ed == 4
        assert len_diff == 4
        
        ed, len_diff = char_edit_stats("", "test")
        assert ed == 4
        assert len_diff == -4


class TestSyllablesTrFunction:
    """Test syllables_tr function"""
    
    def test_basic_syllable_counting(self):
        """Test basic syllable counting"""
        assert syllables_tr("test") == 1  # 1 vowel
        assert syllables_tr("güzel") == 2  # ü, e
        assert syllables_tr("çocuk") == 2  # o, u
        assert syllables_tr("öğrenci") == 3  # ö, e, i
        assert syllables_tr("Atatürk") == 3  # A, a, ü
    
    def test_single_vowels(self):
        """Test single vowel words"""
        assert syllables_tr("a") == 1
        assert syllables_tr("e") == 1
        assert syllables_tr("ı") == 1
        assert syllables_tr("i") == 1
        assert syllables_tr("o") == 1
        assert syllables_tr("ö") == 1
        assert syllables_tr("u") == 1
        assert syllables_tr("ü") == 1
    
    def test_no_vowels(self):
        """Test words with no vowels (should return 1)"""
        assert syllables_tr("bcdfg") == 1  # No vowels, minimum 1
        assert syllables_tr("") == 1  # Empty string, minimum 1
    
    def test_case_insensitive(self):
        """Test case insensitive counting"""
        assert syllables_tr("GÜZEL") == syllables_tr("güzel")
        assert syllables_tr("Atatürk") == syllables_tr("atatürk")
    
    def test_turkish_specific_cases(self):
        """Test Turkish-specific cases"""
        assert syllables_tr("çocuklar") == 3  # ç, o, u, a
        assert syllables_tr("öğretmen") == 3  # ö, e, e
        assert syllables_tr("şarkıcı") == 3  # ş, a, ı, ı
        assert syllables_tr("müzik") == 2  # ü, i


class TestIntegrationNormalization:
    """Integration tests for normalization functions"""
    
    def test_full_normalization_pipeline(self):
        """Test full normalization pipeline"""
        # Test with realistic Turkish text
        test_cases = [
            ("Güzel, bir gün!", "guzel, bir gun!"),
            ("Atatürk'ün", "ataturk'un"),
            ("çocuk--", "cocuk"),
            ("İhtiyaçlarımız.", "ihtiyaclarimiz."),
            ("Şarkı söylüyor.", "sarki soyluyor."),
        ]
        
        for input_text, expected_output in test_cases:
            result = _norm_token(input_text)
            assert result == expected_output, f"Failed for '{input_text}': got '{result}', expected '{expected_output}'"
    
    def test_classification_pipeline(self):
        """Test classification pipeline with normalized tokens"""
        # Test substitution classification with various cases
        test_cases = [
            ("güzel", "güzell", "harf_ekleme"),
            ("güzell", "güzel", "harf_eksiltme"),
            ("güzel", "güzel", "harf_değiştirme"),  # Same length, 0 edit distance
            ("güzel", "güzellik", "hece_ekleme"),
            ("güzellik", "güzel", "hece_eksiltme"),
        ]
        
        for ref, hyp, expected_subtype in test_cases:
            result = classify_replace(ref, hyp)
            assert result == expected_subtype, f"Failed for '{ref}' -> '{hyp}': got '{result}', expected '{expected_subtype}'"
    
    def test_normalization_consistency(self):
        """Test that normalization is consistent"""
        # Same input should always produce same output
        test_input = "Güzel, bir gün!"
        result1 = _norm_token(test_input)
        result2 = _norm_token(test_input)
        assert result1 == result2
        
        # Similar inputs should produce similar outputs
        input1 = "Güzel, bir gün!"
        input2 = "güzel, bir gün!"
        result1 = _norm_token(input1)
        result2 = _norm_token(input2)
        assert result1 == result2  # Should be same after normalization


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

