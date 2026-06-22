import uuid

from fastapi import Request
from sqlalchemy.orm import Session

from app.api.deps import COOKIE_NAME
from app.models.user import User
from app.services.auth_service import decode_access_token


def get_optional_user(request: Request, db: Session) -> User | None:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        return None
    user = db.get(User, uuid.UUID(payload["sub"]))
    if user is None or not user.is_active:
        return None
    return user
