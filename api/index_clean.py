"""
SemiProcess MCP Server - 15개 Tool (사용자 입력 기반)
"""

from typing import Any, Dict, List, Optional
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

app = FastAPI(title="SemiProcess MCP Server")

DISCLAIMER = """
📌 안내: 본 분석 결과는 사용자가 입력한 데이터를 기반으로 생성되었습니다.
실제 의사결정 시 현장 상황과 전문가 검토를 병행하세요.
"""


def _missing(req: List[str], provided: Dict[str, Any]) -> List[str]:
    return [k for k in req if provided.get(k) is None]


def _err(missing: List[str]) -> str:
    return f"{DISCLAIMER}\n\n## ⚠️ 입력 오류\n" + "\n".join(f"- `{m}` 누락" for m in missing)


# ----- Tools -----
def analyze_defect(defect_code: str, defect_description: str, process_step: str,
                   equipment_id: str = None, wafer_id: str = None,
                   known_causes: Optional[List[str]] = None, recent_changes: Optional[List[str]] = None) -> str:
    miss = _missing(["defect_code", "defect_description", "process_step"], locals())
    if miss:
        return _err(miss)
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


def get_defect_history(defect_records: List[Dict[str, Any]], analysis_type: str = "trend") -> str:
    miss = _missing(["defect_records"], locals())
    if miss:
        return _err(miss)
    if not defect_records:
        return f"{DISCLAIMER}\n\n## ⚠️ 입력 오류\n불량 이력이 비어 있습니다."
    rows = "\n".join(
        f"| {r.get('date','-')} | {r.get('defect_type','-')} | {r.get('equipment_id','-')} | {r.get('wafer_count','-')} | {r.get('action_taken','-')} | {r.get('result','-')} |"
        for r in defect_records
    )
    return (
        f"{DISCLAIMER}\n\n## 📊 불량 이력 ({analysis_type})\n"
        f"| 날짜 | 불량 | 장비 | 웨이퍼 | 조치 | 결과 |\n|------|------|------|--------|------|------|\n{rows}\n"
    )


def suggest_corrective_action(problem_description: str, affected_equipment: str, severity: str, current_status: str,
                              available_resources: Optional[List[str]] = None, time_constraint: str = None) -> str:
    miss = _missing(["problem_description", "affected_equipment", "severity", "current_status"], locals())
    if miss:
        return _err(miss)
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


def compare_to_baseline(baseline_recipe: Dict[str, Dict[str, Any]], current_recipe: Dict[str, float], recipe_name: str = None) -> str:
    miss = _missing(["baseline_recipe", "current_recipe"], locals())
    if miss:
        return _err(miss)
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


def compare_two_recipes(recipe_a: Dict[str, float], recipe_b: Dict[str, float], recipe_a_name: str = "Recipe A",
                        recipe_b_name: str = "Recipe B", tolerance: Optional[Dict[str, float]] = None) -> str:
    miss = _missing(["recipe_a", "recipe_b"], locals())
    if miss:
        return _err(miss)
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
        f"{DISCLAIMER}\n\n## 🔄 두 레시피 비교\n- {recipe_a_name} vs {recipe_b_name}\n\n"
        f"| 파라미터 | {recipe_a_name} | {recipe_b_name} | 상태 |\n|----------|---------------|---------------|------|\n{table}\n"
    )


