import uuid
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.chat_core import run_chat_core

router = APIRouter(prefix="/api/v1/chat", tags=["chatbot"])

class ChatMessageRequest(BaseModel):
    agent_id: int
    session_id: Optional[str] = None
    message_text: str
    language: Optional[str] = "en"

class ChatMessageResponse(BaseModel):
    response: str
    session_id: str
    sources: List[str]
    agent_name: str

@router.post("/message", response_model=ChatMessageResponse)
async def send_chat_message(
    body: ChatMessageRequest,
    db: Session = Depends(get_db)
):
    """
    Exposes unified text chatbot messages endpoint for widgets/external scripts.
    Returns generated responses and document citations.
    """
    session_id = body.session_id
    if not session_id or not session_id.strip():
        session_id = f"chat_{uuid.uuid4().hex[:12]}"

    text = body.message_text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="message_text cannot be empty")

    from app.models.agent_config import AgentConfig
    agent = db.query(AgentConfig).filter(AgentConfig.id == body.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    if not agent.is_active:
        raise HTTPException(status_code=403, detail="Agent is not active")

    try:
        result = await run_chat_core(
            db=db,
            agent_id=body.agent_id,
            text=text,
            session_id=session_id,
            language=body.language
        )
        return ChatMessageResponse(
            response=result["response"],
            session_id=result["session_id"],
            sources=result["sources"],
            agent_name=result["agent_name"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
