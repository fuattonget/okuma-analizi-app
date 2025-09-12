from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Union
from typing import Optional
import os
import uuid
from datetime import datetime
import soundfile as sf
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from app.config import settings
from app.models.documents import AudioFileDoc, AnalysisDoc, TextDoc
from app.db import redis_conn
from app.logging_config import app_logger

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


class UploadResponse(BaseModel):
    analysis_id: str


@router.post("/", response_model=UploadResponse)
@limiter.limit("5/minute")
async def upload_audio(
    request: Request,
    file: UploadFile = File(...),
    text_id: str = Form(...)
):
    """
    Upload audio file for analysis
    
    - **file**: Audio file (mp3, wav, etc.)
    - **text_id**: ID of the text to analyze against
    """
    
    request_id = getattr(request.state, 'request_id', None)
    app_logger.bind(
        request_id=request_id,
        filename=file.filename,
        text_id=text_id,
        content_type=file.content_type
    ).info("Audio upload started")
    
    # Validate text_id
    try:
        # Find text by text_id field (not MongoDB _id)
        text = await TextDoc.find_one(TextDoc.text_id == text_id)
        if not text:
            raise HTTPException(status_code=404, detail="Text not found")
        text_obj_id = str(text.id)  # Use MongoDB _id for analysis
    except Exception as e:
        app_logger.bind(
            request_id=request_id,
            text_id=text_id,
            error=str(e)
        ).error("Text validation failed")
        raise HTTPException(status_code=400, detail="Invalid text ID")
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="File must be an audio file")
    
    # Create directory structure: YIL/AY/DD/
    now = datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")
    
    # Create meaningful filename with timestamp
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    original_name = os.path.splitext(file.filename)[0] if file.filename else "audio"
    # Clean filename (remove special characters)
    clean_name = "".join(c for c in original_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    if not clean_name:
        clean_name = "audio"
    
    file_ext = os.path.splitext(file.filename)[1] if file.filename else '.wav'
    if not file_ext.startswith('.'):
        file_ext = '.wav'
    
    # Create filename: YYYYMMDD_HHMMSS_clean_name.ext
    filename = f"{timestamp}_{clean_name}{file_ext}"
    
    dir_path = os.path.join(settings.media_root, year, month, day)
    os.makedirs(dir_path, exist_ok=True)
    
    file_path = os.path.join(dir_path, filename)
    
    # Save file
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # DEBUG: Log file upload details
        app_logger.bind(
            request_id=request_id,
            text_id=text_id,
            original_filename=file.filename,
            saved_filename=filename,
            file_path=file_path,
            size_bytes=len(content)
        ).info("Audio file saved successfully")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Extract audio metadata
    duration_ms = None
    sample_rate = None
    try:
        data, sr = sf.read(file_path)
        duration_ms = int(len(data) / sr * 1000)  # Convert to milliseconds
        sample_rate = sr
    except Exception as e:
        # If we can't read the file, continue without metadata
        pass
    
    # Create AudioFileDoc
    audio_doc = AudioFileDoc(
        original_name=file.filename,
        path=file_path,
        duration_ms=duration_ms,
        sr=sample_rate
    )
    await audio_doc.insert()
    
    # Create AnalysisDoc
    analysis_doc = AnalysisDoc(
        text_id=text_obj_id,
        audio_id=str(audio_doc.id),
        status="queued"
    )
    await analysis_doc.insert()
    
    # Queue analysis job
    try:
        job = redis_conn.queue.enqueue("worker.jobs.analyze_audio", str(analysis_doc.id))
        
        # DEBUG: Log job queued
        app_logger.bind(
            request_id=request_id,
            analysis_id=str(analysis_doc.id),
            job_id=str(job.id) if hasattr(job, 'id') else None
        ).debug("Analysis job queued successfully")
        
    except Exception as e:
        # If queue fails, mark analysis as failed
        analysis_doc.status = "failed"
        analysis_doc.error = f"Failed to queue job: {str(e)}"
        await analysis_doc.save()
        raise HTTPException(status_code=500, detail="Failed to queue analysis job")
    
    return UploadResponse(analysis_id=str(analysis_doc.id))


@router.get("/status/{analysis_id}")
async def get_analysis_status(analysis_id: str):
    """Get analysis processing status"""
    try:
        analysis = await AnalysisDoc.get(analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return {
            "analysis_id": str(analysis.id),
            "status": analysis.status,
            "started_at": analysis.started_at,
            "finished_at": analysis.finished_at,
            "error": analysis.error
        }
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid analysis ID")
