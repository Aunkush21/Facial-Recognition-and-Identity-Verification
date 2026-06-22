from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.recognition import RecognitionFrameResponse, RecognitionResponse
from app.services.recognition import process_frame
from app.utils.image import InvalidImage, decode_upload_to_bgr

router = APIRouter(prefix="/recognize", tags=["recognition"])


@router.post("", response_model=RecognitionResponse)
async def recognize(
    session_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN.value, UserRole.OPERATOR.value)),
) -> RecognitionResponse:
    try:
        image = decode_upload_to_bgr(await file.read())
    except InvalidImage as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    results = process_frame(db, session_id, image, actor_user_id=current_user.id)
    return RecognitionResponse(
        results=[
            RecognitionFrameResponse(
                status=r.status,
                identity_id=r.identity_id,
                name=r.name,
                similarity=r.similarity,
                liveness_score=r.liveness_score,
                consensus_count=r.consensus_count,
            )
            for r in results
        ]
    )
