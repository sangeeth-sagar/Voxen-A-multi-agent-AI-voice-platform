"""
Metrics & Analytics API routes.

Provides endpoints for:
  - Volume metrics per agent
  - Performance (latency) metrics per agent
  - Financial (cost) metrics per agent
  - Reliability (error) metrics per agent
  - Platform-wide aggregate metrics
  - Raw API call logs with filtering
"""
from typing import Optional
import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.agent_config import AgentConfig
from app.models.api_call import ApiCall
from app.services.metrics import (
    get_volume_metrics,
    get_performance_metrics,
    get_financial_metrics,
    get_reliability_metrics,
    get_platform_metrics,
)

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])
logger = structlog.get_logger()


def _verify_agent_owner(agent_uuid: str, user: User, db: Session):
    """Return agent if user owns it, else raise 403."""
    agent = db.query(AgentConfig).filter(AgentConfig.uuid == agent_uuid).first()
    if not agent:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Agent not found")
    if agent.user_id != user.id:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Access denied")
    return agent


@router.get("/{agent_uuid}/volume")
def volume(
    agent_uuid: str,
    range: str = Query("30d", regex="^(7d|30d|90d)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    agent = _verify_agent_owner(agent_uuid, current_user, db)
    return get_volume_metrics(db, agent.id, range)


@router.get("/{agent_uuid}/performance")
def performance(
    agent_uuid: str,
    range: str = Query("30d", regex="^(7d|30d|90d)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    agent = _verify_agent_owner(agent_uuid, current_user, db)
    return get_performance_metrics(db, agent.id, range)


@router.get("/{agent_uuid}/financial")
def financial(
    agent_uuid: str,
    range: str = Query("30d", regex="^(7d|30d|90d)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return {
        "estimated_cost_today": 0.0,
        "estimated_cost_period": 0.0,
        "estimated_cost_monthly": 0.0,
        "costs_by_service": {},
        "time_range": range,
    }


@router.get("/{agent_uuid}/reliability")
def reliability(
    agent_uuid: str,
    range: str = Query("30d", regex="^(7d|30d|90d)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    agent = _verify_agent_owner(agent_uuid, current_user, db)
    return get_reliability_metrics(db, agent.id, range)


@router.get("/platform")
def platform(
    range: str = Query("30d", regex="^(7d|30d|90d)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_platform_metrics(db, range)


@router.get("/{agent_uuid}/logs")
def logs(
    agent_uuid: str,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    agent = _verify_agent_owner(agent_uuid, current_user, db)
    rows = (
        db.query(ApiCall)
        .filter(ApiCall.agent_id == agent.id)
        .order_by(desc(ApiCall.created_at))
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "session_id": r.session_id,
            "user_text": r.user_text,
            "agent_response": r.agent_response,
            "stt_latency_ms": r.stt_latency_ms,
            "webhook_latency_ms": r.webhook_latency_ms,
            "tts_latency_ms": r.tts_latency_ms,
            "total_latency_ms": r.total_latency_ms,
            "webhook_status": r.webhook_status,
            "webhook_error_message": r.webhook_error_message,
            "language": r.language,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
