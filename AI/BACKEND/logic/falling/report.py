# BACKEND/logic/report.py
from typing import List, Dict, Optional
import numpy as np

# ===========================
# 튜닝 상수
# ===========================
PART_PARAMS = {
    "hip": dict(
        v_pre_min=90.0,
        v_post_max=50.0,
        drop_min=60.0,
        drop_ratio_max=0.60,
        decel_factor=2.2,
        jerk_factor=1.4,
        sustain=0.05,
        pre=0.12,
        post=0.12,
    ),
    "back": dict(
        v_pre_min=80.0,
        v_post_max=60.0,
        drop_min=55.0,
        drop_ratio_max=0.65,
        decel_factor=2.0,
        jerk_factor=1.3,
        sustain=0.06,
        pre=0.14,
        post=0.14,
    ),
    "hand_L": dict(
        v_pre_min=80.0,
        v_post_max=70.0,
        drop_min=50.0,
        drop_ratio_max=0.70,
        decel_factor=1.8,
        jerk_factor=1.2,
        sustain=0.05,
        pre=0.12,
        post=0.12,
    ),
    "hand_R": dict(
        v_pre_min=80.0,
        v_post_max=70.0,
        drop_min=50.0,
        drop_ratio_max=0.70,
        decel_factor=1.8,
        jerk_factor=1.2,
        sustain=0.05,
        pre=0.12,
        post=0.12,
    ),
    "elbow_L": dict(
        v_pre_min=75.0,
        v_post_max=70.0,
        drop_min=48.0,
        drop_ratio_max=0.70,
        decel_factor=1.7,
        jerk_factor=1.2,
        sustain=0.05,
        pre=0.12,
        post=0.12,
    ),
    "elbow_R": dict(
        v_pre_min=75.0,
        v_post_max=70.0,
        drop_min=48.0,
        drop_ratio_max=0.70,
        decel_factor=1.7,
        jerk_factor=1.2,
        sustain=0.05,
        pre=0.12,
        post=0.12,
    ),
}

MIN_GAP_FRAMES = 2
ORDER_TOL_FRAMES = 1

# back이 안 잡혔을 때 hip 이후 몇 프레임 뒤를 back으로 볼지
BACK_FALLBACK_OFFSET_FRAMES = 5

# 머리 충돌 감시 윈도우/임계값
HEAD_WIN_AFTER_BACK_S = 0.18
HEAD_COLLAPSE_THRESH_PX = 1.2

# 서서 착지 판정용
STANDING_WIN_AFTER_FEET_S = 0.22
STANDING_GAP_MIN_RATIO_TORSO = 1.35


# ===========================
# 기본 신호 유틸
# ===========================
def _vy(y: np.ndarray, fps: float, y_down: bool) -> np.ndarray:
    v = np.zeros_like(y, dtype=np.float32)
    if len(y) >= 2:
        v[1:] = np.diff(y) * float(fps)
    return v if y_down else -v


def _ay(v: np.ndarray, fps: float) -> np.ndarray:
    a = np.zeros_like(v, dtype=np.float32)
    if len(v) >= 2:
        a[1:] = (v[1:] - v[:-1]) * float(fps)
    return a


def _jerk(a: np.ndarray, fps: float) -> np.ndarray:
    j = np.zeros_like(a, dtype=np.float32)
    if len(a) >= 2:
        j[1:] = (a[1:] - a[:-1]) * float(fps)
    return j


def _median_torso_span(kpts_series: List[np.ndarray]) -> float:
    vals = []
    for kp in kpts_series:
        xy = kp[:, :2]
        if (
            np.all(np.isfinite(xy[5]))
            and np.all(np.isfinite(xy[6]))
            and np.all(np.isfinite(xy[11]))
            and np.all(np.isfinite(xy[12]))
        ):
            sh_mid = (xy[5] + xy[6]) / 2.0
            hip_mid = (xy[11] + xy[12]) / 2.0
            vals.append(abs(float(sh_mid[1] - hip_mid[1])))
    if not vals:
        return 120.0
    return float(np.median(vals))


