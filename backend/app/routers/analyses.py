from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form, Request
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from typing import Union
import tempfile
import os
from datetime import datetime
import soundfile as sf
# from app.models.documents import AnalysisDoc, TextDoc, AudioFileDoc, WordEventDoc, PauseEventDoc
from app.config import settings
from app.storage import upload_audio_file
from app.crud import insert_audio
from app.logging_config import app_logger

router = APIRouter()


class AnalysisSummary(BaseModel):
    id: str
    created_at: str
    status: str
    text_title: str
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


class AnalysisDetail(BaseModel):
    id: str
    created_at: str
    status: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    error: Optional[str] = None
    summary: Dict[str, Any]
    text: Dict[str, str]  # {title, body}
    audio_url: str
    word_events: List[Dict[str, Any]]
    pause_events: List[Dict[str, Any]]
    # DEBUG fields
    timings: Optional[Dict[str, Any]] = None
    counts_direct: Optional[Dict[str, int]] = None


class AnalyzeResponse(BaseModel):
    analysis_id: str
    audio_id: str
    gcs_url: Optional[str] = None
    status: str
    message: str


@router.get("/", response_model=List[AnalysisSummary])
async def get_analyses(limit: int = Query(20, ge=1, le=100)):
    """Get analyses list with pagination and lookups"""
    
    # Get analyses ordered by created_at desc
    analyses = await AnalysisDoc.find_all().sort("-created_at").limit(limit).to_list()
    
    if not analyses:
        return []
    
    # Get unique text and audio IDs for batch lookup
    text_ids = list(set(str(analysis.text_id) for analysis in analyses))
    audio_ids = list(set(str(analysis.audio_id) for analysis in analyses))
    
    # Batch fetch texts and audios
    texts = await TextDoc.find({"_id": {"$in": text_ids}}).to_list()
    audios = await AudioFileDoc.find({"_id": {"$in": audio_ids}}).to_list()
    
    # Create lookup dictionaries
    text_lookup = {str(text.id): text for text in texts}
    audio_lookup = {str(audio.id): audio for audio in audios}
    
    # Build response
    result = []
    for analysis in analyses:
        text = text_lookup.get(str(analysis.text_id))
        audio = audio_lookup.get(str(analysis.audio_id))
        
        # Extract summary data
        summary = analysis.summary or {}
        counts = summary.get("counts", {})
        
        # Build base response
        response_data = {
            "id": str(analysis.id),
            "created_at": analysis.created_at.isoformat(),
            "status": analysis.status,
            "text_title": text.title if text else "Unknown",
            "wer": summary.get("wer"),
            "accuracy": summary.get("accuracy"),
            "wpm": summary.get("wpm"),
            "counts": counts,
            "audio_id": str(analysis.audio_id),
            "audio_name": audio.original_name if audio else None,
            "audio_duration_sec": getattr(audio, 'duration_sec', None) if audio else None,
            "audio_size_bytes": getattr(audio, 'size_bytes', None) if audio else None
        }
        
        # Add DEBUG fields if enabled
        if settings.debug:
            # Add timings
            timings = {}
            if analysis.created_at:
                timings["queued_at"] = analysis.created_at.isoformat()
            if analysis.started_at:
                timings["started_at"] = analysis.started_at.isoformat()
            if analysis.finished_at:
                timings["finished_at"] = analysis.finished_at.isoformat()
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
    
    return result


