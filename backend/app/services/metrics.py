"""
Metrics service — calculates volume, performance, financial, and reliability
metrics from the api_calls, voice_sessions, and usage_metrics tables.
"""
from datetime import date, datetime, timedelta
from typing import Optional
import structlog
from sqlalchemy import func, case, text
from sqlalchemy.orm import Session

from app.models.api_call import ApiCall
from app.models.voice_session import VoiceSession
from app.models.usage_metric import UsageMetric
from app.models.agent_config import AgentConfig

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Pricing constants (per million units)
# ---------------------------------------------------------------------------
STT_COST_PER_MINUTE = 0.003   # Groq Whisper ~$0.003/min
TTS_COST_PER_CHARACTER = 0.002  # ElevenLabs ~$0.002/char (avg)


def _date_range(time_range: str):
    """Return (start_date, end_date) for a given range string."""
    today = date.today()
    if time_range == "7d":
        start = today - timedelta(days=7)
    elif time_range == "90d":
        start = today - timedelta(days=90)
    else:
        start = today - timedelta(days=30)
    return start, today


# =========================================================================
# Volume metrics
# =========================================================================
def get_volume_metrics(db: Session, agent_id: int, time_range: str = "30d"):
    start, end = _date_range(time_range)

    base = db.query(ApiCall).filter(
        ApiCall.agent_id == agent_id,
        func.date(ApiCall.created_at) >= start,
        func.date(ApiCall.created_at) <= end,
    )

    total_requests = base.count()
    active_sessions = (
        db.query(func.count(func.distinct(ApiCall.session_id)))
        .filter(
            ApiCall.agent_id == agent_id,
            func.date(ApiCall.created_at) >= start,
            func.date(ApiCall.created_at) <= end,
        )
        .scalar()
    )

    # Requests per day (last 30 days)
    daily_rows = (
        db.query(
            func.date(ApiCall.created_at).label("day"),
            func.count(ApiCall.id).label("count"),
        )
        .filter(
            ApiCall.agent_id == agent_id,
            func.date(ApiCall.created_at) >= start,
        )
        .group_by(func.date(ApiCall.created_at))
        .order_by(func.date(ApiCall.created_at))
        .all()
    )
    requests_per_day = [{"date": str(r.day), "count": r.count} for r in daily_rows]

    # Requests by hour (last 24h)
    yesterday = date.today() - timedelta(days=1)
    hourly_rows = (
        db.query(
            func.extract("hour", ApiCall.created_at).label("hour"),
            func.count(ApiCall.id).label("count"),
        )
        .filter(
            ApiCall.agent_id == agent_id,
            func.date(ApiCall.created_at) >= yesterday,
        )
        .group_by(func.extract("hour", ApiCall.created_at))
        .order_by(func.extract("hour", ApiCall.created_at))
        .all()
    )
    requests_by_hour = [{"hour": int(r.hour), "count": r.count} for r in hourly_rows]

    return {
        "total_requests": total_requests,
        "active_sessions": active_sessions or 0,
        "requests_per_day": requests_per_day,
        "requests_by_hour": requests_by_hour,
        "time_range": time_range,
    }


