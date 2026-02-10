# BACKEND/api/hold_routes.py
from __future__ import annotations
from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Body,
    Path,
    HTTPException,
    status as http,
)
from ..models.hold_schemas import (
    DetectResp,
    SessionCreateResp,
    SessionGetResp,
    DetectReq,
)
from ..services.session_service import SessionService
from ..services.detect_service import DetectService

router = APIRouter(
    prefix="/hold",
    tags=["hold"],
)


@router.post("/sessions", response_model=SessionCreateResp)
async def create_session(image: UploadFile = File(...)):
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=http.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="이미지 파일만 업로드 가능합니다.",
        )

    meta = await SessionService.create_from_upload(image)
    return SessionCreateResp(session_id=meta.session_id)


@router.post("/sessions/{session_id}/holds:detect", response_model=DetectResp)
async def detect_holds(session_id: str = Path(...), req: DetectReq = Body(...)):
    meta = SessionService.get_open(session_id)
    x = int(round(req.x))
    y = int(round(req.y))
    if not (0 <= x < meta.width and 0 <= y < meta.height):
        raise HTTPException(
            status_code=http.HTTP_400_BAD_REQUEST,
            detail="좌표가 이미지 범위를 벗어났습니다.",
        )
    meta.touch()
    # 이제 DetectReq 안의 model_alias / keywords 를 그대로 전달
    return DetectService.detect_candidates(meta, req)


@router.get("/sessions/{session_id}", response_model=SessionGetResp)
async def get_session(session_id: str = Path(...)):
    import time as _t

    meta = SessionService.get_open(session_id)
    ttl_remain = max(0, int(meta.expires_at - _t.time()))
    meta.touch()
    return SessionGetResp(
        session_id=meta.session_id,
        image_width=meta.width,
        image_height=meta.height,
        status=meta.status,
        ttl_remain_sec=ttl_remain,
    )


@router.post("/sessions/{session_id}:close")
async def close_session(session_id: str = Path(...)):
    SessionService.close(session_id)
    return {"ok": True}
