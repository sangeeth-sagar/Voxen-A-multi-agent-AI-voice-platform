-- =========================================================================
-- Voice Agent Metrics — PostgreSQL Schema
-- Run this after the existing alembic migrations.
-- =========================================================================

-- API call log — one row per voice interaction
CREATE TABLE IF NOT EXISTS api_calls (
    id              TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    agent_id        INTEGER NOT NULL REFERENCES agent_configs(id) ON DELETE CASCADE,
    session_id      TEXT,
    user_text       TEXT,
    agent_response  TEXT,
    stt_latency_ms      DOUBLE PRECISION,
    webhook_latency_ms  DOUBLE PRECISION,
    tts_latency_ms      DOUBLE PRECISION,
    total_latency_ms    DOUBLE PRECISION,
    webhook_status      INTEGER,
    webhook_error_message TEXT,
    audio_duration_seconds DOUBLE PRECISION,
    characters_count    INTEGER,
    language        TEXT DEFAULT 'en',
    created_at      TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_api_calls_agent_id   ON api_calls(agent_id);
CREATE INDEX IF NOT EXISTS idx_api_calls_session_id  ON api_calls(session_id);
CREATE INDEX IF NOT EXISTS idx_api_calls_created_at  ON api_calls(created_at);

-- Voice sessions
CREATE TABLE IF NOT EXISTS voice_sessions (
    id              TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    agent_id        INTEGER NOT NULL REFERENCES agent_configs(id) ON DELETE CASCADE,
    started_at      TIMESTAMP DEFAULT now(),
    ended_at        TIMESTAMP,
    total_calls     INTEGER DEFAULT 0,
    total_duration_seconds DOUBLE PRECISION DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_voice_sessions_agent_id ON voice_sessions(agent_id);

-- Daily usage metrics (aggregated)
CREATE TABLE IF NOT EXISTS usage_metrics (
    id              SERIAL PRIMARY KEY,
    agent_id        INTEGER NOT NULL REFERENCES agent_configs(id) ON DELETE CASCADE,
    date            DATE NOT NULL,
    total_requests          INTEGER DEFAULT 0,
    successful_requests     INTEGER DEFAULT 0,
    failed_requests         INTEGER DEFAULT 0,
    total_latency_sum       DOUBLE PRECISION DEFAULT 0,
    total_stt_latency_sum   DOUBLE PRECISION DEFAULT 0,
    total_webhook_latency_sum DOUBLE PRECISION DEFAULT 0,
    total_tts_latency_sum   DOUBLE PRECISION DEFAULT 0,
    peak_concurrent_sessions INTEGER DEFAULT 0,
    estimated_cost          DOUBLE PRECISION DEFAULT 0,
    audio_duration_minutes  DOUBLE PRECISION DEFAULT 0,
    characters_count        INTEGER DEFAULT 0,
    UNIQUE(agent_id, date)
);

CREATE INDEX IF NOT EXISTS idx_usage_metrics_agent_date ON usage_metrics(agent_id, date);