# =========================================================================
# Performance metrics
# =========================================================================
def get_performance_metrics(db: Session, agent_id: int, time_range: str = "30d"):
    start, end = _date_range(time_range)

    stats = (
        db.query(
            func.avg(ApiCall.stt_latency_ms).label("avg_stt"),
            func.avg(ApiCall.webhook_latency_ms).label("avg_webhook"),
            func.avg(ApiCall.tts_latency_ms).label("avg_tts"),
            func.avg(ApiCall.total_latency_ms).label("avg_total"),
        )
        .filter(
            ApiCall.agent_id == agent_id,
            func.date(ApiCall.created_at) >= start,
            func.date(ApiCall.created_at) <= end,
        )
        .first()
    )

    avg_stt = round(stats.avg_stt or 0, 1)
    avg_webhook = round(stats.avg_webhook or 0, 1)
    avg_tts = round(stats.avg_tts or 0, 1)
    avg_total = round(stats.avg_total or 0, 1)

    # Percentiles via raw SQL
    percentile_sql = text("""
        SELECT
            PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY total_latency_ms) as p50,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY total_latency_ms) as p75,
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total_latency_ms) as p95,
            PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY total_latency_ms) as p99
        FROM api_calls
        WHERE agent_id = :agent_id
          AND DATE(created_at) >= :start
          AND DATE(created_at) <= :end
          AND total_latency_ms IS NOT NULL
    """)
    result = db.execute(
        percentile_sql,
        {"agent_id": agent_id, "start": start, "end": end},
    ).first()

    percentiles = {
        "p50": round(result.p50 or 0, 1),
        "p75": round(result.p75 or 0, 1),
        "p95": round(result.p95 or 0, 1),
        "p99": round(result.p99 or 0, 1),
    }

    # Latency trend (daily)
    trend_rows = (
        db.query(
            func.date(ApiCall.created_at).label("day"),
            func.avg(ApiCall.stt_latency_ms).label("stt"),
            func.avg(ApiCall.webhook_latency_ms).label("webhook"),
            func.avg(ApiCall.tts_latency_ms).label("tts"),
            func.avg(ApiCall.total_latency_ms).label("total"),
        )
        .filter(
            ApiCall.agent_id == agent_id,
            func.date(ApiCall.created_at) >= start,
            ApiCall.total_latency_ms.isnot(None),
        )
        .group_by(func.date(ApiCall.created_at))
        .order_by(func.date(ApiCall.created_at))
        .all()
    )
    latency_trend = [
        {
            "date": str(r.day),
            "stt_ms": round(r.stt or 0, 1),
            "webhook_ms": round(r.webhook or 0, 1),
            "tts_ms": round(r.tts or 0, 1),
            "total_ms": round(r.total or 0, 1),
        }
        for r in trend_rows
    ]

    # Determine slowest component
    components = {"stt": avg_stt, "webhook": avg_webhook, "tts": avg_tts}
    slowest = max(components, key=components.get) if any(components.values()) else "webhook"

    return {
        "avg_stt_latency_ms": avg_stt,
        "avg_webhook_latency_ms": avg_webhook,
        "avg_tts_latency_ms": avg_tts,
        "avg_total_latency_ms": avg_total,
        "latency_percentiles": percentiles,
        "latency_trend": latency_trend,
        "slowest_component": slowest,
        "time_range": time_range,
    }


# =========================================================================
# Financial metrics
# =========================================================================
def get_financial_metrics(db: Session, agent_id: int, time_range: str = "30d"):
    start, end = _date_range(time_range)

    stats = (
        db.query(
            func.sum(ApiCall.audio_duration_seconds).label("total_audio_sec"),
            func.sum(ApiCall.characters_count).label("total_chars"),
            func.count(ApiCall.id).label("total_calls"),
        )
        .filter(
            ApiCall.agent_id == agent_id,
            func.date(ApiCall.created_at) >= start,
            func.date(ApiCall.created_at) <= end,
        )
        .first()
    )

    total_audio_min = (stats.total_audio_sec or 0) / 60.0
    total_chars = stats.total_chars or 0

    stt_cost = round(total_audio_min * STT_COST_PER_MINUTE, 4)
    tts_cost = round(total_chars * TTS_COST_PER_CHARACTER, 4)
    total_cost = round(stt_cost + tts_cost, 4)

    # Today's cost
    today = date.today()
    today_stats = (
        db.query(
            func.sum(ApiCall.audio_duration_seconds).label("audio_sec"),
            func.sum(ApiCall.characters_count).label("chars"),
        )
        .filter(
            ApiCall.agent_id == agent_id,
            func.date(ApiCall.created_at) == today,
        )
        .first()
    )
    today_audio_min = (today_stats.audio_sec or 0) / 60.0
    today_chars = today_stats.chars or 0
    cost_today = round(
        today_audio_min * STT_COST_PER_MINUTE + today_chars * TTS_COST_PER_CHARACTER, 4
    )

    # Monthly projection (extrapolate from current month's data)
    days_in_range = max((end - start).days, 1)
    days_in_month = 30
    monthly_projection = round(total_cost * (days_in_month / days_in_range), 2)

    # Cost breakdown by service
    costs_by_service = {
        "stt": {
            "provider": "Groq Whisper",
            "duration_minutes": round(total_audio_min, 2),
            "cost": stt_cost,
            "per_minute": STT_COST_PER_MINUTE,
        },
        "tts": {
            "provider": "Edge TTS",
            "characters": total_chars,
            "cost": tts_cost,
            "per_character": TTS_COST_PER_CHARACTER,
        },
    }

    return {
        "estimated_cost_today": cost_today,
        "estimated_cost_period": total_cost,
        "estimated_cost_monthly": monthly_projection,
        "costs_by_service": costs_by_service,
        "time_range": time_range,
    }


