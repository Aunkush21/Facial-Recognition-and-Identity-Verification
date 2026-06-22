import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.database import get_db
from app.models.audit_log import AuditEventType, AuditResult
from app.models.user import User, UserRole
from app.schemas.identity import EnrollResponse
from app.services import audit_service
from app.services.identity_service import (
    MultipleFacesDetected,
    NoFaceDetected,
    SpoofDetected,
    enroll_face_image,
    get_identity_by_id,
)
from app.utils.image import InvalidImage, decode_upload_to_bgr

router = APIRouter(prefix="/identities", tags=["enrollment"])


@router.post("/{identity_id}/enroll", response_model=EnrollResponse)
async def enroll(
    identity_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN.value, UserRole.OPERATOR.value)),
) -> EnrollResponse:
    identity = get_identity_by_id(db, identity_id)
    if identity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Identity not found")

    try:
        image = decode_upload_to_bgr(await file.read())
    except InvalidImage as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    try:
        embedding = enroll_face_image(db, identity, image)
    except (NoFaceDetected, MultipleFacesDetected, SpoofDetected) as exc:
        audit_service.write_event(
            db,
            event_type=AuditEventType.ENROLL,
            result=AuditResult.REJECTED,
            actor_user_id=current_user.id,
            identity_id=identity_id,
            detail={"reason": str(exc)},
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    audit_service.write_event(
        db,
        event_type=AuditEventType.ENROLL,
        result=AuditResult.SUCCESS,
        actor_user_id=current_user.id,
        identity_id=identity_id,
    )
    db.commit()
    return EnrollResponse(identity_id=identity_id, embedding_id=embedding.id, model_version=embedding.model_version)
