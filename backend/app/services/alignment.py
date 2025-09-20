from typing import List, Dict, Any, Tuple
import re
import unicodedata


def _norm_token(tok: str) -> str:
    """Normalize token for case-insensitive comparison while preserving apostrophes"""
    if not tok:
        return ""
    # Normalize Unicode and convert to lowercase for comparison
    t = unicodedata.normalize("NFC", tok).lower()
    return t


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
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # Initialize base cases
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    
    # Fill DP table
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            # Use normalized comparison for case-insensitive matching
            if _norm_token(ref_tokens[i-1]) == _norm_token(hyp_tokens[j-1]):
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(
                    dp[i-1][j],    # delete
                    dp[i][j-1],    # insert
                    dp[i-1][j-1]   # replace
                )
    
    # Backtrack to find alignment
    alignment = []
    i, j = m, n
    
    while i > 0 or j > 0:
        if i > 0 and j > 0 and _norm_token(ref_tokens[i-1]) == _norm_token(hyp_tokens[j-1]):
            # Equal (normalized)
            alignment.append(("equal", ref_tokens[i-1], hyp_tokens[j-1], i-1, j-1))
            i -= 1
            j -= 1
        elif i > 0 and (j == 0 or dp[i-1][j] < dp[i][j-1]):
            # Delete
            alignment.append(("delete", ref_tokens[i-1], "", i-1, -1))
            i -= 1
        elif j > 0 and (i == 0 or dp[i][j-1] < dp[i-1][j]):
            # Insert
            alignment.append(("insert", "", hyp_tokens[j-1], -1, j-1))
            j -= 1
        else:
            # Replace
            alignment.append(("replace", ref_tokens[i-1], hyp_tokens[j-1], i-1, j-1))
            i -= 1
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
        # Map operation to event type
        if op == "equal":
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
        else:
            event_type = "substitution"  # fallback for unknown operations
            subtype = None
        
        # Get timing data
        start_ms = None
        end_ms = None
        
        if hyp_idx >= 0 and hyp_idx < len(word_times):
            start_ms = word_times[hyp_idx].get("start", 0) * 1000
            end_ms = word_times[hyp_idx].get("end", 0) * 1000
        
        word_events.append({
            "ref_token": ref_token if ref_token else None,
            "hyp_token": hyp_token if hyp_token else None,
            "start_ms": start_ms,
            "end_ms": end_ms,
            "type": event_type,
            "subtype": subtype,
            "ref_idx": ref_idx,
            "hyp_idx": hyp_idx
        })
    
    return word_events