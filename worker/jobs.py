#!/usr/bin/env python3
"""
Worker jobs for audio analysis
"""

import asyncio
import json
import sys
import os
import time
from datetime import datetime
from loguru import logger
# PydanticObjectId removed in Pydantic v2, using str instead

# Configure logging based on settings
def setup_logging():
    from worker.config import settings
    
    # Remove default handler
    logger.remove()
    
    # Configure log level
    log_level = settings.log_level.upper()
    
    # Configure format
    if settings.log_format.lower() == "json":
        log_format = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} | {message}"
    else:
        log_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>"
    
    # Add console handler
    logger.add(
        sink=lambda msg: print(msg, end=""),
        format=log_format,
        level=log_level,
        colorize=settings.log_format.lower() != "json"
    )
    
    # Add file handler with rotation
    if settings.log_file:
        os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)
        logger.add(
            sink=settings.log_file,
            format=log_format,
            level=log_level,
            rotation="5 MB",
            retention="7 days",
            compression="zip"
        )

# Setup logging
setup_logging()

from faster_whisper import WhisperModel

from worker.db import connect_to_mongo, close_mongo_connection
from backend.app.models.documents import AnalysisDoc, AudioFileDoc, TextDoc, WordEventDoc, PauseEventDoc
from worker.services import alignment
from worker.services import pauses
from worker.services import scoring
from worker.config import settings


