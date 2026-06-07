from sqlalchemy import Column, ForeignKey, Integer, String
from app.database import Base


class AgentApiKeyAssignment(Base):
    __tablename__ = "agent_api_key_assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(
        Integer,
        ForeignKey("agent_configs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    llm_provider = Column(String(50), nullable=True)
    llm_api_key_id = Column(
        Integer, ForeignKey("user_api_keys.id"), nullable=True
    )
    tts_provider = Column(String(50), nullable=True)
    tts_api_key_id = Column(
        Integer, ForeignKey("user_api_keys.id"), nullable=True
    )
    stt_provider = Column(String(50), nullable=True)
    stt_api_key_id = Column(
        Integer, ForeignKey("user_api_keys.id"), nullable=True
    )
