"""
Per-user API key management.

Each user can store multiple encrypted keys (one per provider) and assign
them to specific agents.
"""
from typing import List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.user_api_key import UserApiKey
from app.utils.encryption import encrypt_key, decrypt_key


router = APIRouter(prefix="/api/v1/keys", tags=["api-keys"])


SUPPORTED_PROVIDERS = {
    "llm": ["gemini", "openai", "claude"],
    "tts": ["elevenlabs", "groq", "azure_tts", "deepgram"],
    "stt": ["groq", "elevenlabs", "deepgram"],
}


class AddKeyRequest(BaseModel):
    provider: str
    api_key: str
    label: str


# ---------------------------------------------------------------------------
# Static provider catalog
# ---------------------------------------------------------------------------
@router.get("/providers")
async def get_providers(
    current_user: User = Depends(get_current_user),
):
    return SUPPORTED_PROVIDERS


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------
@router.get("/")
async def list_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List the caller's stored API keys. Only the last 4 characters of
    the decrypted key are returned — the full key is never exposed."""
    keys: List[UserApiKey] = (
        db.query(UserApiKey)
        .filter(
            UserApiKey.user_id == current_user.id,
            UserApiKey.is_active == True,  # noqa: E712
        )
        .all()
    )
    result = []
    for k in keys:
        try:
            plain = decrypt_key(k.api_key)
            preview = f"****{plain[-4:]}" if len(plain) >= 4 else "****"
        except Exception:
            preview = "****"
        result.append(
            {
                "id": k.id,
                "provider": k.provider,
                "label": k.label,
                "key_preview": preview,
                "is_active": k.is_active,
                "created_at": k.created_at,
            }
        )
    return result


@router.post("/")
async def add_key(
    body: AddKeyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Encrypt and store a new API key for the caller."""
    all_providers = (
        SUPPORTED_PROVIDERS["llm"]
        + SUPPORTED_PROVIDERS["tts"]
        + SUPPORTED_PROVIDERS["stt"]
    )
    if body.provider not in all_providers:
        raise HTTPException(
            status_code=400, detail=f"Unsupported provider: {body.provider}"
        )
    if not body.api_key or not body.api_key.strip():
        raise HTTPException(status_code=400, detail="api_key is required")
    if not body.label or not body.label.strip():
        raise HTTPException(status_code=400, detail="label is required")

    encrypted = encrypt_key(body.api_key.strip())
    key = UserApiKey(
        user_id=current_user.id,
        provider=body.provider,
        api_key=encrypted,
        label=body.label.strip(),
    )
    db.add(key)
    db.commit()
    db.refresh(key)
    return {"message": "Key added successfully", "id": key.id}


@router.delete("/{key_id}")
async def delete_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deleted = (
        db.query(UserApiKey)
        .filter(
            UserApiKey.id == key_id,
            UserApiKey.user_id == current_user.id,
        )
        .delete()
    )
    db.commit()
    if not deleted:
        raise HTTPException(status_code=404, detail="Key not found")
    return {"deleted": key_id}
