# BACKEND/logic/detect_falling.py
from typing import List, Optional, Tuple
import numpy as np


def detect_events_with_feet(
    com_series: List[np.ndarray],
    fps: int,
    kpts_series: Optional[List[np.ndarray]] = None,
    start_climbing_frame: int = 0,
    end_climbing_frame: int = 200000,
    min_airtime_s: float = 0.20,
    v_pre_min_px_s: float = 120.0,
    v_post_max_px_s: float = 40.0,
    drop_min_px_s: float = 80.0,
    drop_ratio_max: float = 0.45,
    decel_factor: float = 2.5,
    jerk_gate_factor: float = 1.5,
    max_retries: int = 3,
) -> Tuple[int, int]:

    print("\n[detect_events_with_feet] 호출")
    print(f"  - len(com_series)={len(com_series)}, fps={fps}")
    print(f"  - start_climbing_frame={start_climbing_frame}")

    # ---------------- 공통 신호 생성 ----------------
    y_com = np.asarray([float(p[1]) for p in com_series], dtype=np.float32)

    vy = np.zeros(len(y_com), dtype=np.float32)
    for i in range(1, len(y_com)):
        vy[i] = (y_com[i] - y_com[i - 1]) * float(fps)

    downward_v = vy  # y-down 기준: 값이 클수록 더 빠른 하강
    ay = np.zeros_like(vy)
    ay[1:] = (vy[1:] - vy[:-1]) * float(fps)
    j = np.zeros_like(ay)
    j[1:] = (ay[1:] - ay[:-1]) * float(fps)

    n = len(vy)
    if n < 3:
        raise ValueError("프레임 수가 너무 적습니다.")

    base_win = max(3, int(0.40 * fps))
    sustain_L = max(2, int(0.10 * fps))
    k_base = max(2, int(0.30 * fps))

    # 탐색 시작 프레임 클램프
    start_idx_global = max(0, min(start_climbing_frame, n - 1))
    print(f"  - 탐색 시작 프레임: {start_idx_global} 이후")

    if n - start_idx_global < 3:
        raise ValueError(
            f"탐색 가능 구간이 너무 짧습니다. (start={start_idx_global}, n={n})"
        )

    print(f"  - n={n}, base_win={base_win}, sustain_L={sustain_L}, k_base={k_base}")

    # ---------------- 내부 탐색 함수 ----------------
    def _find_pair_from(start_idx: int) -> Tuple[int, int]:
        # 항상 start_climbing_frame 이후에서 시작
        start_idx = max(start_idx_global, min(start_idx, n - 1))
        print(f"[detect_events_with_feet::_find_pair_from] start_idx={start_idx}")

        # ---------- t_drop 탐색 ----------
        t_drop: Optional[int] = None

        # t는 base_win 보장 + start_idx 이후 + sustain_L 고려
        t_start = max(base_win, start_idx)
        for t in range(t_start, n - sustain_L):
            prev_L = max(start_idx, t - base_win)
            prev = downward_v[prev_L:t]
            if len(prev) < 2:
                continue

            mu = float(np.mean(prev))
            sig = float(np.std(prev) + 1e-6)
            v_thr = max(80.0, mu + 2.0 * sig)

            seg = downward_v[t : t + sustain_L]
            cond_v = float(np.mean(seg)) >= v_thr
            cond_a = float(np.max(ay[t : t + sustain_L])) >= 600.0

            if cond_v and cond_a:
                t_drop = t
                print(f"  - t_drop 감지: t={t}, v_thr={v_thr:.2f}")
                break

        if t_drop is None:
            # 탐색 구간 내 최대 하강 속도 프레임 사용
            win = downward_v[start_idx:]
            if win.size == 0:
                raise RuntimeError("검색 구간이 비어 있습니다.")
            off = int(np.argmax(win))
            t_drop = start_idx + off
            print(f"  - t_drop 폴백(argmax in [{start_idx}, {n-1}]): t_drop={t_drop}")

        # ---------- t_touch_v1 (COM 기반) ----------
        sustain_L_v1 = max(1, int(round(0.04 * fps)))
        pre_L = max(1, int(round(0.10 * fps)))
        post_L = max(1, int(round(0.10 * fps)))
        air_min_L = max(1, int(round(min_airtime_s * fps)))

        # 기준 분산: start_idx 기준
        if n > start_idx + k_base:
            std_ay = float(np.std(ay[start_idx : start_idx + k_base]) + 1e-6)
            std_jj = float(np.std(j[start_idx : start_idx + k_base]) + 1e-6)
        else:
            std_ay = float(np.std(ay) + 1e-6)
            std_jj = float(np.std(j) + 1e-6)

        decel_thr = decel_factor * std_ay
        jerk_thr = jerk_gate_factor * std_jj

        search_from = int(t_drop) + air_min_L
        search_from = max(start_idx, search_from)
        search_from = min(search_from, n - 1)

        t_touch_v1: Optional[int] = None
        for t in range(search_from, n - sustain_L_v1):
            seg_ay = ay[t : t + sustain_L_v1]
            cond_decel = (np.mean(-seg_ay) >= decel_thr) or (
                np.mean(np.abs(seg_ay)) >= decel_thr
            )

            l_pre, r_pre = max(start_idx, t - pre_L), t
            l_post, r_post = t, min(n, t + post_L)
            if r_pre <= l_pre or r_post <= l_post:
                continue

            v_pre = float(np.mean(downward_v[l_pre:r_pre]))
            v_post = float(np.mean(downward_v[l_post:r_post]))
            dv = v_pre - v_post

            cond_pre = v_pre >= v_pre_min_px_s
            cond_post = v_post <= v_post_max_px_s
            cond_abs = dv >= drop_min_px_s
            cond_ratio = (v_post / max(v_pre, 1.0)) <= drop_ratio_max
            cond_jerk = float(np.max(np.abs(j[t : t + sustain_L_v1]))) >= jerk_thr

            if (
                cond_decel
                and cond_pre
                and cond_post
                and cond_abs
                and cond_ratio
                and cond_jerk
            ):
                t_touch_v1 = t
                print(
                    f"  - t_touch_v1 감지: t={t}, "
                    f"v_pre={v_pre:.1f}, v_post={v_post:.1f}, dv={dv:.1f}"
                )
                break

        if t_touch_v1 is None:
            # COM 가속도 기준 최대 충격 지점 폴백
            win = np.abs(ay[search_from:])
            if win.size == 0:
                t_touch_v1 = t_drop
            else:
                off = int(np.argmax(win))
                t_touch_v1 = search_from + off
            print(f"  - t_touch_v1 폴백: t={t_touch_v1}")

        # ---------- 발목 기반 보강 ----------
        t_touch = t_touch_v1
        if kpts_series is not None:
            try:
                print("  - 발목 시그널 기반 보강 시도")
                L_IDX, R_IDX = 15, 16

                yL = np.asarray(
                    [
                        (
                            float(k[L_IDX, 1])
                            if (k is not None and k.shape[0] > R_IDX)
                            else np.nan
                        )
                        for k in kpts_series
                    ],
                    dtype=np.float32,
                )
                yR = np.asarray(
                    [
                        (
                            float(k[R_IDX, 1])
                            if (k is not None and k.shape[0] > R_IDX)
                            else np.nan
                        )
                        for k in kpts_series
                    ],
                    dtype=np.float32,
                )

                def _vy_(y):
                    v = np.zeros_like(y, dtype=np.float32)
                    if len(y) >= 2:
                        v[1:] = np.diff(y) * float(fps)
                    return v

                def _ay_(v):
                    a = np.zeros_like(v, dtype=np.float32)
                    if len(v) >= 2:
                        a[1:] = (v[1:] - v[:-1]) * float(fps)
                    return a

                def _jj_(a):
                    jj = np.zeros_like(a, dtype=np.float32)
                    if len(a) >= 2:
                        jj[1:] = (a[1:] - a[:-1]) * float(fps)
                    return jj

                def _first_touch_foot(y, label: str):
                    vyf = _vy_(y)
                    ayf = _ay_(vyf)
                    jf = _jj_(ayf)

                    if n > start_idx + k_base:
                        std_ayf = float(
                            np.std(ayf[start_idx : start_idx + k_base]) + 1e-6
                        )
                        std_jf = float(
                            np.std(jf[start_idx : start_idx + k_base]) + 1e-6
                        )
                    else:
                        std_ayf = float(np.std(ayf) + 1e-6)
                        std_jf = float(np.std(jf) + 1e-6)

                    thr_a = decel_factor * std_ayf
                    thr_j = jerk_gate_factor * std_jf

                    start_f = max(start_idx, int(t_drop) + air_min_L)
                    start_f = min(start_f, n - 1)

                    for tt in range(start_f, n - sustain_L_v1):
                        seg_a = ayf[tt : tt + sustain_L_v1]
                        if (np.mean(-seg_a) >= thr_a) or (
                            np.mean(np.abs(seg_a)) >= thr_a
                        ):
                            l_pre, r_pre = max(start_idx, tt - pre_L), tt
                            l_post, r_post = tt, min(n, tt + post_L)
                            if r_pre <= l_pre or r_post <= l_post:
                                continue
                            v_pre = float(np.mean(vyf[l_pre:r_pre]))
                            v_post = float(np.mean(vyf[l_post:r_post]))
                            dv = v_pre - v_post
                            if (
                                v_pre >= v_pre_min_px_s
                                and v_post <= v_post_max_px_s
                                and dv >= drop_min_px_s
                                and (v_post / max(v_pre, 1.0)) <= drop_ratio_max
                                and np.max(np.abs(jf[tt : tt + sustain_L_v1])) >= thr_j
                            ):
                                print(f"    - {label} foot touch 감지: t={tt}")
                                return tt
                    return None

                tL = _first_touch_foot(yL, "L")
                tR = _first_touch_foot(yR, "R")

                cand = None
                if tL is not None and tR is not None:
                    cand = tL if tL <= tR else tR
                elif tL is not None:
                    cand = tL
                elif tR is not None:
                    cand = tR

                if cand is not None:
                    cand = max(start_idx, min(cand, n - 1))
                    t_touch = cand

            except Exception as e:
                print(f"  - 발목 보강 중 예외 발생: {e} (COM 기반 유지)")

        # ---------- 관계/에어타임 보정 ----------
        if t_touch < t_drop:
            print("  - t_touch < t_drop 감지 → t_touch=t_drop로 보정")
            t_touch = t_drop

        min_air_frames = max(2, int(min_airtime_s * fps))
        if (t_touch - t_drop) < min_air_frames:
            print(
                f"  - 에어타임 부족({t_touch - t_drop} < {min_air_frames}) "
                f"→ t_drop 재조정 시도"
            )
            look_L = max(start_idx, t_touch - int(0.6 * fps))
            if t_touch > look_L:
                peak_off = int(np.argmax(downward_v[look_L:t_touch]))
                peak = look_L + peak_off
            else:
                peak = t_drop

            if peak > look_L:
                gate_v = max(
                    30.0,
                    np.percentile(
                        downward_v[max(start_idx, peak - int(0.3 * fps)) : peak],
                        60,
                    ),
                )
                for tt in range(max(start_idx, peak - int(0.3 * fps)), peak):
                    ahead = downward_v[tt + 1 : min(tt + 1 + 3, peak + 1)]
                    if (
                        downward_v[tt] < gate_v
                        and len(ahead)
                        and float(np.mean(ahead)) >= gate_v
                    ):
                        if tt < t_drop:
                            print(f"    - t_drop 보정: {t_drop} -> {tt}")
                            t_drop = tt
                        break

        print(
            f"[detect_events_with_feet::_find_pair_from] 반환: "
            f"t_drop={t_drop}, t_touch={t_touch}"
        )
        return int(t_drop), int(t_touch)

    # ---------------- 1차 탐색 + hold gate ----------------
    t_drop, t_touch = _find_pair_from(start_idx_global)

    retries = 0
    while retries < max_retries:
        # 등반 종료 프레임 이후에서 낙하 시작이 잡히면 더 이상 의미 없는 재탐색이므로 중단
        if t_drop > end_climbing_frame:
            print(
                f"[hold_gate] t_drop={t_drop} > end_climbing_frame={end_climbing_frame} "
                f"→ 재탐색 중지"
            )
            break

        y_touch = float(y_com[t_touch])
        print(f"[hold_gate] try={retries}, t_touch={t_touch}, " f"y_touch={y_touch}")

        retries += 1
        start_next = min(max(t_touch + 1, start_idx_global), n - 1)
        print(f"[hold_gate] 재탐색 start_next={start_next}")
        t_drop, t_touch = _find_pair_from(start_next)

    print(
        f"[detect_events_with_feet] 최종 결정: " f"t_drop={t_drop}, t_touch={t_touch}\n"
    )
    return int(t_drop), int(t_touch)
