"""
SemiProcess MCP Server - 사용자 입력 기반 분석 도구 집합
"""

from typing import Any, Dict, List, Optional
import math
import statistics
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

app = FastAPI(title="SemiProcess MCP Server")

DISCLAIMER = """
📌 안내: 본 분석 결과는 사용자가 입력한 데이터를 기반으로 생성되었습니다.
실제 의사결정 시 현장 상황과 전문가 검토를 병행하세요.
"""


# ===== 공통 유틸 =====
def _missing_required(required: List[str], provided: Dict[str, Any]) -> List[str]:
    return [field for field in required if provided.get(field) is None]


def _format_missing(missing: List[str]) -> str:
    items = "\n".join([f"- `{m}`" for m in missing])
    return f"{DISCLAIMER}\n\n## ⚠️ 입력 오류\n필수 입력이 누락되었습니다.\n{items}"


def _pct_diff(a: float, b: float) -> float:
    if b == 0:
        return 0.0
    return (a - b) / b * 100


def _weighted_score(values: Dict[str, float], weights: Dict[str, float]) -> float:
    if not values:
        return 0.0
    total_weight = sum(weights.get(k, 1.0) for k in values.keys()) or 1.0
    score = sum(values.get(k, 0.0) * weights.get(k, 1.0) for k in values.keys())
    return score / total_weight


def _margin_score(value: float, low: float, high: float) -> float:
    # 남은 마진을 기준으로 위험도 점수 계산 (0~100, 가까울수록 높음)
    if high == low:
        return 100.0
    if value < low or value > high:
        return 100.0
    dist = min(value - low, high - value)
    span = (high - low) / 2
    if span == 0:
        return 100.0
    ratio = 1 - (dist / span)
    return max(0.0, min(100.0, ratio * 100))


# ===== Tool 구현 함수들 =====
def analyze_defect(
    defect_code: str,
    defect_description: str,
    process_step: str,
    equipment_id: str = None,
    wafer_id: str = None,
    known_causes: Optional[List[str]] = None,
    recent_changes: Optional[List[str]] = None,
) -> str:
    required = ["defect_code", "defect_description", "process_step"]
    provided = {
        "defect_code": defect_code,
        "defect_description": defect_description,
        "process_step": process_step,
    }
    missing = _missing_required(required, provided)
    if missing:
        return _format_missing(missing)

    general_checks = [
        "장비 상태/알람 로그 확인",
        "최근 PM/캘리브레이션 이력 검토",
        "레시피 변경 이력 및 버전 확인",
        "소재/케미컬 Lot 변경 여부",
        "SPC/Lot 간 편차 확인",
    ]
    causes = known_causes or []
    changes = recent_changes or []
    cause_matrix = "\n".join([f"| 사용자 제안 원인 | {c} |" for c in causes]) if causes else "| 사용자 제안 원인 | - |"
    general_matrix = "\n".join([f"| 일반 점검 | {c} |" for c in general_checks])
    change_list = "\n".join([f"- {c}" for c in changes]) if changes else "- 최근 변경 없음 보고"

    return (
        f"{DISCLAIMER}\n\n"
        f"## 🔍 불량 분석 결과\n"
        f"- **불량 코드**: {defect_code}\n"
        f"- **불량 설명**: {defect_description}\n"
        f"- **공정 단계**: {process_step}\n"
        f"- **장비 ID**: {equipment_id or '미입력'}\n"
        f"- **웨이퍼 ID**: {wafer_id or '미입력'}\n\n"
        f"### 원인 분석 매트릭스\n"
        f"| 구분 | 내용 |\n|------|------|\n"
        f"{cause_matrix}\n"
        f"{general_matrix}\n\n"
        f"### 최근 변경 사항\n{change_list}\n\n"
        f"### 조사 우선순위 제안\n"
        f"1. 최근 변경/작업 항목 역추적\n"
        f"2. 장비 알람 및 센서 로그 확인\n"
        f"3. 동일 Lot/인접 Lot 비교 분석\n"
        f"4. 레시피 파라미터 편차 검증\n\n"
        f"### 체크리스트\n"
        f"- [ ] 현상 위치 패턴 맵 확인\n"
        f"- [ ] 장비 상태(압력/온도/유량) 정상 범위 검증\n"
        f"- [ ] 소모품 교체 주기 확인\n"
        f"- [ ] 클린룸 환경/입자 모니터링 기록 확인\n"
    )


def get_defect_history(
    defect_records: List[Dict[str, Any]],
    analysis_type: str = "trend",
) -> str:
    required = ["defect_records"]
    provided = {"defect_records": defect_records}
    missing = _missing_required(required, provided)
    if missing:
        return _format_missing(missing)

    if not isinstance(defect_records, list) or len(defect_records) == 0:
        return (
            f"{DISCLAIMER}\n\n## ⚠️ 입력 오류\n"
            f"불량 이력(`defect_records`)은 1개 이상 객체 배열이어야 합니다."
        )

    total = len(defect_records)
    wafer_sum = sum(r.get("wafer_count", 0) for r in defect_records)
    actions = [r.get("action_taken", "") for r in defect_records if r.get("action_taken")]
    unique_actions = list({a for a in actions})

    equip_counter: Dict[str, int] = {}
    for r in defect_records:
        eq = r.get("equipment_id", "미입력")
        equip_counter[eq] = equip_counter.get(eq, 0) + 1
    top_equipment = sorted(equip_counter.items(), key=lambda x: x[1], reverse=True)
    top_equipment_text = "\n".join([f"- {eq}: {cnt}회" for eq, cnt in top_equipment[:3]]) or "- 데이터 부족"

    rows = [
        f"| {r.get('date','-')} | {r.get('defect_type','-')} | {r.get('equipment_id','-')} | {r.get('wafer_count','-')} | {r.get('action_taken','-')} | {r.get('result','-')} |"
        for r in defect_records
    ]
    table = "\n".join(rows)

    return (
        f"{DISCLAIMER}\n\n"
        f"## 📊 불량 이력 분석 ({analysis_type})\n"
        f"### 데이터 개요\n"
        f"- 총 이력: {total}건\n"
        f"- 불량 웨이퍼 합계: {wafer_sum}매\n"
        f"- 사용된 조치: {', '.join(unique_actions) if unique_actions else '조치 정보 부족'}\n\n"
        f"### 발생 이력\n"
        f"| 날짜 | 불량 유형 | 장비 | 불량 웨이퍼 | 조치 | 결과 |\n"
        f"|------|-----------|------|-------------|------|------|\n"
        f"{table}\n\n"
        f"### 패턴 발견\n"
        f"- 장비 집중도 상위\n{top_equipment_text}\n"
        f"- 분석 유형: {analysis_type}\n\n"
        f"### 개선 권장 사항\n"
        f"- 반복 장비에 대한 공정 조건 재점검\n"
        f"- 조치 후 효과 검증(전/후 지표 비교)\n"
        f"- 예방적 PM 주기 조정 검토\n"
    )


def suggest_corrective_action(
    problem_description: str,
    affected_equipment: str,
    severity: str,
    current_status: str,
    available_resources: Optional[List[str]] = None,
    time_constraint: str = None,
) -> str:
    required = ["problem_description", "affected_equipment", "severity", "current_status"]
    provided = {
        "problem_description": problem_description,
        "affected_equipment": affected_equipment,
        "severity": severity,
        "current_status": current_status,
    }
    missing = _missing_required(required, provided)
    if missing:
        return _format_missing(missing)

    severity_norm = severity.lower()
    immediate = {
        "critical": ["즉시 장비 안전 정지", "원인 구간 격리 및 영향 Lot 차단", "전문 엔지니어 호출"],
        "major": ["공정 일시 중지 및 조건 점검", "대체 장비 전환 검토", "장비 알람/로그 수집"],
        "minor": ["조건 미세 조정", "모니터링 강화", "추가 샘플 검증"],
    }.get(severity_norm, ["상황 평가 후 조치 결정"])

    resources = "\n".join([f"- {r}" for r in (available_resources or ["자원 미입력"])])
    time_text = time_constraint or "미입력"

    return (
        f"{DISCLAIMER}\n\n"
        f"## 🔧 시정 조치 제안\n"
        f"- **문제 설명**: {problem_description}\n"
        f"- **영향 장비**: {affected_equipment}\n"
        f"- **심각도**: {severity}\n"
        f"- **현재 상태**: {current_status}\n"
        f"- **시간 제약**: {time_text}\n\n"
        f"### 즉시 조치 (우선순위 순)\n"
        + "\n".join([f"{idx+1}. {act}" for idx, act in enumerate(immediate)])
        + "\n\n"
        f"### 단계별 조치 가이드\n"
        f"1. 현상 재현 여부 확인 및 로그 확보\n"
        f"2. 공정/장비 파라미터 점검 (설정 vs 실제)\n"
        f"3. 최근 변경/작업 이력 검토\n"
        f"4. 영향 범위(웨이퍼/Lot/공정) 파악\n"
        f"5. 조치 후 검증 계획 수립\n\n"
        f"### 필요 자원 체크리스트\n{resources}\n\n"
        f"### 에스컬레이션 기준\n"
        f"- 제한 시간 내 미해결 시 상위 엔지니어 통보\n"
        f"- 생산 차질 예상 시 라인 매니저 즉시 보고\n\n"
        f"### 재발 방지 대책\n"
        f"- 원인 교정 후 표준 작업서/레시피 업데이트\n"
        f"- 모니터링 알람 한계 재조정 및 교육 실시\n"
    )


