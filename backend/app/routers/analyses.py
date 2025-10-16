from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form, Request, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from typing import Union
import tempfile
import os
from datetime import datetime, timezone, timedelta
from app.utils.timezone import to_turkish_isoformat, get_utc_now
import soundfile as sf
from bson import ObjectId
from app.models.documents import AnalysisDoc, TextDoc, AudioFileDoc, WordEventDoc, PauseEventDoc, ReadingSessionDoc
from app.models.user import UserDoc, get_current_user
from app.models.rbac import require_permission
from app.config import settings
from app.storage import upload_audio_file
from app.storage.gcs import generate_signed_url
from app.crud import insert_audio
from app.logging_config import app_logger
from app.schemas import WordEventResponse, PauseEventResponse, MetricsResponse

router = APIRouter()


@router.get("/test-export")
async def test_export():
    """Test export endpoint"""
    return {"message": "Export test endpoint working"}


@router.get("/{analysis_id}/export")
@require_permission("analysis:view")
async def export_analysis(analysis_id: str, current_user: UserDoc = Depends(get_current_user)):
    """Export complete analysis data as JSON"""
    app_logger.info(f"Export analysis called with ID: {analysis_id}")
    
    try:
        # Validate ObjectId
        try:
            oid = ObjectId(analysis_id)
            app_logger.info(f"ObjectId created successfully: {oid}")
        except Exception as e:
            app_logger.error(f"Invalid ObjectId: {e}")
            raise HTTPException(status_code=400, detail="Invalid analysis id")

        # Fetch analysis
        app_logger.info(f"Fetching analysis with ObjectId: {oid}")
        analysis = await AnalysisDoc.get(oid)
        if not analysis:
            app_logger.warning(f"Analysis not found: {oid}")
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        app_logger.info(f"Analysis found: {analysis.id}")

        # Fetch related events
        app_logger.info("Fetching word events...")
        try:
            word_events = await WordEventDoc.find(WordEventDoc.analysis_id == analysis.id).to_list()
            app_logger.info(f"Found {len(word_events)} word events")
        except Exception as e:
            app_logger.error(f"Error fetching word events: {e}")
            word_events = []
        
        app_logger.info("Fetching pause events...")
        try:
            pause_events = await PauseEventDoc.find(PauseEventDoc.analysis_id == analysis.id).to_list()
            app_logger.info(f"Found {len(pause_events)} pause events")
        except Exception as e:
            app_logger.error(f"Error fetching pause events: {e}")
            pause_events = []

        # Build response
        app_logger.info("Building response...")
        
        # Convert documents to dicts and ensure ObjectId fields are strings
        events_data = []
        for we in word_events:
            event_dict = we.dict()
            event_dict["analysis_id"] = str(event_dict["analysis_id"])
            
            # Normalize sub_type if present
            if "sub_type" in event_dict and event_dict["sub_type"]:
                from app.services.alignment import normalize_sub_type
                event_dict["sub_type"] = normalize_sub_type(event_dict["sub_type"])
            
            # Ensure char_diff and cer_local are included for substitution events
            if event_dict.get("type") == "substitution":
                if "char_diff" not in event_dict or event_dict["char_diff"] is None:
                    # Calculate char_diff if missing
                    ref_token = event_dict.get("ref_token", "")
                    hyp_token = event_dict.get("hyp_token", "")
                    if ref_token and hyp_token:
                        from app.services.alignment import char_edit_stats
                        char_diff = char_edit_stats(ref_token, hyp_token)[0]
                        event_dict["char_diff"] = char_diff
                        event_dict["cer_local"] = char_diff / max(len(ref_token), 1)
            
            events_data.append(event_dict)
        
        pauses_data = []
        for pe in pause_events:
            pause_dict = pe.dict()
            pause_dict["analysis_id"] = str(pause_dict["analysis_id"])
            pauses_data.append(pause_dict)
        
        # Validate summary consistency
        from app.services.scoring import validate_summary_consistency
        is_consistent = validate_summary_consistency(analysis.summary, word_events)
        if not is_consistent:
            app_logger.warning(f"Summary consistency validation failed for analysis {analysis_id}")
        
        # Get STT result for transcript
        from app.models.documents import SttResultDoc
        session = await ReadingSessionDoc.get(analysis.session_id)
        transcript_text = None
        app_logger.info(f"Getting STT result for session: {session.id if session else 'None'}")
        if session:
            stt_result = await SttResultDoc.find_one(SttResultDoc.session_id == session.id)
            app_logger.info(f"STT result found: {stt_result is not None}")
            if stt_result:
                transcript_text = stt_result.transcript
                app_logger.info(f"Transcript length: {len(transcript_text) if transcript_text else 0}")
        
        result = {
            "analysis_id": str(analysis.id),
            "text_id": str(analysis.session_id),
            "events": events_data,
            "pauses": pauses_data,
            "summary": analysis.summary or {},
            "metrics": analysis.summary.get("metrics", {}) if analysis.summary else {},
            "transcript": transcript_text,
            "validation": {
                "summary_consistent": is_consistent
            }
        }
        app_logger.info("Response built successfully")
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Failed to export analysis {analysis_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to export analysis: {str(e)}")


class AnalysisSummary(BaseModel):
    id: str
    created_at: str
    status: str
    text_title: str
    student_id: Optional[str] = None
    text: Optional[Dict[str, str]] = None
    wer: Optional[float] = None
    accuracy: Optional[float] = None
    wpm: Optional[float] = None
    counts: Optional[Dict[str, int]] = None
    audio_id: str
    audio_name: Optional[str] = None
    audio_duration_sec: Optional[float] = None
    audio_size_bytes: Optional[int] = None
    # DEBUG fields
    timings: Optional[Dict[str, Any]] = None
    counts_direct: Optional[Dict[str, int]] = None


class TextInfo(BaseModel):
    title: str
    body: str
    grade: int

class AnalysisDetail(BaseModel):
    id: str
    created_at: str
    status: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    error: Optional[str] = None
    student_id: Optional[str] = None
    summary: Dict[str, Any]
    text: TextInfo
    # DEBUG fields
    timings: Optional[Dict[str, Any]] = None
    counts_direct: Optional[Dict[str, int]] = None


class AnalyzeResponse(BaseModel):
    analysis_id: str
    audio_id: str
    status: str
    message: str


@router.get("/", response_model=List[AnalysisSummary])
async def get_analyses(
    limit: int = Query(20, ge=1, le=100),
    student_id: Optional[str] = Query(None, description="Filter analyses by student ID"),
    current_user: UserDoc = Depends(get_current_user)
):
    """
    Get analyses list with pagination and lookups.
    - If student_id provided: requires analysis:read permission (student-specific)
    - If no student_id: requires analysis:read_all permission (all analyses)
    """
    
    from app.logging_config import app_logger
    app_logger.info(f"DEBUG: GET /analyses called with limit={limit}, student_id={student_id}")
    
    # Permission check: different permissions for different access patterns
    if student_id:
        # Accessing specific student's analyses - requires analysis:read
        if not await current_user.has_any_permission(["analysis:read", "analysis:read_all", "*"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Required permission: analysis:read"
            )
        app_logger.info(f"DEBUG: User has permission to view student analyses")
    else:
        # Accessing all analyses - requires analysis:read_all
        if not await current_user.has_any_permission(["analysis:read_all", "*"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Required permission: analysis:read_all"
            )
        app_logger.info(f"DEBUG: User has permission to view all analyses")
    
    # Build query filter
    query_filter = {}
    if student_id:
        from bson import ObjectId
        query_filter["student_id"] = ObjectId(student_id)
        app_logger.info(f"DEBUG: Filtering by student_id: {student_id}")
    
    # Get analyses ordered by created_at desc
    analyses = await AnalysisDoc.find(query_filter).sort("-created_at").limit(limit).to_list()
    
    app_logger.info(f"DEBUG: Found {len(analyses)} analyses")
    print(f"STDOUT DEBUG: Found {len(analyses)} analyses")
    
    if not analyses:
        app_logger.info("DEBUG: No analyses found, returning empty list")
        print("STDOUT DEBUG: No analyses found, returning empty list")
        return []
    
    # Get unique session IDs for batch lookup
    session_ids = list(set(str(analysis.session_id) for analysis in analyses))
    app_logger.info(f"DEBUG: Found {len(session_ids)} unique session IDs: {session_ids[:3]}...")
    
    # Convert session IDs to ObjectId for MongoDB query
    from bson import ObjectId
    session_object_ids = [ObjectId(sid) for sid in session_ids]
    app_logger.info(f"DEBUG: Converted to ObjectIds: {session_object_ids[:3]}...")
    
    # Batch fetch sessions, texts and audios
    sessions = await ReadingSessionDoc.find({"_id": {"$in": session_object_ids}}).to_list()
    app_logger.info(f"DEBUG: Found {len(sessions)} sessions")
    
    text_ids = list(set(str(session.text_id) for session in sessions))
    audio_ids = list(set(str(session.audio_id) for session in sessions))
    app_logger.info(f"DEBUG: Found {len(text_ids)} text IDs, {len(audio_ids)} audio IDs")
    
    # Convert text and audio IDs to ObjectId for MongoDB query
    text_object_ids = [ObjectId(tid) for tid in text_ids]
    audio_object_ids = [ObjectId(aid) for aid in audio_ids]
    
    texts = await TextDoc.find({"_id": {"$in": text_object_ids}}).to_list()
    audios = await AudioFileDoc.find({"_id": {"$in": audio_object_ids}}).to_list()
    app_logger.info(f"DEBUG: Found {len(texts)} texts, {len(audios)} audios")
    
    # Create lookup dictionaries
    session_lookup = {str(session.id): session for session in sessions}
    text_lookup = {str(text.id): text for text in texts}
    audio_lookup = {str(audio.id): audio for audio in audios}
    
    # Build response
    result = []
    skipped_count = 0
    for analysis in analyses:
        session = session_lookup.get(str(analysis.session_id))
        if not session:
            skipped_count += 1
            continue  # Skip if session not found
            
        text = text_lookup.get(str(session.text_id))
        audio = audio_lookup.get(str(session.audio_id))
        
        # Extract summary data
        summary = analysis.summary or {}
        counts = summary.get("counts", {})
        
        # Build base response
        response_data = {
            "id": str(analysis.id),
            "created_at": to_turkish_isoformat(analysis.created_at),
            "status": analysis.status,
            "text_title": text.title if text else "Unknown",
            "student_id": str(analysis.student_id) if analysis.student_id else None,
            "text": {
                "title": text.title if text else "Unknown",
                "body": text.body if text else ""
            },
            "wer": summary.get("wer"),
            "accuracy": summary.get("accuracy"),
            "wpm": summary.get("wpm"),
            "counts": counts,
            "audio_id": str(session.audio_id),
            "audio_name": audio.original_name if audio else None,
            "audio_duration_sec": analysis.audio_duration_sec,
            "audio_size_bytes": getattr(audio, 'size_bytes', None) if audio else None
        }
        
        # Debug audio duration
        app_logger.info(f"DEBUG: audio object: {audio}")
        app_logger.info(f"DEBUG: audio_duration_sec: {response_data.get('audio_duration_sec')}")
        app_logger.info(f"DEBUG: response_data.student_id: {response_data.get('student_id')}")
        
        # Add DEBUG fields if enabled
        if settings.debug:
            # Add timings
            timings = {}
            if analysis.created_at:
                timings["queued_at"] = to_turkish_isoformat(analysis.created_at)
            if analysis.started_at:
                timings["started_at"] = to_turkish_isoformat(analysis.started_at)
            if analysis.finished_at:
                timings["finished_at"] = to_turkish_isoformat(analysis.finished_at)
                if analysis.started_at:
                    total_ms = (analysis.finished_at - analysis.started_at).total_seconds() * 1000
                    timings["total_ms"] = round(total_ms, 2)
            
            response_data["timings"] = timings if timings else None
            
            # Add direct counts
            response_data["counts_direct"] = {
                "correct": counts.get("correct", 0),
                "missing": counts.get("missing", 0),
                "extra": counts.get("extra", 0),
                "diff": counts.get("diff", 0)
            }
        
        result.append(AnalysisSummary(**response_data))
    
    app_logger.info(f"DEBUG: Built {len(result)} results, skipped {skipped_count} analyses")
    return result


@router.get("/{analysis_id}/word-events", response_model=List[WordEventResponse])
async def get_analysis_word_events(analysis_id: str):
    """Get word events for a specific analysis"""
    
    try:
        analysis = await AnalysisDoc.get(analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        word_events = await WordEventDoc.find(WordEventDoc.analysis_id == analysis_id).to_list()
        
        app_logger.info(f"Retrieved {len(word_events)} word events for analysis {analysis_id}")
        return word_events
        
    except Exception as e:
        app_logger.error(f"Failed to get word events for analysis {analysis_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get word events: {str(e)}")


@router.get("/{analysis_id}/pause-events", response_model=List[PauseEventResponse])
async def get_analysis_pause_events(analysis_id: str):
    """Get pause events for a specific analysis"""
    
    try:
        analysis = await AnalysisDoc.get(analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        pause_events = await PauseEventDoc.find(PauseEventDoc.analysis_id == analysis_id).to_list()
        
        app_logger.info(f"Retrieved {len(pause_events)} pause events for analysis {analysis_id}")
        return pause_events
        
    except Exception as e:
        app_logger.error(f"Failed to get pause events for analysis {analysis_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get pause events: {str(e)}")


@router.get("/{analysis_id}/metrics", response_model=MetricsResponse)
async def get_analysis_metrics(analysis_id: str):
    """Get aggregated metrics for a specific analysis"""
    
    try:
        analysis = await AnalysisDoc.get(analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Get word events
        word_events = await WordEventDoc.find(WordEventDoc.analysis_id == analysis_id).to_list()
        
        # Get pause events
        pause_events = await PauseEventDoc.find(PauseEventDoc.analysis_id == analysis_id).to_list()
        
        # Calculate counts
        counts = {
            "correct": 0,
            "missing": 0,
            "extra": 0,
            "diff": 0,
            "total_words": len(word_events)
        }
        
        for event in word_events:
            if event.type == "correct":
                counts["correct"] += 1
            elif event.type == "missing":
                counts["missing"] += 1
            elif event.type == "extra":
                counts["extra"] += 1
            elif event.type in ["substitution", "diff"]:
                counts["diff"] += 1
        
        # Calculate WER and accuracy
        total_ref = counts["correct"] + counts["missing"] + counts["diff"]
        if total_ref > 0:
            wer = (counts["missing"] + counts["extra"] + counts["diff"]) / total_ref
            accuracy = (counts["correct"] / total_ref) * 100
        else:
            wer = 0.0
            accuracy = 0.0
        
        # Calculate WPM (words per minute)
        wpm = 0.0
        if analysis.summary and "wpm" in analysis.summary:
            wpm = analysis.summary["wpm"]
        
        # Count long pauses
        long_pauses = len([p for p in pause_events if p.class_ in ["long", "very_long"]])
        
        metrics_data = {
            "analysis_id": analysis_id,
            "counts": counts,
            "wer": wer,
            "accuracy": accuracy,
            "wpm": wpm,
            "long_pauses": {
                "count": long_pauses,
                "threshold_ms": 500
            },
            "error_types": {
                "missing": counts["missing"],
                "extra": counts["extra"],
                "substitution": counts["diff"],
                "repetition": counts.get("repetition", 0),
                "pause_long": long_pauses
            }
        }
        
        app_logger.info(f"Retrieved metrics for analysis {analysis_id}")
        return MetricsResponse(**metrics_data)
        
    except Exception as e:
        app_logger.error(f"Failed to get metrics for analysis {analysis_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.post("/file", response_model=AnalyzeResponse)
@require_permission("analysis:create")
async def analyze_file(
    request: Request,
    current_user: UserDoc = Depends(get_current_user),
    file: UploadFile = File(...),
    text_id: Optional[str] = Form(None),
    custom_text: Optional[str] = Form(None),
    uploaded_by: Optional[str] = Form(None)
):
    """
    Analyze audio file directly with optional text.
    
    - **file**: Audio file (mp3, wav, m4a, etc.)
    - **text_id**: Optional text ID to analyze against existing text
    - **custom_text**: Optional custom text to analyze against
    - **uploaded_by**: Optional user identifier
    
    Note: Either text_id or custom_text must be provided.
    """
    
    request_id = getattr(request.state, 'request_id', None)
    app_logger.bind(
        request_id=request_id,
        filename=file.filename,
        text_id=text_id,
        has_custom_text=bool(custom_text),
        uploaded_by=uploaded_by,
        content_type=file.content_type
    ).info("File analysis started")
    
    # Validate inputs
    if not text_id and not custom_text:
        raise HTTPException(status_code=400, detail="Either text_id or custom_text must be provided")
    
    if text_id and custom_text:
        raise HTTPException(status_code=400, detail="Cannot provide both text_id and custom_text")
    
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    if not file.content_type or not file.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="File must be an audio file")
    
    # Check file size (10MB limit)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB")
    
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file not allowed")
    
    # Handle text validation and creation
    text_obj_id = None
    if text_id:
        # Validate existing text
        try:
            text = await TextDoc.find_one({"text_id": text_id})
            if not text:
                raise HTTPException(status_code=404, detail="Text not found")
            text_obj_id = str(text.id)
        except Exception as e:
            app_logger.bind(
                request_id=request_id,
                text_id=text_id,
                error=str(e)
            ).error("Text validation failed")
            raise HTTPException(status_code=400, detail="Invalid text ID")
    else:
        # Create custom text document
        try:
            from app.utils.text_tokenizer import normalize_turkish_text, tokenize_turkish_text
            from app.models.documents import CanonicalTokens
            
            # Normalize and tokenize the custom text
            normalized_body = normalize_turkish_text(custom_text)
            tokenized_words = tokenize_turkish_text(normalized_body)
            
            # Generate unique slug for custom text
            custom_slug = f"custom-{get_utc_now().strftime('%Y%m%d_%H%M%S')}"
            
            custom_text_doc = TextDoc(
                slug=custom_slug,
                grade=0,  # Custom texts have grade 0
                title="Custom Text",
                body=normalized_body,  # Use normalized body
                canonical=CanonicalTokens(
                    tokens=tokenized_words
                ),
                comment="Generated from analyze/file endpoint",
                active=True
            )
            await custom_text_doc.insert()
            text_obj_id = str(custom_text_doc.id)
            
            app_logger.bind(
                request_id=request_id,
                custom_text_id=str(custom_text_doc.id)
            ).info("Custom text document created with proper tokenization")
            
        except Exception as e:
            app_logger.bind(
                request_id=request_id,
                error=str(e)
            ).error("Failed to create custom text document")
            raise HTTPException(status_code=500, detail="Failed to create custom text document")
    
    # Save file temporarily for processing
    temp_file_path = None
    try:
        # Create temporary file for processing
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Calculate duration (optional)
        duration_sec = None
        try:
            data, sr = sf.read(temp_file_path)
            duration_sec = len(data) / sr
        except Exception as e:
            app_logger.bind(
                request_id=request_id,
                error=str(e)
            ).warning("Could not calculate audio duration")
        
        # Upload to GCS
        try:
            gcs_result = upload_audio_file(
                text_id=text_id,  # Use text_id for blob naming, None for custom
                original_name=file.filename,
                file_path=temp_file_path,
                content_type=file.content_type
            )
            
            app_logger.bind(
                request_id=request_id,
                text_id=text_id,
                original_filename=file.filename,
                size_bytes=gcs_result["size_bytes"]
            ).info("Audio file uploaded to GCS successfully")
            
        except Exception as e:
            app_logger.bind(
                request_id=request_id,
                error=str(e)
            ).error("Failed to upload to GCS")
            raise HTTPException(status_code=500, detail=f"Failed to upload to cloud storage: {str(e)}")
        
    except Exception as e:
        app_logger.bind(
            request_id=request_id,
            error=str(e)
        ).error("Failed to process file")
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")
    
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                app_logger.bind(
                    request_id=request_id,
                    error=str(e)
                ).warning("Failed to clean up temporary file")
    
    # Create audio document
    try:
        audio_payload = {
            "text_id": text_id,  # None for custom texts
            "original_name": file.filename,
            "path": gcs_result["gs_uri"],  # Store GCS URI as path for backward compatibility
            "storage_name": gcs_result["blob_name"],
            "gcs_uri": gcs_result["gs_uri"],
            "content_type": file.content_type,
            "size_bytes": gcs_result["size_bytes"],
            "md5_hash": gcs_result["md5"],
            "duration_sec": duration_sec,
            "uploaded_at": get_utc_now(),
            "uploaded_by": uploaded_by
        }
        
        audio_doc = await insert_audio(audio_payload)
        
        app_logger.bind(
            request_id=request_id,
            audio_id=str(audio_doc.id),
            text_id=text_id
        ).info("Audio document saved to MongoDB successfully")
        
    except Exception as e:
        app_logger.bind(
            request_id=request_id,
            error=str(e)
        ).error("Failed to save audio document to MongoDB")
        raise HTTPException(status_code=500, detail=f"Failed to save audio metadata: {str(e)}")
    
    # Create reading session first
    try:
        session_doc = ReadingSessionDoc(
            text_id=ObjectId(text_obj_id),
            audio_id=ObjectId(str(audio_doc.id)),
            reader_id=uploaded_by,
            status="active"
        )
        await session_doc.insert()
        
        app_logger.bind(
            request_id=request_id,
            session_id=str(session_doc.id),
            text_id=text_obj_id,
            audio_id=str(audio_doc.id)
        ).info("Reading session created successfully")
        
    except Exception as e:
        app_logger.bind(
            request_id=request_id,
            error=str(e)
        ).error("Failed to create reading session")
        raise HTTPException(status_code=500, detail=f"Failed to create reading session: {str(e)}")
    
    # Create analysis document
    try:
        analysis_doc = AnalysisDoc(
            session_id=ObjectId(str(session_doc.id)),
            status="queued"
        )
        await analysis_doc.insert()
        
        app_logger.bind(
            request_id=request_id,
            analysis_id=str(analysis_doc.id),
            audio_id=str(audio_doc.id)
        ).info("Analysis document created successfully")
        
        return AnalyzeResponse(
            analysis_id=str(analysis_doc.id),
            audio_id=str(audio_doc.id),
            status="queued",
            message="Analysis queued successfully"
        )
        
    except Exception as e:
        app_logger.bind(
            request_id=request_id,
            error=str(e)
        ).error("Failed to create analysis document")
        raise HTTPException(status_code=500, detail=f"Failed to create analysis: {str(e)}")


@router.post("/")
async def create_analysis():
    """Create a new analysis"""
    return {"message": "Create analysis endpoint - to be implemented"}


class AnalysisUpdate(BaseModel):
    status: Optional[str] = None
    error_message: Optional[str] = None
    student_id: Optional[str] = None

@router.put("/{analysis_id}")
async def update_analysis(analysis_id: str, update_data: AnalysisUpdate):
    """Update a specific analysis by ID"""
    try:
        analysis = await AnalysisDoc.get(analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Update fields if provided
        if update_data.status is not None:
            analysis.status = update_data.status
        
        if update_data.error_message is not None:
            analysis.error = update_data.error_message
        
        if update_data.student_id is not None:
            from bson import ObjectId
            analysis.student_id = ObjectId(update_data.student_id)
        
        # Save changes
        await analysis.save()
        
        app_logger.info(f"Updated analysis {analysis_id}: status={update_data.status}, error={update_data.error_message}, student_id={update_data.student_id}")
        
        return {
            "id": str(analysis.id),
            "status": analysis.status,
            "error": analysis.error,
            "message": "Analysis updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Failed to update analysis {analysis_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update analysis: {str(e)}")


@router.get("/{analysis_id}/audio-url")
async def get_analysis_audio_url(analysis_id: str, expiration_hours: int = Query(1, ge=1, le=24)):
    """Get signed URL for analysis audio file"""
    try:
        # Get analysis
        analysis = await AnalysisDoc.get(analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Get session first
        session = await ReadingSessionDoc.get(analysis.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Related session not found")
        
        # Get audio file
        audio = await AudioFileDoc.get(session.audio_id)
        if not audio:
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        # Generate signed URL
        signed_url = generate_signed_url(
            bucket_name=settings.gcs_bucket,
            blob_name=audio.storage_name,
            expiration_hours=expiration_hours
        )
        
        return {
            "analysis_id": analysis_id,
            "audio_id": str(session.audio_id),
            "signed_url": signed_url,
            "expiration_hours": expiration_hours,
            "expires_at": (get_utc_now() + timedelta(hours=expiration_hours)).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Failed to generate signed URL for analysis {analysis_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate audio URL: {str(e)}")


@router.delete("/{analysis_id}")
@require_permission("analysis:delete")
async def delete_analysis(analysis_id: str, current_user: UserDoc = Depends(get_current_user)):
    """Delete a specific analysis by ID"""
    return {"message": f"Delete analysis {analysis_id} - to be implemented"}


@router.get("/{analysis_id}", response_model=AnalysisDetail)
@require_permission("analysis:view")
async def get_analysis(analysis_id: str, current_user: UserDoc = Depends(get_current_user)):
    """Get detailed analysis by ID"""
    
    try:
        analysis = await AnalysisDoc.get(analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid analysis ID")
    
    # Get related session
    session = await ReadingSessionDoc.get(analysis.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Related session not found")
    
    # Get related text
    text = await TextDoc.get(session.text_id)
    if not text:
        raise HTTPException(status_code=404, detail="Related text not found")
    
    # Get related audio
    audio = await AudioFileDoc.get(session.audio_id)
    if not audio:
        raise HTTPException(status_code=404, detail="Related audio not found")
    
    # Audio files are now private - use signed URLs instead of direct access
    
    
    # Build base response
    response_data = {
        "id": str(analysis.id),
        "created_at": to_turkish_isoformat(analysis.created_at),
        "status": analysis.status,
        "started_at": to_turkish_isoformat(analysis.started_at),
        "finished_at": to_turkish_isoformat(analysis.finished_at),
        "error": analysis.error,
        "student_id": str(analysis.student_id) if analysis.student_id else None,
        "summary": analysis.summary or {},
        "text": {
            "title": text.title,
            "body": text.body,
            "grade": text.grade
        }
    }
    
    # Add DEBUG fields if enabled
    if settings.debug:
        # Add timings
        timings = {}
        if analysis.created_at:
            timings["queued_at"] = to_turkish_isoformat(analysis.created_at)
        if analysis.started_at:
            timings["started_at"] = to_turkish_isoformat(analysis.started_at)
        if analysis.finished_at:
            timings["finished_at"] = to_turkish_isoformat(analysis.finished_at)
        
        response_data["debug"] = {
            "timings": timings,
            "session_id": str(session.id),
            "text_id": str(text.id),
            "audio_id": str(audio.id),
            "audio_filename": audio.original_name,
            "audio_size": audio.size_bytes,
            "audio_duration": audio.duration_sec
        }
    
    return AnalysisDetail(**response_data)
