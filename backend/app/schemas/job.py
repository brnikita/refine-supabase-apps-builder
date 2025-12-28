from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any
from app.models.job import JobStatus


class JobResponse(BaseModel):
   id: UUID
   app_id: UUID
   status: JobStatus
   model: str
   prompt: str
   error_message: Optional[str]
   created_at: datetime
   updated_at: datetime

   class Config:
      from_attributes = True


class JobDetailResponse(JobResponse):
   llm_request: Optional[Dict[str, Any]]
   llm_response: Optional[Dict[str, Any]]