def compare_to_baseline(
    baseline_recipe: Dict[str, Dict[str, Any]],
    current_recipe: Dict[str, float],
    recipe_name: str = None,
) -> str:
    required = ["baseline_recipe", "current_recipe"]
    provided = {"baseline_recipe": baseline_recipe, "current_recipe": current_recipe}
    missing = _missing_required(required, provided)
    if missing:
        return _format_missing(missing)

    rows = []
    out_of_range = []
    for param, meta in baseline_recipe.items():
        curr_val = current_recipe.get(param)
        min_v, max_v = meta.get("min"), meta.get("max")
        std_val = meta.get("value")
        unit = meta.get("unit", "")
        if curr_val is None:
            rows.append(f"| {param} | {std_val} {unit} | - | - | ⚠️ 미입력 |")
            out_of_range.append(f"- {param}: 현재값 미입력")
            continue
        status = "✅ 범위 내"
        if min_v is not None and curr_val < min_v:
            status = "❌ 하한 미달"
            out_of_range.append(f"- {param}: {curr_val} < {min_v}{unit}")
        if max_v is not None and curr_val > max_v:
            status = "❌ 상한 초과"
            out_of_range.append(f"- {param}: {curr_val} > {max_v}{unit}")
        diff = curr_val - std_val if std_val is not None else 0
        rows.append(f"| {param} | {std_val} {unit} | {curr_val} | {diff:+.2f} | {status} |")

    table = "\n".join(rows) if rows else "| - | - | - | - | - |"
    warn_text = "\n".join(out_of_range) if out_of_range else "- 모든 파라미터 기준 충족"

    return (
        f"{DISCLAIMER}\n\n"
        f"## 📏 기준 대비 비교\n"
        f"- **레시피 명**: {recipe_name or '미입력'}\n\n"
        f"| 파라미터 | 기준값 | 현재값 | 편차 | 상태 |\n"
        f"|----------|--------|--------|------|------|\n"
        f"{table}\n\n"
        f"### 범위 이탈 항목\n{warn_text}\n\n"
        f"### 조정 권장\n"
        f"- 이탈 항목 우선 조정 후 재측정\n"
        f"- 영향도 큰 파라미터부터 순차 조정\n"
    )


def compare_two_recipes(
    recipe_a: Dict[str, float],
    recipe_b: Dict[str, float],
    recipe_a_name: str = "Recipe A",
    recipe_b_name: str = "Recipe B",
    tolerance: Optional[Dict[str, float]] = None,
) -> str:
    required = ["recipe_a", "recipe_b"]
    provided = {"recipe_a": recipe_a, "recipe_b": recipe_b}
    missing = _missing_required(required, provided)
    if missing:
        return _format_missing(missing)

    all_params = set(recipe_a.keys()) | set(recipe_b.keys())
    rows = []
    highlights = []
    for p in sorted(all_params):
        a_val = recipe_a.get(p)
        b_val = recipe_b.get(p)
        if a_val is None or b_val is None:
            rows.append(f"| {p} | {a_val if a_val is not None else '-'} | {b_val if b_val is not None else '-'} | - | ⚠️ 값 부족 |")
            continue
        diff = b_val - a_val
        tol_pct = tolerance.get(p) if tolerance else None
        status = "✅ 허용"
        if tol_pct is not None:
            pct = _pct_diff(b_val, a_val)
            if abs(pct) > tol_pct:
                status = "❌ 초과"
                highlights.append(f"- {p}: 편차 {pct:+.2f}% > 허용 {tol_pct}%")
        rows.append(f"| {p} | {a_val} | {b_val} | {diff:+.2f} | {status} |")

    diff_text = "\n".join(rows) if rows else "| - | - | - | - | - |"
    highlight_text = "\n".join(highlights) if highlights else "- 큰 편차 없음"

    return (
        f"{DISCLAIMER}\n\n"
        f"## 🔄 두 레시피 비교\n"
        f"- **{recipe_a_name}** vs **{recipe_b_name}**\n\n"
        f"| 파라미터 | {recipe_a_name} | {recipe_b_name} | 차이 | 상태 |\n"
        f"|----------|-----------------|-----------------|------|------|\n"
        f"{diff_text}\n\n"
        f"### 주요 차이점\n{highlight_text}\n"
        f"- 편차 큰 항목을 우선 조정 후 평가\n"
    )


def validate_process_window(
    process_window: Dict[str, Dict[str, Any]],
    test_conditions: Dict[str, float],
    critical_params: Optional[List[str]] = None,
) -> str:
    required = ["process_window", "test_conditions"]
    provided = {"process_window": process_window, "test_conditions": test_conditions}
    missing = _missing_required(required, provided)
    if missing:
        return _format_missing(missing)

    rows = []
    all_pass = True
    critical_params = critical_params or []
    alerts = []

    for param, limits in process_window.items():
        val = test_conditions.get(param)
        min_v = limits.get("min")
        max_v = limits.get("max")
        unit = limits.get("unit", "")
        if val is None:
            rows.append(f"| {param} | - | {min_v}-{max_v}{unit} | - | ⚠️ 미입력 |")
            alerts.append(f"- {param}: 값 미입력")
            all_pass = False
            continue
        in_range = (min_v is None or val >= min_v) and (max_v is None or val <= max_v)
        margin = min(val - min_v, max_v - val) if (min_v is not None and max_v is not None) and in_range else 0
        status = "✅ PASS" if in_range else "❌ FAIL"
        if param in critical_params and not in_range:
            alerts.append(f"- 중요 파라미터 {param}: {val} (범위 {min_v}-{max_v}{unit})")
        if not in_range:
            all_pass = False
        rows.append(f"| {param} | {val} {unit} | {min_v}-{max_v} {unit} | {margin:.2f} | {status} |")

    table = "\n".join(rows) if rows else "| - | - | - | - | - |"
    overall = "✅ 모든 파라미터 PASS" if all_pass else "❌ 일부 파라미터 FAIL"
    alert_text = "\n".join(alerts) if alerts else "- 이탈 없음"

    return (
        f"{DISCLAIMER}\n\n"
        f"## ✔️ 공정 윈도우 검증\n"
        f"- **결과**: {overall}\n\n"
        f"| 파라미터 | 입력값 | 허용 범위 | 마진 | 결과 |\n"
        f"|----------|--------|-----------|------|------|\n"
        f"{table}\n\n"
        f"### 위험 파라미터\n{alert_text}\n"
        f"### 권장 사항\n"
        f"- FAIL 항목 조정 후 재검증\n"
        f"- 중요 파라미터 우선 조정\n"
    )


def analyze_metrics(
    metrics_data: Dict[str, float],
    targets: Dict[str, float],
    period: str = None,
    equipment_id: str = None,
) -> str:
    required = ["metrics_data", "targets"]
    provided = {"metrics_data": metrics_data, "targets": targets}
    missing = _missing_required(required, provided)
    if missing:
        return _format_missing(missing)

    rows = []
    gaps = []
    for k, target in targets.items():
        current = metrics_data.get(k)
        if current is None:
            rows.append(f"| {k} | - | {target} | ⚠️ 데이터 없음 |")
            gaps.append(f"- {k}: 데이터 없음")
            continue
        status = "✅ 달성" if current >= target else "❌ 미달"
        gap = current - target
        rows.append(f"| {k} | {current} | {target} | {status} |")
        if current < target:
            gaps.append(f"- {k}: {gap:+.2f} (목표 미달)")

    table = "\n".join(rows) if rows else "| - | - | - | - |"
    gap_text = "\n".join(gaps) if gaps else "- 모든 KPI 달성"

    return (
        f"{DISCLAIMER}\n\n"
        f"## 📈 메트릭 분석\n"
        f"- **기간**: {period or '미입력'}\n"
        f"- **장비**: {equipment_id or '전체'}\n\n"
        f"| 지표 | 현재 | 목표 | 상태 |\n"
        f"|------|------|------|------|\n"
        f"{table}\n\n"
        f"### 개선 필요 항목\n{gap_text}\n"
        f"- 미달 항목은 원인(레시피/장비/재료) 별로 분류해 추가 분석\n"
    )


