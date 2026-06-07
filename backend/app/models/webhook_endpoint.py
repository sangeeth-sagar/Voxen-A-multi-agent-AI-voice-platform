from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String
)
from sqlalchemy.sql import func
from app.database import Base


class WebhookEndpoint(Base):
    __tablename__ = "webhook_endpoints"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(
        Integer,
        ForeignKey("agent_configs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    webhook_secret = Column(String(100), nullable=False, unique=True)
    webhook_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, server_default="true", nullable=False)
    created_at = Column(DateTime, server_default=func.now())
