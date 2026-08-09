"""
Token-based webhook endpoints (external suite integration).

External services POST `{ "text": "...", "session_id": "...", "language": "en" }`
to `/api/v1/webhook/agent/{token}`. The handler:
  1. Looks up the WebhookEndpoint by token.
  2. Loads the agent + its assigned LLM API key.
  3. Runs `chat_with_provider` to get a response.
  4. (Optionally) POSTs the response back to the configured `webhook_url`.
"""
import json
import secrets
import httpx
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.security import hash_password  # noqa: F401
from app.models.user import User
from app.models.agent_config import AgentConfig
from app.models.agent_key_assignment import AgentApiKeyAssignment
from app.models.user_api_key import UserApiKey
from app.models.webhook_endpoint import WebhookEndpoint
from app.models.voxen_api_key import VoxenApiKey
from app.utils.encryption import decrypt_key
from app.llm_router import chat_with_provider, chat_with_tools
from app.services.rag_engine import query_similar_context

router = APIRouter(prefix="/api/v1/webhook", tags=["webhook"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class GenerateWebhookRequest(BaseModel):
    callback_url: Optional[str] = None


# ---------------------------------------------------------------------------
# Generate a webhook token for one of the caller's agents
# ---------------------------------------------------------------------------
@router.post("/agent/{agent_id}/generate")
async def generate_webhook(
    agent_id: int,
    body: GenerateWebhookRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a fresh WebhookEndpoint bound to `agent_id` and return the
    public token URL the caller can POST to."""
    agent = (
        db.query(AgentConfig)
        .filter(
            AgentConfig.id == agent_id,
            AgentConfig.user_id == current_user.id,
        )
        .first()
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    token = secrets.token_urlsafe(32)
    endpoint = WebhookEndpoint(
        agent_id=agent_id,
        user_id=current_user.id,
        webhook_secret=token,
        webhook_url=body.callback_url,
    )
    db.add(endpoint)
    db.commit()
    db.refresh(endpoint)

    return {
        "webhook_token": token,
        "webhook_url": f"/api/v1/webhook/agent/{token}",
        "usage": "POST JSON: { text, session_id, language }",
        "callback_url": body.callback_url,
    }


# ---------------------------------------------------------------------------
# External: POST /api/v1/webhook/agent/{token}
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Asynchronous Webhook Task Worker
# ---------------------------------------------------------------------------
async def execute_async_webhook(endpoint_id: int, payload: dict, callback_url: str):
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        endpoint = db.query(WebhookEndpoint).filter(WebhookEndpoint.id == endpoint_id).first()
        if not endpoint:
            return
        agent = db.query(AgentConfig).filter(AgentConfig.id == endpoint.agent_id).first()
        if not agent:
            return
        
        result = await process_agent_logic(db, agent, payload)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.post(callback_url, json=result)
    except Exception as e:
        print(f"Async webhook task error: {e}")
    finally:
        db.close()


async def process_agent_logic(db: Session, agent: AgentConfig, payload: dict) -> dict:
    text = (payload.get("text") or "").strip()
    language = payload.get("language", "en")
    session_id = payload.get("session_id")

    # 1. Resolve Keys
    key_assignment = db.query(AgentApiKeyAssignment).filter(AgentApiKeyAssignment.agent_id == agent.id).first()
    if not key_assignment or not key_assignment.llm_api_key_id:
        raise Exception("Agent has no LLM API key configured")
    
    llm_key_row = db.query(UserApiKey).filter(UserApiKey.id == key_assignment.llm_api_key_id).first()
    if not llm_key_row:
        raise Exception("LLM API key not found")
    llm_key = decrypt_key(llm_key_row.api_key)

    # 2. RAG Context Lookup (if enabled)
    kb_context = ""
    if agent.kb_enabled:
        kb_context = await query_similar_context(db, agent.id, text)

    # Inject JSON Schema requirements into system prompt if requested
    original_system_prompt = agent.system_prompt
    if agent.output_schema:
        schema_instruction = (
            f"\n\nCRITICAL: You MUST respond with a JSON object that matches the following JSON Schema. "
            f"Do NOT include any markdown formatting, backticks (e.g. ```json), or conversational text. "
            f"Output ONLY raw JSON:\n{json.dumps(agent.output_schema)}"
        )
        agent.system_prompt = (original_system_prompt or "") + schema_instruction

    # 3. Load conversation history
    history = []
    if session_id:
        from app.models.plan import ConversationSession
        session_obj = db.query(ConversationSession).filter(ConversationSession.session_id == session_id).first()
        if session_obj and session_obj.messages:
            for msg in session_obj.messages[-10:]:
                role = "human" if msg.get("role") == "user" else "assistant"
                history.append((role, msg.get("content", "")))

    # 4. LLM Execution with dynamic tool calling
    response_text = await chat_with_tools(
        text=text,
        agent_config=agent,
        api_key=llm_key,
        llm_provider=key_assignment.llm_provider or "gemini",
        language=language,
        history=history,
        db=db,
        user_id=agent.user_id,
        session_id=session_id or ""
    )

    # Restore prompt state
    agent.system_prompt = original_system_prompt

    # 5. Parse Output Schema
    agent_response = response_text
    if agent.output_schema:
        try:
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            agent_response = json.loads(cleaned)
        except Exception:
            pass

    # 6. Save conversation turn
    if session_id:
        from app.models.plan import ConversationSession
        session_obj = db.query(ConversationSession).filter(ConversationSession.session_id == session_id).first()
        if not session_obj:
            session_obj = ConversationSession(
                session_id=session_id,
                user_id=agent.user_id,
                agent_id=agent.id,
                messages=[]
            )
            db.add(session_obj)
            db.commit()
            db.refresh(session_obj)

        from datetime import datetime
        new_msgs = list(session_obj.messages or []) + [
            {"role": "user", "content": text, "timestamp": datetime.utcnow().isoformat()},
            {"role": "assistant", "content": str(agent_response) if isinstance(agent_response, (dict, list)) else agent_response, "timestamp": datetime.utcnow().isoformat()}
        ]
        session_obj.messages = new_msgs
        session_obj.updated_at = datetime.utcnow()
        db.commit()

    return {
        "agent_response": agent_response,
        "agent_name": agent.name,
        "session_id": session_id,
        "language": language,
    }


# ---------------------------------------------------------------------------
# External: POST /api/v1/webhook/agent/{token}
# ---------------------------------------------------------------------------
@router.post("/agent/{webhook_token}")
async def handle_webhook(
    webhook_token: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Receive a text message from an external suite, run the agent (sync or async),
    and return the response or POST to callback_url."""
    endpoint = (
        db.query(WebhookEndpoint)
        .filter(
            WebhookEndpoint.webhook_secret == webhook_token,
            WebhookEndpoint.is_active == True,  # noqa: E712
        )
        .first()
    )
    if not endpoint:
        raise HTTPException(status_code=404, detail="Webhook endpoint not found")

    try:
        payload = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    text = (payload.get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="'text' field is required")

    agent = (
        db.query(AgentConfig)
        .filter(AgentConfig.id == endpoint.agent_id)
        .first()
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent configuration not found")
    if not agent.is_active:
        raise HTTPException(status_code=403, detail="Agent is not active")

    # Secure webhook validation using Voxen API Keys (if configured for this agent)
    active_keys_exist = db.query(VoxenApiKey).filter(
        VoxenApiKey.agent_id == agent.id,
        VoxenApiKey.is_active == True
    ).first()

    if active_keys_exist:
        api_key_val = request.headers.get("X-Voxen-API-Key")
        if not api_key_val:
            api_key_val = request.query_params.get("api_key")
        if not api_key_val:
            api_key_val = payload.get("api_key")

        if not api_key_val:
            raise HTTPException(
                status_code=401,
                detail="Missing X-Voxen-API-Key header, query param, or payload parameter for this secured agent"
            )
        
        valid_key = db.query(VoxenApiKey).filter(
            VoxenApiKey.agent_id == agent.id,
            VoxenApiKey.api_key == api_key_val,
            VoxenApiKey.is_active == True
        ).first()

        if not valid_key:
            raise HTTPException(
                status_code=401,
                detail="Invalid or revoked API Key"
            )

    # Determine execution mode (sync vs async)
    mode = payload.get("mode", agent.webhook_mode or "sync").strip().lower()
    callback_url = payload.get("callback_url", endpoint.webhook_url)

    if mode == "async":
        if not callback_url:
            raise HTTPException(
                status_code=400, 
                detail="Async mode requires a callback_url configured on endpoint or provided in request"
            )
        background_tasks.add_task(execute_async_webhook, endpoint.id, payload, callback_url)
        return {"status": "accepted", "message": "Asynchronous process started"}

    # Synchronous processing
    try:
        result = await process_agent_logic(db, agent, payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# List the caller's webhook tokens for one agent
# ---------------------------------------------------------------------------
@router.get("/agent/{agent_id}/list")
async def list_webhooks(
    agent_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    agent = (
        db.query(AgentConfig)
        .filter(
            AgentConfig.id == agent_id,
            AgentConfig.user_id == current_user.id,
        )
        .first()
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    endpoints = (
        db.query(WebhookEndpoint)
        .filter(
            WebhookEndpoint.agent_id == agent_id,
            WebhookEndpoint.user_id == current_user.id,
        )
        .all()
    )
    return [
        {
            "id": e.id,
            "webhook_token": e.webhook_secret,
            "webhook_url": f"/api/v1/webhook/agent/{e.webhook_secret}",
            "callback_url": e.webhook_url,
            "is_active": e.is_active,
            "created_at": e.created_at,
        }
        for e in endpoints
    ]
