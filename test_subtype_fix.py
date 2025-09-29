#!/usr/bin/env python3
"""
Test sub_type fix for substitution events
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.app.services.alignment import (
    levenshtein_align, build_word_events, tokenize_tr
)

def test_subtype_fix():
    """Test that sub_type is properly calculated for substitution events"""
    
    # Test case from the user's analysis
    ref_tokens = ["üzerindeki"]
    hyp_tokens = ["üzerinde"]
    
    alignment = levenshtein_align(ref_tokens, hyp_tokens)
    events = build_word_events(alignment, [])
    
    print("Test Case: 'üzerindeki' -> 'üzerinde'")
    print("=" * 50)
    
    for event in events:
        print(f"Type: {event['type']}")
        print(f"Ref Token: '{event['ref_token']}'")
        print(f"Hyp Token: '{event['hyp_token']}'")
        print(f"Sub Type: {event['sub_type']}")
        print(f"Char Diff: {event.get('char_diff', 'N/A')}")
        print(f"CER Local: {event.get('cer_local', 'N/A')}")
        print("-" * 30)
    
    # Check if sub_type is properly calculated
    substitution_events = [e for e in events if e["type"] == "substitution"]
    
    if substitution_events:
        sub_event = substitution_events[0]
        if sub_event["sub_type"] is not None:
            print("✅ SUCCESS: sub_type is properly calculated!")
            print(f"   Sub Type: {sub_event['sub_type']}")
            return True
        else:
            print("❌ FAILED: sub_type is still null")
            return False
    else:
        print("❌ FAILED: No substitution events found")
        return False

def test_multiple_substitutions():
    """Test multiple substitution types"""
    
    test_cases = [
        ("test", "tests", "harf_ekleme"),
        ("tests", "test", "harf_eksiltme"),
        ("test", "tast", "harf_değiştirme"),
        ("test", "testing", "hece_ekleme"),
        ("testing", "test", "hece_eksiltme")
    ]
    
    print("\nMultiple Substitution Types Test")
    print("=" * 50)
    
    all_passed = True
    
    for ref, hyp, expected_subtype in test_cases:
        alignment = levenshtein_align([ref], [hyp])
        events = build_word_events(alignment, [])
        
        substitution_events = [e for e in events if e["type"] == "substitution"]
        
        if substitution_events:
            actual_subtype = substitution_events[0]["sub_type"]
            passed = actual_subtype == expected_subtype
            all_passed = all_passed and passed
            
            status = "✅" if passed else "❌"
            print(f"{status} '{ref}' -> '{hyp}': {actual_subtype} (expected: {expected_subtype})")
        else:
            print(f"❌ '{ref}' -> '{hyp}': No substitution event found")
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    print("Sub Type Fix Test")
    print("=" * 50)
    
    # Test the specific case from user's analysis
    test1_passed = test_subtype_fix()
    
    # Test multiple substitution types
    test2_passed = test_multiple_substitutions()
    
    print(f"\nOverall Result: {'✅ PASSED' if (test1_passed and test2_passed) else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("🎉 All sub_type calculations are working correctly!")
    else:
        print("⚠️  Some sub_type calculations are still not working properly.")

