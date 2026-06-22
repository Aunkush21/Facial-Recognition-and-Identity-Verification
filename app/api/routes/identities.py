import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.database import get_db
from app.models.audit_log import AuditEventType, AuditResult
from app.models.identity import Identity
from app.models.user import User, UserRole
from app.schemas.identity import IdentityCreate, IdentityResponse
from app.services import audit_service
from app.services.identity_service import ValidationError, create_identity, get_identity_by_id

router = APIRouter(prefix="/identities", tags=["identities"])


@router.post("", response_model=IdentityResponse, status_code=status.HTTP_201_CREATED)
def create(
    payload: IdentityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
) -> Identity:
    try:
        identity = create_identity(db, payload.external_id, payload.full_name, payload.extra_metadata)
    except ValidationError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    audit_service.write_event(
        db,
        event_type=AuditEventType.REGISTER,
        result=AuditResult.SUCCESS,
        actor_user_id=current_user.id,
        identity_id=identity.id,
        detail={"external_id": identity.external_id},
    )
    db.commit()
    return identity


@router.get("", response_model=list[IdentityResponse])
def list_identities(
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN.value, UserRole.OPERATOR.value)),
) -> list[Identity]:
    return db.query(Identity).order_by(Identity.created_at.desc()).all()


@router.get("/{identity_id}", response_model=IdentityResponse)
def get_identity(
    identity_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN.value, UserRole.OPERATOR.value)),
) -> Identity:
    identity = get_identity_by_id(db, identity_id)
    if identity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Identity not found")
    return identity