def validate_process_window(process_window: Dict[str, Dict[str, Any]], test_conditions: Dict[str, float],
                            critical_params: Optional[List[str]] = None) -> str:
    miss = _missing(["process_window", "test_conditions"], locals())
    if miss:
        return _err(miss)
    rows = []
    alerts = []
    for p, lim in process_window.items():
        val = test_conditions.get(p)
        min_v, max_v = lim.get("min"), lim.get("max")
        status = "✅ PASS"
        if val is None or (min_v is not None and val < min_v) or (max_v is not None and val > max_v):
            status = "❌ FAIL"
            if critical_params and p in critical_params:
                alerts.append(f"- 중요 {p}: {val} (범위 {min_v}-{max_v})")
        rows.append(f"| {p} | {val} | {min_v}-{max_v} | {status} |")
    return (
        f"{DISCLAIMER}\n\n## ✔️ 공정 윈도우 검증\n"
        f"| 파라미터 | 입력값 | 범위 | 결과 |\n|----------|--------|------|------|\n" + "\n".join(rows) + "\n\n"
        f"### 위험 파라미터\n" + ("\n".join(alerts) if alerts else "- 없음")
    )


def analyze_metrics(metrics_data: Dict[str, float], targets: Dict[str, float], period: str = None, equipment_id: str = None) -> str:
    miss = _missing(["metrics_data", "targets"], locals())
    if miss:
        return _err(miss)
    rows = []
    for k, target in targets.items():
        cur = metrics_data.get(k)
        status = "❌ 미달" if cur is None or cur < target else "✅ 달성"
        rows.append(f"| {k} | {cur} | {target} | {status} |")
    return (
        f"{DISCLAIMER}\n\n## 📈 메트릭 분석\n- 기간: {period or '미입력'} / 장비: {equipment_id or '전체'}\n\n"
        f"| 지표 | 현재 | 목표 | 상태 |\n|------|------|------|------|\n" + "\n".join(rows)
    )


def analyze_spc_data(data_points: List[float], spec_limits: Dict[str, float], control_limits: Optional[Dict[str, float]] = None,
                     parameter_name: str = None, equipment_id: str = None) -> str:
    miss = _missing(["data_points", "spec_limits"], locals())
    if miss:
        return _err(miss)
    if not data_points:
        return f"{DISCLAIMER}\n\n## ⚠️ 입력 오류\n데이터 포인트가 비어 있습니다."
    import statistics
    mean_val = statistics.mean(data_points)
    stdev_val = statistics.pstdev(data_points) if len(data_points) > 1 else 0.0
    usl, lsl = spec_limits.get("usl"), spec_limits.get("lsl")
    ucl = control_limits.get("ucl") if control_limits else mean_val + 3 * stdev_val
    lcl = control_limits.get("lcl") if control_limits else mean_val - 3 * stdev_val
    cp = (usl - lsl) / (6 * stdev_val) if stdev_val and usl is not None and lsl is not None else 0.0
    cpk = min((usl - mean_val), (mean_val - lsl)) / (3 * stdev_val) if stdev_val and usl is not None and lsl is not None else 0.0
    return (
        f"{DISCLAIMER}\n\n## 📊 SPC 데이터 분석\n"
        f"- 파라미터: {parameter_name or '미입력'} / 장비: {equipment_id or '미입력'}\n"
        f"- 평균: {mean_val:.3f}, σ: {stdev_val:.3f}, Cp/Cpk: {cp:.2f}/{cpk:.2f}, UCL/LCL: {ucl:.3f}/{lcl:.3f}\n"
    )


def predict_defect_risk(process_window: Dict[str, Dict[str, float]], current_conditions: Dict[str, float],
                        critical_params: Optional[List[str]] = None, historical_defect_correlation: Optional[Dict[str, str]] = None) -> str:
    miss = _missing(["process_window", "current_conditions"], locals())
    if miss:
        return _err(miss)
    critical_params = critical_params or []
    historical_defect_correlation = historical_defect_correlation or {}
    rows = []
    for p, lim in process_window.items():
        val = current_conditions.get(p)
        rows.append(f"- {p}: {val} (범위 {lim.get('min')}-{lim.get('max')}, 상관 {historical_defect_correlation.get(p,'N/A')})")
    return (
        f"{DISCLAIMER}\n\n## 🔮 불량 위험도 예측\n"
        f"- 중요 파라미터: {', '.join(critical_params) if critical_params else '미입력'}\n"
        f"### 파라미터별 요약\n" + "\n".join(rows)
    )


