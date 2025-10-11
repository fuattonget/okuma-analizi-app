from typing import Dict, Any, List
from loguru import logger


def compute_metrics(n_ref: int, subs: int, dels: int, ins: int) -> Dict[str, float]:
    """
    Compute WER and Accuracy metrics
    
    Args:
        n_ref: Number of reference tokens
        subs: Number of substitutions
        dels: Number of deletions
        ins: Number of insertions
    
    Returns:
        Dictionary with wer and accuracy
    """
    if n_ref == 0:
        return {"wer": 1.0, "accuracy": 0.0}
    
    wer = (subs + dels + ins) / max(n_ref, 1)
    accuracy = 100.0 * (n_ref - subs - dels) / max(n_ref, 1)
    
    # Log metrics calculation
    logger.info(f"Metrics calculated: n_ref={n_ref}, s={subs}, d={dels}, i={ins}, wer={wer:.3f}, accuracy={accuracy:.1f}%")
    
    return {
        "wer": wer,
        "accuracy": accuracy
    }


def compute_wpm(hyp_count: int, first_ms: float, last_ms: float) -> float:
    """
    Compute Words Per Minute
    
    Args:
        hyp_count: Number of hypothesis tokens
        first_ms: Start time in milliseconds
        last_ms: End time in milliseconds
    
    Returns:
        Words per minute
    """
    if first_ms >= last_ms or hyp_count == 0:
        return 0.0
    
    duration_minutes = (last_ms - first_ms) / (1000 * 60)  # Convert to minutes
    wpm = hyp_count / duration_minutes if duration_minutes > 0 else 0.0
    
    # Log WPM calculation
    logger.info(f"WPM calculated: hyp_count={hyp_count}, first_ms={first_ms:.1f}, last_ms={last_ms:.1f}, wpm={wpm:.1f}")
    
    return wpm


def recompute_counts(word_events: List[Any]) -> Dict[str, int]:
    """
    Recompute counts from WordEventDoc list including sub_type classifications
    
    Args:
        word_events: List of WordEventDoc objects or dicts with 'type' and 'sub_type' fields
    
    Returns:
        Dictionary with aggregated counts including sub_type breakdowns
    """
    counts = {
        # Main type counts
        "correct": 0,
        "missing": 0,
        "extra": 0,
        "substitution": 0,
        "repetition": 0,
        "total_words": 0,
        
        # Sub-type counts for detailed error analysis
        "harf_eksiltme": 0,
        "harf_ekleme": 0,
        "harf_değiştirme": 0,
        "hece_eksiltme": 0,
        "hece_ekleme": 0,
        "kelime_eksiltme": 0,
        "kelime_ekleme": 0,
        "kelime_değiştirme": 0,
        "tekrarlama": 0,
        
        # Pause counts (will be added separately)
        "uzun_duraksama": 0
    }
    
    for event in word_events:
        # Handle both dict and object access
        if hasattr(event, 'type'):
            event_type = event.type
            sub_type = getattr(event, 'sub_type', None)
        elif isinstance(event, dict):
            event_type = event.get('type', 'unknown')
            sub_type = event.get('sub_type', None)
        else:
            continue
        
        counts["total_words"] += 1
        
        # Count main types
        if event_type == "correct":
            counts["correct"] += 1
        elif event_type == "missing":
            counts["missing"] += 1
        elif event_type == "extra":
            counts["extra"] += 1
        elif event_type == "substitution":
            counts["substitution"] += 1
        elif event_type == "repetition":
            counts["repetition"] += 1
        
        # Count sub-types for detailed analysis
        if sub_type:
            if sub_type == "harf_eksiltme":
                counts["harf_eksiltme"] += 1
            elif sub_type == "harf_ekleme":
                counts["harf_ekleme"] += 1
            elif sub_type == "harf_değiştirme":
                counts["harf_değiştirme"] += 1
            elif sub_type == "hece_eksiltme":
                counts["hece_eksiltme"] += 1
            elif sub_type == "hece_ekleme":
                counts["hece_ekleme"] += 1
            elif sub_type == "kelime_eksiltme":
                counts["kelime_eksiltme"] += 1
            elif sub_type == "kelime_ekleme":
                counts["kelime_ekleme"] += 1
            elif sub_type == "kelime_değiştirme":
                counts["kelime_değiştirme"] += 1
            elif sub_type in ["tekrarlama", "repetition", "enhanced_pattern", "consecutive_pattern"]:
                counts["tekrarlama"] += 1
    
    # Add backward compatibility for "diff" field
    counts["diff"] = counts["substitution"]
    
    logger.debug(f"Recomputed counts from {len(word_events)} word events: {counts}")
    return counts

