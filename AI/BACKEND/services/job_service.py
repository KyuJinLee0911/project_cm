# BACKEND/services/job_service.py
from __future__ import annotations

import threading
from typing import Optional

from ..models.analysis_schemas import (
    AnalysisJobCreate,
    AnalysisJobStatus,
    AnalysisJobResult,
)
from ..repositories.job_store import STORE, JobNotFoundError
from ..repositories.artifact_store import ARTIFACTS

from ..core.pipeline import run_job_pipeline


class JobService:
    """
    잡 생성/시작, 상태/결과 조회를 위한 서비스 계층.
    - create_and_start(payload): 잡 생성 후 백그라운드 스레드에서 파이프라인 시작
    - get_status(job_id): 현재 잡 상태 조회
    - get_result(job_id): 완료된 결과 조회(없으면 None)
    """

    @staticmethod
    def create_and_start(payload: AnalysisJobCreate) -> AnalysisJobStatus:
        """
        1) 잡을 생성(queued)하고,
        2) 잡 디렉터리 레이아웃을 보장한 뒤,
        3) 백그라운드 스레드에서 파이프라인을 시작합니다.
        """
        # 1) 인메모리 스토어에 잡 생성
        status = STORE.create(payload)
        job_id = status.job_id

        # 2) 아티팩트 디렉터리 보장
        ARTIFACTS.ensure_layout(job_id)

        # 3) 백그라운드 스레드로 파이프라인 실행
        t = threading.Thread(
            target=JobService._run_pipeline_safe,
            args=(job_id,),
            daemon=True,
            name=f"pipeline-{job_id[:8]}",
        )
        t.start()

        return status

    @staticmethod
    def get_status(job_id: str) -> AnalysisJobStatus:
        return STORE.get_status(job_id)

    @staticmethod
    def get_now_status(job_id: str):
        return STORE.get_now_status(job_id)

    @staticmethod
    def get_result(job_id: str) -> Optional[AnalysisJobResult]:
        return STORE.get_result(job_id)

    # -----------------------------
    # 내부: 워커 스레드 안전 실행 래퍼
    # -----------------------------
    @staticmethod
    def _run_pipeline_safe(job_id: str) -> None:
        """
        파이프라인 실제 실행. 예외가 나더라도 스토어에 실패 상태를 반영합니다.
        """
        try:
            run_job_pipeline(job_id)
        except JobNotFoundError:
            # 생성 직후 삭제된 극히 예외적인 상황
            STORE.set_error(job_id, "job not found")
        except Exception as e:
            STORE.set_error(job_id, f"pipeline error: {e}")
