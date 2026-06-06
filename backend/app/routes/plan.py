from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import Optional
from app.auth.dependencies import get_optional_user
from app.database import get_db
from app.models.plan import Plan, JobStatus
from app.models.user import User
from app.schemas.plan import PlanCreate, PlanResponse
from app.worker import generate_plan_task
import uuid

router = APIRouter()


@router.post("", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def generate_plan(
    plan_in: PlanCreate,
    background_tasks: BackgroundTasks,
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    # Create plan record
    job_id = str(uuid.uuid4())
    plan = Plan(
        job_id=job_id,
        user_id=user.id if user else None,
        status=JobStatus.PENDING,
        user_prompt=plan_in.user_prompt,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    # Trigger async job
    background_tasks.add_task(generate_plan_task, job_id, plan_in)
    return PlanResponse.model_validate(plan)


@router.get("/{job_id}", response_model=PlanResponse)
def get_plan(
    job_id: str,
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    plan = db.query(Plan).filter(Plan.job_id == job_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found",
        )
    # Check ownership: if plan has a user_id, then only that user (or admin) can access
    if plan.user_id is not None:
        if user is None or user.id != plan.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )
    return PlanResponse.model_validate(plan)