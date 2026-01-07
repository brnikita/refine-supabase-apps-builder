import json
import logging
import re
import random
import string
from typing import Optional, List, Tuple, Union
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete

from app.models import App, AppStatus, AppBlueprint, ValidationStatus, GenerationJob, JobStatus, AppRuntimeConfig
from app.schemas.blueprint import BlueprintV2, BlueprintV3
from app.services.llm import LLMService
from app.services.blueprint import BlueprintService
from app.services.provisioning import ProvisioningService
from app.services.backend_generator import BackendGeneratorService

logger = logging.getLogger(__name__)


class AppService:
   def __init__(self, db: AsyncSession):
      self.db = db
      self.llm_service = LLMService()
      self.blueprint_service = BlueprintService()
      self.backend_generator = BackendGeneratorService()

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

   async def _ensure_unique_slug(self, base_slug: str, exclude_app_id: Optional[UUID] = None) -> str:
      """Ensure the slug is unique by appending a suffix if necessary."""
      slug = base_slug
      attempt = 0
      max_attempts = 100

      while attempt < max_attempts:
         # Check if slug exists
         query = select(App).where(App.slug == slug)
         if exclude_app_id:
            query = query.where(App.id != exclude_app_id)
         
         result = await self.db.execute(query)
         existing = result.scalar_one_or_none()

         if not existing:
            return slug

         # Generate a new slug with suffix
         attempt += 1
         if attempt <= 10:
            # First try numeric suffixes
            slug = f"{base_slug[:25]}-{attempt}"
         else:
            # Then try random suffixes
            suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
            slug = f"{base_slug[:25]}-{suffix}"

      # Fallback: use timestamp
      timestamp = datetime.utcnow().strftime("%H%M%S")
      return f"{base_slug[:20]}-{timestamp}"

   async def generate_app(
      self,
      user_id: UUID,
      prompt: str,
      model: Optional[str] = None,
      sync_db: Session = None,
      version: int = 3  # Default to V3
   ) -> Tuple[UUID, UUID]:
      """
      Generate a new app from a prompt.
      Returns: (job_id, app_id)
      """
      # Create a temporary app name and slug from prompt
      temp_name = prompt[:50].strip()
      temp_slug = self._generate_slug(temp_name)
      # Ensure temp slug is unique
      temp_slug = await self._ensure_unique_slug(temp_slug)

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
         # Generate blueprint via LLM (now generates V3)
         blueprint_dict, llm_request, llm_response = await self.llm_service.generate_blueprint(
            prompt, model, version=version
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
                  model,
                  version=version
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
               version=version,
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
         # Ensure the blueprint slug is unique
         unique_slug = await self._ensure_unique_slug(blueprint.app.slug, exclude_app_id=app.id)
         
         app.name = blueprint.app.name
         app.slug = unique_slug
         app.status = AppStatus.RUNNING

         # Update the blueprint dict with the unique slug if it changed
         if unique_slug != blueprint.app.slug:
            blueprint_dict['app']['slug'] = unique_slug

         # Store blueprint
         app_blueprint = AppBlueprint(
            app_id=app.id,
            version=version,
            blueprint_json=blueprint_dict,
            blueprint_hash=self.blueprint_service.compute_hash(blueprint_dict),
            validation_status=ValidationStatus.VALID
         )
         self.db.add(app_blueprint)

         # Create runtime config
         schema_name = f"app_{str(app.id).replace('-', '')[:12]}"
         
         # For V3, generate backend and get the URL
         backend_url = None
         backend_port = None
         
         if version == 3 and isinstance(blueprint, BlueprintV3):
            try:
               backend_result = await self.backend_generator.generate_backend(
                  app.id, blueprint, schema_name
               )
               backend_url = backend_result.get("backend_url")
               backend_port = backend_result.get("port")
               logger.info(f"Generated backend for app {app.id}: {backend_url}")
            except Exception as e:
               logger.error(f"Failed to generate backend: {e}")
               # Continue without backend - app will use mock data

         runtime_config = AppRuntimeConfig(
            app_id=app.id,
            db_schema=schema_name,
            public_base_path=f"/apps/{unique_slug}",
            enabled=True
         )
         self.db.add(runtime_config)

         await self.db.commit()

         # Provision database schema (sync operation) - for V2 or as fallback
         if sync_db and (version == 2 or not backend_url):
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
      """Start an app (set status to RUNNING) and start backend container."""
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
         
         # Start the backend container if it exists
         try:
            await self.backend_generator.start_backend(app_id)
            logger.info(f"Started backend container for app {app_id}")
         except Exception as e:
            logger.warning(f"Failed to start backend container for app {app_id}: {e}")
         
         return True
      return False

   async def stop_app(self, app_id: UUID, user_id: UUID) -> bool:
      """Stop an app (set status to STOPPED) and stop backend container."""
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
         
         # Stop the backend container if it exists
         try:
            await self.backend_generator.stop_backend(app_id)
            logger.info(f"Stopped backend container for app {app_id}")
         except Exception as e:
            logger.warning(f"Failed to stop backend container for app {app_id}: {e}")
         
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

      # Delete generated backend if exists
      try:
         await self.backend_generator.delete_backend(app_id)
      except Exception as e:
         logger.error(f"Failed to delete generated backend: {e}")

      # Delete related records first (in correct order due to FK constraints)
      # Delete blueprints
      await self.db.execute(delete(AppBlueprint).where(AppBlueprint.app_id == app_id))
      # Delete generation jobs
      await self.db.execute(delete(GenerationJob).where(GenerationJob.app_id == app_id))
      # Delete runtime config
      await self.db.execute(delete(AppRuntimeConfig).where(AppRuntimeConfig.app_id == app_id))
      # Delete the app
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

   async def get_backend_status(self, app_id: UUID) -> Optional[dict]:
      """Get the status of the generated backend for an app."""
      return await self.backend_generator.get_backend_status(app_id)

   def _generate_slug(self, name: str) -> str:
      """Generate a URL-safe slug from a name."""
      slug = name.lower()
      slug = re.sub(r'[^a-z0-9\s-]', '', slug)
      slug = re.sub(r'[\s_]+', '-', slug)
      slug = re.sub(r'-+', '-', slug)
      slug = slug.strip('-')
      return slug[:30] or "app"
