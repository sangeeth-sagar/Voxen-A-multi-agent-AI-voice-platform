"""
Voice-agent turn orchestrator.

Loads the user's per-agent API key and delegates the actual LLM call
to `app.llm_router.chat`. The key is mandatory — there is no fallback
to `settings.google_api_key`.
"""
import structlog
from typing import List, Dict, Any
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.llm_router import chat as llm_chat
from app.models.agent_config import AgentConfig
from app.models.agent_key_assignment import AgentApiKeyAssignment
from app.models.user_api_key import UserApiKey
from app.utils.encryption import decrypt_key

logger = structlog.get_logger()


def resolve_agent_llm_key(
    db: Session, agent: AgentConfig
) -> tuple[str, str]:
    """Look up the AgentApiKeyAssignment for this agent and return
    (decrypted_api_key, provider). Raises HTTPException(400) with a
    user-friendly message if no key is attached."""
    assignment = (
        db.query(AgentApiKeyAssignment)
        .filter(AgentApiKeyAssignment.agent_id == agent.id)
        .first()
    )
    if not assignment or not assignment.llm_api_key_id:
        raise HTTPException(
            status_code=400,
            detail=(
                "No API key attached to this agent. Go to Agents → Edit Agent "
                "and attach your Gemini/OpenAI/Claude key, or add a key in "
                "Profile → API Keys first."
            ),
        )

    llm_key_row = (
        db.query(UserApiKey)
        .filter(UserApiKey.id == assignment.llm_api_key_id)
        .first()
    )
    if not llm_key_row or not llm_key_row.is_active:
        raise HTTPException(
            status_code=400,
            detail="The API key attached to this agent is missing or inactive.",
        )

    return (
        decrypt_key(llm_key_row.api_key),
        assignment.llm_provider or "gemini",
    )


async def run_agent_turn(
    db: Session,
    user_text: str,
    agent: AgentConfig,
    system_prompt: str,
    session_messages: List[Dict[str, Any]],
    kb_context: str = "",
    agent_name: str = "Nova",
    language: str = "en",
) -> str:
    """Run a single turn of the voice agent LLM logic.

    Loads the user's per-agent API key and forwards to
    `app.llm_router.chat`.

    `language` (en | hi | mr | ml) forces the LLM to reply in that language.
    """
    api_key, llm_provider = resolve_agent_llm_key(db, agent)
    try:
        return await llm_chat(
            text=user_text,
            session_messages=session_messages,
            base_system_prompt=system_prompt,
            kb_context=kb_context,
            agent_name=agent_name,
            language=language,
            api_key=api_key,
            llm_provider=llm_provider,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "agent_turn_failed",
            error=str(e),
            language=language,
            provider=llm_provider,
        )
        raise HTTPException(
            status_code=500, detail=f"Agent turn failed: {str(e)}"
        )
