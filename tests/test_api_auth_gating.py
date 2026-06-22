import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app
from app.models.user import User, UserRole
from app.services.auth_service import hash_password


@pytest.fixture
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _create_user(db_session, username, role):
    user = User(username=username, hashed_password=hash_password("password123"), role=role)
    db_session.add(user)
    db_session.commit()
    return user


def test_login_rejects_unknown_user(client):
    res = client.post("/auth/login", json={"username": "nobody", "password": "x"})
    assert res.status_code == 401


def test_login_succeeds_and_sets_cookie(client, db_session):
    _create_user(db_session, "admin1", UserRole.ADMIN)
    res = client.post("/auth/login", json={"username": "admin1", "password": "password123"})
    assert res.status_code == 200
    assert "access_token" in res.cookies


def test_operator_cannot_create_identity(client, db_session):
    _create_user(db_session, "operator1", UserRole.OPERATOR)
    client.post("/auth/login", json={"username": "operator1", "password": "password123"})
    res = client.post("/identities", json={"external_id": "emp-1", "full_name": "Jane"})
    assert res.status_code == 403


def test_admin_can_create_identity(client, db_session):
    _create_user(db_session, "admin2", UserRole.ADMIN)
    client.post("/auth/login", json={"username": "admin2", "password": "password123"})
    res = client.post("/identities", json={"external_id": "emp-2", "full_name": "Jane"})
    assert res.status_code == 201


def test_creating_identity_writes_register_audit_event(client, db_session):
    from app.models.audit_log import AuditEventType, AuditLog, AuditResult

    admin = _create_user(db_session, "admin3", UserRole.ADMIN)
    client.post("/auth/login", json={"username": "admin3", "password": "password123"})
    res = client.post("/identities", json={"external_id": "emp-3", "full_name": "Jane"})
    assert res.status_code == 201
    identity_id = res.json()["id"]

    event = (
        db_session.query(AuditLog)
        .filter(AuditLog.event_type == AuditEventType.REGISTER)
        .one()
    )
    assert event.result == AuditResult.SUCCESS
    assert str(event.actor_user_id) == str(admin.id)
    assert str(event.identity_id) == identity_id


def test_unauthenticated_request_rejected(client):
    res = client.get("/attendance")
    assert res.status_code == 401


def test_operator_cannot_view_audit_log(client, db_session):
    _create_user(db_session, "operator2", UserRole.OPERATOR)
    client.post("/auth/login", json={"username": "operator2", "password": "password123"})
    res = client.get("/audit-log")
    assert res.status_code == 403


def test_operator_cannot_create_users(client, db_session):
    _create_user(db_session, "operator4", UserRole.OPERATOR)
    client.post("/auth/login", json={"username": "operator4", "password": "password123"})
    res = client.post("/users", json={"username": "newop", "password": "password123", "role": "operator"})
    assert res.status_code == 403


def test_admin_creates_operator_who_can_log_in(client, db_session):
    _create_user(db_session, "admin5", UserRole.ADMIN)
    client.post("/auth/login", json={"username": "admin5", "password": "password123"})

    res = client.post(
        "/users",
        json={"username": "phy_teacher", "password": "physics123", "role": "operator", "label": "Physics"},
    )
    assert res.status_code == 201
    assert res.json()["label"] == "Physics"

    # the new operator can authenticate with their own credentials
    res = client.post("/auth/login", json={"username": "phy_teacher", "password": "physics123"})
    assert res.status_code == 200


def test_admin_cannot_deactivate_self(client, db_session):
    admin = _create_user(db_session, "admin6", UserRole.ADMIN)
    client.post("/auth/login", json={"username": "admin6", "password": "password123"})
    res = client.post(f"/users/{admin.id}/status", json={"is_active": False})
    assert res.status_code == 400


def test_admin_can_reset_operator_password(client, db_session):
    _create_user(db_session, "admin7", UserRole.ADMIN)
    target = _create_user(db_session, "forgetful_op", UserRole.OPERATOR)
    client.post("/auth/login", json={"username": "admin7", "password": "password123"})

    res = client.post(f"/users/{target.id}/password", json={"password": "brand-new-pass"})
    assert res.status_code == 200

    # old password no longer works, new one does
    assert client.post("/auth/login", json={"username": "forgetful_op", "password": "password123"}).status_code == 401
    assert client.post("/auth/login", json={"username": "forgetful_op", "password": "brand-new-pass"}).status_code == 200


def test_operator_cannot_reset_passwords(client, db_session):
    _create_user(db_session, "operator5", UserRole.OPERATOR)
    victim = _create_user(db_session, "victim", UserRole.OPERATOR)
    client.post("/auth/login", json={"username": "operator5", "password": "password123"})
    res = client.post(f"/users/{victim.id}/password", json={"password": "hijacked1"})
    assert res.status_code == 403
