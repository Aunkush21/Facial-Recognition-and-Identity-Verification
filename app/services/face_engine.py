from dataclasses import dataclass
from pathlib import Path

import numpy as np
from insightface.app import FaceAnalysis

from app.core.config import settings

MODELS_ROOT = Path(__file__).resolve().parent.parent / "models_data" / "insightface"
EMBEDDING_DIM = 512


@dataclass
class DetectedFace:
    bbox: tuple[int, int, int, int]  # x1, y1, x2, y2
    embedding: np.ndarray  # L2-normalized, shape (512,)
    det_score: float


class FaceEngine:
    """Wraps InsightFace's RetinaFace detector + ArcFace embedder (CPU-only)."""

    def __init__(self, model_pack: str | None = None, det_size: tuple[int, int] = (640, 640)):
        self._app = FaceAnalysis(
            name=model_pack or settings.face_model_pack,
            root=str(MODELS_ROOT),
            providers=["CPUExecutionProvider"],
        )
        self._app.prepare(ctx_id=-1, det_size=det_size)
        self.model_version = f"insightface-{model_pack or settings.face_model_pack}"

    def detect_and_embed(self, bgr_image: np.ndarray) -> list[DetectedFace]:
        faces = self._app.get(bgr_image)
        results = []
        for face in faces:
            embedding = face.embedding.astype(np.float32)
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            x1, y1, x2, y2 = face.bbox.astype(int)
            results.append(DetectedFace(bbox=(x1, y1, x2, y2), embedding=embedding, det_score=float(face.det_score)))
        return results


_engine: FaceEngine | None = None


def get_face_engine() -> FaceEngine:
    global _engine
    if _engine is None:
        _engine = FaceEngine()
    return _engine
