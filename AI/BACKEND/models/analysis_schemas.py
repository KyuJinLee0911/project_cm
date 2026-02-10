# BACKEND/models/analysis_schemas.py
from __future__ import annotations

from typing import List, Tuple, Optional, Literal
from pydantic import BaseModel, Field, HttpUrl, ConfigDict, field_validator


# -------------------------------------------------------------------
# 공통 베이스
# -------------------------------------------------------------------
class SafeModel(BaseModel):
    model_config = ConfigDict(protected_namespaces=())  # "model_*" 필드명 허용


# -------------------------------------------------------------------
# 입력 지오메트리/옵션
# -------------------------------------------------------------------
class HoldPolygon(SafeModel):
    """
    클라이언트가 제공하는 홀드 폴리곤.
    - id: "start", "top", 또는 자유로운 식별자
    - polygon: [(x, y), ...] 화면 픽셀 좌표(영상 해상도 기준), 3점 이상
    """

    type: Optional[Literal["start", "top", "common"]] = Field(default=None)
    polygon: List[Tuple[float, float]] = Field(
        ..., min_items=3, description="다각형 좌표 목록[(x,y)...], 3개 이상"
    )

    @field_validator("polygon")
    @classmethod
    def _validate_polygon(cls, v: List[Tuple[float, float]]):
        if len(v) < 3:
            raise ValueError("폴리곤은 최소 3개의 꼭짓점이 필요합니다.")
        for xy in v:
            if len(xy) != 2:
                raise ValueError("각 점은 (x, y) 튜플이어야 합니다.")
        return v


class AnalysisJobCreate(SafeModel):
    """잡 생성 요청 페이로드."""

    video_url: HttpUrl = Field(..., description="분석 대상 동영상 URL (http/https)")
    holds: List[dict] = Field(
        ..., min_items=1, description="분석에 사용할 홀드 폴리곤 배열"
    )


# -------------------------------------------------------------------
# 잡/상태/산출물
# -------------------------------------------------------------------
JobStatusLiteral = Literal[
    "queued",
    "downloading",
    "skeletonizing",
    "analyzing",
    "succeeded",
    "failed",
    "canceled",
]


class Artifacts(SafeModel):
    """산출물 경로/URL."""

    input_video_path: Optional[str] = None


class AnalysisJobStatus(SafeModel):
    """잡 상태 조회 응답."""

    job_id: str
    message: Optional[str] = None


# -------------------------------------------------------------------
# 결과 스키마
# -------------------------------------------------------------------
class Point2D(SafeModel):
    x: float
    y: float


class BBoxXYWH(SafeModel):
    """바운딩 박스 (x, y, w, h) — (x, y)는 좌상단."""

    x: float
    y: float
    w: float = Field(..., gt=0)
    h: float = Field(..., gt=0)


class TriQuadPolygon(SafeModel):
    points: List[Point2D] = Field(..., min_items=3, max_items=4)

    @field_validator("points")
    @classmethod
    def _validate_tri_quad(cls, v: List[Point2D]):
        if len(v) not in (3, 4):
            raise ValueError("points는 3개 또는 4개의 점이어야 합니다.")
        return v


class Skeleton2D(SafeModel):
    points: List[Point2D] = Field(default_factory=list)


class FrameMetrics(SafeModel):
    tilt_pct: float = Field(..., ge=0, le=100)  # 기울기
    flexion_pct: float  # 관절
    com_pct: float = Field(..., ge=0, le=100)  # 무게중심 차이
    avg_pct: float = Field(..., ge=0, le=100)  # 전체점수
    stability: str

    @field_validator("stability")
    @classmethod
    def _derive_stability(cls, v, info):
        if v in ("stable", "unstable"):
            return v
        avg = info.data.get("avg_pct")
        if avg is None:
            raise ValueError("stability를 생략하려면 avg_pct가 필요합니다.")
        return "stable" if avg >= 70.0 else "unstable"


class FrameAnalysis(SafeModel):
    frame_idx: int = Field(..., ge=0, description="프레임 index")
    skeleton: List[Tuple[float, float]]
    tri_quad: List
    body_center: Tuple[float, float]
    tri_quad_center: Optional[Tuple[float, float]]
    metrics: FrameMetrics
    start_climbing_frame: int
    end_climbing_frame: int


# -------------------------- 요약/이벤트 -------------------------


class DropAnalysis(SafeModel):
    t_drop: int = Field(..., ge=0, description="낙하 시작 프레임 index")
    t_touch: int = Field(..., ge=0, description="최초 접촉 프레임 index")
    message: Optional[str] = None  # 피드백 메시지
    landing_sequence: List[str] = None  # 착지 순서


# -------------------------- 최종 결과 --------------------------
class AnalysisJobResult(SafeModel):
    job_id: str  # 분석 세션 id
    status: str  # 분석 정상 완료 여부
    frames: List[FrameAnalysis] = Field(
        default_factory=list, description="프레임별 분석 시계열"
    )
    drop: Optional[DropAnalysis] = None
    average_score: float  # 영상 전체 점수