# ===========================
# 머리/어깨 포인트
# ===========================
def _head_center_from_kpts(
    kp: np.ndarray, up_ratio: float = 0.22
) -> Optional[np.ndarray]:
    xy = kp[:, :2]
    cands = []

    if np.all(np.isfinite(xy[0])):  # nose
        cands.append(xy[0])
    if np.all(np.isfinite(xy[1])) and np.all(np.isfinite(xy[2])):  # both eyes
        cands.append((xy[1] + xy[2]) / 2.0)
    elif np.all(np.isfinite(xy[1])):
        cands.append(xy[1])
    elif np.all(np.isfinite(xy[2])):
        cands.append(xy[2])
    if np.all(np.isfinite(xy[3])):  # ears
        cands.append(xy[3])
    if np.all(np.isfinite(xy[4])):
        cands.append(xy[4])

    torso_h = 0.0
    sh_mid = None
    if (
        np.all(np.isfinite(xy[5]))
        and np.all(np.isfinite(xy[6]))
        and np.all(np.isfinite(xy[11]))
        and np.all(np.isfinite(xy[12]))
    ):
        sh_mid = (xy[5] + xy[6]) / 2.0
        hip_mid = (xy[11] + xy[12]) / 2.0
        torso_h = abs(float(sh_mid[1] - hip_mid[1]))

    if cands:
        face_center = np.mean(np.stack(cands, axis=0), axis=0)
        if torso_h > 0.0:
            return np.array(
                [face_center[0], face_center[1] - up_ratio * torso_h], dtype=np.float32
            )
        return np.array(face_center, dtype=np.float32)

    if sh_mid is not None and torso_h > 0.0:
        return np.array([sh_mid[0], sh_mid[1] - 0.35 * torso_h], dtype=np.float32)
    return None


def _build_tracks_from_kpts(kpts_series: List[np.ndarray]) -> Dict[str, np.ndarray]:
    tracks = {
        "feet": [],
        "hip": [],
        "back": [],
        "hand_L": [],
        "hand_R": [],
        "elbow_L": [],
        "elbow_R": [],
        "_head_y": [],
        "_back_y": [],
        "_shoulder_y": [],
    }

    for kp in kpts_series:
        xy = kp[:, :2]

        feet_y = float(np.mean([xy[15, 1], xy[16, 1]]))
        tracks["feet"].append(feet_y)

        hip_y = float(np.mean([xy[11, 1], xy[12, 1]]))
        tracks["hip"].append(hip_y)

        sh_mid = (xy[5] + xy[6]) / 2.0
        hip_mid = (xy[11] + xy[12]) / 2.0
        back_p = (sh_mid + hip_mid) / 2.0
        tracks["back"].append(float(back_p[1]))
        tracks["_back_y"].append(float(back_p[1]))

        shoulder_y = (xy[5, 1] + xy[6, 1]) / 2.0
        tracks["_shoulder_y"].append(float(shoulder_y))

        tracks["hand_L"].append(
            float(xy[9, 1]) if np.all(np.isfinite(xy[9])) else np.nan
        )
        tracks["hand_R"].append(
            float(xy[10, 1]) if np.all(np.isfinite(xy[10])) else np.nan
        )
        tracks["elbow_L"].append(
            float(xy[7, 1]) if np.all(np.isfinite(xy[7])) else np.nan
        )
        tracks["elbow_R"].append(
            float(xy[8, 1]) if np.all(np.isfinite(xy[8])) else np.nan
        )

        hc = _head_center_from_kpts(kp)
        tracks["_head_y"].append(float(hc[1]) if hc is not None else np.nan)

    return {k: np.asarray(v, dtype=np.float32) for k, v in tracks.items()}