def analyze_spc_data(
    data_points: List[float],
    spec_limits: Dict[str, float],
    control_limits: Optional[Dict[str, float]] = None,
    parameter_name: str = None,
    equipment_id: str = None,
) -> str:
    required = ["data_points", "spec_limits"]
    provided = {"data_points": data_points, "spec_limits": spec_limits}
    missing = _missing_required(required, provided)
    if missing:
        return _format_missing(missing)

    if not data_points:
        return f"{DISCLAIMER}\n\n## ⚠️ 입력 오류\n데이터 포인트가 비어 있습니다."

    mean_val = statistics.mean(data_points)
    stdev_val = statistics.pstdev(data_points) if len(data_points) > 1 else 0.0
    usl = spec_limits.get("usl")
    lsl = spec_limits.get("lsl")
    target = spec_limits.get("target", mean_val)

    ucl = control_limits.get("ucl") if control_limits else mean_val + 3 * stdev_val
    lcl = control_limits.get("lcl") if control_limits else mean_val - 3 * stdev_val
    cl = control_limits.get("cl") if control_limits else mean_val

    # Cp, Cpk 계산
    cp = (usl - lsl) / (6 * stdev_val) if stdev_val and usl is not None and lsl is not None else 0.0
    cpk = (
        min((usl - mean_val) / (3 * stdev_val), (mean_val - lsl) / (3 * stdev_val))
        if stdev_val and usl is not None and lsl is not None
        else 0.0
    )

    violations = [v for v in data_points if v > ucl or v < lcl]
    trend_flag = False
    if len(data_points) >= 7:
        trend_flag = all(data_points[i] < data_points[i + 1] for i in range(len(data_points) - 1)) or all(
            data_points[i] > data_points[i + 1] for i in range(len(data_points) - 1)
        )

    return (
        f"{DISCLAIMER}\n\n"
        f"## 📊 SPC 데이터 분석\n"
        f"- **파라미터**: {parameter_name or '미입력'}\n"
        f"- **장비**: {equipment_id or '미입력'}\n\n"
        f"### 통계 요약\n"
        f"- 평균: {mean_val:.3f}\n"
        f"- 표준편차: {stdev_val:.3f}\n"
        f"- USL/LSL: {usl}/{lsl}\n"
        f"- UCL/LCL/CL: {ucl:.3f}/{lcl:.3f}/{cl:.3f}\n"
        f"- Cp/Cpk: {cp:.2f}/{cpk:.2f}\n\n"
        f"### 관리 상태\n"
        f"- 관리 한계 이탈: {'있음' if violations else '없음'}\n"
        f"- 트렌드(7점 연속): {'감지' if trend_flag else '없음'}\n"
        f"- 데이터 포인트 수: {len(data_points)}\n\n"
        f"### 개선 권장 사항\n"
        f"- 이탈 발생 시 원인 구간 역추적 및 재측정\n"
        f"- 편차 큰 샘플에 대해 장비/재료/레시피 교차 확인\n"
    )


def predict_defect_risk(
    process_window: Dict[str, Dict[str, float]],
    current_conditions: Dict[str, float],
    critical_params: Optional[List[str]] = None,
    historical_defect_correlation: Optional[Dict[str, str]] = None,
) -> str:
    required = ["process_window", "current_conditions"]
    provided = {"process_window": process_window, "current_conditions": current_conditions}
    missing = _missing_required(required, provided)
    if missing:
        return _format_missing(missing)

    critical_params = critical_params or []
    historical_defect_correlation = historical_defect_correlation or {}
    rows = []
    risk_components = []

    for param, limits in process_window.items():
        val = current_conditions.get(param)
        min_v = limits.get("min")
        max_v = limits.get("max")
        if val is None or min_v is None or max_v is None:
            rows.append(f"| {param} | - | {min_v}-{max_v} | ⚠️ 데이터 부족 |")
            continue
        base_risk = _margin_score(val, min_v, max_v)
        weight = 1.5 if param in critical_params else 1.0
        corr = historical_defect_correlation.get(param, "").upper()
        corr_weight = {"HIGH": 1.3, "MEDIUM": 1.1, "LOW": 1.0}.get(corr, 1.0)
        risk = base_risk * weight * corr_weight
        risk_components.append(min(100.0, risk))
        rows.append(f"| {param} | {val} | {min_v}-{max_v} | {risk:.1f} |")

    overall = sum(risk_components) / len(risk_components) if risk_components else 0.0
    sorted_risk = sorted(zip(process_window.keys(), risk_components), key=lambda x: x[1], reverse=True)
    risk_rank = "\n".join([f"- {p}: {r:.1f}" for p, r in sorted_risk[:5]]) if sorted_risk else "- 계산 불가"
    rows_text = "\n".join(rows) if rows else "| - | - | - | - |"

    return (
        f"{DISCLAIMER}\n\n"
        f"## 🔮 불량 위험도 예측\n"
        f"- **종합 점수 (0-100)**: {overall:.1f}\n\n"
        f"| 파라미터 | 현재 | 허용 범위 | 위험도 |\n"
        f"|----------|------|-----------|--------|\n"
        f"{rows_text}\n\n"
        f"### 위험 요인 순위\n{risk_rank}\n\n"
        f"### 예방 조치 권장\n"
        f"- 위험도 상위 항목 우선 조정\n"
        f"- 중요 파라미터는 좁은 마진 유지 및 추가 모니터링\n"
    )


def optimize_recipe_direction(
    current_recipe: Dict[str, float],
    current_performance: Dict[str, float],
    target_performance: Dict[str, float],
    param_sensitivity: Optional[Dict[str, str]] = None,
    constraints: Optional[Dict[str, Dict[str, float]]] = None,
) -> str:
    required = ["current_recipe", "current_performance", "target_performance"]
    provided = {
        "current_recipe": current_recipe,
        "current_performance": current_performance,
        "target_performance": target_performance,
    }
    missing = _missing_required(required, provided)
    if missing:
        return _format_missing(missing)

    param_sensitivity = param_sensitivity or {}
    constraints = constraints or {}
    perf_gaps = []
    for k, target in target_performance.items():
        curr = current_performance.get(k, 0)
        perf_gaps.append((k, target - curr))
    perf_text = "\n".join([f"- {k}: 목표 대비 {gap:+.2f}" for k, gap in perf_gaps])

    adjustments = []
    for p, val in current_recipe.items():
        sens = param_sensitivity.get(p, "MEDIUM")
        cons = constraints.get(p, {})
        min_c = cons.get("min")
        max_c = cons.get("max")
        direction = "상향" if any(gap > 0 for _, gap in perf_gaps) else "하향/최적화"
        note = f"(민감도 {sens}, 제약 {min_c}-{max_c})"
        adjustments.append(f"- {p}: {direction} 조정 권장 {note}")

    return (
        f"{DISCLAIMER}\n\n"
        f"## ⚙️ 레시피 최적화 방향\n"
        f"### 성과 갭 분석\n{perf_text or '- 데이터 부족'}\n\n"
        f"### 조정 권장 파라미터\n"
        + "\n".join(adjustments or ["- 입력된 파라미터 없음"])
        + "\n\n"
        f"### 우선순위\n"
        f"- 민감도 HIGH > MEDIUM > LOW 순서로 조정\n"
        f"- 제약 조건 내에서 최소 변경으로 목표 접근\n"
    )


def simulate_parameter_change(
    current_state: Dict[str, Any],
    proposed_changes: Dict[str, float],
    impact_rules: List[Dict[str, Any]],
    process_window: Optional[Dict[str, Dict[str, float]]] = None,
) -> str:
    required = ["current_state", "proposed_changes", "impact_rules"]
    provided = {
        "current_state": current_state,
        "proposed_changes": proposed_changes,
        "impact_rules": impact_rules,
    }
    missing = _missing_required(required, provided)
    if missing:
        return _format_missing(missing)

    before_recipe = current_state.get("recipe", {})
    before_perf = current_state.get("performance", {})
    after_recipe = before_recipe.copy()
    after_recipe.update(proposed_changes)

    predicted_perf = before_perf.copy()
    for rule in impact_rules:
        impacts = rule.get("impact", {})
        for metric, delta in impacts.items():
            predicted_perf[metric] = predicted_perf.get(metric, 0) + delta

    window_alerts = []
    if process_window:
        for p, val in after_recipe.items():
            limits = process_window.get(p, {})
            min_v, max_v = limits.get("min"), limits.get("max")
            if min_v is not None and val < min_v:
                window_alerts.append(f"- {p}: {val} < {min_v}")
            if max_v is not None and val > max_v:
                window_alerts.append(f"- {p}: {val} > {max_v}")

    recipe_table = "\n".join(
        [f"| {k} | {before_recipe.get(k,'-')} | {after_recipe.get(k,'-')} |" for k in after_recipe.keys()]
    )
    perf_table = "\n".join(
        [f"| {k} | {before_perf.get(k,'-')} | {predicted_perf.get(k,'-')} |" for k in predicted_perf.keys()]
    )
    risk_text = "- 범위 초과 없음" if not window_alerts else "범위 초과:\n" + "\n".join(window_alerts)

    return (
        f"{DISCLAIMER}\n\n"
        f"## 🧪 파라미터 변경 시뮬레이션\n"
        f"### 레시피 변경 전/후\n"
        f"| 파라미터 | Before | After |\n|----------|--------|-------|\n{recipe_table}\n\n"
        f"### 예상 성과 변화\n"
        f"| 지표 | Before | After |\n|------|--------|-------|\n{perf_table}\n\n"
        f"### 리스크 평가\n"
        f"{risk_text}\n\n"
        f"### 권장 여부\n"
        f"- 영향도/리스크를 고려해 단계적 적용 및 검증 권장\n"
    )


