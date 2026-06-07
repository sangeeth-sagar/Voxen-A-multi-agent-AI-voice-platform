from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Response, Depends
from sqlalchemy.orm import Session
from typing import Optional
import structlog

from app.services.stt import transcribe_audio
from app.services.tts import synthesize_speech
from app.services.rag import retrieve_context
from app.services.session_store import (
    create_session, add_message,
    get_session_messages, get_session
)
from app.services.llm_agent import run_agent_turn
from app.llm_router import normalize_language
from app.models.agent_config import AgentConfig
from app.database import get_db

logger = structlog.get_logger()
router = APIRouter()

@router.post("/{webhook_id}")
async def handle_webhook(
    webhook_id: str,
    audio: UploadFile = File(...),
    language: str = Form("en"),
    session_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    External-facing voice-in → voice-out endpoint.
    No JWT required - webhook_id IS the auth token.

    `language` is a 2-letter code (en, hi, mr, ml) used for STT, LLM forcing,
    and TTS voice selection.
    """
    language = normalize_language(language)

    # 1. Find agent by webhook_id in DB
    agent = db.query(AgentConfig).filter(AgentConfig.webhook_id == webhook_id).first()
    if not agent:
        logger.warning("webhook_not_found", webhook_id=webhook_id)
        raise HTTPException(status_code=404, detail="Webhook not found")
    if not agent.is_active:
        logger.warning("agent_not_active", webhook_id=webhook_id, agent_id=agent.id)
        raise HTTPException(status_code=403, detail="Agent is not active")

    # 2. Read audio bytes from upload
    audio_bytes = await audio.read()

    # 3. Call transcribe_audio
    try:
        transcribed_text = await transcribe_audio(
            audio_bytes=audio_bytes,
            filename=audio.filename or "audio.webm",
            language=language,
        )
        if not transcribed_text or not transcribed_text.strip():
            logger.warning("transcription_empty", webhook_id=webhook_id, language=language)
            raise HTTPException(status_code=400, detail="Could not transcribe audio")
    except Exception as e:
        logger.error("transcription_failed", webhook_id=webhook_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

    # 4. Get or create session
    session = None
    if session_id:
        session = get_session(db, session_id)
    if not session:
        session = create_session(db, agent_id=agent.id)

    # 5. Get last 10 messages
    session_messages = get_session_messages(db, session.session_id)

    # 6. Get RAG context if kb enabled
    kb_context = ""
    if agent.kb_enabled and agent.kb_collection_name:
        kb_context = await retrieve_context(
            agent.kb_collection_name, transcribed_text
        )

    # 7. Run LLM (resolves the agent's per-user API key inside run_agent_turn)
    try:
        response_text = await run_agent_turn(
            db=db,
            agent=agent,
            user_text=transcribed_text,
            system_prompt=agent.voice_system_prompt or agent.system_prompt,
            session_messages=session_messages,
            kb_context=kb_context,
            agent_name=agent.wake_word,
            language=language,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("llm_agent_failed", webhook_id=webhook_id, error=str(e), language=language)
        raise HTTPException(status_code=500, detail=f"Agent processing failed: {str(e)}")

    # 8. Save messages to session
    await add_message(db, session.session_id, "user", transcribed_text)
    await add_message(db, session.session_id, "assistant", response_text)

    # 9. Synthesize response to audio (language-matched voice)
    try:
        audio_response = await synthesize_speech(response_text, language=language)
    except Exception as e:
        logger.error("tts_failed", webhook_id=webhook_id, error=str(e), language=language)
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {str(e)}")

    # 10. Return audio bytes as Response
    response_headers = {
        "X-Session-Id": session.session_id,
        "X-Transcribed-Text": transcribed_text,
        "X-Response-Text": response_text,
        "X-Language": language,
    }

    logger.info("webhook_interaction_completed",
                webhook_id=webhook_id,
                agent_name=agent.name,
                language=language,
                transcribed_text_length=len(transcribed_text),
                response_text_length=len(response_text),
                session_id=session.session_id)

    return Response(
        content=audio_response,
        media_type="audio/mpeg",
        headers=response_headers
    )