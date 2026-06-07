"""
Voice Agent API endpoint.
Flow:
  Browser SpeechRecognition → text
  → POST /api/v1/voice/chat (this endpoint)
  → User's own Gemini/OpenAI/Claude key (from user_api_keys)
  → text response
  → Browser speechSynthesis speaks it
"""
import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.llm_router import chat as llm_chat, normalize_language
from app.models.agent_config import AgentConfig
from app.models.agent_key_assignment import AgentApiKeyAssignment
from app.models.user_api_key import UserApiKey
from app.models.user import User
from app.utils.encryption import decrypt_key

router = APIRouter()
logger = structlog.get_logger(__name__)

DEFAULT_VOICE_PROMPT = """You are a helpful, friendly, and concise AI voice assistant.
You answer questions clearly and briefly since your responses will be spoken aloud.
Keep responses under 3 sentences unless more detail is explicitly requested.
Be conversational and natural. Never use markdown, bullet points, or special
characters in your responses — only plain spoken language."""


class VoiceChatRequest(BaseModel):
    text: str                          # transcribed speech from browser STT
    agent_uuid: Optional[str] = None   # if None, use user's default voice agent
    language: str = "en"               # 2-letter code: en, hi, mr, ml


class VoiceChatResponse(BaseModel):
    response_text: str     # text for browser TTS to speak
    agent_name: str
    language: str          # 2-letter code (en/hi/mr/ml) — echoes input


def _load_user_llm_key(db: Session, agent: AgentConfig) -> tuple[str, str]:
    """Load the user-attached LLM key for an agent.

    Returns (decrypted_api_key, provider). Raises 400 if no key is
    attached — the caller surfaces a clear message to the frontend.
    """
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

    return decrypt_key(llm_key_row.api_key), (assignment.llm_provider or "gemini")


@router.post("/chat", response_model=VoiceChatResponse)
async def voice_chat(
    body: VoiceChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Process a voice message and return text response for TTS.
    If agent_uuid is provided, use that agent's system prompt.
    Otherwise use the user's default voice agent.

    The LLM is forced to reply in `body.language` (en, hi, mr, ml).
    Uses the user's own API key attached to the agent.
    """
    if not body.text or not body.text.strip():
        raise HTTPException(status_code=400, detail="Empty voice input")

    language = normalize_language(body.language)

    # Get agent config
    agent = None
    if body.agent_uuid:
        agent = db.query(AgentConfig).filter(
            AgentConfig.uuid == body.agent_uuid,
            AgentConfig.user_id == current_user.id,
        ).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
    else:
        # Use default voice agent
        agent = db.query(AgentConfig).filter(
            AgentConfig.user_id == current_user.id,
            AgentConfig.is_voice_agent == True,
        ).order_by(AgentConfig.created_at.asc()).first()

    system_prompt = DEFAULT_VOICE_PROMPT
    agent_name = "Default Voice Assistant"

    if agent:
        system_prompt = agent.voice_system_prompt or DEFAULT_VOICE_PROMPT
        agent_name = agent.name

        # If agent has knowledge base, append it to system prompt
        if agent.knowledge_base_text:
            system_prompt += f"""

You also have access to the following knowledge base.
Use it to answer relevant questions:

--- KNOWLEDGE BASE ---
{agent.knowledge_base_text[:8000]}
--- END KNOWLEDGE BASE ---"""

    # Load the user's API key for this agent
    if agent is None:
        raise HTTPException(
            status_code=400,
            detail="No voice agent found. Create one and attach an API key first.",
        )
    llm_key, llm_provider = _load_user_llm_key(db, agent)

    try:
        response_text = await llm_chat(
            text=body.text.strip(),
            base_system_prompt=system_prompt,
            agent_name=agent_name,
            language=language,
            api_key=llm_key,
            llm_provider=llm_provider,
        )

        logger.info(
            "voice_chat_success",
            user=current_user.username,
            agent=agent_name,
            language=language,
            provider=llm_provider,
            input_len=len(body.text),
            output_len=len(response_text),
        )
        return VoiceChatResponse(
            response_text=response_text,
            agent_name=agent_name,
            language=language,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("voice_chat_error", error=str(e), language=language)
        raise HTTPException(
            status_code=500,
            detail="Voice agent failed to respond. Please try again."
        )