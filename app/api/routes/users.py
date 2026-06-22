import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserPasswordUpdate, UserResponse, UserStatusUpdate
from app.services.user_service import (
    UserError,
    create_user,
    list_users,
    set_user_active,
    set_user_password,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN.value)),
) -> User:
    try:
        user = create_user(db, payload.username, payload.password, payload.role, payload.label)
    except UserError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    db.commit()
    return user


@router.get("", response_model=list[UserResponse])
def list_all(
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN.value)),
) -> list[User]:
    return list_users(db)


@router.post("/{user_id}/status", response_model=UserResponse)
def set_status(
    user_id: uuid.UUID,
    payload: UserStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
) -> User:
    if user_id == current_user.id and not payload.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot deactivate your own account.")
    user = set_user_active(db, user_id, payload.is_active)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    db.commit()
    return user


@router.post("/{user_id}/password", response_model=UserResponse)
def reset_password(
    user_id: uuid.UUID,
    payload: UserPasswordUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN.value)),
) -> User:
    user = set_user_password(db, user_id, payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    db.commit()
    return user
