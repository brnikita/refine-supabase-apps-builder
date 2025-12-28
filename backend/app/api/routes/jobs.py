from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.job import JobResponse, JobDetailResponse
from app.services.app_service import AppService

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobDetailResponse)
async def get_job(
   job_id: UUID,
   current_user: User = Depends(get_current_user),
   db: AsyncSession = Depends(get_db)
):
   """Get job details."""
   app_service = AppService(db)
   job = await app_service.get_job(job_id)

   if not job:
      raise HTTPException(
         status_code=status.HTTP_404_NOT_FOUND,
         detail="Job not found"
      )

   # Verify ownership through app
   app = await app_service.get_app(job.app_id, current_user.id)
   if not app:
      raise HTTPException(
         status_code=status.HTTP_404_NOT_FOUND,
         detail="Job not found"
      )

   return job

