from beanie import Document
from pydantic import Field, BaseModel, ConfigDict, field_serializer, field_validator
from typing import Optional, Literal, Dict, Any, List
from datetime import datetime, timezone, timedelta
from app.utils.timezone import get_utc_now, to_utc
from pymongo import IndexModel, ASCENDING, DESCENDING
from bson import ObjectId
import pytz

print("📄 Loading document models...")


class TurkishDateTime:
    """Custom datetime field that preserves Turkish timezone in MongoDB"""
    
    @staticmethod
    def __get_validators__():
        yield TurkishDateTime.validate
    
    @classmethod
    def validate(cls, value):
        if isinstance(value, str):
            # Parse ISO string
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        elif isinstance(value, datetime):
            dt = value
        else:
            raise ValueError(f"Invalid datetime value: {value}")
        
        # Ensure it has Turkish timezone
        if dt.tzinfo is None:
            # Assume it's Turkish time if no timezone
            dt = dt.replace(tzinfo=timezone(timedelta(hours=3)))
        elif dt.tzinfo != timezone(timedelta(hours=3)):
            # Convert to Turkish timezone
            dt = dt.astimezone(timezone(timedelta(hours=3)))
        
        return dt
    
    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type='string', format='date-time')


class CanonicalTokens(BaseModel):
    """Canonical tokenization structure"""
    tokens: List[str] = Field(default_factory=list)


class HashInfo(BaseModel):
    """Hash information for files"""
    md5: Optional[str] = None
    sha256: Optional[str] = None


class PrivacyInfo(BaseModel):
    """Privacy and retention information"""
    retention_policy: Optional[str] = None


class OwnerInfo(BaseModel):
    """Owner information"""
    reader_id: Optional[str] = None


class TextDoc(Document):
    """Text document model with slug-based identification"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    slug: str  # unique slug identifier
    grade: int  # sınıf seviyesi int olarak
    title: str  # metin başlığı
    body: str  # metin içeriği
    canonical: CanonicalTokens = Field(default_factory=lambda: CanonicalTokens())  # canonical tokenization
    comment: Optional[str] = None  # metin hakkında oluşturan kişinin yorumu
    created_at: datetime = Field(default_factory=get_utc_now)
    active: bool = True  # metin silinmiş yada aktif metin mi
    
    @field_validator('created_at', mode='before')
    @classmethod
    def ensure_utc_timezone(cls, value: Optional[datetime]) -> Optional[datetime]:
        """Ensure datetime is in UTC timezone before saving"""
        return to_utc(value)
    
    
    class Settings:
        name = "texts"
        indexes = [
            IndexModel([("slug", ASCENDING)], name="texts_slug_asc", unique=True),
            IndexModel([("grade", ASCENDING)], name="texts_grade_asc"),
            IndexModel([("created_at", DESCENDING)], name="texts_created_at_desc"),
            IndexModel([("active", ASCENDING)], name="texts_active_asc"),
        ]

print("✅ TextDoc model loaded")


class AudioFileDoc(Document):
    """Audio file document model with privacy controls"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    # Core fields
    original_name: str
    duration_ms: Optional[int] = None
    sr: Optional[int] = None
    uploaded_at: datetime = Field(default_factory=get_utc_now)
    
    @field_validator('uploaded_at', mode='before')
    @classmethod
    def ensure_utc_timezone(cls, value: Optional[datetime]) -> Optional[datetime]:
        """Ensure datetime is in UTC timezone before saving"""
        return to_utc(value)
    
    # GCS metadata fields
    text_id: Optional[ObjectId] = None
    storage_name: str  # GCS blob name
    gcs_uri: str  # gs://bucket/path (private access only)
    content_type: Optional[str] = None
    size_bytes: Optional[int] = None
    duration_sec: Optional[float] = None  # duration in seconds (more precise than ms)
    
    # Hash information
    hash: HashInfo = Field(default_factory=HashInfo)
    
    # Privacy and ownership
    privacy: PrivacyInfo = Field(default_factory=PrivacyInfo)
    owner: OwnerInfo = Field(default_factory=OwnerInfo)
    
    
    class Settings:
        name = "audio_files"
        indexes = [
            IndexModel([("storage_name", ASCENDING)], name="audios_storage_name_asc", unique=True),
            IndexModel([("gcs_uri", ASCENDING)], name="audios_gcs_uri_asc", unique=True),
            IndexModel([("text_id", ASCENDING)], name="audios_text_id_asc"),
            IndexModel([("uploaded_at", DESCENDING)], name="audios_uploaded_at_desc"),
            IndexModel([("owner.reader_id", ASCENDING)], name="audios_owner_reader_id_asc"),
        ]

print("✅ AudioFileDoc model loaded")


class ErrorTypes(BaseModel):
    """Normalized error types in summary"""
    missing: int = 0
    extra: int = 0
    substitution: int = 0
    pause_long: int = 0


