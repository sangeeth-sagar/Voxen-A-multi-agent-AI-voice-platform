from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class AgentConfigCreate(BaseModel):
    name: str
    description: Optional[str] = None
    agent_type: str = "business_intel"
    system_prompt: Optional[str] = None
    tools_enabled: List[str] = ["web_search", "memory", "critic"]
    output_format: str = "markdown"
    is_public: bool = False
    # Voice agent fields
    is_voice_agent: bool = False
    voice_language: str = "en-US"
    voice_system_prompt: Optional[str] = None
    knowledge_base_text: Optional[str] = None
    # New fields
    wake_word: str = "Nova"
    kb_enabled: bool = False
    wake_confirm_message: str = "Hey {agent_name}"
    welcome_message: str = "How can I help you today?"
    # API key assignment fields
    llm_provider: Optional[str] = "gemini"
    llm_key_id: Optional[int] = None
    tts_provider: Optional[str] = "browser"
    tts_key_id: Optional[int] = None
    stt_provider: Optional[str] = "groq"
    stt_key_id: Optional[int] = None


class AgentConfigUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    tools_enabled: Optional[List[str]] = None
    output_format: Optional[str] = None
    is_public: Optional[bool] = None
    # Voice agent fields
    is_voice_agent: Optional[bool] = None
    voice_language: Optional[str] = None
    voice_system_prompt: Optional[str] = None
    knowledge_base_text: Optional[str] = None
    # New fields
    wake_word: Optional[str] = None
    kb_enabled: Optional[bool] = None
    wake_confirm_message: Optional[str] = None
    welcome_message: Optional[str] = None
    # API key assignment fields
    llm_provider: Optional[str] = None
    llm_key_id: Optional[int] = None
    tts_provider: Optional[str] = None
    tts_key_id: Optional[int] = None
    stt_provider: Optional[str] = None
    stt_key_id: Optional[int] = None


class AgentConfigResponse(BaseModel):
    uuid: str
    name: str
    description: Optional[str]
    agent_type: str
    system_prompt: Optional[str]
    tools_enabled: List[str]
    output_format: str
    is_public: bool
    is_template: bool
    template_name: Optional[str]
    use_count: int
    created_at: datetime
    owner_username: Optional[str] = None
    # Voice agent fields
    is_voice_agent: bool
    voice_language: str
    voice_system_prompt: Optional[str]
    knowledge_base_text: Optional[str]
    # New fields
    wake_word: str
    is_active: bool
    webhook_id: Optional[str]
    webhook_url: Optional[str]
    kb_enabled: bool
    kb_collection_name: Optional[str]
    wake_confirm_message: str
    welcome_message: str
    # API key assignment fields (joined from agent_api_key_assignments)
    has_key_assignment: bool = False
    llm_provider: Optional[str] = None
    tts_provider: Optional[str] = None
    stt_provider: Optional[str] = None
    llm_key_id: Optional[int] = None
    tts_key_id: Optional[int] = None
    stt_key_id: Optional[int] = None

    model_config = {"from_attributes": True}