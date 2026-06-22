import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditEventType(str, enum.Enum):
    REGISTER = "register"
    ENROLL = "train_enroll"
    RECOGNIZE_ATTEMPT = "recognize_attempt"
    RECOGNIZE_SUCCESS = "recognize_success"
    RECOGNIZE_REJECT_LIVENESS = "recognize_reject_liveness"
    RECOGNIZE_REJECT_THRESHOLD = "recognize_reject_threshold"
    LOGIN = "login"
    LOGIN_FAILED = "login_failed"
    ATTENDANCE_WRITE = "attendance_write"


class AuditResult(str, enum.Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    REJECTED = "rejected"


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    event_type: Mapped[AuditEventType] = mapped_column(
        Enum(AuditEventType, name="audit_event_type", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    identity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("identities.id", ondelete="SET NULL"), nullable=True
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    result: Mapped[AuditResult] = mapped_column(
        Enum(AuditResult, name="audit_result", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    detail: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), index=True
    )
