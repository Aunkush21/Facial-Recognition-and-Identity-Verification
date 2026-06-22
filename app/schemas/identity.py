import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IdentityCreate(BaseModel):
    external_id: str
    full_name: str
    extra_metadata: dict | None = None


class IdentityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    external_id: str
    full_name: str
    is_active: bool
    created_at: datetime


class EnrollResponse(BaseModel):
    identity_id: uuid.UUID
    embedding_id: uuid.UUID
    model_version: str
