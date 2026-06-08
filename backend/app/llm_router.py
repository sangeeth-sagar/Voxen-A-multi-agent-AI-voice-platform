"""
Provider-agnostic LLM router.

Primary API (new architecture):
    get_llm(provider, api_key) -> chat model
    build_system_prompt(agent_config, language) -> str
    chat_with_provider(text, agent_config, api_key, llm_provider, language, history) -> str

Backwards-compatible API (per-user API key required):
    chat(text, session_messages, base_system_prompt, kb_context,
         agent_name, language, api_key, llm_provider) -> str
    normalize_language(language) -> str
    build_system_prompt(base_prompt, language) -> str

Note: every chat() / chat_with_provider() call requires an explicit
`api_key`. The server no longer falls back to `settings.google_api_key`
— users add their own keys via Profile → API Keys.
"""
from typing import Any, Dict, List, Optional
import structlog

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_groq import ChatGroq
from groq import Groq

from app.config import settings
from app.utils.llm_utils import extract_text_from_content


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
    "hi": "\u0939\u092e\u0947\u0936\u093e \u0915\u0947\u0935\u093b \u0939\u093f\u0928\u094d\u0926\u0940 \u092e\u0947\u0902 \u091c\u0935\u093e\u092c \u0926\u0947\u0902\u0964",
    "mr": "\u0928\u0947\u0939\u092e\u0940 \u092b\u0915\u094d\u0924 \u092e\u0930\u093e\u0920\u0940\u0924 \u0909\u0924\u094d\u0924\u0930 \u0926\u094d\u092f\u093e.",
    "ml": "\u0d0e\u0d2a\u0d4d\u0d2a\u0d4b\u0d34\u0d41\u0d02 \u0d2e\u0d32\u0d2f\u0d3e\u0d33\u0d24\u0d4d\u0d24\u0d3f\u0d7d \u0d2e\u0d3e\u0d24\u0d4d\u0d30\u0d02 \u0d2e\u0d31\u0d41\u0d2a\u0d1f\u0d3f \u0d28\u0d7d\u0d15\u0d41\u0d15.",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def normalize_language(language: Optional[str]) -> str:
    """Coerce arbitrary input to a supported 2-letter code, defaulting to English."""
    if not language:
        return DEFAULT_LANGUAGE
    code = language.strip().lower().split("-")[0].split("_")[0]
    return code if code in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


# ---------------------------------------------------------------------------
# Provider factory
# ---------------------------------------------------------------------------
def get_llm(provider: str, api_key: str):
    """Return a LangChain chat model for the given provider + API key."""
    if not api_key:
        raise RuntimeError(
            f"No API key supplied for provider '{provider}'."
        )
    if provider == "gemini":
        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=api_key,
            max_retries=2,
            timeout=15,
        )
    if provider == "openai":
        return ChatOpenAI(
            model=settings.openai_model,
            openai_api_key=api_key,
            max_retries=2,
            timeout=15,
        )
    if provider == "claude":
        return ChatAnthropic(
            model=settings.claude_model,
            anthropic_api_key=api_key,
            max_retries=2,
            timeout=10,
        )
    if provider == "groq":
        return ChatGroq(
            model="llama-3.1-8b-instant",   # fast and free tier available
            groq_api_key=api_key,
            max_retries=2,
            timeout=15,
        )
    raise ValueError(f"Unsupported LLM provider: {provider}")


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------
def _build_system_prompt_from_base(base_prompt: str, language: str) -> str:
    """Internal: build a system prompt from a raw string + language."""
    lang = normalize_language(language)
    lang_instruction = LANGUAGE_INSTRUCTION.get(lang, LANGUAGE_INSTRUCTION[DEFAULT_LANGUAGE])
    lang_name = LANGUAGE_NAMES.get(lang, "English")
    return (
        f"{base_prompt}\n\n"
        f"IMPORTANT: {lang_instruction}\n"
        f"You MUST only respond in {lang_name}. "
        f"Do not mix languages under any circumstances."
    )


