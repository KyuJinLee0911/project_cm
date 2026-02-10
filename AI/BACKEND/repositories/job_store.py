# BACKEND/repositories/job_store.py
from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable

from ..models.analysis_schemas import (
    AnalysisJobCreate,
    AnalysisJobStatus,
    AnalysisJobResult,
    Artifacts,
    DropAnalysis,
    FrameAnalysis,
)


# -----------------------------
# 예외 정의
# -----------------------------
class JobNotFoundError(Exception):
    pass


# -----------------------------
# 내부 저장 레코드
# -----------------------------
@dataclass
class JobRecord:
    job_id: str
    # 입력 원본(워커 단계에서 사용)
    video_url: str
    holds: List[Dict]  # HoldPolygon.model_dump() 형태 저장
    options: Dict[str, Any] = field(default_factory=dict)

    # 진행/상태
    status: str = (
        "queued"  # queued|downloading|skeletonizing|analyzing|succeeded|failed|canceled
    )
    progress: int = 0  # 0~100
    message: Optional[str] = None

    # 산출물
    artifacts: Artifacts = field(default_factory=Artifacts)

    # 타임스탬프
    created_at: float = field(default_factory=lambda: time.time())
    updated_at: float = field(default_factory=lambda: time.time())

    # 최종 결과 (완료 시 세팅)
    result: Optional[AnalysisJobResult] = None

    # 유틸
    def touch(self):
        self.updated_at = time.time()


# -----------------------------
# 인메모리 Job Store (스레드 세이프)
# -----------------------------
class JobStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._jobs: Dict[str, JobRecord] = {}

    # ------- 생성 -------
    def create(self, payload: AnalysisJobCreate) -> AnalysisJobStatus:
        job_id = uuid.uuid4().hex
        rec = JobRecord(
            job_id=job_id,
            video_url=str(payload.video_url),
            holds=payload.holds,
            options={},  # options 미사용 시 안전 기본값
            status="queued",
            progress=0,
            message="queued",
        )
        with self._lock:
            self._jobs[job_id] = rec
        return self._to_status(rec)

    # ------- 조회 -------
    def _get(self, job_id: str) -> JobRecord:
        with self._lock:
            rec = self._jobs.get(job_id)
        if not rec:
            raise JobNotFoundError(job_id)
        return rec

    def get_status(self, job_id: str) -> AnalysisJobStatus:
        rec = self._get(job_id)
        return self._to_status(rec)

    def get_now_status(self, job_id: str):
        rec = self._get(job_id)
        return rec.status

    def get_result(self, job_id: str) -> Optional[AnalysisJobResult]:
        rec = self._get(job_id)
        return rec.result

    # ------- 갱신 -------
    def set_status(
        self,
        job_id: str,
        *,
        status: Optional[str] = None,
        progress: Optional[int] = None,
        message: Optional[str] = None,
        artifacts: Optional[Artifacts] = None,
    ) -> AnalysisJobStatus:
        rec = self._get(job_id)
        with self._lock:
            if status is not None:
                rec.status = status
            if progress is not None:
                rec.progress = max(0, min(100, int(progress)))
            if message is not None:
                rec.message = message
            if artifacts is not None:
                # 부분 업데이트 지원
                merged = rec.artifacts.model_dump()
                merged.update({k: v for k, v in artifacts.model_dump().items() if v})
                rec.artifacts = Artifacts(**merged)
            rec.touch()
        return self._to_status(rec)

    def set_artifacts(self, job_id: str, **kwargs) -> Artifacts:
        """
        사용 예:
        store.set_artifacts(job_id, skeleton_npy_path="/data/jobs/..../sequence.npy")
        """
        rec = self._get(job_id)
        with self._lock:
            merged = rec.artifacts.model_dump()
            merged.update({k: v for k, v in kwargs.items() if v is not None})
            rec.artifacts = Artifacts(**merged)
            rec.touch()
        return rec.artifacts

    def set_error(self, job_id: str, message: str) -> AnalysisJobStatus:
        return self.set_status(job_id, status="failed", progress=100, message=message)

    def set_result(
        self,
        job_id: str,
        *,
        frames: List[FrameAnalysis],
        drop: Optional[DropAnalysis],
        average_score: float,
    ) -> AnalysisJobResult:
        rec = self._get(job_id)
        with self._lock:
            rec.result = AnalysisJobResult(
                job_id=rec.job_id,
                status="succeeded",  # 결과 객체에도 상태 기록
                frames=frames,
                drop=drop,
                average_score=average_score,
            )
            rec.status = "succeeded"
            rec.progress = 100
            rec.message = "done"
            rec.touch()
            return rec.result

    # ------- 청소(선택) -------
    def cleanup(
        self,
        *,
        older_than_sec: int = 60 * 10,
        on_remove: Optional[Callable[[JobRecord], None]] = None,
    ) -> int:
        """
        완료/실패/취소 후 특정 시간 지난 잡들을 정리.
        - older_than_sec: 이 시간보다 오래된 레코드 제거
        - on_remove: 각 레코드 제거 직전에 호출할 콜백(디스크 아티팩트 삭제 등)
        반환: 제거한 건수
        """
        now = time.time()
        removed = 0
        with self._lock:
            for job_id, rec in list(self._jobs.items()):
                if (
                    rec.status in {"succeeded", "failed", "canceled"}
                    and (now - rec.updated_at) > older_than_sec
                ):
                    try:
                        if on_remove:
                            on_remove(rec)  # 예: artifact_store.delete_tree(job_id)
                    finally:
                        self._jobs.pop(job_id, None)
                        removed += 1
        return removed

    # ------- 유틸 -------
    @staticmethod
    def _to_status(rec: JobRecord) -> AnalysisJobStatus:
        return AnalysisJobStatus(
            job_id=rec.job_id,
            message=rec.message,
        )


# 싱글톤 인스턴스
STORE = JobStore()
