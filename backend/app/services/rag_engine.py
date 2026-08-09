import structlog
from typing import List
from sqlalchemy.orm import Session
from app.models.agent_knowledge_base import AgentKnowledgeBase, VectorEmbedding
from app.models.agent_config import AgentConfig
from app.services.rag import get_embedding_function, resolve_user_gemini_key
from app.services.document_parser import split_text_recursive

logger = structlog.get_logger(__name__)

async def ingest_kb_document(
    db: Session, 
    agent_id: int, 
    source_type: str, 
    source_name: str, 
    raw_text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> int:
    """
    Chunks text, calculates embeddings, and saves the document metadata and
    pgvector embeddings into PostgreSQL.
    """
    logger.info("kb_ingest_started", agent_id=agent_id, source_name=source_name)
    
    # 1. Chunk document
    chunks = split_text_recursive(raw_text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    if not chunks:
        logger.warning("kb_ingest_no_chunks", agent_id=agent_id, source_name=source_name)
        return 0

    # 2. Resolve agent and their Gemini API Key
    agent = db.query(AgentConfig).filter(AgentConfig.id == agent_id).first()
    if not agent:
        logger.error("kb_ingest_agent_not_found", agent_id=agent_id)
        return 0
    api_key = resolve_user_gemini_key(db, agent.user_id)

    # 3. Get embedding function & generate embeddings
    model = get_embedding_function(api_key)
    embeddings = model(chunks)

    # 3. Create KB source entry
    kb_source = AgentKnowledgeBase(
        agent_id=agent_id,
        source_type=source_type,
        source_name=source_name,
        total_chunks=len(chunks)
    )
    db.add(kb_source)
    db.commit()
    db.refresh(kb_source)

    # 4. Insert Vector Embedding records
    for text_chunk, vector in zip(chunks, embeddings):
        emb_record = VectorEmbedding(
            kb_id=kb_source.id,
            agent_id=agent_id,
            chunk_text=text_chunk,
            embedding=vector,
            metadata_json={"source_name": source_name, "chunk_len": len(text_chunk)}
        )
        db.add(emb_record)
        
    db.commit()
    logger.info("kb_ingest_completed", agent_id=agent_id, source_name=source_name, chunks=len(chunks))
    return len(chunks)


async def query_similar_context(
    db: Session, 
    agent_id: int, 
    query: str, 
    top_k: int = 4, 
    similarity_threshold: float = 0.35
) -> str:
    """
    Computes query embedding and returns matches from pgvector within the similarity threshold.
    """
    if not query or not query.strip():
        return ""

    # Generate query embedding
    agent = db.query(AgentConfig).filter(AgentConfig.id == agent_id).first()
    if not agent:
        return ""
    api_key = resolve_user_gemini_key(db, agent.user_id)

    model = get_embedding_function(api_key)
    query_vector = model([query])[0]

    # Cosine distance = 1 - Cosine similarity
    # We query ordering by distance, and filtering by distance <= (1 - similarity_threshold)
    distance_expr = VectorEmbedding.embedding.cosine_distance(query_vector)
    
    max_distance = 1.0 - similarity_threshold
    
    results = (
        db.query(VectorEmbedding)
        .filter(
            VectorEmbedding.agent_id == agent_id,
            distance_expr <= max_distance
        )
        .order_by(distance_expr)
        .limit(top_k)
        .all()
    )

    if not results:
        return ""

    context_chunks = []
    for r in results:
        source_info = r.metadata_json.get("source_name", "Unknown Source")
        context_chunks.append(f"[Source: {source_info}]\n{r.chunk_text}")

    context = "\n---\n".join(context_chunks)
    logger.info("kb_retrieval_completed", agent_id=agent_id, matches=len(results))
    return context
