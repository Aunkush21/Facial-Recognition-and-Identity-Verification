import uuid

from app.services.consensus import ConsensusTracker


def test_confirms_after_required_frames():
    tracker = ConsensusTracker(frames_required=3, window_seconds=10)
    identity_id = uuid.uuid4()
    session_id = "session-a"

    confirmed, count = tracker.record_match(session_id, identity_id, 0.8)
    assert not confirmed and count == 1
    confirmed, count = tracker.record_match(session_id, identity_id, 0.8)
    assert not confirmed and count == 2
    confirmed, count = tracker.record_match(session_id, identity_id, 0.8)
    assert confirmed and count == 3


def test_different_identities_do_not_share_consensus():
    tracker = ConsensusTracker(frames_required=2, window_seconds=10)
    session_id = "session-b"
    id_a, id_b = uuid.uuid4(), uuid.uuid4()

    tracker.record_match(session_id, id_a, 0.8)
    confirmed, count = tracker.record_match(session_id, id_b, 0.8)
    assert not confirmed
    assert count == 1


def test_window_expiry_resets_old_matches():
    tracker = ConsensusTracker(frames_required=2, window_seconds=0.05)
    session_id = "session-c"
    identity_id = uuid.uuid4()

    tracker.record_match(session_id, identity_id, 0.8)
    import time

    time.sleep(0.1)
    confirmed, count = tracker.record_match(session_id, identity_id, 0.8)
    assert not confirmed
    assert count == 1


def test_reset_session_clears_state():
    tracker = ConsensusTracker(frames_required=1, window_seconds=10)
    session_id = "session-d"
    identity_id = uuid.uuid4()

    tracker.record_match(session_id, identity_id, 0.8)
    tracker.reset_session(session_id)
    confirmed, count = tracker.record_match(session_id, identity_id, 0.8)
    assert confirmed and count == 1


def test_sessions_are_independent():
    tracker = ConsensusTracker(frames_required=2, window_seconds=10)
    identity_id = uuid.uuid4()

    tracker.record_match("session-x", identity_id, 0.8)
    confirmed, count = tracker.record_match("session-y", identity_id, 0.8)
    assert not confirmed
    assert count == 1