# ===========================
# 단일 트랙에서 터치 프레임 찾기
# ===========================
def _first_touch_like_step(
    y_track: np.ndarray,
    fps: int,
    t_drop_canonical: int,
    *,
    y_down: bool = True,
    v_pre_min: float,
    v_post_max: float,
    drop_min: float,
    drop_ratio_max: float,
    decel_factor: float,
    jerk_factor: float,
    sustain: float,
    pre: float,
    post: float,
    min_airtime_s: float = 0.20,
) -> Optional[int]:
    n = len(y_track)
    if n < 5 or not np.isfinite(y_track).any():
        return None

    v = _vy(y_track, fps, y_down)
    a = _ay(v, fps)
    j = _jerk(a, fps)

    sustain_L = max(1, int(round(sustain * fps)))
    pre_L = max(1, int(round(pre * fps)))
    post_L = max(1, int(round(post * fps)))
    air_min_L = max(1, int(round(min_airtime_s * fps)))

    k_base = max(2, int(0.30 * fps))
    base_std_ay = float(np.std(a[:k_base]) if n > k_base else (np.std(a) + 1e-6))
    base_std_j = float(np.std(j[:k_base]) if n > k_base else (np.std(j) + 1e-6))
    thr_a = decel_factor * (base_std_ay + 1e-6)
    thr_j = jerk_factor * (base_std_j + 1e-6)

    start = min(max(0, int(t_drop_canonical) + air_min_L), n - 1)

    for t in range(start, n - sustain_L):
        seg_a = a[t : t + sustain_L]
        cond_decel = (np.mean(-seg_a) >= thr_a) or (np.mean(np.abs(seg_a)) >= thr_a)
        if not cond_decel:
            continue

        l_pre, r_pre = max(0, t - pre_L), t
        l_post, r_post = t, min(n, t + post_L)
        if r_pre <= l_pre or r_post <= l_post:
            continue

        v_pre = float(np.mean(v[l_pre:r_pre]))
        v_post = float(np.mean(v[l_post:r_post]))
        dv = v_pre - v_post

        cond_pre = v_pre >= v_pre_min
        cond_post = v_post <= v_post_max
        cond_abs = dv >= drop_min
        cond_ratio = (v_post / max(v_pre, 1.0)) <= drop_ratio_max
        cond_jerk = float(np.max(np.abs(j[t : t + sustain_L]))) >= thr_j

        if cond_pre and cond_post and cond_abs and cond_ratio and cond_jerk:
            return t
    return None


# ===========================
# back 터치 보강(수렴 기반)
# ===========================
def _back_touch_by_convergence(
    y_back: np.ndarray,
    y_hip: np.ndarray,
    kpts_series: List[np.ndarray],
    fps: int,
    *,
    t_drop: int,
    t_feet: int,
    y_down: bool = True,
    alpha: float = 0.14,
    max_lead_frames: int = 3,
) -> Optional[int]:
    n = min(len(y_back), len(y_hip))
    if n < 5:
        return None

    S = _median_torso_span(kpts_series)
    thr = alpha * S

    start_from_drop = int(t_drop + 0.10 * fps)
    start = max(0, min(t_feet, start_from_drop) - 2)

    for t in range(start, n):
        d = float(abs(y_back[t] - y_hip[t]))
        if d <= thr:
            if t < t_feet - max_lead_frames:
                continue
            return t
    return None


# ===========================
# 서서 착지 판정 (feet 기준)
# ===========================
def _check_standing_landing_from_tracks(
    contact_times: Dict,
    *,
    win_after_feet_s: float,
    gap_min_ratio_torso: float,
) -> Dict:
    tF = contact_times.get("feet")
    feet = contact_times.get("_feet_y")
    hip = contact_times.get("_hip_y")
    sh = contact_times.get("_shoulder_y")
    fps = contact_times.get("_fps")

    if tF is None or feet is None or hip is None or sh is None or fps is None:
        return {"standing": False, "reason": "insufficient_tracks"}

    feet = np.asarray(feet, dtype=np.float32)
    hip = np.asarray(hip, dtype=np.float32)
    sh = np.asarray(sh, dtype=np.float32)

    n = min(len(feet), len(hip), len(sh))
    if tF >= n:
        return {"standing": False, "reason": "feet_out_of_range"}

    torso_span = np.median(np.abs(sh - hip))
    if not np.isfinite(torso_span) or torso_span <= 1.0:
        torso_span = 120.0

    thr = gap_min_ratio_torso * float(torso_span)
    win_L = max(1, int(round(win_after_feet_s * fps)))
    end = min(n, tF + win_L)

    lowered = False
    max_gap = -1.0
    for t in range(tF, end):
        if not (np.isfinite(feet[t]) and np.isfinite(hip[t])):
            continue
        gap = float(feet[t] - hip[t])
        if gap > max_gap:
            max_gap = gap
        if gap < thr:
            lowered = True
            break

    if lowered:
        return {
            "standing": False,
            "reason": f"hip_lowered(gap<{thr:.1f}px) within {win_after_feet_s:.2f}s",
        }
    else:
        return {
            "standing": True,
            "reason": f"gap_always_large(max_gap={max_gap:.1f}px, thr={thr:.1f}px, win={win_after_feet_s:.2f}s)",
        }


