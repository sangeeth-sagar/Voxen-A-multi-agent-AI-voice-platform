from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, admin, agents, plan, voice, webhook, voice_agent
from app.config import get_settings

app = FastAPI(
    title=get_settings().app_name,
    version=get_settings().app_version,
    description="Voice Agent Backend with Authentication and Admin Panel",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(plan.router, prefix="/api/v1/plan", tags=["plan"])
app.include_router(
    voice.router,
    prefix="/api/v1/voice",
    tags=["voice"]
)
app.include_router(
    webhook.router,
    prefix="/api/v1/webhook",
    tags=["webhook"]
)
app.include_router(
    voice_agent.router,
    prefix="/api/v1/voice-agent",
    tags=["voice-agent"]
)

@app.get("/")
def root():
    return {"message": "Voice Agent Backend is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}