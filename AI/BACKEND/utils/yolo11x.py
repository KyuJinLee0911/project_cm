# BACKEND/utils/yolo11x.py
from ultralytics import YOLO
import numpy as np
import cv2
import torch

# 17개 키포인트 연결(COCO)
SKELETON = [
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),  # 머리
    (5, 6),
    (6, 11),
    (11, 12),
    (5, 11),  # 몸통
    (5, 7),
    (7, 9),
    (6, 8),
    (8, 10),  # 팔
    (11, 13),
    (13, 15),
    (12, 14),
    (14, 16),  # 다리
]


def estimate_body_center(points):
    """인체 무게중심 추정"""
    weights = {"head": 0.08, "torso": 0.43, "arms": 0.14, "legs": 0.35}

    head = np.mean(points[[0, 1, 2, 3, 4]], axis=0)
    torso = np.mean(points[[5, 6, 11, 12]], axis=0)
    arms = np.mean(points[[7, 8, 9, 10]], axis=0)
    legs = np.mean(points[[13, 14, 15, 16]], axis=0)

    cx = (
        head[0] * weights["head"]
        + torso[0] * weights["torso"]
        + arms[0] * weights["arms"]
        + legs[0] * weights["legs"]
    )
    cy = (
        head[1] * weights["head"]
        + torso[1] * weights["torso"]
        + arms[1] * weights["arms"]
        + legs[1] * weights["legs"]
    )
    return [cx, cy]


# YOLOv11-pose 로더(필요 시 전역으로 한 번만 로드)
def load_pose_model(model_size="n"):
    """
    model_size: 'n','s','m','l','x'
    클라이밍은 손/발 포인트가 중요하니 's' 또는 'm' 추천(속도-정확도 균형)
    """
    ckpt = f"yolo11{model_size}-pose.pt"
    model = YOLO(ckpt)
    # GPU가 있으면 half로 조금 더 빠르게
    if torch.cuda.is_available():
        model.to("cuda")
        try:
            model.fuse()  # 가능하면 layer fuse
        except Exception:
            pass
    return model


def detect_people(
    frame: np.ndarray,
    model: YOLO = None,
    draw: bool = False,
    scale: float = 1.0,
    kp_conf: float = 0.15,
    iou: float = 0.5,
    imgsz: int = 640,
    max_det: int = 10,
):
    """
    사람 감지(+선택적 시각화)
    return: (people, frame)
      - people: list of dict
        {
          "keypoints": (17,2) np.ndarray,
          "hands_feet": [lw, rw, la, ra],
          "polygon": np.ndarray (4,1,2,int32),
          "body_center": (2,),
          "stable": bool,
          "bbox": (x1,y1,x2,y2) or None,
          "keypoint_confs": (17,) or None
        }
    """
    if model is None:
        model = load_pose_model("n")  # 기본: yolo11x-pose.pt

    with torch.inference_mode():
        # v11도 predict 인터페이스 동일
        results = model(
            frame,
            conf=kp_conf,
            iou=iou,
            imgsz=int(imgsz * scale),
            verbose=False,
            max_det=max_det,
        )
        if torch.cuda.is_available():
            torch.cuda.synchronize()

    if not results or len(results) == 0:
        return [], frame

    r0 = results[0]
    keypoints = getattr(r0, "keypoints", None)
    boxes = getattr(results[0], "boxes", None)
    people = []
    if keypoints is None or len(keypoints.xy) == 0:
        return people, frame

    # draw=True일 때만 원본 프레임을 수정
    overlay = frame.copy() if draw else None

    for i, person_xy in enumerate(keypoints.xy):
        pts = person_xy.detach().cpu().numpy()  # (17,2)
        if pts.shape[0] < 17:
            continue

        # 손발 포인트
        left_wrist, right_wrist = pts[9], pts[10]
        left_ankle, right_ankle = pts[15], pts[16]

        # 지지 다각형(손2+발2)
        polygon = np.array(
            [left_wrist, right_wrist, right_ankle, left_ankle], np.int32
        ).reshape((-1, 1, 2))

        # 무게중심 및 안정 여부
        body_center = estimate_body_center(pts)
        stable = (
            cv2.pointPolygonTest(
                polygon, (int(body_center[0]), int(body_center[1])), False
            )
            >= 0
        )

        # keypoint confidence (있을 때만)
        conf = None
        if hasattr(keypoints, "conf") and keypoints.conf is not None:
            try:
                conf = keypoints.conf[i].detach().cpu().numpy()  # (17,)
            except Exception:
                conf = None

        # bbox (원하면 활성화)
        bbox = None
        if boxes is not None and hasattr(boxes, "xyxy") and len(boxes.xyxy) > i:
            try:
                x1, y1, x2, y2 = map(int, boxes.xyxy[i].detach().cpu().numpy())
                bbox = (x1, y1, x2, y2)
            except Exception:
                bbox = None

        person_info = {
            "keypoints": pts,
            "hands_feet": [left_wrist, right_wrist, left_ankle, right_ankle],
            "polygon": polygon,
            "body_center": body_center,
            "stable": stable,
            "bbox": bbox,
            "keypoint_confs": conf,
        }
        people.append(person_info)

        if draw:
            # 지지 다각형
            cv2.polylines(frame, [polygon], True, (0, 255, 255), 2)
            cv2.fillPoly(overlay, [polygon], (0, 255, 255))

            # 스켈레톤
            for p1, p2 in SKELETON:
                x1, y1 = pts[p1]
                x2, y2 = pts[p2]
                cv2.line(frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 0), 2)
            for x, y in pts:
                cv2.circle(frame, (int(x), int(y)), 4, (0, 0, 0), -1)

            # 몸 중심
            cv2.circle(
                frame, (int(body_center[0]), int(body_center[1])), 6, (0, 0, 255), -1
            )

    if draw:
        # 폴리곤 반투명 채움 적용
        frame = cv2.addWeighted(overlay, 0.4, frame, 0.6, 0)

    return people, frame
