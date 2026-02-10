# utils_contact.py
import numpy as np
from typing import Optional

def first_contact_by_kinematics(
    y_series, fps,
    *, t_drop_hint: Optional[int] = None,
    y_down: bool = True,
    # 검색 창/보호
    min_after_drop_frames: int = 3,
    min_airtime_s: float = 0.20,
    search_horizon_s: float = 1.0,
    # 방향전환 유효성
    smooth_win: int = 3,
    v_down_min_px_s: float = 60.0,
    # 감속/저크 대안 임계
    decel_factor: float = 2.5,
    jerk_gate_factor: float = 1.5,
    sustain_win_s: float = 0.04,
    pre_win_s: float = 0.10,
    post_win_s: float = 0.10,
    v_pre_min_px_s: float = 120.0,
    v_post_max_px_s: float = 40.0,
    drop_min_px_s: float = 80.0,
    drop_ratio_max: float = 0.45,
    a_abs_min_px_s2: float = 1200.0,
    debug: bool = False,
) -> Optional[int]:
    """
    단일 y-시퀀스(예: 발, 엉덩이, 등, 손)의 접촉 프레임을 검출.
    1) v(+↓) 부호전환(+→≤0)
    2) 감속+전후속도+저크 지속
    3) 폴백: 최소 에어타임 이후 |ay| 최대
    """
    y = np.asarray(y_series, dtype=np.float32)
    n = len(y)
    if n < 3:
        return None

    def _ma(x, k):
        if k <= 1: return x
        k = int(k); pad = k // 2
        c = np.convolve(x, np.ones(k, dtype=np.float32)/k, mode="same")
        for i in range(pad):
            c[i] = np.mean(x[:i+1])
            c[-(i+1)] = np.mean(x[-(i+1):])
        return c

    y_s = _ma(y, smooth_win)
    v = np.zeros_like(y_s)
    v[1:] = np.diff(y_s) * float(fps)
    if not y_down:
        v = -v

    a = np.zeros_like(v)
    a[1:] = (v[1:] - v[:-1]) * float(fps)
    j = np.zeros_like(a)
    j[1:] = (a[1:] - a[:-1]) * float(fps)

    air_L = max(1, int(round(min_airtime_s * fps)))
    start = 0 if t_drop_hint is None else min(max(0, int(t_drop_hint) + max(min_after_drop_frames, air_L)), n - 1)
    end = min(n - 1, start + int(round(search_horizon_s * fps)))

    # 1) 방향 전환(+→≤0)
    for t in range(start + 1, end + 1):
        if (v[t-1] >= v_down_min_px_s) and (v[t] <= 0.0):
            return t

    # 2) 감속 지속 + 전후속도 급락 + 저크
    k_base = max(2, int(0.3 * fps))
    std_ay = float(np.std(a[:k_base]) if n > k_base else (np.std(a) + 1e-6))
    std_j  = float(np.std(j[:k_base]) if n > k_base else (np.std(j) + 1e-6))
    thr_a, thr_j = decel_factor * (std_ay + 1e-6), jerk_gate_factor * (std_j + 1e-6)

    sustain_L = max(1, int(round(sustain_win_s * fps)))
    pre_L = max(1, int(round(pre_win_s * fps)))
    post_L = max(1, int(round(post_win_s * fps)))

    for t in range(start, max(start, end - sustain_L) + 1):
        seg_a = a[t:t+sustain_L]
        cond_decel = (np.mean(-seg_a) >= thr_a) or (np.mean(np.abs(seg_a)) >= thr_a)
        l_pre, r_pre = max(0, t - pre_L), t
        l_post, r_post = t, min(n, t + post_L)
        if r_pre <= l_pre or r_post <= l_post:
            continue

        v_pre = float(np.mean(v[l_pre:r_pre]))
        v_post = float(np.mean(v[l_post:r_post]))
        dv = v_pre - v_post
        conds = (
            cond_decel,
            v_pre >= v_pre_min_px_s,
            v_post <= v_post_max_px_s,
            dv >= drop_min_px_s,
            (v_post / max(v_pre, 1.0)) <= drop_ratio_max,
            float(np.max(np.abs(j[t:t+sustain_L]))) >= thr_j
        )
        if all(conds):
            return t

    # 3) 폴백: |ay| 최대
    t_alt = int(np.argmax(np.abs(a[start:end+1])) + start)
    if np.abs(a[t_alt]) >= a_abs_min_px_s2:
        return t_alt

    return None