def optimize_recipe_direction(current_recipe: Dict[str, float], current_performance: Dict[str, float], target_performance: Dict[str, float],
                              param_sensitivity: Optional[Dict[str, str]] = None, constraints: Optional[Dict[str, Dict[str, float]]] = None) -> str:
    miss = _missing(["current_recipe", "current_performance", "target_performance"], locals())
    if miss:
        return _err(miss)
    param_sensitivity = param_sensitivity or {}
    rows = [f"- {p}: 민감도 {param_sensitivity.get(p,'MEDIUM')}, 제약 {constraints.get(p) if constraints else 'N/A'}" for p in current_recipe]
    return (
        f"{DISCLAIMER}\n\n## ⚙️ 레시피 최적화 방향\n"
        f"### 조정 후보\n" + "\n".join(rows)
    )


def simulate_parameter_change(current_state: Dict[str, Any], proposed_changes: Dict[str, float], impact_rules: List[Dict[str, Any]],
                              process_window: Optional[Dict[str, Dict[str, float]]] = None) -> str:
    miss = _missing(["current_state", "proposed_changes", "impact_rules"], locals())
    if miss:
        return _err(miss)
    return (
        f"{DISCLAIMER}\n\n## 🧪 파라미터 변경 시뮬레이션\n"
        f"- 변경안: {proposed_changes}\n- 영향 규칙: {impact_rules}\n- 윈도우: {process_window or '미입력'}\n"
    )


def calculate_yield_impact(baseline_yield: float, parameter_changes: List[Dict[str, Any]],
                           interaction_effects: Optional[List[Dict[str, Any]]] = None) -> str:
    miss = _missing(["baseline_yield", "parameter_changes"], locals())
    if miss:
        return _err(miss)
    return (
        f"{DISCLAIMER}\n\n## 🎯 수율 영향 계산\n"
        f"- 기준 수율: {baseline_yield}%\n- 변경 목록: {parameter_changes}\n- 상호작용: {interaction_effects or '미입력'}\n"
    )


def analyze_equipment_comparison(equipment_data: List[Dict[str, Any]], weights: Optional[Dict[str, float]] = None,
                                 benchmark: Optional[Dict[str, float]] = None) -> str:
    miss = _missing(["equipment_data"], locals())
    if miss:
        return _err(miss)
    rows = "\n".join(f"- {e.get('equipment_id','?')}: {e.get('metrics',{})}" for e in equipment_data)
    return (
        f"{DISCLAIMER}\n\n## 🏭 장비 비교 분석\n"
        f"### 장비별 메트릭\n{rows}\n### 가중치\n{weights or '미입력'}\n### 벤치마크\n{benchmark or '미입력'}\n"
    )


def generate_shift_report(production_summary: Dict[str, Any], equipment_status: List[Dict[str, Any]], quality_summary: Dict[str, Any],
                          key_events: Optional[List[Dict[str, Any]]] = None, pending_actions: Optional[List[str]] = None,
                          shift_info: Optional[Dict[str, str]] = None) -> str:
    miss = _missing(["production_summary", "equipment_status", "quality_summary"], locals())
    if miss:
        return _err(miss)
    return (
        f"{DISCLAIMER}\n\n## 📝 교대 리포트\n"
        f"- 교대: {shift_info or '미입력'}\n- 생산: {production_summary}\n- 장비: {equipment_status}\n- 품질: {quality_summary}\n"
        f"- 이벤트: {key_events or '없음'}\n- 미결: {pending_actions or '없음'}\n"
    )


