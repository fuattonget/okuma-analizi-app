from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from typing import Union
from app.models.documents import AnalysisDoc, TextDoc, AudioFileDoc, WordEventDoc, PauseEventDoc
from app.config import settings
import os

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
            "audio_id": str(analysis.audio_id)
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
    # Convert absolute path to relative path for media URL
    audio_path = audio.path
    if audio_path.startswith(settings.media_root):
        relative_path = os.path.relpath(audio_path, settings.media_root)
        audio_url = f"/media/{relative_path}"
    else:
        # Fallback if path doesn't start with media_root
        audio_url = f"/media/{os.path.basename(audio_path)}"
    
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