def compute_grade_score(grade: int, counts: Dict[str, int], total_words: int) -> Dict[str, Any]:
    """
    Compute grade-specific scoring based on Turkish reading assessment criteria
    
    Args:
        grade: Student grade level (1, 2, 3, 4, 5, 6, 7, etc.)
        counts: Dictionary with error counts from recompute_counts
        total_words: Total number of words in the text
    
    Returns:
        Dictionary with detailed scoring breakdown and total score
    """
    if grade == 1:
        return _compute_grade_1_score(counts, total_words)
    elif grade == 2:
        return _compute_grade_2_score(counts, total_words)
    elif grade == 3:
        return _compute_grade_3_score(counts, total_words)
    elif grade in [4, 5]:
        return _compute_grade_4_5_score(counts, total_words, grade)
    elif grade in [6, 7]:
        return _compute_grade_6_7_score(counts, total_words, grade)
    else:
        # For other grades (8+), return basic scoring for now
        return _compute_basic_score(counts, total_words)


def _compute_grade_6_7_score(counts: Dict[str, int], total_words: int, grade: int = 6) -> Dict[str, Any]:
    """
    Compute 6th and 7th grade scoring based on the provided criteria
    Total: 100 points (50 for correct words + 50 for error types)
    """
    
    # 1. Doğru Okunan Kelime Sayısı (50 points max) - 6. ve 7. sınıf için en yüksek beklenti
    correct_words = counts.get("correct", 0)
    correct_score = _score_correct_words_grade_6_7(correct_words)
    
    # 2. Harf Eksiltme (5 points max)
    harf_eksiltme_count = counts.get("harf_eksiltme", 0)
    harf_eksiltme_score = _score_error_count_grade_1_harf(harf_eksiltme_count)  # Same as grade 1
    
    # 3. Harf Ekleme (5 points max)
    harf_ekleme_count = counts.get("harf_ekleme", 0)
    harf_ekleme_score = _score_error_count_grade_1_harf(harf_ekleme_count)  # Same as grade 1
    
    # 4. Harf Değiştirme (5 points max)
    harf_değiştirme_count = counts.get("harf_değiştirme", 0)
    harf_değiştirme_score = _score_error_count_grade_1_harf(harf_değiştirme_count)  # Same as grade 1
    
    # 5. Hece Eksiltme (5 points max)
    hece_eksiltme_count = counts.get("hece_eksiltme", 0)
    hece_eksiltme_score = _score_error_count_grade_1_hece(hece_eksiltme_count)  # Same as grade 1
    
    # 6. Hece Ekleme (5 points max)
    hece_ekleme_count = counts.get("hece_ekleme", 0)
    hece_ekleme_score = _score_error_count_grade_1_hece(hece_ekleme_count)  # Same as grade 1
    
    # 7. Kelime Eksiltme (5 points max)
    kelime_eksiltme_count = counts.get("missing", 0)  # missing = kelime eksiltme
    kelime_eksiltme_score = _score_error_count_grade_1_kelime(kelime_eksiltme_count)  # Same as grade 1
    
    # 8. Kelime Ekleme (5 points max)
    kelime_ekleme_count = counts.get("extra", 0)  # extra = kelime ekleme
    kelime_ekleme_score = _score_error_count_grade_1_kelime(kelime_ekleme_count)  # Same as grade 1
    
    # 9. Kelime Değiştirme (5 points max)
    kelime_değiştirme_count = counts.get("kelime_değiştirme", 0)
    kelime_değiştirme_score = _score_error_count_grade_1_kelime(kelime_değiştirme_count)  # Same as grade 1
    
    # 10. Kelime Tanıma (Uzun Duraksama) (5 points max)
    uzun_duraksama_count = counts.get("uzun_duraksama", 0)
    uzun_duraksama_score = _score_error_count_grade_1_pause(uzun_duraksama_count)  # Same as grade 1
    
    # 11. Tekrarlama (5 points max)
    tekrarlama_count = counts.get("tekrarlama", 0)
    tekrarlama_score = _score_error_count_grade_1_pause(tekrarlama_count)
    
    # Calculate total score
    total_score = (correct_score + harf_eksiltme_score + harf_ekleme_score + 
                   harf_değiştirme_score + hece_eksiltme_score + hece_ekleme_score +
                   kelime_eksiltme_score + kelime_ekleme_score + kelime_değiştirme_score +
                   uzun_duraksama_score + tekrarlama_score)
    
    return {
        "grade": grade,  # Actual grade (6 or 7)
        "total_score": total_score,
        "max_score": 100,
        "score_percentage": round((total_score / 100) * 100, 1),
        "breakdown": {
            "doğru_kelime": {
                "count": correct_words,
                "score": correct_score,
                "max_score": 50
            },
            "harf_eksiltme": {
                "count": harf_eksiltme_count,
                "score": harf_eksiltme_score,
                "max_score": 5
            },
            "harf_ekleme": {
                "count": harf_ekleme_count,
                "score": harf_ekleme_score,
                "max_score": 5
            },
            "harf_değiştirme": {
                "count": harf_değiştirme_count,
                "score": harf_değiştirme_score,
                "max_score": 5
            },
            "hece_eksiltme": {
                "count": hece_eksiltme_count,
                "score": hece_eksiltme_score,
                "max_score": 5
            },
            "hece_ekleme": {
                "count": hece_ekleme_count,
                "score": hece_ekleme_score,
                "max_score": 5
            },
            "kelime_eksiltme": {
                "count": kelime_eksiltme_count,
                "score": kelime_eksiltme_score,
                "max_score": 5
            },
            "kelime_ekleme": {
                "count": kelime_ekleme_count,
                "score": kelime_ekleme_score,
                "max_score": 5
            },
            "kelime_değiştirme": {
                "count": kelime_değiştirme_count,
                "score": kelime_değiştirme_score,
                "max_score": 5
            },
            "uzun_duraksama": {
                "count": uzun_duraksama_count,
                "score": uzun_duraksama_score,
                "max_score": 5
            },
            "tekrarlama": {
                "count": tekrarlama_count,
                "score": tekrarlama_score,
                "max_score": 5
            }
        }
    }