def analyze_trend(time_series_data: List[Dict[str, Any]], parameter_name: str, spec_limits: Optional[Dict[str, float]] = None,
                  analysis_options: Optional[Dict[str, Any]] = None) -> str:
    miss = _missing(["time_series_data", "parameter_name"], locals())
    if miss:
        return _err(miss)
    values = [d.get("value") for d in time_series_data if d.get("value") is not None]
    if not values:
        return f"{DISCLAIMER}\n\n## ⚠️ 입력 오류\n시계열 값이 없습니다."
    import statistics
    mean_val = statistics.mean(values)
    return (
        f"{DISCLAIMER}\n\n## 📈 트렌드 분석: {parameter_name}\n"
        f"- 평균: {mean_val:.3f}\n- 값 개수: {len(values)}\n- 스펙: {spec_limits or '미입력'}\n- 옵션: {analysis_options or '기본'}\n"
    )


TOOLS = [
    {"name": "analyze_defect", "description": "불량 분석(사용자 입력 기반)", "inputSchema": {
        "type": "object",
        "properties": {
            "defect_code": {"type": "string"},
            "defect_description": {"type": "string"},
            "process_step": {"type": "string"},
            "equipment_id": {"type": "string"},
            "wafer_id": {"type": "string"},
            "known_causes": {"type": "array", "items": {"type": "string"}},
            "recent_changes": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["defect_code", "defect_description", "process_step"],
    }},
    {"name": "get_defect_history", "description": "불량 이력 패턴 분석", "inputSchema": {
        "type": "object",
        "properties": {
            "defect_records": {"type": "array", "items": {"type": "object"}},
            "analysis_type": {"type": "string"},
        },
        "required": ["defect_records"],
    }},
    {"name": "suggest_corrective_action", "description": "시정 조치 가이드", "inputSchema": {
        "type": "object",
        "properties": {
            "problem_description": {"type": "string"},
            "affected_equipment": {"type": "string"},
            "severity": {"type": "string", "enum": ["critical", "major", "minor"]},
            "current_status": {"type": "string"},
            "available_resources": {"type": "array", "items": {"type": "string"}},
            "time_constraint": {"type": "string"},
        },
        "required": ["problem_description", "affected_equipment", "severity", "current_status"],
    }},
    {"name": "compare_to_baseline", "description": "기준 레시피 대비 비교", "inputSchema": {
        "type": "object",
        "properties": {
            "baseline_recipe": {"type": "object"},
            "current_recipe": {"type": "object"},
            "recipe_name": {"type": "string"},
        },
        "required": ["baseline_recipe", "current_recipe"],
    }},
    {"name": "compare_two_recipes", "description": "두 레시피 비교", "inputSchema": {
        "type": "object",
        "properties": {
            "recipe_a": {"type": "object"},
            "recipe_b": {"type": "object"},
            "recipe_a_name": {"type": "string"},
            "recipe_b_name": {"type": "string"},
            "tolerance": {"type": "object"},
        },
        "required": ["recipe_a", "recipe_b"],
    }},
    {"name": "validate_process_window", "description": "공정 윈도우 검증", "inputSchema": {
        "type": "object",
        "properties": {
            "process_window": {"type": "object"},
            "test_conditions": {"type": "object"},
            "critical_params": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["process_window", "test_conditions"],
    }},
    {"name": "analyze_metrics", "description": "메트릭 목표 대비 분석", "inputSchema": {
        "type": "object",
        "properties": {
            "metrics_data": {"type": "object"},
            "targets": {"type": "object"},
            "period": {"type": "string"},
            "equipment_id": {"type": "string"},
        },
        "required": ["metrics_data", "targets"],
    }},
    {"name": "analyze_spc_data", "description": "SPC 데이터 분석", "inputSchema": {
        "type": "object",
        "properties": {
            "data_points": {"type": "array", "items": {"type": "number"}},
            "spec_limits": {"type": "object"},
            "control_limits": {"type": "object"},
            "parameter_name": {"type": "string"},
            "equipment_id": {"type": "string"},
        },
        "required": ["data_points", "spec_limits"],
    }},
    {"name": "predict_defect_risk", "description": "불량 위험도 예측", "inputSchema": {
        "type": "object",
        "properties": {
            "process_window": {"type": "object"},
            "current_conditions": {"type": "object"},
            "critical_params": {"type": "array", "items": {"type": "string"}},
            "historical_defect_correlation": {"type": "object"},
        },
        "required": ["process_window", "current_conditions"],
    }},
    {"name": "optimize_recipe_direction", "description": "레시피 최적화 방향 제안", "inputSchema": {
        "type": "object",
        "properties": {
            "current_recipe": {"type": "object"},
            "current_performance": {"type": "object"},
            "target_performance": {"type": "object"},
            "param_sensitivity": {"type": "object"},
            "constraints": {"type": "object"},
        },
        "required": ["current_recipe", "current_performance", "target_performance"],
    }},
    {"name": "simulate_parameter_change", "description": "파라미터 변경 시뮬레이션", "inputSchema": {
        "type": "object",
        "properties": {
            "current_state": {"type": "object"},
            "proposed_changes": {"type": "object"},
            "impact_rules": {"type": "array", "items": {"type": "object"}},
            "process_window": {"type": "object"},
        },
        "required": ["current_state", "proposed_changes", "impact_rules"],
    }},
    {"name": "calculate_yield_impact", "description": "수율 영향 계산", "inputSchema": {
        "type": "object",
        "properties": {
            "baseline_yield": {"type": "number"},
            "parameter_changes": {"type": "array", "items": {"type": "object"}},
            "interaction_effects": {"type": "array", "items": {"type": "object"}},
        },
        "required": ["baseline_yield", "parameter_changes"],
    }},
    {"name": "analyze_equipment_comparison", "description": "장비 비교 분석", "inputSchema": {
        "type": "object",
        "properties": {
            "equipment_data": {"type": "array", "items": {"type": "object"}},
            "weights": {"type": "object"},
            "benchmark": {"type": "object"},
        },
        "required": ["equipment_data"],
    }},
    {"name": "generate_shift_report", "description": "교대 리포트 생성", "inputSchema": {
        "type": "object",
        "properties": {
            "production_summary": {"type": "object"},
            "equipment_status": {"type": "array", "items": {"type": "object"}},
            "quality_summary": {"type": "object"},
            "key_events": {"type": "array", "items": {"type": "object"}},
            "pending_actions": {"type": "array", "items": {"type": "string"}},
            "shift_info": {"type": "object"},
        },
        "required": ["production_summary", "equipment_status", "quality_summary"],
    }},
    {"name": "analyze_trend", "description": "트렌드 분석", "inputSchema": {
        "type": "object",
        "properties": {
            "time_series_data": {"type": "array", "items": {"type": "object"}},
            "parameter_name": {"type": "string"},
            "spec_limits": {"type": "object"},
            "analysis_options": {"type": "object"},
        },
        "required": ["time_series_data", "parameter_name"],
    }},
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
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2026-01-14",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "SemiProcess MCP", "version": "2.0.0"},
                },
            })
        if method == "notifications/initialized":
            return JSONResponse({"jsonrpc": "2.0", "id": request_id, "result": {}})
        if method == "tools/list":
            return JSONResponse({"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOLS}})
        if method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            handler = TOOL_HANDLERS.get(tool_name)
            if not handler:
                return JSONResponse({"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}})
            try:
                result = handler(**arguments)
                return JSONResponse({"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": result}]}})
            except TypeError as e:
                return JSONResponse({"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": f"Invalid parameters: {e}"}})
            except Exception as e:
                return JSONResponse({"jsonrpc": "2.0", "id": request_id, "error": {"code": -32603, "message": f"Tool execution error: {e}"}})
        return JSONResponse({"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"Method not found: {method}"}})
    except Exception as e:
        return JSONResponse({"jsonrpc": "2.0", "id": 1, "error": {"code": -32700, "message": f"Parse error: {e}"}}, status_code=400)


@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)
