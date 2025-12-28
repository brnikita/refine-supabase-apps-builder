import uuid
import enum
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class AppStatus(str, enum.Enum):
   DRAFT = "DRAFT"
   RUNNING = "RUNNING"
   STOPPED = "STOPPED"
   ERROR = "ERROR"
   DELETING = "DELETING"


class App(Base):
   __tablename__ = "apps"
   __table_args__ = {"schema": "control_plane"}

   id: Mapped[uuid.UUID] = mapped_column(
      UUID(as_uuid=True),
      primary_key=True,
      default=uuid.uuid4
   )
   owner_user_id: Mapped[uuid.UUID] = mapped_column(
      UUID(as_uuid=True),
      ForeignKey("control_plane.users.id"),
      nullable=False
   )
   name: Mapped[str] = mapped_column(String(255), nullable=False)
   slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
   status: Mapped[AppStatus] = mapped_column(
      Enum(AppStatus, schema="control_plane"),
      default=AppStatus.DRAFT
   )
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
   owner = relationship("User", back_populates="apps")
   blueprints = relationship("AppBlueprint", back_populates="app", cascade="all, delete-orphan")
   generation_jobs = relationship("GenerationJob", back_populates="app", cascade="all, delete-orphan")
   runtime_config = relationship("AppRuntimeConfig", back_populates="app", uselist=False, cascade="all, delete-orphan")