def _compute_grade_4_5_score(counts: Dict[str, int], total_words: int, grade: int = 4) -> Dict[str, Any]:
    """
    Compute 4th and 5th grade scoring based on the provided criteria
    Total: 100 points (50 for correct words + 50 for error types)
    """
    
    # 1. Doğru Okunan Kelime Sayısı (50 points max) - 4. ve 5. sınıf için en yüksek beklenti
    correct_words = counts.get("correct", 0)
    correct_score = _score_correct_words_grade_4_5(correct_words)
    
    # 2. Harf Eksiltme (5 points max)
    harf_eksiltme_count = counts.get("harf_eksiltme", 0)
    harf_eksiltme_score = _score_error_count_grade_1_harf(harf_eksiltme_count)  # Same as grade 1
    
    # 3. Harf Ekleme (5 points max)
    harf_ekleme_count = counts.get("harf_ekleme", 0)
    harf_ekleme_score = _score_error_count_grade_1_harf(harf_ekleme_count)  # Same as grade 1
    
    # 4. Harf Değiştirme (5 points max)
    harf_değiştirme_count = counts.get("harf_değiştirme", 0)
    harf_değiştirme_score = _score_error_count_grade_1_harf(harf_değiştirme_count)  # Same as grade 1
    
    # 5. Hece Eksiltme (5 points max)
    hece_eksiltme_count = counts.get("hece_eksiltme", 0)
    hece_eksiltme_score = _score_error_count_grade_1_hece(hece_eksiltme_count)  # Same as grade 1
    
    # 6. Hece Ekleme (5 points max)
    hece_ekleme_count = counts.get("hece_ekleme", 0)
    hece_ekleme_score = _score_error_count_grade_1_hece(hece_ekleme_count)  # Same as grade 1
    
    # 7. Kelime Eksiltme (5 points max)
    kelime_eksiltme_count = counts.get("missing", 0)  # missing = kelime eksiltme
    kelime_eksiltme_score = _score_error_count_grade_1_kelime(kelime_eksiltme_count)  # Same as grade 1
    
    # 8. Kelime Ekleme (5 points max)
    kelime_ekleme_count = counts.get("extra", 0)  # extra = kelime ekleme
    kelime_ekleme_score = _score_error_count_grade_1_kelime(kelime_ekleme_count)  # Same as grade 1
    
    # 9. Kelime Değiştirme (5 points max)
    kelime_değiştirme_count = counts.get("kelime_değiştirme", 0)
    kelime_değiştirme_score = _score_error_count_grade_1_kelime(kelime_değiştirme_count)  # Same as grade 1
    
    # 10. Kelime Tanıma (Uzun Duraksama) (5 points max)
    uzun_duraksama_count = counts.get("uzun_duraksama", 0)
    uzun_duraksama_score = _score_error_count_grade_1_pause(uzun_duraksama_count)  # Same as grade 1
    
    # 11. Tekrarlama (5 points max)
    tekrarlama_count = counts.get("tekrarlama", 0)
    tekrarlama_score = _score_error_count_grade_1_pause(tekrarlama_count)
    
    # Calculate total score
    total_score = (correct_score + harf_eksiltme_score + harf_ekleme_score + 
                   harf_değiştirme_score + hece_eksiltme_score + hece_ekleme_score +
                   kelime_eksiltme_score + kelime_ekleme_score + kelime_değiştirme_score +
                   uzun_duraksama_score + tekrarlama_score)
    
    return {
        "grade": grade,  # Actual grade (4 or 5)
        "total_score": total_score,
        "max_score": 100,
        "score_percentage": round((total_score / 100) * 100, 1),
        "breakdown": {
            "doğru_kelime": {
                "count": correct_words,
                "score": correct_score,
                "max_score": 50
            },
            "harf_eksiltme": {
                "count": harf_eksiltme_count,
                "score": harf_eksiltme_score,
                "max_score": 5
            },
            "harf_ekleme": {
                "count": harf_ekleme_count,
                "score": harf_ekleme_score,
                "max_score": 5
            },
            "harf_değiştirme": {
                "count": harf_değiştirme_count,
                "score": harf_değiştirme_score,
                "max_score": 5
            },
            "hece_eksiltme": {
                "count": hece_eksiltme_count,
                "score": hece_eksiltme_score,
                "max_score": 5
            },
            "hece_ekleme": {
                "count": hece_ekleme_count,
                "score": hece_ekleme_score,
                "max_score": 5
            },
            "kelime_eksiltme": {
                "count": kelime_eksiltme_count,
                "score": kelime_eksiltme_score,
                "max_score": 5
            },
            "kelime_ekleme": {
                "count": kelime_ekleme_count,
                "score": kelime_ekleme_score,
                "max_score": 5
            },
            "kelime_değiştirme": {
                "count": kelime_değiştirme_count,
                "score": kelime_değiştirme_score,
                "max_score": 5
            },
            "uzun_duraksama": {
                "count": uzun_duraksama_count,
                "score": uzun_duraksama_score,
                "max_score": 5
            },
            "tekrarlama": {
                "count": tekrarlama_count,
                "score": tekrarlama_score,
                "max_score": 5
            }
        }
    }


