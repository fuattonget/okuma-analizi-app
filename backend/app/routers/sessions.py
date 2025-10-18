from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from app.utils.timezone import get_utc_now
from app.models.documents import ReadingSessionDoc, AnalysisDoc, TextDoc, AudioFileDoc
from app.schemas import SessionSummary, SessionDetail
from app.logging_config import app_logger

router = APIRouter()


@router.get("/", response_model=List[SessionSummary])
async def get_sessions(
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by status: active, completed, cancelled"),
    reader_id: Optional[str] = Query(None, description="Filter by reader ID")
):
    """Get reading sessions list with pagination and filtering"""
    
    # Build query
    query = {}
    if status:
        query["status"] = status
    if reader_id:
        query["reader_id"] = reader_id
    
    # Get sessions ordered by created_at desc
    sessions = await ReadingSessionDoc.find(query).sort("-created_at").limit(limit).to_list()
    
    if not sessions:
        return []
    
    # Build response
    result = []
    for session in sessions:
        session_data = {
            "id": str(session.id),
            "text_id": str(session.text_id),
            "audio_id": str(session.audio_id),
            "reader_id": session.reader_id,
            "status": session.status,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None
        }
        result.append(SessionSummary(**session_data))
    
    app_logger.info(f"Retrieved {len(result)} reading sessions")
    return result


@router.get("/{session_id}", response_model=SessionDetail)
async def get_session(session_id: str):
    """Get detailed reading session by ID"""
    
    try:
        session = await ReadingSessionDoc.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Reading session not found")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid session ID")
    
    # Get related text
    text = await TextDoc.get(session.text_id)
    if not text:
        raise HTTPException(status_code=404, detail="Related text not found")
    
    # Get related audio
    audio = await AudioFileDoc.get(session.audio_id)
    if not audio:
        raise HTTPException(status_code=404, detail="Related audio not found")
    
    # Build response
    response_data = {
        "id": str(session.id),
        "text_id": str(session.text_id),
        "audio_id": str(session.audio_id),
        "reader_id": session.reader_id,
        "status": session.status,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        "text": {
            "title": text.title,
            "body": text.body
        },
        "audio": {
            "id": str(audio.id),
            "original_name": audio.original_name,
            "storage_name": audio.storage_name,
            "content_type": audio.content_type,
            "size_bytes": audio.size_bytes,
            "duration_sec": audio.duration_sec,
            "uploaded_at": audio.uploaded_at.isoformat()
        }
    }
    
    return SessionDetail(**response_data)


@router.get("/{session_id}/analyses", response_model=List[dict])
async def get_session_analyses(
    session_id: str,
    limit: int = Query(20, ge=1, le=100)
):
    """Get analyses for a specific reading session"""
    
    try:
        session = await ReadingSessionDoc.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Reading session not found")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid session ID")
    
    # Get analyses for this session
    analyses = await AnalysisDoc.find(
        {"session_id": session.id}
    ).sort("-created_at").limit(limit).to_list()
    
    if not analyses:
        return []
    
    # Build response
    result = []
    for analysis in analyses:
        analysis_data = {
            "id": str(analysis.id),
            "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
            "status": analysis.status,
            "started_at": analysis.started_at.isoformat() if analysis.started_at else None,
            "finished_at": analysis.finished_at.isoformat() if analysis.finished_at else None,
            "error": analysis.error,
            "summary": analysis.summary or {}
        }
        result.append(analysis_data)
    
    app_logger.info(f"Retrieved {len(result)} analyses for session {session_id}")
    return result


@router.put("/{session_id}/status")
async def update_session_status(
    session_id: str,
    status: str = Query(..., description="New status: active, completed, cancelled")
):
    """Update reading session status"""
    
    if status not in ["active", "completed", "cancelled"]:
        raise HTTPException(status_code=400, detail="Invalid status. Must be: active, completed, cancelled")
    
    try:
        session = await ReadingSessionDoc.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Reading session not found")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid session ID")
    
    # Update status
    session.status = status
    if status == "completed":
        session.completed_at = get_utc_now()
    await session.save()
    
    app_logger.info(f"Updated session {session_id} status to {status}")
    return {"message": f"Session status updated to {status}", "session_id": session_id}

