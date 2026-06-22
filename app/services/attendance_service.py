import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.attendance import AttendanceRecord, AttendanceStatus


def record_present(db: Session, identity_id: uuid.UUID, confidence: float, when: datetime | None = None) -> bool:
    """Atomically records the first 'present' arrival for an identity on a given day.
    Returns True if this call created the row (first detection today), False if a
    present record already existed (subsequent detections same day are no-ops)."""
    when = when or datetime.now()
    stmt = (
        pg_insert(AttendanceRecord)
        .values(
            identity_id=identity_id,
            date=when.date(),
            time_recorded=when.time(),
            status=AttendanceStatus.PRESENT,
            confidence=confidence,
        )
        .on_conflict_do_nothing(index_elements=["identity_id", "date"])
    )
    result = db.execute(stmt)
    return result.rowcount > 0
