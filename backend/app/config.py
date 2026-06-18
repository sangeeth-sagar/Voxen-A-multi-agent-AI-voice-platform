from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "AgentIQ"
    app_version: str = "2.4.0"
    
    # The Union type tells Pydantic not to crash if Render passes a plain string
    cors_origins: Union[List[str], str] = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        # If it's already a list (like from our defaults), keep it
        if isinstance(v, list):
            return v
        # If it's a string from the Render environment variable
        if isinstance(v, str):
            # If the string is empty, fallback to defaults safely
            if not v.strip():
                return ["http://localhost:5173", "http://localhost:3000"]
            # Split the comma-separated URLs into a proper Python list
            return [i.strip() for i in v.split(",") if i.strip()]
        return ["http://localhost:5173", "http://localhost:3000"]

    # Database configuration
    database_url: str = "postgresql://postgres:postgres@localhost:5432/agentiq"

    # API keys
    google_api_key: str = ""   # not used — users add their own keys via Profile UI
    secret_key: str = "change-me-in-production-use-32-chars"
    groq_api_key: str = ""

    # Security
    jwt_secret: str = "change-me-to-32-char-random-string-in-production"
    jwt_expire_minutes: int = 10080  # 7 days

    # Limits
    max_agents_per_user: int = 20
    max_file_upload_mb: int = 10

    # LLM configuration
    model_name: str = "gemini-3.1-flash-lite"        # legacy field used by chat()
    gemini_model: str = "gemini-3.1-flash-lite"
    openai_model: str = "gpt-4o-mini"
    claude_model: str = "claude-haiku-4-5-20251001"

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

    # Encryption for per-user API keys at rest (Fernet)
    encryption_key: str = ""

    # Defaults for new agents
    default_llm_provider: str = "gemini"
    default_tts_provider: str = "elevenlabs"
    default_stt_provider: str = "groq"

    # Superadmin bootstrap
    admin_email: str = "admin@voxen.ai"

    # Analytics tracking (future use)
    track_token_usage: bool = True
    track_response_time: bool = True

    # Rate limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 500

    # Pydantic Settings Configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignores any unrelated environment variables safely
    )

def get_settings():
    return Settings()

settings = get_settings()