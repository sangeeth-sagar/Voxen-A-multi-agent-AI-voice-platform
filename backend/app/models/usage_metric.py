from datetime import date
from sqlalchemy import (
    Column, Date, Float, ForeignKey, Integer
)
from app.database import Base


class UsageMetric(Base):
    __tablename__ = "usage_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(
        Integer,
        ForeignKey("agent_configs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date = Column(Date, nullable=False, index=True)
    total_requests = Column(Integer, default=0)
    successful_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)
    total_latency_sum = Column(Float, default=0.0)
    total_stt_latency_sum = Column(Float, default=0.0)
    total_webhook_latency_sum = Column(Float, default=0.0)
    total_tts_latency_sum = Column(Float, default=0.0)
    peak_concurrent_sessions = Column(Integer, default=0)
    estimated_cost = Column(Float, default=0.0)
    audio_duration_minutes = Column(Float, default=0.0)
    characters_count = Column(Integer, default=0)
