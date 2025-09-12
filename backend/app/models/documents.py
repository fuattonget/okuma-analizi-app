from beanie import Document, Indexed
from pydantic import Field
from pydantic import BaseModel
from typing import Union
from typing import Optional, Literal, Dict, Any
from datetime import datetime


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
        indexes = ["text_id", "grade", "active", "-created_at"]


class AudioFileDoc(Document):
    original_name: str
    path: str
    duration_ms: Optional[int] = None
    sr: Optional[int] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "audio_files"


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
        indexes = ["-created_at", "status"]


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
        indexes = ["analysis_id", [("analysis_id", 1), ("idx", 1)]]


class PauseEventDoc(Document):
    analysis_id: str
    after_word_idx: int
    start_ms: float
    end_ms: float
    duration_ms: float
    
    class Settings:
        name = "pause_events"
        indexes = [["analysis_id", "after_word_idx"]]

