import uuid
import enum
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base


class JobStatus(str, enum.Enum):
   QUEUED = "QUEUED"
   RUNNING = "RUNNING"
   SUCCEEDED = "SUCCEEDED"
   FAILED = "FAILED"


class GenerationJob(Base):
   __tablename__ = "generation_jobs"
   __table_args__ = {"schema": "control_plane"}

   id: Mapped[uuid.UUID] = mapped_column(
      UUID(as_uuid=True),
      primary_key=True,
      default=uuid.uuid4
   )
   app_id: Mapped[uuid.UUID] = mapped_column(
      UUID(as_uuid=True),
      ForeignKey("control_plane.apps.id"),
      nullable=False
   )
   status: Mapped[JobStatus] = mapped_column(
      Enum(JobStatus, schema="control_plane"),
      default=JobStatus.QUEUED
   )
   model: Mapped[str] = mapped_column(String(100), nullable=False)
   prompt: Mapped[str] = mapped_column(Text, nullable=False)
   llm_request: Mapped[dict] = mapped_column(JSONB, nullable=True)
   llm_response: Mapped[dict] = mapped_column(JSONB, nullable=True)
   error_message: Mapped[str] = mapped_column(Text, nullable=True)
   created_at: Mapped[datetime] = mapped_column(
      DateTime(timezone=True),
      default=datetime.utcnow
   )
   updated_at: Mapped[datetime] = mapped_column(
      DateTime(timezone=True),
      default=datetime.utcnow,
      onupdate=datetime.utcnow
   )

   # Relationships
   app = relationship("App", back_populates="generation_jobs")

