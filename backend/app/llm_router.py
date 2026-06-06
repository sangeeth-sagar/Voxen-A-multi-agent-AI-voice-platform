from typing import List, Dict, Any, Optional
import structlog
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import get_settings

logger = structlog.get_logger()

SUPPORTED_LANGUAGES = ("en", "hi", "mr", "ml")
DEFAULT_LANGUAGE = "en"

LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
    "ml": "Malayalam",
}

LANGUAGE_INSTRUCTION = {
    "en": "Always respond in English only.",
    "hi": "\u0939\u092e\u0947\u0936\u093e \u0915\u0947\u0935\u0932 \u0939\u093f\u0928\u094d\u0926\u0940 \u092e\u0947\u0902 \u091c\u0935\u093e\u092c \u0926\u0947\u0902\u0964",
    "mr": "\u0928\u0947\u0939\u092e\u0940 \u092b\u0915\u094d\u0924 \u092e\u0930\u093e\u0920\u0940\u0924 \u0909\u0924\u094d\u0924\u0930 \u0926\u094d\u092f\u093e.",
    "ml": "\u0d0e\u0d2a\u0d4d\u0d2a\u0d4b\u0d34\u0d41\u0d02 \u0d2e\u0d32\u0d2f\u0d3e\u0d33\u0d24\u0d4d\u0d24\u0d3f\u0d7d \u0d2e\u0d3e\u0d24\u0d4d\u0d30\u0d02 \u0d2e\u0d31\u0d41\u0d2a\u0d1f\u0d3f \u0d28\u0d7d\u0d15\u0d41\u0d15.",
}


def normalize_language(language: Optional[str]) -> str:
    """Coerce arbitrary input to a supported 2-letter code, defaulting to English."""
    if not language:
        return DEFAULT_LANGUAGE
    code = language.strip().lower().split("-")[0].split("_")[0]
    return code if code in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def build_system_prompt(base_prompt: str, language: str = DEFAULT_LANGUAGE) -> str:
    """
    Append a strong language-forcing directive to a base system prompt.
    """
    lang = normalize_language(language)
    lang_instruction = LANGUAGE_INSTRUCTION.get(lang, LANGUAGE_INSTRUCTION[DEFAULT_LANGUAGE])
    lang_name = LANGUAGE_NAMES.get(lang, "English")
    return (
        f"{base_prompt}\n\n"
        f"IMPORTANT: {lang_instruction}\n"
        f"You must ONLY respond in {lang_name}. "
        f"Do not mix languages. Do not respond in any other language even if "
        f"the user writes in another language."
    )


def get_llm(task: str = "default") -> ChatGoogleGenerativeAI:
    """
    Return a Gemini chat model instance for the given task.
    """
    settings = get_settings()
    if not settings.google_api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY is not configured. Set it in your .env file."
        )
    return ChatGoogleGenerativeAI(
        model=settings.model_name,
        google_api_key=settings.google_api_key,
    )


async def chat(text: str,
               session_messages: Optional[List[Dict[str, Any]]] = None,
               base_system_prompt: Optional[str] = None,
               kb_context: str = "",
               agent_name: str = "Assistant",
               language: str = DEFAULT_LANGUAGE) -> str:
    """
    Run a single LLM turn with language forcing.

    - `language` accepts any of: en, hi, mr, ml (others fall back to en).
    - `base_system_prompt` is the agent's prompt; the language directive
      is appended on top so the model always replies in the selected language.
    - Session history is trimmed to the last 10 messages.
    - Returns cleaned text (no markdown/special chars) suitable for TTS.
    """
    settings = get_settings()
    if not settings.google_api_key:
        raise RuntimeError("GOOGLE_API_KEY is not configured.")

    lang = normalize_language(language)
    base = base_system_prompt or "You are a helpful voice assistant."
    system_prompt = build_system_prompt(base, lang)

    if kb_context:
        system_prompt += f"\n\nKNOWLEDGE BASE:\n{kb_context}\n"
    system_prompt += (
        f"\nYou are {agent_name}. Keep responses under 3 sentences for voice output. "
        f"Never use markdown, bullet points, or special characters. "
        f"Speak naturally and conversationally."
    )

    llm = ChatGoogleGenerativeAI(
        model=settings.model_name,
        google_api_key=settings.google_api_key,
        temperature=0.7,
        max_output_tokens=200,
    )

    messages: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]
    if session_messages:
        last_messages = session_messages[-10:] if len(session_messages) > 10 else session_messages
        for msg in last_messages:
            messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": text})

    result = await llm.ainvoke(messages)
    response_text = result.content
    cleaned = response_text.replace("*", "").replace("#", "").replace("`", "").replace("-", "")
    cleaned = " ".join(cleaned.split())

    logger.info("llm_chat_completed",
                language=lang,
                agent=agent_name,
                input_len=len(text),
                output_len=len(cleaned))
    return cleaned
