#!/usr/bin/env python3
"""
Test STT Passthrough - Ensure raw words are preserved without merging

This test verifies that ElevenLabs STT words are passed through directly
without any word merging or combining.
"""

import unittest
from unittest.mock import Mock
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from worker.services.elevenlabs_stt import ElevenLabsSTT


class TestSTTPassthrough(unittest.TestCase):
    """Test STT word passthrough functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.stt_client = ElevenLabsSTT(
            api_key="test_key",
            model="scribe_v1",
            language="tr"
        )
    
    def test_raw_words_passthrough(self):
        """Test that raw words are passed through without merging"""
        # Mock ElevenLabs response with spacing tokens
        mock_words_data = [
            {"text": "Atatürk", "start": 1.0, "end": 1.5, "type": "word", "logprob": -0.1},
            {"text": " ", "start": 1.5, "end": 1.6, "type": "spacing", "logprob": -0.05},
            {"text": "bir", "start": 1.6, "end": 1.8, "type": "word", "logprob": -0.2},
            {"text": " ", "start": 1.8, "end": 1.9, "type": "spacing", "logprob": -0.05},
            {"text": "öğretmendi", "start": 1.9, "end": 2.3, "type": "word", "logprob": -0.15},
        ]
        
        # Extract raw words
        raw_words = self.stt_client.extract_raw_words(mock_words_data)
        
        # Verify only word types are extracted
        self.assertEqual(len(raw_words), 3)
        
        # Verify words are preserved exactly
        self.assertEqual(raw_words[0]["word"], "Atatürk")
        self.assertEqual(raw_words[0]["start"], 1.0)
        self.assertEqual(raw_words[0]["end"], 1.5)
        self.assertEqual(raw_words[0]["confidence"], -0.1)
        
        self.assertEqual(raw_words[1]["word"], "bir")
        self.assertEqual(raw_words[1]["start"], 1.6)
        self.assertEqual(raw_words[1]["end"], 1.8)
        self.assertEqual(raw_words[1]["confidence"], -0.2)
        
        self.assertEqual(raw_words[2]["word"], "öğretmendi")
        self.assertEqual(raw_words[2]["start"], 1.9)
        self.assertEqual(raw_words[2]["end"], 2.3)
        self.assertEqual(raw_words[2]["confidence"], -0.15)
    
    def test_punctuation_preservation(self):
        """Test that punctuation in words is preserved"""
        mock_words_data = [
            {"text": "Öğretmen,", "start": 1.0, "end": 1.4, "type": "word", "logprob": -0.1},
            {"text": " ", "start": 1.4, "end": 1.5, "type": "spacing", "logprob": -0.05},
            {"text": "dedi.", "start": 1.5, "end": 1.8, "type": "word", "logprob": -0.2},
        ]
        
        raw_words = self.stt_client.extract_raw_words(mock_words_data)
        
        # Verify punctuation is preserved
        self.assertEqual(len(raw_words), 2)
        self.assertEqual(raw_words[0]["word"], "Öğretmen,")
        self.assertEqual(raw_words[1]["word"], "dedi.")
    
    def test_empty_words_ignored(self):
        """Test that empty words are ignored"""
        mock_words_data = [
            {"text": "Atatürk", "start": 1.0, "end": 1.5, "type": "word", "logprob": -0.1},
            {"text": "", "start": 1.5, "end": 1.6, "type": "word", "logprob": -0.05},
            {"text": "bir", "start": 1.6, "end": 1.8, "type": "word", "logprob": -0.2},
            {"text": "   ", "start": 1.8, "end": 1.9, "type": "word", "logprob": -0.05},
        ]
        
        raw_words = self.stt_client.extract_raw_words(mock_words_data)
        
        # Only non-empty words should be included
        self.assertEqual(len(raw_words), 2)
        self.assertEqual(raw_words[0]["word"], "Atatürk")
        self.assertEqual(raw_words[1]["word"], "bir")
    
    def test_spacing_completely_ignored(self):
        """Test that spacing tokens are completely ignored"""
        mock_words_data = [
            {"text": "Atatürk", "start": 1.0, "end": 1.5, "type": "word", "logprob": -0.1},
            {"text": "   ", "start": 1.5, "end": 1.6, "type": "spacing", "logprob": -0.05},
            {"text": "\n", "start": 1.6, "end": 1.7, "type": "spacing", "logprob": -0.05},
            {"text": "\t", "start": 1.7, "end": 1.8, "type": "spacing", "logprob": -0.05},
            {"text": "bir", "start": 1.8, "end": 2.0, "type": "word", "logprob": -0.2},
        ]
        
        raw_words = self.stt_client.extract_raw_words(mock_words_data)
        
        # Only word types should be included
        self.assertEqual(len(raw_words), 2)
        self.assertEqual(raw_words[0]["word"], "Atatürk")
        self.assertEqual(raw_words[1]["word"], "bir")
    
    def test_no_word_merging(self):
        """Test that words are never merged together"""
        # This is a critical test - words should NEVER be merged
        mock_words_data = [
            {"text": "Bu", "start": 1.0, "end": 1.1, "type": "word", "logprob": -0.1},
            {"text": " ", "start": 1.1, "end": 1.2, "type": "spacing", "logprob": -0.05},
            {"text": "güzel", "start": 1.2, "end": 1.5, "type": "word", "logprob": -0.2},
            {"text": " ", "start": 1.5, "end": 1.6, "type": "spacing", "logprob": -0.05},
            {"text": "bir", "start": 1.6, "end": 1.7, "type": "word", "logprob": -0.3},
        ]
        
        raw_words = self.stt_client.extract_raw_words(mock_words_data)
        
        # Verify words remain separate
        self.assertEqual(len(raw_words), 3)
        self.assertEqual(raw_words[0]["word"], "Bu")
        self.assertEqual(raw_words[1]["word"], "güzel")
        self.assertEqual(raw_words[2]["word"], "bir")
        
        # Verify no combined words exist
        combined_words = [w["word"] for w in raw_words if len(w["word"]) > 10]
        self.assertEqual(len(combined_words), 0, "No combined words should exist")


if __name__ == "__main__":
    unittest.main()
