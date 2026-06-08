from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.auth.security import hash_password, verify_password, create_access_token
from app.auth.dependencies import get_current_user, get_optional_user, require_admin
from app.config import get_settings
from app.database import get_db
from app.models.user import User, UserRole
from app.models.agent_config import AgentConfig
from app.schemas.user import (
    UserRegister, UserLogin, UserResponse, TokenResponse, UserUpdate, AdminUserUpdate,
    AdminPasswordReset, UserPasswordReset
)


router = APIRouter()

limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(request: Request, user_in: UserRegister, db: Session = Depends(get_db)):
    # Check email uniqueness
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    # Check username uniqueness
    if db.query(User).filter(User.username == user_in.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )
    # Create user
    hashed_pw = hash_password(user_in.password)
    user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=hashed_pw,
        role=UserRole.USER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    # Create default voice agent for new user
    DEFAULT_VOICE_PROMPT = """You are a helpful, friendly, and concise AI voice assistant.
You answer questions clearly and briefly since your responses will be spoken aloud.
Keep responses under 3 sentences unless more detail is explicitly requested.
Be conversational and natural. Never use markdown, bullet points, or special
characters in your responses — only plain spoken language."""

    default_voice_agent = AgentConfig(
        user_id=user.id,
        name="Default Voice Assistant",
        description="Your personal AI voice assistant. Ask anything!",
        agent_type="voice",
        is_voice_agent=True,
        voice_language="en",    # use 2-letter code matching the language system
        voice_system_prompt=DEFAULT_VOICE_PROMPT,
        tools_enabled=[],
        output_format="text",
        is_public=False,
        is_template=False,
        wake_word="Nova",
    )
    db.add(default_voice_agent)

    # Also create the default Business Intelligence Agent
    default_bi_agent = AgentConfig(
        user_id=user.id,
        name="Business Intelligence Agent",
        description="Generate GTM strategies, competitor analysis, and business plans.",
        agent_type="business_intel",
        is_voice_agent=False,
        tools_enabled=["web_search", "memory", "critic"],
        output_format="markdown",
        is_public=False,
        is_template=False,
    )
    db.add(default_bi_agent)
    db.commit()
    # Create access token
    access_token = create_access_token(user.uuid, user.role.value)
    # Return token and user info
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
        needs_api_key=True,    # signal frontend to show key setup prompt
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, user_in: UserLogin, db: Session = Depends(get_db)):
    # Find user by email
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    # Create access token
    access_token = create_access_token(user.uuid, user.role.value)
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
def update_current_user(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # If username is being updated, check uniqueness
    if user_in.username is not None and user_in.username != current_user.username:
        if db.query(User).filter(User.username == user_in.username).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken",
            )
        current_user.username = user_in.username
    # If new password is provided, verify current password and update
    if user_in.new_password is not None:
        if not user_in.current_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password required to set new password",
            )
        if not verify_password(user_in.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect current password",
            )
        current_user.hashed_password = hash_password(user_in.new_password)
    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(current_user: User = Depends(get_current_user)):
    # JWT is stateless, so we just return a message.
    # The client should discard the token.
    return {"message": "Logged out successfully"}


@router.post("/change-password")
def change_own_password(
    body: UserPasswordReset,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """User changes their own password — requires current password."""
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.hashed_password = hash_password(body.new_password)
    db.commit()
    return {"message": "Password updated successfully"}