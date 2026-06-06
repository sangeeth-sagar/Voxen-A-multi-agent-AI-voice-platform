from pydantic_settings import BaseSettings
from typing import List
import secrets

class Settings(BaseSettings):
    app_name: str = "AgentIQ"
    app_version: str = "2.4.0"
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # Database configuration
    database_url: str = "postgresql://postgres:postgres@localhost:5432/agentiq"
    
    # API keys
    google_api_key: str = ""
    secret_key: str = "change-me-in-production-use-32-chars"
    groq_api_key: str = ""
    
    # Security
    jwt_secret: str = "change-me-to-32-char-random-string-in-production"
    jwt_expire_minutes: int = 1440
    
    # Limits
    max_agents_per_user: int = 20
    max_file_upload_mb: int = 10
    
    # LLM configuration
    model_name: str = "gemini-3.1-flash-lite"
    
    # TTS - Edge TTS
    tts_voice: str = "en-IN-NeerjaNeural"
    tts_voice_male: str = "en-IN-PrabhatNeural"
    
    # Wake word engine
    wake_word_sensitivity: float = 0.5
    
    # RAG / Knowledge base
    chroma_persist_dir: str = "./chroma_db"
    embedding_model: str = "all-MiniLM-L6-v2"
    rag_top_k: int = 4
    
    # Webhook base URL (set in .env for production)
    webhook_base_url: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

def get_settings():
    return Settings()