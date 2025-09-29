"""
UI Integration tests for alignment algorithms
Tests that can be run from UI to verify alignment functionality
"""
import pytest
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app.services.alignment import (
    levenshtein_align, build_word_events, tokenize_tr,
    _norm_token, classify_replace
)


class TestUIIntegration:
    """UI Integration tests for alignment algorithms"""
    
    def test_basic_alignment_ui_test(self):
        """Basic alignment test for UI"""
        ref_text = "Güzel bir gün var"
        hyp_text = "Güzel çok güzel gün merhaba"
        
        ref_tokens = tokenize_tr(ref_text)
        hyp_tokens = tokenize_tr(hyp_text)
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        # Count different event types
        event_counts = {}
        for event in events:
            event_type = event["type"]
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        # Expected results
        expected_results = {
            "correct": 2,  # "Güzel" and "gün" should be correct
            "substitution": 1,  # "bir" -> "çok"
            "extra": 1,  # "merhaba"
            "missing": 0,  # No missing tokens
            "repetition": 1  # "güzel" repetition
        }
        
        # Verify results
        for event_type, expected_count in expected_results.items():
            actual_count = event_counts.get(event_type, 0)
            assert actual_count == expected_count, f"Expected {expected_count} {event_type} events, got {actual_count}"
        
        return {
            "ref_text": ref_text,
            "hyp_text": hyp_text,
            "ref_tokens": ref_tokens,
            "hyp_tokens": hyp_tokens,
            "events": events,
            "event_counts": event_counts
        }
    
    def test_punctuation_handling_ui_test(self):
        """Test punctuation handling for UI"""
        ref_text = "Merhaba, dünya!"
        hyp_text = "Merhaba, dünya."
        
        ref_tokens = tokenize_tr(ref_text)
        hyp_tokens = tokenize_tr(hyp_text)
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        # Should be all correct due to punctuation normalization
        correct_events = [e for e in events if e["type"] == "correct"]
        assert len(correct_events) == 2  # "Merhaba" and "dünya"
        
        # Check that punctuation is preserved in tokens
        for event in correct_events:
            if event["hyp_token"]:
                assert "," in event["hyp_token"] or "." in event["hyp_token"]
        
        return {
            "ref_text": ref_text,
            "hyp_text": hyp_text,
            "events": events,
            "all_correct": len(correct_events) == len(events)
        }
    
    def test_turkish_character_normalization_ui_test(self):
        """Test Turkish character normalization for UI"""
        ref_text = "İhtiyaçlarımız çok önemli"
        hyp_text = "ihtiyaçlarımız çok önemli"
        
        ref_tokens = tokenize_tr(ref_text)
        hyp_tokens = tokenize_tr(hyp_text)
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        # Should be all correct due to normalization
        correct_events = [e for e in events if e["type"] == "correct"]
        assert len(correct_events) == 3  # All three words should be correct
        
        return {
            "ref_text": ref_text,
            "hyp_text": hyp_text,
            "events": events,
            "all_correct": len(correct_events) == len(events)
        }
    
    def test_substitution_subtypes_ui_test(self):
        """Test substitution subtypes for UI"""
        test_cases = [
            ("test", "tests", "harf_ekleme"),
            ("tests", "test", "harf_eksiltme"),
            ("test", "tast", "harf_değiştirme"),
            ("test", "testing", "hece_ekleme"),
            ("testing", "test", "hece_eksiltme"),
        ]
        
        results = []
        for ref, hyp, expected_subtype in test_cases:
            alignment = levenshtein_align([ref], [hyp])
            events = build_word_events(alignment, [])
            
            substitution_events = [e for e in events if e["type"] == "substitution"]
            assert len(substitution_events) == 1
            
            actual_subtype = substitution_events[0]["sub_type"]
            assert actual_subtype == expected_subtype
            
            results.append({
                "ref": ref,
                "hyp": hyp,
                "expected_subtype": expected_subtype,
                "actual_subtype": actual_subtype,
                "correct": actual_subtype == expected_subtype
            })
        
        return results
    
    def test_repetition_detection_ui_test(self):
        """Test repetition detection for UI"""
        test_cases = [
            {
                "name": "Dash pattern repetition",
                "ref_tokens": ["okul"],
                "hyp_tokens": ["okul--", "okul"],
                "expected_repetitions": 1
            },
            {
                "name": "Consecutive identical tokens",
                "ref_tokens": ["güzel", "gün"],
                "hyp_tokens": ["güzel", "güzel", "güzel", "gün"],
                "expected_repetitions": 2
            },
            {
                "name": "No repetition (different words)",
                "ref_tokens": [],
                "hyp_tokens": ["kelime--", "farklı"],
                "expected_repetitions": 0
            }
        ]
        
        results = []
        for test_case in test_cases:
            alignment = levenshtein_align(test_case["ref_tokens"], test_case["hyp_tokens"])
            events = build_word_events(alignment, [])
            
            repetition_events = [e for e in events if e["type"] == "repetition"]
            actual_repetitions = len(repetition_events)
            expected_repetitions = test_case["expected_repetitions"]
            
            assert actual_repetitions == expected_repetitions, f"Test '{test_case['name']}': expected {expected_repetitions} repetitions, got {actual_repetitions}"
            
            results.append({
                "name": test_case["name"],
                "ref_tokens": test_case["ref_tokens"],
                "hyp_tokens": test_case["hyp_tokens"],
                "expected_repetitions": expected_repetitions,
                "actual_repetitions": actual_repetitions,
                "correct": actual_repetitions == expected_repetitions,
                "repetition_tokens": [e["hyp_token"] for e in repetition_events]
            })
        
        return results
    
    def test_comprehensive_scenario_ui_test(self):
        """Comprehensive test scenario for UI"""
        ref_text = "Atatürk'ün güzel bir günü var"
        hyp_text = "Atatürk'ün çok güzel güzel günü merhaba"
        
        ref_tokens = tokenize_tr(ref_text)
        hyp_tokens = tokenize_tr(hyp_text)
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        # Analyze results
        event_analysis = {
            "total_events": len(events),
            "event_types": {},
            "substitution_details": [],
            "repetition_details": [],
            "correct_details": [],
            "extra_details": [],
            "missing_details": []
        }
        
        for event in events:
            event_type = event["type"]
            event_analysis["event_types"][event_type] = event_analysis["event_types"].get(event_type, 0) + 1
            
            if event_type == "substitution":
                event_analysis["substitution_details"].append({
                    "ref_token": event["ref_token"],
                    "hyp_token": event["hyp_token"],
                    "sub_type": event["sub_type"],
                    "char_diff": event["char_diff"],
                    "cer_local": event["cer_local"]
                })
            elif event_type == "repetition":
                event_analysis["repetition_details"].append({
                    "hyp_token": event["hyp_token"],
                    "sub_type": event["sub_type"]
                })
            elif event_type == "correct":
                event_analysis["correct_details"].append({
                    "ref_token": event["ref_token"],
                    "hyp_token": event["hyp_token"],
                    "sub_type": event["sub_type"]
                })
            elif event_type == "extra":
                event_analysis["extra_details"].append({
                    "hyp_token": event["hyp_token"]
                })
            elif event_type == "missing":
                event_analysis["missing_details"].append({
                    "ref_token": event["ref_token"]
                })
        
        # Verify expected results
        assert event_analysis["event_types"]["correct"] >= 2  # "Atatürk'ün" and "günü" should be correct
        assert event_analysis["event_types"]["substitution"] >= 1  # "bir" -> "çok"
        assert event_analysis["event_types"]["extra"] >= 1  # "merhaba"
        assert event_analysis["event_types"]["repetition"] >= 1  # "güzel" repetition
        
        return {
            "ref_text": ref_text,
            "hyp_text": hyp_text,
            "ref_tokens": ref_tokens,
            "hyp_tokens": hyp_tokens,
            "events": events,
            "event_analysis": event_analysis
        }
    
    def test_error_type_classification_ui_test(self):
        """Test error type classification for UI"""
        test_scenarios = [
            {
                "name": "All correct",
                "ref_tokens": ["güzel", "bir", "gün"],
                "hyp_tokens": ["güzel", "bir", "gün"],
                "expected": {"correct": 3, "substitution": 0, "extra": 0, "missing": 0, "repetition": 0}
            },
            {
                "name": "Substitution only",
                "ref_tokens": ["güzel", "bir", "gün"],
                "hyp_tokens": ["güzel", "çok", "gün"],
                "expected": {"correct": 2, "substitution": 1, "extra": 0, "missing": 0, "repetition": 0}
            },
            {
                "name": "Extra only",
                "ref_tokens": ["güzel", "gün"],
                "hyp_tokens": ["güzel", "çok", "gün"],
                "expected": {"correct": 2, "substitution": 0, "extra": 1, "missing": 0, "repetition": 0}
            },
            {
                "name": "Missing only",
                "ref_tokens": ["güzel", "bir", "gün"],
                "hyp_tokens": ["güzel", "gün"],
                "expected": {"correct": 2, "substitution": 0, "extra": 0, "missing": 1, "repetition": 0}
            },
            {
                "name": "Repetition only",
                "ref_tokens": ["güzel", "gün"],
                "hyp_tokens": ["güzel", "güzel", "gün"],
                "expected": {"correct": 2, "substitution": 0, "extra": 0, "missing": 0, "repetition": 1}
            }
        ]
        
        results = []
        for scenario in test_scenarios:
            alignment = levenshtein_align(scenario["ref_tokens"], scenario["hyp_tokens"])
            events = build_word_events(alignment, [])
            
            # Count event types
            actual_counts = {}
            for event in events:
                event_type = event["type"]
                actual_counts[event_type] = actual_counts.get(event_type, 0) + 1
            
            # Verify results
            correct = True
            for event_type, expected_count in scenario["expected"].items():
                actual_count = actual_counts.get(event_type, 0)
                if actual_count != expected_count:
                    correct = False
                    break
            
            results.append({
                "name": scenario["name"],
                "ref_tokens": scenario["ref_tokens"],
                "hyp_tokens": scenario["hyp_tokens"],
                "expected": scenario["expected"],
                "actual": actual_counts,
                "correct": correct,
                "events": events
            })
        
        return results


