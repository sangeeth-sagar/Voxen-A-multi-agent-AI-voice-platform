import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey,
    Integer, JSON, String, Text
)
from sqlalchemy.orm import relationship
from app.database import Base


class AgentConfig(Base):
    __tablename__ = "agent_configs"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    uuid          = Column(String, unique=True, nullable=False,
                           default=lambda: str(uuid.uuid4()))
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name          = Column(String, nullable=False)
    description   = Column(Text, nullable=True)
    agent_type    = Column(String, default="business_intel")
    system_prompt = Column(Text, nullable=True)
    tools_enabled = Column(JSON, default=lambda: ["web_search","memory","critic"])
    output_format = Column(String, default="markdown")
    is_public     = Column(Boolean, default=False)
    is_template   = Column(Boolean, default=False)
    template_name = Column(String, nullable=True)
    use_count     = Column(Integer, default=0)
    created_at    = Column(DateTime, default=datetime.utcnow)
    # Voice agent fields
    is_voice_agent       = Column(Boolean, default=False)
    voice_language       = Column(String, default="en-US")
    voice_system_prompt  = Column(Text, nullable=True)
    knowledge_base_text  = Column(Text, nullable=True)
    # Wake word / activation
    wake_word            = Column(String, nullable=False, default="Nova")
    is_active            = Column(Boolean, default=False)
    webhook_id           = Column(String, nullable=True, unique=True)
    webhook_url          = Column(String, nullable=True)
    # Knowledge base
    kb_enabled           = Column(Boolean, default=False)
    kb_collection_name   = Column(String, nullable=True)
    # Welcome messages (no LLM, direct TTS)
    wake_confirm_message = Column(
        String,
        default="Hey {agent_name}"
    )
    welcome_message      = Column(
        String,
        default="How can I help you today?"
    )

    user = relationship("User", back_populates="agent_configs")