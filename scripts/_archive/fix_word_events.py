#!/usr/bin/env python3
"""
Fix Word Events Script - Re-align word events with raw STT words

This script fixes word_events that were created with combined words
by re-aligning them with the raw STT words from stt_results.
"""

import asyncio
import sys
import os
from datetime import datetime
from loguru import logger

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from backend.app.models.documents import (
    AnalysisDoc, SttResultDoc, WordEventDoc, ReadingSessionDoc
)
from worker.services import alignment
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
            AnalysisDoc, SttResultDoc, WordEventDoc, ReadingSessionDoc
        ]
    )
    
    logger.info("Database initialized successfully")


async def fix_word_events_for_analysis(analysis_id: str):
    """
    Fix word events for a specific analysis
    
    Args:
        analysis_id: ID of the analysis to fix
    """
    logger.info(f"Fixing word events for analysis: {analysis_id}")
    
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
        
        # Get existing word events
        existing_events = await WordEventDoc.find({"analysis_id": analysis.id}).to_list()
        logger.info(f"Found {len(existing_events)} existing word events")
        
        # Check if we need to fix (look for combined words)
        needs_fix = False
        for event in existing_events:
            if event.hyp_token and len(event.hyp_token) > 10:  # Suspiciously long words
                needs_fix = True
                break
        
        if not needs_fix:
            logger.info("No combined words found, skipping fix")
            return True
        
        # Get raw words from STT result
        raw_words = stt_result.words
        logger.info(f"Found {len(raw_words)} raw words from STT result")
        
        # Get reference text from session
        from backend.app.models.documents import TextDoc
        text = await TextDoc.get(session.text_id)
        if not text:
            logger.error(f"Text {session.text_id} not found")
            return False
        
        # Tokenize reference text
        ref_tokens = alignment.tokenize_tr(text.body)
        logger.info(f"Tokenized reference text into {len(ref_tokens)} tokens")
        
        # Create hypothesis text from raw words
        hyp_text = " ".join([w['word'] for w in raw_words])
        hyp_tokens = alignment.tokenize_tr(hyp_text)
        logger.info(f"Tokenized hypothesis text into {len(hyp_tokens)} tokens")
        
        # Perform alignment
        alignment_result = alignment.levenshtein_align(ref_tokens, hyp_tokens)
        logger.info(f"Alignment completed: {len(alignment_result)} operations")
        
        # Build new word events
        new_word_events_data = alignment.build_word_events(alignment_result, raw_words)
        logger.info(f"Built {len(new_word_events_data)} new word events")
        
        # Delete existing word events
        await WordEventDoc.find({"analysis_id": analysis.id}).delete()
        logger.info("Deleted existing word events")
        
        # Create new word event documents
        new_word_events = []
        for i, event_data in enumerate(new_word_events_data):
            word_event = WordEventDoc(
                analysis_id=analysis.id,
                position=i,
                ref_token=event_data.get('ref_token'),
                hyp_token=event_data.get('hyp_token'),
                type=event_data.get('type', 'unknown'),
                sub_type=event_data.get('sub_type'),
                timing={
                    'start_ms': event_data.get('start_ms'),
                    'end_ms': event_data.get('end_ms')
                } if event_data.get('start_ms') else None,
                char_diff=event_data.get('char_diff')
            )
            new_word_events.append(word_event)
        
        # Save new word events
        if new_word_events:
            await WordEventDoc.insert_many(new_word_events)
            logger.info(f"Saved {len(new_word_events)} new word events")
        
        # Update analysis summary
        from worker.services import scoring
        
        # Count alignment results
        subs = sum(1 for a in alignment_result if a[0] == "replace")
        dels = sum(1 for a in alignment_result if a[0] == "delete")
        ins = sum(1 for a in alignment_result if a[0] == "insert")
        correct = sum(1 for a in alignment_result if a[0] == "equal")
        
        # Calculate metrics
        metrics = scoring.compute_metrics(len(ref_tokens), subs, dels, ins)
        
        # Update summary
        if not analysis.summary:
            analysis.summary = {}
        
        analysis.summary["counts"] = {
            "correct": correct,
            "missing": dels,
            "extra": ins,
            "diff": subs
        }
        analysis.summary["wer"] = metrics["wer"]
        analysis.summary["accuracy"] = metrics["accuracy"]
        
        await analysis.save()
        logger.info(f"Updated analysis summary with new metrics")
        
        logger.info(f"Successfully fixed word events for analysis {analysis_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to fix word events for analysis {analysis_id}: {str(e)}")
        return False


async def find_analyses_with_combined_words():
    """
    Find analyses that have word events with combined words
    
    Returns:
        List of analysis IDs that need fixing
    """
    logger.info("Searching for analyses with combined words...")
    
    # Get all analyses
    analyses = await AnalysisDoc.find({"status": "done"}).to_list()
    logger.info(f"Found {len(analyses)} completed analyses")
    
    analyses_to_fix = []
    
    for analysis in analyses:
        # Get word events for this analysis
        word_events = await WordEventDoc.find({"analysis_id": analysis.id}).limit(10).to_list()
        
        # Check for suspiciously long words
        has_combined_words = False
        for event in word_events:
            if event.hyp_token and len(event.hyp_token) > 10:
                has_combined_words = True
                logger.info(f"Analysis {analysis.id} has combined word: '{event.hyp_token}'")
                break
        
        if has_combined_words:
            analyses_to_fix.append(str(analysis.id))
    
    logger.info(f"Found {len(analyses_to_fix)} analyses with combined words")
    return analyses_to_fix


async def main():
    """Main function"""
    logger.info("Starting Word Events Fix Script")
    
    # Initialize database
    await init_database()
    
    if len(sys.argv) > 1:
        # Fix specific analysis
        analysis_id = sys.argv[1]
        success = await fix_word_events_for_analysis(analysis_id)
        if success:
            logger.info("Fix completed successfully")
        else:
            logger.error("Fix failed")
            sys.exit(1)
    else:
        # Find and fix all analyses with combined words
        analyses_to_fix = await find_analyses_with_combined_words()
        
        if not analyses_to_fix:
            logger.info("No analyses need fixing")
            return
        
        logger.info(f"Fixing {len(analyses_to_fix)} analyses...")
        
        success_count = 0
        for analysis_id in analyses_to_fix:
            success = await fix_word_events_for_analysis(analysis_id)
            if success:
                success_count += 1
        
        logger.info(f"Fixed {success_count}/{len(analyses_to_fix)} analyses")


if __name__ == "__main__":
    asyncio.run(main())
