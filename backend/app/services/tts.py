import structlog
import edge_tts
from fastapi import HTTPException
from app.config import get_settings

logger = structlog.get_logger()

SUPPORTED_LANGUAGES = ("en", "hi", "mr", "ml")
DEFAULT_LANGUAGE = "en"

TTS_VOICE_MAP = {
    "en": "en-US-AriaNeural",
    "hi": "hi-IN-SwaraNeural",
    "mr": "mr-IN-AarohiNeural",
    "ml": "ml-IN-SobhanaNeural",
}

LANG_LOCALE_MAP = {
    "en": "en-US",
    "hi": "hi-IN",
    "mr": "mr-IN",
    "ml": "ml-IN",
}


def resolve_voice(language: str = DEFAULT_LANGUAGE) -> str:
    """Map a 2-letter language code to an edge-tts voice name."""
    if language not in SUPPORTED_LANGUAGES:
        logger.warning("tts_unsupported_language",
                       requested=language, fallback=DEFAULT_LANGUAGE)
        return TTS_VOICE_MAP[DEFAULT_LANGUAGE]
    return TTS_VOICE_MAP[language]


async def synthesize_speech(text: str,
                            voice: str = None,
                            speed: float = 1.0,
                            language: str = DEFAULT_LANGUAGE) -> bytes:
    """
    Synthesize speech using Edge-TTS.

    If `voice` is given, it is used as-is (back-compat).
    Otherwise the voice is selected from TTS_VOICE_MAP by `language`.
    """
    if voice is None:
        voice = resolve_voice(language)

    percent = int((speed - 1.0) * 100)
    rate_str = f"{percent:+d}%"

    try:
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate_str
        )
        audio_chunks = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_chunks.append(chunk["data"])
        return b"".join(audio_chunks)
    except Exception as e:
        logger.error("tts_failed", error=str(e), voice=voice, language=language)
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {str(e)}")


async def get_available_voices() -> list:
    """
    Get list of available voices from edge-tts, with Indian voices first.
    """
    try:
        voices = await edge_tts.VoicesManager.create()
        indian_voices = [v for v in voices.voices if "IN" in v["Name"]]
        other_voices = [v for v in voices.voices if "IN" not in v["Name"]]
        indian_voices.sort(key=lambda x: x["Name"])
        other_voices.sort(key=lambda x: x["Name"])
        return indian_voices + other_voices
    except Exception as e:
        logger.error("failed_to_get_voices", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get voices: {str(e)}")
