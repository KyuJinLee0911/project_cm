# BACKEND/repositories/artifact_store.py
from __future__ import annotations

from pathlib import Path
from typing import Optional, Dict

from ..core.config import settings


class ArtifactStore:
    def __init__(self, base_dir: Optional[str] = None):
        # 기존 세션 저장에 쓰던 STORAGE_DIR를 기본 기반으로 활용
        root = base_dir or settings.STORAGE_DIR or "./storage"
        self.base = Path(root).resolve()

    # ----------------------------
    # 디렉터리
    # ----------------------------
    def job_root(self, job_id: str) -> Path:
        return self.base / "jobs" / job_id

    def input_dir(self, job_id: str) -> Path:
        return self.job_root(job_id) / "input"

    # ----------------------------
    # 파일 경로(표준 파일명)
    # ----------------------------
    def input_video_path(
        self, job_id: str, *, stem: str = "input", ext: str = ".mp4"
    ) -> Path:
        return self.input_dir(job_id) / f"{stem}{ext}"

    # ----------------------------
    # 디렉터리 보장 / 초기화 / 정리
    # ----------------------------
    def ensure_layout(self, job_id: str) -> Dict[str, Path]:
        """
        잡 생성 시 한 번 호출하여 디렉터리 레이아웃 보장.
        """
        input_p = self.input_dir(job_id)
        input_p.mkdir(parents=True, exist_ok=True)

        return {
            "root": self.job_root(job_id),
            "input": input_p,
        }


# 싱글톤 인스턴스
ARTIFACTS = ArtifactStore()
