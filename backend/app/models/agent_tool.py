import re
import uuid as py_uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import validates
from sqlalchemy.orm import relationship
from app.database import Base


_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]+$")


class AgentTool(Base):
    __tablename__ = "agent_tools"

    id                = Column(Integer, primary_key=True, autoincrement=True)
    uuid              = Column(String, unique=True, nullable=False, default=lambda: str(py_uuid.uuid4()))
    agent_id          = Column(Integer, ForeignKey("agent_configs.id", ondelete="CASCADE"), nullable=False, index=True)
    name              = Column(String(64), nullable=False)
    description       = Column(Text, nullable=False)
    parameters_schema = Column(JSON, nullable=False, default=dict)
    target_url        = Column(String(500), nullable=False)
    http_method       = Column(String(10), default="POST")
    is_active         = Column(Boolean, default=True)
    created_at        = Column(DateTime, default=datetime.utcnow)

    @property
    def webhook_url(self) -> str:
        return self.target_url

    @webhook_url.setter
    def webhook_url(self, value: str):
        self.target_url = value

    @property
    def parameters(self) -> list:
        properties = (self.parameters_schema or {}).get("properties", {})
        required = set((self.parameters_schema or {}).get("required", []))
        
        param_list = []
        for prop_name, prop_schema in properties.items():
            param_list.append({
                "name": prop_name,
                "type": prop_schema.get("type", "string"),
                "description": prop_schema.get("description", ""),
                "required": prop_name in required
            })
        return param_list

    @parameters.setter
    def parameters(self, param_list: list):
        properties = {}
        required = []
        
        for p in param_list or []:
            name = p.get("name")
            if not name:
                continue
            properties[name] = {
                "type": p.get("type", "string"),
                "description": p.get("description", "")
            }
            if p.get("required"):
                required.append(name)
                
        self.parameters_schema = {
            "type": "object",
            "properties": properties,
            "required": required
        }

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
