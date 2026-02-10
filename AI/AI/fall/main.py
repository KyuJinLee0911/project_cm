# main.py
import os
import numpy as np
from step3_processing import build_step3_outputs
from step4_events import detect_events_with_feet
from step5_height import estimate_drop_height_airtime
from step6_gate import LOW_M, HIGH_M
from step7_rules import (
    extract_contact_times,
    compute_features,
    classify_landing_type,
    evaluate_rules,
)
from step8_report import compose_report, export_result


def run_pipeline(skeleton_path: str, fps: int = 60):

    if not os.path.exists(skeleton_path):
        raise FileNotFoundError(f"스켈레톤 데이터가 없습니다: {skeleton_path}")

    seq = np.load(skeleton_path, allow_pickle=True)

    # 여기 다 자세 인식한 쪽에서 다 받아와야함
    out3 = build_step3_outputs(seq, smoothing="ma", ma_win=3, fps=fps)
    kpts_series  = out3["kpts_series"]
    com_series   = out3["com_series"]


    # ✅ Step 4: 낙하 이벤트 감지
    t_drop, t_touch = detect_events_with_feet(
        com_series=com_series,
        fps=fps,
        kpts_series=kpts_series,
        # hold_y_min= 여기에 최저 홀드 값 받아와야함
    )

    # ✅ Step 5: 낙하 높이 및 체공시간 추정
    H_drop, H_sigma= estimate_drop_height_airtime(
        com_series,
        t_drop,
        t_touch,
        fps,
    )

    # ✅ Step 6: 낮은 낙하의 경우 조기 종료
    if H_drop + H_sigma < LOW_M:
        result = compose_report(
            height_m=H_drop,
            height_sigma_m=H_sigma,
            gate="low_ok",
            landing_type=None,
            checks={},
        )
        return export_result(result)

    # ✅ Step 7: 착지 분석
    contact_times = extract_contact_times(
        kpts_series,
        fps=fps,
        t_feet_canonical=t_touch,
        t_drop_canonical=t_drop,
    )
    features     = compute_features(kpts_series, contact_times, fps)
    landing_type = classify_landing_type(contact_times, features)
    checks       = evaluate_rules(landing_type, contact_times, features, fps)

    # ✅ Step 8: 게이트 결정 및 리포트 생성
    gate = "use_breakfall"
    if H_drop - H_sigma > HIGH_M:
        gate = "climb_down"

    result = compose_report(
        height_m=H_drop,
        height_sigma_m=H_sigma,
        gate=gate,
        landing_type=landing_type,
        checks=checks,
        meta={"t_drop": t_drop, "t_touch": t_touch},
    )

    return export_result(result)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("--fps", type=int, default=60, help="영상 FPS (기본 60)")
    args = parser.parse_args()

    run_pipeline(
        fps=args.fps,
    )
