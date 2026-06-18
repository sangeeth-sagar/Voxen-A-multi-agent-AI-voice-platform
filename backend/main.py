from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.routes import auth, admin, agents, plan, voice, webhook, voice_agent
from app.routes.api_keys import router as keys_router
from app.routes.ws_voice import router as ws_router
from app.routes.webhooks import router as webhook_router
from app.routes.metrics import router as metrics_router
from app.routes.voice_process import router as voice_process_router
from app.config import settings  # Optimized import

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
app.include_router(webhook_router)
app.include_router(webhook.router, prefix="/api/v1/webhook", tags=["webhook"])
app.include_router(voice_agent.router, prefix="/api/v1/voice-agent", tags=["voice-agent"])
app.include_router(keys_router)
app.include_router(ws_router)
app.include_router(metrics_router)
app.include_router(voice_process_router)

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