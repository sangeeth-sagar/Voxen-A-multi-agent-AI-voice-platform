"""
Plan generation workflow.
Stub implementation -- replace with real LangGraph multi-agent pipeline.
"""
import structlog

logger = structlog.get_logger(__name__)


def run_plan_workflow(job_id: str, user_prompt: str) -> dict:
    """
    Run the multi-agent plan generation workflow.

    Returns a dict with keys:
        structured_json  - parsed plan data
        markdown_output  - human-readable plan
        execution_plan   - list of execution steps
    """
    logger.info("plan_workflow_started", job_id=job_id)

    structured_json = {
        "job_id": job_id,
        "user_prompt": user_prompt,
        "steps": [
            {"step": 1, "action": "analyze", "description": "Analyze the user request"},
            {"step": 2, "action": "plan", "description": "Generate execution plan"},
            {"step": 3, "action": "validate", "description": "Validate the plan"},
        ],
    }

    markdown_output = (
        f"# Plan for Job {job_id}\n\n"
        f"## Request\n{user_prompt}\n\n"
        f"## Steps\n"
        f"1. Analyze the user request\n"
        f"2. Generate execution plan\n"
        f"3. Validate the plan\n"
    )

    execution_plan = structured_json["steps"]

    logger.info("plan_workflow_completed", job_id=job_id)
    return {
        "structured_json": structured_json,
        "markdown_output": markdown_output,
        "execution_plan": execution_plan,
    }
