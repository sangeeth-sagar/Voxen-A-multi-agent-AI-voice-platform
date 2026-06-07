"""
Multi-provider TTS router.

Supported providers:
    - elevenlabs   (REST streaming, multilingual voices)
    - groq         (playai-tts sync client wrapped in asyncio.to_thread)
    - browser      (returns empty bytes; client does speechSynthesis itself)
"""
import asyncio
import httpx
from groq import Groq


ELEVENLABS_VOICE_MAP = {
    "en": "21m00Tcm4TlvDq8ikWAM",   # Rachel — English
    "hi": "pNInz6obpgDQGcFmaJgB",   # Adam — multilingual
    "mr": "pNInz6obpgDQGcFmaJgB",
    "ml": "pNInz6obpgDQGcFmaJgB",
}


async def synthesize(
    text: str,
    provider: str,
    api_key: str,
    language: str = "en",
) -> bytes:
    """Synthesize `text` to audio bytes using the chosen provider."""
    if provider == "elevenlabs":
        return await _elevenlabs_tts(text, api_key, language)
    if provider == "groq":
        return await _groq_tts(text, api_key, language)
    if provider == "browser":
        # Frontend uses browser speechSynthesis; return empty.
        return b""
    if provider == "azure_tts":
        # Placeholder — Azure TTS not wired up; raise so the caller knows.
        raise ValueError("azure_tts provider is not yet implemented")
    raise ValueError(f"Unsupported TTS provider: {provider}")


async def _elevenlabs_tts(text: str, api_key: str, language: str) -> bytes:
    voice_id = ELEVENLABS_VOICE_MAP.get(language, ELEVENLABS_VOICE_MAP["en"])
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream",
            headers={
                "xi-api-key": api_key,
                "Content-Type": "application/json",
            },
            json={
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                },
            },
        )
        response.raise_for_status()
        return response.content


async def _groq_tts(text: str, api_key: str, language: str) -> bytes:
    def _sync() -> bytes:
        client = Groq(api_key=api_key)
        response = client.audio.speech.create(
            model="playai-tts",
            voice="Celeste-PlayAI",
            input=text,
            response_format="mp3",
        )
        return response.read()

    return await asyncio.to_thread(_sync)