def calculate_yield_impact(
    baseline_yield: float,
    parameter_changes: List[Dict[str, Any]],
    interaction_effects: Optional[List[Dict[str, Any]]] = None,
) -> str:
    required = ["baseline_yield", "parameter_changes"]
    provided = {"baseline_yield": baseline_yield, "parameter_changes": parameter_changes}
    missing = _missing_required(required, provided)
    if missing:
        return _format_missing(missing)

    interaction_effects = interaction_effects or []
    rows = []
    total_delta = 0.0
    for change in parameter_changes:
        sens = change.get("yield_sensitivity", 0)
        from_v = change.get("from")
        to_v = change.get("to")
        if from_v in [None, 0]:
            delta_pct = 0
        else:
            delta_pct = (to_v - from_v) / from_v * 100
        impact = delta_pct * sens
        total_delta += impact
        rows.append(f"| {change.get('param','-')} | {from_v} -> {to_v} | {impact:+.2f}% |")

    interaction_delta = sum(effect.get("effect", 0) for effect in interaction_effects)
    total_delta += interaction_delta
    final_yield = baseline_yield + total_delta
    rows_text = "\n".join(rows) if rows else "| - | - | - |"

    return (
        f"{DISCLAIMER}\n\n"
        f"## 🎯 수율 영향 계산\n"
        f"- 기준 수율: {baseline_yield:.2f}%\n"
        f"- 예상 총 변화: {total_delta:+.2f}% (상호작용 {interaction_delta:+.2f} 포함)\n"
        f"- 예상 수율: {final_yield:.2f}%\n\n"
        f"| 파라미터 | 변경 | 예상 수율 영향 |\n"
        f"|----------|------|----------------|\n"
        f"{rows_text}\n\n"
        f"### 검증 권장\n"
        f"- 민감도 큰 항목은 소량 변경 후 실측 검증\n"
        f"- 상호작용 가능성이 큰 조합은 DOE로 확인\n"
    )


def analyze_equipment_comparison(
    equipment_data: List[Dict[str, Any]],
    weights: Optional[Dict[str, float]] = None,
    benchmark: Optional[Dict[str, float]] = None,
) -> str:
    required = ["equipment_data"]
    provided = {"equipment_data": equipment_data}
    missing = _missing_required(required, provided)
    if missing:
        return _format_missing(missing)

    weights = weights or {}
    rows = []
    ranking = []

    for item in equipment_data:
        eq = item.get("equipment_id", "미입력")
        metrics = item.get("metrics", {})
        score = _weighted_score(metrics, weights)
        ranking.append((eq, score))
        rows.append(f"| {eq} | {score:.2f} | {metrics} |")

    ranking_sorted = sorted(ranking, key=lambda x: x[1], reverse=True)
    rank_text = "\n".join([f"{idx+1}. {eq}: {score:.2f}" for idx, (eq, score) in enumerate(ranking_sorted)])

    benchmark_text = ""
    if benchmark:
        bench_rows = "\n".join([f"- {k}: 목표 {v}" for k, v in benchmark.items()])
        benchmark_text = f"\n### 벤치마크\n{bench_rows}"
    rows_text = "\n".join(rows) if rows else "| - | - | - |"

    return (
        f"{DISCLAIMER}\n\n"
        f"## 🏭 장비 비교 분석\n"
        f"| 장비 | 종합 점수 | 메트릭 |\n"
        f"|------|-----------|--------|\n"
        f"{rows_text}\n\n"
        f"### 종합 랭킹\n{rank_text or '- 데이터 부족'}\n"
        f"{benchmark_text}\n"
        f"### 개선 우선순위 제안\n"
        f"- 하위 점수 장비의 취약 메트릭을 우선 개선\n"
    )


def generate_shift_report(
    production_summary: Dict[str, Any],
    equipment_status: List[Dict[str, Any]],
    quality_summary: Dict[str, Any],
    key_events: Optional[List[Dict[str, Any]]] = None,
    pending_actions: Optional[List[str]] = None,
    shift_info: Optional[Dict[str, str]] = None,
) -> str:
    required = ["production_summary", "equipment_status", "quality_summary"]
    provided = {
        "production_summary": production_summary,
        "equipment_status": equipment_status,
        "quality_summary": quality_summary,
    }
    missing = _missing_required(required, provided)
    if missing:
        return _format_missing(missing)

    eq_rows = "\n".join(
        [f"| {e.get('equipment_id','-')} | {e.get('status','-')} | {e.get('issues','-')} |" for e in equipment_status]
    ) or "| - | - | - |"
    events_rows = "\n".join(
        [f"| {ev.get('time','-')} | {ev.get('event','-')} | {ev.get('action','-')} | {ev.get('status','-')} |" for ev in (key_events or [])]
    ) or "| - | - | - | - |"
    pending = "\n".join([f"- {p}" for p in (pending_actions or [])]) or "- 미결 없음"

    return (
        f"{DISCLAIMER}\n\n"
        f"## 📝 교대 리포트\n"
        f"- **교대 정보**: {shift_info.get('shift') if shift_info else '미입력'} / {shift_info.get('date') if shift_info else '미입력'}\n\n"
        f"### 생산 요약\n"
        f"- 투입: {production_summary.get('wafer_in','-')}\n"
        f"- 완료: {production_summary.get('wafer_out','-')}\n"
        f"- 목표: {production_summary.get('target','-')}\n"
        f"- 수율: {production_summary.get('yield','-')}\n\n"
        f"### 장비 상태\n"
        f"| 장비 | 상태 | 이슈 |\n|------|------|------|\n{eq_rows}\n\n"
        f"### 품질 요약\n"
        f"- 불량 수: {quality_summary.get('defect_count','-')}\n"
        f"- 주요 불량: {quality_summary.get('major_defects','-')}\n"
        f"- SPC 알람: {quality_summary.get('spc_alerts','-')}\n\n"
        f"### 주요 이벤트\n"
        f"| 시간 | 이벤트 | 조치 | 상태 |\n|------|--------|------|------|\n{events_rows}\n\n"
        f"### 인수인계 필요 사항\n{pending}\n"
    )


def analyze_trend(
    time_series_data: List[Dict[str, Any]],
    parameter_name: str,
    spec_limits: Optional[Dict[str, float]] = None,
    analysis_options: Optional[Dict[str, Any]] = None,
) -> str:
    required = ["time_series_data", "parameter_name"]
    provided = {"time_series_data": time_series_data, "parameter_name": parameter_name}
    missing = _missing_required(required, provided)
    if missing:
        return _format_missing(missing)

    values = [d.get("value") for d in time_series_data if d.get("value") is not None]
    if not values:
        return f"{DISCLAIMER}\n\n## ⚠️ 입력 오류\n시계열 값이 없습니다."

    analysis_options = analysis_options or {}
    detect_shift = analysis_options.get("detect_shift", True)
    detect_trend = analysis_options.get("detect_trend", True)
    forecast_points = analysis_options.get("forecast_points", 0)

    mean_val = statistics.mean(values)
    stdev_val = statistics.pstdev(values) if len(values) > 1 else 0.0
    trend = "상승" if values[-1] > values[0] else "하락" if values[-1] < values[0] else "안정"

    shift_flag = False
    if detect_shift and len(values) >= 6:
        half = len(values) // 2
        shift_flag = statistics.mean(values[half:]) - statistics.mean(values[:half]) > (stdev_val or 0)

    forecast_text = "- 예측 미실행"
    if forecast_points > 0 and len(values) >= 2:
        delta = values[-1] - values[-2]
        forecast = [values[-1] + delta * (i + 1) for i in range(forecast_points)]
        forecast_text = ", ".join([f"{v:.2f}" for v in forecast])

    spec_text = ""
    if spec_limits:
        usl, lsl = spec_limits.get("usl"), spec_limits.get("lsl")
        out = [v for v in values if (usl is not None and v > usl) or (lsl is not None and v < lsl)]
        spec_text = f"- 스펙 이탈: {len(out)}건"

    return (
        f"{DISCLAIMER}\n\n"
        f"## 📈 트렌드 분석: {parameter_name}\n"
        f"- 평균: {mean_val:.3f}\n"
        f"- 표준편차: {stdev_val:.3f}\n"
        f"- 추세: {trend}\n"
        f"- 시프트 감지: {'예' if shift_flag else '아니오'}\n"
        f"{spec_text}\n\n"
        f"### 이상점 탐지\n"
        f"- 값 범위: {min(values):.3f} ~ {max(values):.3f}\n"
        f"- 샘플 수: {len(values)}\n\n"
        f"### 예측\n"
        f"{forecast_text}\n\n"
        f"### 권장 조치\n"
        f"- 추세가 하락이면 민감 파라미터 점검\n"
        f"- 시프트 감지 시 변경 이력/장비 상태 확인\n"
    )


