import cv2
import numpy as np
import torch
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pose_detect.yolo11x import detect_people, SKELETON
from ultralytics import YOLO
from pose_detect.kalman import KalmanTracker
import argparse

# ---- 인자 파싱 ----
parser = argparse.ArgumentParser()
parser.add_argument("--video_path", type=str, required=True)
parser.add_argument("--output_path", type=str, required=True)
parser.add_argument("--pose_model_path", type=str, required=True)
parser.add_argument("--holds_path", type=str, required=True)
parser.add_argument("--skeleton_path", type=str, required=True)
parser.add_argument("--data_path", type=str, required=True)
args = parser.parse_args()

VIDEO_PATH = args.video_path
OUTPUT_PATH = args.output_path
POSE_MODEL_PATH = args.pose_model_path
HOLDS_PATH = args.holds_path
SKELETON_PATH = args.skeleton_path
DATA_PATH = args.data_path

# ---- 상수 ----
MIN_ANGLE = 160
MAX_ANGLE = 200
STRETCH_LEG = 1.4

CONF_TH = 0.7
HOLD_TIMEOUT = 1.0
RELEASE_DETECT = 1.5
HOLD_DETECT = 0.5

# ---- 스켈레톤 및 터치 데이터 ----
all_skeletons = []
touch_data = []

# ---- 관절 번호 ----
LEFT_SHOULDER, RIGHT_SHOULDER = 5, 6
LEFT_ELBOW, RIGHT_ELBOW = 7, 8
LEFT_WRIST, RIGHT_WRIST = 9, 10
LEFT_HIP, RIGHT_HIP = 11, 12
LEFT_KNEE, RIGHT_KNEE = 13, 14
LEFT_ANKLE, RIGHT_ANKLE = 15, 16

# ---- 홀드 불러오기 ----
selected_holds = np.load(HOLDS_PATH, allow_pickle=True)

# ---- YOLO Pose 모델 ----
pose_model = YOLO(POSE_MODEL_PATH)
if torch.cuda.is_available():
    pose_model.to("cuda")
    try:
        pose_model.fuse()
    except Exception:
        pass

# ---- 비디오 설정 ----
cap = cv2.VideoCapture(VIDEO_PATH)
native_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
src_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
src_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
out_size = (src_w, src_h)
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
writer = cv2.VideoWriter(OUTPUT_PATH, fourcc, native_fps, out_size)

# ---- Kalman Tracker ----
dt = 1.0 / native_fps
tracker = KalmanTracker(num_kp=17, dt=1.0, q=1e-3, r=1e-2, conf_th=CONF_TH, occluded_damp=0.2)
tracker.set_dt(dt)

# ---- 상태 변수 ----
prev_limb_pos = [None, None, None, None]
current_hold_idx = [None, None, None, None]
overlap_time = [0, 0, 0, 0]
release_time = [0, 0, 0, 0]

start_hold_time = 0.0
top_hold_time = 0.0
show_visuals = False

# ---- 함수 정의 (손/발 박스 계산, 스켈레톤, 시각화 등) ----
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
    leg_len = max(np.linalg.norm(pts[LEFT_HIP] - pts[LEFT_KNEE]), np.linalg.norm(pts[RIGHT_HIP] - pts[RIGHT_KNEE]))
    return max(1.0, shoulder_dist / 170.0, leg_len / 170.0)

def get_limb_radius(pts):
    shoulder_dist = np.linalg.norm(pts[RIGHT_SHOULDER] - pts[LEFT_SHOULDER])
    return shoulder_dist * 0.3

def get_hand_box(elbow, wrist, hand_size, overlap_ratio=0.3):
    vec = wrist - elbow
    length = np.linalg.norm(vec)
    vec_unit = np.array([0,1]) if length < 1e-5 else vec / length
    perp = np.array([-vec_unit[1], vec_unit[0]])
    half_size = hand_size / 2
    wrist_adj = wrist - vec_unit * hand_size * overlap_ratio
    top_left = wrist_adj - perp * half_size + vec_unit * hand_size
    top_right = wrist_adj + perp * half_size + vec_unit * hand_size
    bottom_left = wrist_adj - perp * half_size
    bottom_right = wrist_adj + perp * half_size
    pts = np.array([top_left, top_right, bottom_right, bottom_left], dtype=np.int32)
    x1, y1 = np.min(pts[:,0]), np.min(pts[:,1])
    x2, y2 = np.max(pts[:,0]), np.max(pts[:,1])
    return (int(x1), int(y1), int(x2), int(y2)), pts

LEG_STRAIGHT_ANGLE_TH = 20
STRETCH_LEG = 1.4

