import asyncio
import logging
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.database import get_db, get_sync_db, async_session_factory, sync_session_factory
from app.api.deps import get_current_user
from app.models.user import User
from app.models.app import AppStatus
from app.schemas.app import AppResponse, AppListResponse, GenerateAppRequest
from app.schemas.blueprint import BlueprintResponse
from app.schemas.job import JobResponse
from app.services.app_service import AppService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/apps", tags=["apps"])


@router.get("", response_model=AppListResponse)
async def list_apps(
   current_user: User = Depends(get_current_user),
   db: AsyncSession = Depends(get_db)
):
   """List all apps for the current user."""
   app_service = AppService(db)
   apps = await app_service.list_apps(current_user.id)
   return AppListResponse(apps=apps, total=len(apps))


async def _run_generation_in_background(
   job_id: UUID,
   app_id: UUID,
   prompt: str,
   model: Optional[str]
):
   """Run the actual generation in background."""
   logger.info(f"Background task started for job {job_id}")
   db = None
   sync_db = None
   try:
      db = async_session_factory()
      sync_db = sync_session_factory()
      logger.info(f"Starting generation for job {job_id}")
      app_service = AppService(db)
      await app_service.run_generation(
         job_id=job_id,
         app_id=app_id,
         prompt=prompt,
         model=model,
         sync_db=sync_db
      )
      logger.info(f"Generation completed for job {job_id}")
   except Exception as e:
      logger.error(f"Background generation failed for job {job_id}: {e}", exc_info=True)
      # Update job status to FAILED
      if db:
         try:
            from app.models.job import GenerationJob, JobStatus
            from sqlalchemy import select
            result = await db.execute(select(GenerationJob).where(GenerationJob.id == job_id))
            job = result.scalar_one_or_none()
            if job:
               job.status = JobStatus.FAILED
               job.error_message = str(e)
               await db.commit()
         except Exception as e2:
            logger.error(f"Failed to update job status: {e2}")
   finally:
      if sync_db:
         sync_db.close()
      if db:
         await db.close()


@router.post("/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate_app(
   request: GenerateAppRequest,
   current_user: User = Depends(get_current_user),
   db: AsyncSession = Depends(get_db),
):
   """Generate a new app from a prompt. Returns immediately with job ID."""
   app_service = AppService(db)

   try:
      # Create app and job records immediately
      job_id, app_id = await app_service.create_generation_job(
         user_id=current_user.id,
         prompt=request.prompt,
         model=request.model,
      )
      
      # Run the actual generation in a background task
      logger.info(f"Creating background task for job {job_id}, app {app_id}")
      
      def task_done_callback(t):
         try:
            exc = t.exception()
            if exc:
               logger.error(f"Background task failed with exception: {exc}")
         except asyncio.CancelledError:
            logger.warning(f"Background task was cancelled")
      
      task = asyncio.create_task(
         _run_generation_in_background(
            job_id,
            app_id,
            request.prompt,
            request.model
         )
      )
      task.add_done_callback(task_done_callback)
      
      logger.info(f"Background task created: {task}")
      return {"job_id": str(job_id), "app_id": str(app_id)}
   except Exception as e:
      raise HTTPException(
         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
         detail=str(e)
      )


@router.get("/{app_id}", response_model=AppResponse)
async def get_app(
   app_id: UUID,
   current_user: User = Depends(get_current_user),
   db: AsyncSession = Depends(get_db)
):
   """Get app details."""
   app_service = AppService(db)
   app = await app_service.get_app(app_id, current_user.id)
   if not app:
      raise HTTPException(
         status_code=status.HTTP_404_NOT_FOUND,
         detail="App not found"
      )
   return app


@router.post("/{app_id}/start")
async def start_app(
   app_id: UUID,
   current_user: User = Depends(get_current_user),
   db: AsyncSession = Depends(get_db)
):
   """Start an app."""
   app_service = AppService(db)
   success = await app_service.start_app(app_id, current_user.id)
   if not success:
      raise HTTPException(
         status_code=status.HTTP_404_NOT_FOUND,
         detail="App not found"
      )
   return {"status": "started"}


@router.post("/{app_id}/stop")
async def stop_app(
   app_id: UUID,
   current_user: User = Depends(get_current_user),
   db: AsyncSession = Depends(get_db)
):
   """Stop an app."""
   app_service = AppService(db)
   success = await app_service.stop_app(app_id, current_user.id)
   if not success:
      raise HTTPException(
         status_code=status.HTTP_404_NOT_FOUND,
         detail="App not found"
      )
   return {"status": "stopped"}


@router.delete("/{app_id}")
async def delete_app(
   app_id: UUID,
   current_user: User = Depends(get_current_user),
   db: AsyncSession = Depends(get_db),
   sync_db: Session = Depends(get_sync_db)
):
   """Delete an app."""
   app_service = AppService(db)
   success = await app_service.delete_app(app_id, current_user.id, sync_db)
   if not success:
      raise HTTPException(
         status_code=status.HTTP_404_NOT_FOUND,
         detail="App not found"
      )
   return {"status": "deleted"}


@router.get("/{app_id}/blueprints/latest", response_model=BlueprintResponse)
async def get_latest_blueprint(
   app_id: UUID,
   current_user: User = Depends(get_current_user),
   db: AsyncSession = Depends(get_db)
):
   """Get the latest blueprint for an app."""
   app_service = AppService(db)

   # Verify app ownership
   app = await app_service.get_app(app_id, current_user.id)
   if not app:
      raise HTTPException(
         status_code=status.HTTP_404_NOT_FOUND,
         detail="App not found"
      )

   blueprint = await app_service.get_latest_blueprint(app_id)
   if not blueprint:
      raise HTTPException(
         status_code=status.HTTP_404_NOT_FOUND,
         detail="Blueprint not found"
      )
   return blueprint

