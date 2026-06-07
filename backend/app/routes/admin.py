"""
Superadmin-only administration endpoints.

All routes require `current_user.is_superadmin == True`. The check is
performed by `require_superadmin`.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.security import hash_password
from app.models.user import User
from app.models.agent_config import AgentConfig


router = APIRouter()


def require_superadmin(
    current_user: User = Depends(get_current_user),
) -> User:
    if not getattr(current_user, "is_superadmin", False):
        raise HTTPException(status_code=403, detail="Superadmin access required")
    return current_user


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------
@router.get("/stats")
async def get_stats(
    admin: User = Depends(require_superadmin),
    db: Session = Depends(get_db),
):
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()  # noqa: E712
    total_agents = db.query(AgentConfig).count()
    return {
        "total_users": total_users,
        "active_users": active_users,
        "suspended_users": total_users - active_users,
        "total_agents": total_agents,
    }


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
@router.get("/users")
async def list_all_users(
    admin: User = Depends(require_superadmin),
    db: Session = Depends(get_db),
):
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "uuid": u.uuid,
            "email": u.email,
            "username": u.username,
            "full_name": getattr(u, "full_name", None) or u.username,
            "is_active": u.is_active,
            "is_superadmin": getattr(u, "is_superadmin", False),
            "role": u.role.value if hasattr(u.role, "value") else u.role,
            "agent_count": (
                db.query(AgentConfig)
                .filter(AgentConfig.user_id == u.id)
                .count()
            ),
        }
        for u in users
    ]


@router.patch("/users/{user_id}/toggle")
async def toggle_user_active(
    user_id: int,
    admin: User = Depends(require_superadmin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_superadmin:
        raise HTTPException(
            status_code=400, detail="Cannot suspend a superadmin"
        )
    user.is_active = not user.is_active
    db.commit()
    return {"user_id": user_id, "is_active": user.is_active}


@router.patch("/users/{user_id}/promote")
async def promote_to_superadmin(
    user_id: int,
    admin: User = Depends(require_superadmin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_superadmin = True
    db.commit()
    return {"user_id": user_id, "is_superadmin": True}


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    admin: User = Depends(require_superadmin),
    db: Session = Depends(get_db),
):
    """Generate a new random password for a user and return it once."""
    import secrets
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    new_password = secrets.token_urlsafe(12)
    user.hashed_password = hash_password(new_password)
    db.commit()
    return {"user_id": user_id, "new_password": new_password}


# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------
@router.get("/agents")
async def list_all_agents(
    admin: User = Depends(require_superadmin),
    db: Session = Depends(get_db),
):
    return db.query(AgentConfig).all()


@router.delete("/agents/{agent_id}")
async def delete_any_agent(
    agent_id: int,
    admin: User = Depends(require_superadmin),
    db: Session = Depends(get_db),
):
    deleted = (
        db.query(AgentConfig)
        .filter(AgentConfig.id == agent_id)
        .delete()
    )
    db.commit()
    if not deleted:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"deleted": agent_id}
