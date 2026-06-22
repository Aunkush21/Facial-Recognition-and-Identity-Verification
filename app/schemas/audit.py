import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_type: str
    result: str
    actor_user_id: uuid.UUID | None
    identity_id: uuid.UUID | None
    confidence: float | None
    detail: dict | None
    timestamp: datetime
