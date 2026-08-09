from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.routes import auth, admin, agents, plan, voice, webhook, voice_agent, notifications
from app.routes.api_keys import router as keys_router
from app.routes.ws_voice import router as ws_router
from app.routes.webhooks import router as webhook_router
from app.routes.metrics import router as metrics_router
from app.routes.voice_process import router as voice_process_router
from app.routes.chat import router as chat_router
from app.routes.telegram import router as telegram_router
from app.routes.voxen_api_keys import router as voxen_keys_router
from app.config import settings

# =====================================================================
# THE DATABASE FIX: Tell SQLAlchemy to build the tables in Supabase
# =====================================================================
from app.database import engine, Base
from sqlalchemy import text
# Ensure your models are loaded so SQLAlchemy knows what tables to build
import app.models 

# Auto-migration: Ensure pgvector and organization columns exist
with engine.begin() as conn:
    try:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        print("pgvector extension check/setup completed")
    except Exception as ext_err:
        print(f"Failed to create vector extension: {ext_err}")

    try:
        conn.execute(text("SELECT auth_provider FROM users LIMIT 1"))
    except Exception:
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN auth_provider VARCHAR(20) NOT NULL DEFAULT 'local'"))
            print("Successfully added auth_provider column to users table")
        except Exception as alter_err:
            print(f"Failed to auto-alter users table for auth_provider: {alter_err}")

Base.metadata.create_all(bind=engine)

with engine.begin() as conn:
    try:
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS organization_id INTEGER REFERENCES organizations(id)"))
        print("Successfully ensured organization_id on users")
    except Exception as e:
        print(f"Failed to add organization_id to users: {e}")

    try:
        conn.execute(text("ALTER TABLE agent_configs ADD COLUMN IF NOT EXISTS organization_id INTEGER REFERENCES organizations(id)"))
        print("Successfully ensured organization_id on agent_configs")
    except Exception as e:
        print(f"Failed to add organization_id to agent_configs: {e}")

    try:
        conn.execute(text("ALTER TABLE agent_configs ADD COLUMN IF NOT EXISTS webhook_mode VARCHAR(20) DEFAULT 'sync'"))
        print("Successfully ensured webhook_mode on agent_configs")
    except Exception as e:
        print(f"Failed to add webhook_mode to agent_configs: {e}")

    try:
        conn.execute(text("ALTER TABLE telegram_bot_configs ADD COLUMN IF NOT EXISTS voxen_api_key_id INTEGER REFERENCES voxen_api_keys(id) ON DELETE SET NULL"))
        print("Successfully ensured voxen_api_key_id on telegram_bot_configs")
    except Exception as e:
        print(f"Failed to add voxen_api_key_id to telegram_bot_configs: {e}")

    try:
        conn.execute(text("ALTER TABLE agent_configs ADD COLUMN IF NOT EXISTS output_schema JSONB"))
        print("Successfully ensured output_schema on agent_configs")
    except Exception as e:
        print(f"Failed to add output_schema to agent_configs: {e}")
# =====================================================================

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Voice Agent Backend with Authentication and Admin Panel",
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- THE FIX: Hardcode the Vercel URL temporarily to prove the code works ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "https://voxen-a-multi-agent-ai-voice-platfo.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(plan.router, prefix="/api/v1/plan", tags=["plan"])
app.include_router(voice.router, prefix="/api/v1/voice", tags=["voice"])
app.include_router(chat_router)
app.include_router(telegram_router)
app.include_router(webhook_router)
app.include_router(webhook.router, prefix="/api/v1/webhook", tags=["webhook"])
app.include_router(voice_agent.router, prefix="/api/v1/voice-agent", tags=["voice-agent"])
app.include_router(keys_router)
app.include_router(voxen_keys_router)
app.include_router(ws_router)
app.include_router(metrics_router)
app.include_router(voice_process_router)
app.include_router(
    notifications.router,
    prefix="/api/v1/notifications",
    tags=["notifications"],
)

# Mount test client
app.mount("/test", StaticFiles(directory="test", html=True), name="test")

# Serve embeddable widget
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return {"message": "Voice Agent Backend is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}