class AnalysisDoc(Document):
    """Analysis document model with session reference"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    session_id: ObjectId  # reference to ReadingSessionDoc
    status: Literal["queued", "running", "done", "failed"] = "queued"
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    summary: Dict[str, Any] = {}
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=get_utc_now)
    
    @field_validator('created_at', 'started_at', 'finished_at', mode='before')
    @classmethod
    def ensure_utc_timezone(cls, value: Optional[datetime]) -> Optional[datetime]:
        """Ensure datetime is in UTC timezone before saving"""
        return to_utc(value)
    
    
    class Settings:
        name = "analyses"
        indexes = [
            IndexModel([("session_id", ASCENDING)], name="analyses_session_id_asc"),
            IndexModel([("created_at", DESCENDING)], name="analyses_created_at_desc"),
            IndexModel([("status", ASCENDING)], name="analyses_status_asc"),
        ]

print("✅ AnalysisDoc model loaded")


class ReadingSessionDoc(Document):
    """Reading session document model"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    text_id: ObjectId  # reference to TextDoc
    audio_id: ObjectId  # reference to AudioFileDoc
    reader_id: Optional[str] = None
    status: Literal["active", "completed", "cancelled"] = "active"
    created_at: datetime = Field(default_factory=get_utc_now)
    completed_at: Optional[datetime] = None
    
    @field_validator('created_at', 'completed_at', mode='before')
    @classmethod
    def ensure_utc_timezone(cls, value: Optional[datetime]) -> Optional[datetime]:
        """Ensure datetime is in UTC timezone before saving"""
        return to_utc(value)
    
    
    class Settings:
        name = "reading_sessions"
        indexes = [
            IndexModel([("text_id", ASCENDING)], name="sessions_text_id_asc"),
            IndexModel([("audio_id", ASCENDING)], name="sessions_audio_id_asc"),
            IndexModel([("reader_id", ASCENDING)], name="sessions_reader_id_asc"),
            IndexModel([("status", ASCENDING)], name="sessions_status_asc"),
            IndexModel([("created_at", DESCENDING)], name="sessions_created_at_desc"),
        ]

print("✅ ReadingSessionDoc model loaded")


class WordEventDoc(Document):
    """Word-level event document model"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    analysis_id: ObjectId  # reference to AnalysisDoc
    position: int  # position in the text
    ref_token: Optional[str] = None  # reference token
    hyp_token: Optional[str] = None  # hypothesis token
    type: Literal["correct", "missing", "extra", "substitution", "repetition"]  # event type
    sub_type: Optional[str] = None  # detailed sub-type classification
    timing: Optional[Dict[str, float]] = None  # start_ms, end_ms
    char_diff: Optional[int] = None  # character-level difference
    
    class Settings:
        name = "word_events"
        indexes = [
            IndexModel([("analysis_id", ASCENDING)], name="word_events_analysis_id_asc"),
            IndexModel([("position", ASCENDING)], name="word_events_position_asc"),
            IndexModel([("type", ASCENDING)], name="word_events_type_asc"),
            IndexModel([("analysis_id", ASCENDING), ("position", ASCENDING)], name="word_events_analysis_position_asc"),
        ]

print("✅ WordEventDoc model loaded")


class PauseEventDoc(Document):
    """Pause event document model"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    analysis_id: ObjectId  # reference to AnalysisDoc
    after_position: int  # position after which pause occurs
    duration_ms: float  # pause duration in milliseconds
    class_: Literal["short", "medium", "long", "very_long"]  # pause classification
    start_ms: float  # start time in milliseconds
    end_ms: float  # end time in milliseconds
    
    class Settings:
        name = "pause_events"
        indexes = [
            IndexModel([("analysis_id", ASCENDING)], name="pause_events_analysis_id_asc"),
            IndexModel([("after_position", ASCENDING)], name="pause_events_after_position_asc"),
            IndexModel([("class_", ASCENDING)], name="pause_events_class_asc"),
            IndexModel([("duration_ms", DESCENDING)], name="pause_events_duration_ms_desc"),
        ]

print("✅ PauseEventDoc model loaded")


class WordData(BaseModel):
    """Word data structure for STT results"""
    word: str
    start: float
    end: float
    confidence: Optional[float] = None


class SttResultDoc(Document):
    """Speech-to-Text result document model"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    session_id: ObjectId  # reference to ReadingSessionDoc
    provider: str  # STT provider (e.g., "elevenlabs", "whisper")
    model: str  # model name/version
    language: str  # detected language code
    transcript: str  # full transcript text
    words: List[WordData] = Field(default_factory=list)  # word-level data
    created_at: datetime = Field(default_factory=get_utc_now)
    
    class Settings:
        name = "stt_results"
        indexes = [
            IndexModel([("session_id", ASCENDING)], name="stt_results_session_id_asc"),
            IndexModel([("provider", ASCENDING)], name="stt_results_provider_asc"),
            IndexModel([("language", ASCENDING)], name="stt_results_language_asc"),
            IndexModel([("created_at", DESCENDING)], name="stt_results_created_at_desc"),
        ]

print("✅ SttResultDoc model loaded")


print("🎉 All document models loaded successfully")