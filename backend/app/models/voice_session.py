import uuid
from datetime import datetime
from sqlalchemy import (
    Column, DateTime, Float, ForeignKey, Integer, String
)
from sqlalchemy.orm import relationship
from app.database import Base


class VoiceSession(Base):
    __tablename__ = "voice_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(
        Integer,
        ForeignKey("agent_configs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    total_calls = Column(Integer, default=0)
    total_duration_seconds = Column(Float, default=0.0)

    agent = relationship("AgentConfig", backref="voice_sessions")
