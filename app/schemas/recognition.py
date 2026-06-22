import uuid

from pydantic import BaseModel


class RecognitionFrameResponse(BaseModel):
    status: str
    identity_id: uuid.UUID | None = None
    name: str | None = None
    similarity: float | None = None
    liveness_score: float | None = None
    consensus_count: int = 0


class RecognitionResponse(BaseModel):
    results: list[RecognitionFrameResponse]
