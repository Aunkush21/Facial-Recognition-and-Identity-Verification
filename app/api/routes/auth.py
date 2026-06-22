from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import COOKIE_NAME, get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.audit_log import AuditEventType, AuditResult
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.services import audit_service
from app.services.auth_service import authenticate_user, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> TokenResponse:
    user = authenticate_user(db, payload.username, payload.password)
    if user is None:
        audit_service.write_event(
            db,
            event_type=AuditEventType.LOGIN_FAILED,
            result=AuditResult.FAILURE,
            detail={"username": payload.username},
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    token = create_access_token(user.id, user.role.value)
    audit_service.write_event(
        db,
        event_type=AuditEventType.LOGIN,
        result=AuditResult.SUCCESS,
        actor_user_id=user.id,
    )
    db.commit()

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="strict",
        max_age=settings.access_token_expire_minutes * 60,
    )
    return TokenResponse(access_token=token, role=user.role.value)


@router.post("/logout")
def logout(response: Response, _: User = Depends(get_current_user)) -> dict:
    response.delete_cookie(COOKIE_NAME)
    return {"detail": "logged out"}
