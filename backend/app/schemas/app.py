from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from app.models.app import AppStatus


class AppCreate(BaseModel):
   name: str
   slug: str


class GenerateAppRequest(BaseModel):
   prompt: str
   model: Optional[str] = None


class AppResponse(BaseModel):
   id: UUID
   name: str
   slug: str
   status: AppStatus
   created_at: datetime
   updated_at: datetime
   owner_user_id: UUID

   class Config:
      from_attributes = True


class AppListResponse(BaseModel):
   apps: List[AppResponse]
   total: int


class GenerateAppResponse(BaseModel):
   job_id: UUID
   app_id: UUID

