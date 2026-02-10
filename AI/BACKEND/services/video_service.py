# BACKEND/services/video_service.py
from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Tuple, Dict

import cv2
import requests

from ..core.settings_analysis import settings as A


def _ensure_parent_dir(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


def _download_to_temp(url: str) -> Path:
    """
    스트리밍 다운로드로 임시 파일을 만든다.
    """
    if not (url.startswith("http://") or url.startswith("https://")):
        raise ValueError("video_url은 http/https여야 합니다.")

    # 임시 파일 생성
    fd, tmp_path = tempfile.mkstemp(suffix=".mp4")
    os.close(fd)
    tmp = Path(tmp_path)

    # 스트리밍 다운로드
    with requests.get(url, stream=True, timeout=30) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
    return tmp


def _opencv_meta(video_path: str) -> Dict:
    """
    OpenCV로 메타데이터 최소 추출 (fps/width/height/duration_s).
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError("영상 파일을 열 수 없습니다.")

    fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    cap.release()

    duration_s = float(frame_count / fps) if fps and frame_count > 0 else 0.0
    return {
        "fps": int(fps),
        "width": width,
        "height": height,
        "frames": frame_count,
        "duration_s": duration_s,
    }


def download(video_url: str, dst_path: str) -> Tuple[str, Dict]:
    """
    video_url을 다운로드하여 dst_path로 저장.
    fps가 지정되면 FFmpeg로 FPS 고정(FFmpeg 미설치 시 건너뜀).
    반환: (최종 저장 경로, 메타데이터 dict)
    """
    dst = Path(dst_path)
    _ensure_parent_dir(dst)

    # 1) 다운로드
    tmp_in = _download_to_temp(video_url)

    final_path = dst
    shutil.move(str(tmp_in), str(dst))

    # 3) 메타 추출
    meta = _opencv_meta(str(final_path))

    # 4) 길이 제한 검사
    max_len = A.MAX_VIDEO_DURATION_S or 0
    if max_len and meta.get("duration_s", 0) > max_len:
        # 초과 시 파일 정리 후 예외
        try:
            final_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise RuntimeError(
            f"영상 길이 초과: {meta.get('duration_s', 0):.2f}s > {max_len}s"
        )

    return str(final_path), meta


def delete_video(path: Path | Path) -> None:
    """
    분석 파이프라인 종료 후 원본 영상을 삭제하기 위한 유틸.
    - 파일 또는 디렉터리 모두 안전하게 삭제.
    - 존재하지 않아도 조용히 넘어감.
    """
    p = path
    try:
        shutil.rmtree(p)
    except FileNotFoundError:
        pass
    except Exception as e:
        # TODO: logger.warning(f"delete_video 실패: {p} — {e}")
        pass