# ===== MCP Tools 정의 =====
TOOLS = [
    {
        "name": "analyze_defect",
        "description": "사용자가 입력한 불량 설명과 컨텍스트를 기반으로 원인 매트릭스와 체크리스트를 생성합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "defect_code": {"type": "string", "description": "불량 코드/명칭"},
                "defect_description": {"type": "string", "description": "불량 상세 설명"},
                "process_step": {"type": "string", "description": "공정 단계"},
                "equipment_id": {"type": "string", "description": "장비 ID"},
                "wafer_id": {"type": "string", "description": "웨이퍼 ID"},
                "known_causes": {"type": "array", "items": {"type": "string"}, "description": "알려진 가능한 원인 목록"},
                "recent_changes": {"type": "array", "items": {"type": "string"}, "description": "최근 변경 사항"},
            },
            "required": ["defect_code", "defect_description", "process_step"],
        },
    },
    {
        "name": "get_defect_history",
        "description": "사용자가 제공한 불량 이력 데이터를 기반으로 패턴을 분석합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "defect_records": {
                    "type": "array",
                    "description": "불량 이력 배열",
                    "items": {
                        "type": "object",
                        "properties": {
                            "date": {"type": "string", "description": "발생 일자"},
                            "defect_type": {"type": "string", "description": "불량 유형"},
                            "equipment_id": {"type": "string", "description": "장비 ID"},
                            "wafer_count": {"type": "number", "description": "불량 웨이퍼 수"},
                            "action_taken": {"type": "string", "description": "조치 내용"},
                            "result": {"type": "string", "description": "조치 결과"},
                        },
                        "required": ["date", "defect_type", "equipment_id", "wafer_count"],
                    },
                },
                "analysis_type": {"type": "string", "description": "분석 유형: trend/equipment/time"},
            },
            "required": ["defect_records"],
        },
    },
    {
        "name": "suggest_corrective_action",
        "description": "입력된 상황 정보로 즉시/단계별 시정 조치 가이드를 생성합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "problem_description": {"type": "string", "description": "문제 상황 설명"},
                "affected_equipment": {"type": "string", "description": "영향 받은 장비"},
                "severity": {"type": "string", "enum": ["critical", "major", "minor"], "description": "심각도"},
                "current_status": {"type": "string", "description": "현재 상태 설명"},
                "available_resources": {"type": "array", "items": {"type": "string"}, "description": "가용 자원"},
                "time_constraint": {"type": "string", "description": "시간 제약"},
            },
            "required": ["problem_description", "affected_equipment", "severity", "current_status"],
        },
    },
    {
        "name": "compare_to_baseline",
        "description": "사용자 기준 레시피와 현재 레시피를 비교하여 이탈 항목을 하이라이트합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "baseline_recipe": {
                    "type": "object",
                    "description": "기준 레시피 {param:{value,min,max,unit}}",
                },
                "current_recipe": {"type": "object", "description": "현재 레시피 {param:value}"},
                "recipe_name": {"type": "string", "description": "레시피 명칭"},
            },
            "required": ["baseline_recipe", "current_recipe"],
        },
    },
    {
        "name": "compare_two_recipes",
        "description": "두 레시피를 비교하고 허용 편차 초과 항목을 표시합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "recipe_a": {"type": "object", "description": "레시피 A {param:value}"},
                "recipe_b": {"type": "object", "description": "레시피 B {param:value}"},
                "recipe_a_name": {"type": "string", "description": "레시피 A 명칭"},
                "recipe_b_name": {"type": "string", "description": "레시피 B 명칭"},
                "tolerance": {"type": "object", "description": "허용 편차 {param:percent}"},
            },
            "required": ["recipe_a", "recipe_b"],
        },
    },
    {
        "name": "validate_process_window",
        "description": "사용자 정의 공정 윈도우와 테스트 조건을 검증합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "process_window": {"type": "object", "description": "공정 윈도우 {param:{min,max,unit}}"},
                "test_conditions": {"type": "object", "description": "검증 대상 {param:value}"},
                "critical_params": {"type": "array", "items": {"type": "string"}, "description": "중요 파라미터"},
            },
            "required": ["process_window", "test_conditions"],
        },
    },
    {
        "name": "analyze_metrics",
        "description": "입력된 메트릭과 목표를 비교해 달성 여부와 개선 포인트를 제시합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "metrics_data": {"type": "object", "description": "현재 메트릭 {kpi:value}"},
                "targets": {"type": "object", "description": "목표 {kpi:value}"},
                "period": {"type": "string", "description": "데이터 기간"},
                "equipment_id": {"type": "string", "description": "장비 ID"},
            },
            "required": ["metrics_data", "targets"],
        },
    },
    {
        "name": "analyze_spc_data",
        "description": "SPC 데이터로 통계 요약, Cp/Cpk, 관리 한계 이탈을 분석합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "data_points": {"type": "array", "items": {"type": "number"}, "description": "측정 데이터 배열"},
                "spec_limits": {"type": "object", "description": "스펙 한계 {usl, lsl, target}"},
                "control_limits": {"type": "object", "description": "관리 한계 {ucl, lcl, cl}"},
                "parameter_name": {"type": "string", "description": "파라미터명"},
                "equipment_id": {"type": "string", "description": "장비 ID"},
            },
            "required": ["data_points", "spec_limits"],
        },
    },
    {
        "name": "predict_defect_risk",
        "description": "공정 윈도우 대비 현재 조건을 기반으로 불량 위험도를 예측합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "process_window": {"type": "object", "description": "공정 윈도우 {param:{min,max}}"},
                "current_conditions": {"type": "object", "description": "현재 조건 {param:value}"},
                "critical_params": {"type": "array", "items": {"type": "string"}, "description": "중요 파라미터"},
                "historical_defect_correlation": {"type": "object", "description": "과거 불량 상관 {param:HIGH/MEDIUM/LOW}"},
            },
            "required": ["process_window", "current_conditions"],
        },
    },
    {
        "name": "optimize_recipe_direction",
        "description": "현재/목표 성과와 민감도를 기반으로 레시피 조정 방향을 제안합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "current_recipe": {"type": "object", "description": "현재 레시피"},
                "current_performance": {"type": "object", "description": "현재 성과 KPI"},
                "target_performance": {"type": "object", "description": "목표 성과 KPI"},
                "param_sensitivity": {"type": "object", "description": "민감도 정보 {param:HIGH/MEDIUM/LOW}"},
                "constraints": {"type": "object", "description": "제약 {param:{min,max}}"},
            },
            "required": ["current_recipe", "current_performance", "target_performance"],
        },
    },
    {
        "name": "simulate_parameter_change",
        "description": "사용자 정의 영향 규칙으로 파라미터 변경 시 예상 변화를 시뮬레이션합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "current_state": {"type": "object", "description": "현재 상태 {recipe, performance}"},
                "proposed_changes": {"type": "object", "description": "변경 제안 {param:new_value}"},
                "impact_rules": {"type": "array", "items": {"type": "object"}, "description": "영향 규칙 목록"},
                "process_window": {"type": "object", "description": "공정 윈도우(선택)"},
            },
            "required": ["current_state", "proposed_changes", "impact_rules"],
        },
    },
    {
        "name": "calculate_yield_impact",
        "description": "파라미터 변화와 민감도를 기반으로 예상 수율 변화를 계산합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "baseline_yield": {"type": "number", "description": "기준 수율(%)"},
                "parameter_changes": {"type": "array", "items": {"type": "object"}, "description": "파라미터 변경 목록"},
                "interaction_effects": {"type": "array", "items": {"type": "object"}, "description": "상호작용 효과 목록"},
            },
            "required": ["baseline_yield", "parameter_changes"],
        },
    },
    {
        "name": "analyze_equipment_comparison",
        "description": "여러 장비 메트릭을 가중 평균하여 비교하고 랭킹을 제공합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "equipment_data": {"type": "array", "items": {"type": "object"}, "description": "장비별 메트릭"},
                "weights": {"type": "object", "description": "지표별 가중치"},
                "benchmark": {"type": "object", "description": "벤치마크 기준"},
            },
            "required": ["equipment_data"],
        },
    },
    {
        "name": "generate_shift_report",
        "description": "교대 인수인계용 리포트를 생성합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "production_summary": {"type": "object", "description": "생산 요약 {wafer_in, wafer_out, target, yield}"},
                "equipment_status": {"type": "array", "items": {"type": "object"}, "description": "장비 상태 목록"},
                "quality_summary": {"type": "object", "description": "품질 요약 {defect_count, major_defects, spc_alerts}"},
                "key_events": {"type": "array", "items": {"type": "object"}, "description": "주요 이벤트"},
                "pending_actions": {"type": "array", "items": {"type": "string"}, "description": "미결 조치"},
                "shift_info": {"type": "object", "description": "교대 정보 {shift, date}"},
            },
            "required": ["production_summary", "equipment_status", "quality_summary"],
        },
    },
    {
        "name": "analyze_trend",
        "description": "시계열 데이터를 분석하여 추세/시프트/예측을 제공합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "time_series_data": {"type": "array", "items": {"type": "object"}, "description": "시계열 데이터 [{timestamp,value}]"},
                "parameter_name": {"type": "string", "description": "파라미터명"},
                "spec_limits": {"type": "object", "description": "스펙 한계 {usl, lsl}"},
                "analysis_options": {"type": "object", "description": "옵션 {detect_shift, detect_trend, forecast_points}"},
            },
            "required": ["time_series_data", "parameter_name"],
        },
    },
]

