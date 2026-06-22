import uuid
from dataclasses import dataclass

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.audit_log import AuditEventType, AuditResult
from app.models.embedding import FaceEmbedding
from app.models.identity import Identity
from app.services import attendance_service, audit_service
from app.services.consensus import get_consensus_tracker
from app.services.face_engine import get_face_engine
from app.services.liveness import get_liveness_checker


@dataclass
class RecognitionResult:
    status: str  # no_face | spoof_rejected | unknown | verifying | present_recorded | already_present
    identity_id: uuid.UUID | None = None
    name: str | None = None
    similarity: float | None = None
    liveness_score: float | None = None
    consensus_count: int = 0


def _find_best_match(db: Session, embedding: np.ndarray) -> tuple[uuid.UUID | None, str | None, float]:
    distance_expr = FaceEmbedding.embedding.cosine_distance(embedding).label("distance")
    stmt = (
        select(Identity.id, Identity.full_name, distance_expr)
        .join(FaceEmbedding, FaceEmbedding.identity_id == Identity.id)
        .where(Identity.is_active.is_(True))
        .order_by(distance_expr)
        .limit(1)
    )
    row = db.execute(stmt).first()
    if row is None:
        return None, None, 0.0
    identity_id, name, distance = row
    similarity = 1.0 - distance  # vectors are L2-normalized, so cosine_distance = 1 - cosine_similarity
    return identity_id, name, float(similarity)


def process_frame(
    db: Session,
    session_id: str,
    bgr_image: np.ndarray,
    actor_user_id: uuid.UUID | None = None,
) -> list[RecognitionResult]:
    """Pipeline: detect -> liveness gate -> embed -> compare -> consensus -> attendance write.
    A face must pass liveness AND clear the similarity threshold on N consecutive/agreeing
    frames within the consensus window before attendance is ever written."""
    faces = get_face_engine().detect_and_embed(bgr_image)
    if not faces:
        return []

    liveness = get_liveness_checker()
    tracker = get_consensus_tracker()
    results: list[RecognitionResult] = []

    for face in faces:
        is_live, liveness_score = liveness.is_live(bgr_image, face.bbox)
        if not is_live:
            audit_service.write_event(
                db,
                event_type=AuditEventType.RECOGNIZE_REJECT_LIVENESS,
                result=AuditResult.REJECTED,
                actor_user_id=actor_user_id,
                confidence=liveness_score,
            )
            results.append(RecognitionResult(status="spoof_rejected", liveness_score=liveness_score))
            continue

        identity_id, name, similarity = _find_best_match(db, face.embedding)
        if identity_id is None or similarity < settings.recognition_threshold:
            audit_service.write_event(
                db,
                event_type=AuditEventType.RECOGNIZE_REJECT_THRESHOLD,
                result=AuditResult.REJECTED,
                actor_user_id=actor_user_id,
                identity_id=identity_id,
                confidence=similarity,
            )
            results.append(RecognitionResult(status="unknown", similarity=similarity, liveness_score=liveness_score))
            continue

        confirmed, count = tracker.record_match(session_id, identity_id, similarity)
        if not confirmed:
            results.append(
                RecognitionResult(
                    status="verifying",
                    identity_id=identity_id,
                    name=name,
                    similarity=similarity,
                    liveness_score=liveness_score,
                    consensus_count=count,
                )
            )
            continue

        created = attendance_service.record_present(db, identity_id, similarity)
        audit_service.write_event(
            db,
            event_type=AuditEventType.RECOGNIZE_SUCCESS,
            result=AuditResult.SUCCESS,
            actor_user_id=actor_user_id,
            identity_id=identity_id,
            confidence=similarity,
            detail={"attendance_created": created},
        )
        results.append(
            RecognitionResult(
                status="present_recorded" if created else "already_present",
                identity_id=identity_id,
                name=name,
                similarity=similarity,
                liveness_score=liveness_score,
                consensus_count=count,
            )
        )

    db.commit()
    return results
