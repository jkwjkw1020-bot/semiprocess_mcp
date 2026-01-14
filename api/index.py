"""
SemiProcess MCP Server - 사용자 입력 기반 분석 도구 집합 (15개 Tool)
"""

from typing import Any, Dict, List, Optional
import statistics

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

app = FastAPI(title="SemiProcess MCP Server")

DISCLAIMER = """
> 📌 **분석 기준 안내**
>
> 본 분석은 아래 기준으로 수행되었습니다:
> - **입력 데이터**: 사용자 제공 (정확성은 사용자 책임)
> - **계산 로직**: 산업 표준 방법론을 참고(ISO/AIAG/FMEA/DOE 등)하되, 단순화된 계산을 적용
> - **결과 활용**: 참고용이며, 최종 의사결정 전 전문가 검토 권장
>
> ⚠️ 실무 적용 시 사내 표준, 실측 데이터, 전문가 검증을 반드시 병행하세요.
"""


def _missing(required: List[str], provided: Dict[str, Any]) -> List[str]:
    return [k for k in required if provided.get(k) is None]


def _err_missing(missing: List[str]) -> str:
    items = "\n".join(f"- `{m}`" for m in missing)
    return f"{DISCLAIMER}\n\n## ⚠️ 입력 오류\n필수 입력이 누락되었습니다.\n{items}"


# CSV 파싱 헬퍼 함수들
def _parse_csv_records(records_csv: str) -> List[Dict[str, Any]]:
    """CSV 형식: '날짜,장비,수량,조치,결과' 각 행을 세미콜론으로 구분"""
    records = []
    for row in records_csv.split(';'):
        row = row.strip()
        if not row:
            continue
        parts = [p.strip() for p in row.split(',')]
        if len(parts) >= 5:
            records.append({
                'date': parts[0],
                'equipment_id': parts[1],
                'wafer_count': int(parts[2]) if parts[2].isdigit() else 0,
                'action_taken': parts[3],
                'result': parts[4],
                'defect_type': 'SCRATCH'
            })
    return records


def _parse_csv_dict(csv_str: str, separator: str = ',') -> Dict[str, Any]:
    """CSV 형식: 'key:value' 쉼표로 구분. % 기호 제거 후 float 변환"""
    result = {}
    for item in csv_str.split(separator):
        item = item.strip()
        if ':' in item:
            key, value = item.split(':', 1)
            key = key.strip()
            value = value.strip().rstrip('%')  # % 기호 제거
            try:
                result[key] = float(value) if '.' in value else int(value)
            except (ValueError, TypeError):
                result[key] = value
    return result


def _parse_window_params(window_csv: str) -> Dict[str, Dict[str, float]]:
    """파라미터:최소:최대 또는 파라미터:최소-최대 형식"""
    result = {}
    for item in window_csv.split(','):
        item = item.strip()
        if ':' in item:
            parts = [p.strip() for p in item.split(':')]
            if len(parts) >= 2:
                param = parts[0]
                # 두 번째 부분에서 대시(min-max) 또는 콜론(min:max) 분리
                range_str = ':'.join(parts[1:])
                if '-' in range_str and ':' not in range_str[range_str.index('-')+1:]:
                    # 대시 포맷: "450-500"
                    min_max = [p.strip() for p in range_str.split('-')]
                    if len(min_max) == 2:
                        try:
                            result[param] = {'min': float(min_max[0]), 'max': float(min_max[1])}
                        except (ValueError, TypeError):
                            pass
                elif len(parts) >= 3:
                    # 콜론 포맷: "450:500"
                    try:
                        result[param] = {'min': float(parts[1]), 'max': float(parts[2])}
                    except (ValueError, TypeError):
                        pass
    return result


def _parse_baseline_params(baseline_csv: str) -> Dict[str, Dict[str, Any]]:
    """파라미터:표준값:최소:최대:단위 형식"""
    result = {}
    for item in baseline_csv.split(','):
        item = item.strip()
        if ':' in item:
            parts = [p.strip() for p in item.split(':')]
            if len(parts) >= 3:
                try:
                    result[parts[0]] = {
                        'value': float(parts[1]),
                        'min': float(parts[2]),
                        'max': float(parts[3]),
                        'unit': parts[4] if len(parts) > 4 else ''
                    }
                except (ValueError, TypeError):
                    pass
    return result


def _parse_recipe_params(recipe_csv: str) -> Dict[str, float]:
    """파라미터:값 형식"""
    result = {}
    for item in recipe_csv.split(','):
        item = item.strip()
        if ':' in item:
            key, value = item.split(':', 1)
            key = key.strip()
            value = value.strip()
            try:
                result[key] = float(value)
            except (ValueError, TypeError):
                result[key] = value
    return result


def analyze_defect(
    defect_code: str,
    defect_description: str,
    process_step: str,
    equipment_id: str = None,
    wafer_id: str = None,
    known_causes: Optional[List[str]] = None,
    recent_changes: Optional[List[str]] = None,
) -> str:
    miss = _missing(["defect_code", "defect_description", "process_step"], locals())
    if miss:
        return _err_missing(miss)
    causes = "\n".join(f"- {c}" for c in (known_causes or [])) or "- (사용자 원인 미입력)"
    changes = "\n".join(f"- {c}" for c in (recent_changes or [])) or "- 최근 변경 없음 보고"
    return (
        f"{DISCLAIMER}\n\n## 🔍 불량 분석\n"
        f"- 코드: {defect_code}\n- 설명: {defect_description}\n- 공정: {process_step}\n"
        f"- 장비: {equipment_id or '미입력'} / 웨이퍼: {wafer_id or '미입력'}\n\n"
        f"### 사용자 제안 원인\n{causes}\n\n"
        f"### 일반 점검\n- 장비 알람/로그\n- 최근 PM/캘리브레이션\n- 레시피 변경 이력\n- 소재/케미 Lot\n- SPC/Lot 편차\n\n"
        f"### 최근 변경 사항\n{changes}\n"
    )


def get_defect_history(defect_type: str = None, records_csv: str = None, defect_records: List[Dict[str, Any]] = None, analysis_type: str = "trend") -> str:
    # CSV 형식 지원 (CSV 우선)
    if records_csv and not defect_records:
        defect_records = _parse_csv_records(records_csv)
    
    miss = _missing(["defect_records"], {"defect_records": defect_records})
    if miss:
        return _err_missing(miss)
    if not defect_records:
        return f"{DISCLAIMER}\n\n## ⚠️ 입력 오류\n불량 이력이 비어 있습니다."
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
    rows = "\n".join(
        f"| {r.get('date','-')} | {r.get('defect_type','-')} | {r.get('equipment_id','-')} | {r.get('wafer_count','-')} | {r.get('action_taken','-')} | {r.get('result','-')} |"
        for r in defect_records
    )
    return (
        f"{DISCLAIMER}\n\n## 📊 불량 이력 분석 ({analysis_type})\n"
        f"- 총 이력: {total}건\n- 불량 웨이퍼 합계: {wafer_sum}매\n"
        f"- 사용된 조치: {', '.join(unique_actions) if unique_actions else '조치 정보 부족'}\n\n"
        f"| 날짜 | 불량 | 장비 | 웨이퍼 | 조치 | 결과 |\n|------|------|------|--------|------|------|\n{rows}\n\n"
        f"### 패턴 발견\n- 장비 집중도 상위\n{top_equipment_text}\n"
    )


def suggest_corrective_action(
    problem_description: str,
    affected_equipment: str,
    severity: str,
    current_status: str,
    available_resources: Optional[List[str]] = None,
    time_constraint: str = None,
) -> str:
    miss = _missing(["problem_description", "affected_equipment", "severity", "current_status"], locals())
    if miss:
        return _err_missing(miss)
    sev = severity.lower()
    immediate = {
        "critical": ["즉시 장비 정지", "영향 Lot 격리", "전문 엔지니어 호출"],
        "major": ["공정 일시 중지", "조건 점검", "알람/로그 수집"],
        "minor": ["조건 미세 조정", "모니터링 강화"],
    }.get(sev, ["상황 평가 후 결정"])
    resources = "\n".join(f"- {r}" for r in (available_resources or ["자원 미입력"]))
    return (
        f"{DISCLAIMER}\n\n## 🔧 시정 조치 제안\n"
        f"- 문제: {problem_description}\n- 장비: {affected_equipment}\n- 심각도: {severity}\n- 상태: {current_status}\n- 시간 제약: {time_constraint or '미입력'}\n\n"
        f"### 즉시 조치\n" + "\n".join(f"{i+1}. {v}" for i, v in enumerate(immediate)) + "\n\n"
        f"### 필요 자원\n{resources}\n"
    )