@router.get("/{analysis_id}", response_model=AnalysisDetail)
async def get_analysis(analysis_id: str):
    """Get detailed analysis by ID"""
    
    try:
        analysis = await AnalysisDoc.get(analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid analysis ID")
    
    # Get related text
    text = await TextDoc.get(analysis.text_id)
    if not text:
        raise HTTPException(status_code=404, detail="Related text not found")
    
    # Get related audio
    audio = await AudioFileDoc.get(analysis.audio_id)
    if not audio:
        raise HTTPException(status_code=404, detail="Related audio not found")
    
    # Build audio public URL
    # All audio files are now stored in GCS
    if hasattr(audio, 'gcs_url') and audio.gcs_url:
        audio_url = audio.gcs_url
    else:
        # Fallback for legacy data - use GCS URI as URL
        audio_url = audio.path if audio.path.startswith('gs://') else f"gs://{settings.gcs_bucket}/{audio.path}"
    
    # Get word events
    word_events = await WordEventDoc.find({"analysis_id": analysis.id}).sort("idx").to_list()
    word_events_data = [
        {
            "idx": event.idx,
            "ref_token": event.ref_token,
            "hyp_token": event.hyp_token,
            "start_ms": event.start_ms,
            "end_ms": event.end_ms,
            "type": event.type,
            "subtype": event.subtype,
            "details": event.details
        }
        for event in word_events
    ]
    
    # Get pause events
    pause_events = await PauseEventDoc.find({"analysis_id": analysis.id}).sort("after_word_idx").to_list()
    pause_events_data = [
        {
            "after_word_idx": event.after_word_idx,
            "start_ms": event.start_ms,
            "end_ms": event.end_ms,
            "duration_ms": event.duration_ms
        }
        for event in pause_events
    ]
    
    # Build base response
    response_data = {
        "id": str(analysis.id),
        "created_at": analysis.created_at.isoformat(),
        "status": analysis.status,
        "started_at": analysis.started_at.isoformat() if analysis.started_at else None,
        "finished_at": analysis.finished_at.isoformat() if analysis.finished_at else None,
        "error": analysis.error,
        "summary": analysis.summary or {},
        "text": {
            "title": text.title,
            "body": text.body
        },
        "audio_url": audio_url,
        "word_events": word_events_data,
        "pause_events": pause_events_data
    }
    
    # Add DEBUG fields if enabled
    if settings.debug:
        # Add timings
        timings = {}
        if analysis.created_at:
            timings["queued_at"] = analysis.created_at.isoformat()
        if analysis.started_at:
            timings["started_at"] = analysis.started_at.isoformat()
        if analysis.finished_at:
            timings["finished_at"] = analysis.finished_at.isoformat()
            if analysis.started_at:
                total_ms = (analysis.finished_at - analysis.started_at).total_seconds() * 1000
                timings["total_ms"] = round(total_ms, 2)
        
        response_data["timings"] = timings if timings else None
        
        # Add direct counts
        summary = analysis.summary or {}
        counts = summary.get("counts", {})
        response_data["counts_direct"] = {
            "correct": counts.get("correct", 0),
            "missing": counts.get("missing", 0),
            "extra": counts.get("extra", 0),
            "diff": counts.get("diff", 0)
        }
    
    return AnalysisDetail(**response_data)


@router.post("/file", response_model=AnalyzeResponse)
async def analyze_file(
    request: Request,
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
            text = await TextDoc.find_one(TextDoc.text_id == text_id)
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
            custom_text_doc = TextDoc(
                text_id=f"custom_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                grade=0,  # Custom texts have grade 0
                title="Custom Text",
                body=custom_text,
                comment="Generated from analyze/file endpoint",
                active=True
            )
            await custom_text_doc.insert()
            text_obj_id = str(custom_text_doc.id)
            
            app_logger.bind(
                request_id=request_id,
                custom_text_id=custom_text_doc.text_id
            ).info("Custom text document created")
            
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
                gcs_url=gcs_result["public_url"],
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
            "gcs_url": gcs_result["public_url"],
            "gcs_uri": gcs_result["gs_uri"],
            "content_type": file.content_type,
            "size_bytes": gcs_result["size_bytes"],
            "md5_hash": gcs_result["md5"],
            "duration_sec": duration_sec,
            "uploaded_at": datetime.utcnow(),
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
    
    # Create analysis document
    try:
        analysis_doc = AnalysisDoc(
            text_id=text_obj_id,
            audio_id=str(audio_doc.id),
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
            gcs_url=gcs_result["public_url"],
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


@router.put("/{analysis_id}")
async def update_analysis(analysis_id: str):
    """Update a specific analysis by ID"""
    return {"message": f"Update analysis {analysis_id} - to be implemented"}


@router.delete("/{analysis_id}")
async def delete_analysis(analysis_id: str):
    """Delete a specific analysis by ID"""
    return {"message": f"Delete analysis {analysis_id} - to be implemented"}
