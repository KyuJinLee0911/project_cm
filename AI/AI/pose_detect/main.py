import cv2
import numpy as np
from yolo11x import detect_people, SKELETON, estimate_body_center
from ultralytics import YOLO
from kalman import KalmanTracker
import torch
video_path = "C:/Users/SSAFY/Desktop/ClimbMate/S13P31A203/AI/video/climbing.mp4"
output_path = "C:/Users/SSAFY/Desktop/ClimbMate/S13P31A203/AI/video/output.mp4"

# YOLOv11x-pose
pose_model = YOLO("C:/Users/SSAFY/Desktop/ClimbMate/S13P31A203/AI/model/yolo11x-pose.pt")
if torch.cuda.is_available():
    pose_model.to("cuda")      # ✅ 모델을 GPU로
    try:
        pose_model.fuse()      # (선택) 레이어 fuse
    except Exception:
        pass
print(f"현재 디바이스: {pose_model.device}")


cap = cv2.VideoCapture(video_path)
native_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
src_w  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
src_h  = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# 스케일(분석/그리기 모두 동일 스케일로 처리)
scale = 0.5
out_size = (int(src_w * scale), int(src_h * scale))

# 저장기(원본 fps로 저장)
fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # mp4
writer = cv2.VideoWriter(output_path, fourcc, native_fps, out_size)

# 칼만 트래커 (dt는 원본 fps 기준으로 고정)
dt = 1.0 / native_fps
tracker = KalmanTracker(num_kp=17, dt=1.0, q=1e-3, r=1e-2, conf_th=0.4, occluded_damp=0.2)
tracker.set_dt(dt)

def draw_skeleton(frame, pts):
    for p1, p2 in SKELETON:
        x1, y1 = pts[p1]; x2, y2 = pts[p2]
        cv2.line(frame, (int(x1), int(y1)), (int(x2), int(y2)), (255,0,0), 2)
    for x, y in pts:
        cv2.circle(frame, (int(x), int(y)), 4, (0,0,0), -1)
    return frame

def recompute_polygon_center_stable(pts):
    lw, rw = pts[9], pts[10]
    la, ra = pts[15], pts[16]
    polygon = np.array([lw, rw, ra, la], np.int32).reshape((-1,1,2))
    body_center = estimate_body_center(pts)
    stable = cv2.pointPolygonTest(polygon, (int(body_center[0]), int(body_center[1])), False) >= 0
    return polygon, body_center, stable

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # 리사이즈(저장 크기와 동일)
    frame = cv2.resize(frame, out_size)

    # 1) 추론: 그리기 없이 키포인트만
    people_raw, _ = detect_people(frame, model=pose_model, draw=False)

    # 2) 칼만 업데이트/예측
    if people_raw:
        pts  = people_raw[0]["keypoints"]
        conf = people_raw[0].get("keypoint_confs", None)
        smoothed_pts = tracker.update(pts, conf=conf, dt=dt)
        
    else:
        smoothed_pts = tracker.predict_only(dt=dt)

    # 3) 스무딩된 좌표로 다시 계산 & 그리기 (초기 미검출 시엔 원본 그대로 저장)
    if smoothed_pts is not None:
        overlay = frame.copy()
        polygon, body_center, stable = recompute_polygon_center_stable(smoothed_pts)

        cv2.polylines(frame, [polygon], True, (0,255,255), 2)
        cv2.fillPoly(overlay, [polygon], (0,255,255))
        frame = cv2.addWeighted(overlay, 0.4, frame, 0.6, 0)

        frame = draw_skeleton(frame, smoothed_pts)

        color = (0,255,0) if stable else (0,0,255)
        cv2.circle(frame, (int(body_center[0]), int(body_center[1])), 6, color, -1)
        cv2.putText(frame, f"Status: {'Stable' if stable else 'Unstable'}", (30, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3)
    
    cv2.imshow("Climbing Pose + Holds (Kalman-Single)", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    # 4) 표시 없이 저장만
    # writer.write(frame)

cap.release()
# writer.release()
cv2.destroyAllWindows()  # 창을 안 띄우므로 불필요
