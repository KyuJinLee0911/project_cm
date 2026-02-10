# step4_events.py
from typing import List, Optional, Tuple
import numpy as np

def detect_events_with_feet(
    com_series: List[np.ndarray],
    fps: float,
    kpts_series: Optional[List[np.ndarray]] = None,
    # 가장 낮은(=y가 가장 큰) 홀드보다 위에서 착지되면 재탐색
    hold_y_min: Optional[float] = None,
    # 튜닝 파라미터
    min_airtime_s: float = 0.20,
    v_pre_min_px_s: float = 120.0,
    v_post_max_px_s: float = 40.0,
    drop_min_px_s: float = 80.0,
    drop_ratio_max: float = 0.45,
    decel_factor: float = 2.5,
    jerk_gate_factor: float = 1.5,
    # 재탐색 한도
    max_retries: int = 3,
) -> Tuple[int, int]:
    """
    반환: (t_drop, t_touch)
    - 좌표계는 OpenCV(y-down) 가정.
    """

    # -------- 공통 신호 생성 --------
    y_com = np.asarray([float(p[1]) for p in com_series], dtype=np.float32)

    vy = np.zeros(len(y_com), dtype=np.float32)
    for i in range(1, len(y_com)):
        vy[i] = (y_com[i] - y_com[i-1]) * float(fps)

    # y-down이므로 낙하(+), 상승(-)
    downward_v = vy

    ay = np.zeros_like(vy); ay[1:] = (vy[1:] - vy[:-1]) * float(fps)
    j  = np.zeros_like(ay); j [1:] = (ay[1:] - ay[:-1]) * float(fps)

    n = len(vy)
    if n < 3:
        raise ValueError("프레임 수가 너무 적습니다.")

    base_win  = max(3, int(0.40 * fps))
    sustain_L = max(2, int(0.10 * fps))
    k_base    = max(2, int(0.30 * fps))

    # -------- 내부 탐색기 --------
    def _find_pair_from(start_idx: int) -> Tuple[int, int]:
        # --- t_drop ---
        t_drop = None
        for t in range(max(base_win, start_idx), n - sustain_L):
            prev = downward_v[max(start_idx, t-base_win):t]
            if len(prev) < 2:
                continue
            mu, sig = float(np.mean(prev)), float(np.std(prev) + 1e-6)
            v_thr   = max(80.0, mu + 2.0 * sig)
            seg     = downward_v[t:t+sustain_L]
            cond_v  = np.mean(seg) >= v_thr
            cond_a  = np.max(ay[t:t+sustain_L]) >= 600.0
            if cond_v and cond_a:
                t_drop = t
                break
        if t_drop is None:
            # 폴백: 검색구간 내 최대 낙하속도 프레임
            win = downward_v[start_idx:]
            if win.size == 0:
                raise RuntimeError("검색 구간이 비어 있습니다.")
            t_drop = int(np.argmax(win) + start_idx)

        # --- t_touch_v1 (COM 기반) ---
        sustain_L_v1 = max(1, int(round(0.04 * fps)))
        pre_L        = max(1, int(round(0.10 * fps)))
        post_L       = max(1, int(round(0.10 * fps)))
        air_min_L    = max(1, int(round(min_airtime_s * fps)))

        std_ay = float(np.std(ay[:k_base]) if n > k_base else (np.std(ay) + 1e-6))
        std_jj = float(np.std(j [:k_base]) if n > k_base else (np.std(j ) + 1e-6))
        decel_thr = decel_factor     * (std_ay + 1e-6)
        jerk_thr  = jerk_gate_factor * (std_jj + 1e-6)

        search_from = min(max(0, int(t_drop) + air_min_L), n-1)
        t_touch_v1  = None
        for t in range(max(search_from, start_idx), n - sustain_L_v1):
            seg_ay = ay[t:t+sustain_L_v1]
            cond_decel = (np.mean(-seg_ay) >= decel_thr) or (np.mean(np.abs(seg_ay)) >= decel_thr)

            l_pre,  r_pre  = max(0, t - pre_L), t
            l_post, r_post = t, min(n, t + post_L)
            if r_pre <= l_pre or r_post <= l_post:
                continue

            v_pre  = float(np.mean(downward_v[l_pre:r_pre]))
            v_post = float(np.mean(downward_v[l_post:r_post]))
            dv     = v_pre - v_post

            cond_pre   = (v_pre  >= v_pre_min_px_s)
            cond_post  = (v_post <= v_post_max_px_s)
            cond_abs   = (dv     >= drop_min_px_s)
            cond_ratio = (v_post / max(v_pre, 1.0)) <= drop_ratio_max
            cond_jerk  = float(np.max(np.abs(j[t:t+sustain_L_v1]))) >= jerk_thr

            if cond_decel and cond_pre and cond_post and cond_abs and cond_ratio and cond_jerk:
                t_touch_v1 = t
                break

        if t_touch_v1 is None:
            win = np.abs(ay[search_from:])
            t_touch_v1 = int(np.argmax(win) + search_from)

        # --- 발목 보강(가능 시) ---
        t_touch = t_touch_v1
        if kpts_series is not None:
            try:
                L_IDX, R_IDX = 15, 16
                yL = np.asarray([float(k[L_IDX,1]) if (k is not None and len(k) > R_IDX) else np.nan
                                 for k in kpts_series], dtype=np.float32)
                yR = np.asarray([float(k[R_IDX,1]) if (k is not None and len(k) > R_IDX) else np.nan
                                 for k in kpts_series], dtype=np.float32)

                def _vy_(y):
                    v = np.zeros_like(y, dtype=np.float32)
                    if len(y) >= 2: v[1:] = np.diff(y) * float(fps)
                    return v  # y-down 고정

                def _ay_(v):
                    a = np.zeros_like(v, dtype=np.float32)
                    if len(v) >= 2: a[1:] = (v[1:] - v[:-1]) * float(fps)
                    return a

                def _jj_(a):
                    jj = np.zeros_like(a, dtype=np.float32)
                    if len(a) >= 2: jj[1:] = (a[1:] - a[:-1]) * float(fps)
                    return jj

                def _first_touch_foot(y):
                    vyf = _vy_(y); ayf = _ay_(vyf); jf = _jj_(ayf)
                    std_ayf = float(np.std(ayf[:k_base]) if n > k_base else (np.std(ayf) + 1e-6))
                    std_jf  = float(np.std(jf [:k_base]) if n > k_base else (np.std(jf ) + 1e-6))
                    thr_a   = decel_factor     * (std_ayf + 1e-6)
                    thr_j   = jerk_gate_factor * (std_jf  + 1e-6)
                    start_f = min(max(0, int(t_drop) + air_min_L, start_idx), n-1)
                    for t in range(start_f, n - sustain_L_v1):
                        seg_a = ayf[t:t+sustain_L_v1]
                        if (np.mean(-seg_a) >= thr_a) or (np.mean(np.abs(seg_a)) >= thr_a):
                            l_pre,  r_pre  = max(0, t - pre_L), t
                            l_post, r_post = t, min(n, t + post_L)
                            if r_pre <= l_pre or r_post <= l_post:
                                continue
                            v_pre  = float(np.mean(vyf[l_pre:r_pre]))
                            v_post = float(np.mean(vyf[l_post:r_post]))
                            dv     = v_pre - v_post
                            if (v_pre >= v_pre_min_px_s and v_post <= v_post_max_px_s and
                                dv >= drop_min_px_s and (v_post / max(v_pre,1.0)) <= drop_ratio_max and
                                np.max(np.abs(jf[t:t+sustain_L_v1])) >= thr_j):
                                return t
                    return None

                tL = _first_touch_foot(yL)
                tR = _first_touch_foot(yR)
                if tL is not None and tR is not None:
                    t_touch = tL if tL <= tR else tR
                elif tL is not None:
                    t_touch = tL
                elif tR is not None:
                    t_touch = tR
            except Exception:
                # 발목 시그널이 비정상이어도 COM 기반 결과를 유지
                pass

        # 가드
        if t_touch < t_drop:
            t_touch = t_drop

        # 최소 에어타임 보정 (필요 시 t_drop 앞당김)
        min_air_frames = max(2, int(min_airtime_s * fps))
        if (t_touch - t_drop) < min_air_frames:
            look_L = max(start_idx, t_touch - int(0.6 * fps))
            peak   = int(np.argmax(downward_v[look_L:t_touch]) + look_L)
            if peak > look_L:
                gate = max(30.0, np.percentile(downward_v[max(look_L, peak - int(0.3*fps)):peak], 60))
                for tt in range(max(look_L, peak - int(0.3*fps)), peak):
                    ahead = downward_v[tt+1 : min(tt+1+3, peak+1)]
                    if downward_v[tt] < gate and len(ahead) and float(np.mean(ahead)) >= gate:
                        if tt < t_drop:
                            t_drop = tt
                        break

        return int(t_drop), int(t_touch)

    # -------- 1차 탐색 + hold gate 재탐색 루프 --------
    retries = 0
    t_drop, t_touch = _find_pair_from(0)

    # hold 게이트: y_touch < hold_y_min (y-down) 이면 '홀드 위쪽에서' 닿은 것 → 무효 → 재탐색
    while hold_y_min is not None and retries < max_retries:
        y_touch = float(y_com[t_touch])
        touch_above_hold = (y_touch < hold_y_min)
        if not touch_above_hold:
            break  # OK

        retries += 1
        start_next = min(t_touch + 1, n - 1)
        t_drop, t_touch = _find_pair_from(start_next)

    return int(t_drop), int(t_touch)
