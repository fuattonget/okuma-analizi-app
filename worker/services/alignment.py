from typing import List, Dict, Any, Tuple
import re
import unicodedata

# Normalization and stopword helpers
_PUNCTUATION = {'.', ',', '!', '?', ';', ':', '"', '"', '"', "'"}
_STOPWORDS = {"ve", "de", "da", "ile", "mi", "mı", "mu", "mü", "ki"}

# Filler/booster words that should be treated as EXTRA when overused
FILLERS = {"çok", "yani", "işte", "şey", "eee", "ııı", "hımm", "falan", "filan", "baya", "hakikaten", "gerçekten"}

def _is_punctuation(tok: str) -> bool:
    """Check if token is punctuation"""
    return tok in _PUNCTUATION

def _is_filler(tok: str) -> bool:
    """Check if token is a filler/booster word"""
    return _norm_token(tok) in FILLERS

def _track_filler_repetitions(hyp_tokens: List[str], word_times: List[Dict[str, Any]]) -> Dict[int, bool]:
    """
    Track filler repetitions within a 2-second sliding window.
    Returns dict mapping hyp_token_index -> is_repeated_filler
    """
    repetition_window_ms = 2000  # 2 seconds
    filler_counts = {}  # filler_word -> list of (timestamp, index)
    repeated_fillers = {}
    
    for i, (token, timing) in enumerate(zip(hyp_tokens, word_times)):
        if _is_filler(token) and timing and 'start' in timing:
            start_ms = timing['start'] * 1000
            filler_word = _norm_token(token)
            
            if filler_word not in filler_counts:
                filler_counts[filler_word] = []
            
            # Add current occurrence
            filler_counts[filler_word].append((start_ms, i))
            
            # Remove old occurrences outside window
            filler_counts[filler_word] = [
                (ts, idx) for ts, idx in filler_counts[filler_word] 
                if start_ms - ts <= repetition_window_ms
            ]
            
            # Mark as repeated if appears 2+ times in window
            if len(filler_counts[filler_word]) >= 2:
                repeated_fillers[i] = True
            else:
                repeated_fillers[i] = False
    
    return repeated_fillers

def _detect_word_repetitions(hyp_tokens: List[str], word_times: List[Dict[str, Any]] = None) -> Dict[int, Dict[str, Any]]:
    """
    Detect word repetitions in hypothesis tokens.
    Returns dict mapping hyp_token_index -> repetition_info
    
    Repetition patterns:
    1. Exact repetitions: "yeni yeni nesil"
    2. Partial repetitions: "yeni nese- yeni nesil" 
    3. Similar repetitions: "yeni yeni- nesil"
    """
    repetition_info = {}
    n = len(hyp_tokens)
    
    for i in range(n):
        current_token = hyp_tokens[i]
        current_norm = _norm_token(current_token)
        
        # Skip very short tokens or punctuation
        if len(current_norm) < 2 or _is_punctuation(current_token):
            repetition_info[i] = {"is_repetition": False, "repetition_group": None, "repetition_type": None}
            continue
        
        # Look for repetitions in nearby tokens (within 5 positions)
        repetition_group = [i]
        repetition_type = None
        
        # Check previous tokens
        for j in range(max(0, i-5), i):
            prev_token = hyp_tokens[j]
            prev_norm = _norm_token(prev_token)
            
            if len(prev_norm) < 2 or _is_punctuation(prev_token):
                continue
                
            # Check for exact match (no normalization)
            # But avoid false positives like "istediği," and "istediği"
            if current_token == prev_token:
                repetition_group.append(j)
                repetition_type = "exact"
                break
            # Check if one is punctuation variant of the other - if so, don't consider repetition
            elif (len(current_token) >= 5 and len(prev_token) >= 5 and 
                  abs(len(current_token) - len(prev_token)) <= 2 and
                  ''.join(c for c in current_token if c.isalnum()) == ''.join(c for c in prev_token if c.isalnum())):
                # These are punctuation variants, not repetitions
                continue
            
            # Check for partial match (current is prefix of previous) - only for longer words
            # But avoid false positives like "istediği" in "istediği,"
            if (len(current_token) >= 5 and len(prev_token) >= 5 and 
                current_token in prev_token and len(current_token) >= 3 and
                not (len(prev_token) - len(current_token) <= 2)):  # Avoid punctuation variants
                repetition_group.append(j)
                repetition_type = "partial"
                break
                    
            # Check for high similarity - only for longer words to avoid false positives
            if len(current_norm) >= 5 and len(prev_norm) >= 5:
                lev_dist = char_edit_stats(current_norm, prev_norm)[0]
                max_len = max(len(current_norm), len(prev_norm), 1)
                similarity = 1.0 - (lev_dist / max_len)
                
                if similarity > 0.7:  # High similarity threshold
                    repetition_group.append(j)
                    repetition_type = "similar"
                    break
        
        # Check next tokens for exact repetitions (like "yeni" -> "yeni")
        if not repetition_type:
            for j in range(i + 1, min(n, i + 5)):  # Check next 4 tokens
                next_token = hyp_tokens[j]
                next_norm = _norm_token(next_token)
                
                if len(next_norm) < 2 or _is_punctuation(next_token):
                    continue
                    
                # Check for exact match
                if current_norm == next_norm:
                    repetition_group.append(j)
                    repetition_type = "exact"
                    break
        
        # Check next tokens for partial repetitions (like "nese-")
        if not repetition_type and i < n - 1:
            next_token = hyp_tokens[i + 1]
            next_norm = _norm_token(next_token)
            
            # Check if current token is a partial version of next token
            if (current_norm and next_norm and 
                current_norm in next_norm and 
                len(current_norm) >= 3 and 
                len(next_norm) > len(current_norm)):
                repetition_group.append(i + 1)
                repetition_type = "partial_forward"
        
        # Check if current token is a partial version of a previous token
        if not repetition_type:
            for j in range(max(0, i-5), i):
                prev_token = hyp_tokens[j]
                prev_norm = _norm_token(prev_token)
                
                if (len(prev_norm) >= 2 and not _is_punctuation(prev_token) and
                    current_norm and prev_norm and 
                    current_norm in prev_norm and 
                    len(current_norm) >= 3 and 
                    len(prev_norm) > len(current_norm)):
                    repetition_group.append(j)
                    repetition_type = "partial_backward"
                    break
        
        # Check if current token is a partial version of a next token
        if not repetition_type and i < n - 1:
            for j in range(i + 1, min(n, i + 3)):  # Check next 2 tokens
                next_token = hyp_tokens[j]
                next_norm = _norm_token(next_token)
                
                if (len(next_norm) >= 2 and not _is_punctuation(next_token) and
                    current_norm and next_norm and 
                    len(current_norm) >= 3 and 
                    len(next_norm) > len(current_norm)):
                    
                    # Check for substring match
                    if current_norm in next_norm:
                        repetition_group.append(j)
                        repetition_type = "partial_forward"
                        break
                    
                    # Check for high similarity (for cases like "nese" vs "nesil")
                    lev_dist = char_edit_stats(current_norm, next_norm)[0]
                    max_len = max(len(current_norm), len(next_norm), 1)
                    similarity = 1.0 - (lev_dist / max_len)
                    
                    if similarity >= 0.6:  # Lower threshold for partial matches
                        repetition_group.append(j)
                        repetition_type = "partial_forward"
                        break
        
        # NEW: Check for forward repetition patterns
        # This handles cases like "yeni nese- yeni nesil" where the first "yeni" and "nese-" 
        # should be marked as repetitions because they appear again later
        if not repetition_type and i < n - 2:
            # Look for patterns where current token + next token form a repetition
            # with tokens that appear later in the sequence
            for j in range(i + 2, min(n, i + 6)):  # Check tokens 2-5 positions ahead
                later_token = hyp_tokens[j]
                later_norm = _norm_token(later_token)
                
                if len(later_norm) < 2 or _is_punctuation(later_token):
                    continue
                
                # Check if current token matches a later token
                if current_norm == later_norm:
                    # Found a match, now check if there's a partial match in between
                    for k in range(i + 1, j):
                        middle_token = hyp_tokens[k]
                        middle_norm = _norm_token(middle_token)
                        
                        if len(middle_norm) < 2 or _is_punctuation(middle_token):
                            continue
                        
                        # Check if middle token is a partial version of the later token
                        if (middle_norm and later_norm and 
                            middle_norm in later_norm and 
                            len(middle_norm) >= 3 and 
                            len(later_norm) > len(middle_token)):
                            # Found a forward repetition pattern
                            repetition_group.extend([i, k, j])
                            repetition_type = "forward_repetition"
                            break
                    
                    if repetition_type:
                        break
        
        # Mark as repetition if group has more than one token
        is_repetition = len(repetition_group) > 1
        repetition_info[i] = {
            "is_repetition": is_repetition,
            "repetition_group": repetition_group if is_repetition else None,
            "repetition_type": repetition_type if is_repetition else None
        }
    
    return repetition_info

