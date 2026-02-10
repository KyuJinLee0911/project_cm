# step8_report.py
# 8단계: 결과 리포트 조립 + 내보내기 (진행상황 로그 포함)

from __future__ import annotations
from typing import Dict, Any, Optional
import os
import json
import datetime as dt

def _now_iso() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")

def compose_report(
    *,
    height_m: float,
    height_sigma_m: float,
    gate: str,                      # "low_ok" | "use_breakfall" | "climb_down"
    landing_type: Optional[str],    # "back" | "rolling" | "uncertain" | None
    checks: Dict[str, Any],         # step7_rules.evaluate_rules 결과 (또는 {})
    meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    파이프라인 결과를 일관된 JSON 구조로 조립합니다.
    """
    summary_msg = {
        "low_ok": "0.5m 미만: 자유 착지 권고(기본 수칙 확인).",
        "use_breakfall": "0.5~1.2m: 낙법 평가 구간.",
        "climb_down": "1.2m 초과: 한 단 더 내려와 착지 권고."
    }.get(gate, "분류 불명")

    report: Dict[str, Any] = {
        "generated_at": _now_iso(),
        "summary": {
            "gate": gate,
            "message": summary_msg,
            "height_m": float(round(height_m, 4)),
            "height_sigma_m": float(round(height_sigma_m, 4)),
            "landing_type": landing_type
        },
        "checks": checks or {},
        "meta": meta or {}
    }
    return report


def _format_txt_summary(report: Dict[str, Any]) -> str:
    s = report.get("summary", {})
    checks = report.get("checks", {})
    meta = report.get("meta", {})

    lines = []
    lines.append(f"[Falling Report] generated_at={report.get('generated_at','')}")
    lines.append(f"- Gate: {s.get('gate')}  |  {s.get('message')}")
    lines.append(f"- Height: {s.get('height_m')} ± {s.get('height_sigma_m')} m")
    lines.append(f"- Landing Type: {s.get('landing_type')}")
    if meta:
        td = meta.get("t_drop", None)
        tt = meta.get("t_touch", None)
        lines.append(f"- Events: t_drop={td}, t_touch={tt}")

    if checks:
        lines.append("- Checks:")
        for k, v in checks.items():
            pv = v.get("pass", None)
            pv_str = "PASS" if pv is True else ("FAIL" if pv is False else "N/A")
            lines.append(f"   · {k}: {pv_str}  { {kk:vv for kk,vv in v.items() if kk!='pass'} }")
    return "\n".join(lines)


def export_result(
    report: Dict[str, Any],
    out_dir: str = "./outputs",
    base_name: str = "report"
) -> Dict[str, Any]:
    """
    report.json / report.txt 저장 + 콘솔 요약 출력.
    반환: {
        "json_path": ".../report.json",
        "txt_path":  ".../report.txt",
        "summary":   report["summary"]
    }
    """
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, f"{base_name}.json")
    txt_path  = os.path.join(out_dir, f"{base_name}.txt")

    # JSON 저장
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # TXT 요약 저장
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(_format_txt_summary(report))

    # 콘솔 요약
    s = report["summary"]

    return {
        "json_path": json_path,
        "txt_path": txt_path,
        "summary": s
    }
