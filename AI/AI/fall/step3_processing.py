# step3_processing.py — lean & compatible
from typing import List, Tuple, Literal, Dict
import numpy as np
import time

# -----------------------------
# 1) 파생 포인트/COM
# -----------------------------
def estimate_body_center(points: np.ndarray) -> np.ndarray:
    """
    points: (17,2) COCO keypoints (픽셀)
    단순 가중 평균 기반 COM 근사.
    """
    # 각 파트 평균점
    head  = np.nanmean(points[[0, 1, 2, 3, 4]], axis=0)
    torso = np.nanmean(points[[5, 6, 11, 12]], axis=0)
    arms  = np.nanmean(points[[7, 8, 9, 10]], axis=0)
    legs  = np.nanmean(points[[13, 14, 15, 16]], axis=0)
    # 가중치 (간단 모델)
    w_head, w_torso, w_arms, w_legs = 0.08, 0.43, 0.14, 0.35
    cx = head[0]*w_head + torso[0]*w_torso + arms[0]*w_arms + legs[0]*w_legs
    cy = head[1]*w_head + torso[1]*w_torso + arms[1]*w_arms + legs[1]*w_legs
    return np.array([cx, cy], dtype=np.float32)

def avg_ankle(p: np.ndarray) -> np.ndarray:
    """좌/우 발목 평균 (COCO: 15, 16)."""
    return (p[15] + p[16]) / 2.0

def mid_shoulder(p: np.ndarray) -> np.ndarray:
    return (p[5] + p[6]) / 2.0

def mid_hip(p: np.ndarray) -> np.ndarray:
    return (p[11] + p[12]) / 2.0

# -----------------------------
# 2) NaN 보간 유틸
# -----------------------------
def _interp_1d_nan(arr: np.ndarray) -> np.ndarray:
    """1D 선형보간. 끝단 NaN은 가장 가까운 유효값으로 연장, 전부 NaN이면 0."""
    out = arr.astype(np.float32).copy()
    n = len(out)
    idx = np.arange(n)
    mask = ~np.isnan(out)
    if mask.any():
        out[~mask] = np.interp(idx[~mask], idx[mask], out[mask])
        if np.isnan(out[0]):  out[0]  = out[mask][0]
        if np.isnan(out[-1]): out[-1] = out[mask][-1]
    else:
        out[:] = 0.0
    return out

def interp_xy_series(series_xy: List[np.ndarray]) -> List[np.ndarray]:
    """[(x,y), ...] 시계열의 NaN을 x,y 각각 독립 보간."""
    xs = np.array([p[0] for p in series_xy], dtype=np.float32)
    ys = np.array([p[1] for p in series_xy], dtype=np.float32)
    xs = _interp_1d_nan(xs); ys = _interp_1d_nan(ys)
    return [np.array([x, y], dtype=np.float32) for x, y in zip(xs, ys)]

# -----------------------------
# 3) 스무딩 (MA/EMA)
# -----------------------------
def moving_average_xy(series_xy: List[np.ndarray], win: int = 3) -> List[np.ndarray]:
    """이동평균. 중앙 패딩 구간은 부분 평균으로 경계 왜곡 최소화."""
    k = max(1, int(win))
    xs = np.array([p[0] for p in series_xy], dtype=np.float32)
    ys = np.array([p[1] for p in series_xy], dtype=np.float32)

    def _ma(v):
        if k == 1:
            return v
        c = np.convolve(v, np.ones(k, dtype=np.float32)/k, mode="same")
        pad = k // 2
        for i in range(pad):
            c[i] = np.mean(v[:i+1])
            c[-(i+1)] = np.mean(v[-(i+1):])
        return c

    xs_s = _ma(xs); ys_s = _ma(ys)
    return [np.array([x, y], dtype=np.float32) for x, y in zip(xs_s, ys_s)]

def ema_xy(series_xy: List[np.ndarray], alpha: float = 0.4) -> List[np.ndarray]:
    """지수이동평균."""
    a = float(np.clip(alpha, 0.0, 1.0))
    out, prev = [], None
    for p in series_xy:
        p = p.astype(np.float32)
        prev = p if prev is None else (a * p + (1.0 - a) * prev)
        out.append(prev.copy())
    return out

# -----------------------------
# 4) 속도 계산
# -----------------------------
def derive_vy(series_xy: List[np.ndarray], fps: float) -> List[float]:
    """y 성분 속도(px/s). OpenCV 좌표계(y-down)면 낙하 시 양수가 되도록 그대로 사용."""
    vy = [0.0]
    for i in range(1, len(series_xy)):
        vy.append((series_xy[i][1] - series_xy[i-1][1]) * float(fps))
    return vy

# -----------------------------
# 5) 메인 파이프
# -----------------------------
def build_step3_outputs(
    seq: List[Dict],                         # step2 결과: [{"idx","time","kpts","conf"}, ...]
    smoothing: Literal["ma", "ema"] = "ma",
    ma_win: int = 3,
    ema_alpha: float = 0.4,
    fps: float = 30.0,
    *,
    verbose: bool = False
) -> Dict[str, List]:
    """
    반환:
        {
          "times":        List[float],
          "kpts_series":  List[np.ndarray] (각 (17,2)),
          "com_series":   List[np.ndarray] (각 (2,)),
          "ankle_series": List[np.ndarray] (각 (2,)),
          "vy_com":       List[float]
        }
    """
    t0 = time.time()
    times = [float(d["time"]) for d in seq]
    kpts_raw = [np.asarray(d["kpts"], dtype=np.float32) for d in seq]

    # 1) 원시 파생 포인트
    com_raw   = [estimate_body_center(p) for p in kpts_raw]
    ankle_raw = [avg_ankle(p)           for p in kpts_raw]

    # 2) NaN 보간
    com_filled   = interp_xy_series(com_raw)
    ankle_filled = interp_xy_series(ankle_raw)

    # 3) 스무딩
    if smoothing == "ma":
        com_s   = moving_average_xy(com_filled, win=ma_win)
        ankle_s = moving_average_xy(ankle_filled, win=ma_win)
        # 전체 17개 관절도 동일 정책으로 보간+스무딩
        sm_joints = []
        for j in range(17):
            series_j = [p[j] for p in kpts_raw]
            series_j = interp_xy_series(series_j)
            series_j = moving_average_xy(series_j, win=ma_win)
            sm_joints.append(series_j)
        kpts_series = [np.stack([sm_joints[j][i] for j in range(17)], axis=0) for i in range(len(seq))]
    else:
        com_s   = ema_xy(com_filled, alpha=ema_alpha)
        ankle_s = ema_xy(ankle_filled, alpha=ema_alpha)
        sm_joints = []
        for j in range(17):
            series_j = [p[j] for p in kpts_raw]
            series_j = interp_xy_series(series_j)
            series_j = ema_xy(series_j, alpha=ema_alpha)
            sm_joints.append(series_j)
        kpts_series = [np.stack([sm_joints[j][i] for j in range(17)], axis=0) for i in range(len(seq))]

    # 4) COM 수직 속도
    vy_com = derive_vy(com_s, fps=fps)

    if verbose:
        elapsed = time.time() - t0

    return {
        "times": times,
        "kpts_series": kpts_series,
        "com_series": com_s,
        "ankle_series": ankle_s,
        "vy_com": vy_com,
    }
