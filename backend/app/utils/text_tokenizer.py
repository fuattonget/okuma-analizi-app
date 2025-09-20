"""
Text tokenization utilities for Turkish text processing
"""
import re
from typing import List


def tokenize_turkish_text(text: str) -> List[str]:
    """
    Tokenize Turkish text into words using regex pattern
    
    Args:
        text: Input text to tokenize
        
    Returns:
        List of tokens (words and punctuation)
    """
    if not text or not text.strip():
        return []
    
    # Keep original casing and extract words and punctuation
    text = text.strip()
    
    # Turkish word pattern: includes Turkish characters, apostrophes, and punctuation
    # This pattern matches Turkish words including çğıöşüâîû characters, apostrophes, and punctuation
    tokens = re.findall(r"[a-zA-ZçğıöşüâîûÇĞIİÖŞÜÂÎÛ']+|[.,!?;:\"\"„…]+", text)
    
    # Filter out empty strings and very short words (1 char) unless they are common or punctuation
    common_single_chars = {"a", "e", "i", "ı", "o", "ö", "u", "ü"}
    punctuation_chars = {",", ".", "!", "?", ";", ":", '"', '"', "„", "…"}
    filtered_tokens = []
    
    for token in tokens:
        if len(token) > 1 or token in common_single_chars or token in punctuation_chars:
            filtered_tokens.append(token)
    
    return filtered_tokens


def normalize_turkish_text(text: str) -> str:
    """
    Normalize Turkish text for consistent processing
    
    Args:
        text: Input text to normalize
        
    Returns:
        Normalized text with preserved punctuation and apostrophes
    """
    if not text:
        return ""
    
    # Remove extra whitespace but preserve punctuation and apostrophes
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Normalize spacing around punctuation but keep the punctuation
    text = re.sub(r'\s*([.,!?;:])', r'\1', text)  # Remove space before punctuation
    text = re.sub(r'([.,!?;:])\s*', r'\1 ', text)  # Ensure space after punctuation
    
    return text


def validate_tokenized_words(words: List[str]) -> List[str]:
    """
    Validate and clean tokenized words
    
    Args:
        words: List of tokenized words
        
    Returns:
        Cleaned and validated words
    """
    if not words:
        return []
    
    cleaned_words = []
    for word in words:
        # Remove empty strings and very short words
        if word and len(word.strip()) > 0:
            cleaned_word = word.strip()
            if len(cleaned_word) > 1 or cleaned_word in {"a", "e", "i", "ı", "o", "ö", "u", "ü"}:
                cleaned_words.append(cleaned_word)
    
    return cleaned_words


def get_word_count(text: str) -> int:
    """
    Get word count for a text
    
    Args:
        text: Input text
        
    Returns:
        Word count
    """
    words = tokenize_turkish_text(text)
    return len(words)


def get_reading_time_estimate(text: str, wpm: int = 200) -> float:
    """
    Estimate reading time in minutes
    
    Args:
        text: Input text
        wpm: Words per minute (default 200 for Turkish)
        
    Returns:
        Estimated reading time in minutes
    """
    word_count = get_word_count(text)
    return word_count / wpm

