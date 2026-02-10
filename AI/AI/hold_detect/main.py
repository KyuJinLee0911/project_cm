import cv2
import os
import numpy as np
from ultralytics import YOLO

# ------------------ 모델 로드 ------------------
model = YOLO("C:/Users/SSAFY/Desktop/ClimbMate/S13P31A203/AI/model/climbingcrux_model.pt")

crop_size = 1000
near_distance = 20.0
display_scale = 1  # 화면 표시 축소 비율
smooth_kernel = 9 #외곽선 매끄럽게

clicked_holds = []

# ------------------ 유틸 함수 ------------------
def crop_region(image, center, size):
    cx, cy = center
    h, w = image.shape[:2]
    half = size // 2
    x1, y1 = max(0, cx - half), max(0, cy - half)
    x2, y2 = min(w, cx + half), min(h, cy + half)
    cropped = image[y1:y2, x1:x2]
    rel_x = cx - x1
    rel_y = cy - y1
    return cropped, x1, y1, (rel_x, rel_y)


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

# ------------------ 클릭 로직 ------------------
def get_clicked_holds():
    return clicked_holds


def start_clicking(img_path, save_path=None):
    global clicked_holds
    clicked_holds = []

    original_img = cv2.imread(img_path)
    if original_img is None:
        print("❌ 이미지를 불러올 수 없습니다:", img_path)
        return

    display_img = original_img.copy()
    resized_display = cv2.resize(display_img, None, fx=display_scale, fy=display_scale)

    click_stages = ["시작 홀드", "탑 홀드", "나머지 홀드들"]
    stage_idx = 0
    print(f"Step 1: {click_stages[stage_idx]}을 클릭하세요.")

    def mouse_callback(event, x, y, flags, param):
        nonlocal stage_idx, display_img
        if event != cv2.EVENT_LBUTTONDOWN:
            return

        orig_x, orig_y = int(x / display_scale), int(y / display_scale)
        roi, x_offset, y_offset, rel_click = crop_region(original_img, (orig_x, orig_y), crop_size)
        click_x, click_y = rel_click

        results = model.predict(roi, conf=0.3, verbose=False)[0]
        if not hasattr(results, "boxes") or results.boxes is None or len(results.boxes) == 0:
            print("탐지된 객체 없음")
            return

        boxes = results.boxes.xyxy.cpu().numpy()
        classes = results.boxes.cls.cpu().numpy().astype(int)
        names = results.names
        centers = [((b[0]+b[2])/2.0, (b[1]+b[3])/2.0) for b in boxes]
        distances = [np.hypot(cx - click_x, cy - click_y) for (cx, cy) in centers]

        hold_idx = [i for i, c in enumerate(classes) if 'hold' in names[c].lower()]

        chosen_box, chosen_type, chosen_center, chosen_dist = None, None, None, None

        if chosen_box is None and hold_idx:
            hold_dists = [distances[i] for i in hold_idx]
            nearest_hold_i = hold_idx[np.argmin(hold_dists)]
            nearest_hold_dist = hold_dists[np.argmin(hold_dists)]
            chosen_box = boxes[nearest_hold_i]
            chosen_type = "hold"
            chosen_center = centers[nearest_hold_i]
            chosen_dist = nearest_hold_dist

        if chosen_box is None:
            print("인식된 홀드 없음")
            return

        expanded_box = expand_box(chosen_box[:4], image_shape=roi.shape)
        ex1, ey1, ex2, ey2 = expanded_box
        expanded_roi = roi[int(ey1):int(ey2), int(ex1):int(ex2)]

        polygon_points = extract_polygon(expanded_roi)

        x1, y1, x2, y2 = chosen_box[:4]
        x1 += x_offset
        x2 += x_offset
        y1 += y_offset
        y2 += y_offset
        cx_global = int((x1 + x2) / 2)
        cy_global = int((y1 + y2) / 2)

        entry = {
            "type": chosen_type,
            "box": (int(x1), int(y1), int(x2), int(y2)),
            "center": (cx_global, cy_global),
            "distance": float(chosen_dist),
            "click": (orig_x, orig_y),
            "polygon": polygon_points.tolist() if polygon_points is not None else None  # 좌표 저장
        }

        if polygon_points is not None:
            polygon_global = []
            for p in polygon_points:
                gx = int(p[0] + ex1 + x_offset)
                gy = int(p[1] + ey1 + y_offset)
                polygon_global.append((gx, gy))
            entry["polygon"] = polygon_global
            
            # 시각화
            for i in range(len(polygon_global)):
                pt1 = polygon_global[i]
                pt2 = polygon_global[(i+1) % len(polygon_global)]
                cv2.line(display_img, pt1, pt2, (0, 0, 255), 2)
                cv2.circle(display_img, pt1, 2, (0, 0, 255), -1)
            print(f"✅ 윤곽선 추출 완료 (점 {len(polygon_global)}개)")

        clicked_holds.append(entry)
        print(f"{click_stages[stage_idx]} 저장됨. 총 {len(clicked_holds)}개")

        if stage_idx < 2:
            stage_idx += 1
            print(f"Step {stage_idx+1}: {click_stages[stage_idx]} 클릭하세요.")

        color = (0, 255, 0)
        cv2.rectangle(display_img, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
        cv2.circle(display_img, (orig_x, orig_y), 6, (0, 0, 255), -1)

        resized_display = cv2.resize(display_img, None, fx=display_scale, fy=display_scale)
        cv2.imshow("image", resized_display)

    cv2.namedWindow("image", cv2.WINDOW_AUTOSIZE)
    cv2.imshow("image", resized_display)
    cv2.setMouseCallback("image", mouse_callback)

    while True:
        key = cv2.waitKey(1)
        if key == 27:  # ESC 종료
            break

    cv2.destroyAllWindows()

    if save_path is None:
        save_path = os.path.join("C:/Users/SSAFY/Desktop/ClimbMate/S13P31A203/AI/data", "clicked_holds.npy")
    np.save(save_path, clicked_holds, allow_pickle=True)
    print(f"\n💾 클릭된 홀드 정보가 저장되었습니다: {save_path}")


# ------------------ 테스트 실행 ------------------
if __name__ == "__main__":
    start_clicking("C:/Users/SSAFY/Desktop/ClimbMate/S13P31A203/AI/photo/1.jpg")
