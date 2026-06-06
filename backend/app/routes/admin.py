from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from app.auth.dependencies import get_current_user, require_admin
from app.database import get_db
from app.models.user import User, UserRole
from app.models.plan import Plan, JobStatus
from app.schemas.user import UserResponse, AdminUserUpdate, AdminPasswordReset
from app.auth.security import hash_password
from datetime import datetime, timedelta
import math

router = APIRouter()


@router.get("/users", response_model=List[UserResponse])
def get_users(
    search: str = "",
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    query = db.query(User)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.email.ilike(search_term)) | (User.username.ilike(search_term))
        )
    users = query.all()
    return [UserResponse.model_validate(user) for user in users]


@router.patch("/users/{user_uuid}", response_model=UserResponse)
def update_user(
    user_uuid: str,
    user_in: AdminUserUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    # Find the user by uuid
    user = db.query(User).filter(User.uuid == user_uuid).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    # Prevent modifying own account via this endpoint
    if user.id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify your own account via this endpoint",
        )
    # Update role if provided
    if user_in.role is not None:
        if user_in.role not in [r.value for r in UserRole]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role",
            )
        user.role = UserRole(user_in.role)
    # Update is_active if provided
    if user_in.is_active is not None:
        user.is_active = user_in.is_active
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.delete("/users/{user_uuid}", status_code=status.HTTP_200_OK)
def deactivate_user(
    user_uuid: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    user = db.query(User).filter(User.uuid == user_uuid).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    # Prevent self-deactivation
    if user.id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account",
        )
    # Soft delete: set is_active=False and anonymize email
    user.is_active = False
    user.email = f"deleted_{user.id}@deleted.invalid"
    db.commit()
    return {"message": "User deactivated"}


@router.get("/jobs", response_model=List[dict])
def get_jobs(
    status_filter: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    query = db.query(Plan)
    if status_filter:
        if status_filter not in [s.value for s in JobStatus]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status",
            )
        query = query.filter(Plan.status == status_filter)
    jobs = query.order_by(desc(Plan.created_at)).limit(100).all()
    # Convert to list of dicts with required fields
    jobs_data = []
    for job in jobs:
        job_dict = {
            "job_id": job.job_id,
            "status": job.status,
            "user_prompt": job.user_prompt,
            "created_at": job.created_at,
            "username": job.user.username if job.user else None
        }
        jobs_data.append(job_dict)
    return jobs_data


@router.get("/stats", response_model=dict)
def get_stats(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    # Total users
    total_users = db.query(User).count()
    # Active users
    active_users = db.query(User).filter(User.is_active == True).count()
    # Admin users
    admin_users = db.query(User).filter(User.role == UserRole.ADMIN).count()
    # Total jobs
    total_jobs = db.query(Plan).count()
    # Completed jobs
    completed_jobs = db.query(Plan).filter(Plan.status == JobStatus.COMPLETED).count()
    # Failed jobs
    failed_jobs = db.query(Plan).filter(Plan.status == JobStatus.FAILED).count()
    # Pending jobs
    pending_jobs = db.query(Plan).filter(Plan.status == JobStatus.PENDING).count()
    # Total tokens and cost from users
    total_tokens = db.query(func.sum(User.total_tokens)).scalar() or 0
    total_cost_usd = db.query(func.sum(User.total_cost_usd)).scalar() or 0.0
    # Jobs today
    today = datetime.utcnow().date()
    jobs_today = db.query(Plan).filter(func.date(Plan.created_at) == today).count()
    # Average QA score from completed jobs' structured_json
    # We assume structured_json is a JSON field and we want to extract the 'qa_score' field
    # This is database-specific. For SQLite, we can use json_extract. For PostgreSQL, we can use ->>.
    # Since we don't know the database, we'll do a fallback: if the field doesn't exist, we return 0.
    # We'll try to compute the average only for jobs that have structured_json and qa_score.
    # This is a simplified version. In a real app, you might want to store QA score separately.
    qa_scores = []
    completed_plans = db.query(Plan).filter(Plan.status == JobStatus.COMPLETED).all()
    for plan in completed_plans:
        if plan.structured_json and isinstance(plan.structured_json, dict):
            qa_score = plan.structured_json.get("qa_score")
            if qa_score is not None and isinstance(qa_score, (int, float)):
                qa_scores.append(float(qa_score))
    avg_qa_score = sum(qa_scores) / len(qa_scores) if qa_scores else 0.0
    return {
        "total_users": total_users,
        "active_users": active_users,
        "admin_users": admin_users,
        "total_jobs": total_jobs,
        "completed_jobs": completed_jobs,
        "failed_jobs": failed_jobs,
        "pending_jobs": pending_jobs,
        "total_tokens": int(total_tokens),
        "total_cost_usd": float(total_cost_usd),
        "jobs_today": jobs_today,
        "avg_qa_score": float(avg_qa_score),
    }


@router.post("/users/{user_uuid}/reset-password")
def admin_reset_password(
    user_uuid: str,
    body: AdminPasswordReset,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Admin directly sets a new password for any user.
    No current password required — admin override.
    """
    user = db.query(User).filter(User.uuid == user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = hash_password(body.new_password)
    db.commit()

    import structlog
    logger = structlog.get_logger(__name__)
    logger.info(
        "admin_password_reset",
        target_user=user.email,
        admin=admin.email,
    )
    return {"message": f"Password reset successfully for {user.username}"}