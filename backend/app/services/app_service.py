import json
import logging
import re
from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete

from app.models import App, AppStatus, AppBlueprint, ValidationStatus, GenerationJob, JobStatus, AppRuntimeConfig
from app.schemas.blueprint import BlueprintV1
from app.services.llm import LLMService
from app.services.blueprint import BlueprintService
from app.services.provisioning import ProvisioningService

logger = logging.getLogger(__name__)


class AppService:
   def __init__(self, db: AsyncSession):
      self.db = db
      self.llm_service = LLMService()
      self.blueprint_service = BlueprintService()

   async def list_apps(self, user_id: UUID) -> List[App]:
      """List all apps for a user."""
      result = await self.db.execute(
         select(App).where(App.owner_user_id == user_id).order_by(App.created_at.desc())
      )
      return result.scalars().all()

   async def get_app(self, app_id: UUID, user_id: UUID) -> Optional[App]:
      """Get an app by ID."""
      result = await self.db.execute(
         select(App).where(App.id == app_id, App.owner_user_id == user_id)
      )
      return result.scalar_one_or_none()

   async def get_app_by_slug(self, slug: str) -> Optional[App]:
      """Get an app by slug."""
      result = await self.db.execute(
         select(App).where(App.slug == slug)
      )
      return result.scalar_one_or_none()

   async def generate_app(
      self,
      user_id: UUID,
      prompt: str,
      model: Optional[str] = None,
      sync_db: Session = None
   ) -> Tuple[UUID, UUID]:
      """
      Generate a new app from a prompt.
      Returns: (job_id, app_id)
      """
      # Create a temporary app name and slug from prompt
      temp_name = prompt[:50].strip()
      temp_slug = self._generate_slug(temp_name)

      # Create the app record
      app = App(
         owner_user_id=user_id,
         name=temp_name,
         slug=temp_slug,
         status=AppStatus.DRAFT
      )
      self.db.add(app)
      await self.db.flush()

      # Create the generation job
      job = GenerationJob(
         app_id=app.id,
         status=JobStatus.RUNNING,
         model=model or self.llm_service.default_model,
         prompt=prompt
      )
      self.db.add(job)
      await self.db.flush()

      try:
         # Generate blueprint via LLM
         blueprint_dict, llm_request, llm_response = await self.llm_service.generate_blueprint(
            prompt, model
         )

         # Update job with LLM data
         job.llm_request = llm_request
         job.llm_response = llm_response

         # Validate blueprint
         is_valid, blueprint, errors = self.blueprint_service.validate_blueprint(blueprint_dict)

         if not is_valid:
            # Try to repair
            logger.info(f"Blueprint invalid, attempting repair. Errors: {errors}")
            try:
               blueprint_dict, repair_request, repair_response = await self.llm_service.repair_blueprint(
                  prompt,
                  json.dumps(blueprint_dict, indent=2),
                  "\n".join(errors),
                  model
               )
               job.llm_request = repair_request
               job.llm_response = repair_response

               is_valid, blueprint, errors = self.blueprint_service.validate_blueprint(blueprint_dict)
            except Exception as e:
               logger.error(f"Repair failed: {e}")

         if not is_valid:
            # Store invalid blueprint and fail
            app_blueprint = AppBlueprint(
               app_id=app.id,
               version=1,
               blueprint_json=blueprint_dict,
               blueprint_hash=self.blueprint_service.compute_hash(blueprint_dict),
               validation_status=ValidationStatus.INVALID,
               validation_errors={"errors": errors}
            )
            self.db.add(app_blueprint)

            job.status = JobStatus.FAILED
            job.error_message = f"Blueprint validation failed: {'; '.join(errors)}"
            app.status = AppStatus.ERROR

            await self.db.commit()
            return job.id, app.id

         # Blueprint is valid - update app with blueprint info
         app.name = blueprint.app.name
         app.slug = blueprint.app.slug
         app.status = AppStatus.RUNNING

         # Store blueprint
         app_blueprint = AppBlueprint(
            app_id=app.id,
            version=1,
            blueprint_json=blueprint_dict,
            blueprint_hash=self.blueprint_service.compute_hash(blueprint_dict),
            validation_status=ValidationStatus.VALID
         )
         self.db.add(app_blueprint)

         # Create runtime config
         schema_name = f"app_{str(app.id).replace('-', '')[:12]}"
         runtime_config = AppRuntimeConfig(
            app_id=app.id,
            db_schema=schema_name,
            public_base_path=f"/apps/{blueprint.app.slug}",
            enabled=True
         )
         self.db.add(runtime_config)

         await self.db.commit()

         # Provision database schema (sync operation)
         if sync_db:
            provisioning = ProvisioningService(sync_db)
            provisioning.provision_app_schema(schema_name, blueprint)

         # Update job status
         job.status = JobStatus.SUCCEEDED
         await self.db.commit()

         return job.id, app.id

      except Exception as e:
         logger.error(f"App generation failed: {e}")
         job.status = JobStatus.FAILED
         job.error_message = str(e)
         app.status = AppStatus.ERROR
         await self.db.commit()
         raise

   async def start_app(self, app_id: UUID, user_id: UUID) -> bool:
      """Start an app (set status to RUNNING)."""
      result = await self.db.execute(
         update(App)
         .where(App.id == app_id, App.owner_user_id == user_id)
         .values(status=AppStatus.RUNNING, updated_at=datetime.utcnow())
      )
      if result.rowcount > 0:
         await self.db.execute(
            update(AppRuntimeConfig)
            .where(AppRuntimeConfig.app_id == app_id)
            .values(enabled=True)
         )
         await self.db.commit()
         return True
      return False

   async def stop_app(self, app_id: UUID, user_id: UUID) -> bool:
      """Stop an app (set status to STOPPED)."""
      result = await self.db.execute(
         update(App)
         .where(App.id == app_id, App.owner_user_id == user_id)
         .values(status=AppStatus.STOPPED, updated_at=datetime.utcnow())
      )
      if result.rowcount > 0:
         await self.db.execute(
            update(AppRuntimeConfig)
            .where(AppRuntimeConfig.app_id == app_id)
            .values(enabled=False)
         )
         await self.db.commit()
         return True
      return False

   async def delete_app(self, app_id: UUID, user_id: UUID, sync_db: Session = None) -> bool:
      """Delete an app and its schema."""
      # Get the app first
      app = await self.get_app(app_id, user_id)
      if not app:
         return False

      # Get runtime config for schema name
      result = await self.db.execute(
         select(AppRuntimeConfig).where(AppRuntimeConfig.app_id == app_id)
      )
      runtime_config = result.scalar_one_or_none()

      # Mark as deleting
      app.status = AppStatus.DELETING
      await self.db.commit()

      # Drop schema if exists
      if runtime_config and sync_db:
         try:
            provisioning = ProvisioningService(sync_db)
            provisioning.drop_app_schema(runtime_config.db_schema)
         except Exception as e:
            logger.error(f"Failed to drop schema: {e}")

      # Delete the app (cascades to blueprints, jobs, runtime_config)
      await self.db.execute(delete(App).where(App.id == app_id))
      await self.db.commit()

      return True

   async def get_latest_blueprint(self, app_id: UUID) -> Optional[AppBlueprint]:
      """Get the latest blueprint for an app."""
      result = await self.db.execute(
         select(AppBlueprint)
         .where(AppBlueprint.app_id == app_id)
         .order_by(AppBlueprint.version.desc())
         .limit(1)
      )
      return result.scalar_one_or_none()

   async def get_job(self, job_id: UUID) -> Optional[GenerationJob]:
      """Get a generation job by ID."""
      result = await self.db.execute(
         select(GenerationJob).where(GenerationJob.id == job_id)
      )
      return result.scalar_one_or_none()

   def _generate_slug(self, name: str) -> str:
      """Generate a URL-safe slug from a name."""
      slug = name.lower()
      slug = re.sub(r'[^a-z0-9\s-]', '', slug)
      slug = re.sub(r'[\s_]+', '-', slug)
      slug = re.sub(r'-+', '-', slug)
      slug = slug.strip('-')
      return slug[:30] or "app"

