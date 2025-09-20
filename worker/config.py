from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class Settings(BaseSettings):
    # Media settings
    media_root: str = "./media"
    
    # ElevenLabs Speech-to-Text settings
    long_pause_ms: int = 500
    elevenlabs_api_key: str = ""
    elevenlabs_model: str = "scribe_v1"
    elevenlabs_language: str = "tr"  # Turkish
    elevenlabs_temperature: float = 0.0
    
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
