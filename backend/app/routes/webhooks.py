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
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.security import hash_password  # noqa: F401  (kept for parity with admin)
from app.models.user import User
from app.models.agent_config import AgentConfig
from app.models.agent_key_assignment import AgentApiKeyAssignment
from app.models.user_api_key import UserApiKey
from app.models.webhook_endpoint import WebhookEndpoint
from app.utils.encryption import decrypt_key
from app.llm_router import chat_with_provider

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
@router.post("/agent/{webhook_token}")
async def handle_webhook(
    webhook_token: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Receive a text message from an external suite, run the agent, and
    return (or POST back) the response."""
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
    language = payload.get("language", "en")
    session_id = payload.get("session_id")

    if not text:
        raise HTTPException(status_code=400, detail="'text' field is required")

    agent = (
        db.query(AgentConfig)
        .filter(AgentConfig.id == endpoint.agent_id)
        .first()
    )
    key_assignment = (
        db.query(AgentApiKeyAssignment)
        .filter(AgentApiKeyAssignment.agent_id == agent.id)
        .first()
    )
    if not key_assignment or not key_assignment.llm_api_key_id:
        raise HTTPException(
            status_code=500,
            detail="Agent has no LLM API key configured",
        )

    llm_key_row = (
        db.query(UserApiKey)
        .filter(UserApiKey.id == key_assignment.llm_api_key_id)
        .first()
    )
    if not llm_key_row:
        raise HTTPException(status_code=500, detail="LLM API key not found")
    llm_key = decrypt_key(llm_key_row.api_key)

    response_text = await chat_with_provider(
        text=text,
        agent_config=agent,
        api_key=llm_key,
        llm_provider=key_assignment.llm_provider or "gemini",
        language=language,
    )

    result = {
        "agent_response": response_text,
        "agent_name": agent.name,
        "session_id": session_id,
        "language": language,
    }

    # Optional async callback
    if endpoint.webhook_url:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(endpoint.webhook_url, json=result)
        except Exception:
            # Don't fail the caller's request if the callback fails
            pass

    return result


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
