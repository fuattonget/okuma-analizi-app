#!/usr/bin/env python3
"""
Quick Alignment Test for UI
Simple test script that can be run from UI to verify alignment functionality
"""
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_basic_alignment():
    """Test basic alignment functionality"""
    try:
        from backend.app.services.alignment import (
            levenshtein_align, build_word_events, tokenize_tr,
            _norm_token, classify_replace
        )
        
        # Test case 1: Basic alignment
        ref_text = "Güzel bir gün var"
        hyp_text = "Güzel çok güzel gün merhaba"
        
        ref_tokens = tokenize_tr(ref_text)
        hyp_tokens = tokenize_tr(hyp_text)
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        # Count event types
        event_counts = {}
        for event in events:
            event_type = event["type"]
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        return {
            "success": True,
            "test_name": "Basic Alignment",
            "ref_text": ref_text,
            "hyp_text": hyp_text,
            "ref_tokens": ref_tokens,
            "hyp_tokens": hyp_tokens,
            "event_counts": event_counts,
            "events": events
        }
        
    except Exception as e:
        return {
            "success": False,
            "test_name": "Basic Alignment",
            "error": str(e)
        }

def test_punctuation_handling():
    """Test punctuation handling"""
    try:
        from backend.app.services.alignment import levenshtein_align, build_word_events, tokenize_tr
        
        ref_text = "Merhaba, dünya!"
        hyp_text = "Merhaba, dünya."
        
        ref_tokens = tokenize_tr(ref_text)
        hyp_tokens = tokenize_tr(hyp_text)
        
        alignment = levenshtein_align(ref_tokens, hyp_tokens)
        events = build_word_events(alignment, [])
        
        # Should be all correct due to punctuation normalization
        correct_events = [e for e in events if e["type"] == "correct"]
        all_correct = len(correct_events) == len(events)
        
        return {
            "success": True,
            "test_name": "Punctuation Handling",
            "ref_text": ref_text,
            "hyp_text": hyp_text,
            "all_correct": all_correct,
            "correct_count": len(correct_events),
            "total_count": len(events)
        }
        
    except Exception as e:
        return {
            "success": False,
            "test_name": "Punctuation Handling",
            "error": str(e)
        }

def test_turkish_normalization():
    """Test Turkish character normalization"""
    try:
        from backend.app.services.alignment import _norm_token
        
        test_cases = [
            ("İhtiyaçlarımız", "ihtiyaclarimiz"),
            ("Güzel", "guzel"),
            ("çocuk", "cocuk"),
            ("öğrenci", "ogrenci"),
            ("şarkı", "sarki"),
            ("Atatürk'ün", "ataturk'un")
        ]
        
        results = []
        all_passed = True
        
        for input_text, expected_output in test_cases:
            actual_output = _norm_token(input_text)
            passed = actual_output == expected_output
            all_passed = all_passed and passed
            
            results.append({
                "input": input_text,
                "expected": expected_output,
                "actual": actual_output,
                "passed": passed
            })
        
        return {
            "success": True,
            "test_name": "Turkish Normalization",
            "all_passed": all_passed,
            "results": results
        }
        
    except Exception as e:
        return {
            "success": False,
            "test_name": "Turkish Normalization",
            "error": str(e)
        }

def test_substitution_subtypes():
    """Test substitution subtypes"""
    try:
        from backend.app.services.alignment import classify_replace
        
        test_cases = [
            ("test", "tests", "harf_ekleme"),
            ("tests", "test", "harf_eksiltme"),
            ("test", "tast", "harf_değiştirme"),
            ("test", "testing", "hece_ekleme"),
            ("testing", "test", "hece_eksiltme")
        ]
        
        results = []
        all_passed = True
        
        for ref, hyp, expected_subtype in test_cases:
            actual_subtype = classify_replace(ref, hyp)
            passed = actual_subtype == expected_subtype
            all_passed = all_passed and passed
            
            results.append({
                "ref": ref,
                "hyp": hyp,
                "expected": expected_subtype,
                "actual": actual_subtype,
                "passed": passed
            })
        
        return {
            "success": True,
            "test_name": "Substitution Subtypes",
            "all_passed": all_passed,
            "results": results
        }
        
    except Exception as e:
        return {
            "success": False,
            "test_name": "Substitution Subtypes",
            "error": str(e)
        }

def test_repetition_detection():
    """Test repetition detection"""
    try:
        from backend.app.services.alignment import levenshtein_align, build_word_events
        
        test_cases = [
            {
                "name": "Dash pattern",
                "ref_tokens": ["okul"],
                "hyp_tokens": ["okul--", "okul"],
                "expected_repetitions": 1
            },
            {
                "name": "Consecutive identical",
                "ref_tokens": ["güzel", "gün"],
                "hyp_tokens": ["güzel", "güzel", "güzel", "gün"],
                "expected_repetitions": 2
            },
            {
                "name": "No repetition",
                "ref_tokens": [],
                "hyp_tokens": ["kelime--", "farklı"],
                "expected_repetitions": 0
            }
        ]
        
        results = []
        all_passed = True
        
        for test_case in test_cases:
            alignment = levenshtein_align(test_case["ref_tokens"], test_case["hyp_tokens"])
            events = build_word_events(alignment, [])
            
            repetition_events = [e for e in events if e["type"] == "repetition"]
            actual_repetitions = len(repetition_events)
            expected_repetitions = test_case["expected_repetitions"]
            
            passed = actual_repetitions == expected_repetitions
            all_passed = all_passed and passed
            
            results.append({
                "name": test_case["name"],
                "expected": expected_repetitions,
                "actual": actual_repetitions,
                "passed": passed,
                "repetition_tokens": [e["hyp_token"] for e in repetition_events]
            })
        
        return {
            "success": True,
            "test_name": "Repetition Detection",
            "all_passed": all_passed,
            "results": results
        }
        
    except Exception as e:
        return {
            "success": False,
            "test_name": "Repetition Detection",
            "error": str(e)
        }

def run_all_tests():
    """Run all quick tests"""
    tests = [
        test_basic_alignment,
        test_punctuation_handling,
        test_turkish_normalization,
        test_substitution_subtypes,
        test_repetition_detection
    ]
    
    results = {
        "timestamp": str(Path(__file__).stat().st_mtime),
        "tests": [],
        "summary": {
            "total": 0,
            "passed": 0,
            "failed": 0
        }
    }
    
    for test_func in tests:
        result = test_func()
        results["tests"].append(result)
        results["summary"]["total"] += 1
        
        if result["success"] and result.get("all_passed", True):
            results["summary"]["passed"] += 1
        else:
            results["summary"]["failed"] += 1
    
    results["summary"]["success_rate"] = (results["summary"]["passed"] / results["summary"]["total"] * 100) if results["summary"]["total"] > 0 else 0
    
    return results

def main():
    """Main function"""
    print("Quick Alignment Test")
    print("=" * 50)
    
    results = run_all_tests()
    
    # Print results
    for test in results["tests"]:
        status = "✅ PASS" if (test["success"] and test.get("all_passed", True)) else "❌ FAIL"
        print(f"{status} {test['test_name']}")
        
        if not test["success"]:
            print(f"   Error: {test['error']}")
        elif not test.get("all_passed", True):
            print(f"   Some assertions failed")
    
    print("\n" + "=" * 50)
    print(f"Summary: {results['summary']['passed']}/{results['summary']['total']} tests passed")
    print(f"Success Rate: {results['summary']['success_rate']:.1f}%")
    
    # Save results
    with open("quick_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("Results saved to quick_test_results.json")
    
    return results["summary"]["failed"] == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