def _compute_grade_3_score(counts: Dict[str, int], total_words: int) -> Dict[str, Any]:
    """
    Compute 3rd grade scoring based on the provided criteria
    Total: 100 points (50 for correct words + 50 for error types)
    """
    
    # 1. Doğru Okunan Kelime Sayısı (50 points max) - 3. sınıf için en yüksek beklenti
    correct_words = counts.get("correct", 0)
    correct_score = _score_correct_words_grade_3(correct_words)
    
    # 2. Harf Eksiltme (5 points max)
    harf_eksiltme_count = counts.get("harf_eksiltme", 0)
    harf_eksiltme_score = _score_error_count_grade_1_harf(harf_eksiltme_count)  # Same as grade 1
    
    # 3. Harf Ekleme (5 points max)
    harf_ekleme_count = counts.get("harf_ekleme", 0)
    harf_ekleme_score = _score_error_count_grade_1_harf(harf_ekleme_count)  # Same as grade 1
    
    # 4. Harf Değiştirme (5 points max)
    harf_değiştirme_count = counts.get("harf_değiştirme", 0)
    harf_değiştirme_score = _score_error_count_grade_1_harf(harf_değiştirme_count)  # Same as grade 1
    
    # 5. Hece Eksiltme (5 points max)
    hece_eksiltme_count = counts.get("hece_eksiltme", 0)
    hece_eksiltme_score = _score_error_count_grade_1_hece(hece_eksiltme_count)  # Same as grade 1
    
    # 6. Hece Ekleme (5 points max)
    hece_ekleme_count = counts.get("hece_ekleme", 0)
    hece_ekleme_score = _score_error_count_grade_1_hece(hece_ekleme_count)  # Same as grade 1
    
    # 7. Kelime Eksiltme (5 points max)
    kelime_eksiltme_count = counts.get("missing", 0)  # missing = kelime eksiltme
    kelime_eksiltme_score = _score_error_count_grade_1_kelime(kelime_eksiltme_count)  # Same as grade 1
    
    # 8. Kelime Ekleme (5 points max)
    kelime_ekleme_count = counts.get("extra", 0)  # extra = kelime ekleme
    kelime_ekleme_score = _score_error_count_grade_1_kelime(kelime_ekleme_count)  # Same as grade 1
    
    # 9. Kelime Değiştirme (5 points max)
    kelime_değiştirme_count = counts.get("kelime_değiştirme", 0)
    kelime_değiştirme_score = _score_error_count_grade_1_kelime(kelime_değiştirme_count)  # Same as grade 1
    
    # 10. Kelime Tanıma (Uzun Duraksama) (5 points max)
    uzun_duraksama_count = counts.get("uzun_duraksama", 0)
    uzun_duraksama_score = _score_error_count_grade_1_pause(uzun_duraksama_count)  # Same as grade 1
    
    # 11. Tekrarlama (5 points max)
    tekrarlama_count = counts.get("tekrarlama", 0)
    tekrarlama_score = _score_error_count_grade_1_pause(tekrarlama_count)
    
    # Calculate total score
    total_score = (correct_score + harf_eksiltme_score + harf_ekleme_score + 
                   harf_değiştirme_score + hece_eksiltme_score + hece_ekleme_score +
                   kelime_eksiltme_score + kelime_ekleme_score + kelime_değiştirme_score +
                   uzun_duraksama_score + tekrarlama_score)
    
    return {
        "grade": 3,
        "total_score": total_score,
        "max_score": 100,
        "score_percentage": round((total_score / 100) * 100, 1),
        "breakdown": {
            "doğru_kelime": {
                "count": correct_words,
                "score": correct_score,
                "max_score": 50
            },
            "harf_eksiltme": {
                "count": harf_eksiltme_count,
                "score": harf_eksiltme_score,
                "max_score": 5
            },
            "harf_ekleme": {
                "count": harf_ekleme_count,
                "score": harf_ekleme_score,
                "max_score": 5
            },
            "harf_değiştirme": {
                "count": harf_değiştirme_count,
                "score": harf_değiştirme_score,
                "max_score": 5
            },
            "hece_eksiltme": {
                "count": hece_eksiltme_count,
                "score": hece_eksiltme_score,
                "max_score": 5
            },
            "hece_ekleme": {
                "count": hece_ekleme_count,
                "score": hece_ekleme_score,
                "max_score": 5
            },
            "kelime_eksiltme": {
                "count": kelime_eksiltme_count,
                "score": kelime_eksiltme_score,
                "max_score": 5
            },
            "kelime_ekleme": {
                "count": kelime_ekleme_count,
                "score": kelime_ekleme_score,
                "max_score": 5
            },
            "kelime_değiştirme": {
                "count": kelime_değiştirme_count,
                "score": kelime_değiştirme_score,
                "max_score": 5
            },
            "uzun_duraksama": {
                "count": uzun_duraksama_count,
                "score": uzun_duraksama_score,
                "max_score": 5
            },
            "tekrarlama": {
                "count": tekrarlama_count,
                "score": tekrarlama_score,
                "max_score": 5
            }
        }
    }


    """
    Compute 2nd grade scoring based on the provided criteria
    Total: 100 points (50 for correct words + 50 for error types)
    """
    
    # 1. Doğru Okunan Kelime Sayısı (50 points max) - 2. sınıf için daha yüksek beklenti
    correct_words = counts.get("correct", 0)
    correct_score = _score_correct_words_grade_2(correct_words)
    
    # 2. Harf Eksiltme (5 points max)
    harf_eksiltme_count = counts.get("harf_eksiltme", 0)
    harf_eksiltme_score = _score_error_count_grade_1_harf(harf_eksiltme_count)  # Same as grade 1
    
    # 3. Harf Ekleme (5 points max)
    harf_ekleme_count = counts.get("harf_ekleme", 0)
    harf_ekleme_score = _score_error_count_grade_1_harf(harf_ekleme_count)  # Same as grade 1
    
    # 4. Harf Değiştirme (5 points max)
    harf_değiştirme_count = counts.get("harf_değiştirme", 0)
    harf_değiştirme_score = _score_error_count_grade_1_harf(harf_değiştirme_count)  # Same as grade 1
    
    # 5. Hece Eksiltme (5 points max)
    hece_eksiltme_count = counts.get("hece_eksiltme", 0)
    hece_eksiltme_score = _score_error_count_grade_1_hece(hece_eksiltme_count)  # Same as grade 1
    
    # 6. Hece Ekleme (5 points max)
    hece_ekleme_count = counts.get("hece_ekleme", 0)
    hece_ekleme_score = _score_error_count_grade_1_hece(hece_ekleme_count)  # Same as grade 1
    
    # 7. Kelime Eksiltme (5 points max)
    kelime_eksiltme_count = counts.get("missing", 0)  # missing = kelime eksiltme
    kelime_eksiltme_score = _score_error_count_grade_1_kelime(kelime_eksiltme_count)  # Same as grade 1
    
    # 8. Kelime Ekleme (5 points max)
    kelime_ekleme_count = counts.get("extra", 0)  # extra = kelime ekleme
    kelime_ekleme_score = _score_error_count_grade_1_kelime(kelime_ekleme_count)  # Same as grade 1
    
    # 9. Kelime Değiştirme (5 points max)
    kelime_değiştirme_count = counts.get("kelime_değiştirme", 0)
    kelime_değiştirme_score = _score_error_count_grade_1_kelime(kelime_değiştirme_count)  # Same as grade 1
    
    # 10. Kelime Tanıma (Uzun Duraksama) (5 points max)
    uzun_duraksama_count = counts.get("uzun_duraksama", 0)
    uzun_duraksama_score = _score_error_count_grade_1_pause(uzun_duraksama_count)  # Same as grade 1
    
    # 11. Tekrarlama (5 points max)
    tekrarlama_count = counts.get("tekrarlama", 0)
    tekrarlama_score = _score_error_count_grade_1_pause(tekrarlama_count)
    
    # Calculate total score
    total_score = (correct_score + harf_eksiltme_score + harf_ekleme_score + 
                   harf_değiştirme_score + hece_eksiltme_score + hece_ekleme_score +
                   kelime_eksiltme_score + kelime_ekleme_score + kelime_değiştirme_score +
                   uzun_duraksama_score + tekrarlama_score)
    
    return {
        "grade": 2,
        "total_score": total_score,
        "max_score": 100,
        "score_percentage": round((total_score / 100) * 100, 1),
        "breakdown": {
            "doğru_kelime": {
                "count": correct_words,
                "score": correct_score,
                "max_score": 50
            },
            "harf_eksiltme": {
                "count": harf_eksiltme_count,
                "score": harf_eksiltme_score,
                "max_score": 5
            },
            "harf_ekleme": {
                "count": harf_ekleme_count,
                "score": harf_ekleme_score,
                "max_score": 5
            },
            "harf_değiştirme": {
                "count": harf_değiştirme_count,
                "score": harf_değiştirme_score,
                "max_score": 5
            },
            "hece_eksiltme": {
                "count": hece_eksiltme_count,
                "score": hece_eksiltme_score,
                "max_score": 5
            },
            "hece_ekleme": {
                "count": hece_ekleme_count,
                "score": hece_ekleme_score,
                "max_score": 5
            },
            "kelime_eksiltme": {
                "count": kelime_eksiltme_count,
                "score": kelime_eksiltme_score,
                "max_score": 5
            },
            "kelime_ekleme": {
                "count": kelime_ekleme_count,
                "score": kelime_ekleme_score,
                "max_score": 5
            },
            "kelime_değiştirme": {
                "count": kelime_değiştirme_count,
                "score": kelime_değiştirme_score,
                "max_score": 5
            },
            "uzun_duraksama": {
                "count": uzun_duraksama_count,
                "score": uzun_duraksama_score,
                "max_score": 5
            },
            "tekrarlama": {
                "count": tekrarlama_count,
                "score": tekrarlama_score,
                "max_score": 5
            }
        }
    }


    """
    Compute 1st grade scoring based on the provided criteria
    Total: 100 points (50 for correct words + 50 for error types)
    """
    
    # 1. Doğru Okunan Kelime Sayısı (50 points max)
    correct_words = counts.get("correct", 0)
    correct_score = _score_correct_words_grade_1(correct_words)
    
    # 2. Harf Eksiltme (5 points max)
    harf_eksiltme_count = counts.get("harf_eksiltme", 0)
    harf_eksiltme_score = _score_error_count_grade_1_harf(harf_eksiltme_count)
    
    # 3. Harf Ekleme (5 points max)
    harf_ekleme_count = counts.get("harf_ekleme", 0)
    harf_ekleme_score = _score_error_count_grade_1_harf(harf_ekleme_count)
    
    # 4. Harf Değiştirme (5 points max)
    harf_değiştirme_count = counts.get("harf_değiştirme", 0)
    harf_değiştirme_score = _score_error_count_grade_1_harf(harf_değiştirme_count)
    
    # 5. Hece Eksiltme (5 points max)
    hece_eksiltme_count = counts.get("hece_eksiltme", 0)
    hece_eksiltme_score = _score_error_count_grade_1_hece(hece_eksiltme_count)
    
    # 6. Hece Ekleme (5 points max)
    hece_ekleme_count = counts.get("hece_ekleme", 0)
    hece_ekleme_score = _score_error_count_grade_1_hece(hece_ekleme_count)
    
    # 7. Kelime Eksiltme (5 points max)
    kelime_eksiltme_count = counts.get("missing", 0)  # missing = kelime eksiltme
    kelime_eksiltme_score = _score_error_count_grade_1_kelime(kelime_eksiltme_count)
    
    # 8. Kelime Ekleme (5 points max)
    kelime_ekleme_count = counts.get("extra", 0)  # extra = kelime ekleme
    kelime_ekleme_score = _score_error_count_grade_1_kelime(kelime_ekleme_count)
    
    # 9. Kelime Değiştirme (5 points max)
    kelime_değiştirme_count = counts.get("kelime_değiştirme", 0)
    kelime_değiştirme_score = _score_error_count_grade_1_kelime(kelime_değiştirme_count)
    
    # 10. Kelime Tanıma (Uzun Duraksama) (5 points max)
    uzun_duraksama_count = counts.get("uzun_duraksama", 0)
    uzun_duraksama_score = _score_error_count_grade_1_pause(uzun_duraksama_count)
    
    # 11. Tekrarlama (5 points max)
    tekrarlama_count = counts.get("tekrarlama", 0)
    tekrarlama_score = _score_error_count_grade_1_pause(tekrarlama_count)
    
    # Calculate total score
    total_score = (correct_score + harf_eksiltme_score + harf_ekleme_score + 
                   harf_değiştirme_score + hece_eksiltme_score + hece_ekleme_score +
                   kelime_eksiltme_score + kelime_ekleme_score + kelime_değiştirme_score +
                   uzun_duraksama_score + tekrarlama_score)
    
    return {
        "grade": 1,
        "total_score": total_score,
        "max_score": 100,
        "score_percentage": round((total_score / 100) * 100, 1),
        "breakdown": {
            "doğru_kelime": {
                "count": correct_words,
                "score": correct_score,
                "max_score": 50
            },
            "harf_eksiltme": {
                "count": harf_eksiltme_count,
                "score": harf_eksiltme_score,
                "max_score": 5
            },
            "harf_ekleme": {
                "count": harf_ekleme_count,
                "score": harf_ekleme_score,
                "max_score": 5
            },
            "harf_değiştirme": {
                "count": harf_değiştirme_count,
                "score": harf_değiştirme_score,
                "max_score": 5
            },
            "hece_eksiltme": {
                "count": hece_eksiltme_count,
                "score": hece_eksiltme_score,
                "max_score": 5
            },
            "hece_ekleme": {
                "count": hece_ekleme_count,
                "score": hece_ekleme_score,
                "max_score": 5
            },
            "kelime_eksiltme": {
                "count": kelime_eksiltme_count,
                "score": kelime_eksiltme_score,
                "max_score": 5
            },
            "kelime_ekleme": {
                "count": kelime_ekleme_count,
                "score": kelime_ekleme_score,
                "max_score": 5
            },
            "kelime_değiştirme": {
                "count": kelime_değiştirme_count,
                "score": kelime_değiştirme_score,
                "max_score": 5
            },
            "uzun_duraksama": {
                "count": uzun_duraksama_count,
                "score": uzun_duraksama_score,
                "max_score": 5
            },
            "tekrarlama": {
                "count": tekrarlama_count,
                "score": tekrarlama_score,
                "max_score": 5
            }
        }
    }


