from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

class PlanCreate(BaseModel):
    user_prompt: str

class PlanResponse(BaseModel):
    job_id: str
    status: str
    user_prompt: Optional[str] = None
    structured_json: Optional[Dict] = None
    markdown_output: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}