import structlog
from typing import Optional

from app.database import SessionLocal
from app.llm_router import get_llm
from app.models.agent_config import AgentConfig
from app.models.agent_key_assignment import AgentApiKeyAssignment
from app.models.agent_memory import AgentMemory
from app.models.api_call import ApiCall
from app.models.user_api_key import UserApiKey
from app.utils.encryption import decrypt_key

logger = structlog.get_logger()


async def summarize_session(
    agent_id: int,
    user_id: int,
    session_id: Optional[str],
) -> None:
    """Summarize a completed conversation session and upsert into agent_memories.

    Designed to run as a background task — never raises into the caller.
    Creates its own DB session to avoid use-after-close from the caller's session.
    """
    db = SessionLocal()
    try:
        agent = db.query(AgentConfig).filter(AgentConfig.id == agent_id).first()
        if not agent:
            return
        if hasattr(agent, "memory_enabled") and not agent.memory_enabled:
            return

        calls = (
            db.query(ApiCall)
            .filter(
                ApiCall.agent_id == agent_id,
                ApiCall.session_id == session_id,
                ApiCall.webhook_status == 200,
            )
            .order_by(ApiCall.created_at.asc())
            .all()
        )
        lines = []
        if len(calls) >= 4:
            for c in calls:
                if c.user_text:
                    lines.append(f"User: {c.user_text}")
                if c.agent_response:
                    lines.append(f"Agent: {c.agent_response}")
        else:
            # Fall back to text chat ConversationSession history
            from app.models.plan import ConversationSession
            chat_session = (
                db.query(ConversationSession)
                .filter(ConversationSession.session_id == session_id)
                .first()
            )
            if chat_session and chat_session.messages:
                for t in chat_session.messages:
                    role_name = "User" if t.get("role") == "user" else "Agent"
                    lines.append(f"{role_name}: {t.get('content', '')}")

        conversation_text = "\n".join(lines)
        if not conversation_text.strip():
            return

        assignment = (
            db.query(AgentApiKeyAssignment)
            .filter(AgentApiKeyAssignment.agent_id == agent_id)
            .first()
        )
        if not assignment or not assignment.llm_api_key_id:
            logger.info("memory_summarization_skipped", reason="no_llm_key", agent_id=agent_id)
            return

        llm_key_row = (
            db.query(UserApiKey)
            .filter(UserApiKey.id == assignment.llm_api_key_id)
            .first()
        )
        if not llm_key_row:
            return

        llm_key = decrypt_key(llm_key_row.api_key)
        llm = get_llm(assignment.llm_provider or "gemini", llm_key)

        existing = (
            db.query(AgentMemory)
            .filter(
                AgentMemory.agent_id == agent_id,
                AgentMemory.user_id == user_id,
            )
            .first()
        )
        prev_summary = existing.summary if existing else "No previous memory."

        prompt = (
            "Summarize the key facts, preferences, and unresolved items from this "
            "conversation in 2-3 sentences, for use as background context in a future "
            "conversation with the same user. Do not include pleasantries or restate "
            "the obvious.\n\n"
            f"Previous Memory: {prev_summary}\n\n"
            f"New Conversation:\n{conversation_text}\n\n"
            "New consolidated summary:"
        )

        response = await llm.ainvoke([("human", prompt)])
        summary_text = response.content
        if isinstance(summary_text, list):
            summary_text = "".join(
                p.get("text", "") if isinstance(p, dict) else (str(p) if p else "")
                for p in summary_text
            )
        summary_text = summary_text.strip()
        if not summary_text:
            return

        if existing:
            existing.summary = summary_text
            existing.session_id = session_id
        else:
            db.add(
                AgentMemory(
                    agent_id=agent_id,
                    user_id=user_id,
                    session_id=session_id,
                    summary=summary_text,
                )
            )
        db.commit()
        logger.info("session_memory_summarized", agent_id=agent_id, user_id=user_id)

    except Exception as e:
        logger.warning("memory_summarization_failed", error=str(e), agent_id=agent_id)
    finally:
        db.close()
