from typing import List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.agent_config import AgentConfig
from app.models.voxen_api_key import VoxenApiKey

router = APIRouter(prefix="/api/v1/voxen-keys", tags=["voxen-api-keys"])

class CreateKeyRequest(BaseModel):
    label: str

class VoxenApiKeyResponse(BaseModel):
    id: int
    agent_id: int
    key_preview: str
    label: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/agent/{agent_id}", response_model=List[VoxenApiKeyResponse])
def list_voxen_keys(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists all Voxen API keys for a given agent owned by the user."""
    agent = db.query(AgentConfig).filter(AgentConfig.id == agent_id, AgentConfig.user_id == current_user.id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    keys = db.query(VoxenApiKey).filter(
        VoxenApiKey.agent_id == agent_id,
        VoxenApiKey.user_id == current_user.id
    ).order_by(VoxenApiKey.created_at.desc()).all()

    # Build response format with masked preview
    result = []
    for k in keys:
        preview = f"{k.api_key[:8]}...{k.api_key[-4:]}" if len(k.api_key) > 12 else "****"
        result.append(
            VoxenApiKeyResponse(
                id=k.id,
                agent_id=k.agent_id,
                key_preview=preview,
                label=k.label,
                is_active=k.is_active,
                created_at=k.created_at
            )
        )
    return result

@router.post("/agent/{agent_id}")
def generate_voxen_key(
    agent_id: int,
    body: CreateKeyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generates a new Voxen API key for the agent. Exposes the full key ONCE."""
    agent = db.query(AgentConfig).filter(AgentConfig.id == agent_id, AgentConfig.user_id == current_user.id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    plain_key = VoxenApiKey.generate_key_string()
    
    new_key = VoxenApiKey(
        user_id=current_user.id,
        agent_id=agent_id,
        api_key=plain_key,
        label=body.label.strip()
    )
    db.add(new_key)
    db.commit()
    db.refresh(new_key)

    return {
        "id": new_key.id,
        "agent_id": new_key.agent_id,
        "label": new_key.label,
        "full_key": plain_key,  # Expose this only on creation
        "key_preview": f"{plain_key[:8]}...{plain_key[-4:]}",
        "created_at": new_key.created_at
    }

@router.delete("/{key_id}")
def revoke_voxen_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Revokes (deletes) a Voxen API key."""
    key = db.query(VoxenApiKey).filter(
        VoxenApiKey.id == key_id,
        VoxenApiKey.user_id == current_user.id
    ).first()

    if not key:
        raise HTTPException(status_code=404, detail="API Key not found")

    db.delete(key)
    db.commit()
    return {"message": "API key revoked successfully", "id": key_id}
