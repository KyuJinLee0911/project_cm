# app/services/detect_service.py
from __future__ import annotations
from typing import List
from fastapi import HTTPException
from ..repositories.session_store import SessionMeta
from ..models.hold_schemas import DetectResp, DetectReq
import numpy as np
import cv2
from ultralytics import YOLO

model = YOLO("C:/Users/SSAFY/Desktop/ClimbMate/S13P31A203/AI/model/climbingcrux_model.pt")

crop_size = 1000
near_distance = 20.0
display_scale = 1  # 화면 표시 축소 비율
smooth_kernel = 9 #외곽선 매끄럽게

# ------------------ 유틸 함수 ------------------
def crop_region(image, center, size):
    cx, cy = center
    h, w = image.shape[:2]
    half = size // 2
    x1, y1 = int(max(0, cx - half)), int(max(0, cy - half))
    x2, y2 = int(min(w, cx + half)), int(min(h, cy + half))
    cropped = image[y1:y2, x1:x2]

    return cropped, (x1,y1)


def expand_box(box, expand_ratio=0.05, image_shape=None):
    x1, y1, x2, y2 = box
    w, h = x2 - x1, y2 - y1
    dw, dh = w * expand_ratio, h * expand_ratio
    x1_new = int(max(0, x1 - dw))
    y1_new = int(max(0, y1 - dh))
    x2_new = int(min(image_shape[1] - 1, x2 + dw))
    y2_new = int(min(image_shape[0] - 1, y2 + dh))
    return x1_new, y1_new, x2_new, y2_new


def extract_polygon(roi, min_hull_length=50):
    """ROI에서 윤곽선 기반 외곽점 추출 (Contour 사용)"""
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)

    edges = cv2.Canny(blur, 70, 120)
    block_size = 11
    thresh = cv2.adaptiveThreshold(blur, 255,
                                   cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, block_size, 2)
    combined = cv2.bitwise_or(edges, thresh)

    kernel = np.ones((3, 3), np.uint8)
    for _ in range(3):
        combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel)
        combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    contour = max(contours, key=cv2.contourArea)
    if cv2.arcLength(contour, True) < min_hull_length:
        return None

    epsilon_ratio = 0.001
    epsilon = epsilon_ratio * cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, epsilon, True)

    # --- 스무딩 ---
    approx = approx.reshape(-1, 2).astype(np.float32)
    smooth_window = 7
    smoothed = []
    half_k = smooth_window // 2
    for i in range(len(approx)):
        start = max(0, i - half_k)
        end = min(len(approx), i + half_k)
        window = approx[start:end]
        smoothed.append(np.mean(window, axis=0))
    smoothed = np.array(smoothed, dtype=np.int32)

    return smoothed


def start_clicking(image_np, click_x, click_y, save_path=None):

    original_img = image_np
    # 이미지를 불러올 수 없습니다
    if original_img is None:
        raise HTTPException(status_code=400, detail="이미지를 불러올 수 없습니다.")
    roi, (rx,ry) = crop_region(original_img, (click_x, click_y), crop_size)
    results = model.predict(roi, conf=0.3, verbose=False)[0]

    if not hasattr(results, "boxes") or results.boxes is None or len(results.boxes) == 0:
        raise HTTPException(status_code=404,detail="탐지된 객체가 없습니다. 이미지 내에서 인식 가능한 객체를 찾을 수 없습니다.")
    
    boxes = results.boxes.xyxy.cpu().numpy()
    classes = results.boxes.cls.cpu().numpy().astype(int)
    names = results.names


    centers = [((b[0]+b[2])/2.0, (b[1]+b[3])/2.0) for b in boxes]
    distances = [np.hypot(cx+rx - click_x, cy+ry - click_y) for (cx, cy) in centers]
    hold_idx = [i for i, c in enumerate(classes) if 'hold' in names[c].lower()]
    chosen_box = None
    if chosen_box is None and hold_idx:
        hold_dists = [distances[i] for i in hold_idx]
        nearest_hold_i = hold_idx[np.argmin(hold_dists)]
        chosen_box = boxes[nearest_hold_i]

    if chosen_box is None:
        raise HTTPException(status_code=404,detail="인식된 홀드가 없습니다. 이미지에서 홀드를 찾을 수 없습니다.")
    

    x1, y1, x2, y2 = chosen_box
    chosen_box_global = [
        x1 + rx, y1 + ry,
        x2 + rx, y2 + ry
    ]

    expanded_box = expand_box(chosen_box_global, image_shape=original_img.shape)
    ex1, ey1, ex2, ey2 = expanded_box
    expanded_roi = original_img[ey1:ey2, ex1:ex2]
    polygon_points = extract_polygon(expanded_roi)
    poly =  polygon_points.tolist() if polygon_points is not None else None  # 좌표 저장
    if polygon_points is not None:
        polygon_global = []
        for p in polygon_points:
            gx = int(p[0] + ex1)
            gy = int(p[1] + ey1)
            polygon_global.append((gx, gy))
        poly = polygon_global
    result = {"polygon": poly, "box": chosen_box_global}
    return result

# # ------------------ 테스트 실행 ------------------
# if __name__ == "__main__":
#     poly = start_clicking("C:/Users/SSAFY/Desktop/ClimbMate/S13P31A203/AI/photo/1.jpg",200,200)
#     print(Polygon(points=poly))
    


    ###########수정하기##################
class DetectService:
    @staticmethod
    def detect_candidates(meta: SessionMeta, req: DetectReq):
        result = start_clicking(meta.image_np, req.x, req.y)
        # 스키마에 맞춰 '단일' 결과 반환
        return DetectResp(polygon=result.get("polygon"), bbox=result.get("box"))
