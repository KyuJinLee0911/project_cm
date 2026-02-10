# BACKEND/models/schemas.py
from __future__ import annotations
from typing import List, Tuple
from pydantic import BaseModel, validator
import numpy as np


class SessionCreateResp(BaseModel):
    session_id: str


class SessionGetResp(BaseModel):
    session_id: str
    image_width: int
    image_height: int
    status: str
    ttl_remain_sec: int


class DetectReq(BaseModel):
    x: float
    y: float

    @validator("x", "y")
    def non_nan(cls, v):
        if v is None or (isinstance(v, float) and np.isnan(v)):
            raise ValueError("좌표는 필수입니다.")
        return v


class DetectResp(BaseModel):
    polygon: List[Tuple[int, int]]
    bbox: List[float]
