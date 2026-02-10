# score/main.py (데이터 저장용 버전)
import numpy as np
import cv2
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pose_detect.yolo11x import estimate_body_center
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--video_path", type=str, required=True)
parser.add_argument("--skeleton_path", type=str, required=True)
parser.add_argument("--data_path", type=str, required=True)
parser.add_argument("--output_data_path", type=str, required=True)
args = parser.parse_args()

VIDEO_PATH = args.video_path
SKELETON_PATH = args.skeleton_path
DATA_PATH = args.data_path
OUTPUT_DATA_PATH = args.output_data_path

touch_data = np.load(DATA_PATH, allow_pickle=True)
skeletons = np.load(SKELETON_PATH, allow_pickle=True)
print(f"✅ touch_data: {len(touch_data)}개 프레임, skeletons: {len(skeletons)}개 프레임 로드 완료")

cap = cv2.VideoCapture(VIDEO_PATH)
if not cap.isOpened():
    raise IOError(f"영상 파일을 열 수 없습니다: {VIDEO_PATH}")

w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)
fourcc = cv2.VideoWriter_fourcc(*'XVID')

def calc_stability_score(com, poly_center, polygon):
    if len(polygon) < 3:
        return 0
    avg_dist = np.mean(np.linalg.norm(polygon - poly_center, axis=1))
    com_dist = np.linalg.norm(com - poly_center)
    score = max(0, 100 - (com_dist / (avg_dist + 1e-6)) * 100)
    return np.clip(score, 0, 100)

def calc_angle(a, b, c):
    ba = a - b
    bc = c - b
    cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
    angle = np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))
    return angle

draw_order = [0, 1, 3, 2]
frame_idx = 0
score_data = []

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_info = {
        "body_center": None,
        "polygon_center": None,
        "polygon_points": None,
        "torso_angle": None,
        "joint_angles": {},
        "stability_score": None
    }

    body_center = None
    torso_angle = None

    if frame_idx < len(skeletons):
        frame_data = skeletons[frame_idx]
        if isinstance(frame_data, dict) and "kpts" in frame_data:
            keypoints = np.array(frame_data["kpts"])[:, :2]

            # 무게중심
            body_center = estimate_body_center(keypoints)
            frame_info["body_center"] = body_center.tolist()

            # 몸통 각도
            if len(keypoints) >= 17:
                l_shoulder, r_shoulder = keypoints[5], keypoints[6]
                l_hip, r_hip = keypoints[11], keypoints[12]
                shoulder_center = (l_shoulder + r_shoulder) / 2
                hip_center = (l_hip + r_hip) / 2
                vec = hip_center - shoulder_center
                vertical = np.array([0, 1])
                angle_rad = np.arccos(np.clip(np.dot(vec, vertical) / (np.linalg.norm(vec) + 1e-6), -1.0, 1.0))
                torso_angle = np.degrees(angle_rad)
                if vec[0] < 0:
                    torso_angle *= -1
                frame_info["torso_angle"] = torso_angle

            # 관절 각도
            joints = {
                "L_Elbow": (5, 7, 9),
                "R_Elbow": (6, 8, 10),
                "L_Knee": (11, 13, 15),
                "R_Knee": (12, 14, 16)
            }
            for name, (a, b, c) in joints.items():
                if np.all(keypoints[[a, b, c]] > 0):
                    angle = calc_angle(keypoints[a], keypoints[b], keypoints[c])
                    frame_info["joint_angles"][name] = angle

    # 터치 데이터
    current_touches = []
    for frame_touches in touch_data:
        if len(frame_touches) > 0 and frame_touches[0]["frame"] == frame_idx:
            current_touches = frame_touches
            break

    limb_points = []
    for limb_id in draw_order:
        for touch in current_touches:
            if touch["limb_id"] == limb_id:
                cx, cy = map(int, touch["limb_center"])
                limb_points.append([cx, cy])
                break

    # 다각형 및 중심
    polygon_center = None
    if len(limb_points) >= 3:
        polygon_np = np.array(limb_points, dtype=np.float32)
        polygon_center = np.mean(polygon_np, axis=0)
        frame_info["polygon_center"] = polygon_center.tolist()
        frame_info["polygon_points"] = polygon_np.tolist()

    # 안정도 점수
    if body_center is not None and polygon_center is not None and len(limb_points) >= 3:
        score = calc_stability_score(np.array(body_center), np.array(polygon_center), np.array(limb_points))
        frame_info["stability_score"] = score

    score_data.append(frame_info)
    frame_idx += 1

cap.release()
cv2.destroyAllWindows()

# 데이터 저장
os.makedirs(os.path.dirname(OUTPUT_DATA_PATH), exist_ok=True)
np.save(OUTPUT_DATA_PATH, score_data, allow_pickle=True)
print("✅ 모든 프레임 데이터 저장 완료:", OUTPUT_DATA_PATH)
