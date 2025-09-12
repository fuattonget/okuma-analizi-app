from beanie import Document
from pydantic import Field
from pydantic import BaseModel
from typing import Union
from typing import Optional, Literal, Dict, Any
from datetime import datetime
from pymongo import IndexModel, ASCENDING, DESCENDING

print("📄 Loading document models...")


class TextDoc(Document):
    text_id: str  # sınıf seviyesi + title otomatik oluşturulacak
    grade: int  # sınıf seviyesi int olarak
    title: str  # metin başlığı
    body: str  # metin içeriği
    comment: Optional[str] = None  # metin hakkında oluşturan kişinin yorumu
    created_at: datetime = Field(default_factory=datetime.utcnow)  # metin oluşturulma tarih ve saati
    active: bool = True  # metin silinmiş yada aktif metin mi
    
    class Settings:
        name = "texts"
        indexes = [
            IndexModel([("text_id", ASCENDING)], name="texts_text_id_asc", unique=True),
            IndexModel([("grade", ASCENDING)], name="texts_grade_asc"),
            IndexModel([("created_at", DESCENDING)], name="texts_created_at_desc"),
        ]

print("✅ TextDoc model loaded")


class AudioFileDoc(Document):
    # Original fields
    original_name: str
    path: str
    duration_ms: Optional[int] = None
    sr: Optional[int] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    
    # GCS metadata fields
    text_id: Optional[str] = None
    storage_name: str  # GCS blob name
    gcs_url: str  # public URL
    gcs_uri: str  # gs://bucket/path
    content_type: Optional[str] = None
    size_bytes: Optional[int] = None
    md5_hash: Optional[str] = None
    duration_sec: Optional[float] = None  # duration in seconds (more precise than ms)
    uploaded_by: Optional[str] = None  # future user ID
    
    class Settings:
        name = "audio_files"
        indexes = [
            IndexModel([("storage_name", ASCENDING)], name="audios_storage_name_asc", unique=True),
            IndexModel([("gcs_uri", ASCENDING)], name="audios_gcs_uri_asc", unique=True),
            IndexModel([("text_id", ASCENDING)], name="audios_text_id_asc"),
            IndexModel([("uploaded_at", DESCENDING)], name="audios_uploaded_at_desc"),
        ]

print("✅ AudioFileDoc model loaded")


class AnalysisDoc(Document):
    text_id: str
    audio_id: str
    status: Literal["queued", "running", "done", "failed"] = "queued"
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    summary: Dict[str, Any] = {}
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "analyses"
        indexes = [
            IndexModel([("text_id", ASCENDING)], name="analyses_text_id_asc"),
            IndexModel([("audio_id", ASCENDING)], name="analyses_audio_id_asc"),
            IndexModel([("created_at", DESCENDING)], name="analyses_created_at_desc"),
            IndexModel([("status", ASCENDING)], name="analyses_status_asc"),
        ]

print("✅ AnalysisDoc model loaded")


class WordEventDoc(Document):
    analysis_id: str
    idx: int
    ref_token: Optional[str] = None
    hyp_token: Optional[str] = None
    start_ms: Optional[float] = None
    end_ms: Optional[float] = None
    type: Literal["correct", "missing", "extra", "diff"]
    subtype: Optional[Literal["harf_ek", "harf_cik", "degistirme", "hece_ek", "hece_cik"]] = None
    details: Dict[str, Any] = {}
    
    class Settings:
        name = "word_events"
        indexes = [
            IndexModel([("analysis_id", ASCENDING), ("idx", ASCENDING)], name="word_events_analysis_idx_asc"),
            IndexModel([("analysis_id", ASCENDING)], name="word_events_analysis_id_asc"),
        ]

print("✅ WordEventDoc model loaded")


class PauseEventDoc(Document):
    analysis_id: str
    after_word_idx: int
    start_ms: float
    end_ms: float
    duration_ms: float
    
    class Settings:
        name = "pause_events"
        indexes = [
            IndexModel([("analysis_id", ASCENDING), ("after_word_idx", ASCENDING)], name="pause_events_analysis_word_asc"),
            IndexModel([("analysis_id", ASCENDING)], name="pause_events_analysis_id_asc"),
        ]

print("✅ PauseEventDoc model loaded")
print("🎉 All document models loaded successfully")