TOOL_HANDLERS = {
    "analyze_defect": analyze_defect,
    "get_defect_history": get_defect_history,
    "suggest_corrective_action": suggest_corrective_action,
    "compare_to_baseline": compare_to_baseline,
    "compare_two_recipes": compare_two_recipes,
    "validate_process_window": validate_process_window,
    "analyze_metrics": analyze_metrics,
    "analyze_spc_data": analyze_spc_data,
    "predict_defect_risk": predict_defect_risk,
    "optimize_recipe_direction": optimize_recipe_direction,
    "simulate_parameter_change": simulate_parameter_change,
    "calculate_yield_impact": calculate_yield_impact,
    "analyze_equipment_comparison": analyze_equipment_comparison,
    "generate_shift_report": generate_shift_report,
    "analyze_trend": analyze_trend,
}


# ===== API 엔드포인트 =====
@app.get("/")
async def root():
    return {
        "service": "SemiProcess MCP",
        "spec": "2026-01-14",
        "health": "/health",
        "mcp": "/mcp",
        "tools_count": len(TOOLS),
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "SemiProcess MCP", "version": "2.0.0"}


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """MCP JSON-RPC 엔드포인트"""
    try:
        body = await request.json()
        method = body.get("method", "")
        params = body.get("params", {})
        request_id = body.get("id", 1)

        if method == "initialize":
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2026-01-14",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "SemiProcess MCP", "version": "2.0.0"},
                    },
                }
            )
        elif method == "notifications/initialized":
            return JSONResponse({"jsonrpc": "2.0", "id": request_id, "result": {}})
        elif method == "tools/list":
            return JSONResponse({"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOLS}})
        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            handler = TOOL_HANDLERS.get(tool_name)
            if not handler:
                return JSONResponse(
                    {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"},
                    }
                )
            try:
                result = handler(**arguments)
                return JSONResponse({"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": result}]}})
            except TypeError as e:
                return JSONResponse(
                    {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": f"Invalid parameters: {str(e)}"}}
                )
            except Exception as e:
                return JSONResponse(
                    {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32603, "message": f"Tool execution error: {str(e)}"}}
                )
        else:
            return JSONResponse(
                {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}
            )
    except Exception as e:
        return JSONResponse({"jsonrpc": "2.0", "id": 1, "error": {"code": -32700, "message": f"Parse error: {str(e)}"}}, status_code=400)


@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)
"""
Vercel Serverless MCP Server - 독립형 구현
SemiProcess: 반도체 공정 관리 MCP 서버
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

app = FastAPI(title="SemiProcess MCP Server")

# ===== Mock 데이터 =====
DEFECT_DB = {
    "PARTICLE": {
        "description": "입자 오염 불량",
        "causes": ["챔버 내 파티클", "웨이퍼 핸들링 오염", "가스 라인 오염", "필터 성능 저하"],
        "solutions": ["챔버 클리닝", "필터 교체", "핸들링 로봇 점검", "가스 라인 퍼지"]
    },
    "SCRATCH": {
        "description": "스크래치 불량",
        "causes": ["CMP 패드 마모", "슬러리 응집", "로봇 암 오정렬", "척 표면 손상"],
        "solutions": ["CMP 패드 교체", "슬러리 필터링", "로봇 캘리브레이션", "척 표면 연마"]
    },
    "PATTERN_DEFECT": {
        "description": "패턴 불량",
        "causes": ["포토레지스트 도포 불균일", "노광 에너지 변동", "현상액 농도 이상", "마스크 오염"],
        "solutions": ["코터 점검", "노광기 캘리브레이션", "현상액 교체", "마스크 클리닝"]
    },
    "CD_VARIATION": {
        "description": "CD(Critical Dimension) 변동",
        "causes": ["에칭 시간 변동", "플라즈마 불균일", "온도 변동", "가스 유량 변동"],
        "solutions": ["공정 시간 최적화", "플라즈마 소스 점검", "온도 제어 개선", "MFC 캘리브레이션"]
    },
    "OVERLAY_ERROR": {
        "description": "오버레이 오차",
        "causes": ["스테이지 정밀도 저하", "마스크 정렬 오차", "웨이퍼 휨", "온도에 의한 팽창"],
        "solutions": ["스테이지 캘리브레이션", "정렬 마크 최적화", "웨이퍼 평탄화", "온도 보정"]
    }
}

RECIPE_DB = {
    "etch": {
        "oxide": {
            "temperature": {"value": 60, "unit": "°C", "min": 55, "max": 65},
            "pressure": {"value": 30, "unit": "mTorr", "min": 25, "max": 35},
            "rf_power": {"value": 800, "unit": "W", "min": 750, "max": 850},
            "gas_cf4": {"value": 50, "unit": "sccm", "min": 45, "max": 55},
            "gas_o2": {"value": 10, "unit": "sccm", "min": 8, "max": 12},
            "time": {"value": 120, "unit": "sec", "min": 110, "max": 130}
        },
        "poly": {
            "temperature": {"value": 50, "unit": "°C", "min": 45, "max": 55},
            "pressure": {"value": 20, "unit": "mTorr", "min": 15, "max": 25},
            "rf_power": {"value": 600, "unit": "W", "min": 550, "max": 650},
            "gas_cl2": {"value": 80, "unit": "sccm", "min": 75, "max": 85},
            "gas_hbr": {"value": 20, "unit": "sccm", "min": 18, "max": 22}
        }
    },
    "deposition": {
        "oxide": {
            "temperature": {"value": 400, "unit": "°C", "min": 390, "max": 410},
            "pressure": {"value": 2, "unit": "Torr", "min": 1.8, "max": 2.2},
            "rf_power": {"value": 500, "unit": "W", "min": 480, "max": 520},
            "gas_sih4": {"value": 100, "unit": "sccm", "min": 95, "max": 105},
            "gas_n2o": {"value": 1000, "unit": "sccm", "min": 950, "max": 1050}
        },
        "nitride": {
            "temperature": {"value": 350, "unit": "°C", "min": 340, "max": 360},
            "pressure": {"value": 1.5, "unit": "Torr", "min": 1.3, "max": 1.7},
            "rf_power": {"value": 450, "unit": "W", "min": 430, "max": 470},
            "gas_sih4": {"value": 80, "unit": "sccm", "min": 75, "max": 85},
            "gas_nh3": {"value": 600, "unit": "sccm", "min": 570, "max": 630}
        }
    },
    "lithography": {
        "i-line": {
            "exposure_energy": {"value": 150, "unit": "mJ/cm²", "min": 140, "max": 160},
            "focus_offset": {"value": 0, "unit": "μm", "min": -0.2, "max": 0.2},
            "pr_thickness": {"value": 1.2, "unit": "μm", "min": 1.1, "max": 1.3}
        }
    },
    "implant": {
        "source_drain": {
            "energy": {"value": 30, "unit": "keV", "min": 28, "max": 32},
            "dose": {"value": 5e15, "unit": "ions/cm²", "min": 4.8e15, "max": 5.2e15},
            "tilt": {"value": 7, "unit": "°", "min": 6, "max": 8}
        }
    },
    "cmp": {
        "oxide": {
            "down_force": {"value": 3, "unit": "psi", "min": 2.5, "max": 3.5},
            "platen_speed": {"value": 60, "unit": "rpm", "min": 55, "max": 65},
            "slurry_flow": {"value": 200, "unit": "ml/min", "min": 180, "max": 220}
        }
    }
}


# ===== Tool 구현 함수들 =====
def analyze_defect(defect_code: str, process_step: str, wafer_id: str = None) -> str:
    defect_info = DEFECT_DB.get(defect_code.upper(), {})
    
    if not defect_info:
        available = ", ".join(DEFECT_DB.keys())
        return f"## ⚠️ 알 수 없는 불량 코드\n\n`{defect_code}`에 대한 정보가 없습니다.\n\n**사용 가능한 불량 코드**: {available}"
    
    wafer_info = f"- **웨이퍼 ID**: {wafer_id}\n" if wafer_id else ""
    causes_list = "\n".join([f"  - {c}" for c in defect_info.get("causes", [])])
    solutions_list = "\n".join([f"  - {s}" for s in defect_info.get("solutions", [])])
    
    return f"""## 🔍 불량 분석 결과

### 기본 정보
- **불량 코드**: {defect_code.upper()}
- **불량 유형**: {defect_info.get("description", "N/A")}
- **공정 단계**: {process_step}
{wafer_info}