# ===========================
# 머리 gap 붕괴 체크 (tracks 기반)
# ===========================
def _check_head_safety_gap_collapse_from_tracks(
    contact_times: Dict[str, Optional[int]],
    *,
    win_after_back_s: float,
    collapse_thresh_px: float,
) -> Dict:
    tB = contact_times.get("back")
    head = contact_times.get("_head_y")
    sh = contact_times.get("_shoulder_y")
    fps = contact_times.get("_fps")

    if tB is None:
        return {"pass": True, "reason": "no_back_event"}
    if head is None or sh is None or fps is None:
        return {"pass": True, "reason": "no_tracks"}

    head = np.asarray(head, dtype=np.float32)
    sh = np.asarray(sh, dtype=np.float32)

    n = min(len(head), len(sh))
    if tB >= n:
        return {"pass": True, "reason": "back_out_of_range"}

    base_head_y = head[tB]
    base_sh_y = sh[tB]
    if not np.isfinite(base_head_y) or not np.isfinite(base_sh_y):
        return {"pass": True, "reason": "no_head_or_shoulder_at_back"}

    base_gap = base_sh_y - base_head_y

    win_L = max(1, int(round(win_after_back_s * fps)))
    end = min(n, tB + win_L)

    max_collapse = 0.0
    max_collapse_t = None
    for t in range(tB + 1, end):
        if not np.isfinite(head[t]) or not np.isfinite(sh[t]):
            continue
        gap_t = sh[t] - head[t]
        collapse = base_gap - gap_t
        if collapse > max_collapse:
            max_collapse = collapse
            max_collapse_t = t

    if max_collapse_t is not None and max_collapse >= collapse_thresh_px:
        return {
            "pass": False,
            "reason": f"head_gap_collapse({max_collapse:.1f}px) at {max_collapse_t}",
            "t": max_collapse_t,
            "collapse_px": float(max_collapse),
        }

    return {
        "pass": True,
        "reason": f"ok (max_collapse={max_collapse:.1f}px)",
        "max_collapse_px": float(max_collapse),
    }


# 부위별 착지 시점 추출
def extract_contact_times(
    kpts_series: List[np.ndarray],
    fps: int,
    *,
    t_feet_canonical: int,
    t_drop_canonical: int,
) -> Dict[str, Optional[int]]:
    if kpts_series is None:
        return {
            "feet": t_feet_canonical,
            "hip": None,
            "back": None,
            "hand_L": None,
            "hand_R": None,
            "elbow_L": None,
            "elbow_R": None,
            "_head_y": None,
            "_shoulder_y": None,
            "_fps": fps,
            "head_check": {"pass": True, "reason": "no_kpts"},
        }

    tracks = _build_tracks_from_kpts(kpts_series)

    times: Dict[str, Optional[int]] = {
        "feet": int(t_feet_canonical) if t_feet_canonical is not None else None,
        "hip": None,
        "back": None,
        "hand_L": None,
        "hand_R": None,
        "elbow_L": None,
        "elbow_R": None,
    }

    for part in ["hip", "back", "hand_L", "hand_R", "elbow_L", "elbow_R"]:
        y = tracks[part]
        if not np.isfinite(y).any():
            continue

        pp = PART_PARAMS.get(part, PART_PARAMS["hand_L"])

        if part == "back":
            t = _back_touch_by_convergence(
                tracks["back"],
                tracks["hip"],
                kpts_series,
                fps,
                t_drop=t_drop_canonical,
                t_feet=times.get(
                    "feet", t_feet_canonical if t_feet_canonical is not None else 0
                ),
            )
            if t is None:
                t = _first_touch_like_step(
                    y,
                    fps,
                    t_drop_canonical,
                    v_pre_min=pp["v_pre_min"],
                    v_post_max=pp["v_post_max"],
                    drop_min=pp["drop_min"],
                    drop_ratio_max=pp["drop_ratio_max"],
                    decel_factor=pp["decel_factor"],
                    jerk_factor=pp["jerk_factor"],
                    sustain=pp["sustain"],
                    pre=pp["pre"],
                    post=pp["post"],
                    min_airtime_s=0.20,
                )
            if t is None:
                t_hip = times.get("hip")
                if t_hip is not None:
                    t = min(
                        t_hip + BACK_FALLBACK_OFFSET_FRAMES, len(tracks["back"]) - 1
                    )
                else:
                    t = None
        else:
            t = _first_touch_like_step(
                y,
                fps,
                t_drop_canonical,
                v_pre_min=pp["v_pre_min"],
                v_post_max=pp["v_post_max"],
                drop_min=pp["drop_min"],
                drop_ratio_max=pp["drop_ratio_max"],
                decel_factor=pp["decel_factor"],
                jerk_factor=pp["jerk_factor"],
                sustain=pp["sustain"],
                pre=pp["pre"],
                post=pp["post"],
                min_airtime_s=0.20,
            )
            # (삭제됨) near_feet 보조 검사 및 t 무효화 로직

        times[part] = t

    # head는 back 프레임을 대표로
    tB = times.get("back")
    times["head"] = tB

    # tracks를 contact_times에 같이 저장 (후속 evaluate에서 사용)
    times["_head_y"] = tracks["_head_y"]
    times["_shoulder_y"] = tracks["_shoulder_y"]
    times["_feet_y"] = tracks["feet"]
    times["_hip_y"] = tracks["hip"]
    times["_fps"] = fps

    # 머리 gap 붕괴 검사(프레임 저장 관련 로직 제거)
    head_check = _check_head_safety_gap_collapse_from_tracks(
        times,
        win_after_back_s=HEAD_WIN_AFTER_BACK_S,
        collapse_thresh_px=HEAD_COLLAPSE_THRESH_PX,
    )
    times["head_check"] = head_check

    return times