async def analyze_audio(analysis_id: str):
    """
    Main job function for analyzing audio
    
    Args:
        analysis_id: ID of the analysis document
    """
    start_time = time.time()
    logger.info(f"Starting analysis for {analysis_id}")
    
    try:
        # Connect to database
        await connect_to_mongo()
        logger.debug("Database connection established")
        
        # Get analysis document
        analysis = await AnalysisDoc.get(analysis_id)
        if not analysis:
            logger.error(f"Analysis {analysis_id} not found")
            return
        
        # Update status to running
        analysis.status = "running"
        analysis.started_at = datetime.utcnow()
        await analysis.save()
        logger.info(f"Analysis {analysis_id} status updated to running")
        
        # Get related documents
        audio = await AudioFileDoc.get(analysis.audio_id)
        text = await TextDoc.get(analysis.text_id)
        
        if not audio:
            raise Exception(f"Audio file {analysis.audio_id} not found")
        if not text:
            raise Exception(f"Text {analysis.text_id} not found")
        
        # DEBUG: Log file details
        file_size = os.path.getsize(audio.path) if os.path.exists(audio.path) else 0
        logger.debug(f"Processing file: {audio.path}, size: {file_size} bytes")
        
        # Load Whisper model
        logger.debug(f"Loading Whisper model: {settings.whisper_model}")
        model_start = time.time()
        model = WhisperModel(
            settings.whisper_model,
            device=settings.whisper_device,
            compute_type=settings.whisper_compute_type
        )
        model_load_time = (time.time() - model_start) * 1000
        logger.debug(f"Model loaded in {model_load_time:.2f}ms")
        
        # Transcribe audio
        logger.debug("Starting transcription")
        stt_start = time.time()
        segments, info = model.transcribe(
            audio.path,
            beam_size=5,
            vad_filter=True,
            word_timestamps=True,
            language=None
        )
        
        # Collect word-level timestamps
        words = []
        for segment in segments:
            if hasattr(segment, 'words') and segment.words:
                for word in segment.words:
                    words.append({
                        'word': word.word,
                        'start': word.start,
                        'end': word.end,
                        'confidence': getattr(word, 'probability', 0.0)
                    })
        
        stt_time = (time.time() - stt_start) * 1000
        segments_list = list(segments)
        logger.debug(f"Transcription completed in {stt_time:.2f}ms, {len(words)} words, {len(segments_list)} segments")
        
        if not words:
            raise Exception("No words detected in audio")
        
        # Get first and last word times
        first_ms = words[0]['start'] * 1000
        last_ms = words[-1]['end'] * 1000
        
        # Create hypothesis text
        hyp_text = " ".join([w['word'] for w in words])
        logger.debug(f"Hypothesis text: {hyp_text[:100]}...")
        
        # Tokenize texts
        logger.debug("Starting text tokenization and alignment")
        align_start = time.time()
        
        ref_tokens = alignment.tokenize_tr(text.body)
        hyp_tokens = alignment.tokenize_tr(hyp_text)
        
        logger.debug(f"Reference tokens: {len(ref_tokens)}, Hypothesis tokens: {len(hyp_tokens)}")
        
        # Perform alignment
        alignment_result = alignment.levenshtein_align(ref_tokens, hyp_tokens)
        
        # Count alignment results
        subs = sum(1 for a in alignment_result if a[0] == "replace")
        dels = sum(1 for a in alignment_result if a[0] == "delete")
        ins = sum(1 for a in alignment_result if a[0] == "insert")
        correct = sum(1 for a in alignment_result if a[0] == "equal")
        
        align_time = (time.time() - align_start) * 1000
        logger.debug(f"Alignment completed in {align_time:.2f}ms: {correct} correct, {subs} substitutions, {dels} deletions, {ins} insertions")
        
        # Build word events
        word_events = alignment.build_word_events(alignment_result, words)
        logger.debug(f"Built {len(word_events)} word events")
        
        # Calculate metrics
        metrics = scoring.compute_metrics(len(ref_tokens), subs, dels, ins)
        wpm = scoring.compute_wpm(len(hyp_tokens), first_ms, last_ms)
        
        logger.info(f"Metrics calculated: WER={metrics['wer']:.3f}, Accuracy={metrics['accuracy']:.1f}%, WPM={wpm:.1f}")
        
        # Detect pauses
        logger.debug("Detecting pauses")
        pause_start = time.time()
        pause_events = pauses.detect_pauses(words, settings.long_pause_ms)
        pause_time = (time.time() - pause_start) * 1000
        logger.debug(f"Pause detection completed in {pause_time:.2f}ms, found {len(pause_events)} pauses")
        
        # Create word event documents
        word_event_docs = []
        for i, event in enumerate(word_events):
            word_event_docs.append(WordEventDoc(
                analysis_id=str(analysis.id),
                idx=i,
                ref_token=event.get('ref_token'),
                hyp_token=event.get('hyp_token'),
                start_ms=event.get('start_ms'),
                end_ms=event.get('end_ms'),
                type=event.get('type'),
                subtype=event.get('subtype'),
                details=event.get('details', {})
            ))
        
        # Create pause event documents
        pause_event_docs = []
        for pause in pause_events:
            pause_event_docs.append(PauseEventDoc(
                analysis_id=str(analysis.id),
                after_word_idx=pause['after_word_idx'],
                start_ms=pause['start_ms'],
                end_ms=pause['end_ms'],
                duration_ms=pause['duration_ms']
            ))
        
        # Bulk insert events
        if word_event_docs:
            await WordEventDoc.insert_many(word_event_docs)
            logger.debug(f"Inserted {len(word_event_docs)} word events")
        
        if pause_event_docs:
            await PauseEventDoc.insert_many(pause_event_docs)
            logger.debug(f"Inserted {len(pause_event_docs)} pause events")
        
        # Update analysis summary
        total_time = (time.time() - start_time) * 1000
        
        summary = {
            "counts": {
                "correct": correct,
                "missing": dels,
                "extra": ins,
                "diff": subs
            },
            "wer": metrics["wer"],
            "accuracy": metrics["accuracy"],
            "wpm": wpm,
            "long_pauses": {
                "count": len(pause_events),
                "threshold_ms": settings.long_pause_ms
            }
        }
        
        # Add DEBUG information if enabled
        if settings.debug:
            summary["debug"] = {
                "model": {
                    "name": settings.whisper_model,
                    "device": settings.whisper_device,
                    "compute": settings.whisper_compute_type
                },
                "timings_ms": {
                    "model_load": round(model_load_time, 2),
                    "stt": round(stt_time, 2),
                    "align": round(align_time, 2),
                    "pauses": round(pause_time, 2),
                    "total": round(total_time, 2)
                }
            }
        
        analysis.summary = summary
        analysis.status = "done"
        analysis.finished_at = datetime.utcnow()
        await analysis.save()
        
        logger.info(f"Analysis {analysis_id} completed successfully in {total_time:.2f}ms")
        
    except Exception as e:
        logger.error(f"Analysis {analysis_id} failed: {str(e)}", exc_info=True)
        
        # Update analysis with error
        try:
            analysis = await AnalysisDoc.get(analysis_id)
            if analysis:
                analysis.status = "failed"
                analysis.error = str(e)
                analysis.finished_at = datetime.utcnow()
                await analysis.save()
        except:
            pass
        
        raise e
    
    finally:
        await close_mongo_connection()
        logger.debug("Database connection closed")


if __name__ == "__main__":
    # For testing
    import sys
    if len(sys.argv) > 1:
        asyncio.run(analyze_audio(sys.argv[1]))