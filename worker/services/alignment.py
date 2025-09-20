from typing import List, Dict, Any, Tuple
import re
import unicodedata

# Normalization and stopword helpers
_PUNCT = r"[.,!?;:\"\"„…]+"
_PUNCTUATION = {'.', ',', '!', '?', ';', ':', '"', '"', '"', "'"}
_STOPWORDS = {"ve", "de", "da", "ile", "mi", "mı", "mu", "mü", "ki"}

def _is_punctuation(tok: str) -> bool:
    """Check if token is punctuation"""
    return tok in _PUNCTUATION

def normalize_sub_type(sub_type: str) -> str:
    """Normalize sub_type labels to standard format"""
    if not sub_type:
        return sub_type
    
    # Mapping for sub_type normalization
    normalization_map = {
        "hece_ek": "hece_ekleme",
        "hece_cik": "hece_eksiltme", 
        "degistirme": "harf_değiştirme"
    }
    
    return normalization_map.get(sub_type, sub_type)

def _norm_token(tok: str) -> str:
    """Normalize token: NFC + casefold + remove leading/trailing punctuation"""
    t = unicodedata.normalize("NFC", tok or "").casefold()
    # Remove leading and trailing punctuation (but keep apostrophes)
    t = re.sub(rf"^{_PUNCT}", "", t)
    t = re.sub(rf"{_PUNCT}$", "", t)
    # Keep internal apostrophes (like Atatürk'ün) - they are part of the word
    return t

def _is_stop(tok: str) -> bool:
    """Check if token is a stopword"""
    return _norm_token(tok) in _STOPWORDS

def _get_operation_cost(ref_token: str, hyp_token: str, operation: str) -> float:
    """Get cost for specific operation considering stopwords"""
    if operation == "equal":
        return 0.0
    elif operation in ["insert", "delete"]:
        # Lower cost for stopwords
        token = ref_token if operation == "delete" else hyp_token
        return 0.4 if _is_stop(token) else 1.0
    elif operation == "replace":
        # Higher cost for stopword substitutions
        return 1.2 if (_is_stop(ref_token) or _is_stop(hyp_token)) else 1.0
    return 1.0


def tokenize_tr(text: str) -> List[str]:
    """Turkish tokenization using regex pattern"""
    # Keep original casing and extract words and punctuation
    words = re.findall(r"[a-zA-ZçğıöşüâîûÇĞIİÖŞÜÂÎÛ']+|[.,!?;:\"\"„…]+", text)
    return words


def levenshtein_align(ref_tokens: List[str], hyp_tokens: List[str]) -> List[Tuple[str, str, str, int, int]]:
    """
    Dynamic programming alignment between reference and hypothesis tokens
    Returns list of (operation, ref_token, hyp_token, ref_idx, hyp_idx)
    """
    m, n = len(ref_tokens), len(hyp_tokens)
    
    # Create DP table
    dp = [[0.0] * (n + 1) for _ in range(m + 1)]
    
    # Initialize base cases with stopword-aware costs
    for i in range(m + 1):
        if i == 0:
            dp[i][0] = 0
        else:
            dp[i][0] = dp[i-1][0] + _get_operation_cost(ref_tokens[i-1], "", "delete")
    
    for j in range(n + 1):
        if j == 0:
            dp[0][j] = 0
        else:
            dp[0][j] = dp[0][j-1] + _get_operation_cost("", hyp_tokens[j-1], "insert")
    
    # Fill DP table
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            ref_token = ref_tokens[i-1]
            hyp_token = hyp_tokens[j-1]
            
            # Check for normalized equality first
            if _norm_token(ref_token) == _norm_token(hyp_token):
                dp[i][j] = dp[i-1][j-1]
            else:
                # Calculate costs for each operation
                del_cost = dp[i-1][j] + _get_operation_cost(ref_token, "", "delete")
                ins_cost = dp[i][j-1] + _get_operation_cost("", hyp_token, "insert")
                
                # For punctuation tokens, disallow substitution (set cost to infinity)
                if _is_punctuation(ref_token) or _is_punctuation(hyp_token):
                    rep_cost = float('inf')
                else:
                    rep_cost = dp[i-1][j-1] + _get_operation_cost(ref_token, hyp_token, "replace")
                
                dp[i][j] = min(del_cost, ins_cost, rep_cost)
    
    # Backtrack to find alignment
    alignment = []
    i, j = m, n
    
    while i > 0 or j > 0:
        ref_token = ref_tokens[i-1] if i > 0 else ""
        hyp_token = hyp_tokens[j-1] if j > 0 else ""
        
        # Check for normalized equality first
        if i > 0 and j > 0 and _norm_token(ref_token) == _norm_token(hyp_token):
            # Equal (normalized)
            alignment.append(("equal", ref_token, hyp_token, i-1, j-1))
            i -= 1
            j -= 1
        elif i > 0 and (j == 0 or dp[i-1][j] < dp[i][j-1]):
            # Delete
            alignment.append(("delete", ref_token, "", i-1, -1))
            i -= 1
        elif j > 0 and (i == 0 or dp[i][j-1] < dp[i-1][j]):
            # Insert
            alignment.append(("insert", "", hyp_token, -1, j-1))
            j -= 1
        else:
            # Replace (only if not punctuation)
            if not (_is_punctuation(ref_token) or _is_punctuation(hyp_token)):
                alignment.append(("replace", ref_token, hyp_token, i-1, j-1))
                i -= 1
                j -= 1
            else:
                # Force delete/insert for punctuation
                if i > 0:
                    alignment.append(("delete", ref_token, "", i-1, -1))
                    i -= 1
                elif j > 0:
                    alignment.append(("insert", "", hyp_token, -1, j-1))
                    j -= 1
    
    return list(reversed(alignment))


