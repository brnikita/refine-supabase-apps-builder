import uuid
import enum
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Enum, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base


class ValidationStatus(str, enum.Enum):
   VALID = "VALID"
   INVALID = "INVALID"


class AppBlueprint(Base):
   __tablename__ = "app_blueprints"
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
   version: Mapped[int] = mapped_column(Integer, default=1)
   blueprint_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
   blueprint_hash: Mapped[str] = mapped_column(String(64), nullable=True)
   validation_status: Mapped[ValidationStatus] = mapped_column(
      Enum(ValidationStatus, schema="control_plane"),
      default=ValidationStatus.VALID
   )
   validation_errors: Mapped[dict] = mapped_column(JSONB, nullable=True)
   created_at: Mapped[datetime] = mapped_column(
      DateTime(timezone=True),
      default=datetime.utcnow
   )

   # Relationships
   app = relationship("App", back_populates="blueprints")