def normalize_sub_type(sub_type: str) -> str:
    """Normalize sub_type labels to standard format"""
    if not sub_type:
        return sub_type
    
    # Mapping for sub_type normalization
    normalization_map = {
        "hece_ek": "hece_ekleme",
        "hece_cik": "hece_eksiltme", 
        "harf_ek": "harf_ekleme",
        "harf_cik": "harf_eksiltme",
        "degistirme": "harf_değiştirme"
    }
    
    return normalization_map.get(sub_type, sub_type)

def _norm_token(tok: str) -> str:
    """Normalize token: lowercase + Turkish diacritic normalization + strip only dashes for repetition detection"""
    if not tok:
        return ""
    
    # Convert to lowercase first
    t = tok.lower()
    
    # Turkish diacritic normalization
    # İ → i, ğ → g, ç → c, ö → o, ü → u, ş → s
    t = t.replace('ı', 'i')
    t = t.replace('ğ', 'g')
    t = t.replace('ç', 'c')
    t = t.replace('ö', 'o')
    t = t.replace('ü', 'u')
    t = t.replace('ş', 's')
    
    # Handle İ variations (İ can become i̇ after casefold)
    t = t.replace('i̇', 'i')  # İ casefold result
    
    # Remove combining diacritical marks
    t = unicodedata.normalize('NFD', t)
    t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    t = unicodedata.normalize('NFC', t)
    
    # Strip trailing dashes, quotes, and punctuation (for repetition detection)
    # According to criteria: "Noktalama farkı ("," "." vb.) tek başına hata oluşturmaz"
    # But quotes and dashes are often repetition markers from STT, so strip them
    t = re.sub(r'-+$', '', t)
    t = re.sub(r'^-+', '', t)
    t = re.sub(r'["""]+$', '', t)  # Remove trailing quotes
    t = re.sub(r'^["""]+', '', t)  # Remove leading quotes
    t = re.sub(r'[.,!?;:]+$', '', t)  # Remove trailing punctuation
    t = re.sub(r'^[.,!?;:]+', '', t)  # Remove leading punctuation
    
    return t

def _is_punctuation_only_difference(ref: str, hyp: str) -> bool:
    """Check if the only difference between ref and hyp is punctuation"""
    if not ref or not hyp:
        return False
    
    # Remove all punctuation from both tokens
    ref_clean = re.sub(r'[.,!?;:""\'-]', '', ref)
    hyp_clean = re.sub(r'[.,!?;:""\'-]', '', hyp)
    
    # Check if they are equal after removing punctuation
    return _norm_token(ref_clean) == _norm_token(hyp_clean)

