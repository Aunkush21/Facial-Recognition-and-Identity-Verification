import numpy as np

from app.models.embedding import FaceEmbedding
from app.services.consensus import ConsensusTracker
from app.services.identity_service import create_identity
from app.services.recognition import process_frame
from tests.conftest import make_face, random_image


def _patch_engine(monkeypatch, faces):
    monkeypatch.setattr(
        "app.services.recognition.get_face_engine",
        lambda: type("E", (), {"detect_and_embed": staticmethod(lambda img: faces)})(),
    )


def _patch_liveness(monkeypatch, is_live: bool, score: float):
    monkeypatch.setattr(
        "app.services.recognition.get_liveness_checker",
        lambda: type("L", (), {"is_live": staticmethod(lambda img, bbox: (is_live, score))})(),
    )


def _patch_tracker(monkeypatch, frames_required=2, window_seconds=10):
    tracker = ConsensusTracker(frames_required=frames_required, window_seconds=window_seconds)
    monkeypatch.setattr("app.services.recognition.get_consensus_tracker", lambda: tracker)
    return tracker


def test_spoofed_frame_is_rejected_before_matching(db_session, monkeypatch, session_id):
    face = make_face()
    _patch_engine(monkeypatch, [face])
    _patch_liveness(monkeypatch, is_live=False, score=0.1)
    _patch_tracker(monkeypatch)

    results = process_frame(db_session, session_id, random_image())
    assert len(results) == 1
    assert results[0].status == "spoof_rejected"
    assert results[0].liveness_score == 0.1


def test_unrecognized_face_is_rejected_below_threshold(db_session, monkeypatch, session_id):
    face = make_face()
    _patch_engine(monkeypatch, [face])
    _patch_liveness(monkeypatch, is_live=True, score=0.95)
    _patch_tracker(monkeypatch)

    results = process_frame(db_session, session_id, random_image())
    assert len(results) == 1
    assert results[0].status == "unknown"


def test_consensus_gating_then_attendance_write(db_session, monkeypatch, session_id):
    embedding = np.random.default_rng(1).normal(size=512).astype(np.float32)
    embedding /= np.linalg.norm(embedding)
    face = make_face(embedding=embedding)

    identity = create_identity(db_session, "emp-200", "Jane Doe")
    db_session.add(
        FaceEmbedding(identity_id=identity.id, embedding=embedding.tolist(), model_version="test", source_image_hash="x")
    )
    db_session.commit()

    _patch_engine(monkeypatch, [face])
    _patch_liveness(monkeypatch, is_live=True, score=0.95)
    _patch_tracker(monkeypatch, frames_required=3, window_seconds=10)

    first = process_frame(db_session, session_id, random_image())[0]
    assert first.status == "verifying"
    assert first.consensus_count == 1

    second = process_frame(db_session, session_id, random_image())[0]
    assert second.status == "verifying"
    assert second.consensus_count == 2

    third = process_frame(db_session, session_id, random_image())[0]
    assert third.status == "present_recorded"
    assert third.identity_id == identity.id

    fourth = process_frame(db_session, session_id, random_image())[0]
    assert fourth.status == "already_present"


def test_no_face_returns_empty_results(db_session, monkeypatch, session_id):
    _patch_engine(monkeypatch, [])
    results = process_frame(db_session, session_id, random_image())
    assert results == []
