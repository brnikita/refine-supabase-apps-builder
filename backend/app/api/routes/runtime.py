from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import App, AppStatus, AppRuntimeConfig, AppBlueprint
from app.services.app_service import AppService

router = APIRouter(prefix="/runtime", tags=["runtime"])


@router.get("/apps/{slug}")
async def get_runtime_app(
   slug: str,
   db: AsyncSession = Depends(get_db)
):
   """Get app runtime info by slug (public endpoint for runtime)."""
   app_service = AppService(db)
   app = await app_service.get_app_by_slug(slug)

   if not app:
      raise HTTPException(
         status_code=status.HTTP_404_NOT_FOUND,
         detail="App not found"
      )

   if app.status != AppStatus.RUNNING:
      return {
         "status": "stopped",
         "message": "This app is currently stopped"
      }

   # Get runtime config
   result = await db.execute(
      select(AppRuntimeConfig).where(AppRuntimeConfig.app_id == app.id)
   )
   runtime_config = result.scalar_one_or_none()

   # Get latest blueprint
   blueprint = await app_service.get_latest_blueprint(app.id)

   return {
      "status": "running",
      "app": {
         "id": str(app.id),
         "name": app.name,
         "slug": app.slug
      },
      "runtime_config": {
         "db_schema": runtime_config.db_schema if runtime_config else None,
         "base_path": runtime_config.public_base_path if runtime_config else None
      },
      "blueprint": blueprint.blueprint_json if blueprint else None
   }

