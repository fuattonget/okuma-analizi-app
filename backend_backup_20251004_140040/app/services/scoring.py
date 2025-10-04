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
    Recompute counts from WordEventDoc list
    
    Args:
        word_events: List of WordEventDoc objects or dicts with 'type' field
    
    Returns:
        Dictionary with aggregated counts
    """
    counts = {
        "correct": 0,
        "missing": 0,
        "extra": 0,
        "substitution": 0,  # Changed from "diff" to "substitution"
        "repetition": 0,  # Added repetition counter
        "total_words": 0
    }
    
    for event in word_events:
        # Handle both dict and object access
        if hasattr(event, 'type'):
            event_type = event.type
        elif isinstance(event, dict):
            event_type = event.get('type', 'unknown')
        else:
            continue
        
        counts["total_words"] += 1
        
        if event_type == "correct":
            counts["correct"] += 1
        elif event_type == "missing":
            counts["missing"] += 1
        elif event_type == "extra":
            counts["extra"] += 1
        elif event_type == "substitution":  # Changed from "diff" to "substitution"
            counts["substitution"] += 1
        elif event_type == "repetition":  # Added repetition counter
            counts["repetition"] += 1
    
    # Add backward compatibility for "diff" field
    counts["diff"] = counts["substitution"]
    
    logger.debug(f"Recomputed counts from {len(word_events)} word events: {counts}")
    return counts


def validate_summary_consistency(summary: Dict[str, Any], word_events: List[Any]) -> bool:
    """
    Validate that summary counts are consistent with actual word events
    
    Args:
        summary: Analysis summary dictionary
        word_events: List of word events
    
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