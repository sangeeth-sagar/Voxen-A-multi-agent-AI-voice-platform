import secrets
from datetime import datetime
from sqlalchemy import (
    Column, DateTime, ForeignKey, Integer, String, Boolean
)
from sqlalchemy.orm import relationship
from app.database import Base

class VoxenApiKey(Base):
    __tablename__ = "voxen_api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agent_configs.id", ondelete="CASCADE"), nullable=False, index=True)
    api_key = Column(String, unique=True, nullable=False, index=True)
    label = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="voxen_api_keys")
    agent = relationship("AgentConfig", backref="voxen_api_keys")

    @staticmethod
    def generate_key_string() -> str:
        return f"vx_live_{secrets.token_hex(24)}"