def compare_to_baseline(
    recipe_name: str = None,
    baseline_params: str = None,
    current_params: str = None,
    baseline_recipe: Dict[str, Dict[str, Any]] = None,
    current_recipe: Dict[str, float] = None,
) -> str:
    # CSV 형식 지원
    if baseline_params and not baseline_recipe:
        baseline_recipe = _parse_baseline_params(baseline_params)
    if current_params and not current_recipe:
        current_recipe = _parse_recipe_params(current_params)
    
    miss = _missing(["baseline_recipe", "current_recipe"], {"baseline_recipe": baseline_recipe, "current_recipe": current_recipe})
    if miss:
        return _err_missing(miss)
    rows = []
    for p, meta in baseline_recipe.items():
        cur = current_recipe.get(p)
        status = "✅"
        min_v, max_v = meta.get("min"), meta.get("max")
        if cur is None:
            status = "⚠️ 미입력"
        elif (min_v is not None and cur < min_v) or (max_v is not None and cur > max_v):
            status = "❌ 이탈"
        rows.append(f"| {p} | {meta.get('value')} {meta.get('unit','')} | {cur} | {status} |")
    table = "\n".join(rows) if rows else "| - | - | - | - |"
    return (
        f"{DISCLAIMER}\n\n## 📏 기준 대비 비교\n- 레시피: {recipe_name or '미입력'}\n\n"
        f"| 파라미터 | 기준 | 현재 | 상태 |\n|----------|------|------|------|\n{table}\n"
    )


def compare_two_recipes(
    recipe_a_name: str = None,
    recipe_a_params: str = None,
    recipe_b_name: str = None,
    recipe_b_params: str = None,
    tolerance_params: str = None,
    recipe_a: Dict[str, float] = None,
    recipe_b: Dict[str, float] = None,
    tolerance: Optional[Dict[str, float]] = None,
) -> str:
    # CSV 형식 지원
    if recipe_a_params and not recipe_a:
        recipe_a = _parse_recipe_params(recipe_a_params)
    if recipe_b_params and not recipe_b:
        recipe_b = _parse_recipe_params(recipe_b_params)
    if tolerance_params and not tolerance:
        tolerance = _parse_csv_dict(tolerance_params, ',')
    
    miss = _missing(["recipe_a", "recipe_b"], {"recipe_a": recipe_a, "recipe_b": recipe_b})
    if miss:
        return _err_missing(miss)
    rows = []
    all_params = set(recipe_a.keys()) | set(recipe_b.keys())
    for p in sorted(all_params):
        a, b = recipe_a.get(p), recipe_b.get(p)
        status = "✅"
        if tolerance and p in tolerance and a is not None and b is not None:
            diff_pct = ((b - a) / a * 100) if a else 0
            if abs(diff_pct) > tolerance[p]:
                status = "❌ 초과"
        rows.append(f"| {p} | {a} | {b} | {status} |")
    table = "\n".join(rows)
    return (
        f"{DISCLAIMER}\n\n## 🔄 두 레시피 비교\n- {recipe_a_name or 'Recipe A'} vs {recipe_b_name or 'Recipe B'}\n\n"
        f"| 파라미터 | {recipe_a_name or 'Recipe A'} | {recipe_b_name or 'Recipe B'} | 상태 |\n|----------|---------------|---------------|------|\n{table}\n"
    )


def validate_process_window(
    process_name: str = None,
    window_params: str = None,
    test_params: str = None,
    critical_params: str = None,
    process_window: Dict[str, Dict[str, Any]] = None,
    test_conditions: Dict[str, float] = None,
) -> str:
    # CSV 형식 지원
    if window_params and not process_window:
        process_window = _parse_window_params(window_params)
    if test_params and not test_conditions:
        test_conditions = _parse_recipe_params(test_params)
    
    critical_list = []
    if isinstance(critical_params, str):
        critical_list = [p.strip() for p in critical_params.split(',')]
    elif isinstance(critical_params, list):
        critical_list = critical_params
    
    miss = _missing(["process_window", "test_conditions"], {"process_window": process_window, "test_conditions": test_conditions})
    if miss:
        return _err_missing(miss)
    rows = []
    alerts = []
    for p, lim in process_window.items():
        val = test_conditions.get(p)
        min_v, max_v = lim.get("min"), lim.get("max")
        status = "✅ PASS"
        if val is None or (min_v is not None and val < min_v) or (max_v is not None and val > max_v):
            status = "❌ FAIL"
            if critical_list and p in critical_list:
                alerts.append(f"- 중요 {p}: {val} (범위 {min_v}-{max_v})")
        rows.append(f"| {p} | {val} | {min_v}-{max_v} | {status} |")
    return (
        f"{DISCLAIMER}\n\n## ✔️ 공정 윈도우 검증\n"
        f"| 파라미터 | 입력값 | 범위 | 결과 |\n|----------|--------|------|------|\n" + "\n".join(rows) + "\n\n"
        f"### 위험 파라미터\n" + ("\n".join(alerts) if alerts else "- 없음")
    )


def analyze_metrics(
    period: str = None,
    metrics_data: str = None,
    targets_data: str = None,
    equipment_id: str = None,
    metrics_dict: Dict[str, float] = None,
    targets: Dict[str, float] = None,
) -> str:
    # CSV 형식 지원
    if isinstance(metrics_data, str) and not metrics_dict:
        metrics_dict = _parse_csv_dict(metrics_data, ',')
    if isinstance(targets_data, str) and not targets:
        targets = _parse_csv_dict(targets_data, ',')
    
    miss = _missing(["metrics_dict", "targets"], {"metrics_dict": metrics_dict, "targets": targets})
    if miss:
        return _err_missing(miss)
    rows = []
    gaps = []
    for k, target in targets.items():
        cur = metrics_dict.get(k)
        status = "❌ 미달" if cur is None or cur < target else "✅ 달성"
        rows.append(f"| {k} | {cur} | {target} | {status} |")
        if cur is None or cur < target:
            gaps.append(f"- {k}: {(cur - target) if cur is not None else 'N/A'}")
    return (
        f"{DISCLAIMER}\n\n## 📈 메트릭 분석\n- 기간: {period or '미입력'} / 장비: {equipment_id or '전체'}\n\n"
        f"| 지표 | 현재 | 목표 | 상태 |\n|------|------|------|------|\n" + "\n".join(rows)
        + "\n\n### 개선 필요 항목\n"
        + ("\n".join(gaps) if gaps else "- 모든 KPI 달성")
    )


