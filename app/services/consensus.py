import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from threading import Lock

from app.core.config import settings


@dataclass
class _SessionState:
    matches: deque[tuple[float, uuid.UUID, float]] = field(default_factory=deque)  # (ts, identity_id, similarity)


class ConsensusTracker:
    """Requires N agreeing matches for the same identity within a sliding time window
    before a recognition is considered confirmed (mitigates single-frame false positives)."""

    def __init__(self, frames_required: int | None = None, window_seconds: float | None = None):
        self.frames_required = frames_required or settings.consensus_frames_required
        self.window_seconds = window_seconds or settings.consensus_window_seconds
        self._sessions: dict[str, _SessionState] = {}
        self._lock = Lock()

    def record_match(self, session_id: str, identity_id: uuid.UUID, similarity: float) -> tuple[bool, int]:
        """Returns (confirmed, current_count_for_this_identity)."""
        now = time.monotonic()
        with self._lock:
            state = self._sessions.setdefault(session_id, _SessionState())
            state.matches.append((now, identity_id, similarity))

            cutoff = now - self.window_seconds
            while state.matches and state.matches[0][0] < cutoff:
                state.matches.popleft()

            count = sum(1 for _, ident, _ in state.matches if ident == identity_id)
            confirmed = count >= self.frames_required
            return confirmed, count

    def reset_session(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)


_tracker: ConsensusTracker | None = None


def get_consensus_tracker() -> ConsensusTracker:
    global _tracker
    if _tracker is None:
        _tracker = ConsensusTracker()
    return _tracker
