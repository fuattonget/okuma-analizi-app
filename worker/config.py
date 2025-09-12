from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Media settings
    media_root: str = "./media"
    
    # Whisper settings
    long_pause_ms: int = 800
    whisper_model: str = "medium"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    
    # Database settings
    mongo_uri: str = "mongodb://mongo:27017"
    mongo_db: str = "okuma_analizi"
    
    # DEBUG settings
    debug: bool = False
    log_level: str = "INFO"
    log_format: str = "pretty"
    log_file: str = "./logs/worker.log"
    trace_slow_ms: int = 250
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