def _is_stop(tok: str) -> bool:
    """Check if token is a stopword"""
    return _norm_token(tok) in _STOPWORDS

def _get_operation_cost(ref_token: str, hyp_token: str, operation: str, 
                       repeated_fillers: Dict[int, bool] = None, hyp_idx: int = -1) -> float:
    """Get cost for specific operation considering stopwords, fillers, and POS"""
    if operation == "equal":
        return 0.0
    elif operation in ["insert", "delete"]:
        # Base cost
        base_cost = 1.0
        
        # Lower cost for stopwords
        token = ref_token if operation == "delete" else hyp_token
        if _is_stop(token):
            base_cost = 0.4
        
        # Filler handling - only penalize repeated fillers
        if operation == "insert" and _is_filler(hyp_token):
            if repeated_fillers and hyp_idx in repeated_fillers and repeated_fillers[hyp_idx]:
                # Repeated filler - give bonus for insertion
                return max(0.1, base_cost - 0.3)
            else:
                # Single filler - normal cost
                return base_cost
        
        return base_cost
    elif operation == "replace":
        # Check for punctuation substitution - forbid all punctuation substitutions
        if _is_punctuation(ref_token) or _is_punctuation(hyp_token):
            # Any punctuation substitution - forbid completely
            return float('inf')
        
        # Check for filler substitution penalties - forbid all filler substitutions
        if _is_filler(hyp_token) and not _is_filler(ref_token):
            # Filler substituting content word - forbid this completely
            return float('inf')
        
        # SUB gating: compute normalized Levenshtein distance
        ref_norm = _norm_token(ref_token)
        hyp_norm = _norm_token(hyp_token)
        lev_dist = char_edit_stats(ref_norm, hyp_norm)[0]
        max_len = max(len(ref_norm), len(hyp_norm), 1)
        lev_norm = lev_dist / max_len
        
        # If lev_norm > 0.5, treat SUB as disallowed
        if lev_norm > 0.5:
            return float('inf')
        
        # Proper-noun rule: if ref looks like a proper noun and lev_norm > 0.4, disallow SUB
        if re.match(r'^[A-ZÇĞİÖŞÜÂÎÛ]', ref_token) and lev_norm > 0.4:
            return float('inf')
        
        # Higher cost for stopword substitutions
        return 1.2 if (_is_stop(ref_token) or _is_stop(hyp_token)) else 1.0
    
    return 1.0


def tokenize_tr(text: str) -> List[str]:
    """Turkish tokenization using regex pattern - preserves apostrophes, removes punctuation"""
    if not text or not text.strip():
        return []
    
    # Normalize curly quotes to ASCII apostrophe
    text = text.replace("'", "'").replace("'", "'")
    
    # Keep original casing and extract words only (no punctuation)
    # Pattern matches: [letters/digits]+(?:'[letters/digits]+)*
    # This ensures apostrophes are part of words when between letters/digits
    words = re.findall(r"[A-Za-zÇĞİÖŞÜÂÎÛçğıöşü0-9]+(?:'[A-Za-zÇĞİÖŞÜÂÎÛçğıöşü0-9]+)*", text)
    
    # Filter out empty strings and very short words (1 char) unless they are common
    common_single_chars = {"a", "e", "i", "ı", "o", "ö", "u", "ü"}
    filtered_words = []
    
    for word in words:
        if len(word) > 1 or word in common_single_chars:
            filtered_words.append(word)
    
    return filtered_words


def levenshtein_align(ref_tokens: List[str], hyp_tokens: List[str], 
                     word_times: List[Dict[str, Any]] = None) -> List[Tuple[str, str, str, int, int]]:
    """
    Dynamic programming alignment between reference and hypothesis tokens
    Returns list of (operation, ref_token, hyp_token, ref_idx, hyp_idx)
    """
    m, n = len(ref_tokens), len(hyp_tokens)
    
    # Track filler repetitions if word_times available
    repeated_fillers = {}
    if word_times and len(word_times) == len(hyp_tokens):
        repeated_fillers = _track_filler_repetitions(hyp_tokens, word_times)
    
    # Detect word repetitions
    word_repetitions = _detect_word_repetitions(hyp_tokens, word_times)
    
    # Create DP table
    dp = [[0.0] * (n + 1) for _ in range(m + 1)]
    
    # Initialize base cases with filler-aware costs
    for i in range(m + 1):
        if i == 0:
            dp[i][0] = 0
        else:
            dp[i][0] = dp[i-1][0] + _get_operation_cost(ref_tokens[i-1], "", "delete", repeated_fillers, -1)
    
    for j in range(n + 1):
        if j == 0:
            dp[0][j] = 0
        else:
            dp[0][j] = dp[0][j-1] + _get_operation_cost("", hyp_tokens[j-1], "insert", repeated_fillers, j-1)
    
    # Fill DP table
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            ref_token = ref_tokens[i-1]
            hyp_token = hyp_tokens[j-1]
            
            # Check for normalized equality first
            if _norm_token(ref_token) == _norm_token(hyp_token):
                dp[i][j] = dp[i-1][j-1]
            else:
                # Calculate costs for each operation with filler awareness
                del_cost = dp[i-1][j] + _get_operation_cost(ref_token, "", "delete", repeated_fillers, -1)
                ins_cost = dp[i][j-1] + _get_operation_cost("", hyp_token, "insert", repeated_fillers, j-1)
                rep_cost = dp[i-1][j-1] + _get_operation_cost(ref_token, hyp_token, "replace", repeated_fillers, j-1)
                
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
        elif i > 0 and j > 0 and _is_punctuation(ref_token) and _is_punctuation(hyp_token):
            # Punctuation matching - only allow exact match, otherwise skip
            if ref_token == hyp_token:
                alignment.append(("equal", ref_token, hyp_token, i-1, j-1))
                i -= 1
                j -= 1
            else:
                # Different punctuation - skip both (treat as equal)
                alignment.append(("equal", ref_token, hyp_token, i-1, j-1))
                i -= 1
                j -= 1
        elif i > 0 and (j == 0 or dp[i-1][j] < dp[i][j-1]):
            # Delete - but skip punctuation completely
            if _is_punctuation(ref_token):
                # Skip punctuation completely - don't add to alignment
                i -= 1
            else:
                alignment.append(("delete", ref_token, "", i-1, -1))
                i -= 1
        elif j > 0 and (i == 0 or dp[i][j-1] < dp[i-1][j]):
            # Insert - but skip punctuation completely
            if _is_punctuation(hyp_token):
                # Skip punctuation completely - don't add to alignment
                j -= 1
            else:
                alignment.append(("insert", "", hyp_token, -1, j-1))
                j -= 1
        else:
            # Replace (check if allowed)
            rep_cost = _get_operation_cost(ref_token, hyp_token, "replace", repeated_fillers, j-1)
            if rep_cost == float('inf'):
                # Forbidden substitution - force delete/insert
                if i > 0:
                    alignment.append(("delete", ref_token, "", i-1, -1))
                    i -= 1
                elif j > 0:
                    alignment.append(("insert", "", hyp_token, -1, j-1))
                    j -= 1
            else:
                alignment.append(("replace", ref_token, hyp_token, i-1, j-1))
                i -= 1
                j -= 1
    
    alignment = list(reversed(alignment))
    
    # Post-repair pass: convert problematic filler substitutions
    alignment = _post_repair_filler_substitutions(alignment)
    
    return alignment


