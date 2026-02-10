# step5_height.py — pruned: keep only estimate_drop_height_airtime
from typing import List, Optional, Tuple, Dict, Any
import numpy as np

G_STANDARD = 9.80665  # m/s^2

def _safe_idx(a, i):
    i = int(np.clip(i, 0, len(a)-1))
    return i

def _compute_vy_from_series_y(y_list: List[float], fps: float) -> np.ndarray:
    vy = np.zeros(len(y_list), dtype=np.float32)
    if len(y_list) >= 2:
        dy = np.diff(np.asarray(y_list, dtype=np.float32))
        vy[1:] = dy * float(fps)  # px/s
    return vy

# -------------------------
# 1) AIR-TIME 기반 높이 (주 방식)
# -------------------------
def estimate_drop_height_airtime(
    com_series: List[np.ndarray],
    t_drop: int,
    t_touch: int,
    fps: float,
    *,
    # 매트 압축 보정: 고정 압축구간(ms)
    comp_ms_default: float = 60.0,
    # v0(초기 수직속도) 보정
    use_v0: bool = True,
    scale_y: Optional[float] = None,   # m/px (v0 보정 시 필요)
    # 불확실도
    scale_sigma_ratio: float = 0.03,   # 스케일 불확실성(3%) → v0 항에만 반영
    frame_uncertainty_frames: int = 1, # t_drop, t_touch 타이밍 ±1프레임 가정
    comp_uncertainty_frames: Optional[int] = None,  # 지정 없으면 fps 기반
    g: float = G_STANDARD,
) -> Tuple[float, float]:

    # 입력 방어
    n = len(com_series)
    if n == 0:
        raise ValueError("com_series가 비어 있습니다.")
    t_drop  = _safe_idx(com_series, t_drop)
    t_touch = _safe_idx(com_series, t_touch)
    if t_touch <= t_drop:
        raise ValueError(f"t_touch({t_touch}) <= t_drop({t_drop})")

    # COM y, vy(픽셀/초)
    com_y = [float(p[1]) for p in com_series]
    vy_px_s = _compute_vy_from_series_y(com_y, fps)
    downward_v = vy_px_s
    
    # 에어타임(압축 제외)
    comp_frames = int(round((comp_ms_default/1000.0) * fps))
    comp_frames = max(0, comp_frames)
    airtime_frames = max(1, (t_touch - t_drop) - comp_frames)
    t_air = airtime_frames / float(fps)  # s

    # 기본 높이(자유낙하): h = 1/2 g t^2
    H_air = 0.5 * g * (t_air ** 2)

    # v0 보정(선택)
    v0_corr = 0.0
    if use_v0 and scale_y is not None and scale_y > 0:
        # 착지 직전 구간 평균 하강속도(m/s) 사용 → v0를 근사적으로 추정
        win = max(1, int(round(0.06 * fps)))  # 60ms
        l = max(t_drop, t_touch - win)
        r = t_touch
        if r > l:
            v_pre_px_s = float(np.mean(downward_v[l:r]))
            v_pre_m_s = v_pre_px_s * float(scale_y)
            # 등가 자유낙하 가정에서 v_pre ≈ g * (t_air) → 실제는 v_pre가 더 클 수도/작을 수도
            # 드롭 직후 초기속도 v0 ≈ v_pre - g * t_air
            v0_est = v_pre_m_s - g * t_air
            # v0가 양수(이미 하강중)면 추가 높이 항( (v0^2)/(2g) )을 보정
            if v0_est > 0:
                v0_corr = (v0_est ** 2) / (2.0 * g)

    H_m = H_air + v0_corr

    # 불확실도(대략적): (프레임 경계 ±, comp 경계 ±, 스케일 3%가 v0 항에 주는 영향)
    frame_sigma = (frame_uncertainty_frames / max(1.0, fps))  # s
    if comp_uncertainty_frames is None:
        comp_uncertainty_frames = max(1, int(round(0.5 * fps * 0.06)))  # ~30ms 수준
    comp_sigma = (comp_uncertainty_frames / max(1.0, fps))             # s

    # 시간 오차 → 높이 오차 전파: dh/dt = g t_air
    dh_air = g * t_air * np.sqrt(frame_sigma**2 + comp_sigma**2)

    # v0 항의 스케일 오차
    dh_v0 = 0.0
    if use_v0 and scale_y is not None and scale_y > 0 and v0_corr > 0:
        dh_v0 = scale_sigma_ratio * v0_corr  # 단순 비례 근사

    H_sigma = float(np.sqrt(dh_air**2 + dh_v0**2))

    return float(H_m), float(H_sigma)