def analyze_spc_data(
    parameter_name: str = None,
    data_points: str = None,
    usl: float = None,
    lsl: float = None,
    target: float = None,
    ucl: float = None,
    lcl: float = None,
    equipment_id: str = None,
    data_points_list: List[float] = None,
    spec_limits: Dict[str, float] = None,
    control_limits: Optional[Dict[str, float]] = None,
    subgroup_size: int = 1,
) -> str:
    # CSV 형식 지원
    if isinstance(data_points, str) and not data_points_list:
        try:
            data_points_list = [float(x.strip()) for x in data_points.split(',') if x.strip()]
        except ValueError:
            return f"{DISCLAIMER}\n\n## ⚠️ 입력 오류\n데이터 포인트 형식이 잘못되었습니다."
    
    # 숫자형으로 변환
    if usl is not None and isinstance(usl, str):
        try:
            usl = float(usl)
        except (ValueError, TypeError):
            pass
    if lsl is not None and isinstance(lsl, str):
        try:
            lsl = float(lsl)
        except (ValueError, TypeError):
            pass
    if target is not None and isinstance(target, str):
        try:
            target = float(target)
        except (ValueError, TypeError):
            pass
    
    if not spec_limits and (usl is not None or lsl is not None):
        spec_limits = {'usl': usl, 'lsl': lsl, 'target': target}
    
    miss = _missing(["data_points_list", "spec_limits"], {"data_points_list": data_points_list, "spec_limits": spec_limits})
    if miss:
        return _err_missing(miss)
    if not data_points_list:
        return f"{DISCLAIMER}\n\n## ⚠️ 입력 오류\n데이터 포인트가 비어 있습니다."

    n = len(data_points_list)
    sample_warning = "⚠️ ISO 22514 권장 최소 샘플 수(25개) 미달. 해석 주의." if n < 25 else ""
    mean_val = statistics.mean(data_points_list)
    variance = statistics.pvariance(data_points_list) if n > 1 else 0.0
    std_dev = variance ** 0.5

    skewness = (
        sum((x - mean_val) ** 3 for x in data_points_list) / (n * (statistics.pvariance(data_points_list) ** 1.5))
        if n > 2 and std_dev > 0
        else 0.0
    )
    kurtosis = (
        sum((x - mean_val) ** 4 for x in data_points_list) / (n * (variance**2)) - 3
        if n > 3 and variance > 0
        else 0.0
    )
    is_normal = abs(skewness) < 1 and abs(kurtosis) < 2
    normality_warning = "" if is_normal else "⚠️ 정규성 미흡 가능. Cp/Cpk 해석 주의."

    A2_TABLE = {2: 1.880, 3: 1.023, 4: 0.729, 5: 0.577, 6: 0.483, 7: 0.419, 8: 0.373, 9: 0.337, 10: 0.308}
    if control_limits is None:
        if subgroup_size == 1:
            mrs = [abs(data_points_list[i] - data_points_list[i - 1]) for i in range(1, n)]
            mr_bar = statistics.mean(mrs) if mrs else 0.0
            d2 = 1.128
            sigma_within = mr_bar / d2 if d2 else std_dev
            ucl = mean_val + 3 * sigma_within
            lcl = mean_val - 3 * sigma_within
            cl = mean_val
            calc_method = "이동범위법 (MR/d2)"
        else:
            subgroups = [data_points[i : i + subgroup_size] for i in range(0, n, subgroup_size)]
            subgroup_means = [statistics.mean(sg) for sg in subgroups if len(sg) == subgroup_size]
            subgroup_ranges = [(max(sg) - min(sg)) for sg in subgroups if len(sg) == subgroup_size]
            x_bar_bar = statistics.mean(subgroup_means) if subgroup_means else mean_val
            r_bar = statistics.mean(subgroup_ranges) if subgroup_ranges else 0.0
            A2 = A2_TABLE.get(subgroup_size, 0.577)
            ucl = x_bar_bar + A2 * r_bar
            lcl = x_bar_bar - A2 * r_bar
            cl = x_bar_bar
            sigma_within = std_dev
            calc_method = f"X-bar & R (A2={A2}, n={subgroup_size})"
    else:
        ucl = control_limits.get("ucl")
        lcl = control_limits.get("lcl")
        cl = control_limits.get("cl", mean_val)
        sigma_within = std_dev
        calc_method = "사용자 지정"

    usl, lsl = spec_limits.get("usl"), spec_limits.get("lsl")
    sigma_overall = std_dev or sigma_within or 1e-9
    Cp = (usl - lsl) / (6 * sigma_within) if usl is not None and lsl is not None and sigma_within else None
    Pp = (usl - lsl) / (6 * sigma_overall) if usl is not None and lsl is not None and sigma_overall else None

    def _cpk(mean, usl, lsl, sigma):
        if (usl is None and lsl is None) or sigma == 0:
            return None
        if usl is not None and lsl is not None:
            return min((usl - mean) / (3 * sigma), (mean - lsl) / (3 * sigma))
        if usl is not None:
            return (usl - mean) / (3 * sigma)
        return (mean - lsl) / (3 * sigma)

    Cpk = _cpk(mean_val, usl, lsl, sigma_within)
    Ppk = _cpk(mean_val, usl, lsl, sigma_overall)
    violations = [x for x in data_points_list if (ucl is not None and x > ucl) or (lcl is not None and x < lcl)]
    violations_text = "\n".join(f"- {v:.3f}" for v in violations[:5]) if violations else "- 위반 사항 없음"

    # 포맷팅을 위해 값을 미리 정제
    ucl_fmt = f"{ucl:.4f}" if ucl is not None else "N/A"
    cl_fmt = f"{cl:.4f}" if cl is not None else "N/A"
    lcl_fmt = f"{lcl:.4f}" if lcl is not None else "N/A"
    cp_fmt = f"{Cp:.3f}" if Cp is not None else "N/A"
    pp_fmt = f"{Pp:.3f}" if Pp is not None else "N/A"
    cpk_fmt = f"{Cpk:.3f}" if Cpk is not None else "N/A"
    ppk_fmt = f"{Ppk:.3f}" if Ppk is not None else "N/A"

    return f"""{DISCLAIMER}

## 📊 SPC 분석 결과
- 파라미터: {parameter_name or '미입력'} / 장비: {equipment_id or '미입력'}
- 관리한계 계산: {calc_method}
- 샘플 수: {n}개 {sample_warning}
- 정규성: {"정상" if is_normal else "주의"} {normality_warning}

### 기본 통계량
| 항목 | 값 |
|------|-----|
| 평균 (X̄) | {mean_val:.4f} |
| 표준편차 (σ) | {std_dev:.4f} |
| 최대/최소 | {max(data_points_list):.4f} / {min(data_points_list):.4f} |

### 관리한계
| 항목 | 값 |
|------|-----|
| UCL | {ucl_fmt} |
| CL | {cl_fmt} |
| LCL | {lcl_fmt} |

### 공정능력지수
| 지수 | 값 |
|------|-----|
| Cp / Pp | {cp_fmt} / {pp_fmt} |
| Cpk / Ppk | {cpk_fmt} / {ppk_fmt} |

### 관리 한계 이탈
{violations_text}
"""


def predict_defect_risk(
    process_name: str = None,
    window_params: str = None,
    current_params: str = None,
    severity_params: str = None,
    critical_params: str = None,
    process_window: Dict[str, Dict[str, float]] = None,
    current_conditions: Dict[str, float] = None,
    severity_ratings: Optional[Dict[str, int]] = None,
    occurrence_ratings: Optional[Dict[str, int]] = None,
    detection_ratings: Optional[Dict[str, int]] = None,
    historical_defect_correlation: Optional[Dict[str, str]] = None,
) -> str:
    # CSV 형식 지원
    if window_params and not process_window:
        process_window = _parse_window_params(window_params)
    if current_params and not current_conditions:
        current_conditions = _parse_recipe_params(current_params)
    
    critical_list = []
    if isinstance(critical_params, str):
        critical_list = [p.strip() for p in critical_params.split(',')]
    elif isinstance(critical_params, list):
        critical_list = critical_params
    
    if severity_params and not severity_ratings:
        severity_ratings = _parse_csv_dict(severity_params, ',')
    
    miss = _missing(["process_window", "current_conditions"], {"process_window": process_window, "current_conditions": current_conditions})
    if miss:
        return _err_missing(miss)

    severity_ratings = severity_ratings or {}
    occurrence_ratings = occurrence_ratings or {}
    detection_ratings = detection_ratings or {}
    historical_defect_correlation = historical_defect_correlation or {}

    def estimate_occurrence_from_margin(cur, min_v, max_v):
        rng = max_v - min_v
        if rng <= 0:
            return 5, "범위 정의 불명확"
        min_margin = min(max_v - cur, cur - min_v)
        margin_pct = (min_margin / (rng / 2)) * 100 if rng else 0
        if margin_pct <= 0:
            return 10, "범위 이탈"
        if margin_pct < 10:
            return 8, "마진 10% 미만"
        if margin_pct < 20:
            return 6, "마진 20% 미만"
        if margin_pct < 30:
            return 5, "마진 30% 미만"
        if margin_pct < 50:
            return 3, "마진 50% 미만"
        return 2, "마진 여유"

    def action_priority(s, o, d, rpn):
        if s >= 9 and o >= 4:
            return "H"
        if s >= 5 and o >= 6:
            return "H"
        if s >= 5 and o >= 4 and d >= 6:
            return "M"
        if rpn >= 100:
            return "M"
        return "L"

    rows = []
    rpns = []
    for p, limits in process_window.items():
        cur = current_conditions.get(p)
        min_v, max_v = limits.get("min"), limits.get("max")
        if cur is None or min_v is None or max_v is None:
            continue
        S = severity_ratings.get(p, 5)
        if p in occurrence_ratings:
            O = occurrence_ratings[p]
            o_basis = "사용자 입력"
        else:
            O, o_basis = estimate_occurrence_from_margin(cur, min_v, max_v)
        D = detection_ratings.get(p, 5)
        RPN = S * O * D
        AP = action_priority(S, O, D, RPN)
        margin_pct = (min(max_v - cur, cur - min_v) / ((max_v - min_v) / 2)) * 100 if max_v != min_v else 0
        rows.append(
            f"| {p} | {cur} | {margin_pct:.1f}% | {S} | {O} | {D} | {RPN} | {AP} | {o_basis} | {historical_defect_correlation.get(p,'N/A')} |"
        )
        rpns.append(RPN)

    rows_text = "\n".join(rows) if rows else "| - | - | - | - | - | - | - | - | - | - |"
    max_rpn = max(rpns) if rpns else 0
    high_ap = " H " in rows_text
    if high_ap or max_rpn >= 200:
        overall = "🔴 고위험 - 즉시 조치"
    elif max_rpn >= 100:
        overall = "🟡 중위험 - 계획 조치"
    else:
        overall = "🟢 저위험 - 모니터링"

    return f"""{DISCLAIMER}

## 🔍 FMEA 기반 불량 위험도 평가
- 적용 기준: AIAG & VDA FMEA (단순화)
- 중요 파라미터: {', '.join(critical_params) if critical_params else '미입력'}

### 종합 위험도
{overall}
- 최대 RPN: {max_rpn}

### 파라미터별 FMEA 테이블
| 파라미터 | 현재값 | 마진 | S | O | D | RPN | AP | O 근거 | 과거 상관 |
|----------|--------|------|---|---|---|-----|----|--------|-----------|
{rows_text}
"""


