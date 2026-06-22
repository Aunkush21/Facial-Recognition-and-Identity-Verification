from datetime import datetime

from app.services.attendance_service import record_present
from app.services.identity_service import create_identity


def test_record_present_creates_row_once(db_session):
    identity = create_identity(db_session, "emp-100", "Jane Doe")
    db_session.commit()

    when = datetime(2026, 1, 5, 9, 0, 0)
    created_first = record_present(db_session, identity.id, 0.9, when=when)
    db_session.commit()
    assert created_first is True

    created_second = record_present(db_session, identity.id, 0.95, when=datetime(2026, 1, 5, 9, 5, 0))
    db_session.commit()
    assert created_second is False
