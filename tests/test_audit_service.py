from app.models.audit_log import AuditEventType, AuditLog, AuditResult
from app.services import audit_service


def test_write_event_persists_row(db_session):
    entry = audit_service.write_event(
        db_session,
        event_type=AuditEventType.LOGIN,
        result=AuditResult.SUCCESS,
        detail={"note": "test"},
    )
    db_session.commit()

    fetched = db_session.get(AuditLog, entry.id)
    assert fetched is not None
    assert fetched.event_type == AuditEventType.LOGIN
    assert fetched.result == AuditResult.SUCCESS
    assert fetched.detail == {"note": "test"}
