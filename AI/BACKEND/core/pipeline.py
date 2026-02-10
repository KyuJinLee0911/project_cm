# BACKEND/services/job_pipeline.py (혹은 기존 위치)
from __future__ import annotations

from ..repositories.job_store import STORE
from ..repositories.artifact_store import ARTIFACTS
from ..models.analysis_schemas import (
    DropAnalysis,
)
from ..services import climbing_service, fall_service, video_service
from .redis_pubsub import publisher


def run_job_pipeline(job_id: str) -> None:
    # 진행률 기준선
    P_DL_START, P_DL_DONE = 10, 30
    P_SKEL_START, P_SKEL_DONE = 45, 80
    P_ANALYZE_START, P_ANALYZE_DONE = 85, 100

    # 공통 정보
    rec = STORE._get(job_id)
    video_url: str = rec.video_url
    holds: list[dict] = rec.holds

    # 아티팩트 경로 세팅
    ARTIFACTS.ensure_layout(job_id)
    input_video_path = ARTIFACTS.input_video_path(job_id)

    final_video_path: str | None = None

    try:
        # -------------------------
        # 1) Download
        # -------------------------
        STORE.set_status(
            job_id, status="downloading", progress=P_DL_START, message="downloading..."
        )
        STORE.set_artifacts(job_id, input_video_path=str(input_video_path))
        publisher.publish_status(job_id, "downloading", P_DL_START, "downloading...")

        try:
            final_video_path, video_meta = video_service.download(
                video_url=str(video_url),
                dst_path=str(input_video_path),
            )
            STORE.set_status(job_id, progress=P_DL_DONE, message="download complete")
            STORE.set_artifacts(job_id, input_video_path=final_video_path)
            publisher.publish_status(job_id, "downloading", P_DL_DONE, "download complete")
        except Exception as e:
            STORE.set_error(job_id, f"download error: {e}")
            publisher.publish_error(job_id, f"download error: {e}")
            return
        fps = video_meta.get("fps")
        # -------------------------
        # 2) Skeletonize
        # -------------------------
        STORE.set_status(
            job_id,
            status="skeletonizing",
            progress=P_SKEL_START,
            message="extracting skeletons...",
        )
        publisher.publish_status(job_id, "skeletonizing", P_SKEL_START, "extracting skeletons...")

        try:
            (
                frames,
                skeletons,
                coms,
                start_climbing_frame,
                end_climbing_frame,
                average_score,
            ) = climbing_service.run(
                video_path=str(final_video_path),
                holds=holds,
                fps=fps,
            )

            # 중간 결과 저장
            STORE.set_result(
                job_id, frames=frames, drop=None, average_score=average_score
            )
            STORE.set_status(job_id, progress=P_SKEL_DONE, message="skeleton ready")
            publisher.publish_status(job_id, "skeletonizing", P_SKEL_DONE, "skeleton ready")
        except Exception as e:
            STORE.set_error(job_id, f"skeleton error: {e}")
            publisher.publish_error(job_id, f"skeleton error: {e}")
            return

        # -------------------------
        # 3) Analyze
        # -------------------------
        STORE.set_status(
            job_id,
            status="analyzing",
            progress=P_ANALYZE_START,
            message="analyzing fall...",
        )
        publisher.publish_status(job_id, "analyzing", P_ANALYZE_START, "analyzing fall...")

        try:
            drop: DropAnalysis = fall_service.run(
                kpts_series=skeletons,
                com_series=coms,
                start_climbing_frame=start_climbing_frame,
                end_climbing_frame=end_climbing_frame,
                fps=fps,
            )

            result = STORE.set_result(
                job_id, frames=frames, drop=drop, average_score=average_score
            )
            STORE.set_status(
                job_id,
                progress=P_ANALYZE_DONE,
                status="succeeded",
                message="analysis complete",
            )

            # Redis Pub/Sub으로 최종 결과 Publish
            publisher.publish_status(job_id, "succeeded", P_ANALYZE_DONE, "analysis complete")
            publisher.publish_result(job_id, result.model_dump())
        except Exception as e:
            STORE.set_error(job_id, f"analysis error: {e}")
            publisher.publish_error(job_id, f"analysis error: {e}")
            return
    finally:
        # -------------------------
        # 4) Cleanup (항상 실행)
        # -------------------------
        if final_video_path:
            video_service.delete_video(ARTIFACTS.job_root(job_id))
