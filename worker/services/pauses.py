from typing import List, Dict, Any


def detect_pauses(words: List[Dict[str, Any]], threshold_ms: int) -> List[Dict[str, Any]]:
    """
    Detect pauses from word timing data for PauseEventDoc
    
    Args:
        words: List of word data with 'start', 'end' keys
        threshold_ms: Minimum pause duration in milliseconds to consider
    
    Returns:
        List of pause events in PauseEventDoc format
    """
    if not words or len(words) < 2:
        return []
    
    pauses = []
    threshold_s = threshold_ms / 1000.0  # Convert to seconds
    
    # Find pauses between consecutive words
    for i in range(len(words) - 1):
        current_word = words[i]
        next_word = words[i + 1]
        
        # Calculate pause duration between words
        pause_start = current_word.get("end", 0)
        pause_end = next_word.get("start", 0)
        pause_duration = pause_end - pause_start
        
        # Only consider pauses longer than threshold
        if pause_duration >= threshold_s:
            pause_duration_ms = pause_duration * 1000
            start_ms = pause_start * 1000
            end_ms = pause_end * 1000
            
            # Classify pause severity
            if pause_duration >= 1.0:  # 1 second or more
                pause_class = "very_long"
            elif pause_duration >= 0.5:  # 0.5-1 second
                pause_class = "long"
            elif pause_duration >= 0.3:  # 0.3-0.5 second
                pause_class = "medium"
            else:  # threshold to 0.3 second
                pause_class = "short"
            
            pause_event = {
                "after_word_idx": i,
                "start_ms": start_ms,
                "end_ms": end_ms,
                "duration_ms": pause_duration_ms,
                "class": pause_class,
                "type": "long_pause"
            }
            pauses.append(pause_event)
    
    return pauses


def detect_pauses_from_elevenlabs(elevenlabs_words: List[Dict[str, Any]], threshold_ms: int) -> List[Dict[str, Any]]:
    """
    Detect pauses from ElevenLabs spacing data (legacy function)
    
    Args:
        elevenlabs_words: List of ElevenLabs word data with 'type', 'start', 'end' keys
        threshold_ms: Minimum pause duration in milliseconds to consider
    
    Returns:
        List of pause events
    """
    if not elevenlabs_words:
        return []
    
    pauses = []
    threshold_s = threshold_ms / 1000.0  # Convert to seconds
    
    # Find all spacing elements
    for i, word_data in enumerate(elevenlabs_words):
        if word_data.get("type") == "spacing":
            # Calculate pause duration
            pause_duration = word_data["end"] - word_data["start"]
            pause_duration_ms = pause_duration * 1000
            
            # Only consider pauses longer than threshold
            if pause_duration >= threshold_s:
                # Find the word index before this spacing
                word_idx = i - 1
                while word_idx >= 0 and elevenlabs_words[word_idx].get("type") != "word":
                    word_idx -= 1
                
                if word_idx >= 0:  # Found a word before this spacing
                    # Classify pause severity
                    if pause_duration >= 1.0:
                        pause_class = "very_long"
                    elif pause_duration >= 0.5:
                        pause_class = "long"
                    elif pause_duration >= 0.3:
                        pause_class = "medium"
                    else:
                        pause_class = "short"
                    
                    pause_event = {
                        "after_word_idx": word_idx,
                        "start_ms": word_data["start"] * 1000,
                        "end_ms": word_data["end"] * 1000,
                        "duration_ms": pause_duration_ms,
                        "class": pause_class,
                        "type": "long_pause"
                    }
                    pauses.append(pause_event)
    
    return pauses