import re
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import validates
from sqlalchemy.orm import relationship
from app.database import Base


_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]+$")


class AgentTool(Base):
    __tablename__ = "agent_tools"

    id                = Column(Integer, primary_key=True, autoincrement=True)
    agent_id          = Column(Integer, ForeignKey("agent_configs.id", ondelete="CASCADE"), nullable=False, index=True)
    name              = Column(String(64), nullable=False)
    description       = Column(Text, nullable=False)
    parameters_schema = Column(JSON, nullable=False, default=dict)
    target_url        = Column(String(500), nullable=False)
    http_method       = Column(String(10), default="POST")
    is_active         = Column(Boolean, default=True)
    created_at        = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("agent_id", "name", name="uq_agent_tools_agent_name"),
    )

    agent = relationship("AgentConfig", back_populates="custom_tools")

    @validates("name")
    def validate_name(self, key, value):
        if not _NAME_RE.match(value):
            raise ValueError(f"Tool name must match [a-zA-Z0-9_-], got: {value!r}")
        if len(value) > 64:
            raise ValueError("Tool name must be 64 characters or fewer")
        return value