def char_edit_stats(a: str, b: str) -> Tuple[int, int]:
    """Calculate Levenshtein distance and length difference"""
    m, n = len(a), len(b)
    
    # Create DP table for Levenshtein distance
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # Initialize base cases
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    
    # Fill DP table
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i-1] == b[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(
                    dp[i-1][j],    # delete
                    dp[i][j-1],    # insert
                    dp[i-1][j-1]   # replace
                )
    
    edit_distance = dp[m][n]
    length_diff = len(a) - len(b)
    
    return edit_distance, length_diff


def syllables_tr(word: str) -> int:
    """Count syllables in Turkish word based on vowels"""
    vowels = "aeıioöuü"
    syllable_count = 0
    
    for char in word.lower():
        if char in vowels:
            syllable_count += 1
    
    # Every word has at least one syllable
    return max(1, syllable_count)


def classify_replace(ref: str, hyp: str) -> str:
    """Classify replacement type based on edit distance and syllable count"""
    ed, len_diff = char_edit_stats(ref, hyp)
    
    if ed == 1 and len_diff == 1:
        return "harf_ek"
    elif ed == 1 and len_diff == -1:
        return "harf_cik"
    elif ed == 1 and len_diff == 0:
        return "degistirme"
    else:  # ed >= 2
        s_ref, s_hyp = syllables_tr(ref), syllables_tr(hyp)
        if s_hyp > s_ref:
            return "hece_ek"
        elif s_hyp < s_ref:
            return "hece_cik"
        else:
            return "degistirme"


def build_word_events(alignment: List[Tuple[str, str, str, int, int]], word_times: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build word events from alignment and word timing data"""
    word_events = []
    
    for op, ref_token, hyp_token, ref_idx, hyp_idx in alignment:
        # Check for normalized equality even if operation is replace
        if op == "replace" and _norm_token(ref_token) == _norm_token(hyp_token):
            # Only case/punctuation difference - treat as correct
            event_type = "correct"
            subtype = "case_punct_only"
        elif op == "equal":
            event_type = "correct"
            subtype = None
        elif op == "delete":
            event_type = "missing"
            subtype = None
        elif op == "insert":
            event_type = "extra"
            subtype = None
        elif op == "replace":
            event_type = "substitution"
            subtype = classify_replace(ref_token, hyp_token)
            # Normalize sub_type
            subtype = normalize_sub_type(subtype)
            
            # Calculate char_diff and cer_local for substitutions
            char_diff = char_edit_stats(ref_token, hyp_token)[0]
            cer_local = char_diff / max(len(ref_token), 1)
        else:
            event_type = "substitution"  # fallback for unknown operations
            subtype = None
        
        # Get timing data
        start_ms = None
        end_ms = None
        
        if hyp_idx >= 0 and hyp_idx < len(word_times):
            start_ms = word_times[hyp_idx].get("start", 0) * 1000
            end_ms = word_times[hyp_idx].get("end", 0) * 1000
        
        event_data = {
            "ref_token": ref_token if ref_token else None,
            "hyp_token": hyp_token if hyp_token else None,
            "start_ms": start_ms,
            "end_ms": end_ms,
            "type": event_type,
            "sub_type": subtype,  # Changed from "subtype" to "sub_type"
            "ref_idx": ref_idx,
            "hyp_idx": hyp_idx
        }
        
        # Add char_diff and cer_local for substitution events
        if event_type == "substitution":
            event_data["char_diff"] = char_diff
            event_data["cer_local"] = cer_local
        else:
            event_data["char_diff"] = None
            event_data["cer_local"] = None
        
        word_events.append(event_data)
    
    return word_events


def test_case_punct_alignment():
    """Test case and punctuation normalization"""
    ref = ["bu", "güzel", "bir", "gün", "güneş", "parlıyor", "ve", "kuşlar", "şarkı", "söylüyor", "çocuklar", "parkta", "oynuyor"]
    hyp = ["Bu", "güzel", "bir", "günler.", "Güneş", "parlıyordu.", "Kuşlar", "şarkı", "söylüyor.", "Çocukların", "parkta", "çok", "oynuyorlardı."]
    
    alignment = levenshtein_align(ref, hyp)
    events = build_word_events(alignment, [])
    
    # Count event types
    correct = sum(1 for e in events if e["type"] == "correct")
    missing = sum(1 for e in events if e["type"] == "missing")
    extra = sum(1 for e in events if e["type"] == "extra")
    substitution = sum(1 for e in events if e["type"] == "substitution")
    
    print(f"Case/Punct Test Results:")
    print(f"  Correct: {correct}, Missing: {missing}, Extra: {extra}, Substitution: {substitution}")
    
    # Check specific cases
    for i, event in enumerate(events):
        if event["ref_token"] == "bu" and event["hyp_token"] == "Bu":
            print(f"  ✓ 'bu' vs 'Bu' -> {event['type']} (should be correct)")
        elif event["ref_token"] == "söylüyor" and event["hyp_token"] == "söylüyor.":
            print(f"  ✓ 'söylüyor' vs 'söylüyor.' -> {event['type']} (should be correct)")
    
    return events


def test_stopword_alignment():
    """Test stopword handling"""
    ref = ["ve", "kuşlar", "şarkı"]
    hyp = ["Kuşlar", "şarkı"]
    
    alignment = levenshtein_align(ref, hyp)
    events = build_word_events(alignment, [])
    
    # Count event types
    correct = sum(1 for e in events if e["type"] == "correct")
    missing = sum(1 for e in events if e["type"] == "missing")
    extra = sum(1 for e in events if e["type"] == "extra")
    substitution = sum(1 for e in events if e["type"] == "substitution")
    
    print(f"Stopword Test Results:")
    print(f"  Correct: {correct}, Missing: {missing}, Extra: {extra}, Substitution: {substitution}")
    
    # Check specific cases
    for i, event in enumerate(events):
        if event["ref_token"] == "ve":
            print(f"  ✓ 've' -> {event['type']} (should be missing)")
        elif event["ref_token"] == "kuşlar" and event["hyp_token"] == "Kuşlar":
            print(f"  ✓ 'kuşlar' vs 'Kuşlar' -> {event['type']} (should be correct)")
        elif event["ref_token"] == "şarkı" and event["hyp_token"] == "şarkı":
            print(f"  ✓ 'şarkı' vs 'şarkı' -> {event['type']} (should be correct)")
    
    return events


def test_apostrophe_alignment():
    """Test apostrophe handling"""
    ref = ["atatürk", "ün", "yanındakiler"]
    hyp = ["Atatürk'ün", "yanındakiler"]
    
    alignment = levenshtein_align(ref, hyp)
    events = build_word_events(alignment, [])
    
    # Count event types
    correct = sum(1 for e in events if e["type"] == "correct")
    missing = sum(1 for e in events if e["type"] == "missing")
    extra = sum(1 for e in events if e["type"] == "extra")
    substitution = sum(1 for e in events if e["type"] == "substitution")
    
    print(f"Apostrophe Test Results:")
    print(f"  Correct: {correct}, Missing: {missing}, Extra: {extra}, Substitution: {substitution}")
    
    # Check specific cases
    for i, event in enumerate(events):
        if event["ref_token"] == "atatürk" and event["hyp_token"] == "Atatürk'ün":
            print(f"  ✓ 'atatürk' vs 'Atatürk'ün' -> {event['type']} (should be substitution)")
        elif event["ref_token"] == "ün":
            print(f"  ✓ 'ün' -> {event['type']} (should be missing)")
        elif event["ref_token"] == "yanındakiler" and event["hyp_token"] == "yanındakiler":
            print(f"  ✓ 'yanındakiler' vs 'yanındakiler' -> {event['type']} (should be correct)")
    
    return events


if __name__ == "__main__":
    print("Testing alignment improvements...")
    print("=" * 50)
    test_case_punct_alignment()
    print()
    test_stopword_alignment()
    print()
    test_apostrophe_alignment()
    print("=" * 50)
    print("Tests completed!")