def _post_repair_filler_substitutions(alignment: List[Tuple[str, str, str, int, int]]) -> List[Tuple[str, str, str, int, int]]:
    """
    Post-repair pass to convert problematic filler substitutions into MISSING+EXTRA pairs.
    """
    repaired = []
    i = 0
    
    while i < len(alignment):
        op, ref_token, hyp_token, ref_idx, hyp_idx = alignment[i]
        
        if op == "replace" and _is_filler(hyp_token) and not _is_filler(ref_token):
            # Check if next alignment has high similarity
            next_similar = False
            if i + 1 < len(alignment):
                next_op, next_ref, next_hyp, _, _ = alignment[i + 1]
                if next_op in ["equal", "replace"] and next_ref and next_hyp:
                    # Calculate normalized Levenshtein distance
                    lev_dist = char_edit_stats(ref_token, next_hyp)[0]
                    max_len = max(len(ref_token or ""), len(next_hyp))
                    lev_norm = lev_dist / max_len if max_len > 0 else 1.0
                    
                    if lev_norm <= 0.3:  # High similarity threshold
                        next_similar = True
            else:
                # If no next alignment, check if ref_token matches any future hyp_token
                for j in range(i + 1, len(alignment)):
                    _, _, future_hyp, _, _ = alignment[j]
                    if future_hyp:
                        lev_dist = char_edit_stats(ref_token, future_hyp)[0]
                        max_len = max(len(ref_token or ""), len(future_hyp))
                        lev_norm = lev_dist / max_len if max_len > 0 else 1.0
                        if lev_norm <= 0.3:
                            next_similar = True
                            break
            
            if next_similar:
                # Convert SUB to MISSING + EXTRA
                repaired.append(("delete", ref_token, "", ref_idx, -1))
                repaired.append(("insert", "", hyp_token, -1, hyp_idx))
            else:
                repaired.append((op, ref_token, hyp_token, ref_idx, hyp_idx))
        else:
            repaired.append((op, ref_token, hyp_token, ref_idx, hyp_idx))
        
        i += 1
    
    return repaired


def char_edit_stats(a: str, b: str) -> Tuple[int, int]:
    """Calculate Levenshtein distance and length difference"""
    if a is None:
        a = ""
    if b is None:
        b = ""
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


def classify_replace(ref: str, hyp: str) -> str:
    """Classify replacement type based on edit distance and character count according to criteria"""
    ed, len_diff = char_edit_stats(ref, hyp)
    
    # According to criteria:
    # - harf_ekleme: fark sadece 1 harf ekleme
    # - harf_eksiltme: fark sadece 1 harf eksiltme  
    # - hece_ekleme: hyp_token ref_token'dan uzun ve aradaki fark ≥2 harf
    # - hece_eksiltme: hyp_token ref_token'dan kısa ve aradaki fark ≥2 harf
    
    # len_diff = len(ref) - len(hyp)
    # So len_diff > 0 means ref is longer (hyp is shorter)
    # And len_diff < 0 means ref is shorter (hyp is longer)
    
    if ed == 1 and len_diff == -1:  # ref shorter by 1, hyp longer by 1
        return "harf_ekleme"
    elif ed == 1 and len_diff == 1:  # ref longer by 1, hyp shorter by 1
        return "harf_eksiltme"
    elif ed == 1 and len_diff == 0:  # same length, 1 character change
        return "harf_değiştirme"
    else:  # ed >= 2
        # Check character length difference for syllable-like classification
        if len_diff <= -2:  # ref much shorter, hyp much longer
            return "hece_ekleme"
        elif len_diff >= 2:  # ref much longer, hyp much shorter
            return "hece_eksiltme"
        elif len_diff == 1:  # ref longer by 1, hyp shorter by 1, but ed >= 2
            return "hece_eksiltme"  # More complex than simple harf_eksiltme
        elif len_diff == -1:  # ref shorter by 1, hyp longer by 1, but ed >= 2
            return "hece_ekleme"  # More complex than simple harf_ekleme
        else:  # len_diff == 0, ed >= 2
            return "harf_değiştirme"


