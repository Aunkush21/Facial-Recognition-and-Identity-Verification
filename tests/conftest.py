import os
import uuid

import numpy as np
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.services.face_engine import DetectedFace

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/facial_recognition_test",
)


@pytest.fixture(scope="session")
def _engine():
    engine = create_engine(TEST_DATABASE_URL)
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
            conn.commit()
    except Exception as exc:  # noqa: BLE001 - any connection failure means "no DB available"
        pytest.skip(f"No test database available at {TEST_DATABASE_URL}: {exc}")
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(_engine):
    Base.metadata.create_all(_engine)
    SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        Base.metadata.drop_all(_engine)


def make_face(embedding: np.ndarray | None = None, bbox=(10, 10, 100, 100), det_score=0.99) -> DetectedFace:
    if embedding is None:
        rng = np.random.default_rng(0)
        embedding = rng.normal(size=512).astype(np.float32)
        embedding /= np.linalg.norm(embedding)
    return DetectedFace(bbox=bbox, embedding=embedding, det_score=det_score)


def random_image() -> np.ndarray:
    return np.zeros((120, 120, 3), dtype=np.uint8)


@pytest.fixture
def session_id() -> str:
    return str(uuid.uuid4())