def build_system_prompt(first_arg, language: str = DEFAULT_LANGUAGE) -> str:
    """Polymorphic system-prompt builder.

    - New (agent_config, language): takes an AgentConfig-like object.
    - Legacy (base_prompt: str, language): takes a raw prompt string.
    """
    if isinstance(first_arg, str):
        return _build_system_prompt_from_base(first_arg, language)
    base = (
        getattr(first_arg, "system_prompt", None)
        or getattr(first_arg, "voice_system_prompt", None)
        or "You are a helpful voice assistant."
    )
    return _build_system_prompt_from_base(base, language)


# ---------------------------------------------------------------------------
# New chat entry point (per-user API key)
# ---------------------------------------------------------------------------
async def chat_with_provider(
    text: str,
    agent_config,
    api_key: str,
    llm_provider: str = "gemini",
    language: str = "en",
    history: Optional[List[Any]] = None,
) -> str:
    """Run a single LLM turn using a per-user API key.

    `agent_config` is an AgentConfig (or any object exposing
    `system_prompt` / `voice_system_prompt`).
    `history` is a list of (role, content) tuples or dicts.
    """
    llm = get_llm(llm_provider, api_key)
    system_prompt = build_system_prompt(agent_config, language)
    messages: List[Any] = [("system", system_prompt)]
    for item in history or []:
        messages.append(item)
    messages.append(("human", text))
    response = await llm.ainvoke(messages)
    raw = response.content
    if isinstance(raw, list):
        return "".join(
            p.get("text", "") if isinstance(p, dict) else (str(p) if p else "")
            for p in raw
        )
    return raw if isinstance(raw, str) else (str(raw) if raw else "")


# ---------------------------------------------------------------------------
# Backwards-compatible chat — requires per-user API key
# ---------------------------------------------------------------------------
async def chat(
    text: str,
    session_messages: Optional[List[Dict[str, Any]]] = None,
    base_system_prompt: Optional[str] = None,
    kb_context: str = "",
    agent_name: str = "Assistant",
    language: str = DEFAULT_LANGUAGE,
    api_key: str = "",
    llm_provider: str = "gemini",
) -> str:
    """Single-turn LLM call using a per-user API key.

    `api_key` and `llm_provider` are now REQUIRED in practice — the
    server no longer reads `settings.google_api_key`. Callers must load
    the encrypted key from `user_api_keys` and decrypt it before calling.
    """
    if not api_key:
        raise RuntimeError(
            "No API key provided. Please add your API key in Profile → API Keys "
            "and attach it to this agent."
        )

    lang = normalize_language(language)
    base = base_system_prompt or "You are a helpful voice assistant."
    system_prompt = _build_system_prompt_from_base(base, lang)

    if kb_context:
        system_prompt += f"\n\nKNOWLEDGE BASE:\n{kb_context}\n"
    system_prompt += (
        f"\nYou are {agent_name}. Keep responses under 3 sentences for voice output. "
        f"Never use markdown, bullet points, or special characters. "
        f"Speak naturally and conversationally."
    )

    llm = get_llm(llm_provider, api_key)

    messages: List[Any] = [("system", system_prompt)]
    if session_messages:
        last = session_messages[-10:] if len(session_messages) > 10 else session_messages
        for msg in last:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            lc_role = "human" if role == "user" else "assistant"
            messages.append((lc_role, content))
    messages.append(("human", text))

    result = await llm.ainvoke(messages)
    raw = result.content
    if isinstance(raw, list):
        response_text = "".join(
            p.get("text", "") if isinstance(p, dict) else (str(p) if p else "")
            for p in raw
        )
    elif isinstance(raw, str):
        response_text = raw
    else:
        response_text = str(raw) if raw else ""

    cleaned = (
        response_text.replace("*", "")
        .replace("#", "")
        .replace("`", "")
        .replace("-", "")
    )
    cleaned = " ".join(cleaned.split())

    logger.info(
        "llm_chat_completed",
        language=lang,
        agent=agent_name,
        provider=llm_provider,
        input_len=len(text),
        output_len=len(cleaned),
    )
    return cleaned
