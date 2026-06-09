"""
Voice processing orchestration endpoint.

POST /api/v1/voice/process
  - Accepts audio file upload
  - Runs STT (Groq Whisper)
  - Calls developer's webhook
  - Runs TTS (Edge TTS)
  - Returns audio + transcript + response

Also logs every call to the api_calls table for metrics.
"""
import time
import structlog
import httpx
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Response, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.agent_config import AgentConfig
from app.services.stt import transcribe_audio
from app.services.tts import synthesize_speech
from app.services.metrics import STT_COST_PER_MINUTE, TTS_COST_PER_CHARACTER
from app.models.api_call import ApiCall

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/voice", tags=["voice-orchestration"])


@router.post("/process")
async def process_voice(
    audio: UploadFile = File(...),
    agent_id: str = Form(...),
    session_id: Optional[str] = Form(None),
    language: str = Form("en"),
    db: Session = Depends(get_db),
):
    """
    Full voice pipeline: audio in → STT → webhook → TTS → audio out.

    The `agent_id` is the agent UUID. The webhook URL is read from the
    agent's `webhook_url` field. If no webhook is configured the LLM
    processes the text directly using the agent's attached API key.
    """
    call_start = time.time()
    stt_ms = webhook_ms = tts_ms = 0.0
    webhook_status = None
    webhook_error = None
    user_text = ""
    response_text = ""

    # 1. Look up agent
    agent = db.query(AgentConfig).filter(AgentConfig.uuid == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # 2. Read audio bytes
    audio_bytes = await audio.read()
    audio_duration = len(audio_bytes) / 16000.0  # rough estimate

    # 3. STT
    stt_start = time.time()
    try:
        user_text = await transcribe_audio(
            audio_bytes=audio_bytes,
            filename=audio.filename or "audio.webm",
            language=language,
        )
        if not user_text or not user_text.strip():
            raise HTTPException(status_code=400, detail="Could not transcribe audio")
        user_text = user_text.strip()
    except HTTPException:
        raise
    except Exception as e:
        logger.error("orchestration_stt_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"STT failed: {e}")
    stt_ms = (time.time() - stt_start) * 1000

    # 4. Call developer webhook or use built-in LLM
    webhook_start = time.time()
    if agent.webhook_url:
        # External webhook
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    agent.webhook_url,
                    json={
                        "text": user_text,
                        "session_id": session_id,
                        "language": language,
                        "agent_id": agent_id,
                    },
                )
                webhook_status = resp.status_code
                if resp.status_code == 200:
                    data = resp.json()
                    response_text = data.get("response", data.get("agent_response", ""))
                else:
                    webhook_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
        except httpx.TimeoutException:
            webhook_status = 0
            webhook_error = "Webhook timeout (>30s)"
        except Exception as e:
            webhook_status = 0
            webhook_error = str(e)[:200]
    else:
        # Built-in LLM processing
        from app.llm_router import chat as llm_chat, normalize_language
        from app.models.agent_key_assignment import AgentApiKeyAssignment
        from app.models.user_api_key import UserApiKey
        from app.utils.encryption import decrypt_key

        assignment = (
            db.query(AgentApiKeyAssignment)
            .filter(AgentApiKeyAssignment.agent_id == agent.id)
            .first()
        )
        if assignment and assignment.llm_api_key_id:
            llm_key_row = (
                db.query(UserApiKey)
                .filter(UserApiKey.id == assignment.llm_api_key_id)
                .first()
            )
            if llm_key_row:
                llm_key = decrypt_key(llm_key_row.api_key)
                try:
                    response_text = await llm_chat(
                        text=user_text,
                        base_system_prompt=agent.voice_system_prompt or agent.system_prompt,
                        agent_name=agent.name,
                        language=language,
                        api_key=llm_key,
                        llm_provider=assignment.llm_provider or "gemini",
                    )
                    webhook_status = 200
                except Exception as e:
                    webhook_status = 500
                    webhook_error = str(e)[:200]
            else:
                webhook_status = 400
                webhook_error = "LLM API key not found"
        else:
            webhook_status = 400
            webhook_error = "No LLM API key attached to agent"

    webhook_ms = (time.time() - webhook_start) * 1000

    if not response_text:
        raise HTTPException(
            status_code=500,
            detail=f"Agent did not produce a response: {webhook_error or 'unknown error'}",
        )

    # 5. TTS
    tts_start = time.time()
    try:
        audio_response = await synthesize_speech(response_text, language=language)
    except Exception as e:
        logger.error("orchestration_tts_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"TTS failed: {e}")
    tts_ms = (time.time() - tts_start) * 1000

    total_ms = (time.time() - call_start) * 1000

    # 6. Log to api_calls table
    api_call = ApiCall(
        agent_id=agent.id,
        session_id=session_id,
        user_text=user_text,
        agent_response=response_text,
        stt_latency_ms=round(stt_ms, 1),
        webhook_latency_ms=round(webhook_ms, 1),
        tts_latency_ms=round(tts_ms, 1),
        total_latency_ms=round(total_ms, 1),
        webhook_status=webhook_status,
        webhook_error_message=webhook_error,
        audio_duration_seconds=round(audio_duration, 2),
        characters_count=len(response_text),
        language=language,
    )
    db.add(api_call)
    db.commit()

    logger.info(
        "voice_process_completed",
        agent_id=agent_id,
        stt_ms=round(stt_ms, 1),
        webhook_ms=round(webhook_ms, 1),
        tts_ms=round(tts_ms, 1),
        total_ms=round(total_ms, 1),
    )

    return Response(
        content=audio_response,
        media_type="audio/mpeg",
        headers={
            "X-Session-Id": session_id or "",
            "X-Transcribed-Text": user_text,
            "X-Response-Text": response_text,
            "X-Language": language,
            "X-Total-Latency-Ms": str(round(total_ms, 1)),
        },
    )