def is_leg_straight(hip, knee, ankle, angle_th=LEG_STRAIGHT_ANGLE_TH, limb_radius=30):
    vec_hip_knee = knee - hip
    vec_knee_ankle = ankle - knee
    cos_theta = np.dot(vec_hip_knee, vec_knee_ankle) / (np.linalg.norm(vec_hip_knee)*np.linalg.norm(vec_knee_ankle)+1e-5)
    angle = np.degrees(np.arccos(np.clip(cos_theta, -1.0, 1.0)))
    vec_hip_ankle = ankle - hip
    proj_len = np.dot(vec_hip_knee, vec_hip_ankle) / (np.linalg.norm(vec_hip_ankle) + 1e-5)
    proj_point = hip + (vec_hip_ankle / np.linalg.norm(vec_hip_ankle)) * proj_len
    knee_offset = np.linalg.norm(knee - proj_point)
    return abs(180 - angle) <= angle_th or knee_offset < limb_radius

def get_foot_box(hip, knee, ankle, foot_length, foot_width, scale, limb_radius=30, overlap_ratio=0.3):
    vec_thigh = knee - hip
    vec_leg = ankle - knee
    vec_leg_unit = vec_leg / (np.linalg.norm(vec_leg)+1e-5)
    cos_theta = np.dot(vec_thigh, vec_leg) / (np.linalg.norm(vec_thigh)*np.linalg.norm(vec_leg)+1e-5)
    angle = np.degrees(np.arccos(np.clip(cos_theta, -1.0, 1.0)))
    if angle < 180 - LEG_STRAIGHT_ANGLE_TH or angle > 180 + LEG_STRAIGHT_ANGLE_TH:
        ankle = knee + vec_leg_unit * STRETCH_LEG * scale * np.linalg.norm(vec_leg)
    ankle_adj = ankle - vec_leg_unit * foot_length * overlap_ratio
    if is_leg_straight(hip, knee, ankle_adj, angle_th=LEG_STRAIGHT_ANGLE_TH, limb_radius=limb_radius):
        x1 = int(ankle_adj[0]-foot_width/2); y1 = int(ankle_adj[1])
        x2 = int(ankle_adj[0]+foot_width/2); y2 = int(ankle_adj[1]+foot_length)
    else:
        cross = vec_thigh[0]*vec_leg[1] - vec_thigh[1]*vec_leg[0]
        if cross >= 0:
            x1 = int(ankle_adj[0]); y1 = int(ankle_adj[1]-foot_width/2)
            x2 = int(ankle_adj[0]+foot_length); y2 = int(ankle_adj[1]+foot_width/2)
        else:
            x1 = int(ankle_adj[0]-foot_length); y1 = int(ankle_adj[1]-foot_width/2)
            x2 = int(ankle_adj[0]); y2 = int(ankle_adj[1]+foot_width/2)
    return (x1, y1, x2, y2)

def get_center(box):
    x1,y1,x2,y2 = box
    return np.array([(x1+x2)/2,(y1+y2)/2])

def point_in_polygon(point, polygon):
    if polygon is None or len(polygon) < 3: return False
    poly_np = np.array(polygon, dtype=np.int32)
    return cv2.pointPolygonTest(poly_np, point, False) >= 0

def get_closest_overlapping_hold(limb_box, hold_list):
    limb_center = get_center(limb_box)
    min_dist = float('inf')
    closest_idx = None
    for i, hold in enumerate(hold_list):
        if hold.get("polygon") is not None and point_in_polygon(limb_center, hold["polygon"]):
            hold_center = get_center(hold["box"])
            dist = np.linalg.norm(limb_center - hold_center)
            if dist < min_dist:
                min_dist = dist
                closest_idx = i
    return closest_idx

def draw_skeleton(frame, pts):
    for p1,p2 in SKELETON:
        x1,y1 = pts[p1]; x2,y2 = pts[p2]
        cv2.line(frame,(int(x1),int(y1)),(int(x2),int(y2)),(255,0,0),2)
    for x,y in pts:
        cv2.circle(frame,(int(x),int(y)),4,(0,0,0),-1)
    return frame

def draw_visuals(frame, smoothed_pts, selected_holds, current_hold_idx, hand_polys, foot_boxes):
    frame_out = frame.copy()
    if smoothed_pts is not None: frame_out = draw_skeleton(frame_out, smoothed_pts)
    for i, hold in enumerate(selected_holds):
        if hold.get("polygon") is not None:
            pts = np.array(hold["polygon"], dtype=np.int32)
            color = (0,0,255) if i in current_hold_idx else (0,255,0)
            cv2.polylines(frame_out, [pts.reshape((-1,1,2))], isClosed=True, color=color, thickness=2)
    for bx in foot_boxes: cv2.rectangle(frame_out, (bx[0],bx[1]), (bx[2],bx[3]), (0,255,255), 2)
    for poly in hand_polys: 
        if poly is not None: cv2.polylines(frame_out, [poly.reshape((-1,1,2))], isClosed=True, color=(0,255,255), thickness=2)
    return frame_out

