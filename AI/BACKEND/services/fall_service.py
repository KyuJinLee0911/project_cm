# BACKEND/services/fall_service.py
from __future__ import annotations
import numpy as np

from BACKEND.logic.falling.calculate_height import estimate_drop_height_airtime
from BACKEND.logic.falling.detect_falling import detect_events_with_feet
from BACKEND.logic.falling.report import (
    evaluate_rules_message,
    extract_contact_times,
    get_landing_order,
)

from ..models.analysis_schemas import DropAnalysis


def run(
    kpts_series: np.ndarray,
    com_series: np.ndarray,
    start_climbing_frame: int,
    end_climbing_frame: int,
    fps: int = 24,
) -> DropAnalysis:

    print("\n[fall_service.run] 호출")
    print(f"  - fps={fps}")
    if kpts_series is None:
        raise RuntimeError("kpts_series is None")

    print(f"  - kpts_series.shape={getattr(kpts_series, 'shape', None)}")
    print(f"  - com_series.shape={getattr(com_series, 'shape', None)}")
    print(f"  - start_climbing_frame={start_climbing_frame}")

    # 1) 낙하 구간 탐지
    t_drop, t_touch = detect_events_with_feet(
        com_series=com_series,
        fps=fps,
        kpts_series=kpts_series,
        start_climbing_frame=start_climbing_frame,
        end_climbing_frame=end_climbing_frame,
    )
    print(
        f"[fall_service.run] detect_events_with_feet -> t_drop={t_drop}, t_touch={t_touch}"
    )

    # 2) 낙하 높이 추정
    H_drop, H_sigma = estimate_drop_height_airtime(
        t_drop,
        t_touch,
        fps,
    )
    print(
        f"[fall_service.run] estimate_drop_height_airtime -> H_drop={H_drop:.4f}, H_sigma={H_sigma:.4f}"
    )

    # 3) 낮은 낙하: 조기 종료
    if H_drop + H_sigma < 0.5:
        print(
            f"[fall_service.run] 낮은 낙하 조기 종료: {H_drop:.3f} + {H_sigma:.3f} < 0.5"
        )
        return DropAnalysis(
            t_drop=t_drop,
            t_touch=t_touch,
            message="낮은 낙하의 경우 조기 종료",
            landing_sequence=["feet"],  # 최소 정보
        )

        # 4) 부위별 착지 타이밍 추출
    contact_times = extract_contact_times(
        kpts_series,
        fps=fps,
        t_feet_canonical=t_touch,
        t_drop_canonical=t_drop,
    )
    print(
        f"[fall_service.run] extract_contact_times -> "
        f"feet={contact_times.get('feet')}, "
        f"hip={contact_times.get('hip')}, "
        f"back={contact_times.get('back')}"
    )

    # 5) 순서 계산
    landing_sequence = get_landing_order(contact_times)
    print(f"[fall_service.run] get_landing_order -> {landing_sequence}")

    # 6) 코칭 메시지 생성
    message = evaluate_rules_message(contact_times)

    print("[fall_service.run] DropAnalysis.message 미리보기:")
    print("  " + message.replace("\n", " / "))

    result = DropAnalysis(
        t_drop=t_drop,
        t_touch=t_touch,
        message=message,
        landing_sequence=landing_sequence,
    )
    print("[fall_service.run] DropAnalysis 생성 완료\n")
    return result
