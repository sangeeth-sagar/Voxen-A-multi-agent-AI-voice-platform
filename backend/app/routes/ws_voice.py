"""
Real-time voice WebSocket.

Client connects to `/ws/voice/{agent_uuid}` and sends JSON messages:
    {"type": "user_text", "text": "...", "language": "en"}
    {"type": "ping"}
    {"type": "interrupt"}

The server streams back:
    {"type": "ready", "agent": "..."}
    {"type": "user_transcript", "text": "..."}
    {"type": "agent_thinking"}
    {"type": "agent_token", "token": "..."}  # streamed
    {"type": "agent_response_complete", "text": "..."}
    {"type": "tts_start"}
    {"type": "tts_chunk", "audio": "<base64>", "index": int, "is_last": bool, "format": "mp3"}
    {"type": "tts_end"}
    {"type": "tts_browser", "text": "...", "language": "en"}  # if TTS=client
    {"type": "interrupted"}
    {"type": "pong"}
    {"type": "error", "message": "..."}
"""
import asyncio
import base64
import logging
import sys
import traceback
import time
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.agent_config import AgentConfig
from app.models.agent_key_assignment import AgentApiKeyAssignment
from app.models.user_api_key import UserApiKey
from app.utils.encryption import decrypt_key
from app.llm_router import get_llm, build_system_prompt
from app.tts_router import synthesize
from app.services.rag import retrieve_context
from app.utils.llm_utils import extract_text_from_content
from app.models.api_call import ApiCall

logger = logging.getLogger(__name__)

router = APIRouter()

# Audio is sent to the browser in 16KB base64 chunks. Sending the entire
# MP3 as one message can blow up Chrome's heap on long responses.
TTS_CHUNK_SIZE = 16 * 1024

# Cap the text we send to TTS. ~500 chars ≈ 30s of speech. Anything longer
# produces multi-MB MP3s that crash the tab and add latency for no gain.
MAX_TTS_CHARS = 500


