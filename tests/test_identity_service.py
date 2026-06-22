import pytest

from app.services.identity_service import (
    MultipleFacesDetected,
    NoFaceDetected,
    SpoofDetected,
    ValidationError,
    create_identity,
    enroll_face_image,
)
from tests.conftest import make_face, random_image


def test_create_identity_persists(db_session):
    identity = create_identity(db_session, "emp-001", "Jane Doe")
    db_session.commit()
    assert identity.id is not None
    assert identity.external_id == "emp-001"


def test_create_identity_rejects_duplicate_external_id(db_session):
    create_identity(db_session, "emp-002", "Jane Doe")
    db_session.commit()
    with pytest.raises(ValidationError):
        create_identity(db_session, "emp-002", "Someone Else")


def test_enroll_face_image_rejects_no_face(db_session, monkeypatch):
    identity = create_identity(db_session, "emp-003", "Jane Doe")
    db_session.commit()

    monkeypatch.setattr(
        "app.services.identity_service.get_face_engine",
        lambda: type("E", (), {"detect_and_embed": staticmethod(lambda img: [])})(),
    )

    with pytest.raises(NoFaceDetected):
        enroll_face_image(db_session, identity, random_image())


def test_enroll_face_image_rejects_multiple_faces(db_session, monkeypatch):
    identity = create_identity(db_session, "emp-004", "Jane Doe")
    db_session.commit()

    monkeypatch.setattr(
        "app.services.identity_service.get_face_engine",
        lambda: type("E", (), {"detect_and_embed": staticmethod(lambda img: [make_face(), make_face()])})(),
    )

    with pytest.raises(MultipleFacesDetected):
        enroll_face_image(db_session, identity, random_image())


def test_enroll_face_image_rejects_spoof(db_session, monkeypatch):
    identity = create_identity(db_session, "emp-005", "Jane Doe")
    db_session.commit()

    monkeypatch.setattr(
        "app.services.identity_service.get_face_engine",
        lambda: type("E", (), {
            "detect_and_embed": staticmethod(lambda img: [make_face()]),
            "model_version": "test",
        })(),
    )
    monkeypatch.setattr(
        "app.services.identity_service.get_liveness_checker",
        lambda: type("L", (), {"is_live": staticmethod(lambda img, bbox: (False, 0.1))})(),
    )

    with pytest.raises(SpoofDetected):
        enroll_face_image(db_session, identity, random_image())


def test_enroll_face_image_succeeds_for_live_single_face(db_session, monkeypatch):
    identity = create_identity(db_session, "emp-006", "Jane Doe")
    db_session.commit()
    face = make_face()

    monkeypatch.setattr(
        "app.services.identity_service.get_face_engine",
        lambda: type("E", (), {
            "detect_and_embed": staticmethod(lambda img: [face]),
            "model_version": "test-v1",
        })(),
    )
    monkeypatch.setattr(
        "app.services.identity_service.get_liveness_checker",
        lambda: type("L", (), {"is_live": staticmethod(lambda img, bbox: (True, 0.95))})(),
    )

    embedding_row = enroll_face_image(db_session, identity, random_image())
    db_session.commit()
    assert embedding_row.identity_id == identity.id
    assert embedding_row.model_version == "test-v1"
