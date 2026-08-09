from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.database import Base

class AgentKnowledgeBase(Base):
    __tablename__ = "agent_knowledge_bases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, ForeignKey("agent_configs.id", ondelete="CASCADE"), nullable=False, index=True)
    source_type = Column(String, nullable=False)  # pdf, url, txt
    source_name = Column(String, nullable=False)
    total_chunks = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    agent = relationship("AgentConfig", back_populates="knowledge_bases")
    embeddings = relationship("VectorEmbedding", back_populates="kb", cascade="all, delete-orphan")


class VectorEmbedding(Base):
    __tablename__ = "vector_embeddings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    kb_id = Column(Integer, ForeignKey("agent_knowledge_bases.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey("agent_configs.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(Vector(384), nullable=False)  # default to 384 for sentence-transformers
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    kb = relationship("AgentKnowledgeBase", back_populates="embeddings")
    agent = relationship("AgentConfig")
