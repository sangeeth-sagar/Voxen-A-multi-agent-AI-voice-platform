from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base

class TelegramBotConfig(Base):
    __tablename__ = "telegram_bot_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, ForeignKey("agent_configs.id", ondelete="CASCADE"), nullable=False, index=True)
    telegram_token = Column(String, unique=True, nullable=False)
    bot_username = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    voxen_api_key_id = Column(Integer, ForeignKey("voxen_api_keys.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    agent = relationship("AgentConfig", back_populates="telegram_bot_configs")
    voxen_api_key = relationship("VoxenApiKey")