def optimize_recipe_direction(
    current_recipe: Optional[Dict[str, float]] = None,
    recipe_csv: str = None,
    current_performance: Optional[Dict[str, float]] = None,
    perf_csv: str = None,
    target_performance: Optional[Dict[str, float]] = None,
    target_csv: str = None,
    param_sensitivity: Optional[Dict[str, str]] = None,
    constraints: Optional[Dict[str, Dict[str, float]]] = None,
) -> str:
    # CSV 형식 지원
    if isinstance(recipe_csv, str) and not current_recipe:
        current_recipe = _parse_recipe_params(recipe_csv)
    if isinstance(perf_csv, str) and not current_performance:
        current_performance = _parse_csv_dict(perf_csv, ':')
        current_performance = {k: float(v) for k,v in current_performance.items()}
    if isinstance(target_csv, str) and not target_performance:
        target_performance = _parse_csv_dict(target_csv, ':')
        target_performance = {k: float(v) for k,v in target_performance.items()}
    
    miss = _missing(["current_recipe", "current_performance", "target_performance"], 
                    {"current_recipe": current_recipe, "current_performance": current_performance, "target_performance": target_performance})
    if miss:
        return _err_missing(miss)
    param_sensitivity = param_sensitivity or {}
    constraints = constraints or {}
    perf_gaps = [(k, target - current_performance.get(k, 0)) for k, target in target_performance.items()]
    perf_text = "\n".join([f"- {k}: 목표 대비 {gap:+.2f}" for k, gap in perf_gaps]) or "- 데이터 부족"
    adjustments = []
    for p, _ in current_recipe.items():
        sens = param_sensitivity.get(p, "MEDIUM")
        cons = constraints.get(p, {})
        min_c, max_c = cons.get("min"), cons.get("max")
        direction = "상향" if any(gap > 0 for _, gap in perf_gaps) else "하향/최적화"
        adjustments.append(f"- {p}: {direction} (민감도 {sens}, 제약 {min_c}-{max_c})")
    return (
        f"{DISCLAIMER}\n\n## ⚙️ 레시피 최적화 방향\n"
        f"### 성과 갭 분석\n{perf_text}\n\n"
        f"### 조정 권장 파라미터\n" + "\n".join(adjustments or ["- 입력된 파라미터 없음"])
    )


def simulate_parameter_change(
    current_state: Optional[Dict[str, Any]] = None,
    state_csv: str = None,
    proposed_changes: Optional[Dict[str, float]] = None,
    changes_csv: str = None,
    impact_rules: Optional[List[Dict[str, Any]]] = None,
    rules_csv: str = None,
    process_window: Optional[Dict[str, Dict[str, float]]] = None,
    window_csv: str = None,
) -> str:
    # CSV 형식 지원
    if isinstance(state_csv, str) and not current_state:
        # state_csv: "recipe:temp:65,pressure:30;performance:yield:97,cpk:1.2"
        current_state = {}
        for section in state_csv.split(';'):
            section = section.strip()
            if ':' in section:
                key, values = section.split(':', 1)
                current_state[key.strip()] = {k.strip(): float(v.strip()) 
                                             for k,v in (p.split(':') for p in values.split(',') if ':' in p)}
    if isinstance(changes_csv, str) and not proposed_changes:
        proposed_changes = _parse_recipe_params(changes_csv)
    if isinstance(rules_csv, str) and not impact_rules:
        # rules_csv: "time->etch_rate:-10;time->uniformity:-2" (새 포맷)
        # 또는: "rule1:yield:+2,cpk:+0.1;rule2:yield:-1" (기존 포맷)
        impact_rules = []
        for rule in rules_csv.split(';'):
            rule = rule.strip()
            if not rule:
                continue
            # 화살표 포맷 처리: "source->target:effect"
            if '->' in rule and ':' in rule:
                try:
                    source_target, impact_str = rule.rsplit(':', 1)
                    effect = float(impact_str.strip())
                    target = source_target.split('->')[-1].strip()
                    impact_rules.append({
                        'name': source_target.strip(),
                        'impact': {target: effect}
                    })
                except (ValueError, TypeError, IndexError):
                    pass
            # 기존 콜론 포맷 처리: "rule1:etch_rate:-10"
            elif ':' in rule:
                parts = rule.split(':', 1)
                rule_name = parts[0].strip()
                impacts_str = parts[1]
                impacts = {}
                for p in impacts_str.split(','):
                    if ':' in p:
                        k, v = p.split(':', 1)
                        try:
                            impacts[k.strip()] = float(v.strip())
                        except (ValueError, TypeError):
                            pass
                if impacts:
                    impact_rules.append({'name': rule_name, 'impact': impacts})
    if isinstance(window_csv, str) and not process_window:
        process_window = _parse_window_params(window_csv)
    
    miss = _missing(["current_state", "proposed_changes", "impact_rules"], 
                    {"current_state": current_state, "proposed_changes": proposed_changes, "impact_rules": impact_rules})
    if miss:
        return _err_missing(miss)
    before_recipe = current_state.get("recipe", {}) if isinstance(current_state, dict) else {}
    before_perf = current_state.get("performance", {}) if isinstance(current_state, dict) else {}
    after_recipe = {**before_recipe, **proposed_changes}
    predicted_perf = before_perf.copy()
    for rule in (impact_rules or []):
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
    recipe_table = "\n".join([f"| {k} | {before_recipe.get(k,'-')} | {after_recipe.get(k,'-')} |" for k in after_recipe.keys()])
    perf_table = "\n".join([f"| {k} | {before_perf.get(k,'-')} | {predicted_perf.get(k,'-')} |" for k in predicted_perf.keys()])
    risk_text = "- 범위 초과 없음" if not window_alerts else "범위 초과:\n" + "\n".join(window_alerts)
    return (
        f"{DISCLAIMER}\n\n## 🧪 파라미터 변경 시뮬레이션\n"
        f"### 레시피 변경 전/후\n| 파라미터 | Before | After |\n|----------|--------|-------|\n{recipe_table}\n\n"
        f"### 예상 성과 변화\n| 지표 | Before | After |\n|------|--------|-------|\n{perf_table}\n\n"
        f"### 리스크 평가\n{risk_text}\n\n"
        f"### ⚠️ 모델 한계\n"
        f"- 사용자 정의 영향 규칙을 선형 가산 적용\n"
        f"- 물리/화학 모델 및 비선형 효과 미포함\n"
    )


def calculate_yield_impact(
    baseline_yield: Optional[float] = None,
    parameter_changes: Optional[List[Dict[str, Any]]] = None,
    changes_csv: str = None,
    interaction_effects: Optional[List[Dict[str, Any]]] = None,
    interactions_csv: str = None,
    confidence_level: float = 0.95,
    model_type: str = "linear",
) -> str:
    # CSV 형식 지원
    if isinstance(changes_csv, str) and not parameter_changes:
        # changes_csv: "temperature:start:65,end:70,sensitivity:0.8;pressure:start:30,end:33,sensitivity:0.1"
        # 또는 기존 포맷: "temperature:65:70:0.8;pressure:30:33:0.1"
        parameter_changes = []
        for item in changes_csv.split(';'):
            item = item.strip()
            if ':' in item:
                parts = [p.strip() for p in item.split(':')]
                if len(parts) >= 2:
                    param = parts[0]
                    # 새 포맷 처리: param:start:65,end:70,sensitivity:0.8
                    if len(parts) == 2 and ',' in parts[1]:
                        sub_parts = {}
                        for sub in parts[1].split(','):
                            if ':' in sub:
                                k, v = sub.split(':', 1)
                                try:
                                    sub_parts[k.strip()] = float(v.strip())
                                except (ValueError, TypeError):
                                    pass
                        if 'start' in sub_parts and 'end' in sub_parts and 'sensitivity' in sub_parts:
                            parameter_changes.append({
                                'param': param,
                                'from': sub_parts['start'],
                                'to': sub_parts['end'],
                                'yield_sensitivity': sub_parts['sensitivity']
                            })
                    # 기존 포맷: "temperature:65:70:0.8"
                    elif len(parts) >= 4:
                        try:
                            parameter_changes.append({
                                'param': parts[0],
                                'from': float(parts[1]),
                                'to': float(parts[2]),
                                'yield_sensitivity': float(parts[3])
                            })
                        except (ValueError, TypeError):
                            pass
    if isinstance(interactions_csv, str) and not interaction_effects:
        # interactions_csv: "temp×pressure:0.01;temp×time:0.005"
        interaction_effects = []
        for item in interactions_csv.split(';'):
            item = item.strip()
            if ':' in item:
                params_str, effect = item.split(':', 1)
                interaction_effects.append({
                    'params': [p.strip() for p in params_str.split('×')],
                    'effect': float(effect)
                })
    
    miss = _missing(["baseline_yield", "parameter_changes"], 
                    {"baseline_yield": baseline_yield, "parameter_changes": parameter_changes})
    if miss:
        return _err_missing(miss)
    linear_effects = []
    total_linear = 0.0
    for change in (parameter_changes or []):
        delta = (change.get("to") - change.get("from")) if change.get("to") is not None and change.get("from") is not None else 0
        sens = change.get("yield_sensitivity", 0)
        effect = delta * sens
        total_linear += effect
        linear_effects.append(
            {"param": change.get("param"), "from": change.get("from"), "to": change.get("to"), "delta": delta, "sens": sens, "effect": effect}
        )
    interaction_total = sum(i.get("effect", 0) for i in (interaction_effects or []))
    predicted_yield = baseline_yield + total_linear + interaction_total
    total_effect = abs(total_linear) + abs(interaction_total)
    uncertainty = total_effect * 0.1 if total_effect > 0 else 0.1
    z = 1.96 if confidence_level >= 0.95 else 2.576
    ci_lower = predicted_yield - z * uncertainty
    ci_upper = predicted_yield + z * uncertainty
    linear_rows = "\n".join(
        f"| {e['param']} | {e['from']} → {e['to']} | {e['delta']:+.2f} | {e['sens']:.4f} | {e['effect']:+.3f}% |"
        for e in linear_effects
    )
    inter_rows = (
        "\n".join([f"| {' × '.join(i.get('params', []))} | {i.get('effect', 0):+.3f}% |" for i in (interaction_effects or [])])
        if interaction_effects
        else "| (없음) | - |"
    )
    return f"""{DISCLAIMER}

## 📈 수율 영향 분석 (DOE 기반 단순 예측)
- 모델: {model_type}
- 신뢰수준: {confidence_level*100:.0f}%

### 결과
| 항목 | 값 |
|------|-----|
| 기준 수율 | {baseline_yield:.2f}% |
| 선형 효과 합계 | {total_linear:+.3f}% |
| 상호작용 합계 | {interaction_total:+.3f}% |
| 예측 수율 | **{predicted_yield:.2f}%** |
| 신뢰구간 | [{ci_lower:.2f}%, {ci_upper:.2f}%] |

### 선형 효과
| 파라미터 | 변경 | Δ | 민감도 | 영향 |
|----------|------|---|--------|------|
{linear_rows}

### 상호작용 효과
| 파라미터 조합 | 영향 |
|---------------|------|
{inter_rows}
"""


