from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class Settings(BaseSettings):
    # Storage settings (GCS is the default and only supported backend)
    storage_backend: str = "gcs"
    gcs_bucket: str = "doky_ai_audio_storage"
    gcs_credentials_path: Optional[str] = "./gcs-service-account.json"
    gcs_public_base: str = "https://storage.googleapis.com"
    
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
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "okuma_analizi"
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # DEBUG settings
    debug: bool = False
    log_level: str = "INFO"
    log_format: str = "pretty"
    log_file: str = "./logs/app.log"
    trace_slow_ms: int = 250
    
    # Additional environment variables that might be passed
    mongo_url: Optional[str] = None
    redis_url: Optional[str] = None
    api_debug: Optional[bool] = None
    gcs_bucket_name: Optional[str] = None
    gcs_project_id: Optional[str] = None
    google_application_credentials: Optional[str] = None
    secret_key: Optional[str] = None
    environment: Optional[str] = None
    
    # Docker-compose environment variables
    gcs_credentials_path: Optional[str] = None
    gcs_bucket: Optional[str] = None
    elevenlabs_model: Optional[str] = None
    elevenlabs_language: Optional[str] = None
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )


settings = Settings()
