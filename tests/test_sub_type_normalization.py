"""
Test sub_type normalization and summary aggregation improvements
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app.services.alignment import (
    normalize_sub_type, build_word_events, levenshtein_align
)
from backend.app.services.scoring import recompute_counts, validate_summary_consistency


class TestSubTypeNormalization:
    """Test sub_type normalization functionality"""
    
    def test_normalize_sub_type(self):
        """Test sub_type normalization mapping"""
        # Test normalization mappings
        assert normalize_sub_type("hece_ek") == "hece_ekleme"
        assert normalize_sub_type("hece_cik") == "hece_eksiltme"
        assert normalize_sub_type("degistirme") == "harf_değiştirme"
        
        # Test unchanged values
        assert normalize_sub_type("harf_ek") == "harf_ek"
        assert normalize_sub_type("harf_cik") == "harf_cik"
        assert normalize_sub_type("unknown_type") == "unknown_type"
        
        # Test edge cases
        assert normalize_sub_type("") == ""
        assert normalize_sub_type(None) is None
    
    def test_build_word_events_with_normalized_sub_type(self):
        """Test that build_word_events normalizes sub_type"""
        # Create alignment with substitution
        ref_tokens = ["güzel", "bir", "gün"]
        hyp_tokens = ["güzel", "çok", "güzel", "gün"]
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        # Find substitution events
        substitution_events = [e for e in events if e["type"] == "substitution"]
        
        # Check that sub_type is normalized
        for event in substitution_events:
            if "sub_type" in event and event["sub_type"]:
                # Should be normalized (not the old format)
                assert event["sub_type"] not in ["hece_ek", "hece_cik", "degistirme"]
                # Should be in new format
                assert event["sub_type"] in ["hece_ekleme", "hece_eksiltme", "harf_değiştirme", "harf_ek", "harf_cik"]


class TestSummaryAggregation:
    """Test summary aggregation improvements"""
    
    def test_recompute_counts_with_substitution(self):
        """Test that recompute_counts correctly counts substitutions"""
        # Create mock word events
        word_events = [
            {"type": "correct"},
            {"type": "missing"},
            {"type": "extra"},
            {"type": "substitution"},
            {"type": "substitution"},
            {"type": "correct"}
        ]
        
        counts = recompute_counts(word_events)
        
        # Check counts
        assert counts["correct"] == 2
        assert counts["missing"] == 1
        assert counts["extra"] == 1
        assert counts["substitution"] == 2
        assert counts["total_words"] == 6
        
        # Check backward compatibility
        assert counts["diff"] == counts["substitution"]
    
    def test_validate_summary_consistency(self):
        """Test summary consistency validation"""
        # Create mock word events
        word_events = [
            {"type": "correct"},
            {"type": "missing"},
            {"type": "substitution"},
            {"type": "correct"}
        ]
        
        # Create consistent summary
        consistent_summary = {
            "counts": {
                "correct": 2,
                "missing": 1,
                "extra": 0,
                "substitution": 1,
                "total_words": 4
            },
            "error_types": {
                "missing": 1,
                "extra": 0,
                "substitution": 1,
                "pause_long": 0
            }
        }
        
        # Create inconsistent summary
        inconsistent_summary = {
            "counts": {
                "correct": 3,  # Wrong count
                "missing": 1,
                "extra": 0,
                "substitution": 1,
                "total_words": 4
            },
            "error_types": {
                "missing": 1,
                "extra": 0,
                "substitution": 1,
                "pause_long": 0
            }
        }
        
        # Test consistent summary
        assert validate_summary_consistency(consistent_summary, word_events) == True
        
        # Test inconsistent summary
        assert validate_summary_consistency(inconsistent_summary, word_events) == False
    
    def test_validate_summary_consistency_edge_cases(self):
        """Test validation with edge cases"""
        # Test with empty data
        assert validate_summary_consistency({}, []) == True
        assert validate_summary_consistency(None, []) == True
        assert validate_summary_consistency({}, None) == True
        
        # Test with missing fields - should be consistent when counts are 0
        word_events = [{"type": "correct"}]
        summary = {
            "counts": {"correct": 1, "missing": 0, "extra": 0, "substitution": 0},
            "error_types": {"missing": 0, "extra": 0, "substitution": 0}
        }
        assert validate_summary_consistency(summary, word_events) == True


class TestIntegration:
    """Integration tests for all improvements"""
    
    def test_complete_workflow(self):
        """Test complete workflow with normalization and validation"""
        # Create test data
        ref_tokens = ["bu", "güzel", "bir", "gün"]
        hyp_tokens = ["bu", "çok", "güzel", "gün"]
        
        # Perform alignment
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        # Check that events have normalized sub_type
        substitution_events = [e for e in events if e["type"] == "substitution"]
        for event in substitution_events:
            if event["sub_type"]:
                assert event["sub_type"] in ["hece_ekleme", "hece_eksiltme", "harf_değiştirme", "harf_ek", "harf_cik"]
        
        # Test recompute_counts
        counts = recompute_counts(events)
        assert "substitution" in counts
        assert counts["substitution"] >= 0
        
        # Test validation
        summary = {
            "counts": counts,
            "error_types": {
                "missing": counts["missing"],
                "extra": counts["extra"],
                "substitution": counts["substitution"],
                "pause_long": 0
            }
        }
        
        is_consistent = validate_summary_consistency(summary, events)
        assert is_consistent == True


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