def analyze_equipment_comparison(
    equipment_data: Optional[List[Dict[str, Any]]] = None,
    equipment_list: str = None,
    metrics_data: str = None,
    weights_csv: str = None,
    benchmark_csv: str = None,
    normalization_method: str = "min-max",
) -> str:
    # CSV 형식 지원
    if isinstance(equipment_list, str) and not equipment_data:
        equipment_data = []
        eq_list = [e.strip() for e in equipment_list.split(',') if e.strip()]
        # metrics_data: "ETCH-01:yield:98.5,cpk:1.45;ETCH-02:yield:97.2,cpk:1.28"
        if metrics_data:
            for item in metrics_data.split(';'):
                item = item.strip()
                if ':' in item:
                    eq_id, metrics_str = item.split(':', 1)
                    metrics = {}
                    for metric_pair in metrics_str.split(','):
                        metric_pair = metric_pair.strip()
                        if ':' in metric_pair:
                            k, v = metric_pair.split(':', 1)
                            try:
                                metrics[k.strip()] = float(v.strip())
                            except ValueError:
                                pass
                    equipment_data.append({'equipment_id': eq_id.strip(), 'metrics': metrics})
    weights = None
    benchmark = None
    if isinstance(weights_csv, str) and not weights:
        weights = _parse_csv_dict(weights_csv, ':')
        weights = {k: float(v) for k,v in weights.items()}
    if isinstance(benchmark_csv, str) and not benchmark:
        benchmark = _parse_csv_dict(benchmark_csv, ':')
        benchmark = {k: float(v) for k,v in benchmark.items()}
    
    miss = _missing(["equipment_data"], {"equipment_data": equipment_data})
    if miss:
        return _err_missing(miss)

    all_metrics = set()
    for eq in equipment_data:
        all_metrics.update(eq.get("metrics", {}).keys())
    if not all_metrics:
        return f"{DISCLAIMER}\n\n## ⚠️ 입력 오류\n메트릭이 없습니다."

    if weights is None:
        weights = {m: 1 / len(all_metrics) for m in all_metrics}
    wsum = sum(weights.values()) or 1.0
    weight_warning = ""
    if abs(wsum - 1.0) > 0.01:
        weights = {k: v / wsum for k, v in weights.items()}
        weight_warning = f"⚠️ 가중치 합계 {wsum:.2f} → 정규화 적용"

    higher_is_better = {"yield": True, "cpk": True, "uptime": True, "throughput": True, "mtbf": True, "defect_rate": False, "mttr": False}

    def norm_minmax(vals, higher=True):
        mn, mx = min(vals), max(vals)
        if mx == mn:
            return [0.5] * len(vals)
        return [((v - mn) / (mx - mn)) if higher else ((mx - v) / (mx - mn)) for v in vals]

    normalized = []
    for eq in equipment_data:
        norm_metrics = {}
        for m in all_metrics:
            vals = [e.get("metrics", {}).get(m, 0) for e in equipment_data]
            higher = higher_is_better.get(m, True)
            norm_vals = norm_minmax(vals, higher)
            norm_metrics[m] = norm_vals[equipment_data.index(eq)]
        score = sum(norm_metrics.get(m, 0) * weights.get(m, 0) for m in all_metrics) * 100
        normalized.append({"equipment_id": eq.get("equipment_id", "?"), "orig": eq.get("metrics", {}), "score": score})

    normalized.sort(key=lambda x: x["score"], reverse=True)
    for i, eq in enumerate(normalized):
        eq["rank"] = i + 1

    metric_headers = " | ".join(all_metrics)
    rows = "\n".join(
        f"| {eq['rank']} | {eq['equipment_id']} | {eq['score']:.1f} | " + " | ".join(str(eq["orig"].get(m, "N/A")) for m in all_metrics) + " |"
        for eq in normalized
    )

    bm_text = ""
    if benchmark:
        bm_rows = []
        for eq in normalized:
            checks = []
            for m, bm in benchmark.items():
                val = eq["orig"].get(m)
                if val is None:
                    checks.append("❓")
                    continue
                better = higher_is_better.get(m, True)
                ok = val >= bm if better else val <= bm
                checks.append("✅" if ok else "❌")
            bm_rows.append(f"| {eq['equipment_id']} | {' '.join(checks)} |")
        bm_text = "\n### 벤치마크 비교\n| 장비 | 충족 |\n|------|------|\n" + "\n".join(bm_rows)

    return f"""{DISCLAIMER}

## 🏭 장비 성능 비교 (가중합)
- 정규화: {normalization_method.upper()}
- 가중치 합계 검증: {weight_warning or 'OK'}

### 가중치
| 지표 | 가중치 |
|------|--------|
{chr(10).join([f"| {m} | {w:.2%} |" for m, w in weights.items()])}

### 순위
| 순위 | 장비 | 점수 | {metric_headers} |
|------|------|------|{' | '.join(['---']*len(all_metrics))}|
{rows}
{bm_text}
"""


