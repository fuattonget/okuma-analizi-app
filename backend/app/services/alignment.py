from typing import List, Dict, Any, Tuple
import re
import unicodedata

# Punctuation characters that should not be substituted
_PUNCTUATION = {'.', ',', '!', '?', ';', ':', '"', '"', '"', "'"}

# Filler/booster words that should be treated as EXTRA when overused
FILLERS = {"çok", "yani", "işte", "şey", "eee", "ııı", "hımm", "falan", "filan", "baya", "hakikaten", "gerçekten"}

# POS heuristics patterns
VERB_PATTERNS = [
    r".*yor$",  # -yor (present continuous)
    r".*dı$", r".*di$", r".*du$", r".*dü$",  # -dı/-di/-du/-dü (past tense)
    r".*acak$", r".*ecek$",  # -acak/-ecek (future tense)
    r".*mış$", r".*miş$", r".*muş$", r".*müş$",  # -mış/-miş/-muş/-müş (perfect tense)
    r".*r$",  # -r (aorist)
    r".*lerdi$", r".*lardı$"  # -lerdi/-lardı (past continuous)
]

NOUN_PATTERNS = [
    r".*lar$", r".*ler$",  # -lar/-ler (plural)
    r".*ı$", r".*i$", r".*u$", r".*ü$",  # -ı/-i/-u/-ü (accusative/possessive)
    r".*da$", r".*de$",  # -da/-de (locative)
    r".*dan$", r".*den$",  # -dan/-den (ablative)
    r".*ın$", r".*in$", r".*un$", r".*ün$",  # -ın/-in/-un/-ün (genitive)
    r".*ım$", r".*im$", r".*um$", r".*üm$"  # -ım/-im/-um/-üm (possessive 1st person)
]

def _is_punctuation(tok: str) -> bool:
    """Check if token is punctuation"""
    return tok in _PUNCTUATION

def _is_filler(tok: str) -> bool:
    """Check if token is a filler/booster word"""
    return _norm_token(tok) in FILLERS

def _is_verb_like(tok: str) -> bool:
    """Check if token looks like a verb based on Turkish morphemes"""
    if not tok:
        return False
    tok_lower = tok.lower()
    return any(re.match(pattern, tok_lower) for pattern in VERB_PATTERNS)

def _is_noun_like(tok: str) -> bool:
    """Check if token looks like a noun based on Turkish morphemes"""
    if not tok:
        return False
    tok_lower = tok.lower()
    return any(re.match(pattern, tok_lower) for pattern in NOUN_PATTERNS)

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

def _get_operation_cost(ref_token: str, hyp_token: str, operation: str, 
                       repeated_fillers: Dict[int, bool] = None, hyp_idx: int = -1) -> float:
    """Get cost for specific operation considering stopwords, fillers, and POS"""
    if operation == "equal":
        return 0.0
    elif operation in ["insert", "delete"]:
        # Base cost
        base_cost = 1.0
        
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
        
        return 1.0
    
    return 1.0

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
    """Normalize token: lowercase + Turkish diacritic normalization + strip punctuation"""
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
    
    # Strip trailing punctuation characters (.,!?;:"")
    t = re.sub(r'[.,!?;:"""]+$', '', t)
    t = re.sub(r'^[.,!?;:"""]+', '', t)
    
    return t


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
            
            # Use normalized comparison for case-insensitive matching
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
                    max_len = max(len(ref_token), len(next_hyp))
                    lev_norm = lev_dist / max_len if max_len > 0 else 1.0
                    
                    if lev_norm <= 0.3:  # High similarity threshold
                        next_similar = True
            else:
                # If no next alignment, check if ref_token matches any future hyp_token
                for j in range(i + 1, len(alignment)):
                    _, _, future_hyp, _, _ = alignment[j]
                    if future_hyp:
                        lev_dist = char_edit_stats(ref_token, future_hyp)[0]
                        max_len = max(len(ref_token), len(future_hyp))
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
        
        # Check for normalized equality for any operation
        elif _norm_token(ref_token) == _norm_token(hyp_token):
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