#!/usr/bin/env python3
"""
Worker jobs for audio analysis
"""

import asyncio
import json
import sys
import os
import time
import tempfile
from datetime import datetime
from loguru import logger
# PydanticObjectId removed in Pydantic v2, using str instead

# Configure logging based on settings
def setup_logging():
    from config import settings
    
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

from db import connect_to_mongo, close_mongo_connection
from models import (
    AnalysisDoc, AudioFileDoc, TextDoc, ReadingSessionDoc,
    WordEventDoc, PauseEventDoc, SttResultDoc
)
from services import alignment
from services import pauses
from services import scoring
from config import settings


def analyze_audio(analysis_id: str):
    """
    Main job function for analyzing audio (sync wrapper for RQ)
    
    Args:
        analysis_id: ID of the analysis document
    """
    return asyncio.run(_analyze_audio_async(analysis_id))


async def _analyze_audio_async(analysis_id: str):
    """
    Async implementation of audio analysis
    
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
        
        # Get session document first
        session = await ReadingSessionDoc.get(analysis.session_id)
        if not session:
            raise Exception(f"Session {analysis.session_id} not found")
        
        # Get related documents from session
        audio = await AudioFileDoc.get(session.audio_id)
        text = await TextDoc.get(session.text_id)
        
        if not audio:
            raise Exception(f"Audio file {session.audio_id} not found")
        if not text:
            raise Exception(f"Text {session.text_id} not found")
        
        # Download audio file from GCS if needed
        if audio.gcs_uri.startswith('gs://'):
            logger.debug(f"Downloading audio file from GCS: {audio.gcs_uri}")
            from google.cloud import storage
            
            # Parse GCS URL
            gs_url = audio.gcs_uri
            bucket_name = gs_url.split('/')[2]
            blob_name = '/'.join(gs_url.split('/')[3:])
            
            # Download to temporary file
            import os
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = settings.gcs_credentials_path
            client = storage.Client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            blob.download_to_filename(temp_file.name)
            audio_path = temp_file.name
            logger.debug(f"Downloaded to: {audio_path}")
        else:
            audio_path = audio.path
        
        # DEBUG: Log file details
        file_size = os.path.getsize(audio_path) if os.path.exists(audio_path) else 0
        logger.debug(f"Processing file: {audio_path}, size: {file_size} bytes")
        
        # Initialize ElevenLabs STT client
        logger.debug(f"Initializing ElevenLabs STT with model: {settings.elevenlabs_model}")
        model_start = time.time()
        from services.elevenlabs_stt import ElevenLabsSTT
        stt_client = ElevenLabsSTT(
            api_key=settings.elevenlabs_api_key,
            model=settings.elevenlabs_model,
            language=settings.elevenlabs_language,
            temperature=settings.elevenlabs_temperature,
            seed=settings.elevenlabs_seed,
            remove_filler_words=settings.elevenlabs_remove_filler_words,
            remove_disfluencies=settings.elevenlabs_remove_disfluencies
        )
        model_load_time = (time.time() - model_start) * 1000
        logger.debug(f"ElevenLabs STT client initialized in {model_load_time:.2f}ms")
        
        # Transcribe audio using ElevenLabs
        logger.info(f"Starting ElevenLabs transcription of file: {audio_path}")
        logger.info(f"File size: {os.path.getsize(audio_path)} bytes")
        stt_start = time.time()
        
        # Call ElevenLabs API
        transcription_result = stt_client.transcribe_file(audio_path)
        
        # Extract words from response - DIRECT PASSTHROUGH, no processing
        words_data = transcription_result.get('words', [])
        logger.info(f"About to call extract_raw_words with {len(words_data)} words from ElevenLabs")
        words = stt_client.extract_raw_words(words_data)  # Direct passthrough
        logger.info(f"extract_raw_words returned {len(words)} words")
        logger.info(f"STT raw words count: {len(words_data)}, processed words count: {len(words)}")
        
        stt_time = (time.time() - stt_start) * 1000
        logger.info(f"ElevenLabs transcription completed in {stt_time:.2f}ms, {len(words)} words")
        logger.info(f"Detected language: {transcription_result.get('language_code')}, probability: {transcription_result.get('language_probability')}")
        
        if not words:
            raise Exception("No words detected in audio")
        
        # Save STT result with raw words
        stt_result = SttResultDoc(
            session_id=session.id,
            provider="elevenlabs",
            model=settings.elevenlabs_model,
            language=transcription_result.get('language_code', 'tr'),
            transcript=stt_client.get_transcript_text(transcription_result),  # Use original transcript
            words=[{
                "word": w['word'],
                "start": w['start'],
                "end": w['end'],
                "confidence": w.get('confidence')
            } for w in words]
        )
        await stt_result.insert()
        logger.info(f"Saved SttResultDoc {stt_result.id}")
        
        # Get first and last word times
        first_ms = words[0]['start'] * 1000
        last_ms = words[-1]['end'] * 1000
        
        # Create hypothesis text from raw words
        hyp_text = " ".join([w['word'] for w in words])
        logger.debug(f"Hypothesis text from raw words: {hyp_text[:100]}...")
        logger.debug(f"Raw words sample: {[w['word'] for w in words[:5]]}")
        logger.debug(f"Total raw words count: {len(words)}")
        
        # Tokenize texts
        logger.debug("Starting text tokenization and alignment")
        align_start = time.time()
        
        # Use canonical tokens from TextDoc instead of re-tokenizing
        # This ensures we use the same tokenization as when the text was saved
        ref_tokens = text.canonical.tokens if text.canonical and text.canonical.tokens else []
        if not ref_tokens:
            # Fallback to tokenizing body if canonical tokens are missing
            from services.alignment import tokenize_tr
            ref_tokens = tokenize_tr(text.body)
            logger.warning("Using fallback tokenization - canonical.tokens was empty")
        
        # Use raw words directly - NO TOKENIZATION of hypothesis
        hyp_tokens = [w['word'] for w in words]
        
        logger.debug(f"Reference tokens: {len(ref_tokens)}, Hypothesis tokens: {len(hyp_tokens)}")
        logger.debug(f"Raw hyp tokens sample: {hyp_tokens[:5]}")
        
        # Perform alignment
        alignment_result = alignment.levenshtein_align(ref_tokens, hyp_tokens)
        
        # Count alignment results
        subs = sum(1 for a in alignment_result if a[0] == "replace")
        dels = sum(1 for a in alignment_result if a[0] == "delete")
        ins = sum(1 for a in alignment_result if a[0] == "insert")
        correct = sum(1 for a in alignment_result if a[0] == "equal")
        
        align_time = (time.time() - align_start) * 1000
        logger.debug(f"Alignment completed in {align_time:.2f}ms: {correct} correct, {subs} substitutions, {dels} deletions, {ins} insertions")
        
        # Build word events from alignment
        word_events_data = alignment.build_word_events(alignment_result, words)
        
        # Save WordEventDoc documents
        word_events = []
        for i, event_data in enumerate(word_events_data):
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
            word_events.append(word_event)
        
        if word_events:
            await WordEventDoc.insert_many(word_events)
            logger.info(f"Saved {len(word_events)} WordEventDoc documents")
        
        # Calculate metrics
        metrics = scoring.compute_metrics(len(ref_tokens), subs, dels, ins)
        wpm = scoring.compute_wpm(len(hyp_tokens), first_ms, last_ms)
        
        logger.info(f"Metrics calculated: WER={metrics['wer']:.3f}, Accuracy={metrics['accuracy']:.1f}%, WPM={wpm:.1f}")
        
        # Detect pauses
        logger.debug("Detecting pauses")
        pause_start = time.time()
        pause_events_data = pauses.detect_pauses(words, settings.long_pause_ms)
        pause_time = (time.time() - pause_start) * 1000
        logger.debug(f"Pause detection completed in {pause_time:.2f}ms, found {len(pause_events_data)} pauses")
        
        # Save PauseEventDoc documents
        pause_events = []
        for i, event_data in enumerate(pause_events_data):
            pause_event = PauseEventDoc(
                analysis_id=analysis.id,
                after_position=event_data.get('after_word_idx', i),
                duration_ms=event_data.get('duration_ms', 0),
                class_=event_data.get('class', 'long'),
                start_ms=event_data.get('start_ms', 0),
                end_ms=event_data.get('end_ms', 0)
            )
            pause_events.append(pause_event)
        
        if pause_events:
            await PauseEventDoc.insert_many(pause_events)
            logger.info(f"Saved {len(pause_events)} PauseEventDoc documents")
        
        
        # Update analysis summary - now aggregate from events
        total_time = (time.time() - start_time) * 1000
        
        # Aggregate counts from WordEventDoc
        counts = scoring.recompute_counts(word_events)
        
        # Add pause counts to the detailed counts
        counts["uzun_duraksama"] = len(pause_events)
        
        # Compute grade-based scoring
        text_grade = text.grade if hasattr(text, 'grade') and text.grade else 1
        grade_score = scoring.compute_grade_score(text_grade, counts, len(ref_tokens))
        
        summary = {
            "counts": counts,
            "wer": metrics["wer"],
            "accuracy": metrics["accuracy"],
            "wpm": wpm,
            "grade_score": grade_score,  # Add grade-based scoring
            "long_pauses": {
                "count": len(pause_events),
                "threshold_ms": settings.long_pause_ms
            },
            "error_types": {
                "missing": counts.get("missing", 0),
                "extra": counts.get("extra", 0),
                "substitution": counts.get("substitution", 0),  # Use "substitution" instead of "diff"
                "repetition": counts.get("repetition", 0),
                "pause_long": len(pause_events)
            }
        }
        
        # Add DEBUG information if enabled
        if settings.debug:
            summary["debug"] = {
                "model": {
                    "name": settings.elevenlabs_model,
                    "provider": "elevenlabs",
                    "language": settings.elevenlabs_language
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
        # Calculate audio duration from last word timestamp
        analysis.audio_duration_sec = round(last_ms / 1000, 2)
        await analysis.save()
        
        # Update session status to completed
        session.status = "completed"
        session.completed_at = datetime.utcnow()
        await session.save()
        
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
        analyze_audio(sys.argv[1])