### 추정 원인
{causes_list}

### 권장 해결 방안
{solutions_list}

### 추가 권장 사항
1. 해당 장비의 PM 이력 확인
2. 최근 레시피 변경 이력 검토
3. 동일 로트 내 다른 웨이퍼 상태 확인
4. SPC 차트에서 이상 트렌드 확인
"""


def get_defect_history(defect_type: str, date_range: str = "30d") -> str:
    defect_info = DEFECT_DB.get(defect_type.upper(), {})
    if not defect_info:
        available = ", ".join(DEFECT_DB.keys())
        return f"## ⚠️ 알 수 없는 불량 유형\n\n`{defect_type}`에 대한 정보가 없습니다.\n\n**사용 가능한 불량 유형**: {available}"
    
    # Mock 이력 데이터
    history_data = [
        {"date": "2024-01-10", "equipment": "ETCH-01", "wafer_count": 3, "action": "챔버 클리닝", "result": "해결"},
        {"date": "2024-01-08", "equipment": "ETCH-02", "wafer_count": 5, "action": "가스 라인 퍼지", "result": "해결"},
        {"date": "2024-01-05", "equipment": "ETCH-01", "wafer_count": 2, "action": "필터 교체", "result": "해결"},
        {"date": "2024-01-03", "equipment": "CVD-01", "wafer_count": 4, "action": "RF 매칭 조정", "result": "해결"},
        {"date": "2023-12-28", "equipment": "ETCH-01", "wafer_count": 1, "action": "레시피 최적화", "result": "해결"},
    ]
    
    rows = "\n".join([f"| {h['date']} | {h['equipment']} | {h['wafer_count']} | {h['action']} | {h['result']} |" for h in history_data])
    
    return f"""## 📊 불량 이력 조회

### 조회 조건
- **불량 유형**: {defect_type.upper()} ({defect_info.get("description", "")})
- **조회 기간**: {date_range}

### 발생 이력
| 발생일 | 장비 | 불량 웨이퍼 수 | 조치 내용 | 결과 |
|--------|------|---------------|-----------|------|
{rows}

### 통계 요약
- **총 발생 건수**: {len(history_data)}건
- **평균 불량 웨이퍼**: {sum(h['wafer_count'] for h in history_data) / len(history_data):.1f}매
- **주요 발생 장비**: ETCH-01 (3회)
- **해결률**: 100%
"""


def suggest_corrective_action(defect_code: str, equipment_id: str, current_conditions: dict = None) -> str:
    defect_info = DEFECT_DB.get(defect_code.upper(), {})
    
    if not defect_info:
        available = ", ".join(DEFECT_DB.keys())
        return f"## ⚠️ 알 수 없는 불량 코드\n\n`{defect_code}`에 대한 정보가 없습니다.\n\n**사용 가능한 불량 코드**: {available}"
    
    solutions = defect_info.get("solutions", ["일반 점검 수행"])
    actions = "\n".join([f"{i+1}. {s}" for i, s in enumerate(solutions)])
    
    conditions_text = ""
    if current_conditions:
        cond_lines = "\n".join([f"  - **{k}**: {v}" for k, v in current_conditions.items()])
        conditions_text = f"\n### 현재 공정 조건\n{cond_lines}\n"
    
    return f"""## 🔧 시정 조치 가이드

### 대상 정보
- **불량 코드**: {defect_code.upper()}
- **불량 유형**: {defect_info.get("description", "N/A")}
- **장비 ID**: {equipment_id}
{conditions_text}
### 즉시 조치 사항
{actions}

### 점검 체크리스트
- [ ] 장비 상태 로그 확인
- [ ] 최근 PM 이력 검토
- [ ] 센서 데이터 정상 여부 확인
- [ ] 인터락 상태 점검
- [ ] 가스/케미컬 잔량 확인

### 에스컬레이션
문제 지속 시 설비 엔지니어에게 에스컬레이션 필요
- 1차: 담당 엔지니어
- 2차: 설비 파트장
- 3차: 공정 담당자
"""


def get_standard_recipe(process_type: str, layer: str) -> str:
    process_recipes = RECIPE_DB.get(process_type.lower(), {})
    
    if not process_recipes:
        available_processes = ", ".join(RECIPE_DB.keys())
        return f"## ⚠️ 레시피 없음\n\n`{process_type}` 공정에 대한 표준 레시피가 없습니다.\n\n**사용 가능한 공정 유형**: {available_processes}"
    
    recipe = process_recipes.get(layer.lower(), {})
    
    if not recipe:
        available_layers = ", ".join(process_recipes.keys())
        return f"## ⚠️ 레시피 없음\n\n`{process_type}/{layer}`에 대한 표준 레시피가 없습니다.\n\n**사용 가능한 레이어**: {available_layers}"
    
    rows = "\n".join([f"| {k} | {v['value']} | {v['unit']} | {v['min']} | {v['max']} |" 
                      for k, v in recipe.items()])
    
    return f"""## 📋 표준 레시피

### 공정 정보
- **공정 유형**: {process_type.upper()}
- **레이어**: {layer.upper()}

### 파라미터 표준값
| 파라미터 | 표준값 | 단위 | 최소 | 최대 |
|----------|--------|------|------|------|
{rows}

### 참고 사항
- 표준값 기준으로 ±5% 이내 운영 권장
- 한계값 초과 시 SPC 알람 발생
- 레시피 변경 시 반드시 ECN 승인 필요
"""


def compare_recipe(process_type: str, current_recipe: dict, equipment_id: str) -> str:
    process_recipes = RECIPE_DB.get(process_type.lower(), {})
    
    # 첫 번째 사용 가능한 레이어의 레시피를 표준으로 사용
    standard = {}
    for layer_name, layer_recipe in process_recipes.items():
        standard = layer_recipe
        break
    
    if not standard:
        return f"## ⚠️ 표준 레시피 없음\n\n`{process_type}` 공정에 대한 표준 레시피가 없습니다."
    
    comparisons = []
    warnings = []
    for param, value in current_recipe.items():
        std = standard.get(param, {})
        if std:
            std_value = std.get("value", value)
            diff = value - std_value
            in_range = std.get("min", 0) <= value <= std.get("max", 999999)
            status = "✅ 정상" if in_range else "⚠️ 범위 초과"
            if not in_range:
                warnings.append(f"- **{param}**: 현재값 {value}이(가) 허용 범위({std.get('min')}-{std.get('max')})를 벗어남")
            comparisons.append(f"| {param} | {std_value} | {value} | {diff:+.2f} | {status} |")
    
    rows = "\n".join(comparisons) if comparisons else "| - | - | - | - | - |"
    warning_text = "\n### ⚠️ 주의 항목\n" + "\n".join(warnings) if warnings else ""
    
    return f"""## 🔄 레시피 비교 분석

### 비교 대상
- **공정 유형**: {process_type.upper()}
- **장비 ID**: {equipment_id}

### 비교 결과
| 파라미터 | 표준값 | 현재값 | 차이 | 상태 |
|----------|--------|--------|------|------|
{rows}
{warning_text}

### 권장 사항
- 범위 초과 항목은 즉시 조정 필요
- 변경 이력 기록 필수
"""


def validate_process_window(process_type: str, parameters: dict) -> str:
    process_recipes = RECIPE_DB.get(process_type.lower(), {})
    
    # 첫 번째 사용 가능한 레이어의 레시피를 표준으로 사용
    standard = {}
    for layer_name, layer_recipe in process_recipes.items():
        standard = layer_recipe
        break
    
    if not standard:
        return f"## ⚠️ 표준 레시피 없음\n\n`{process_type}` 공정에 대한 표준 레시피가 없습니다."
    
    results = []
    all_pass = True
    for param, value in parameters.items():
        std = standard.get(param, {})
        if std:
            min_val = std.get("min", 0)
            max_val = std.get("max", 999999)
            in_range = min_val <= value <= max_val
            margin = min(value - min_val, max_val - value) if in_range else 0
            status = "✅ PASS" if in_range else "❌ FAIL"
            if not in_range:
                all_pass = False
            results.append(f"| {param} | {value} | {min_val}-{max_val} | {margin:.2f} | {status} |")
    
    rows = "\n".join(results) if results else "| - | - | - | - | - |"
    overall = "✅ 모든 파라미터 정상" if all_pass else "❌ 일부 파라미터 범위 초과"
    recommendation = "공정 진행 가능합니다." if all_pass else "범위 초과 파라미터 조정 후 재검증 필요합니다."
    
    return f"""## ✔️ 공정 윈도우 검증

### 검증 결과: {overall}

### 상세 결과
| 파라미터 | 입력값 | 허용 범위 | 마진 | 결과 |
|----------|--------|-----------|------|------|
{rows}

### 권장 사항
{recommendation}
"""


def get_process_metrics(time_range: str = "8h", equipment_id: str = None, process_type: str = None) -> str:
    equip_text = equipment_id if equipment_id else "전체"
    process_text = process_type.upper() if process_type else "전체"
    
    return f"""## 📈 공정 메트릭 대시보드

