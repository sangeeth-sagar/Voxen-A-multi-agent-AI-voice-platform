from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.plan import Plan, JobStatus
from app.schemas.plan import PlanCreate
from app.services.workflow import run_plan_workflow

async def generate_plan_task(job_id: str, plan_in: PlanCreate):
    db = SessionLocal()
    plan = None
    try:
        plan = db.query(Plan).filter(Plan.job_id == job_id).first()
        if not plan:
            return {"status": "error", "message": "Job not found"}

        plan.status = JobStatus.PROCESSING
        db.commit()

        result = run_plan_workflow(job_id, plan_in.user_prompt if hasattr(plan_in, "user_prompt") else str(plan_in))

        plan.structured_json = result.get("structured_json", {})
        plan.markdown_output = result.get("markdown_output", "")
        plan.extracted_goals = result.get("execution_plan", [])
        plan.status = JobStatus.COMPLETED
        db.commit()

        return {"status": "completed", "job_id": job_id}

    except Exception as e:
        if plan:
            plan.status = JobStatus.FAILED
            plan.error_message = str(e)
            db.commit()
        raise
    finally:
        db.close()