def generate_shift_report(
    shift_info: str = None,
    production_data: str = None,
    equipment_status: str = None,
    quality_data: str = None,
    events: str = None,
    pending_actions: str = None,
    shift_info_dict: Optional[Dict[str, str]] = None,
    production_summary: Dict[str, Any] = None,
    equipment_status_list: List[Dict[str, Any]] = None,
    quality_summary: Dict[str, Any] = None,
    key_events: Optional[List[Dict[str, Any]]] = None,
    pending_actions_list: Optional[List[str]] = None,
) -> str:
    # CSV 형식 지원
    if isinstance(production_data, str) and not production_summary:
        production_summary = _parse_csv_dict(production_data, ',')
    if isinstance(equipment_status, str) and not equipment_status_list:
        equipment_status_list = []
        for item in equipment_status.split(';'):
            item = item.strip()
            parts = [p.strip() for p in item.split(':')]
            if len(parts) >= 2:
                equipment_status_list.append({'equipment_id': parts[0], 'status': parts[1], 'issues': parts[2] if len(parts) > 2 else '-'})
    if isinstance(quality_data, str) and not quality_summary:
        quality_summary = _parse_csv_dict(quality_data, ',')
    if isinstance(pending_actions, str) and not pending_actions_list:
        pending_actions_list = [p.strip() for p in pending_actions.split(';') if p.strip()]
    if isinstance(events, str) and not key_events:
        key_events = []
        for item in events.split(';'):
            item = item.strip()
            if ' ' in item:
                parts = item.split(' ', 1)
                key_events.append({'time': parts[0], 'event': parts[1]})
    
    miss = _missing(["production_summary", "equipment_status_list", "quality_summary"], 
                    {"production_summary": production_summary, "equipment_status_list": equipment_status_list, "quality_summary": quality_summary})
    if miss:
        return _err_missing(miss)
    
    eq_rows = "\n".join(
        [f"| {e.get('equipment_id','-')} | {e.get('status','-')} | {e.get('issues','-')} |" for e in equipment_status_list]
    ) or "| - | - | - |"
    events_rows = "\n".join(
        [f"| {ev.get('time','-')} | {ev.get('event','-')} | {ev.get('action','-')} | {ev.get('status','-')} |" for ev in (key_events or [])]
    ) or "| - | - | - | - |"
    pending = "\n".join([f"- {p}" for p in (pending_actions_list or [])]) or "- 미결 없음"
    shift_str = f"{shift_info}" if shift_info else "미입력"
    
    return (
        f"{DISCLAIMER}\n\n## 📝 교대 리포트\n"
        f"- **교대 정보**: {shift_str}\n\n"
        f"### 생산 요약\n"
        f"- 투입: {production_summary.get('in','-')}\n"
        f"- 완료: {production_summary.get('out','-')}\n"
        f"- 목표: {production_summary.get('target','-')}\n"
        f"- 수율: {production_summary.get('yield','-')}\n\n"
        f"### 장비 상태\n| 장비 | 상태 | 이슈 |\n|------|------|------|\n{eq_rows}\n\n"
        f"### 품질 요약\n"
        f"- 불량 수: {quality_summary.get('defects','-')}\n"
        f"- 주요 불량: {quality_summary.get('major','-')}\n\n"
        f"### 주요 이벤트\n| 시간 | 이벤트 | 조치 | 상태 |\n|------|--------|------|------|\n{events_rows}\n\n"
        f"### 인수인계 필요 사항\n{pending}\n"
    )


