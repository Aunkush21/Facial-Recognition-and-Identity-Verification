import uuid

from sqlalchemy.orm import Session

from app.models.audit_log import AuditEventType, AuditLog, AuditResult


def write_event(
    db: Session,
    *,
    event_type: AuditEventType,
    result: AuditResult,
    actor_user_id: uuid.UUID | None = None,
    identity_id: uuid.UUID | None = None,
    confidence: float | None = None,
    detail: dict | None = None,
) -> AuditLog:
    """Single write path for the audit trail — every service that performs a
    security-relevant action (auth, enroll, recognize, attendance) calls this."""
    entry = AuditLog(
        event_type=event_type,
        result=result,
        actor_user_id=actor_user_id,
        identity_id=identity_id,
        confidence=confidence,
        detail=detail,
    )
    db.add(entry)
    db.flush()
    return entry