@router.websocket("/ws/voice/{agent_uuid}")
async def voice_websocket(
    websocket: WebSocket,
    agent_uuid: str,
    db: Session = Depends(get_db),
):
    await websocket.accept()

    try:
        # ---- Load agent + keys -------------------------------------
        agent = (
            db.query(AgentConfig).filter(AgentConfig.uuid == agent_uuid).first()
        )
        if not agent:
            await websocket.send_json({"type": "error", "message": "Agent not found"})
            await websocket.close(code=4004)
            return

        assignment = (
            db.query(AgentApiKeyAssignment)
            .filter(AgentApiKeyAssignment.agent_id == agent.id)
            .first()
        )
        if not assignment or not assignment.llm_api_key_id:
            await websocket.send_json({
                "type": "error",
                "message": (
                    "No API key attached. Edit the agent and attach your Gemini key."
                ),
            })
            await websocket.close(code=4005)
            return

        llm_key_row = (
            db.query(UserApiKey)
            .filter(UserApiKey.id == assignment.llm_api_key_id)
            .first()
        )
        if not llm_key_row:
            await websocket.send_json({
                "type": "error",
                "message": "API key record not found. Please re-attach the key to this agent.",
            })
            await websocket.close(code=4006)
            return

        llm_key = decrypt_key(llm_key_row.api_key)

        tts_key = None
        if assignment.tts_api_key_id:
            tts_key_row = (
                db.query(UserApiKey)
                .filter(UserApiKey.id == assignment.tts_api_key_id)
                .first()
            )
            if tts_key_row:
                tts_key = decrypt_key(tts_key_row.api_key)

        session_id = f"ws_{uuid.uuid4().hex[:12]}"
        conversation_history: list = []
        await websocket.send_json({"type": "ready", "agent": agent.name})

        # ---- Main loop ---------------------------------------------
        while True:
            try:
                data = await websocket.receive_json()
            except WebSocketDisconnect:
                break
            except Exception:
                break

            msg_type = data.get("type")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            if msg_type == "interrupt":
                await websocket.send_json({"type": "interrupted"})
                continue

            if msg_type != "user_text":
                await websocket.send_json(
                    {"type": "error", "message": f"Unknown message type: {msg_type}"}
                )
                continue

            text = (data.get("text") or "").strip()
            language = data.get("language", "en")
            if not text:
                continue

            turn_start = time.time()

            await websocket.send_json({"type": "user_transcript", "text": text})
            await websocket.send_json({"type": "agent_thinking"})

            try:
                llm_start = time.time()
                full_response = ""
                llm = get_llm(assignment.llm_provider or "gemini", llm_key)
                system_prompt = build_system_prompt(agent, language)

                # Inject KB context into system_prompt if the agent has a
                # knowledge base collection attached.
                kb_context = ""
                if agent.kb_collection_name:
                    try:
                        kb_context = await retrieve_context(agent.kb_collection_name, text)
                    except Exception as kb_err:
                        logger.warning(f"KB retrieval failed: {kb_err}")

                if kb_context:
                    system_prompt += f"\n\nKNOWLEDGE BASE CONTEXT:\n{kb_context}\n"

                messages = (
                    [("system", system_prompt)]
                    + list(conversation_history)
                    + [("human", text)]
                )

                async for chunk in llm.astream(messages):
                    # chunk.content can be str or list[dict] in Gemini 3.1
                    raw = chunk.content
                    if isinstance(raw, list):
                        token = "".join(
                            p.get("text", "") if isinstance(p, dict) else (str(p) if p else "")
                            for p in raw
                        )
                    elif isinstance(raw, str):
                        token = raw
                    else:
                        token = str(raw) if raw else ""

                    if token:
                        full_response += token
                        await websocket.send_json(
                            {"type": "agent_token", "token": token}
                        )

                llm_ms = (time.time() - llm_start) * 1000

                await websocket.send_json({
                    "type": "agent_response_complete",
                    "text": full_response[:1000] if len(full_response) > 1000 else full_response,
                })

                # ---- TTS -------------------------------------------
                # Check provider first — browser TTS sends only text and
                # lets the frontend use SpeechSynthesis (zero memory cost
                # compared to streaming a multi-MB MP3 through base64).
                tts_provider = assignment.tts_provider or "browser"
                tts_start = time.time()

                if tts_provider == "browser" or not tts_key:
                    # Let frontend handle TTS using browser SpeechSynthesis
                    # Cap at 500 chars to match API TTS limit and prevent Chrome crash
                    await websocket.send_json({
                        "type": "tts_browser",
                        "text": full_response[:MAX_TTS_CHARS] if len(full_response) > MAX_TTS_CHARS else full_response,
                        "language": language,
                    })
                else:
                    # Use API TTS — stream in chunks to avoid Chrome memory crash
                    await websocket.send_json({"type": "tts_start"})
                    try:
                        audio_bytes = await synthesize(
                            full_response[:MAX_TTS_CHARS],
                            tts_provider,
                            tts_key,
                            language,
                        )
                        audio_size_kb = len(audio_bytes) / 1024 if audio_bytes else 0
                        logger.info(f"TTS audio generated: {audio_size_kb:.1f} KB for {len(full_response)} chars")

                        if audio_size_kb > 500:
                            logger.warning(f"TTS audio too large: {audio_size_kb:.1f} KB — this will crash Chrome")
                            # Force browser TTS for oversized audio
                            await websocket.send_json({
                                "type": "tts_browser",
                                "text": full_response[:MAX_TTS_CHARS] if len(full_response) > MAX_TTS_CHARS else full_response,
                                "language": language,
                            })
                        elif audio_bytes:
                            total = len(audio_bytes)
                            offset = 0
                            index = 0
                            while offset < total:
                                chunk = audio_bytes[offset:offset + TTS_CHUNK_SIZE]
                                await websocket.send_json({
                                    "type": "tts_chunk",
                                    "audio": base64.b64encode(chunk).decode(),
                                    "index": index,
                                    "is_last": (offset + TTS_CHUNK_SIZE >= total),
                                    "format": "mp3",
                                })
                                offset += TTS_CHUNK_SIZE
                                index += 1
                                await asyncio.sleep(0)  # yield to event loop
                    except Exception as tts_err:
                        traceback.print_exc()
                        logger.error(f"TTS error: {tts_err}")
                        # Fallback to browser TTS on any error
                        await websocket.send_json({
                            "type": "tts_browser",
                            "text": full_response[:MAX_TTS_CHARS] if len(full_response) > MAX_TTS_CHARS else full_response,
                            "language": language,
                        })
                    await websocket.send_json({"type": "tts_end"})

                tts_ms = (time.time() - tts_start) * 1000
                total_ms = (time.time() - turn_start) * 1000

                # Log API call to database
                try:
                    api_call = ApiCall(
                        agent_id=agent.id,
                        session_id=session_id,
                        user_text=text,
                        agent_response=full_response,
                        stt_latency_ms=0.0,
                        webhook_latency_ms=round(llm_ms, 1),
                        tts_latency_ms=round(tts_ms, 1),
                        total_latency_ms=round(total_ms, 1),
                        webhook_status=200,
                        characters_count=len(full_response),
                        language=language,
                    )
                    db.add(api_call)
                    db.commit()
                except Exception as db_err:
                    logger.error(f"Failed to log ApiCall: {db_err}")

                conversation_history.extend([
                    ("human", text),
                    ("assistant", full_response),
                ])
                if len(conversation_history) > 20:
                    conversation_history = conversation_history[-20:]

            except Exception as llm_err:
                traceback.print_exc()
                error_msg = str(llm_err)
                logger.error(f"LLM error in WebSocket: {error_msg}")
                print(f"WS LLM ERROR: {type(llm_err).__name__}: {error_msg}")
                try:
                    await websocket.send_json({
                        "type": "llm_error",
                        "message": f"LLM error: {error_msg}",
                    })
                except Exception:
                    pass

                # Log failed ApiCall to database
                try:
                    total_ms = (time.time() - turn_start) * 1000
                    api_call = ApiCall(
                        agent_id=agent.id,
                        session_id=session_id,
                        user_text=text,
                        agent_response="",
                        stt_latency_ms=0.0,
                        webhook_latency_ms=0.0,
                        tts_latency_ms=0.0,
                        total_latency_ms=round(total_ms, 1),
                        webhook_status=500,
                        webhook_error_message=error_msg,
                        characters_count=0,
                        language=language,
                    )
                    db.add(api_call)
                    db.commit()
                except Exception as db_err:
                    logger.error(f"Failed to log failed ApiCall: {db_err}")

                # DO NOT close — keep connection alive for next message
                continue

    except WebSocketDisconnect:
        return
    except Exception as exc:
        traceback.print_exc()
        logger.error(f"WebSocket fatal error: {type(exc).__name__}: {exc}")
        print(f"WS CRASH: {type(exc).__name__}: {exc}")
        try:
            await websocket.send_json({"type": "error", "message": str(exc)})
        except Exception:
            pass