def get_landing_order(contact_times: Dict[str, Optional[int]]) -> List[str]:
    """
    contact_times 딕셔너리(예: extract_contact_times 반환값)에서
    실제 착지된 신체 부위 순서를 프레임 순으로 문자열 리스트로 반환합니다.
    """
    # 분석 대상 파트
    parts = ["feet", "hip", "back", "hand_L", "hand_R", "elbow_L", "elbow_R"]

    # (part, frame) 쌍 중 유효한 값만 추출
    valid_pairs = [
        (p, contact_times.get(p)) for p in parts if contact_times.get(p) is not None
    ]

    # 프레임 인덱스 기준 오름차순 정렬
    ordered = sorted(valid_pairs, key=lambda x: x[1])

    # 파트 이름만 추출
    return [p for p, _ in ordered]


# 한글 라벨
_KR = {
    "feet": "발",
    "hip": "엉덩이",
    "back": "등",
    "hand_L": "왼손",
    "hand_R": "오른손",
    "elbow_L": "왼팔꿈치",
    "elbow_R": "오른팔꿈치",
}


def _fmt_order(order):
    if not order:
        return "정보 없음"
    return " → ".join(_KR.get(x, x) for x in order)


def evaluate_rules_message(contact_times: Dict) -> str:
    """
    extract_contact_times 결과(contact_times)를 기반으로
    규칙을 검사하고, 한국어 코칭 메시지를 반환.
    """

    tF = contact_times.get("feet")
    tH = contact_times.get("hip")
    tB = contact_times.get("back")
    tHL = contact_times.get("hand_L")
    tHR = contact_times.get("hand_R")
    tEL = contact_times.get("elbow_L")
    tER = contact_times.get("elbow_R")

    # 착지 순서
    order = get_landing_order(contact_times)

    # --------------------
    # 1. 인체 인식(필수 부위) 체크
    #    feet, hip, back 셋 다 있어야 "분석 가능"으로 간주
    # --------------------
    essential_ok = tF is not None and tH is not None and tB is not None

    if not essential_ok:
        # 인체 인식 불충분 -> 이 메시지 외에는 아무 것도 포함하지 않음
        lines = []
        if order:
            lines.append(f"[착지 순서] {_fmt_order(order)}")
        lines += [
            "⚠️ 인체 인식이 충분히 되지 않아 낙법 분석을 진행할 수 없습니다.",
            "  - 전신이 화면에 잘 나오도록 카메라 각도와 거리를 조정해 주세요.",
            "  - 몸이 가려지지 않도록 다른 사람·홀드·벽 등에 겹치지 않게 촬영해 주세요.",
            "  - 조명을 밝게 하고, 옷과 배경의 대비를 높이면 인식이 더 잘 됩니다.",
        ]
        return "\n".join(lines)

    # --------------------
    # 2. 서서 착지 판정
    #    서서 착지면 이것만 알림 (다른 규칙 메시지 X)
    # --------------------
    standing_check = _check_standing_landing_from_tracks(
        contact_times,
        win_after_feet_s=STANDING_WIN_AFTER_FEET_S,
        gap_min_ratio_torso=STANDING_GAP_MIN_RATIO_TORSO,
    )
    r2_standing = standing_check.get("standing", False)
    r2_reason = standing_check.get("reason", "")

    if r2_standing:
        lines = []
        lines += [
            "⚠️ 서서 착지 패턴으로 판단됩니다.",
            "• 매우 위험한 착지입니다.",
            "  - 발로만 버티지 말고, 착지와 동시에 엉덩이를 충분히 낮춰 충격을 분산해 주세요.",
        ]
        return "\n".join([ln for ln in lines if ln])

    # --------------------
    # 3. 세부 규칙 (필수 부위 OK + 서서 착지 아님인 경우만)
    #    (1) 순서: 발 < 엉덩이 <= 등+허용오차
    #    (2) 팔(손/팔꿈치)이 등보다 먼저 닿았는지
    #    (3) 머리 간극 붕괴 여부
    # --------------------

    # (1) 순서
    order_ok = tF < tH <= tB + ORDER_TOL_FRAMES

    # (2) 팔 먼저 닿음 (손/팔꿈치 통합)
    arm_contacts = []
    if tHL is not None:
        arm_contacts.append(("왼팔", tHL))
    if tHR is not None:
        arm_contacts.append(("오른팔", tHR))
    if tEL is not None:
        arm_contacts.append(("왼팔꿈치", tEL))
    if tER is not None:
        arm_contacts.append(("오른팔꿈치", tER))

    early_arms = [label for (label, t) in arm_contacts if t < tB]
    arms_ok = len(early_arms) == 0

    # (3) 머리 간극 붕괴
    head_check = contact_times.get(
        "head_check", {"pass": True, "reason": "not_computed_in_extract"}
    )
    head_ok = bool(head_check.get("pass", True))
    head_reason = head_check.get("reason", "")

    # 전체 통과 여부
    overall_pass = order_ok and arms_ok and head_ok

    # --------------------
    # 4. 메시지 구성
    # --------------------
    lines = []
    if order:
        lines.append(f"[착지 순서] {_fmt_order(order)}")

    if overall_pass:
        # 모든 규칙 통과
        lines += [
            "✅ 안전한 낙법 패턴으로 판단됩니다.",
            "— 발 → 엉덩이 → 등 순서를 잘 지키고 있으며, 팔과 머리 보호도 적절하게 수행하고 있습니다.",
        ]
        return "\n".join(lines)

    # 하나라도 위반 시: 해당 항목만 선택적으로 출력

    lines.append("⚠️ 개선이 필요한 부분이 있습니다. 아래 항목을 확인해 주세요.")

    # 순서 문제
    if not order_ok:
        lines += [
            "• 착지 순서가 어긋났습니다.",
            "  - 권장 순서: 발 → 엉덩이 → 등(등은 엉덩이보다 늦거나 거의 동시에).",
            f"  - 현재 순서: {_fmt_order(order)}",
        ]

    # 팔 먼저 닿음
    if not arms_ok:
        who = ", ".join(early_arms)
        lines += [
            f"• 팔이 몸통보다 먼저 닿았습니다 ({who}).",
            "  - 손이나 팔꿈치로 버티면 손목·팔꿈치·어깨 부상 위험이 큽니다.",
            "  - 하체와 몸통으로 먼저 충격을 흡수하고, 팔은 머리와 얼굴을 보호하는 보조 역할로만 사용해 주세요.",
        ]

    # 머리 위험
    if not head_ok:
        lines += [
            "• 머리-어깨 간격이 급격히 줄어드는 위험 패턴이 감지되었습니다.",
            "  - 턱을 더 당기고 고개를 숙여 뒤통수와 목을 보호해 주세요.",
            f"  - 참고 정보: {head_reason}" if head_reason else "",
        ]

    return "\n".join([ln for ln in lines if ln])
