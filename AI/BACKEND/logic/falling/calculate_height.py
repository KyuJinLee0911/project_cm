# BACKEND/logic/calculate_height.py
from typing import Optional, Tuple
import numpy as np

G_STANDARD = 9.80665  # m/s^2


def estimate_drop_height_airtime(
    t_drop: int,
    t_touch: int,
    fps: float,
    *,
    comp_ms_default: float = 60.0,
    frame_uncertainty_frames: int = 1,
    comp_uncertainty_frames: Optional[int] = None,
) -> Tuple[float, float]:

    print("\n[estimate_drop_height_airtime] 호출")
    print(f"  - 입력: t_drop={t_drop}, t_touch={t_touch}, fps={fps}")
    print(f"  - 옵션: comp_ms_default={comp_ms_default}")

    if t_touch <= t_drop:
        raise ValueError(f"t_touch({t_touch}) <= t_drop({t_drop})")

    print(f"  - 보정 후 인덱스: t_drop={t_drop}, t_touch={t_touch}")

    # 에어타임(압축 제외)
    comp_frames = int(round((comp_ms_default / 1000.0) * fps))
    comp_frames = max(0, comp_frames)
    airtime_frames = max(1, (t_touch - t_drop) - comp_frames)
    t_air = airtime_frames / float(fps)  # s

    print(
        f"  - comp_frames={comp_frames}, airtime_frames={airtime_frames}, t_air={t_air:.4f}s"
    )

    # 기본 높이(자유낙하)
    H_air = 0.5 * G_STANDARD * (t_air**2)
    print(f"  - H_air(기본 자유낙하 높이)={H_air:.4f} m")

    # 불확실도 계산
    frame_sigma = frame_uncertainty_frames / max(1.0, fps)
    if comp_uncertainty_frames is None:
        comp_uncertainty_frames = max(1, int(round(0.5 * fps * 0.06)))
    comp_sigma = comp_uncertainty_frames / max(1.0, fps)

    dh_air = G_STANDARD * t_air * np.sqrt(frame_sigma**2 + comp_sigma**2)

    H_sigma = float(np.sqrt(dh_air**2))
    print(f"  - H_sigma(불확실도)={H_sigma:.4f} m")
    print("[estimate_drop_height_airtime] 종료\n")

    return float(H_air), float(H_sigma)