# =========================================================================
# Reliability metrics
# =========================================================================
def get_reliability_metrics(db: Session, agent_id: int, time_range: str = "30d"):
    start, end = _date_range(time_range)

    total = (
        db.query(func.count(ApiCall.id))
        .filter(
            ApiCall.agent_id == agent_id,
            func.date(ApiCall.created_at) >= start,
            func.date(ApiCall.created_at) <= end,
        )
        .scalar()
    )

    success_count = (
        db.query(func.count(ApiCall.id))
        .filter(
            ApiCall.agent_id == agent_id,
            ApiCall.webhook_status == 200,
            func.date(ApiCall.created_at) >= start,
            func.date(ApiCall.created_at) <= end,
        )
        .scalar()
    )

    success_rate = round((success_count / total * 100) if total > 0 else 100.0, 1)

    # Error breakdown
    error_rows = (
        db.query(
            ApiCall.webhook_status,
            func.count(ApiCall.id).label("count"),
        )
        .filter(
            ApiCall.agent_id == agent_id,
            func.date(ApiCall.created_at) >= start,
            func.date(ApiCall.created_at) <= end,
            ApiCall.webhook_status.isnot(None),
            ApiCall.webhook_status != 200,
        )
        .group_by(ApiCall.webhook_status)
        .all()
    )

    errors_by_code = {str(r.webhook_status): r.count for r in error_rows}

    # Timeout count (webhook_latency > 30000ms)
    timeout_count = (
        db.query(func.count(ApiCall.id))
        .filter(
            ApiCall.agent_id == agent_id,
            ApiCall.webhook_latency_ms > 30000,
            func.date(ApiCall.created_at) >= start,
            func.date(ApiCall.created_at) <= end,
        )
        .scalar()
    )

    total_errors = total - success_count

    # Reliability trend (daily)
    trend_rows = (
        db.query(
            func.date(ApiCall.created_at).label("day"),
            func.count(ApiCall.id).label("total"),
            func.count(case((ApiCall.webhook_status == 200, 1))).label("success"),
        )
        .filter(
            ApiCall.agent_id == agent_id,
            func.date(ApiCall.created_at) >= start,
        )
        .group_by(func.date(ApiCall.created_at))
        .order_by(func.date(ApiCall.created_at))
        .all()
    )
    reliability_trend = [
        {
            "date": str(r.day),
            "success_rate": round(r.success / r.total * 100, 1) if r.total > 0 else 100,
            "error_count": r.total - r.success,
        }
        for r in trend_rows
    ]

    return {
        "webhook_success_rate": success_rate,
        "total_requests": total,
        "total_errors": total_errors,
        "errors_by_code": errors_by_code,
        "timeout_count": timeout_count,
        "reliability_trend": reliability_trend,
        "time_range": time_range,
    }


# =========================================================================
# Aggregate platform-wide metrics
# =========================================================================
def get_platform_metrics(db: Session, time_range: str = "30d"):
    start, end = _date_range(time_range)

    total_calls = (
        db.query(func.count(ApiCall.id))
        .filter(
            func.date(ApiCall.created_at) >= start,
            func.date(ApiCall.created_at) <= end,
        )
        .scalar()
    )

    active_agents = (
        db.query(AgentConfig)
        .filter(AgentConfig.is_active == True)
        .count()
    )

    # Top agents by usage
    top_agents = (
        db.query(
            AgentConfig.id,
            AgentConfig.name,
            func.count(ApiCall.id).label("call_count"),
        )
        .join(ApiCall, ApiCall.agent_id == AgentConfig.id)
        .filter(
            func.date(ApiCall.created_at) >= start,
            func.date(ApiCall.created_at) <= end,
        )
        .group_by(AgentConfig.id, AgentConfig.name)
        .order_by(func.count(ApiCall.id).desc())
        .limit(10)
        .all()
    )

    top_agents_list = [
        {"agent_id": r.id, "agent_name": r.name, "call_count": r.call_count}
        for r in top_agents
    ]

    # Daily volume trend
    daily_rows = (
        db.query(
            func.date(ApiCall.created_at).label("day"),
            func.count(ApiCall.id).label("count"),
        )
        .filter(
            func.date(ApiCall.created_at) >= start,
        )
        .group_by(func.date(ApiCall.created_at))
        .order_by(func.date(ApiCall.created_at))
        .all()
    )
    daily_trend = [{"date": str(r.day), "count": r.count} for r in daily_rows]

    total_cost = 0.0

    return {
        "total_calls": total_calls,
        "active_agents": active_agents or 0,
        "top_agents": top_agents_list,
        "daily_trend": daily_trend,
        "total_cost": total_cost,
        "time_range": time_range,
    }