def _score_correct_words_grade_1(correct_count: int) -> int:
    """Score correct words for grade 1 (50 points max)"""
    if correct_count > 85:
        return 50
    elif correct_count >= 80:
        return 40
    elif correct_count >= 70:
        return 30
    elif correct_count >= 50:
        return 20
    elif correct_count >= 40:
        return 10
    else:
        return 0


def _score_correct_words_grade_2(correct_count: int) -> int:
    """Score correct words for grade 2 (50 points max) - Higher expectations"""
    if correct_count > 115:
        return 50
    elif correct_count >= 110:
        return 40
    elif correct_count >= 100:
        return 30
    elif correct_count >= 75:
        return 20
    elif correct_count >= 50:
        return 10
    else:
        return 0


def _score_correct_words_grade_3(correct_count: int) -> int:
    """Score correct words for grade 3 (50 points max) - Highest expectations"""
    if correct_count > 135:
        return 50
    elif correct_count >= 125:
        return 40
    elif correct_count >= 115:
        return 30
    elif correct_count >= 100:
        return 20
    elif correct_count >= 75:
        return 10
    else:
        return 0


def _score_correct_words_grade_4_5(correct_count: int) -> int:
    """Score correct words for grades 4 and 5 (50 points max) - Highest expectations"""
    if correct_count > 170:
        return 50
    elif correct_count >= 160:
        return 30  # Note: 160-170 and 150-160 both get 30 points
    elif correct_count >= 150:
        return 30
    elif correct_count >= 130:
        return 20
    elif correct_count >= 110:
        return 10
    else:
        return 0