### 조회 조건
- **시간 범위**: {time_range}
- **장비 ID**: {equip_text}
- **공정 유형**: {process_text}

### 핵심 KPI
| 지표 | 현재값 | 목표 | 상태 |
|------|--------|------|------|
| 수율 (Yield) | 98.5% | ≥98% | ✅ 양호 |
| Cpk | 1.45 | ≥1.33 | ✅ 양호 |
| 가동률 | 92.3% | ≥90% | ✅ 양호 |
| MTBF | 168h | ≥150h | ✅ 양호 |
| MTTR | 2.5h | ≤4h | ✅ 양호 |

### 생산 현황
| 항목 | 수량 |
|------|------|
| 투입 웨이퍼 | 250매 |
| 완료 웨이퍼 | 246매 |
| 불량 웨이퍼 | 4매 |
| 재작업 | 2매 |

### 최근 알람
| 시간 | 장비 | 내용 | 상태 |
|------|------|------|------|
| 21:30 | ETCH-01 | 압력 센서 경고 | ✅ 해결됨 |
| 20:15 | CVD-02 | 온도 편차 경고 | 🔄 모니터링 중 |
| 18:45 | LITHO-01 | 포커스 조정 필요 | ✅ 해결됨 |
"""


def check_spc_status(parameter_name: str, equipment_id: str, chart_type: str) -> str:
    chart_type_names = {
        "xbar": "X-bar (평균)",
        "range": "R (범위)",
        "sigma": "S (표준편차)"
    }
    chart_name = chart_type_names.get(chart_type.lower(), chart_type)
    
    return f"""## 📊 SPC 상태 리포트

### 조회 정보
- **파라미터**: {parameter_name}
- **장비 ID**: {equipment_id}
- **차트 유형**: {chart_name}

### 관리 상태
| 항목 | 상태 | 설명 |
|------|------|------|
| 관리 한계 이탈 | ✅ 정상 | 최근 24시간 이탈 없음 |
| 트렌드 (7점 연속) | ✅ 정상 | 연속 상승/하강 패턴 없음 |
| 런 규칙 위반 | ✅ 정상 | 중심선 한쪽 연속 7점 미발생 |
| 1/3 규칙 | ✅ 정상 | 2/3 이상 중심 근처 분포 |

### 통계 정보
| 항목 | 값 |
|------|-----|
| 평균 (X̄) | 45.2 |
| 표준편차 (σ) | 1.8 |
| UCL (상한) | 50.6 |
| CL (중심) | 45.2 |
| LCL (하한) | 39.8 |
| Cp | 1.52 |
| Cpk | 1.42 |

### 최근 25개 데이터 요약
- 최대값: 49.1
- 최소값: 41.3
- 범위: 7.8

### 권장 사항
- 현재 공정 안정 상태 유지
- 다음 PM 주기까지 모니터링 지속
"""


# ===== MCP Tools 정의 =====
TOOLS = [
    {
        "name": "analyze_defect",
        "description": "반도체 웨이퍼 불량 유형을 분석하고 원인을 추정합니다. 불량 코드와 공정 단계를 입력하면 가능한 원인과 해결 방안을 Markdown 형식으로 반환합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "defect_code": {"type": "string", "description": "불량 코드 (예: PARTICLE, SCRATCH, PATTERN_DEFECT, CD_VARIATION, OVERLAY_ERROR)"},
                "process_step": {"type": "string", "description": "공정 단계 (예: ETCH, CVD, LITHO, CMP)"},
                "wafer_id": {"type": "string", "description": "웨이퍼 ID (선택사항)"}
            },
            "required": ["defect_code", "process_step"]
        }
    },
    {
        "name": "get_defect_history",
        "description": "특정 불량 유형의 과거 발생 이력과 해결 사례를 조회합니다. 유사 불량에 대한 과거 대응 방법을 참고할 수 있습니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "defect_type": {"type": "string", "description": "불량 유형 (예: PARTICLE, SCRATCH)"},
                "date_range": {"type": "string", "enum": ["7d", "30d", "90d"], "description": "조회 기간", "default": "30d"}
            },
            "required": ["defect_type"]
        }
    },
    {
        "name": "suggest_corrective_action",
        "description": "현재 발생한 불량에 대해 권장 시정 조치를 제안합니다. 공정 조건 조정, 장비 점검 항목 등을 포함합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "defect_code": {"type": "string", "description": "불량 코드"},
                "equipment_id": {"type": "string", "description": "장비 ID (예: ETCH-01, CVD-02)"},
                "current_conditions": {"type": "object", "description": "현재 공정 조건 (선택사항)"}
            },
            "required": ["defect_code", "equipment_id"]
        }
    },
    {
        "name": "get_standard_recipe",
        "description": "특정 공정 단계의 표준 레시피(공정 조건)를 조회합니다. 온도, 압력, 시간, 가스 유량 등 표준 파라미터를 반환합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "process_type": {"type": "string", "enum": ["etch", "deposition", "lithography", "implant", "cmp"], "description": "공정 유형"},
                "layer": {"type": "string", "description": "레이어명 (예: oxide, poly, nitride)"}
            },
            "required": ["process_type", "layer"]
        }
    },
    {
        "name": "compare_recipe",
        "description": "현재 사용 중인 레시피와 표준 레시피를 비교하여 차이점을 분석합니다. 허용 범위 초과 항목을 하이라이트합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "process_type": {"type": "string", "description": "공정 유형"},
                "current_recipe": {"type": "object", "description": "현재 레시피 파라미터 (예: {\"temperature\": 62, \"pressure\": 32})"},
                "equipment_id": {"type": "string", "description": "장비 ID"}
            },
            "required": ["process_type", "current_recipe", "equipment_id"]
        }
    },
    {
        "name": "validate_process_window",
        "description": "입력된 공정 조건이 허용 공정 윈도우 내에 있는지 검증합니다. 각 파라미터의 마진 상태를 확인할 수 있습니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "process_type": {"type": "string", "description": "공정 유형"},
                "parameters": {"type": "object", "description": "검증할 파라미터들 (예: {\"temperature\": 60, \"pressure\": 30})"}
            },
            "required": ["process_type", "parameters"]
        }
    },
    {
        "name": "get_process_metrics",
        "description": "특정 장비 또는 공정의 실시간 주요 지표를 조회합니다. Cpk, 수율, 가동률 등 핵심 KPI를 반환합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "equipment_id": {"type": "string", "description": "장비 ID (선택사항)"},
                "process_type": {"type": "string", "description": "공정 유형 (선택사항)"},
                "time_range": {"type": "string", "enum": ["1h", "8h", "24h"], "description": "조회 시간 범위"}
            },
            "required": ["time_range"]
        }
    },
    {
        "name": "check_spc_status",
        "description": "SPC(통계적 공정 관리) 차트 상태를 확인합니다. 관리 한계 이탈, 트렌드, 런 규칙 위반 여부를 분석합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "parameter_name": {"type": "string", "description": "파라미터명 (예: temperature, pressure)"},
                "equipment_id": {"type": "string", "description": "장비 ID"},
                "chart_type": {"type": "string", "enum": ["xbar", "range", "sigma"], "description": "차트 유형"}
            },
            "required": ["parameter_name", "equipment_id", "chart_type"]
        }
    }
]

TOOL_HANDLERS = {
    "analyze_defect": analyze_defect,
    "get_defect_history": get_defect_history,
    "suggest_corrective_action": suggest_corrective_action,
    "get_standard_recipe": get_standard_recipe,
    "compare_recipe": compare_recipe,
    "validate_process_window": validate_process_window,
    "get_process_metrics": get_process_metrics,
    "check_spc_status": check_spc_status,
}


# ===== API 엔드포인트 =====
@app.get("/")
async def root():
    return {
        "service": "SemiProcess MCP",
        "spec": "2025-03-26",
        "health": "/health",
        "mcp": "/mcp",
        "tools_count": len(TOOLS)
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "SemiProcess MCP", "version": "1.0.0"}


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """MCP JSON-RPC 엔드포인트"""
    try:
        body = await request.json()
        method = body.get("method", "")
        params = body.get("params", {})
        request_id = body.get("id", 1)
        
        # initialize
        if method == "initialize":
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "SemiProcess MCP", "version": "1.0.0"}
                }
            })
        
        # notifications/initialized
        elif method == "notifications/initialized":
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {}
            })
        
        # tools/list
        elif method == "tools/list":
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": TOOLS}
            })
        
        # tools/call
        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            
            handler = TOOL_HANDLERS.get(tool_name)
            if not handler:
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}
                })
            
            try:
                result = handler(**arguments)
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [{"type": "text", "text": result}]
                    }
                })
            except TypeError as e:
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32602, "message": f"Invalid parameters: {str(e)}"}
                })
            except Exception as e:
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32603, "message": f"Tool execution error: {str(e)}"}
                })
        
        else:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            })
            
    except Exception as e:
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": 1,
            "error": {"code": -32700, "message": f"Parse error: {str(e)}"}
        }, status_code=400)


@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)