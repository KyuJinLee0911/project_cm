# BACKEND/utils/kalman.py
import numpy as np
from collections import deque
import cv2


def bbox_from_keypoints(pts, margin=4):
    x1, y1 = np.min(pts, axis=0)
    x2, y2 = np.max(pts, axis=0)
    return int(x1 - margin), int(y1 - margin), int(x2 + margin), int(y2 + margin)


def iou(b1, b2):
    x1 = max(b1[0], b2[0])
    y1 = max(b1[1], b2[1])
    x2 = min(b1[2], b2[2])
    y2 = min(b1[3], b2[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    a1 = max(0, b1[2] - b1[0]) * max(0, b1[3] - b1[1])
    a2 = max(0, b2[2] - b2[0]) * max(0, b2[3] - b2[1])
    uni = a1 + a2 - inter + 1e-6
    return inter / uni


class Kalman2D:
    def __init__(self, dt=1 / 30.0, q=1e-4, r=1e-1):
        self.kf = cv2.KalmanFilter(4, 2)
        self.set_dt(dt)
        self.kf.measurementMatrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], np.float32)
        self.kf.processNoiseCov = np.eye(4, dtype=np.float32) * q
        self.kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * r
        self.kf.errorCovPost = np.eye(4, dtype=np.float32)

    def set_dt(self, dt):
        self.kf.transitionMatrix = np.array(
            [[1, 0, dt, 0], [0, 1, 0, dt], [0, 0, 1, 0], [0, 0, 0, 1]], np.float32
        )

    def init(self, x, y):
        self.kf.statePost = np.array([[x], [y], [0.0], [0.0]], np.float32)

    def predict(self):
        return self.kf.predict()

    def correct(self, x, y):
        meas = np.array([[float(x)], [float(y)]], np.float32)
        return self.kf.correct(meas)

    def state_xy(self):
        s = self.kf.statePost.ravel()
        return float(s[0]), float(s[1])

    def damp_velocity(self, factor=0.5):
        self.kf.statePost[2, 0] *= factor
        self.kf.statePost[3, 0] *= factor


# 17키포인트용 칼만 + 선형보간
class KalmanKeypoints:
    HEAD_IDXS = [0, 1, 2, 3, 4]  # 머리 키포인트

    def __init__(self, num_kp=17, dt=1 / 30.0, q=1e-4, r=1e-1):
        self.num_kp = num_kp
        self.filters = [Kalman2D(dt, q, r) for _ in range(num_kp)]
        self.initialized = False
        self._last_out = None
        self._history = deque(maxlen=10)  # 최근 좌표 저장
        self._history_conf = deque(maxlen=10)  # 최근 신뢰도 저장

    def set_dt(self, dt):
        for f in self.filters:
            f.set_dt(dt)

    def init(self, pts, conf=None):
        pts = np.asarray(pts, dtype=np.float32)
        for i, (x, y) in enumerate(pts):
            self.filters[i].init(x, y)
        self.initialized = True
        self._last_out = pts.copy()
        self._history.append(pts.copy())
        if conf is not None:
            self._history_conf.append(np.asarray(conf, dtype=np.float32))
        else:
            self._history_conf.append(np.ones(self.num_kp, dtype=np.float32))

    # 선형 보간
    def interpolate(self, idx, conf_th=0.4):
        # 이전 좌표
        prev_pts = self._history[-2] if len(self._history) > 1 else self._last_out
        prev_conf = (
            self._history_conf[-2]
            if len(self._history_conf) > 1
            else np.ones(self.num_kp)
        )
        curr_pts = self._history[-1]
        curr_conf = self._history_conf[-1]
        out = curr_pts.copy()
        for i in range(self.num_kp):
            if i in self.HEAD_IDXS:
                continue  # 머리는 항상 현재 관측 그대로
            if curr_conf[i] < conf_th:
                # 이전이 유효하면 직선 보간
                out[i] = 0.5 * prev_pts[i] + 0.5 * curr_pts[i]
        return out

    def update(self, pts, conf=None, conf_th=0.4, occluded_damp=0.2, gate_px=60):
        if not self.initialized:
            self.init(pts, conf)
        pts = np.asarray(pts, dtype=np.float32)
        if conf is None:
            conf_vec = np.ones(self.num_kp)
        else:
            conf_vec = np.asarray(conf, dtype=np.float32).reshape(-1)
        out = np.zeros_like(pts, dtype=np.float32)

        # 저장
        self._history.append(pts.copy())
        self._history_conf.append(conf_vec.copy())

        # 칼만 예측 + 보정
        for i in range(self.num_kp):
            f = self.filters[i]
            f.predict()

            # 머리는 항상 YOLO 따라감
            if i in self.HEAD_IDXS or conf_vec[i] >= conf_th:
                f.correct(pts[i, 0], pts[i, 1])
            else:
                # 저신뢰 → 선형 보간 좌표 사용
                interp_pts = self.interpolate(i, conf_th=conf_th)
                f.correct(interp_pts[i, 0], interp_pts[i, 1])
                f.damp_velocity(occluded_damp)
            out[i] = f.state_xy()

        self._last_out = out.copy()
        return out


class KalmanTracker:
    def __init__(
        self, num_kp=17, dt=1 / 30.0, q=1e-4, r=1e-1, conf_th=0.4, occluded_damp=0.2
    ):
        self.kp_filter = KalmanKeypoints(num_kp=num_kp, dt=dt, q=q, r=r)
        self.conf_th = conf_th
        self.occluded_damp = occluded_damp
        self.initialized = False
        self.last_pts = None

    def set_dt(self, dt):
        self.kp_filter.set_dt(dt)

    def update(self, pts, conf=None, dt=None):
        if dt is not None:
            self.set_dt(dt)
        out = self.kp_filter.update(
            pts, conf=conf, conf_th=self.conf_th, occluded_damp=self.occluded_damp
        )
        self.initialized = True
        self.last_pts = out
        return out

    def predict_only(self, dt=None):
        if dt is not None:
            self.set_dt(dt)
        if not self.initialized:
            return None
        outs = []
        for f in self.kp_filter.filters:
            f.predict()
            f.damp_velocity(self.occluded_damp)
            outs.append(f.state_xy())
        out = np.array(outs, dtype=np.float32)
        self.last_pts = out
        return out
