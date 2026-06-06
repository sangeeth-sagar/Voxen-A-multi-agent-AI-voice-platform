import structlog
from fastapi import HTTPException
from groq import Groq
from app.config import get_settings

logger = structlog.get_logger()

SUPPORTED_LANGUAGES = {
    "en": "en",
    "hi": "hi",
    "mr": "mr",
    "ml": "ml",
}

DEFAULT_LANGUAGE = "en"

GROQ_WHISPER_MODEL = "whisper-large-v3"


async def transcribe_audio(audio_bytes: bytes,
                           filename: str = "audio.webm",
                           language: str = DEFAULT_LANGUAGE) -> str:
    """
    Transcribe audio using Groq Whisper API.

    Supports: English (en), Hindi (hi), Marathi (mr), Malayalam (ml).
    Model: whisper-large-v3 (full multilingual model; the -turbo variant
    has limited Marathi/Malayalam support).
    """
    settings = get_settings()
    if not settings.groq_api_key:
        logger.error("groq_api_key not configured")
        raise HTTPException(status_code=500, detail="Groq API key not configured")

    lang_code = SUPPORTED_LANGUAGES.get(language, SUPPORTED_LANGUAGES[DEFAULT_LANGUAGE])
    if language not in SUPPORTED_LANGUAGES:
        logger.warning("stt_unsupported_language",
                       requested=language, fallback=lang_code)

    try:
        client = Groq(api_key=settings.groq_api_key)
        transcription = client.audio.transcriptions.create(
            file=(filename, audio_bytes, "audio/webm"),
            model=GROQ_WHISPER_MODEL,
            language=lang_code,
            response_format="text"
        )
        logger.info("transcription_completed",
                    length=len(transcription),
                    language=lang_code)
        return transcription
    except Exception as e:
        logger.error("transcription_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
