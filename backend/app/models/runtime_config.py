import uuid
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class AppRuntimeConfig(Base):
   __tablename__ = "app_runtime_config"
   __table_args__ = {"schema": "control_plane"}

   app_id: Mapped[uuid.UUID] = mapped_column(
      UUID(as_uuid=True),
      ForeignKey("control_plane.apps.id"),
      primary_key=True
   )
   db_schema: Mapped[str] = mapped_column(String(100), nullable=False)
   public_base_path: Mapped[str] = mapped_column(String(255), nullable=False)
   enabled: Mapped[bool] = mapped_column(Boolean, default=False)

   # Relationships
   app = relationship("App", back_populates="runtime_config")