def _score_correct_words_grade_6_7(correct_count: int) -> int:
    """Score correct words for grades 6 and 7 (50 points max) - Highest expectations"""
    if correct_count > 215:
        return 50
    elif correct_count >= 210:
        return 40
    elif correct_count >= 200:
        return 30
    elif correct_count >= 180:
        return 20
    elif correct_count >= 150:
        return 10
    else:
        return 0


def _score_error_count_grade_1_harf(error_count: int) -> int:
    """Score harf-level errors for grade 1 (5 points max)"""
    if error_count <= 3:
        return 5
    elif error_count <= 5:
        return 4
    elif error_count <= 8:
        return 3
    elif error_count <= 12:
        return 2
    elif error_count <= 20:
        return 1
    else:
        return 0


def _score_error_count_grade_1_hece(error_count: int) -> int:
    """Score hece-level errors for grade 1 (5 points max)"""
    if error_count <= 2:
        return 5
    elif error_count <= 5:
        return 4
    elif error_count <= 8:
        return 3
    elif error_count <= 12:
        return 2
    elif error_count <= 20:
        return 1
    else:
        return 0


def _score_error_count_grade_1_kelime(error_count: int) -> int:
    """Score kelime-level errors for grade 1 (5 points max)"""
    if error_count <= 2:
        return 5
    elif error_count <= 4:
        return 4
    elif error_count <= 6:
        return 3
    elif error_count <= 8:
        return 2
    elif error_count <= 10:
        return 1
    else:
        return 0


