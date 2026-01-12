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