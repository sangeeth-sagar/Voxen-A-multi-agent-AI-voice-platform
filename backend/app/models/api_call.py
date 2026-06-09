import uuid
from datetime import datetime
from sqlalchemy import (
    Column, DateTime, Float, ForeignKey, Integer, String, Text
)
from sqlalchemy.orm import relationship
from app.database import Base


class ApiCall(Base):
    __tablename__ = "api_calls"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(
        Integer,
        ForeignKey("agent_configs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id = Column(String, nullable=True, index=True)
    user_text = Column(Text, nullable=True)
    agent_response = Column(Text, nullable=True)
    stt_latency_ms = Column(Float, nullable=True)
    webhook_latency_ms = Column(Float, nullable=True)
    tts_latency_ms = Column(Float, nullable=True)
    total_latency_ms = Column(Float, nullable=True)
    webhook_status = Column(Integer, nullable=True)
    webhook_error_message = Column(Text, nullable=True)
    audio_duration_seconds = Column(Float, nullable=True)
    characters_count = Column(Integer, nullable=True)
    language = Column(String, default="en")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    agent = relationship("AgentConfig", backref="api_calls")
