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
    
    # Add backward compatibility for "diff" field
    counts["diff"] = counts["substitution"]
    
    logger.debug(f"Recomputed counts from {len(word_events)} word events: {counts}")
    return counts