def build_word_events(alignment: List[Tuple[str, str, str, int, int]], word_times: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build word events from alignment and word timing data"""
    word_events = []
    
    # Extract hypothesis tokens for repetition detection
    hyp_tokens = []
    for op, ref_token, hyp_token, ref_idx, hyp_idx in alignment:
        if hyp_token:
            hyp_tokens.append(hyp_token)
        else:
            hyp_tokens.append("")
    
    # Detect word repetitions using new algorithm
    word_repetitions = _detect_word_repetitions(hyp_tokens, word_times)
    
    # Create repetition map for backward compatibility
    repetition_map = {}  # alignment_idx -> is_repetition
    for i, (op, ref_token, hyp_token, ref_idx, hyp_idx) in enumerate(alignment):
        if hyp_token and hyp_idx >= 0 and hyp_idx < len(hyp_tokens):
            repetition_info = word_repetitions.get(hyp_idx, {"is_repetition": False})
            repetition_map[i] = repetition_info["is_repetition"]  # Use alignment index i, not hyp_idx
        else:
            repetition_map[i] = False
    
    # NEW: Enhanced repetition detection for "--" patterns and consecutive extra tokens
    def check_enhanced_repetition(alignment_idx: int, op: str, ref_token: str, hyp_token: str) -> bool:
        """Check for enhanced repetition patterns - only for clear repetition cases"""
        if not hyp_token:
            return False
            
        # Check for repetition patterns in both insert and replace operations
        # Insert operations: extra tokens that might be repetitions
        # Replace operations: tokens with clear repetition markers
        if op not in ["insert", "replace"]:
            return False
            
        # Rule 1: Check for "--" pattern in hyp_token (clear repetition marker)
        # If a token ends with "--", it's almost certainly a repetition marker from ElevenLabs
        if "--" in hyp_token:
            # Clean the hyp_token by removing "--" for comparison
            clean_hyp = hyp_token.replace("--", "").strip()
            
            # Look for similar tokens in nearby positions (both before and after)
            for j in range(max(0, alignment_idx - 5), min(len(alignment), alignment_idx + 6)):
                if j == alignment_idx:
                    continue
                other_op, other_ref, other_hyp, other_ref_idx, other_hyp_idx = alignment[j]
                if other_hyp and other_hyp != hyp_token:
                    # Check for exact match after removing "--" and normalizing
                    norm_hyp = _norm_token(clean_hyp)
                    norm_other = _norm_token(other_hyp)
                    if norm_hyp == norm_other:  # Exact match
                        return True
                    
                    # Check if the clean hyp_token is a prefix of other_hyp
                    if (norm_hyp and len(norm_hyp) >= 3 and norm_other and 
                        norm_hyp in norm_other and len(norm_other) > len(norm_hyp)):
                        return True
                    
                    # Check if other_hyp is a prefix of clean hyp_token
                    if (norm_other and len(norm_other) >= 3 and norm_hyp and 
                        norm_other in norm_hyp and len(norm_hyp) > len(norm_other)):
                        return True
                    
                    # Check for high similarity (for cases like "eserin-i--" vs "eseriniz")
                    
                    lev_dist = char_edit_stats(norm_hyp, norm_other)[0]
                    max_len = max(len(norm_hyp), len(norm_other), 1)
                    similarity = 1.0 - (lev_dist / max_len)
                    if similarity >= 0.6:  # 60% similarity threshold for "--" patterns
                        return True
            
            # Special case: If hyp_token ends with "--" and there's a ref_token,
            # check if the clean version matches the ref_token
            if ref_token:
                norm_hyp_clean = _norm_token(clean_hyp)
                norm_ref = _norm_token(ref_token)
                if norm_hyp_clean == norm_ref:  # Exact match with ref
                    return True
                
                # Check for substring relationships with ref_token
                if (norm_hyp_clean and len(norm_hyp_clean) >= 3 and norm_ref and 
                    norm_hyp_clean in norm_ref):
                    return True
                if (norm_ref and len(norm_ref) >= 3 and norm_hyp_clean and 
                    norm_ref in norm_hyp_clean):
                    return True
            
            # If no similar token found nearby, but token has "--", still consider it repetition
            # This handles cases where the repetition is clear from the "--" marker
            return True
        
        # Rule 2: Check for middle-dash patterns in hyp_token (clear repetition marker)
        # Patterns like "u-üzerindeki", "öğre-öğretmenleri" where the dash is in the middle
        if "-" in hyp_token and not hyp_token.startswith("-") and not hyp_token.endswith("-"):
            # Check if the part after the dash matches the ref_token
            if ref_token:
                # Split by dash and take the part after the first dash
                parts = hyp_token.split("-", 1)
                if len(parts) > 1:
                    norm_hyp_after_dash = _norm_token(parts[1])  # Part after first dash
                    norm_ref = _norm_token(ref_token)
                    
                    # Check for exact match
                    if norm_hyp_after_dash == norm_ref:
                        return True
                    
                    # Check for substring relationships
                    if norm_hyp_after_dash and len(norm_hyp_after_dash) >= 3 and norm_hyp_after_dash in norm_ref:
                        return True
                    if norm_ref and len(norm_ref) >= 3 and norm_ref in norm_hyp_after_dash:
                        return True
                    
                    # Check for high similarity
                    
                    lev_dist = char_edit_stats(norm_hyp_after_dash, norm_ref)[0]
                    max_len = max(len(norm_hyp_after_dash), len(norm_ref), 1)
                    similarity = 1.0 - (lev_dist / max_len)
                    if similarity >= 0.7:  # 70% similarity threshold
                        return True
            
            # If no ref_token or no match, but token has middle dash, still consider it repetition
            return True
        
        # Rule 3: Check for repetition patterns in hyp_token (clear repetition markers)
        # Patterns: "es-", "ge-", "ba-", "de-", "da-", "te-", "ta-", etc.
        # If a token starts with a common prefix followed by "-", it's likely a repetition marker
        repetition_prefixes = ["es-", "ge-", "ba-", "de-", "da-", "te-", "ta-", "ke-", "ka-", "me-", "ma-", "ne-", "na-", "pe-", "pa-", "re-", "ra-", "se-", "sa-", "ve-", "va-", "ye-", "ya-", "ze-", "za-"]
        
        for prefix in repetition_prefixes:
            if hyp_token.startswith(prefix):
                # Check if the rest of the token matches the ref_token
                if ref_token:
                    norm_hyp_rest = _norm_token(hyp_token[len(prefix):])  # Remove prefix
                    norm_ref = _norm_token(ref_token)
                    if norm_hyp_rest == norm_ref:  # Exact match
                        return True
                    
                    # Check for substring relationships
                    if norm_hyp_rest and len(norm_hyp_rest) >= 3 and norm_hyp_rest in norm_ref:
                        return True
                    if norm_ref and len(norm_ref) >= 3 and norm_ref in norm_hyp_rest:
                        return True
                    
                    # Check for high similarity
                    
                    lev_dist = char_edit_stats(norm_hyp_rest, norm_ref)[0]
                    max_len = max(len(norm_hyp_rest), len(norm_ref), 1)
                    similarity = 1.0 - (lev_dist / max_len)
                    if similarity >= 0.7:  # 70% similarity threshold
                        return True
                
                # If no ref_token or no match, but token has repetition prefix, still consider it repetition
                return True
        
        
        # Rule 4: Check if consecutive extra tokens later match ref tokens
        # Look ahead for matching ref tokens - but be much more conservative
        for j in range(alignment_idx + 1, min(len(alignment), alignment_idx + 6)):
            future_op, future_ref, future_hyp, future_ref_idx, future_hyp_idx = alignment[j]
            if future_ref and future_hyp:
                # Check if current hyp_token exactly matches future ref_token
                norm_hyp = _norm_token(hyp_token)
                norm_ref = _norm_token(future_ref)
                if norm_hyp == norm_ref:  # Exact match only
                    return True
                
                # Only check for substring relationships if there's a clear repetition pattern
                # This means the hyp_token should be significantly different from ref_token
                # and the future_ref should be significantly different from future_hyp
                if (norm_ref and len(norm_ref) >= 4 and norm_ref in norm_hyp and
                    len(norm_hyp) - len(norm_ref) >= 4):  # At least 4 character difference
                    return True
                
                if (norm_hyp and len(norm_hyp) >= 4 and norm_hyp in norm_ref and
                    len(norm_ref) - len(norm_hyp) >= 4):  # At least 4 character difference
                    return True
                
                # Check for high similarity only for very similar tokens (95%+ similarity)
                # Raised from 0.8 to 0.95 to avoid false positives like "ihtiyaçlar" vs "ihtiyaçları"
                lev_dist = char_edit_stats(norm_hyp, norm_ref)[0]
                max_len = max(len(norm_hyp), len(norm_ref), 1)
                similarity = 1.0 - (lev_dist / max_len)
                if similarity >= 0.95:  # 95% similarity threshold - stricter to avoid false repetitions
                    return True
        
        return False
    
    # NEW: Check for consecutive extra tokens that form repetition patterns
    def check_consecutive_extra_repetition(alignment_idx: int, alignment: List[Tuple[str, str, str, int, int]]) -> bool:
        """Check if current position is part of consecutive extra tokens that form repetition according to criteria"""
        if alignment_idx >= len(alignment):
            return False
            
        current_op, current_ref, current_hyp, current_ref_idx, current_hyp_idx = alignment[alignment_idx]
        
        # Only check insert operations (extra tokens), not replace operations (substitutions)
        if current_op != "insert" or not current_hyp:
            return False
        
        # According to criteria:
        # 1. hyp_token "--" ile bitiyorsa ve sonraki token aynı/benzer → repetition
        # 2. Arka arkaya gelen aynı hyp_token dizileri (extra) sonradan ref_token ile eşleşiyorsa → hepsi repetition
        
        # Rule 1: Check for "--" pattern in hyp_token and next token similarity
        if current_hyp.endswith("--"):
            # Look for next token in alignment
            for j in range(alignment_idx + 1, min(len(alignment), alignment_idx + 3)):
                if j < len(alignment):
                    next_op, next_ref, next_hyp, next_ref_idx, next_hyp_idx = alignment[j]
                    if next_hyp:
                        # Check if next token is similar to current (without --)
                        current_base = current_hyp.replace("--", "")
                        if _norm_token(current_base) == _norm_token(next_hyp):
                            return True
                        # Check for high similarity
                        lev_dist = char_edit_stats(_norm_token(current_base), _norm_token(next_hyp))[0]
                        max_len = max(len(_norm_token(current_base)), len(_norm_token(next_hyp)), 1)
                        similarity = 1.0 - (lev_dist / max_len)
                        if similarity >= 0.8:
                            return True
        
        # Rule 2: Check for consecutive identical hyp_tokens that later match ref tokens
        # Find all consecutive insert operations starting from current position
        consecutive_operations = []
        for j in range(alignment_idx, len(alignment)):
            op, ref_token, hyp_token, ref_idx, hyp_idx = alignment[j]
            if op == "insert" and hyp_token:
                consecutive_operations.append((j, hyp_token))
            else:
                break
        
        # Need at least 2 consecutive operations to form a pattern
        if len(consecutive_operations) < 2:
            return False
        
        # Check if any two consecutive hyp_tokens are identical
        for k in range(len(consecutive_operations) - 1):
            if consecutive_operations[k][1] == consecutive_operations[k+1][1]:
                return True
        
        # Look ahead for correct tokens that might match our consecutive operations
        start_look_ahead = alignment_idx + len(consecutive_operations)
        for j in range(start_look_ahead, min(len(alignment), start_look_ahead + 6)):
            future_op, future_ref, future_hyp, future_ref_idx, future_hyp_idx = alignment[j]
            if future_op == "equal" and future_ref and future_hyp:
                # Check if any of our consecutive operations match this correct token
                for op_idx, op_hyp in consecutive_operations:
                    # Check for exact match (no punctuation cleaning)
                    if op_hyp == future_ref:
                        return True
                    
                    # Check for high similarity
                    lev_dist = char_edit_stats(_norm_token(op_hyp), _norm_token(future_ref))[0]
                    max_len = max(len(_norm_token(op_hyp)), len(_norm_token(future_ref)), 1)
                    similarity = 1.0 - (lev_dist / max_len)
                    if similarity >= 0.8:
                        return True
        
        return False
    
    # Post-repair: Fix repetition events that consumed ref_token
    # If a repetition event consumed a ref_token, the next extra event might be the correct reading
    for i in range(len(alignment) - 1):
        current_op, current_ref, current_hyp, current_ref_idx, current_hyp_idx = alignment[i]
        next_op, next_ref, next_hyp, next_ref_idx, next_hyp_idx = alignment[i + 1]
        
        # If current is repetition and next is extra, check if next should be substitution
        if (current_op in ["replace", "insert"] and current_ref and 
            next_op == "insert" and not next_ref and next_hyp):
            
            # Check if next_hyp is similar to current_ref (the consumed ref_token)
            norm_current_ref = _norm_token(current_ref)
            norm_next_hyp = _norm_token(next_hyp)
            
            # Check for high similarity (80%+ threshold)
            
            lev_dist = char_edit_stats(norm_current_ref, norm_next_hyp)[0]
            max_len = max(len(norm_current_ref), len(norm_next_hyp), 1)
            similarity = 1.0 - (lev_dist / max_len)
            
            if similarity >= 0.8:  # 80% similarity threshold
                # Convert next extra to substitution by giving it the ref_token
                alignment[i + 1] = ("replace", current_ref, next_hyp, current_ref_idx, next_hyp_idx)
                # Make current repetition not consume ref_token
                alignment[i] = (current_op, None, current_hyp, current_ref_idx, current_hyp_idx)

    for i, (op, ref_token, hyp_token, ref_idx, hyp_idx) in enumerate(alignment):
        # Initialize subtype for all cases
        subtype = None
        char_diff = None
        cer_local = None
        
        # Skip punctuation tokens - they should not generate error events
        if _is_punctuation(ref_token) or _is_punctuation(hyp_token):
            # If both are punctuation and same, mark as correct, otherwise skip
            if (ref_token and hyp_token and 
                _is_punctuation(ref_token) and _is_punctuation(hyp_token) and 
                ref_token == hyp_token):
                event_type = "correct"
                subtype = None
            else:
                # Skip this event entirely for punctuation
                continue
        
        elif op == "equal":
            # Check for normalized equality for equal operations
            if _norm_token(ref_token) == _norm_token(hyp_token):
                # Only case/punctuation difference - treat as correct
                event_type = "correct"
                subtype = "case_punct_only"
            else:
                event_type = "correct"
                subtype = None
        elif op == "delete":
            event_type = "missing"
            subtype = None
        elif op == "insert":
            # Check if this is a repetition based on new algorithm
            # Use alignment index instead of hyp_idx for repetition_map
            alignment_idx = len(word_events)  # Current alignment index
            if hyp_token and alignment_idx in repetition_map and repetition_map[alignment_idx]:
                event_type = "repetition"
                subtype = None
                # Repetition olayları ref'i tüketmez - ref_token'ı null yap
                ref_token = None
            elif check_enhanced_repetition(i, op, ref_token, hyp_token):
                event_type = "repetition"
                subtype = "enhanced_pattern"
                # Repetition olayları ref'i tüketmez - ref_token'ı null yap
                ref_token = None
            elif check_consecutive_extra_repetition(i, alignment):
                event_type = "repetition"
                subtype = "consecutive_extra"
                # Repetition olayları ref'i tüketmez - ref_token'ı null yap
                ref_token = None
            else:
                # Check if this is part of a repetition group
                if hyp_token and hyp_idx >= 0 and hyp_idx < len(hyp_tokens):
                    repetition_info = word_repetitions.get(hyp_idx, {"is_repetition": False})
                    if repetition_info["is_repetition"]:
                        event_type = "repetition"
                        subtype = repetition_info.get("repetition_type")
                        # Repetition olayları ref'i tüketmez - ref_token'ı null yap
                        ref_token = None
                    else:
                        # Check if this extra token is similar to the next token (repetition pattern)
                        # Example: "hiç hiçbir" where "hiç" is extra and similar to next "hiçbir"
                        is_extra_repetition = False
                        if i + 1 < len(alignment):
                            next_op, next_ref, next_hyp, next_ref_idx, next_hyp_idx = alignment[i + 1]
                            if next_hyp and hyp_token:
                                norm_current = _norm_token(hyp_token)
                                norm_next = _norm_token(next_hyp)
                                
                                # Check for exact match
                                if norm_current == norm_next:
                                    is_extra_repetition = True
                                else:
                                    # Check for substring relationships (one is prefix of other)
                                    if (norm_current and len(norm_current) >= 3 and norm_next and 
                                        norm_current in norm_next):
                                        is_extra_repetition = True
                                    elif (norm_next and len(norm_next) >= 3 and norm_current and 
                                          norm_next in norm_current):
                                        is_extra_repetition = True
                                    else:
                                        # Check for high similarity (50%+ threshold)
                                        lev_dist = char_edit_stats(norm_current, norm_next)[0]
                                        max_len = max(len(norm_current), len(norm_next), 1)
                                        similarity = 1.0 - (lev_dist / max_len)
                                        if similarity >= 0.5:  # 50% similarity threshold
                                            is_extra_repetition = True
                        
                        if is_extra_repetition:
                            event_type = "repetition"
                            subtype = "extra_similar_to_next"
                            # Repetition olayları ref'i tüketmez - ref_token'ı null yap
                            ref_token = None
                        else:
                            event_type = "extra"
                            subtype = None
                else:
                    event_type = "extra"
                    subtype = None
        elif op == "replace":
            # Check if this is only punctuation difference
            if _is_punctuation_only_difference(ref_token, hyp_token):
                # Only punctuation difference - treat as correct
                event_type = "correct"
                subtype = "case_punct_only"
            else:
                # Check for "--" pattern first - this should always be repetition regardless of operation type
                if hyp_token and "--" in hyp_token:
                    event_type = "repetition"
                    subtype = "enhanced_pattern"
                    # Repetition olayları ref'i tüketmez - ref_token'ı null yap
                    ref_token = None
                # Check for middle-dash patterns (like "u-üzerindeki")
                elif hyp_token and "-" in hyp_token and not hyp_token.startswith("-") and not hyp_token.endswith("-"):
                    event_type = "repetition"
                    subtype = "enhanced_pattern"
                    # Repetition olayları ref'i tüketmez - ref_token'ı null yap
                    ref_token = None
                # Check for other enhanced repetition patterns
                elif check_enhanced_repetition(i, op, ref_token, hyp_token):
                    event_type = "repetition"
                    subtype = "enhanced_pattern"
                    # Repetition olayları ref'i tüketmez - ref_token'ı null yap
                    ref_token = None
                else:
                    # For replace operations, treat as substitution
                    event_type = "substitution"
                    subtype = classify_replace(ref_token, hyp_token)
                    # Normalize sub_type
                    subtype = normalize_sub_type(subtype)
                    
                    # Calculate char_diff and cer_local for substitutions
                    char_diff = char_edit_stats(ref_token, hyp_token)[0]
                    cer_local = char_diff / max(len(ref_token or ""), 1)
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
    
    # Local post-repair: fix consecutive SUB+MISSING patterns
    word_events = _local_swap_repair(word_events)
    
    return word_events


def _local_swap_repair(word_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Local post-repair to fix consecutive SUB+MISSING patterns.
    For each pair of consecutive events i, i+1:
    if events[i].type == "substitution" and events[i+1].type == "missing":
        let ref_i = events[i].ref_token, hyp = events[i].hyp_token, ref_next = events[i+1].ref_token
        s_bad  = lev_norm(ref_i, hyp)
        s_good = lev_norm(ref_next, hyp)
        if s_bad > 0.5 and s_good <= 0.3:
            // rewrite:
            events[i]   = MISSING(ref_i)
            events[i+1] = SUBSTITUTION(ref_next, hyp) with updated char_diff based on normalized forms
    """
    if len(word_events) < 2:
        return word_events
    
    repaired = word_events.copy()
    i = 0
    
    while i < len(repaired) - 1:
        current = repaired[i]
        next_event = repaired[i + 1]
        
        # Check for SUB+MISSING pattern
        if (current["type"] == "substitution" and 
            next_event["type"] == "missing" and
            current["ref_token"] and 
            current["hyp_token"] and 
            next_event["ref_token"]):
            
            ref_i = current["ref_token"]
            hyp = current["hyp_token"]
            ref_next = next_event["ref_token"]
            
            # Calculate normalized Levenshtein distances
            ref_i_norm = _norm_token(ref_i)
            hyp_norm = _norm_token(hyp)
            ref_next_norm = _norm_token(ref_next)
            
            # s_bad = lev_norm(ref_i, hyp)
            lev_dist_bad = char_edit_stats(ref_i_norm, hyp_norm)[0]
            max_len_bad = max(len(ref_i_norm), len(hyp_norm), 1)
            s_bad = lev_dist_bad / max_len_bad
            
            # s_good = lev_norm(ref_next, hyp)
            lev_dist_good = char_edit_stats(ref_next_norm, hyp_norm)[0]
            max_len_good = max(len(ref_next_norm), len(hyp_norm), 1)
            s_good = lev_dist_good / max_len_good
            
            # Apply repair condition: s_bad > 0.5 and s_good <= 0.3
            if s_bad > 0.5 and s_good <= 0.3:
                # Rewrite events:
                # events[i] = MISSING(ref_i)
                # events[i+1] = SUBSTITUTION(ref_next, hyp)
                
                # Update current event to MISSING
                repaired[i] = {
                    **current,
                    "type": "missing",
                    "sub_type": None,
                    "char_diff": None,
                    "cer_local": None,
                    "hyp_token": None,
                    "hyp_idx": -1
                }
                
                # Update next event to SUBSTITUTION
                char_diff = char_edit_stats(ref_next_norm, hyp_norm)[0]
                cer_local = char_diff / max(len(ref_next_norm), 1)
                subtype = classify_replace(ref_next, hyp)
                subtype = normalize_sub_type(subtype)
                
                repaired[i + 1] = {
                    **next_event,
                    "type": "substitution",
                    "sub_type": subtype,
                    "char_diff": char_diff,
                    "cer_local": cer_local,
                    "hyp_token": hyp,
                    "hyp_idx": current["hyp_idx"]  # Use the original hyp_idx from the substitution
                }
        
        i += 1
    
    return repaired
    