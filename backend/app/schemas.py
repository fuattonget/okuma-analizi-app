from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AudioCreate(BaseModel):
    """Schema for creating audio files"""
    text_id: Optional[str] = None
    original_name: str
    storage_name: str
    gcs_url: str
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
    gcs_url: str
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
    gcs_url: str
    content_type: Optional[str] = None
    size_bytes: Optional[int] = None
    duration_sec: Optional[float] = None
    uploaded_at: str
    uploaded_by: Optional[str] = None
