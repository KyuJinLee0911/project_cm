# BACKEND/services/session_service.py
from __future__ import annotations
import uuid, time

import cv2
from fastapi import HTTPException, status as http, UploadFile
from ..core.config import settings
from ..repositories.session_store import STORE, SessionMeta
from ..utils.image import ensure_cv2
import numpy as np


class SessionService:
    @staticmethod
    async def create_from_upload(upload_file: UploadFile) -> SessionMeta:
        data = await upload_file.read()

        max_size = getattr(settings, "MAX_IMAGE_BYTES", 10 * 1024 * 1024)
        if len(data) > max_size:
            raise HTTPException(
                status_code=http.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="이미지 용량 제한을 초과했습니다.",
            )

        ensure_cv2()
        arr = np.frombuffer(data, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(
                status_code=http.HTTP_400_BAD_REQUEST,
                detail="유효한 이미지 형식이 아닙니다.",
            )

        h, w = img.shape[:2]
        now = time.time()

        meta = SessionMeta(
            session_id=uuid.uuid4().hex,
            width=w,
            height=h,
            created_at=now,
            expires_at=now + settings.SESS_TTL_SEC,
            image_np=img,
        )
        STORE.create(meta)
        return meta

    @staticmethod
    def get_open(sid: str) -> SessionMeta:
        try:
            meta = STORE.get_open(sid)
        except KeyError:
            raise HTTPException(
                status_code=http.HTTP_404_NOT_FOUND, detail="세션이 존재하지 않습니다."
            )
        except RuntimeError:
            raise HTTPException(
                status_code=http.HTTP_409_CONFLICT, detail="세션이 종료되었습니다."
            )
        except TimeoutError:
            raise HTTPException(
                status_code=http.HTTP_409_CONFLICT, detail="세션이 만료되었습니다."
            )
        return meta

    @staticmethod
    def close(sid: str):
        try:
            STORE.close(sid)
        except KeyError:
            raise HTTPException(
                status_code=http.HTTP_404_NOT_FOUND, detail="세션이 존재하지 않습니다."
            )
