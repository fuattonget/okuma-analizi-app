"""
ElevenLabs Speech-to-Text API integration
"""
from random import seed
import requests
import tempfile
import os
import time
from typing import Dict, List, Any, Optional
from loguru import logger


class ElevenLabsSTT:
    """ElevenLabs Speech-to-Text API client"""
    
    def __init__(self, api_key: str, model: str = "scribe_v1", seed: int = 12456, language: str = "tr", temperature: float = 0.0):
        self.api_key = api_key
        self.model = model
        self.language = language        
        self.temperature = temperature
        self.seed = seed
        self.base_url = "https://api.elevenlabs.io/v1/speech-to-text"
    
    def transcribe_file(self, file_path: str) -> Dict[str, Any]:
        """
        Transcribe audio file using ElevenLabs API with retry mechanism
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Dictionary with transcription results
        """
        max_retries = 3
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Starting ElevenLabs transcription for file: {file_path} (attempt {attempt + 1}/{max_retries})")
                
                # Prepare headers
                headers = {
                    "xi-api-key": self.api_key
                }
                
                # Prepare form data
                form_data = {
                    "model_id": self.model,
                    "language_code": self.language,
                    "timestamps_granularity": "character",  # Character-level timestamps
                    "tag_audio_events": "false",  # Disable audio events
                    "diarize": "false",
                    "temperature": str(self.temperature),
                    "seed": self.seed # random seed for reproducibility
                }
                
                # Prepare file
                with open(file_path, 'rb') as audio_file:
                    files = {
                        'file': (os.path.basename(file_path), audio_file, 'audio/mp4')
                    }
                    
                    # Make API request
                    response = requests.post(
                        self.base_url,
                        headers=headers,
                        data=form_data,
                        files=files,
                        timeout=300  # 5 minutes timeout
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"ElevenLabs transcription successful. Language: {result.get('language_code')}, Probability: {result.get('language_probability')}")
                    
                    # Debug: Log the full response structure
                    logger.info(f"ElevenLabs response keys: {list(result.keys())}")
                    logger.info(f"ElevenLabs words array length: {len(result.get('words', []))}")
                    logger.info(f"First 3 words from ElevenLabs: {result.get('words', [])[:3]}")
                    
                    return result
                elif response.status_code == 429:
                    # Rate limit or system busy
                    error_data = response.json() if response.text else {}
                    error_detail = error_data.get('detail', {})
                    error_status = error_detail.get('status', 'unknown')
                    error_message = error_detail.get('message', 'Rate limit exceeded')
                    
                    if attempt < max_retries - 1:
                        logger.warning(f"ElevenLabs API 429 error (attempt {attempt + 1}/{max_retries}): {error_status} - {error_message}")
                        logger.info(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    else:
                        error_msg = f"ElevenLabs API error: {response.status_code} - {error_status}: {error_message}"
                        logger.error(error_msg)
                        raise Exception(error_msg)
                else:
                    error_msg = f"ElevenLabs API error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"ElevenLabs transcription failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    logger.error(f"ElevenLabs transcription failed after {max_retries} attempts: {str(e)}")
                    raise
    
    def extract_raw_words(self, words_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract raw words from ElevenLabs response - keep words, drop spacings
        
        Args:
            words_data: Words array from ElevenLabs response
            
        Returns:
            Raw words in our format (keep words, drop spacings)
        """
        raw_words = []
        
        logger.info(f"Extracting {len(words_data)} raw word elements from ElevenLabs (KEEP WORDS, DROP SPACINGS)")
        logger.info(f"First 5 raw word elements: {words_data[:5]}")
        
        for i, word_data in enumerate(words_data):
            # Only extract word type elements, ignore spacing completely
            if word_data.get("type") != "word":
                continue  # spacing ve diğer tokenları atla
            
            word_text = word_data.get("text", "").strip()
            if not word_text:
                continue
            
            logger.info(f"Processing word {i}: '{word_text}' (start: {word_data.get('start', 0.0)}, end: {word_data.get('end', 0.0)})")
            
            raw_words.append({
                "word": word_text,
                "start": float(word_data.get("start", 0.0)),
                "end": float(word_data.get("end", 0.0)),
                "confidence": float(word_data.get("logprob", 0.0))
            })
            logger.info(f"Extracted word: '{word_text}'")
        
        logger.info(f"Extracted {len(raw_words)} raw words from ElevenLabs response (KEEP WORDS, DROP SPACINGS)")
        logger.info(f"First 5 extracted words: {[w['word'] for w in raw_words[:5]]}")
        return raw_words
    
    
    def get_transcript_text(self, transcription_result: Dict[str, Any]) -> str:
        """
        Get transcript text from ElevenLabs response
        
        Args:
            transcription_result: Full transcription result from ElevenLabs
            
        Returns:
            Transcript text
        """
        return transcription_result.get('text', '')


def transcribe_audio_elevenlabs(file_path: str, api_key: str, model: str = "scribe_v1", seed: int = 12456, language: str = "tr") -> Dict[str, Any]:
    """
    Convenience function to transcribe audio using ElevenLabs
    
    Args:
        file_path: Path to audio file
        api_key: ElevenLabs API key
        model: Model to use (scribe_v1 or scribe_v1_experimental)
        language: Language code (e.g., 'tr' for Turkish)
        
    Returns:
        Dictionary with transcription results
    """
    stt_client = ElevenLabsSTT(api_key, model, seed, language)
    return stt_client.transcribe_file(file_path)

    