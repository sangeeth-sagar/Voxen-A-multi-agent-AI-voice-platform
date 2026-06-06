import structlog
from typing import List, Dict, Any
from fastapi import HTTPException
from app.llm_router import chat as llm_chat

logger = structlog.get_logger()


async def run_agent_turn(
    user_text: str,
    system_prompt: str,
    session_messages: List[Dict[str, Any]],
    kb_context: str = "",
    agent_name: str = "Nova",
    language: str = "en",
) -> str:
    """
    Run a single turn of the voice agent LLM logic.

    `language` (en | hi | mr | ml) forces the LLM to reply in that language.
    All LLM invocation details live in `app.llm_router.chat`.
    """
    try:
        return await llm_chat(
            text=user_text,
            session_messages=session_messages,
            base_system_prompt=system_prompt,
            kb_context=kb_context,
            agent_name=agent_name,
            language=language,
        )
    except Exception as e:
        logger.error("agent_turn_failed", error=str(e), language=language)
        raise HTTPException(status_code=500, detail=f"Agent turn failed: {str(e)}")
