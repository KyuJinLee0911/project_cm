# main.py
# 가정: 아래 심벌들은 다른 모듈에서 import됨
# - 상수: LOW_M, HIGH_M
# - IO/모델: load_models, open_video, run_yolov11x_pose
# - 전처리: smooth_series, derive_vy
# - 이벤트: find_drop_start, find_touchdown
# - 높이: estimate_drop_height_COM
# - 낙법분기: extract_contact_times, compute_features, classify_landing_type, evaluate_rules
# - 결과: compose_report, export_result

from step1_io_init import load_models, open_video
from step2_pose_infer import run_yolov11x_pose
from step3_processing import build_step3_outputs
from step4_events import detect_events_with_feet
from step5_height import estimate_drop_height_airtime
from step6_gate import HIGH_M, LOW_M
from step7_rules import classify_landing_type, compute_features, evaluate_rules, extract_contact_times
from step8_report import compose_report, export_result


def main(video_path: str, floor_y: float, scale_y: float, fps: int = 30):
    # 1) 모델/입력 준비
    models = load_models()                    # YOLOv11x-pose 등
    vr = open_video(video_path, force_fps=fps)

    # 2) 포즈 추정 시퀀스 생성 (프레임→키포인트)
    kpts_series = run_yolov11x_pose(vr, models)          # [t] -> np.ndarray(17,2)

    # 3) 스무딩 & 파생량(무게중심, 발목평균, COM 수직속도)
    out3 = build_step3_outputs(kpts_series, smoothing="ma", ma_win=3, fps=fps)
    times        = out3["times"]
    kpts_series  = out3["kpts_series"]
    com_series   = out3["com_series"]
    ankle_series = out3["ankle_series"]
    vy_com       = out3["vy_com"]

        # 4) 이벤트 분할: 낙하 시작/착지 시점
    t_drop, t_touch, meta_evt = detect_events_with_feet(
        com_series, ankle_series, floor_y, fps,
        kpts_series=kpts_series,   # 있으면 전달(없으면 ankle_L/R 직접 전달 가능)
        y_down=True,
        debug=True,
        video_path=video_path,
        # ▼ 추가: 첫 홀드 y 게이트
        hold_y_min=500,         # float 또는 None
    )

    # 5) 낙하 높이 계산(무게중심 기준)
    H_drop, H_sigma, info = estimate_drop_height_airtime(
        com_series, t_drop, t_touch, fps,
        y_down=True,
        # near-floor 제거했으니 아래는 생략해도 됨(호환성 유지만)
        # ankle_series=ankle_series, floor_y=floor_y, floor_eps_px=12.0,
        comp_ms_default=60.0,
        use_v0=True, scale_y=scale_y,
        scale_sigma_ratio=0.03,
        debug=True
    )


    # 6) 높이 게이트 + 자세 피드백 정책
    # 정책:
    #   - H + σ < LOW_M      → low_ok (자세 피드백 생략)
    #   - LOW_M ≤ H ± σ ≤ HIGH_M → use_breakfall (자세 피드백 포함)
    #   - H - σ > HIGH_M     → climb_down + 자세 피드백 포함
    if H_drop + H_sigma < LOW_M:
        # 안전 낮은 높이: 바로 리포트 후 종료
        result = compose_report(
            height_m=H_drop, height_sigma_m=H_sigma,
            gate="low_ok", landing_type=None, checks={}
        )
        return export_result(result)

    # 7) 자세 피드백(공통) — 0.5~1.2, 1.2 초과 모두 수행
    contact_times = extract_contact_times(
        kpts_series,
        floor_y_unused=0.0,      # 미사용
        fps=fps,
        t_feet_canonical=t_touch,
        t_drop_canonical=t_drop,
        y_down=True,
        use_near_feet_check=True,
        video_path=video_path,    # 주면 프레임 저장됨
        save_dir="./example4_events/"
    )
    features      = compute_features(kpts_series, contact_times, fps)
    landing_type  = classify_landing_type(contact_times, features)
    checks        = evaluate_rules(landing_type, contact_times, features, fps)

    # 8) 게이트 결정
    gate = "use_breakfall"
    if H_drop - H_sigma > HIGH_M:
        gate = "climb_down"  # 하강 권고 + 자세 피드백

    # 9) 리포트 출력
    result = compose_report(
        height_m=H_drop, height_sigma_m=H_sigma,
        gate=gate, landing_type=landing_type, checks=checks,
        meta={"t_drop": t_drop, "t_touch": t_touch}
    )
    return export_result(result)


# main.py 최하단 추가
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Falling detection test pipeline")
    parser.add_argument("--video_path", required=True, help="분석할 영상 경로")
    parser.add_argument("--floor_y", type=float, required=True, help="바닥 y 좌표(px)")
    parser.add_argument("--scale_y", type=float, required=True, help="픽셀→미터 스케일 (m/px)")
    parser.add_argument("--fps", type=int, default=30, help="영상 FPS (기본 30)")
    args = parser.parse_args()

    main(
        video_path=args.video_path,
        floor_y=args.floor_y,
        scale_y=args.scale_y,
        fps=args.fps,
    )
