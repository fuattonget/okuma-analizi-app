#!/usr/bin/env python3
"""
Verify Words Script - Check for word merging issues

This script verifies that STT words and word events contain individual words
without any merging (e.g., "Atatürk" + "bir" should not become "Atatürkbir").

Usage:
    python scripts/verify_words.py --analysis-id <analysis_id>
"""

import asyncio
import sys
import os
import argparse
from loguru import logger

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from backend.app.models.documents import (
    AnalysisDoc, SttResultDoc, WordEventDoc, ReadingSessionDoc, TextDoc
)
from worker.config import settings


async def init_database():
    """Initialize Beanie with MongoDB"""
    # Create MongoDB client
    client = AsyncIOMotorClient(settings.mongo_uri)
    db = client[settings.mongo_db]
    
    # Initialize Beanie
    await init_beanie(
        database=db,
        document_models=[
            AnalysisDoc, SttResultDoc, WordEventDoc, ReadingSessionDoc, TextDoc
        ]
    )
    
    logger.info("Database initialized successfully")


def check_for_merged_words(words_list, source_name):
    """
    Check for suspiciously long words that might be merged
    
    Args:
        words_list: List of words to check
        source_name: Name of the source for logging
        
    Returns:
        List of suspicious words
    """
    suspicious_words = []
    
    for word in words_list:
        if isinstance(word, dict):
            word_text = word.get('word', '') if hasattr(word, 'get') else str(word)
        else:
            word_text = str(word)
        
        # Check for suspiciously long words (more than 15 characters)
        if len(word_text) > 15:
            suspicious_words.append(word_text)
        
        # Check for specific merged patterns
        merged_patterns = [
            'atatürkbir', 'biröğretmen', 'öğretmenatatürk',
            'atatürköğretmen', 'öğretmenbir', 'biratatürk',
            'öğrencilerive', 'veöğrencileri', 'öğrencileribir'
        ]
        
        for pattern in merged_patterns:
            if pattern in word_text.lower():
                suspicious_words.append(word_text)
    
    if suspicious_words:
        logger.warning(f"Found suspicious words in {source_name}: {suspicious_words}")
    else:
        logger.info(f"No suspicious words found in {source_name}")
    
    return suspicious_words


async def verify_analysis(analysis_id: str):
    """
    Verify word merging issues for a specific analysis
    
    Args:
        analysis_id: ID of the analysis to verify
        
    Returns:
        True if PASS (no merging), False if FAIL (merging found)
    """
    logger.info(f"Verifying analysis: {analysis_id}")
    
    try:
        # Get analysis
        analysis = await AnalysisDoc.get(analysis_id)
        if not analysis:
            logger.error(f"Analysis {analysis_id} not found")
            return False
        
        # Get session
        session = await ReadingSessionDoc.get(analysis.session_id)
        if not session:
            logger.error(f"Session {analysis.session_id} not found")
            return False
        
        # Get STT result
        stt_result = await SttResultDoc.find_one({"session_id": session.id})
        if not stt_result:
            logger.error(f"STT result not found for session {session.id}")
            return False
        
        # Get text
        text = await TextDoc.get(session.text_id)
        if not text:
            logger.error(f"Text {session.text_id} not found")
            return False
        
        logger.info(f"Found STT result with {len(stt_result.words)} words")
        logger.info(f"Found {len(await WordEventDoc.find({'analysis_id': analysis.id}).to_list())} word events")
        
        # Extract STT words
        stt_words = [w.word for w in stt_result.words]
        logger.info(f"STT words sample (first 10): {stt_words[:10]}")
        
        # Check STT words for merging
        stt_suspicious = check_for_merged_words(stt_result.words, "STT results")
        
        # Get word events
        word_events = await WordEventDoc.find({"analysis_id": analysis.id}).sort("position").to_list()
        
        # Extract hypothesis tokens from word events
        hyp_tokens = [event.hyp_token for event in word_events if event.hyp_token]
        logger.info(f"Word events hyp_token sample (first 10): {hyp_tokens[:10]}")
        
        # Check word events for merging
        events_suspicious = check_for_merged_words(hyp_tokens, "Word events")
        
        # Check if words are properly separated
        all_suspicious = stt_suspicious + events_suspicious
        
        if all_suspicious:
            logger.error("❌ FAIL: Found merged words!")
            logger.error(f"Suspicious words: {all_suspicious}")
            return False
        else:
            logger.info("✅ PASS: No merged words found!")
            logger.info("All words are properly separated")
            return True
        
    except Exception as e:
        logger.error(f"Error verifying analysis {analysis_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Verify word merging issues")
    parser.add_argument("--analysis-id", required=True, help="Analysis ID to verify")
    
    args = parser.parse_args()
    
    logger.info("Starting Word Verification Script")
    
    # Initialize database
    await init_database()
    
    # Verify analysis
    result = await verify_analysis(args.analysis_id)
    
    if result:
        logger.info("🎉 VERIFICATION PASSED: No word merging issues found")
        sys.exit(0)
    else:
        logger.error("💥 VERIFICATION FAILED: Word merging issues found")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
