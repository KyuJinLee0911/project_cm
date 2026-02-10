# BACKEND/core/settings_analysis.py
from __future__ import annotations

import os
from typing import Optional


def _get_int(name: str, default: Optional[int]) -> Optional[int]:
    v = os.getenv(name)
    if v is None or v == "":
        return default
    try:
        return int(v)
    except Exception:
        return default


class AnalysisSettings:
    # 1) 비디오 관련
    #    - DEFAULT_FPS: 강제 리샘플링 FPS (None이면 원본 유지)
    #    - MAX_VIDEO_DURATION_S: 허용 최대 길이(초)
    DEFAULT_FPS: Optional[int]
    MAX_VIDEO_DURATION_S: int

    # 2) 입력 제약
    MAX_POLYGONS: int
    MAX_POLYGON_POINTS: int

    def __init__(self) -> None:
        # 비디오
        self.DEFAULT_FPS = _get_int(
            "ANALYSIS_DEFAULT_FPS", None
        )  # 예: 30, 지정 없으면 원본 FPS 유지
        self.MAX_VIDEO_DURATION_S = _get_int("MAX_VIDEO_DURATION_S", 300)  # 기본 5분

        # 입력 제약
        self.MAX_POLYGONS = _get_int("MAX_POLYGONS", 25)
        self.MAX_POLYGON_POINTS = _get_int("MAX_POLYGON_POINTS", 64)


# 외부에서 import하여 사용
settings = AnalysisSettings()
