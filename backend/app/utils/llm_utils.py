from typing import Any


def extract_text_from_content(content: Any) -> str:
    """Safely extract plain text from LangChain LLM response content.

    Handles:
        - str (older Gemini models, OpenAI, Claude)
        - list of dicts (Gemini 3.1 streaming: [{"type": "text", "text": "..."}])
        - list of strings
        - None
        - any other type (fallback to str())
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict):
                parts.append(part.get("text", ""))
            elif isinstance(part, str):
                parts.append(part)
            else:
                parts.append(str(part) if part else "")
        return "".join(parts)
    if content is None:
        return ""
    return str(content)