def _score_error_count_grade_1_pause(error_count: int) -> int:
    """Score pause/repetition errors for grade 1 (5 points max)"""
    if error_count <= 3:
        return 5
    elif error_count <= 6:
        return 4
    elif error_count <= 10:
        return 3
    elif error_count <= 15:
        return 2
    elif error_count <= 20:
        return 1
    else:
        return 0


def _compute_basic_score(counts: Dict[str, int], total_words: int) -> Dict[str, Any]:
    """Basic scoring for grades other than 1 (placeholder)"""
    correct_words = counts.get("correct", 0)
    accuracy = (correct_words / max(total_words, 1)) * 100
    
    return {
        "grade": "other",
        "total_score": round(accuracy, 1),
        "max_score": 100,
        "score_percentage": round(accuracy, 1),
        "breakdown": {
            "accuracy": {
                "count": correct_words,
                "score": round(accuracy, 1),
                "max_score": 100
            }
        }
    }


def validate_summary_consistency(summary: Dict[str, Any], word_events: List[Any]) -> bool:
    """
    Validate that summary counts are consistent with word events
    
    Args:
        summary: Summary dictionary containing counts
        word_events: List of word event objects
    
    Returns:
        True if consistent, False otherwise
    """
    if not summary or not word_events:
        return True
    
    counts = summary.get("counts", {})
    error_types = summary.get("error_types", {})
    
    # Recompute counts from events
    actual_counts = recompute_counts(word_events)
    
    # Check consistency
    expected_correct = actual_counts.get("correct", 0)
    expected_missing = actual_counts.get("missing", 0)
    expected_extra = actual_counts.get("extra", 0)
    expected_substitution = actual_counts.get("substitution", 0)
    expected_total = actual_counts.get("total_words", 0)
    
    # Validate counts
    if counts.get("correct", 0) != expected_correct:
        logger.warning(f"Count mismatch: correct {counts.get('correct', 0)} != {expected_correct}")
        return False
    
    if counts.get("missing", 0) != expected_missing:
        logger.warning(f"Count mismatch: missing {counts.get('missing', 0)} != {expected_missing}")
        return False
    
    if counts.get("extra", 0) != expected_extra:
        logger.warning(f"Count mismatch: extra {counts.get('extra', 0)} != {expected_extra}")
        return False
    
    if counts.get("substitution", 0) != expected_substitution:
        logger.warning(f"Count mismatch: substitution {counts.get('substitution', 0)} != {expected_substitution}")
        return False
    
    # Validate error_types
    if error_types.get("substitution", 0) != expected_substitution:
        logger.warning(f"Error type mismatch: substitution {error_types.get('substitution', 0)} != {expected_substitution}")
        return False
    
    logger.debug("Summary consistency validation passed")
    return True