# BACKEND/services/skeleton_analyzer.py
from __future__ import annotations

from typing import List

import cv2
import numpy as np
from fastapi import HTTPException
from ultralytics import YOLO

from ..models.analysis_schemas import FrameAnalysis, FrameMetrics
from ..utils.kalman import KalmanTracker
from ..utils.yolo11x import detect_people, estimate_body_center

# TODO: 환경설정/경로는 설정 파일로 분리하는 것이 바람직
pose_model = YOLO(
    "C:/Users/SSAFY/Desktop/ClimbMate/S13P31A203/AI/model/yolo11x-pose.pt"
)


def run(video_path: str, holds: List[dict], fps: int = 24):
    results: List[FrameAnalysis] = []

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise HTTPException(status_code=400, detail="비디오 파일을 열 수 없습니다.")

    # 등반 시작/종료 프레임
    start_climbing_frame = 0
    end_climbing_frame = 0

    # 하이퍼파라미터
    STRETCH_LEG = 1.4
    CONF_TH = 0.7
    RELEASE_DETECT = 1.5
    HOLD_DETECT = 0.5
    LEG_STRAIGHT_ANGLE_TH = 20

    # 스켈레톤 / 무게중심 / 터치 데이터 저장
    all_skeletons = []  # 각 프레임별 (17, 2) keypoints
    body_centers = []  # 각 프레임별 body center (또는 [0,0])

    touch_data = []

    # 관절 인덱스 (COCO 기반 가정)
    LEFT_SHOULDER, RIGHT_SHOULDER = 5, 6
    LEFT_ELBOW, RIGHT_ELBOW = 7, 8
    LEFT_WRIST, RIGHT_WRIST = 9, 10
    LEFT_HIP, RIGHT_HIP = 11, 12
    LEFT_KNEE, RIGHT_KNEE = 13, 14
    LEFT_ANKLE, RIGHT_ANKLE = 15, 16

    # 홀드 목록
    selected_holds = holds

    # 비디오 FPS
    native_fps = fps

    # Kalman Tracker 초기화
    dt = 1.0 / native_fps
    tracker = KalmanTracker(
        num_kp=17,
        dt=1.0,
        q=1e-3,
        r=1e-2,
        conf_th=CONF_TH,
        occluded_damp=0.2,
    )
    tracker.set_dt(dt)

    # 상태 변수들
    # 손/발: [L_hand, R_hand, L_foot, R_foot]
    prev_limb_pos = [None, None, None, None]
    current_hold_idx = [None, None, None, None]
    overlap_time = [0.0, 0.0, 0.0, 0.0]
    release_time = [0.0, 0.0, 0.0, 0.0]

    start_hold_time = 0.0
    top_hold_time = 0.0

    average_score = 0.0

    # tri/quad polygon 그릴 때 limb 순서
    draw_order = [0, 1, 3, 2]

    # ================= 유틸 함수들 =================

    def get_hand_size(pts, scale):
        shoulder_dist = np.linalg.norm(pts[RIGHT_SHOULDER] - pts[LEFT_SHOULDER])
        return max(20, int(shoulder_dist * 0.4 * scale))

    def get_foot_size(pts, scale):
        left_leg_len = np.linalg.norm(pts[LEFT_KNEE] - pts[LEFT_ANKLE])
        right_leg_len = np.linalg.norm(pts[RIGHT_KNEE] - pts[RIGHT_ANKLE])
        foot_length = max(20, int(max(left_leg_len, right_leg_len) * 0.5 * scale))
        foot_width = max(10, int(foot_length * 0.45))
        return foot_length, foot_width

    def get_person_scale(pts):
        shoulder_dist = np.linalg.norm(pts[RIGHT_SHOULDER] - pts[LEFT_SHOULDER])
        leg_len = max(
            np.linalg.norm(pts[LEFT_HIP] - pts[LEFT_KNEE]),
            np.linalg.norm(pts[RIGHT_HIP] - pts[RIGHT_KNEE]),
        )
        return max(1.0, shoulder_dist / 170.0, leg_len / 170.0)

    def get_hand_box(elbow, wrist, hand_size, overlap_ratio=0.3):
        vec = wrist - elbow
        length = np.linalg.norm(vec)
        vec_unit = np.array([0, 1]) if length < 1e-5 else vec / length
        perp = np.array([-vec_unit[1], vec_unit[0]])
        half_size = hand_size / 2

        wrist_adj = wrist - vec_unit * hand_size * overlap_ratio

        top_left = wrist_adj - perp * half_size + vec_unit * hand_size
        top_right = wrist_adj + perp * half_size + vec_unit * hand_size
        bottom_left = wrist_adj - perp * half_size
        bottom_right = wrist_adj + perp * half_size

        pts = np.array(
            [top_left, top_right, bottom_right, bottom_left],
            dtype=np.int32,
        )
        x1, y1 = np.min(pts[:, 0]), np.min(pts[:, 1])
        x2, y2 = np.max(pts[:, 0]), np.max(pts[:, 1])
        return (int(x1), int(y1), int(x2), int(y2)), pts

    def is_leg_straight(
        hip,
        knee,
        ankle,
        angle_th=LEG_STRAIGHT_ANGLE_TH,
        limb_radius=30,
    ):
        vec_hip_knee = knee - hip
        vec_knee_ankle = ankle - knee
        cos_theta = np.dot(vec_hip_knee, vec_knee_ankle) / (
            np.linalg.norm(vec_hip_knee) * np.linalg.norm(vec_knee_ankle) + 1e-5
        )
        angle = np.degrees(np.arccos(np.clip(cos_theta, -1.0, 1.0)))

        vec_hip_ankle = ankle - hip
        proj_len = np.dot(vec_hip_knee, vec_hip_ankle) / (
            np.linalg.norm(vec_hip_ankle) + 1e-5
        )
        proj_point = (
            hip + (vec_hip_ankle / (np.linalg.norm(vec_hip_ankle) + 1e-5)) * proj_len
        )
        knee_offset = np.linalg.norm(knee - proj_point)

        return abs(180 - angle) <= angle_th or knee_offset < limb_radius

    def get_foot_box(
        hip,
        knee,
        ankle,
        foot_length,
        foot_width,
        scale,
        limb_radius=30,
        overlap_ratio=0.3,
    ):
        vec_thigh = knee - hip
        vec_leg = ankle - knee
        vec_leg_unit = vec_leg / (np.linalg.norm(vec_leg) + 1e-5)

        cos_theta = np.dot(vec_thigh, vec_leg) / (
            np.linalg.norm(vec_thigh) * np.linalg.norm(vec_leg) + 1e-5
        )
        angle = np.degrees(np.arccos(np.clip(cos_theta, -1.0, 1.0)))

        if angle < 180 - LEG_STRAIGHT_ANGLE_TH or angle > 180 + LEG_STRAIGHT_ANGLE_TH:
            ankle = knee + vec_leg_unit * STRETCH_LEG * scale * np.linalg.norm(vec_leg)

        ankle_adj = ankle - vec_leg_unit * foot_length * overlap_ratio

        if is_leg_straight(
            hip,
            knee,
            ankle_adj,
            angle_th=LEG_STRAIGHT_ANGLE_TH,
            limb_radius=limb_radius,
        ):
            x1 = int(ankle_adj[0] - foot_width / 2)
            y1 = int(ankle_adj[1])
            x2 = int(ankle_adj[0] + foot_width / 2)
            y2 = int(ankle_adj[1] + foot_length)
        else:
            cross = vec_thigh[0] * vec_leg[1] - vec_thigh[1] * vec_leg[0]
            if cross >= 0:
                x1 = int(ankle_adj[0])
                y1 = int(ankle_adj[1] - foot_width / 2)
                x2 = int(ankle_adj[0] + foot_length)
                y2 = int(ankle_adj[1] + foot_width / 2)
            else:
                x1 = int(ankle_adj[0] - foot_length)
                y1 = int(ankle_adj[1] - foot_width / 2)
                x2 = int(ankle_adj[0])
                y2 = int(ankle_adj[1] + foot_width / 2)

        return (x1, y1, x2, y2)

    def get_center(box):
        x1, y1, x2, y2 = box
        return np.array(
            [(x1 + x2) / 2.0, (y1 + y2) / 2.0],
            dtype=np.float32,
        )

    def point_in_polygon(point, polygon):
        if polygon is None or len(polygon) < 3:
            return False
        poly_np = np.array(polygon, dtype=np.float32).reshape(-1, 1, 2)
        x, y = float(point[0]), float(point[1])
        res = cv2.pointPolygonTest(poly_np, (x, y), False)
        return res >= 0

    def box_poly_overlap(box, polygon):
        """
        limb_box (axis-aligned rect) 와 홀드 polygon 이
        한 점이라도 겹치면 True.
        """
        if polygon is None or len(polygon) < 3:
            return False

        x1, y1, x2, y2 = box
        poly_np = np.array(polygon, dtype=np.float32).reshape(-1, 2)

        # 0. AABB 빠른 탈락 조건
        poly_x_min, poly_y_min = np.min(poly_np[:, 0]), np.min(poly_np[:, 1])
        poly_x_max, poly_y_max = np.max(poly_np[:, 0]), np.max(poly_np[:, 1])

        if x2 < poly_x_min or x1 > poly_x_max or y2 < poly_y_min or y1 > poly_y_max:
            return False

        # 1. 박스 네 꼭짓점 중 하나라도 폴리곤 내부에 있는지
        box_pts = np.array(
            [[x1, y1], [x2, y1], [x2, y2], [x1, y2]],
            dtype=np.float32,
        )
        poly_cv = poly_np.reshape(-1, 1, 2)
        for px, py in box_pts:
            res = cv2.pointPolygonTest(poly_cv, (float(px), float(py)), False)
            if res >= 0:
                return True

        # 2. 폴리곤의 꼭짓점 중 하나라도 박스 내부에 있는지
        inside_box = (
            (poly_np[:, 0] >= x1)
            & (poly_np[:, 0] <= x2)
            & (poly_np[:, 1] >= y1)
            & (poly_np[:, 1] <= y2)
        )
        if np.any(inside_box):
            return True

        # 3. 변-변 교차 검사 (박스 네 변 vs 폴리곤 각 변)
        def ccw(a, b, c):
            return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])

        def segments_intersect(p1, p2, q1, q2):
            return ccw(p1, q1, q2) != ccw(p2, q1, q2) and ccw(p1, p2, q1) != ccw(
                p1, p2, q2
            )

        # 박스 변들
        box_edges = [
            (box_pts[0], box_pts[1]),
            (box_pts[1], box_pts[2]),
            (box_pts[2], box_pts[3]),
            (box_pts[3], box_pts[0]),
        ]

        # 폴리곤 변들
        n = len(poly_np)
        for i in range(n):
            p1 = poly_np[i]
            p2 = poly_np[(i + 1) % n]
            for q1, q2 in box_edges:
                if segments_intersect(p1, p2, q1, q2):
                    return True

        return False

    def get_closest_overlapping_hold(limb_box, hold_list):
        """
        limb_box와 홀드 폴리곤이 겹치는 홀드 중,
        limb_center와 가장 가까운 홀드를 반환.
        """
        limb_center = get_center(limb_box)
        min_dist = float("inf")
        closest_idx = None

        for i, hold in enumerate(hold_list):
            poly = hold.get("polygon")
            box = hold.get("box")
            if poly is None or box is None or len(poly) < 3:
                continue

            # ✅ 센터 기준이 아니라, 실제 겹침 여부로 판정
            if box_poly_overlap(limb_box, poly):
                hold_center = get_center(box)
                dist = np.linalg.norm(limb_center - hold_center)
                if dist < min_dist:
                    min_dist = dist
                    closest_idx = i

        return closest_idx

    def calc_stability_score(com, poly_center, polygon):
        if len(polygon) < 3:
            return 0.0
        avg_dist = np.mean(np.linalg.norm(polygon - poly_center, axis=1))
        com_dist = np.linalg.norm(com - poly_center)
        score = max(
            0.0,
            100.0 - (com_dist / (avg_dist + 1e-6)) * 100.0,
        )
        return float(np.clip(score, 0.0, 100.0))

    def calc_angle(a, b, c):
        ba = a - b
        bc = c - b
        cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
        angle = np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))
        return angle

    def calc_torso_score(torso_angle, max_angle=90):
        deviation = abs(torso_angle)
        norm = min(deviation / max_angle, 1.0)
        score = 100.0 * (1.0 - norm**1.5)
        return round(
            float(np.clip(score, 0.0, 100.0)),
            1,
        )

    def calc_joint_score(
        joint_angles,
    ):
        ideal = 130.0
        tolerance = 40.0
        scores = []

        for angle in joint_angles:
            diff = abs(angle - ideal)
            if diff > tolerance:
                score = max(
                    0.0,
                    100.0 - (diff - tolerance) * 2.0,
                )
            else:
                score = 100.0 - (diff / tolerance) * 20.0
            scores.append(float(np.clip(score, 0.0, 100.0)))

        if not scores:
            return None
        return float(np.mean(scores))

    # ================= 메인 루프 =================

    frame_idx = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        conf = None

        # 사람 / 포즈 탐지
        people_raw, _ = detect_people(
            frame,
            model=pose_model,
            draw=False,
        )

        if people_raw:
            pts = people_raw[0]["keypoints"]
            conf = people_raw[0].get("keypoint_confs", None)
            smoothed_pts = tracker.update(pts, conf=conf, dt=dt)
        else:
            smoothed_pts = tracker.predict_only(dt=dt)

        if smoothed_pts is None:
            smoothed_pts = np.zeros(
                (17, 2),
                dtype=np.float32,
            )

        smoothed_pts = np.array(
            smoothed_pts,
            dtype=np.float32,
        )

        # 프레임별 skeleton 저장
        all_skeletons.append(smoothed_pts)

        frame_touches = []

        # ---------------- 터치 / 홀드 매칭 ----------------
        if smoothed_pts is not None:
            person_scale = get_person_scale(smoothed_pts)
            hand_size = get_hand_size(
                smoothed_pts,
                person_scale,
            )
            foot_length, foot_width = get_foot_size(
                smoothed_pts,
                person_scale,
            )

            limb_boxes = [
                # Left hand
                get_hand_box(
                    smoothed_pts[LEFT_ELBOW],
                    smoothed_pts[LEFT_WRIST],
                    hand_size,
                )[0],
                # Right hand
                get_hand_box(
                    smoothed_pts[RIGHT_ELBOW],
                    smoothed_pts[RIGHT_WRIST],
                    hand_size,
                )[0],
                # Left foot
                get_foot_box(
                    smoothed_pts[LEFT_HIP],
                    smoothed_pts[LEFT_KNEE],
                    smoothed_pts[LEFT_ANKLE],
                    foot_length,
                    foot_width,
                    person_scale,
                ),
                # Right foot
                get_foot_box(
                    smoothed_pts[RIGHT_HIP],
                    smoothed_pts[RIGHT_KNEE],
                    smoothed_pts[RIGHT_ANKLE],
                    foot_length,
                    foot_width,
                    person_scale,
                ),
            ]

            dt_frame = 1.0 / native_fps

            for limb_id, limb_box in enumerate(limb_boxes):
                limb_center = get_center(limb_box)
                if prev_limb_pos[limb_id] is None:
                    prev_limb_pos[limb_id] = limb_center

                # keypoint conf 매칭
                limb_conf = None
                if conf is not None:
                    if limb_id == 0:
                        limb_conf = conf[LEFT_WRIST]
                    elif limb_id == 1:
                        limb_conf = conf[RIGHT_WRIST]
                    elif limb_id == 2:
                        limb_conf = conf[LEFT_ANKLE]
                    elif limb_id == 3:
                        limb_conf = conf[RIGHT_ANKLE]

                idx = get_closest_overlapping_hold(
                    limb_box,
                    selected_holds,
                )

                if idx is not None and (
                    limb_conf is None or limb_conf > CONF_TH * person_scale
                ):
                    overlap_time[limb_id] += dt_frame
                    release_time[limb_id] = 0.0

                    if (
                        overlap_time[limb_id] >= HOLD_DETECT
                        and current_hold_idx[limb_id] != idx
                    ):
                        current_hold_idx[limb_id] = idx
                else:
                    overlap_time[limb_id] = 0.0
                    release_time[limb_id] += dt_frame

                    if (
                        current_hold_idx[limb_id] is not None
                        and release_time[limb_id] >= RELEASE_DETECT
                    ):
                        current_hold_idx[limb_id] = None
                        release_time[limb_id] = 0.0

                prev_limb_pos[limb_id] = limb_center

                frame_touches.append(
                    {
                        "frame": frame_idx,
                        "limb_id": limb_id,
                        "hold_idx": current_hold_idx[limb_id],
                        "limb_center": limb_center.tolist(),
                    }
                )

            # ---------------- start/top 홀드 시간 ----------------
            left_idx = current_hold_idx[0]
            right_idx = current_hold_idx[1]

            left_hold = selected_holds[left_idx] if left_idx is not None else None
            right_hold = selected_holds[right_idx] if right_idx is not None else None

            # 왼손 또는 오른손이 start 홀드를 잡고 있는가?
            on_start = (left_hold is not None and left_hold.get("type") == "start") or (
                right_hold is not None and right_hold.get("type") == "start"
            )

            if on_start:
                start_hold_time += dt_frame
            else:
                start_hold_time = 0.0

            # 왼손 또는 오른손이 top 홀드를 잡고 있는가?
            on_top = (left_hold is not None and left_hold.get("type") == "top") or (
                right_hold is not None and right_hold.get("type") == "top"
            )

            if on_top:
                top_hold_time += dt_frame
            else:
                top_hold_time = 0.0

            left_type = left_hold.get("type") if left_hold else None
            right_type = right_hold.get("type") if right_hold else None

            print(
                f"[frame {frame_idx}] "
                f"L_idx={left_idx}, R_idx={right_idx}, "
                f"L_type={left_type}, R_type={right_type}, "
                f"on_start={on_start}, on_top={on_top}, "
                f"start_hold_time={start_hold_time:.2f}, "
                f"top_hold_time={top_hold_time:.2f}"
            )

        touch_data.append(frame_touches)

        # ---------------- 등반 구간 판정 ----------------
        if start_climbing_frame == 0 and start_hold_time >= 1.0 and top_hold_time < 1.0:
            start_climbing_frame = frame_idx
        elif end_climbing_frame == 0 and top_hold_time >= 1.0:
            end_climbing_frame = frame_idx

        # ---------------- 몸통/관절/안정성 메트릭 ----------------
        keypoints = smoothed_pts
        torso_angle = None
        joint_angles = []

        # 몸통 각도
        if len(keypoints) >= 17:
            l_shoulder = keypoints[LEFT_SHOULDER]
            r_shoulder = keypoints[RIGHT_SHOULDER]
            l_hip = keypoints[LEFT_HIP]
            r_hip = keypoints[RIGHT_HIP]

            shoulder_center = (l_shoulder + r_shoulder) / 2.0
            hip_center = (l_hip + r_hip) / 2.0

            vec = hip_center - (shoulder_center)
            vertical = np.array(
                [0.0, 1.0],
                dtype=np.float32,
            )

            denom = np.linalg.norm(vec) + 1e-6
            torso_angle = np.degrees(
                np.arccos(
                    np.clip(
                        np.dot(
                            vec,
                            vertical,
                        )
                        / denom,
                        -1.0,
                        1.0,
                    )
                )
            )
            if vec[0] < 0:
                torso_angle *= -1.0

        # 관절 각도
        joints = {
            "L_Elbow": (
                LEFT_SHOULDER,
                LEFT_ELBOW,
                LEFT_WRIST,
            ),
            "R_Elbow": (
                RIGHT_SHOULDER,
                RIGHT_ELBOW,
                RIGHT_WRIST,
            ),
            "L_Knee": (
                LEFT_HIP,
                LEFT_KNEE,
                LEFT_ANKLE,
            ),
            "R_Knee": (
                RIGHT_HIP,
                RIGHT_KNEE,
                RIGHT_ANKLE,
            ),
        }

        for (
            _name,
            (a, b, c),
        ) in joints.items():
            if np.all(keypoints[[a, b, c]] > 0):
                joint_angles.append(
                    calc_angle(
                        keypoints[a],
                        keypoints[b],
                        keypoints[c],
                    )
                )

        # 현재 프레임 터치 기반 polygon
        current_touches = touch_data[-1]

        limb_points = []
        for limb_id in draw_order:
            for touch in current_touches:
                if touch["limb_id"] == limb_id:
                    cx, cy = map(
                        int,
                        touch["limb_center"],
                    )
                    limb_points.append([cx, cy])
                    break

        if len(limb_points) >= 3:
            polygon_np = np.array(
                limb_points,
                dtype=np.float32,
            )
            polygon_center = np.mean(
                polygon_np,
                axis=0,
            )
        else:
            polygon_np = np.zeros(
                (0, 2),
                dtype=np.float32,
            )
            polygon_center = None

        body_center = estimate_body_center(smoothed_pts)
        if body_center is not None:
            body_center_arr = np.array(
                body_center,
                dtype=np.float32,
            )
        else:
            # 저장/리턴 시 편의를 위해 [0,0]으로 대체
            body_center_arr = np.array(
                [0.0, 0.0],
                dtype=np.float32,
            )

        # 안정도 점수
        if (
            body_center is not None
            and polygon_center is not None
            and len(limb_points) >= 3
        ):
            score = calc_stability_score(
                body_center_arr,
                polygon_center,
                polygon_np,
            )
            inside = cv2.pointPolygonTest(
                polygon_np.astype(np.int32),
                (
                    float(body_center_arr[0]),
                    float(body_center_arr[1]),
                ),
                False,
            )
            stability = "stable" if inside >= 0 else "unstable"
        else:
            score = 0.0
            stability = "unstable"
            polygon_np = np.zeros(
                (0, 2),
                dtype=np.float32,
            )

        joint_score = calc_joint_score(joint_angles) or 0.0
        torso_score = calc_torso_score(torso_angle) if torso_angle is not None else 0.0
        avg = (score + torso_score + joint_score) / 3.0
        analysis_result = FrameMetrics(
            tilt_pct=torso_score,
            flexion_pct=joint_score,
            com_pct=score,
            avg_pct=avg,
            stability=stability,
        )

        tri_quad_center = (
            polygon_center.tolist() if polygon_center is not None else [0.0, 0.0]
        )

        result = FrameAnalysis(
            frame_idx=frame_idx,
            skeleton=smoothed_pts.tolist(),
            tri_quad=polygon_np.tolist(),
            body_center=body_center_arr.tolist(),
            tri_quad_center=tri_quad_center,
            metrics=analysis_result,
            start_climbing_frame=start_climbing_frame,
            end_climbing_frame=end_climbing_frame,
        )
        average_score += avg
        body_centers.append(body_center_arr)
        results.append(result)
        frame_idx += 1
    average_score /= frame_idx
    cap.release()

    return (
        results,
        np.array(all_skeletons),
        np.array(body_centers),
        start_climbing_frame,
        end_climbing_frame,
        average_score,
    )
