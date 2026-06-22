import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.attendance import AttendanceRecord
    from app.models.embedding import FaceEmbedding

# Strict allowlist: never accept characters that could be abused if this value
# were ever interpolated into a path, shell command, or query — only loose
# alphanumerics, dash, and underscore, capped to a sane length.
EXTERNAL_ID_PATTERN = r"^[A-Za-z0-9_-]{1,32}$"
MAX_NAME_LENGTH = 128


class Identity(Base):
    __tablename__ = "identities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    external_id: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(MAX_NAME_LENGTH), nullable=False)
    extra_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    embeddings: Mapped[list["FaceEmbedding"]] = relationship(
        back_populates="identity", cascade="all, delete-orphan"
    )
    attendance_records: Mapped[list["AttendanceRecord"]] = relationship(
        back_populates="identity", cascade="all, delete-orphan"
    )
