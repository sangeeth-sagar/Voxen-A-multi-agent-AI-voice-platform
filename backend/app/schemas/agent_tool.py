from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class AgentToolCreate(BaseModel):
    name: str
    description: Optional[str] = None
    webhook_url: str
    parameters: List[Dict[str, Any]] = []
    is_active: bool = True

class AgentToolUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    webhook_url: Optional[str] = None
    parameters: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None

class AgentToolResponse(BaseModel):
    uuid: str
    name: str
    description: Optional[str] = None
    webhook_url: str
    parameters: List[Dict[str, Any]] = []
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
