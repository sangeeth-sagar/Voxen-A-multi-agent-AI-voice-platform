import enum
import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean, Column, DateTime, Enum as SQLEnum,
    Float, ForeignKey, Integer, String
)
from sqlalchemy.orm import relationship
from app.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER  = "user"


class User(Base):
    __tablename__ = "users"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    uuid             = Column(String, unique=True, nullable=False,
                              default=lambda: str(uuid.uuid4()))
    email            = Column(String, unique=True, nullable=False, index=True)
    username         = Column(String, unique=True, nullable=False, index=True)
    hashed_password  = Column(String, nullable=False)
    role             = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    is_active        = Column(Boolean, default=True, nullable=False)
    total_jobs       = Column(Integer, default=0)
    total_tokens     = Column(Integer, default=0)
    total_cost_usd   = Column(Float, default=0.0)
    created_at       = Column(DateTime, default=datetime.utcnow)
    last_login       = Column(DateTime, nullable=True)

    plans        = relationship("Plan", back_populates="user",
                                foreign_keys="Plan.user_id")
    agent_configs = relationship("AgentConfig", back_populates="user")