def analyze_trend(
    parameter_name: str = None,
    data_points: str = None,
    timestamps: str = None,
    usl: float = None,
    lsl: float = None,
    forecast_count: int = 0,
    time_series_data: List[Dict[str, Any]] = None,
    spec_limits: Optional[Dict[str, float]] = None,
    analysis_options: Optional[Dict[str, Any]] = None,
) -> str:
    # CSV 형식 지원
    if isinstance(data_points, str) and not time_series_data:
        try:
            values = [float(x.strip()) for x in data_points.split(',') if x.strip()]
            time_series_data = [{"value": v} for v in values]
        except ValueError:
            return f"{DISCLAIMER}\n\n## ⚠️ 입력 오류\n데이터 포인트 형식이 잘못되었습니다."
    
    if not spec_limits and (usl is not None or lsl is not None):
        spec_limits = {'usl': usl, 'lsl': lsl}
    
    if forecast_count and not analysis_options:
        analysis_options = {'forecast_points': forecast_count}
    
    miss = _missing(["time_series_data", "parameter_name"], {"time_series_data": time_series_data, "parameter_name": parameter_name})
    if miss:
        return _err_missing(miss)
    values = [d.get("value") for d in time_series_data if d.get("value") is not None]
    n = len(values)
    if n < 5:
        return f"{DISCLAIMER}\n\n## ⚠️ 데이터 부족\n분석을 위해 최소 5개 이상 필요합니다. (현재: {n}개)"

    analysis_options = analysis_options or {}
    forecast_points = analysis_options.get("forecast_points", 0)
    mean_val = sum(values) / n
    variance = sum((x - mean_val) ** 2 for x in values) / (n - 1)
    std_dev = variance**0.5

    x = list(range(n))
    x_mean = sum(x) / n
    y_mean = mean_val
    denom = sum((xi - x_mean) ** 2 for xi in x)
    slope = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n)) / denom if denom else 0
    intercept = y_mean - slope * x_mean
    ss_tot = sum((v - y_mean) ** 2 for v in values)
    ss_res = sum((values[i] - (slope * x[i] + intercept)) ** 2 for i in range(n))
    r_squared = 1 - (ss_res / ss_tot) if ss_tot else 0
    if n > 2 and denom > 0:
        mse = ss_res / (n - 2)
        se_slope = (mse / denom) ** 0.5 if denom else 0
        t_stat = slope / se_slope if se_slope else 0
        t_crit = 2.0 if n > 30 else 2.3
        trend_significant = abs(t_stat) > t_crit
    else:
        t_stat = 0
        trend_significant = False

    def mann_kendall(data):
        s = 0
        for i in range(len(data) - 1):
            for j in range(i + 1, len(data)):
                diff = data[j] - data[i]
                if diff > 0:
                    s += 1
                elif diff < 0:
                    s -= 1
        var_s = (n * (n - 1) * (2 * n + 5)) / 18
        if s > 0:
            z = (s - 1) / (var_s**0.5)
        elif s < 0:
            z = (s + 1) / (var_s**0.5)
        else:
            z = 0
        trend_txt = "상승 추세(유의)" if z > 1.96 else "하락 추세(유의)" if z < -1.96 else "추세 없음(비유의)"
        return {"S": s, "Z": z, "trend": trend_txt, "significant": abs(z) > 1.96}

    mk = mann_kendall(values)
    first_half = values[: n // 2]
    second_half = values[n // 2 :]
    shift_size = 0
    shift_status = "시프트 없음"
    if first_half and second_half and std_dev > 0:
        shift_size = (sum(second_half) / len(second_half) - sum(first_half) / len(first_half)) / std_dev
        if abs(shift_size) > 1.5:
            shift_status = "유의한 시프트"
        elif abs(shift_size) > 1.0:
            shift_status = "시프트 의심"

    forecast_text = ""
    if forecast_points > 0:
        forecasts = []
        for i in range(forecast_points):
            fx = n + i
            fy = slope * fx + intercept
            forecasts.append(f"| +{i+1} | {fy:.4f} |")
        forecast_text = "\n### 예측 (선형 외삽)\n| 시점 | 예측값 |\n|------|--------|\n" + "\n".join(forecasts) + "\n"

    if mk["significant"] and trend_significant:
        conclusion = "🔴 통계적으로 유의한 추세"
        action = "원인 파악 및 조치"
    elif mk["significant"] or trend_significant:
        conclusion = "🟡 추세 의심"
        action = "추가 데이터 수집/모니터링"
    else:
        conclusion = "🟢 유의한 추세 없음"
        action = "현상 유지"

    spec_txt = ""
    if spec_limits:
        usl, lsl = spec_limits.get("usl"), spec_limits.get("lsl")
        out = [v for v in values if (usl is not None and v > usl) or (lsl is not None and v < lsl)]
        spec_txt = f"- 스펙 이탈: {len(out)}건"

    return f"""{DISCLAIMER}

## 📈 시계열 트렌드 분석
- 대상: {parameter_name}
- 데이터 수: {n}개
{spec_txt}

### 기본 통계량
| 항목 | 값 |
|------|-----|
| 평균 | {mean_val:.4f} |
| 표준편차 | {std_dev:.4f} |
| 최대/최소 | {max(values):.4f} / {min(values):.4f} |

### 선형 회귀(OLS)
| 항목 | 값 | 해석 |
|------|-----|------|
| 기울기 | {slope:.6f} | {'양(상승)' if slope>0 else '음(하락)' if slope<0 else '0'} |
| R² | {r_squared:.4f} | |
| t-통계량 | {t_stat:.3f} | 유의성: {"유의" if trend_significant else "비유의"} |

### Mann-Kendall
| S | Z | 판정 |
|---|---|------|
| {mk['S']} | {mk['Z']:.3f} | {mk['trend']} |

### 시프트 탐지
| 항목 | 값 |
|------|-----|
| 시프트 크기(σ) | {shift_size:.2f} |
| 판정 | {shift_status} |

### 종합 판정
- 결론: {conclusion}
- 권장 조치: {action}
{forecast_text}
"""


TOOLS = [
    # 1. analyze_defect - 기존 유지 (이미 단순함)
    {
        "name": "analyze_defect",
        "description": "반도체 웨이퍼 불량을 분석합니다. 불량 코드, 설명, 공정 단계를 입력하면 원인 분석과 점검 항목을 제공합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "defect_code": {
                    "type": "string",
                    "description": "불량 코드. 예: PARTICLE, SCRATCH, CD_VARIATION"
                },
                "defect_description": {
                    "type": "string",
                    "description": "불량 상세 설명. 예: 웨이퍼 가장자리 깊은 스크래치"
                },
                "process_step": {
                    "type": "string",
                    "description": "공정 단계. 예: ETCH, CVD, CMP, LITHO"
                },
                "equipment_id": {
                    "type": "string",
                    "description": "장비 ID (선택). 예: CMP-01"
                },
                "wafer_id": {
                    "type": "string",
                    "description": "웨이퍼 ID (선택). 예: W123"
                },
                "known_causes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "알려진 원인 목록 (선택). 예: ['패드 마모', '슬러리 오염']"
                },
                "recent_changes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "최근 변경 사항 (선택). 예: ['슬러리 Lot 교체', 'PM 수행']"
                }
            },
            "required": ["defect_code", "defect_description", "process_step"]
        }
    },
    
    # 2. get_defect_history - CSV 형식으로 단순화
    {
        "name": "get_defect_history",
        "description": "불량 이력을 분석합니다. 불량 유형과 이력 데이터를 CSV 형식으로 입력하면 패턴을 분석합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "defect_type": {
                    "type": "string",
                    "description": "불량 유형. 예: SCRATCH, PARTICLE"
                },
                "records_csv": {
                    "type": "string",
                    "description": "이력 데이터 CSV 형식: '날짜,장비,수량,조치,결과' 각 행을 세미콜론으로 구분. 예: '2025-01-10,CMP-01,3,패드교체,해결;2025-01-05,CMP-02,2,필터교체,해결'"
                },
                "analysis_type": {
                    "type": "string",
                    "enum": ["trend", "equipment", "time"],
                    "description": "분석 유형 (선택). 기본값: trend"
                }
            },
            "required": ["defect_type", "records_csv"]
        }
    },
    
    # 3. suggest_corrective_action - 기존 유지 (이미 단순함)
    {
        "name": "suggest_corrective_action",
        "description": "문제 상황에 대한 시정 조치를 제안합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "problem_description": {
                    "type": "string",
                    "description": "문제 설명. 예: 압력 불안정"
                },
                "affected_equipment": {
                    "type": "string",
                    "description": "영향 받은 장비. 예: ETCH-01"
                },
                "severity": {
                    "type": "string",
                    "enum": ["critical", "major", "minor"],
                    "description": "심각도"
                },
                "current_status": {
                    "type": "string",
                    "description": "현재 상태. 예: 알람 반복 발생"
                },
                "available_resources": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "가용 자원 (선택). 예: ['엔지니어 1명', '필터 예비']"
                },
                "time_constraint": {
                    "type": "string",
                    "description": "시간 제약 (선택). 예: 4시간 내"
                }
            },
            "required": ["problem_description", "affected_equipment", "severity", "current_status"]
        }
    },
    
    # 4. compare_to_baseline - CSV 형식으로 단순화
    {
        "name": "compare_to_baseline",
        "description": "기준 레시피와 현재 레시피를 비교합니다. 파라미터를 CSV 형식으로 입력합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "recipe_name": {
                    "type": "string",
                    "description": "레시피 이름. 예: Oxide Etch"
                },
                "baseline_params": {
                    "type": "string",
                    "description": "기준 레시피 CSV 형식: '파라미터:표준값:최소:최대:단위' 쉼표로 구분. 예: 'temperature:60:55:65:C,pressure:30:25:35:mTorr'"
                },
                "current_params": {
                    "type": "string",
                    "description": "현재 레시피 CSV 형식: '파라미터:값' 쉼표로 구분. 예: 'temperature:67,pressure:28'"
                }
            },
            "required": ["recipe_name", "baseline_params", "current_params"]
        }
    },
    
    # 5. compare_two_recipes - CSV 형식으로 단순화
    {
        "name": "compare_two_recipes",
        "description": "두 레시피를 비교합니다. 파라미터를 CSV 형식으로 입력합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "recipe_a_name": {
                    "type": "string",
                    "description": "레시피 A 이름. 예: A라인"
                },
                "recipe_a_params": {
                    "type": "string",
                    "description": "레시피 A 파라미터 CSV: '파라미터:값' 쉼표로 구분. 예: 'temperature:60,pressure:30,rf_power:800'"
                },
                "recipe_b_name": {
                    "type": "string",
                    "description": "레시피 B 이름. 예: B라인"
                },
                "recipe_b_params": {
                    "type": "string",
                    "description": "레시피 B 파라미터 CSV: '파라미터:값' 쉼표로 구분. 예: 'temperature:62,pressure:28,rf_power:820'"
                },
                "tolerance_params": {
                    "type": "string",
                    "description": "허용 편차 CSV (선택): '파라미터:퍼센트' 쉼표로 구분. % 기호 선택. 예: 'temperature:5,pressure:10' 또는 'temperature:5%,pressure:10%'"
                }
            },
            "required": ["recipe_a_name", "recipe_a_params", "recipe_b_name", "recipe_b_params"]
        }
    },
    
    # 6. validate_process_window - CSV 형식으로 단순화
    {
        "name": "validate_process_window",
        "description": "공정 윈도우 내 조건인지 검증합니다. 파라미터를 CSV 형식으로 입력합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "process_name": {
                    "type": "string",
                    "description": "공정 이름. 예: CVD"
                },
                "window_params": {
                    "type": "string",
                    "description": "공정 윈도우 CSV: '파라미터:최소:최대' 또는 '파라미터:최소-최대' 형식. 예: 'temperature:450:500,pressure:0.5:1.5' 또는 'temperature:450-500,pressure:0.5-1.5'"
                },
                "test_params": {
                    "type": "string",
                    "description": "검증할 조건 CSV: '파라미터:값' 쉼표로 구분. 예: 'temperature:480,pressure:0.8'"
                },
                "critical_params": {
                    "type": "string",
                    "description": "중요 파라미터 (선택): 쉼표로 구분. 예: 'temperature'"
                }
            },
            "required": ["process_name", "window_params", "test_params"]
        }
    },
    
    # 7. analyze_spc_data - 단순 파라미터
    {
        "name": "analyze_spc_data",
        "description": "SPC 데이터를 분석합니다 (ISO 22514 기준). 측정값을 쉼표로 구분하여 입력합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "parameter_name": {
                    "type": "string",
                    "description": "파라미터 이름. 예: CD, Temperature"
                },
                "data_points": {
                    "type": "string",
                    "description": "측정값 쉼표로 구분. 예: '45.2,45.8,44.9,46.1,45.5,45.3'"
                },
                "usl": {
                    "type": "number",
                    "description": "상한 스펙 (USL). 예: 50"
                },
                "lsl": {
                    "type": "number",
                    "description": "하한 스펙 (LSL). 예: 40"
                },
                "target": {
                    "type": "number",
                    "description": "목표값 (선택). 미입력시 (USL+LSL)/2"
                },
                "ucl": {
                    "type": "number",
                    "description": "상한 관리한계 (선택)"
                },
                "lcl": {
                    "type": "number",
                    "description": "하한 관리한계 (선택)"
                },
                "equipment_id": {
                    "type": "string",
                    "description": "장비 ID (선택)"
                }
            },
            "required": ["parameter_name", "data_points", "usl", "lsl"]
        }
    },
    
    # 8. predict_defect_risk - CSV 형식으로 단순화
    {
        "name": "predict_defect_risk",
        "description": "FMEA 기반 불량 위험도를 예측합니다. 공정 윈도우와 현재 조건을 CSV로 입력합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "process_name": {
                    "type": "string",
                    "description": "공정 이름. 예: Etch"
                },
                "window_params": {
                    "type": "string",
                    "description": "공정 윈도우 CSV: '파라미터:최소:최대' 또는 '파라미터:최소-최대' 형식. 예: 'temperature:100:130,pressure:50:100' 또는 'temperature:100-130,pressure:50-100'"
                },
                "current_params": {
                    "type": "string",
                    "description": "현재 조건 CSV: '파라미터:값' 쉼표로 구분. 예: 'temperature:128,pressure:92'"
                },
                "severity_params": {
                    "type": "string",
                    "description": "심각도 CSV (선택): '파라미터:1-10점수' 쉼표로 구분. 예: 'temperature:8,pressure:5'"
                },
                "critical_params": {
                    "type": "string",
                    "description": "중요 파라미터 (선택): 쉼표로 구분. 예: 'temperature'"
                }
            },
            "required": ["process_name", "window_params", "current_params"]
        }
    },
    
    # 9. analyze_trend - 단순 파라미터
    {
        "name": "analyze_trend",
        "description": "시계열 데이터의 트렌드를 분석합니다 (최소자승법, Mann-Kendall 검정).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "parameter_name": {
                    "type": "string",
                    "description": "파라미터 이름. 예: temperature"
                },
                "data_points": {
                    "type": "string",
                    "description": "측정값 쉼표로 구분. 예: '60.1,60.3,60.5,60.8,61.0,61.2'"
                },
                "timestamps": {
                    "type": "string",
                    "description": "시간 정보 (선택) 쉼표로 구분. 예: '10:00,11:00,12:00'"
                },
                "usl": {
                    "type": "number",
                    "description": "상한 스펙 (선택)"
                },
                "lsl": {
                    "type": "number",
                    "description": "하한 스펙 (선택)"
                },
                "forecast_count": {
                    "type": "integer",
                    "description": "예측할 포인트 수 (선택). 예: 3"
                }
            },
            "required": ["parameter_name", "data_points"]
        }
    },
    
    # 10. analyze_metrics - CSV 형식으로 단순화
    {
        "name": "analyze_metrics",
        "description": "KPI 메트릭을 목표 대비 분석합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "description": "분석 기간. 예: 2025년 1월 2주차"
                },
                "metrics_data": {
                    "type": "string",
                    "description": "현재 메트릭 CSV: '지표:값' 쉼표로 구분. 예: 'yield:97.8,cpk:1.28,uptime:89.5'"
                },
                "targets_data": {
                    "type": "string",
                    "description": "목표값 CSV: '지표:값' 쉼표로 구분. 예: 'yield:98,cpk:1.33,uptime:90'"
                },
                "equipment_id": {
                    "type": "string",
                    "description": "장비 ID (선택)"
                }
            },
            "required": ["period", "metrics_data", "targets_data"]
        }
    },
    
    # 11. generate_shift_report - CSV 형식으로 단순화
    {
        "name": "generate_shift_report",
        "description": "교대 근무 인수인계 리포트를 생성합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "shift_info": {
                    "type": "string",
                    "description": "교대 정보: '교대:날짜' 형식. 예: 'Day:2025-01-15'"
                },
                "production_data": {
                    "type": "string",
                    "description": "생산 데이터 CSV: 'in:투입,out:완료,target:목표,yield:수율'. 예: 'in:200,out:195,target:200,yield:98.2'"
                },
                "equipment_status": {
                    "type": "string",
                    "description": "장비 상태 CSV: '장비:상태:이슈' 세미콜론으로 구분. 예: 'ETCH-01:running:정상;ETCH-02:down:PM중'"
                },
                "quality_data": {
                    "type": "string",
                    "description": "품질 데이터. 예: 'defects:5,major:파티클3건'"
                },
                "events": {
                    "type": "string",
                    "description": "주요 이벤트 (선택) 세미콜론으로 구분. 예: '14:00 PM시작;16:00 온도경고'"
                },
                "pending_actions": {
                    "type": "string",
                    "description": "미결 조치 (선택) 세미콜론으로 구분. 예: 'ETCH-02 복구확인;CVD온도모니터링'"
                }
            },
            "required": ["shift_info", "production_data", "equipment_status", "quality_data"]
        }
    },
    
    # 12. analyze_equipment_comparison - CSV 형식으로 단순화
    {
        "name": "analyze_equipment_comparison",
        "description": "여러 장비의 성능을 비교 분석합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "equipment_list": {
                    "type": "string",
                    "description": "장비 목록 쉼표로 구분. 예: 'ETCH-01,ETCH-02,ETCH-03'"
                },
                "metrics_data": {
                    "type": "string",
                    "description": "장비별 메트릭 CSV: '장비:지표1:값1,지표2:값2' 세미콜론으로 구분. 예: 'ETCH-01:yield:98.5,cpk:1.45;ETCH-02:yield:97.2,cpk:1.28'"
                },
                "weights_csv": {
                    "type": "string",
                    "description": "가중치 (선택) CSV: '지표:가중치' 쉼표로 구분. 예: 'yield:0.4,cpk:0.3,uptime:0.3'"
                },
                "benchmark_csv": {
                    "type": "string",
                    "description": "벤치마크 (선택) CSV: '지표:값' 쉼표로 구분. 예: 'yield:98,cpk:1.33'"
                }
            },
            "required": ["equipment_list", "metrics_data"]
        }
    },
    
    # 13. optimize_recipe_direction - CSV 형식으로 단순화
    {
        "name": "optimize_recipe_direction",
        "description": "레시피 최적화 방향을 제안합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "recipe_csv": {
                    "type": "string",
                    "description": "현재 레시피 CSV: '파라미터:값' 쉼표로 구분. 예: 'temperature:67,pressure:28,rf_power:800'"
                },
                "perf_csv": {
                    "type": "string",
                    "description": "현재 성과 CSV: '지표:값' 쉼표로 구분. 예: 'yield:97.5,cpk:1.1'"
                },
                "target_csv": {
                    "type": "string",
                    "description": "목표 성과 CSV: '지표:값' 쉼표로 구분. 예: 'yield:98.5,cpk:1.33'"
                }
            },
            "required": ["recipe_csv", "perf_csv", "target_csv"]
        }
    },
    
    # 14. simulate_parameter_change - CSV 형식으로 단순화
    {
        "name": "simulate_parameter_change",
        "description": "파라미터 변경의 영향을 시뮬레이션합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "state_csv": {
                    "type": "string",
                    "description": "현재 상태 CSV: 'section:key:val,key:val' 세미콜론으로 구분. 예: 'recipe:temperature:120,time:300,pressure:75;performance:etch_rate:50,uniformity:91,yield:97'"
                },
                "changes_csv": {
                    "type": "string",
                    "description": "제안된 변경 CSV: '파라미터:새값' 쉼표로 구분. 예: 'time:250'"
                },
                "rules_csv": {
                    "type": "string",
                    "description": "영향 규칙 CSV: '변수->결과:효과' 세미콜론으로 구분. 예: 'time->etch_rate:-10;time->uniformity:-2' (또는 기존 'rule1:etch_rate:-10;rule2:uniformity:-2')"
                },
                "window_csv": {
                    "type": "string",
                    "description": "공정 윈도우 (선택) CSV: '파라미터:최소:최대' 또는 '파라미터:최소-최대' 형식. 예: 'temperature:100:140,pressure:50:100' 또는 'temperature:100-140,pressure:50-100'"
                }
            },
            "required": ["state_csv", "changes_csv", "rules_csv"]
        }
    },
    
    # 15. calculate_yield_impact - CSV 형식으로 단순화
    {
        "name": "calculate_yield_impact",
        "description": "파라미터 변경에 따른 수율 영향을 계산합니다 (DOE 기반, 단순화).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "baseline_yield": {
                    "type": "number",
                    "description": "기준 수율. 예: 97.5"
                },
                "changes_csv": {
                    "type": "string",
                    "description": "파라미터 변경 CSV: '파라미터:start:이전,end:새값,sensitivity:민감도' 세미콜론으로 구분. 예: 'temperature:start:65,end:70,sensitivity:0.8;pressure:start:30,end:33,sensitivity:0.1' (또는 기존 'temperature:65:70:0.8;pressure:30:33:0.1')"
                },
                "interactions_csv": {
                    "type": "string",
                    "description": "상호 작용 효과 (선택) CSV: '파라미터1×파라미터2:효과' 세미콜론으로 구분. 예: 'temperature×pressure:-0.2'"
                },
                "confidence_level": {
                    "type": "number",
                    "description": "신뢰도 (선택). 기본값: 0.95"
                },
                "model_type": {
                    "type": "string",
                    "description": "모델 유형 (선택). 기본값: linear"
                }
            },
            "required": ["baseline_yield", "changes_csv"]
        }
    }
]

