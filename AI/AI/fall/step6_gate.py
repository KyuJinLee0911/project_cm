# step6_gate.py
# 6단계: 높이 게이트 임계/헬퍼 + 진행 로그

# ── 게이트 임계값(메인에서 사용)
LOW_M  = 0.50   # 0.5 m 미만: 자유 착지 권고
HIGH_M = 1.20   # 1.2 m 초과: 한 단 더 내려오라고 권고

def gate_by_height(H_drop: float, H_sigma: float):
    """
    높이 기반 게이트 및 코멘트 리턴.
    return: (gate, message)
      gate ∈ {"low_ok", "use_breakfall", "climb_down"}
    """
    lo, hi = LOW_M, HIGH_M

    if H_drop + H_sigma < lo:
        msg = "0.5m 미만(신뢰도 고려): 그냥 내려와도 무방합니다. 기본 안전 수칙만 확인하세요."
        return "low_ok", msg

    if H_drop - H_sigma > hi:
        msg = "1.2m 초과(신뢰도 고려): 한 단 더 내려와서 착지하세요."
        return "climb_down", msg

    msg = "0.5~1.2m 구간: 낙법 평가(규칙 기반)가 필요합니다."
    return "use_breakfall", msg
