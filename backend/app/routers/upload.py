from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Union
from typing import Optional
import os
import uuid
import tempfile
from datetime import datetime
import soundfile as sf
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from app.config import settings
from app.models.documents import AudioFileDoc, AnalysisDoc, TextDoc
from app.db import redis_conn
from app.logging_config import app_logger
from app.storage import upload_audio_file, get_storage
from app.crud import insert_audio
from app.schemas import AudioResponse

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
    
    # Save file temporarily for processing
    try:
        content = await file.read()
        
        # Create temporary file for processing
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1] if file.filename else '.wav') as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Extract audio metadata
        duration_ms = None
        duration_sec = None
        sample_rate = None
        try:
            data, sr = sf.read(temp_file_path)
            duration_sec = len(data) / sr  # Duration in seconds
            duration_ms = int(duration_sec * 1000)  # Convert to milliseconds
            sample_rate = sr
        except Exception as e:
            app_logger.bind(
                request_id=request_id,
                error=str(e)
            ).warning("Could not extract audio metadata")
        
        # Upload to GCS
        try:
            gcs_result = upload_audio_file(
                text_id=text_id,
                original_name=file.filename or "audio",
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
        
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")
    
    # Create AudioFileDoc with GCS metadata
    audio_payload = {
        "text_id": text_id,
        "original_name": file.filename or "audio",
        "path": gcs_result["gs_uri"],  # Store GCS URI as path for backward compatibility
        "storage_name": gcs_result["blob_name"],
        "gcs_url": gcs_result["public_url"],
        "gcs_uri": gcs_result["gs_uri"],
        "content_type": file.content_type,
        "size_bytes": gcs_result["size_bytes"],
        "md5_hash": gcs_result["md5"],
        "duration_ms": duration_ms,
        "duration_sec": duration_sec,
        "sr": sample_rate,
        "uploaded_at": datetime.utcnow()
    }
    
    audio_doc = await insert_audio(audio_payload)
    
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


@router.post("/audios", response_model=AudioResponse)
@limiter.limit("10/minute")
async def upload_standalone_audio(
    request: Request,
    file: UploadFile = File(...),
    text_id: Optional[str] = Form(None),
    uploaded_by: Optional[str] = Form(None)
):
    """
    Upload standalone audio file to GCS and save metadata to MongoDB.
    
    - **file**: Audio file (mp3, wav, m4a, etc.)
    - **text_id**: Optional text ID to associate with existing text
    - **uploaded_by**: Optional user identifier
    """
    
    request_id = getattr(request.state, 'request_id', None)
    app_logger.bind(
        request_id=request_id,
        filename=file.filename,
        text_id=text_id,
        uploaded_by=uploaded_by,
        content_type=file.content_type
    ).info("Standalone audio upload started")
    
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
    
    # Validate text_id if provided
    if text_id:
        try:
            text = await TextDoc.find_one(TextDoc.text_id == text_id)
            if not text:
                raise HTTPException(status_code=404, detail="Text not found")
        except Exception as e:
            app_logger.bind(
                request_id=request_id,
                text_id=text_id,
                error=str(e)
            ).error("Text validation failed")
            raise HTTPException(status_code=400, detail="Invalid text ID")
    
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
                text_id=text_id,
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
            "text_id": text_id,
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
        
        # Convert to response format
        response_data = {
            "id": str(audio_doc.id),
            "text_id": audio_doc.text_id,
            "original_name": audio_doc.original_name,
            "path": audio_doc.path,
            "storage_name": audio_doc.storage_name,
            "gcs_url": audio_doc.gcs_url,
            "gcs_uri": audio_doc.gcs_uri,
            "content_type": audio_doc.content_type,
            "size_bytes": audio_doc.size_bytes,
            "md5_hash": audio_doc.md5_hash,
            "duration_ms": int(audio_doc.duration_sec * 1000) if audio_doc.duration_sec else None,
            "duration_sec": audio_doc.duration_sec,
            "sr": None,  # Not calculated for standalone uploads
            "uploaded_at": audio_doc.uploaded_at.isoformat(),
            "uploaded_by": audio_doc.uploaded_by,
            "created_at": audio_doc.created_at.isoformat() if hasattr(audio_doc, 'created_at') and audio_doc.created_at else None,
            "updated_at": audio_doc.updated_at.isoformat() if hasattr(audio_doc, 'updated_at') and audio_doc.updated_at else None
        }
        
        return AudioResponse(**response_data)
        
    except Exception as e:
        app_logger.bind(
            request_id=request_id,
            error=str(e)
        ).error("Failed to save audio document to MongoDB")
        raise HTTPException(status_code=500, detail=f"Failed to save audio metadata: {str(e)}")
