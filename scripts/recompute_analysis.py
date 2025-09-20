#!/usr/bin/env python3
"""
Recompute Analysis Script - Fix word events with raw STT words

This script recomputes word events and analysis metrics for existing analyses
using the raw STT words without any word merging.

Usage:
    python scripts/recompute_analysis.py --analysis-id <analysis_id>
    python scripts/recompute_analysis.py --session-id <session_id>
    python scripts/recompute_analysis.py --all-done  # Recompute all done analyses
"""

import asyncio
import sys
import os
import argparse
from datetime import datetime
from loguru import logger

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from backend.app.models.documents import (
    AnalysisDoc, SttResultDoc, WordEventDoc, ReadingSessionDoc, TextDoc
)
from worker.services import alignment, scoring
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


async def recompute_analysis(analysis_id: str):
    """
    Recompute word events and metrics for a specific analysis
    
    Args:
        analysis_id: ID of the analysis to recompute
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Recomputing analysis: {analysis_id}")
    
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
        
        logger.info(f"Found STT result with {len(stt_result.words)} raw words")
        
        # Get raw words from STT result (direct passthrough)
        raw_words = stt_result.words
        logger.info(f"Using {len(raw_words)} raw words from STT result")
        
        # Log sample words to verify they are individual
        sample_words = [w.word for w in raw_words[:5]]
        logger.info(f"Sample raw words: {sample_words}")
        
        # Check for merged words (this should not happen with new pipeline)
        merged_words = [w.word for w in raw_words if len(w.word) > 20]
        if merged_words:
            logger.warning(f"Found suspiciously long words (might be merged): {merged_words}")
        
        # Tokenize reference text
        ref_tokens = alignment.tokenize_tr(text.body)
        logger.info(f"Tokenized reference text into {len(ref_tokens)} tokens")
        
        # Create hypothesis text from raw words
        hyp_text = " ".join([w.word for w in raw_words])
        hyp_tokens = alignment.tokenize_tr(hyp_text)
        logger.info(f"Tokenized hypothesis text into {len(hyp_tokens)} tokens")
        
        # Perform alignment
        alignment_result = alignment.levenshtein_align(ref_tokens, hyp_tokens)
        logger.info(f"Alignment completed: {len(alignment_result)} operations")
        
        # Build new word events
        new_word_events_data = alignment.build_word_events(alignment_result, raw_words)
        logger.info(f"Built {len(new_word_events_data)} new word events")
        
        # Log sample word events to verify individual words
        sample_events = new_word_events_data[:3]
        for event in sample_events:
            logger.info(f"Sample event: ref='{event.get('ref_token')}', hyp='{event.get('hyp_token')}', type='{event.get('type')}'")
        
        # Delete existing word events
        delete_result = await WordEventDoc.find({"analysis_id": analysis.id}).delete()
        logger.info(f"Deleted {delete_result.deleted_count} existing word events")
        
        # Create new word event documents
        new_word_events = []
        for i, event_data in enumerate(new_word_events_data):
            word_event = WordEventDoc(
                analysis_id=analysis.id,
                position=i,
                ref_token=event_data.get('ref_token'),
                hyp_token=event_data.get('hyp_token'),
                type=event_data.get('type', 'unknown'),
                sub_type=event_data.get('subtype'),
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
        
        # Count alignment results
        subs = sum(1 for a in alignment_result if a[0] == "replace")
        dels = sum(1 for a in alignment_result if a[0] == "delete")
        ins = sum(1 for a in alignment_result if a[0] == "insert")
        correct = sum(1 for a in alignment_result if a[0] == "equal")
        
        # Calculate metrics
        metrics = scoring.compute_metrics(len(ref_tokens), subs, dels, ins)
        
        # Get first and last word times
        first_ms = raw_words[0].start * 1000 if raw_words else 0
        last_ms = raw_words[-1].end * 1000 if raw_words else 0
        
        # Calculate WPM
        wpm = scoring.compute_wpm(len(hyp_tokens), first_ms, last_ms)
        
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
        analysis.summary["wpm"] = wpm
        
        # Update analysis
        analysis.updated_at = datetime.utcnow()
        await analysis.save()
        logger.info(f"Updated analysis summary with new metrics")
        
        logger.info(f"Successfully recomputed analysis {analysis_id}")
        logger.info(f"Metrics: WER={metrics['wer']:.3f}, Accuracy={metrics['accuracy']:.1f}%, WPM={wpm:.1f}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to recompute analysis {analysis_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def recompute_by_session_id(session_id: str):
    """
    Recompute analysis for a session
    
    Args:
        session_id: ID of the session
    """
    logger.info(f"Recomputing analysis for session: {session_id}")
    
    # Get session
    session = await ReadingSessionDoc.get(session_id)
    if not session:
        logger.error(f"Session {session_id} not found")
        return False
    
    # Get analysis for this session
    analysis = await AnalysisDoc.find_one({"session_id": session.id})
    if not analysis:
        logger.error(f"Analysis not found for session {session_id}")
        return False
    
    return await recompute_analysis(str(analysis.id))


async def recompute_all_done_analyses():
    """
    Recompute all analyses with status 'done'
    """
    logger.info("Recomputing all done analyses...")
    
    # Get all done analyses
    analyses = await AnalysisDoc.find({"status": "done"}).to_list()
    logger.info(f"Found {len(analyses)} done analyses")
    
    success_count = 0
    for analysis in analyses:
        success = await recompute_analysis(str(analysis.id))
        if success:
            success_count += 1
    
    logger.info(f"Recomputed {success_count}/{len(analyses)} analyses successfully")


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Recompute analysis word events and metrics")
    parser.add_argument("--analysis-id", help="Analysis ID to recompute")
    parser.add_argument("--session-id", help="Session ID to recompute")
    parser.add_argument("--all-done", action="store_true", help="Recompute all done analyses")
    
    args = parser.parse_args()
    
    logger.info("Starting Analysis Recompute Script")
    
    # Initialize database
    await init_database()
    
    if args.analysis_id:
        success = await recompute_analysis(args.analysis_id)
        if success:
            logger.info("Recompute completed successfully")
        else:
            logger.error("Recompute failed")
            sys.exit(1)
    elif args.session_id:
        success = await recompute_by_session_id(args.session_id)
        if success:
            logger.info("Recompute completed successfully")
        else:
            logger.error("Recompute failed")
            sys.exit(1)
    elif args.all_done:
        await recompute_all_done_analyses()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())