# ---- 영상 처리 루프 ----
frame_idx = 0
while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break

    people_raw,_ = detect_people(frame, model=pose_model, draw=False)
    if people_raw:
        pts = people_raw[0]["keypoints"]
        conf = people_raw[0].get("keypoint_confs", None)
        smoothed_pts = tracker.update(pts, conf=conf, dt=dt)
    else:
        smoothed_pts = tracker.predict_only(dt=dt)

    all_skeletons.append({
        "time": frame_idx / native_fps,
        "kpts": smoothed_pts.copy() if smoothed_pts is not None else np.zeros((17,2))
    })
    frame_idx += 1

    hand_polys = []
    foot_boxes = []
    frame_touches = []

    if smoothed_pts is not None:
        person_scale = get_person_scale(smoothed_pts)
        hand_size = get_hand_size(smoothed_pts, person_scale)
        foot_length, foot_width = get_foot_size(smoothed_pts, person_scale)
        LIMB_RADIUS = get_limb_radius(smoothed_pts)

        limb_boxes = [
            get_hand_box(smoothed_pts[LEFT_ELBOW], smoothed_pts[LEFT_WRIST], hand_size)[0],
            get_hand_box(smoothed_pts[RIGHT_ELBOW], smoothed_pts[RIGHT_WRIST], hand_size)[0],
            get_foot_box(smoothed_pts[LEFT_HIP], smoothed_pts[LEFT_KNEE], smoothed_pts[LEFT_ANKLE], foot_length, foot_width, person_scale),
            get_foot_box(smoothed_pts[RIGHT_HIP], smoothed_pts[RIGHT_KNEE], smoothed_pts[RIGHT_ANKLE], foot_length, foot_width, person_scale)
        ]
        hand_polys = [
            get_hand_box(smoothed_pts[LEFT_ELBOW], smoothed_pts[LEFT_WRIST], hand_size)[1],
            get_hand_box(smoothed_pts[RIGHT_ELBOW], smoothed_pts[RIGHT_WRIST], hand_size)[1]
        ]
        foot_boxes = limb_boxes[2:]
        dt_frame = 1.0 / native_fps

        for i, limb_box in enumerate(limb_boxes):
            limb_center = get_center(limb_box)
            if prev_limb_pos[i] is None: prev_limb_pos[i] = limb_center

            limb_conf = None
            if conf is not None:
                if i==0: limb_conf = conf[LEFT_WRIST]
                elif i==1: limb_conf = conf[RIGHT_WRIST]
                elif i==2: limb_conf = conf[LEFT_ANKLE]
                elif i==3: limb_conf = conf[RIGHT_ANKLE]

            idx = get_closest_overlapping_hold(limb_box, selected_holds)

            if idx is not None and (limb_conf is None or limb_conf > CONF_TH * person_scale):
                overlap_time[i] += dt_frame
                release_time[i] = 0
                if overlap_time[i] >= HOLD_DETECT and current_hold_idx[i] != idx:
                    current_hold_idx[i] = idx
                    print(f"손/발 {i} 새 홀드 잡음: {idx}")
            else:
                overlap_time[i] = 0
                release_time[i] += dt_frame
                if current_hold_idx[i] is not None and release_time[i] >= RELEASE_DETECT:
                    print(f"손/발 {i} 홀드 놓음")
                    current_hold_idx[i] = None
                    release_time[i] = 0

            prev_limb_pos[i] = limb_center

            frame_touches.append({
                "frame": frame_idx,
                "limb_id": i,
                "hold_idx": current_hold_idx[i],
                "hold_box": selected_holds[current_hold_idx[i]]["box"] if current_hold_idx[i] is not None else None,
                "limb_center": limb_center.tolist()
            })

        # start/top 홀드 시간 계산
        if current_hold_idx[0] == 0 and current_hold_idx[1] == 0:
            start_hold_time += dt_frame
        else:
            start_hold_time = 0.0

        if current_hold_idx[0] == 1 and current_hold_idx[1] == 1:
            top_hold_time += dt_frame
        else:
            top_hold_time = 0.0

    touch_data.append(frame_touches)

    # 시각화 여부 결정
    if start_hold_time >= 3.0 and top_hold_time < 2.0:
        show_visuals = True
    elif top_hold_time >= 2.0:
        show_visuals = False
    show_visuals = True

    frame_to_show = draw_visuals(frame, smoothed_pts, selected_holds, current_hold_idx, hand_polys, foot_boxes) if show_visuals else frame
    writer.write(frame_to_show)
    cv2.imshow("ClimbMate", frame_to_show)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
writer.release()
cv2.destroyAllWindows()

# ---- npy 저장 ----
np.save(SKELETON_PATH, all_skeletons, allow_pickle=True)
np.save(DATA_PATH, np.array(touch_data, dtype=object), allow_pickle=True)

print(f"✅ 스켈레톤 npy 파일 저장 완료: {SKELETON_PATH}")
print(f"✅ touch_data npy 파일 저장 완료: {DATA_PATH}")
