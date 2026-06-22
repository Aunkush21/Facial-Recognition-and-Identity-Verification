import uuid
from datetime import date as date_, time as time_

from pydantic import BaseModel


class AttendanceRow(BaseModel):
    identity_id: uuid.UUID
    external_id: str
    full_name: str
    status: str
    time_recorded: time_ | None = None
    confidence: float | None = None


class AttendanceSummary(BaseModel):
    date: date_
    total: int
    present: int
    absent: int
    rows: list[AttendanceRow]
