#!/usr/bin/env python3
"""
Test Alignment No Merge - Ensure alignment doesn't merge words

This test verifies that alignment process preserves individual words
and doesn't create merged tokens.
"""

import unittest
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from worker.services import alignment


class TestAlignmentNoMerge(unittest.TestCase):
    """Test alignment functionality without word merging"""
    
    def test_alignment_preserves_individual_words(self):
        """Test that alignment preserves individual words"""
        # Reference tokens (canonical) - no punctuation after tokenization
        ref_tokens = ["öğretmen", "atatürk", "bir", "yurt", "severdi"]
        
        # Hypothesis tokens (from STT - no punctuation after tokenization)
        hyp_tokens = ["Öğretmen", "Atatürk", "bir", "yurt", "severdi"]
        
        # Perform alignment
        alignment_result = alignment.levenshtein_align(ref_tokens, hyp_tokens)
        
        # Verify alignment result
        self.assertEqual(len(alignment_result), 5)
        
        # Check each alignment operation
        expected_operations = [
            ("equal", "öğretmen", "Öğretmen", 0, 0),     # case difference - now equal due to normalization
            ("equal", "atatürk", "Atatürk", 1, 1),       # case difference - now equal due to normalization
            ("equal", "bir", "bir", 2, 2),               # exact match
            ("equal", "yurt", "yurt", 3, 3),             # exact match
            ("equal", "severdi", "severdi", 4, 4),       # exact match
        ]
        
        for i, (op, ref, hyp, ref_idx, hyp_idx) in enumerate(expected_operations):
            actual_op, actual_ref, actual_hyp, actual_ref_idx, actual_hyp_idx = alignment_result[i]
            self.assertEqual(actual_op, op)
            self.assertEqual(actual_ref, ref)
            self.assertEqual(actual_hyp, hyp)
            self.assertEqual(actual_ref_idx, ref_idx)
            self.assertEqual(actual_hyp_idx, hyp_idx)
    
    def test_alignment_with_missing_words(self):
        """Test alignment with missing words"""
        ref_tokens = ["bu", "güzel", "bir", "metin"]
        hyp_tokens = ["bu", "metin"]  # Missing "güzel" and "bir"
        
        alignment_result = alignment.levenshtein_align(ref_tokens, hyp_tokens)
        
        # Verify alignment result
        self.assertEqual(len(alignment_result), 4)
        
        expected_operations = [
            ("equal", "bu", "bu", 0, 0),
            ("delete", "güzel", "", 1, -1),
            ("delete", "bir", "", 2, -1),
            ("equal", "metin", "metin", 3, 1),  # now equal due to normalization
        ]
        
        for i, (op, ref, hyp, ref_idx, hyp_idx) in enumerate(expected_operations):
            actual_op, actual_ref, actual_hyp, actual_ref_idx, actual_hyp_idx = alignment_result[i]
            self.assertEqual(actual_op, op)
            self.assertEqual(actual_ref, ref)
            self.assertEqual(actual_hyp, hyp)
            self.assertEqual(actual_ref_idx, ref_idx)
            self.assertEqual(actual_hyp_idx, hyp_idx)
    
    def test_alignment_with_extra_words(self):
        """Test alignment with extra words"""
        ref_tokens = ["bu", "metin"]
        hyp_tokens = ["bu", "çok", "güzel", "metin"]  # Extra "çok" and "güzel"
        
        alignment_result = alignment.levenshtein_align(ref_tokens, hyp_tokens)
        
        # Verify alignment result
        self.assertEqual(len(alignment_result), 4)
        
        expected_operations = [
            ("equal", "bu", "bu", 0, 0),
            ("insert", "", "çok", -1, 1),
            ("insert", "", "güzel", -1, 2),
            ("equal", "metin", "metin", 1, 3),  # now equal due to normalization
        ]
        
        for i, (op, ref, hyp, ref_idx, hyp_idx) in enumerate(expected_operations):
            actual_op, actual_ref, actual_hyp, actual_ref_idx, actual_hyp_idx = alignment_result[i]
            self.assertEqual(actual_op, op)
            self.assertEqual(actual_ref, ref)
            self.assertEqual(actual_hyp, hyp)
            self.assertEqual(actual_ref_idx, ref_idx)
            self.assertEqual(actual_hyp_idx, hyp_idx)
    
    def test_word_events_no_merging(self):
        """Test that word events don't merge words"""
        # Mock word timing data
        word_times = [
            {"word": "Bu", "start": 1.0, "end": 1.1},
            {"word": "güzel", "start": 1.2, "end": 1.5},
            {"word": "bir", "start": 1.6, "end": 1.7},
            {"word": "metin", "start": 1.8, "end": 2.0},
        ]
        
        # Alignment result
        alignment_result = [
            ("equal", "bu", "Bu", 0, 0),
            ("equal", "güzel", "güzel", 1, 1),
            ("equal", "bir", "bir", 2, 2),
            ("equal", "metin", "metin", 3, 3),
        ]
        
        # Build word events
        word_events = alignment.build_word_events(alignment_result, word_times)
        
        # Verify word events
        self.assertEqual(len(word_events), 4)
        
        # Check that each word event has individual words
        for i, event in enumerate(word_events):
            self.assertEqual(event["type"], "correct")
            self.assertIsNotNone(event["hyp_token"])
            self.assertIsNotNone(event["ref_token"])
            
            # Verify timing data
            self.assertIsNotNone(event["start_ms"])
            self.assertIsNotNone(event["end_ms"])
            
            # Verify no merged words
            self.assertLess(len(event["hyp_token"]), 20, "No merged words should exist")
            self.assertLess(len(event["ref_token"]), 20, "No merged words should exist")
        
        # Verify specific words
        self.assertEqual(word_events[0]["hyp_token"], "Bu")
        self.assertEqual(word_events[0]["ref_token"], "bu")
        self.assertEqual(word_events[0]["start_ms"], 1000)  # 1.0 * 1000
        self.assertEqual(word_events[0]["end_ms"], 1100)    # 1.1 * 1000
        
        self.assertEqual(word_events[1]["hyp_token"], "güzel")
        self.assertEqual(word_events[1]["ref_token"], "güzel")
        self.assertEqual(word_events[1]["start_ms"], 1200)  # 1.2 * 1000
        self.assertEqual(word_events[1]["end_ms"], 1500)    # 1.5 * 1000
        
        self.assertEqual(word_events[2]["hyp_token"], "bir")
        self.assertEqual(word_events[2]["ref_token"], "bir")
        self.assertEqual(word_events[2]["start_ms"], 1600)  # 1.6 * 1000
        self.assertEqual(word_events[2]["end_ms"], 1700)    # 1.7 * 1000
        
        self.assertEqual(word_events[3]["hyp_token"], "metin")
        self.assertEqual(word_events[3]["ref_token"], "metin")
        self.assertEqual(word_events[3]["start_ms"], 1800)  # 1.8 * 1000
        self.assertEqual(word_events[3]["end_ms"], 2000)    # 2.0 * 1000
    
    def test_no_combined_words_in_events(self):
        """Test that word events never contain combined words"""
        # This is a critical test - word events should NEVER contain combined words
        word_times = [
            {"word": "Atatürk", "start": 1.0, "end": 1.5},
            {"word": "bir", "start": 1.6, "end": 1.8},
            {"word": "öğretmendi", "start": 1.9, "end": 2.3},
        ]
        
        alignment_result = [
            ("equal", "atatürk", "Atatürk", 0, 0),
            ("equal", "bir", "bir", 1, 1),
            ("equal", "öğretmendi", "öğretmendi", 2, 2),
        ]
        
        word_events = alignment.build_word_events(alignment_result, word_times)
        
        # Verify no combined words exist
        for event in word_events:
            hyp_token = event["hyp_token"]
            ref_token = event["ref_token"]
            
            # Check for suspiciously long words that might be combined
            self.assertLess(len(hyp_token), 15, f"Hypothesis token '{hyp_token}' is too long, might be combined")
            self.assertLess(len(ref_token), 15, f"Reference token '{ref_token}' is too long, might be combined")
            
            # Check for specific combined patterns
            self.assertNotIn("atatürkbir", hyp_token.lower(), "Words should not be combined")
            self.assertNotIn("biröğretmendi", hyp_token.lower(), "Words should not be combined")
            self.assertNotIn("atatürkbiröğretmendi", hyp_token.lower(), "Words should not be combined")
    
    def test_turkish_apostrophe_preservation(self):
        """Test that Turkish apostrophes are preserved correctly"""
        # Test tokenization with apostrophes
        text_with_apostrophes = "Atatürk'ün Türkiye'nin okulları öğrencileri"
        tokens = alignment.tokenize_tr(text_with_apostrophes)
        
        # Verify apostrophes are preserved in tokens
        expected_tokens = ["Atatürk'ün", "Türkiye'nin", "okulları", "öğrencileri"]
        self.assertEqual(tokens, expected_tokens)
        
        # Test that apostrophes don't split words
        self.assertEqual(tokens[0], "Atatürk'ün")
        self.assertEqual(tokens[1], "Türkiye'nin")
        
        # Test alignment with apostrophe tokens
        ref_tokens = ["Atatürk'ün", "Türkiye'nin", "okulları", "öğrencileri"]
        hyp_tokens = ["Atatürk'ün", "Türkiye'nin", "okulları", "öğrencileri"]
        
        # Perform alignment
        alignment_result = alignment.levenshtein_align(ref_tokens, hyp_tokens)
        
        # Verify alignment result
        self.assertEqual(len(alignment_result), 4)
        
        # Check each alignment operation - should all be equal
        for i, (op, ref, hyp, ref_idx, hyp_idx) in enumerate(alignment_result):
            self.assertEqual(op, "equal")
            self.assertEqual(ref, ref_tokens[i])
            self.assertEqual(hyp, hyp_tokens[i])
            self.assertEqual(ref_idx, i)
            self.assertEqual(hyp_idx, i)
    
    def test_turkish_punctuation_removal(self):
        """Test that Turkish punctuation is removed from tokens"""
        # Test tokenization with punctuation
        text_with_punctuation = "Okulları, öğrencileri güzel bir gün."
        tokens = alignment.tokenize_tr(text_with_punctuation)
        
        # Verify punctuation is removed from tokens
        expected_tokens = ["Okulları", "öğrencileri", "güzel", "bir", "gün"]
        self.assertEqual(tokens, expected_tokens)
        
        # Test that punctuation doesn't appear as separate tokens
        self.assertNotIn(",", tokens)
        self.assertNotIn(".", tokens)
        
        # Test alignment with punctuation-removed tokens
        ref_tokens = ["Okulları", "öğrencileri", "güzel", "bir", "gün"]
        hyp_tokens = ["Okulları", "öğrencileri", "Güzel", "bir", "gün"]
        
        # Perform alignment
        alignment_result = alignment.levenshtein_align(ref_tokens, hyp_tokens)
        
        # Verify alignment result
        self.assertEqual(len(alignment_result), 5)
        
        # Check specific cases
        expected_operations = [
            ("equal", "Okulları", "Okulları", 0, 0),  # exact match
            ("equal", "öğrencileri", "öğrencileri", 1, 1),  # exact match
            ("equal", "güzel", "Güzel", 2, 2),  # case difference but normalized equal
            ("equal", "bir", "bir", 3, 3),  # exact match
            ("equal", "gün", "gün", 4, 4),  # exact match
        ]
        
        for i, (op, ref, hyp, ref_idx, hyp_idx) in enumerate(expected_operations):
            actual_op, actual_ref, actual_hyp, actual_ref_idx, actual_hyp_idx = alignment_result[i]
            self.assertEqual(actual_op, op)
            self.assertEqual(actual_ref, ref)
            self.assertEqual(actual_hyp, hyp)
            self.assertEqual(actual_ref_idx, ref_idx)
            self.assertEqual(actual_hyp_idx, hyp_idx)
    
    def test_turkish_uppercase_preservation(self):
        """Test that Turkish uppercase characters are preserved in original tokens"""
        # Reference tokens with uppercase
        ref_tokens = ["ÖĞRETMEN", "Atatürk'ün", "Türkiye'nin"]
        
        # Hypothesis tokens with different casing
        hyp_tokens = ["öğretmen", "atatürk'ün", "türkiye'nin"]
        
        # Perform alignment
        alignment_result = alignment.levenshtein_align(ref_tokens, hyp_tokens)
        
        # Verify alignment result
        self.assertEqual(len(alignment_result), 3)
        
        # Check that original casing is preserved in alignment result
        for i, (op, ref, hyp, ref_idx, hyp_idx) in enumerate(alignment_result):
            self.assertEqual(op, "equal")  # Should match due to normalization
            self.assertEqual(ref, ref_tokens[i])  # Original casing preserved
            self.assertEqual(hyp, hyp_tokens[i])  # Original casing preserved
            self.assertEqual(ref_idx, i)
            self.assertEqual(hyp_idx, i)
    
    def test_tokenization_requirements(self):
        """Test specific tokenization requirements from user query"""
        # Test 1: Apostrophes must be preserved inside tokens
        text1 = "Atatürk'ün"
        tokens1 = alignment.tokenize_tr(text1)
        self.assertEqual(tokens1, ["Atatürk'ün"])
        
        # Test 2: Multiple words with apostrophes
        text2 = "Türkiye'nin eğitimi"
        tokens2 = alignment.tokenize_tr(text2)
        self.assertEqual(tokens2, ["Türkiye'nin", "eğitimi"])
        
        # Test 3: Punctuation must be removed
        text3 = "Okulu, öğrencileri ve öğretmenleri."
        tokens3 = alignment.tokenize_tr(text3)
        self.assertEqual(tokens3, ["Okulu", "öğrencileri", "ve", "öğretmenleri"])
        
        # Test 4: Complex text with quotes and punctuation
        text4 = 'Atatürk: "Öğretmen" dedi.'
        tokens4 = alignment.tokenize_tr(text4)
        self.assertEqual(tokens4, ["Atatürk", "Öğretmen", "dedi"])
        
        # Test 5: Apostrophes must NOT split tokens
        text5 = "Ali'ye"
        tokens5 = alignment.tokenize_tr(text5)
        self.assertEqual(tokens5, ["Ali'ye"])
        # Verify it's not split
        self.assertNotIn("Ali", tokens5)
        self.assertNotIn("ye", tokens5)
        
        # Test 6: Preserve original casing and diacritics
        text6 = "Atatürk'ün Türkiye'nin"
        tokens6 = alignment.tokenize_tr(text6)
        self.assertEqual(tokens6, ["Atatürk'ün", "Türkiye'nin"])
        # Verify casing is preserved
        self.assertTrue(tokens6[0].startswith("A"))  # Capital A
        self.assertTrue(tokens6[1].startswith("T"))  # Capital T


if __name__ == "__main__":
    unittest.main()
