from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class AudioCreate(BaseModel):
    """Schema for creating audio files"""
    text_id: Optional[str] = None
    original_name: str
    storage_name: str
    gcs_uri: str
    content_type: Optional[str] = None
    size_bytes: Optional[int] = None
    md5_hash: Optional[str] = None
    duration_sec: Optional[float] = None
    uploaded_by: Optional[str] = None


class AudioResponse(BaseModel):
    """Schema for audio file responses"""
    id: str
    text_id: Optional[str] = None
    original_name: str
    path: str  # Keep for backward compatibility
    storage_name: str
    gcs_uri: str
    content_type: Optional[str] = None
    size_bytes: Optional[int] = None
    md5_hash: Optional[str] = None
    duration_ms: Optional[int] = None
    duration_sec: Optional[float] = None
    sr: Optional[int] = None
    uploaded_at: str
    uploaded_by: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class AudioUpdate(BaseModel):
    """Schema for updating audio files"""
    text_id: Optional[str] = None
    content_type: Optional[str] = None
    duration_sec: Optional[float] = None
    uploaded_by: Optional[str] = None


class AudioListResponse(BaseModel):
    """Schema for audio file list responses"""
    id: str
    text_id: Optional[str] = None
    original_name: str
    storage_name: str
    content_type: Optional[str] = None
    size_bytes: Optional[int] = None
    duration_sec: Optional[float] = None
    uploaded_at: str
    uploaded_by: Optional[str] = None


# Session-related schemas
class SessionSummary(BaseModel):
    """Schema for reading session summary"""
    id: str
    text_id: str
    audio_id: str
    reader_id: Optional[str] = None
    status: str
    created_at: str
    completed_at: Optional[str] = None


class SessionDetail(BaseModel):
    """Schema for reading session detail"""
    id: str
    text_id: str
    audio_id: str
    reader_id: Optional[str] = None
    status: str
    created_at: str
    completed_at: Optional[str] = None
    text: Dict[str, str]  # {title, body}
    audio: Dict[str, Any]  # audio file info


# Word Event schemas
class WordEventResponse(BaseModel):
    """Schema for word event response"""
    id: str
    analysis_id: str
    position: int
    ref_token: Optional[str] = None
    hyp_token: Optional[str] = None
    type: str
    sub_type: Optional[str] = None
    timing: Optional[Dict[str, float]] = None
    char_diff: Optional[int] = None


# Pause Event schemas
class PauseEventResponse(BaseModel):
    """Schema for pause event response"""
    id: str
    analysis_id: str
    after_position: int
    duration_ms: float
    class_: str
    start_ms: float
    end_ms: float


# Metrics schemas
class MetricsResponse(BaseModel):
    """Schema for analysis metrics response"""
    analysis_id: str
    counts: Dict[str, int]
    wer: float
    accuracy: float
    wpm: float
    long_pauses: Dict[str, Any]
    error_types: Dict[str, int]
