from typing import List, Dict, Any


def detect_pauses(word_times: List[Dict[str, Any]], threshold_ms: int) -> List[Dict[str, Any]]:
    """
    Detect pauses between words based on threshold
    
    Args:
        word_times: List of word timing data with 'start' and 'end' keys
        threshold_ms: Minimum pause duration in milliseconds to consider
    
    Returns:
        List of pause events
    """
    if not word_times or len(word_times) < 2:
        return []
    
    pauses = []
    threshold_s = threshold_ms / 1000.0  # Convert to seconds
    
    for i in range(len(word_times) - 1):
        current_word = word_times[i]
        next_word = word_times[i + 1]
        
        # Calculate pause duration
        pause_duration = next_word["start"] - current_word["end"]
        
        # Only consider pauses longer than threshold
        if pause_duration >= threshold_s:
            pauses.append({
                "after_word_idx": i,
                "start_ms": current_word["end"] * 1000,
                "end_ms": next_word["start"] * 1000,
                "duration_ms": pause_duration * 1000
            })
    
    return pauses