TOOL_HANDLERS = {
    "analyze_defect": analyze_defect,
    "get_defect_history": get_defect_history,
    "suggest_corrective_action": suggest_corrective_action,
    "compare_to_baseline": compare_to_baseline,
    "compare_two_recipes": compare_two_recipes,
    "validate_process_window": validate_process_window,
    "analyze_spc_data": analyze_spc_data,
    "predict_defect_risk": predict_defect_risk,
    "analyze_trend": analyze_trend,
    "analyze_metrics": analyze_metrics,
    "generate_shift_report": generate_shift_report,
    "analyze_equipment_comparison": analyze_equipment_comparison,
    "optimize_recipe_direction": optimize_recipe_direction,
    "simulate_parameter_change": simulate_parameter_change,
    "calculate_yield_impact": calculate_yield_impact,
}


@app.get("/")
async def root():
    return {"service": "SemiProcess MCP", "spec": "2026-01-14", "health": "/health", "mcp": "/mcp", "tools_count": len(TOOLS)}


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "SemiProcess MCP", "version": "2.0.0"}


@app.post("/mcp")
async def mcp_endpoint(request: Request):
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
        if method == "notifications/initialized":
            return JSONResponse({"jsonrpc": "2.0", "id": request_id, "result": {}})
        if method == "tools/list":
            return JSONResponse({"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOLS}})
        if method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            handler = TOOL_HANDLERS.get(tool_name)
            if not handler:
                return JSONResponse(
                    {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}}
                )
            try:
                result = handler(**arguments)
                return JSONResponse(
                    {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": result}]}}
                )
            except TypeError as e:
                return JSONResponse(
                    {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": f"Invalid parameters: {e}"}}
                )
            except Exception as e:
                return JSONResponse(
                    {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32603, "message": f"Tool execution error: {e}"}}
                )
        return JSONResponse({"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"Method not found: {method}"}})
    except Exception as e:
        return JSONResponse({"jsonrpc": "2.0", "id": 1, "error": {"code": -32700, "message": f"Parse error: {e}"}}, status_code=400)


@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)
