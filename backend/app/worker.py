from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.plan import Plan, JobStatus
from app.schemas.plan import PlanCreate

async def generate_plan_task(job_id: str, plan_in: PlanCreate):
    # Get a DB session
    db = SessionLocal()
    try:
        # Find the Plan by job_id
        plan = db.query(Plan).filter(Plan.job_id == job_id).first()
        if not plan:
            return  # Or raise an exception?
        
        # Set status to "processing"
        plan.status = JobStatus.PROCESSING
        db.commit()
        
        try:
            # Placeholder for actual AI logic
            # For now, set markdown_output to a placeholder
            plan.markdown_output = "Plan generation not yet implemented"
            plan.status = JobStatus.COMPLETED
            db.commit()
        except Exception as e:
            # On failure, set status to "failed" and store error message
            plan.status = JobStatus.FAILED
            plan.error_message = str(e)
            db.commit()
    finally:
        db.close()