import hashlib
import re
import uuid

import numpy as np
from sqlalchemy.orm import Session

from app.models.identity import EXTERNAL_ID_PATTERN, MAX_NAME_LENGTH, Identity
from app.models.embedding import FaceEmbedding
from app.services.face_engine import get_face_engine
from app.services.liveness import get_liveness_checker

_EXTERNAL_ID_RE = re.compile(EXTERNAL_ID_PATTERN)


class ValidationError(Exception):
    pass


class NoFaceDetected(Exception):
    pass


class MultipleFacesDetected(Exception):
    pass


class SpoofDetected(Exception):
    pass


def validate_external_id(external_id: str) -> None:
    if not _EXTERNAL_ID_RE.match(external_id or ""):
        raise ValidationError(
            "external_id must be 1-32 characters of letters, digits, '-' or '_' only."
        )


def validate_full_name(full_name: str) -> None:
    name = (full_name or "").strip()
    if not name:
        raise ValidationError("full_name is required.")
    if len(name) > MAX_NAME_LENGTH:
        raise ValidationError(f"full_name must be at most {MAX_NAME_LENGTH} characters.")


def create_identity(db: Session, external_id: str, full_name: str, extra_metadata: dict | None = None) -> Identity:
    validate_external_id(external_id)
    validate_full_name(full_name)

    existing = db.query(Identity).filter(Identity.external_id == external_id).first()
    if existing is not None:
        raise ValidationError(f"An identity with external_id '{external_id}' already exists.")

    identity = Identity(external_id=external_id, full_name=full_name.strip(), extra_metadata=extra_metadata)
    db.add(identity)
    db.flush()
    return identity


def enroll_face_image(db: Session, identity: Identity, bgr_image: np.ndarray) -> FaceEmbedding:
    """Detects exactly one live face in the enrollment image and stores its embedding.
    Rejects images with zero or multiple faces, and rejects spoofed enrollment photos
    (the same liveness gate used at recognition time)."""
    engine = get_face_engine()
    faces = engine.detect_and_embed(bgr_image)

    if not faces:
        raise NoFaceDetected("No face detected in the enrollment image.")
    if len(faces) > 1:
        raise MultipleFacesDetected("Multiple faces detected; enrollment requires exactly one face per image.")

    face = faces[0]
    is_live, live_score = get_liveness_checker().is_live(bgr_image, face.bbox)
    if not is_live:
        raise SpoofDetected(f"Enrollment image failed the liveness check (score {live_score:.2f}).")

    image_hash = hashlib.sha256(bgr_image.tobytes()).hexdigest()
    embedding_row = FaceEmbedding(
        identity_id=identity.id,
        embedding=face.embedding.tolist(),
        model_version=engine.model_version,
        source_image_hash=image_hash,
    )
    db.add(embedding_row)
    db.flush()
    return embedding_row


def get_identity_by_id(db: Session, identity_id: uuid.UUID) -> Identity | None:
    return db.get(Identity, identity_id)