class TestUIPerformance:
    """UI Performance tests"""
    
    def test_large_text_alignment(self):
        """Test alignment with large text"""
        # Create large text
        ref_text = " ".join(["güzel", "bir", "gün"] * 50)  # 150 words
        hyp_text = " ".join(["güzel", "çok", "güzel", "bir", "gün"] * 30)  # 150 words
        
        ref_tokens = tokenize_tr(ref_text)
        hyp_tokens = tokenize_tr(hyp_text)
        
        # Measure alignment time
        import time
        start_time = time.time()
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        end_time = time.time()
        
        alignment_time = end_time - start_time
        
        # Should complete in reasonable time (< 5 seconds)
        assert alignment_time < 5.0, f"Alignment took too long: {alignment_time:.2f} seconds"
        
        return {
            "ref_token_count": len(ref_tokens),
            "hyp_token_count": len(hyp_tokens),
            "event_count": len(events),
            "alignment_time": alignment_time,
            "tokens_per_second": len(ref_tokens) / alignment_time if alignment_time > 0 else 0
        }
    
    def test_memory_usage(self):
        """Test memory usage with large alignments"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create large alignment
        ref_tokens = ["güzel", "bir", "gün"] * 100  # 300 words
        hyp_tokens = ["güzel", "çok", "güzel", "bir", "gün"] * 60  # 300 words
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_usage = final_memory - initial_memory
        
        # Should not use excessive memory (< 100 MB)
        assert memory_usage < 100, f"Memory usage too high: {memory_usage:.2f} MB"
        
        return {
            "initial_memory_mb": initial_memory,
            "final_memory_mb": final_memory,
            "memory_usage_mb": memory_usage,
            "ref_token_count": len(ref_tokens),
            "hyp_token_count": len(hyp_tokens),
            "event_count": len(events)
        }


def run_ui_tests():
    """Run all UI tests and return results"""
    test_instance = TestUIIntegration()
    
    results = {
        "basic_alignment": test_instance.test_basic_alignment_ui_test(),
        "punctuation_handling": test_instance.test_punctuation_handling_ui_test(),
        "turkish_normalization": test_instance.test_turkish_character_normalization_ui_test(),
        "substitution_subtypes": test_instance.test_substitution_subtypes_ui_test(),
        "repetition_detection": test_instance.test_repetition_detection_ui_test(),
        "comprehensive_scenario": test_instance.test_comprehensive_scenario_ui_test(),
        "error_type_classification": test_instance.test_error_type_classification_ui_test()
    }
    
    # Count total tests passed
    total_tests = 0
    passed_tests = 0
    
    for test_name, test_result in results.items():
        if isinstance(test_result, list):
            for item in test_result:
                total_tests += 1
                if item.get("correct", True):
                    passed_tests += 1
        else:
            total_tests += 1
            if test_result.get("all_correct", True):
                passed_tests += 1
    
    results["summary"] = {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
    }
    
    return results


if __name__ == "__main__":
    # Run UI tests
    results = run_ui_tests()
    
    print("UI Test Results:")
    print("=" * 50)
    print(f"Total Tests: {results['summary']['total_tests']}")
    print(f"Passed Tests: {results['summary']['passed_tests']}")
    print(f"Success Rate: {results['summary']['success_rate']:.1f}%")
    print("=" * 50)
    
    # Save results to file
    with open("ui_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("Results saved to ui_test_results.json")

