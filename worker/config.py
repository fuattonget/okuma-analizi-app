from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class Settings(BaseSettings):
    # Media settings
    media_root: str = "./media"
    
    # ElevenLabs Speech-to-Text settings
    long_pause_ms: int = 500
    elevenlabs_api_key: str = ""
    elevenlabs_model: str = "scribe_v1"  # or "scribe_v1_experimental" for better quality
    elevenlabs_language: str = "tr"  # Turkish
    elevenlabs_temperature: float = 0.0  # 0.0 for deterministic, 0.2-0.5 for more creative
    elevenlabs_seed: int = 12456  # Random seed for reproducibility
    elevenlabs_remove_filler_words: bool = False  # Keep filler words for analysis
    elevenlabs_remove_disfluencies: bool = False  # Keep disfluencies (repetitions, false starts)
    
    # Database settings
    mongo_uri: str = "mongodb://mongodb:27017"
    mongo_db: str = "okuma_analizi"
    
    # GCS settings
    gcs_credentials_path: str = "./gcs-service-account.json"
    gcs_bucket: str = "doky_ai_audio_storage"
    
    # DEBUG settings
    debug: bool = True
    log_level: str = "DEBUG"
    log_format: str = "pretty"
    log_file: str = "./logs/worker.log"
    trace_slow_ms: int = 250
    
    # Environment variables from docker-compose
    mongo_url: Optional[str] = None
    redis_url: Optional[str] = None
    gcs_bucket_name: Optional[str] = None
    gcs_project_id: Optional[str] = None
    google_application_credentials: Optional[str] = None
    environment: Optional[str] = None
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )


settings = Settings()
