# BACKEND/api/analysis_routes.py
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Path, Response

from ..models.analysis_schemas import (
    AnalysisJobCreate,
    AnalysisJobStatus,
    AnalysisJobResult,
)
from ..services.job_service import JobService

from ..repositories.job_store import JobNotFoundError


router = APIRouter(
    prefix="/analysis",
    tags=["analysis"],
)

# 진행 중 상태 집합
PROCESSING = {"queued", "downloading", "skeletonizing", "analyzing"}


@router.post(
    "/jobs",
    response_model=AnalysisJobStatus,
    status_code=202,
    summary="분석 잡 생성 및 시작",
    description=(
        "video_url과 holds(폴리곤)를 입력받아 분석 잡을 큐에 등록하고 즉시 job_id를 반환합니다. "
        "실제 처리(다운로드→스켈레톤 생성→낙법 분석)는 백그라운드에서 비동기로 진행됩니다."
    ),
)
async def create_job(payload: AnalysisJobCreate) -> AnalysisJobStatus:
    return JobService.create_and_start(payload)


@router.get(
    "/jobs/{job_id}",
    response_model=AnalysisJobStatus,
    summary="잡 상태/진척도 조회",
    description="현재 잡의 상태(status), 진행률(progress), 중간 산출물 경로(있으면)를 반환합니다.",
)
async def get_job_status(
    job_id: str = Path(..., description="생성 시 반환된 job_id"),
) -> AnalysisJobStatus:
    try:
        return JobService.get_status(job_id)
    except JobNotFoundError:
        raise HTTPException(status_code=404, detail="job_id를 찾을 수 없습니다.")


@router.get(
    "/jobs/{job_id}/result",
    response_model=AnalysisJobResult,
    summary="완료된 분석 결과 조회",
    description=(
        "잡이 완료(succeeded)된 경우 최종 분석 결과를 반환합니다. "
        "진행 중이면 409(Conflict), 실패면 422, 취소면 410을 반환합니다."
    ),
    responses={
        409: {"description": "처리 중"},
        410: {"description": "취소됨"},
        422: {"description": "실패(예: 다운로드 오류)"},
        404: {"description": "job_id 없음"},
    },
)
async def get_job_result(
    response: Response,
    job_id: str = Path(..., description="생성 시 반환된 job_id"),
) -> AnalysisJobResult:
    try:
        st = JobService.get_now_status(job_id)
    except JobNotFoundError:
        raise HTTPException(status_code=404, detail="job_id를 찾을 수 없습니다.")

    status = st

    if status == "succeeded":
        result = JobService.get_result(job_id)
        if result is None:
            raise HTTPException(
                status_code=409, detail="아직 결과가 준비되지 않았습니다."
            )
        return result

    if status in {"queued", "downloading", "skeletonizing", "analyzing"}:
        response.headers["Retry-After"] = "3"
        raise HTTPException(status_code=409, detail=st.message or "처리 중입니다.")

    if status == "failed":
        raise HTTPException(
            status_code=422, detail=st.message or "작업이 실패했습니다."
        )

    if status == "canceled":
        raise HTTPException(
            status_code=410, detail=st.message or "작업이 취소되었습니다."
        )

    raise HTTPException(status_code=500, detail=f"알 수 없는 상태: {status}")
