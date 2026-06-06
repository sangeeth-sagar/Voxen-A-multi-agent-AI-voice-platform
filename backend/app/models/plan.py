from datetime import datetime
import uuid
from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, String, Text, JSON
)
from sqlalchemy.ext.mutable import MutableList
import enum
from sqlalchemy.orm import relationship
from app.database import Base


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Plan(Base):
    __tablename__ = "plans"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    job_id         = Column(String, unique=True, nullable=False, index=True)
    user_id        = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    user           = relationship("User", back_populates="plans", foreign_keys=[user_id])
    status         = Column(String, default=JobStatus.PENDING, nullable=False)
    user_prompt    = Column(Text, nullable=True)
    structured_json = Column(JSON, nullable=True)
    markdown_output = Column(Text, nullable=True)
    error_message   = Column(Text, nullable=True)
    created_at     = Column(DateTime, default=datetime.utcnow)
    updated_at     = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AgentTrace(Base):
    __tablename__ = "agent_traces"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    plan_id    = Column(Integer, ForeignKey("plans.id"), nullable=False, index=True)
    agent_name = Column(String, nullable=False)
    agent_type = Column(String, nullable=False)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    started_at = Column(DateTime, nullable=False)
    ended_at   = Column(DateTime, nullable=True)
    duration_s = Column(Integer, nullable=True)
    tokens_in  = Column(Integer, nullable=True)
    tokens_out = Column(Integer, nullable=True)
    cost_usd   = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to Plan (optional, but useful for querying)
    plan = relationship("Plan", backref="agent_traces")


class ConversationSession(Base):
    __tablename__ = "conversation_sessions"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    session_id   = Column(String, unique=True, nullable=False,
                          default=lambda: str(uuid.uuid4()))
    user_id      = Column(Integer, ForeignKey("users.id"), 
                          nullable=True)
    agent_id     = Column(Integer, ForeignKey("agent_configs.id"),
                          nullable=True)
    messages     = Column(MutableList.as_mutable(JSON), default=list)
    created_at   = Column(DateTime, default=datetime.utcnow)
    updated_at   = Column(DateTime, default=datetime.utcnow,
                          onupdate=datetime.utcnow)
    is_active    = Column(Boolean, default=True)