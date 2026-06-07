from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
import structlog

from app.services.tts import synthesize_speech
from app.services.session_store import (
    create_session, add_message,
    get_session_messages, get_session, get_user_sessions
)
from app.services.rag import retrieve_context
from app.services.llm_agent import run_agent_turn
from app.models.agent_config import AgentConfig
from app.models.user import User
from app.database import get_db
from app.auth.dependencies import get_current_user

logger = structlog.get_logger()
router = APIRouter()


class VoiceAgentChatRequest(BaseModel):
    text: str
    agent_uuid: str
    session_id: Optional[str] = None
    language: str = "en"


# Endpoint 1: POST /api/v1/voice-agent/chat
@router.post("/chat")
async def voice_agent_chat(
    body: VoiceAgentChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Handle in-app voice agent conversation (used by the Test Window in the frontend).
    This endpoint is JWT authenticated.
    """
    text = body.text
    agent_uuid = body.agent_uuid
    session_id = body.session_id
    language = body.language
    # 1. Find agent by uuid, verify ownership or public access
    agent = db.query(AgentConfig).filter(AgentConfig.uuid == agent_uuid).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    # Check access: own, public, or template
    if not (
        agent.user_id == current_user.id
        or agent.is_public == True
        or agent.is_template == True
    ):
        raise HTTPException(status_code=403, detail="Access denied")

    # 2. Get or create session in DB
    session = None
    if session_id:
        session = await get_session(db, session_id)
    if not session:
        session = await create_session(db, user_id=current_user.id, agent_id=agent.id)

    # 3. Get last 10 session messages
    session_messages = await get_session_messages(db, session.session_id)
    
    # 4. Get RAG context if kb_enabled
    kb_context = ""
    if agent.kb_enabled and agent.kb_collection_name:
        kb_context = await retrieve_context(
            agent.kb_collection_name, text
        )
    
    # 5. Call run_agent_turn (resolves the per-user API key inside)
    try:
        response_text = await run_agent_turn(
            db=db,
            agent=agent,
            user_text=text,
            system_prompt=agent.voice_system_prompt or agent.system_prompt,
            session_messages=session_messages,
            kb_context=kb_context,
            agent_name=agent.wake_word,
            language=language,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("llm_agent_failed", agent_uuid=agent_uuid, error=str(e))
        raise HTTPException(status_code=500, detail=f"Agent processing failed: {str(e)}")
    
    # 6. Save user + assistant messages to session
    await add_message(db, session.session_id, "user", text)
    await add_message(db, session.session_id, "assistant", response_text)
    
    # 7. Return response
    # Get the wake confirm and welcome messages for the frontend
    wake_confirm = agent.wake_confirm_message.replace("{agent_name}", agent.wake_word)
    welcome_message = agent.welcome_message
    
    return {
        "response_text": response_text,
        "session_id": session.session_id,
        "agent_name": agent.name,
        "wake_confirm": wake_confirm,
        "welcome_message": welcome_message
    }

# Endpoint 2: GET /api/v1/voice-agent/wake-confirm/{agent_uuid}
@router.get("/wake-confirm/{agent_uuid}")
async def get_wake_confirm(
    agent_uuid: str,
    language: str = "en",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns the wake confirmation audio as bytes.
    """
    agent = db.query(AgentConfig).filter(AgentConfig.uuid == agent_uuid).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    # Check access: own, public, or template
    if not (
        agent.user_id == current_user.id
        or agent.is_public == True
        or agent.is_template == True
    ):
        raise HTTPException(status_code=403, detail="Access denied")

    # Build wake text
    wake_text = agent.wake_confirm_message.replace(
        "{agent_name}", agent.wake_word
    )

    # Synthesize with edge-tts
    try:
        audio = await synthesize_speech(wake_text, language=language)
    except Exception as e:
        logger.error("tts_failed", agent_uuid=agent_uuid, error=str(e))
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {str(e)}")

    return Response(content=audio, media_type="audio/mpeg")

# Endpoint 3: GET /api/v1/voice-agent/welcome/{agent_uuid}
@router.get("/welcome/{agent_uuid}")
async def get_welcome(
    agent_uuid: str,
    language: str = "en",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns the welcome message audio as bytes.
    """
    agent = db.query(AgentConfig).filter(AgentConfig.uuid == agent_uuid).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    # Check access: own, public, or template
    if not (
        agent.user_id == current_user.id
        or agent.is_public == True
        or agent.is_template == True
    ):
        raise HTTPException(status_code=403, detail="Access denied")

    # Synthesize welcome message
    try:
        audio = await synthesize_speech(agent.welcome_message, language=language)
    except Exception as e:
        logger.error("tts_failed", agent_uuid=agent_uuid, error=str(e))
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {str(e)}")

    return Response(content=audio, media_type="audio/mpeg")

# Endpoint 4: GET /api/v1/voice-agent/sessions
@router.get("/sessions")
async def get_voice_agent_sessions(
    agent_uuid: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns all sessions for current user across all agents.
    Query param: agent_uuid (optional filter)
    """
    agent_id = None
    if agent_uuid:
        agent = db.query(AgentConfig).filter(AgentConfig.uuid == agent_uuid).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        # Check access: own, public, or template
        if not (
            agent.user_id == current_user.id
            or agent.is_public == True
            or agent.is_template == True
        ):
            raise HTTPException(status_code=403, detail="Access denied")
        agent_id = agent.id
    
    # Get sessions
    sessions = await get_user_sessions(db, current_user.id, agent_id)
    return sessions