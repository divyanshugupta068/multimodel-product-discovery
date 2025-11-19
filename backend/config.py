from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    # API Keys
    openai_api_key: str
    anthropic_api_key: str
    deepgram_api_key: str = ""
    
    # Database
    database_url: str = "postgresql://user:password@localhost:5432/product_discovery"
    redis_url: str = "redis://localhost:6379/0"
    chroma_persist_dir: str = "./data/chroma_db"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Model Configuration
    default_vision_model: str = "gpt-4-vision-preview"
    fallback_vision_model: str = "claude-3-5-sonnet-20240620"
    default_text_model: str = "gpt-4-turbo-preview"
    embedding_model: str = "text-embedding-3-small"
    
    # Feature Flags
    enable_vision_processing: bool = True
    enable_speech_processing: bool = True
    enable_caching: bool = True
    enable_metrics: bool = True
    
    # Performance Settings
    max_concurrent_requests: int = 10
    request_timeout: int = 30
    cache_ttl: int = 3600
    
    # Logging
    log_level: str = "INFO"
    sentry_dsn: str = ""
    
    # Evaluation
    eval_dataset_path: str = "./data/evaluation/test_cases.json"
    eval_output_path: str = "./evaluation/results/"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
