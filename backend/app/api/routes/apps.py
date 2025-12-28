from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.database import get_db, get_sync_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.app import AppStatus
from app.schemas.app import AppResponse, AppListResponse, GenerateAppRequest
from app.schemas.blueprint import BlueprintResponse
from app.schemas.job import JobResponse
from app.services.app_service import AppService

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


@router.post("/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate_app(
   request: GenerateAppRequest,
   current_user: User = Depends(get_current_user),
   db: AsyncSession = Depends(get_db),
   sync_db: Session = Depends(get_sync_db)
):
   """Generate a new app from a prompt."""
   app_service = AppService(db)

   try:
      job_id, app_id = await app_service.generate_app(
         user_id=current_user.id,
         prompt=request.prompt,
         model=request.model,
         sync_db=sync_db
      )
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

