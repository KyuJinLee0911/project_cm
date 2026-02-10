import os
import subprocess
import sys
import numpy as np
import cv2

# ======== 경로 설정 ========
BASE_DIR = "C:/Users/SSAFY/Desktop/ClimbMate/S13P31A203/AI"
GRAB_DIR = os.path.join(BASE_DIR, "grab")
FALL_DIR = os.path.join(BASE_DIR, "fall")
SCORE_DIR = os.path.join(BASE_DIR,"score")

# ======== 입력 파일 ========
VIDEO_PATH = os.path.join(BASE_DIR, "video", "1.mp4")
IMG_PATH   = os.path.join(BASE_DIR, "photo", "1.jpg")
HOLDS_VIDEO_PATH = os.path.join(BASE_DIR, "data", "holds_touch.mp4")
OUTPUT_VIDEO_PATH = os.path.join(BASE_DIR, "outputs", "output.mp4")
POSE_MODEL_PATH = os.path.join(BASE_DIR, "model", "yolo11x-pose.pt")
SKELETON_PATH = os.path.join(BASE_DIR, "data", "skeletons.npy")
DATA_PATH = os.path.join(BASE_DIR,"data","touch_data.npy")
HOLDS_PATH = os.path.join(BASE_DIR,"data","clicked_holds.npy")
SCORE_DATA_PATH = os.path.join(BASE_DIR, "data", "score_data.npy")

# ======== 낙하 분석용 파라미터 ========
FLOOR_Y = 900.0
SCALE_Y = 0.0023
FPS = 30

# ======== 실행 함수 ========
def run_grab_module():
    print("\n[1/2] 🧠 Running grab module to extract skeletons...")
    grab_script = os.path.join(GRAB_DIR, "main.py")

    cmd = [
        sys.executable, grab_script,
        "--video_path", VIDEO_PATH,
        "--output_path", HOLDS_VIDEO_PATH,
        "--pose_model_path", POSE_MODEL_PATH,
        "--holds_path", HOLDS_PATH,
        "--skeleton_path",SKELETON_PATH,
        "--data_path",DATA_PATH
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')

    if result.returncode != 0:
        print("[ERROR] grab/main.py 실행 실패 ❌")
        print(result.stderr)
        sys.exit(1)

    print("[OK] grab/main.py 완료 ✅")
    if os.path.exists(SKELETON_PATH):
        print(f"→ 스켈레톤 데이터 저장 완료: {SKELETON_PATH}")
    else:
        print("[WARN] skeletons.npy 파일이 존재하지 않습니다. 경로 확인 필요.")

def run_score_module():
    print("\n[2/3] 🪂 Loading score_data.npy and visualizing...")
    score_script = os.path.join(SCORE_DIR, "main.py")
    cmd = [
        sys.executable, score_script,
        "--video_path", HOLDS_VIDEO_PATH,
        "--skeleton_path", SKELETON_PATH,
        "--data_path", DATA_PATH,
        "--output_data_path", SCORE_DATA_PATH
    ]
    subprocess.run(cmd)
    if not os.path.exists(SCORE_DATA_PATH):
        print("[ERROR] score_data.npy 파일이 없습니다. 먼저 score/main.py를 실행하여 생성하세요.")
        return

    score_data = np.load(SCORE_DATA_PATH, allow_pickle=True)
    print(f"✅ score_data.npy 로드 완료, 프레임 수: {len(score_data)}")

    # 기존 영상 열기
    cap = cv2.VideoCapture(HOLDS_VIDEO_PATH)
    if not cap.isOpened():
        print(f"[ERROR] 영상 파일을 열 수 없습니다: {HOLDS_VIDEO_PATH}")
        return

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(OUTPUT_VIDEO_PATH, fourcc, fps, (w, h))

    print("🎬 score_data 시각화 시작...")

    for frame_idx, frame_info in enumerate(score_data):
        ret, frame = cap.read()
        if not ret:
            break

        # 다각형 그리기
        if frame_info["polygon_points"] is not None:
            pts = np.array(frame_info["polygon_points"], dtype=np.int32).reshape((-1, 1, 2))
            cv2.polylines(frame, [pts], True, (0, 0, 255), 2)

        # 다각형 중심
        if frame_info["polygon_center"] is not None:
            cx, cy = map(int, frame_info["polygon_center"])
            cv2.circle(frame, (cx, cy), 8, (255, 0, 0), -1)
            cv2.putText(frame, "Polygon Center", (cx + 10, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

        # 몸 무게중심
        if frame_info["body_center"] is not None:
            bx, by = map(int, frame_info["body_center"])
            cv2.circle(frame, (bx, by), 6, (0, 255, 0), -1)
            cv2.putText(frame, "Body Center", (bx + 10, by), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # 몸통 각도
        if frame_info["torso_angle"] is not None:
            cv2.putText(frame, f"Torso Angle: {abs(frame_info['torso_angle']):.1f} deg", (50, 130),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 3)

        # 팔/다리 각도
        y_offset = 180
        for joint, angle in frame_info["joint_angles"].items():
            cv2.putText(frame, f"{joint}: {angle:.1f}", (50, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 255), 2)
            y_offset += 30

        # 안정도 점수
        if frame_info["stability_score"] is not None:
            cv2.putText(frame, f"Stability: {frame_info['stability_score']:.1f}", (50, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)

        out.write(frame)

    cap.release()
    out.release()
    cv2.destroyAllWindows()
    print("✅ score_data 시각화 완료:", OUTPUT_VIDEO_PATH)


def run_fall_module():
    print("\n[2/2] 🪂 Running fall_detect module to generate report...")
    fall_script = os.path.join(FALL_DIR, "main.py")

    cmd = [
        sys.executable, fall_script,
        "--video_path", OUTPUT_VIDEO_PATH,
        "--floor_y", str(FLOOR_Y),
        "--scale_y", str(SCALE_Y),
        "--fps", str(FPS)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')

    if result.returncode != 0:
        print("[ERROR] fall_detect/main.py 실행 실패 ❌")
        print(result.stderr)
        sys.exit(1)

    print("[OK] fall_detect/main.py 완료 ✅")
    print(result.stdout)

# ======== 메인 실행 ========
if __name__ == "__main__":
    print("=== 🚀 Full ClimbMate Pipeline Start ===")

    # 1️⃣ Grab 단계
    run_grab_module()

    run_score_module()

    # 2️⃣ Fall Detect 단계
    run_fall_module()

    print("\n=== 🎯 Pipeline Completed Successfully ===")
    print(f"📄 Report saved in: {os.path.join(FALL_DIR, 'example4_events')}")
