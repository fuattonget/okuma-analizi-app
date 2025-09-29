"""
Text tokenization utilities for Turkish text processing
"""
import re
from typing import List


def tokenize_turkish_text(text: str) -> List[str]:
    """
    Tokenize Turkish text into words, preserving apostrophes and removing punctuation
    
    Normalizes all types of apostrophes to ASCII apostrophe and treats apostrophe as part of word.
    Examples:
        "Nevzat'ın"   → ["Nevzat'ın"]
        "Nevzat'ı"    → ["Nevzat'ı"] 
        "Okulu, ..."  → ["Okulu", ...]   // comma removed
        "öğretmendir."→ ["öğretmendir"]  // period removed
    
    Args:
        text: Input text to tokenize
        
    Returns:
        List of word tokens (no punctuation, apostrophes preserved)
    """
    if not text or not text.strip():
        return []
    
    # Normalize all types of apostrophes to ASCII apostrophe
    # Handle various Unicode apostrophe characters
    text = text.replace(chr(8216), "'")  # U+2018 LEFT SINGLE QUOTATION MARK
    text = text.replace(chr(8217), "'")  # U+2019 RIGHT SINGLE QUOTATION MARK  
    text = text.replace(chr(8218), "'")  # U+201A SINGLE LOW-9 QUOTATION MARK
    text = text.replace(chr(8219), "'")  # U+201B SINGLE HIGH-REVERSED-9 QUOTATION MARK
    text = text.replace(chr(96), "'")    # U+0060 GRAVE ACCENT
    text = text.replace(chr(180), "'")   # U+00B4 ACUTE ACCENT
    
    # Keep original casing and extract words only (no punctuation)
    text = text.strip()
    
    # Turkish word pattern: includes Turkish characters and apostrophes, excludes punctuation
    # Pattern matches: [letters/digits]+(?:'[letters/digits]+)*
    # This ensures apostrophes are part of words when between letters/digits
    # Updated pattern to better handle Turkish apostrophes
    tokens = re.findall(r"[A-Za-zÇĞİÖŞÜÂÎÛçğıöşü0-9]+(?:'[A-Za-zÇĞİÖŞÜÂÎÛçğıöşü0-9]+)*", text)
    
    # Filter out empty strings and very short words (1 char) unless they are common
    common_single_chars = {"a", "e", "i", "ı", "o", "ö", "u", "ü", "A", "E", "I", "İ", "O", "Ö", "U", "Ü"}
    filtered_tokens = []
    
    for token in tokens:
        if len(token) > 1 or token in common_single_chars:
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
    
    # Fix missing apostrophes in Turkish possessive forms
    # Pattern: word + space + possessive suffix
    # Examples: "Onur u" -> "Onur'u", "Onur un" -> "Onur'un"
    possessive_patterns = [
        (r'([A-Za-zÇĞİÖŞÜÂÎÛçğıöşü0-9]+)\s+(ın|in|un|ün|ı|i|u|ü)(?=\s|$|[.,!?;:])', r"\1'\2"),  # possessive suffixes
        (r'([A-Za-zÇĞİÖŞÜÂÎÛçğıöşü0-9]+)\s+(ki|kı|ku|kü)(?=\s|$|[.,!?;:])', r"\1'\2"),  # relative pronoun
    ]
    
    for pattern, replacement in possessive_patterns:
        text = re.sub(pattern, replacement, text)
    
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

