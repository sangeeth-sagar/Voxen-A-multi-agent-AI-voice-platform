import structlog
import json
from sqlalchemy.orm import Session
from app.models.agent_config import AgentConfig
from app.models.agent_key_assignment import AgentApiKeyAssignment
from app.models.user_api_key import UserApiKey
from app.models.plan import ConversationSession
from app.utils.encryption import decrypt_key
from app.llm_router import chat_with_tools
from app.services.rag_engine import query_similar_context

logger = structlog.get_logger(__name__)

async def run_chat_core(
    db: Session,
    agent_id: int,
    text: str,
    session_id: str,
    language: str = "en"
) -> dict:
    """
    Unified text chatbot execution engine. Coordinates conversation history,
    pgvector RAG context, and LLM orchestration with custom tool-calling.
    """
    logger.info("chat_core_started", agent_id=agent_id, session_id=session_id)

    # 1. Fetch agent configuration
    agent = db.query(AgentConfig).filter(AgentConfig.id == agent_id).first()
    if not agent:
        raise Exception("Agent configuration not found")
    if not agent.is_active:
        raise Exception("Agent is not active")

    # 2. Resolve credentials
    key_assignment = db.query(AgentApiKeyAssignment).filter(AgentApiKeyAssignment.agent_id == agent.id).first()
    if not key_assignment or not key_assignment.llm_api_key_id:
        raise Exception("Agent has no LLM API key assigned")

    llm_key_row = db.query(UserApiKey).filter(UserApiKey.id == key_assignment.llm_api_key_id).first()
    if not llm_key_row:
        raise Exception("LLM API key record not found")
    llm_key = decrypt_key(llm_key_row.api_key)

    # 3. Retrieve pgvector context
    kb_context = ""
    sources = []
    if agent.kb_enabled:
        # Query pgvector for matches
        kb_context = await query_similar_context(db, agent.id, text, similarity_threshold=0.35)
        # Extract sources list
        if kb_context:
            from app.models.agent_knowledge_base import VectorEmbedding
            # Find vector matches again to yield precise sources lists for citation cards
            from app.services.rag import get_embedding_function, resolve_user_gemini_key
            api_key = resolve_user_gemini_key(db, agent.user_id)
            model = get_embedding_function(api_key)
            query_vector = model([text])[0]
            distance_expr = VectorEmbedding.embedding.cosine_distance(query_vector)
            
            results = (
                db.query(VectorEmbedding)
                .filter(VectorEmbedding.agent_id == agent.id, distance_expr <= 0.65)
                .order_by(distance_expr)
                .limit(4)
                .all()
            )
            for r in results:
                src_name = r.metadata_json.get("source_name", "Unknown Source")
                if src_name not in sources:
                    sources.append(src_name)

    # 4. Load history
    history = []
    if session_id:
        session_obj = db.query(ConversationSession).filter(ConversationSession.session_id == session_id).first()
        if session_obj and session_obj.messages:
            for msg in session_obj.messages[-10:]:
                role = "human" if msg.get("role") == "user" else "assistant"
                history.append((role, msg.get("content", "")))

    # Formulate base system prompt
    original_system_prompt = agent.system_prompt
    kb_header = ""
    if kb_context:
        kb_header = f"\n\n[KNOWLEDGE BASE CONTEXT]\n{kb_context}"
    
    agent.system_prompt = (original_system_prompt or "") + kb_header

    # 5. Run LLM turn
    import time
    call_start = time.time()
    response_text = await chat_with_tools(
        text=text,
        agent_config=agent,
        api_key=llm_key,
        llm_provider=key_assignment.llm_provider or "gemini",
        language=language,
        history=history,
        db=db,
        user_id=agent.user_id,
        session_id=session_id
    )
    total_ms = (time.time() - call_start) * 1000

    # Restore system prompt
    agent.system_prompt = original_system_prompt

    # Increment use count and log metrics to api_calls table
    agent.use_count = (agent.use_count or 0) + 1
    from app.models.api_call import ApiCall
    api_call = ApiCall(
        agent_id=agent.id,
        session_id=session_id,
        user_text=text,
        agent_response=response_text,
        total_latency_ms=round(total_ms, 1),
        characters_count=len(response_text),
        language=language,
        webhook_status=200
    )
    db.add(api_call)
    db.commit()

    # 6. Persist conversation turn
    if session_id:
        session_obj = db.query(ConversationSession).filter(ConversationSession.session_id == session_id).first()
        if not session_obj:
            session_obj = ConversationSession(
                session_id=session_id,
                user_id=agent.user_id,
                agent_id=agent.id,
                messages=[]
            )
            db.add(session_obj)
            db.commit()
            db.refresh(session_obj)

        from datetime import datetime
        new_msgs = list(session_obj.messages or []) + [
            {"role": "user", "content": text, "timestamp": datetime.utcnow().isoformat()},
            {"role": "assistant", "content": response_text, "timestamp": datetime.utcnow().isoformat()}
        ]
        session_obj.messages = new_msgs
        session_obj.updated_at = datetime.utcnow()
        db.commit()

        # Trigger async summarizer if conversation turns exceed 10
        if len(new_msgs) >= 10:
            import asyncio
            from app.services.memory import summarize_session
            asyncio.create_task(summarize_session(agent.id, agent.user_id, session_id))

    logger.info("chat_core_completed", agent_id=agent_id, session_id=session_id)
    return {
        "response": response_text,
        "session_id": session_id,
        "sources": sources,
        "agent_name": agent.name,
    }
