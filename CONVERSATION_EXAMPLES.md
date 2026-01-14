# SemiProcess MCP 대화 예시

반도체 공정 분석 및 문제 해결을 위한 MCP 도구 사용 예시입니다. (CSV 형식 버전)

---

## 1. 불량 분석

**사용자:**
```
CMP 공정에서 웨이퍼 가장자리에서 깊은 스크래치가 발견되었어. 
웨이퍼 ID는 W12345, 장비는 CMP-02, 최근 패드를 교체했고 슬러리 Lot도 변경했어.
원인 분석 좀 해줄래?
```

**MCP 도구 호출:**
```json
{
  "name": "analyze_defect",
  "arguments": {
    "defect_code": "SCRATCH",
    "defect_description": "웨이퍼 가장자리 깊은 스크래치",
    "process_step": "CMP",
    "equipment_id": "CMP-02",
    "wafer_id": "W12345",
    "known_causes": ["패드 마모", "슬러리 오염"],
    "recent_changes": ["패드 교체", "슬러리 Lot 변경"]
  }
}
```

---

## 2. 불량 이력 분석

**사용자:**
```
지난 3주일 간 스크래치 불량이 자꾸 발생해. 
이 데이터로 패턴을 찾아줄 수 있을까?

2025-01-10, CMP-01, 3개, 패드교체, 해결
2025-01-08, CMP-02, 5개, 필터교체, 진행중
2025-01-06, CMP-03, 2개, 슬러리교체, 해결
2025-01-04, CMP-01, 4개, PM수행, 해결
```

**MCP 도구 호출:**
```json
{
  "name": "get_defect_history",
  "arguments": {
    "defect_type": "SCRATCH",
    "records_csv": "2025-01-10,CMP-01,3,패드교체,해결;2025-01-08,CMP-02,5,필터교체,진행중;2025-01-06,CMP-03,2,슬러리교체,해결;2025-01-04,CMP-01,4,PM수행,해결",
    "analysis_type": "equipment"
  }
}
```

---

## 3. 시정 조치 제안

**사용자:**
```
ETCH-01에서 갑자기 압력이 불안정해지고 있어. 
재시작 후에도 계속 알람이 뜨고 있고, 엔지니어 2명이랑 필터 예비가 있어.
지금 즉시 어떻게 해야 해? (내 시간 제약은 2시간)
```

**MCP 도구 호출:**
```json
{
  "name": "suggest_corrective_action",
  "arguments": {
    "problem_description": "압력 불안정",
    "affected_equipment": "ETCH-01",
    "severity": "critical",
    "current_status": "재시작 후에도 알람 반복 발생",
    "available_resources": ["엔지니어 2명", "필터 예비"],
    "time_constraint": "2시간 내"
  }
}
```

---

## 4. 기준 레시피 비교

**사용자:**
```
Oxide Etch 공정의 기준 레시피는:
- 온도: 표준 60, 범위 55~65°C
- 압력: 표준 30, 범위 25~35 mTorr

지금 현재 설정이:
- 온도: 67°C
- 압력: 28 mTorr

이게 정상 범위 내인지 확인해줄래?
```

**MCP 도구 호출:**
```json
{
  "name": "compare_to_baseline",
  "arguments": {
    "recipe_name": "Oxide Etch",
    "baseline_params": "temperature:60:55:65,pressure:30:25:35",
    "baseline_units": "C,mTorr",
    "current_params": "temperature:67,pressure:28",
    "current_units": "C,mTorr"
  }
}
```

---

## 5. 두 레시피 비교

**사용자:**
```
A라인과 B라인의 레시피 설정을 비교하고 싶어.

A라인: temperature 60, pressure 30, rf_power 800
B라인: temperature 62, pressure 28, rf_power 820

허용 편차: ±5% 정도?
```

**MCP 도구 호출:**
```json
{
  "name": "compare_two_recipes",
  "arguments": {
    "recipe_a_name": "A라인",
    "recipe_a_params": "temperature:60,pressure:30,rf_power:800",
    "recipe_b_name": "B라인",
    "recipe_b_params": "temperature:62,pressure:28,rf_power:820",
    "tolerance_params": "temperature:5%,pressure:10%,rf_power:5%"
  }
}
```

---

## 6. 공정 윈도우 검증

**사용자:**
```
CVD 공정 온도 검증이 필요해.

공정 윈도우:
- 온도: 450~500°C
- 압력: 0.5~1.5 Torr

현재 설정:
- 온도: 480°C
- 압력: 0.8 Torr

중요 파라미터는 온도가 맞아.
이 조건이 유효한지 확인해줄래?
```

**MCP 도구 호출:**
```json
{
  "name": "validate_process_window",
  "arguments": {
    "process_name": "CVD",
    "window_params": "temperature:450-500,pressure:0.5-1.5",
    "test_params": "temperature:480,pressure:0.8",
    "critical_params": "temperature"
  }
}
```

---

## 7. SPC 데이터 분석

**사용자:**
```
이번 주 CD 측정값들을 SPC 분석해줄래?

측정값: 45.2, 45.8, 44.9, 46.1, 45.5, 45.3, 45.7, 46.0 nm

스펙: USL 50nm, LSL 40nm
목표: 45nm
```

**MCP 도구 호출:**
```json
{
  "name": "analyze_spc_data",
  "arguments": {
    "parameter_name": "CD",
    "data_points": "45.2,45.8,44.9,46.1,45.5,45.3,45.7,46.0",
    "usl": 50,
    "lsl": 40,
    "target": 45
  }
}
```

---

## 8. 불량 위험도 예측 (FMEA)

**사용자:**
```
현재 ETCH 공정의 리스크를 FMEA로 평가해줄래?

공정 윈도우:
- 온도: 100~130°C
- 압력: 50~100 mTorr

현재 설정:
- 온도: 128°C
- 압력: 92 mTorr

중요 파라미터는 온도야.
온도 심각도는 8/10, 압력은 5/10 정도로 봐.
```

**MCP 도구 호출:**
```json
{
  "name": "predict_defect_risk",
  "arguments": {
    "process_name": "Etch",
    "window_params": "temperature:100-130,pressure:50-100",
    "current_params": "temperature:128,pressure:92",
    "severity_params": "temperature:8,pressure:5",
    "critical_params": "temperature"
  }
}
```

---

## 9. 트렌드 분석

**사용자:**
```
어제 오전 ETCH-01의 온도 추이를 분석해줄 수 있을까?

시간: 08:00, 09:00, 10:00, 11:00, 12:00, 13:00
온도: 120.1, 120.3, 120.5, 121.2, 121.8, 122.3°C

스펙은 120~125°C고, 
앞으로 3시간 더 추이를 예측해줄 수 있을까?
```

**MCP 도구 호출:**
```json
{
  "name": "analyze_trend",
  "arguments": {
    "parameter_name": "Temperature",
    "data_points": "120.1,120.3,120.5,121.2,121.8,122.3",
    "timestamps": "08:00,09:00,10:00,11:00,12:00,13:00",
    "usl": 125,
    "lsl": 120,
    "forecast_count": 3
  }
}
```

---

## 10. 메트릭 분석

**사용자:**
```
이번 주(1월 2주차) KPI를 목표와 비교해줄 수 있을까?

현재:
- 수율: 97.8%
- CPK: 1.28
- 가동률: 89.5%

목표:
- 수율: 98%
- CPK: 1.33
- 가동률: 90%
```

**MCP 도구 호출:**
```json
{
  "name": "analyze_metrics",
  "arguments": {
    "period": "2025년 1월 2주차",
    "metrics_data": "yield:97.8,cpk:1.28,uptime:89.5",
    "targets_data": "yield:98,cpk:1.33,uptime:90"
  }
}
```

---

## 11. 교대 리포트 생성

**사용자:**
```
오늘 일근(Day shift) 교대 리포트를 만들어줄래?

날짜: 2025-01-15
투입: 200매, 완료: 195매, 목표: 200매, 수율: 98.2%

장비 상태:
- ETCH-01: 정상 운영
- ETCH-02: PM 진행 중
- CVD-01: 정상 운영

불량: 5개 (파티클 3건, 스크래치 2건)

주요 이벤트:
- 14:00 PM 시작
- 16:00 온도 경고

미결 조치:
- ETCH-02 복구 확인
- 온도 모니터링
```

**MCP 도구 호출:**
```json
{
  "name": "generate_shift_report",
  "arguments": {
    "shift_info": "Day:2025-01-15",
    "production_data": "in:200,out:195,target:200,yield:98.2",
    "equipment_status": "ETCH-01:running:정상;ETCH-02:down:PM중;CVD-01:running:정상",
    "quality_data": "defects:5,major:파티클3건+스크래치2건",
    "events": "14:00 PM시작;16:00 온도경고",
    "pending_actions": "ETCH-02복구확인;온도모니터링"
  }
}
```

---

## 12. 장비 비교 분석

**사용자:**
```
우리 CMP 장비 3대의 성능을 비교하고 싶어.

CMP-01: 수율 98.5%, CPK 1.45, 가동률 92%
CMP-02: 수율 97.2%, CPK 1.28, 가동률 88%
CMP-03: 수율 98.1%, CPK 1.38, 가동률 91%

가중치: 수율 40%, CPK 30%, 가동률 30%

벤치마크:
수율 98%, CPK 1.33, 가동률 90%
```

**MCP 도구 호출:**
```json
{
  "name": "analyze_equipment_comparison",
  "arguments": {
    "equipment_list": "CMP-01,CMP-02,CMP-03",
    "metrics_data": "CMP-01:yield:98.5,cpk:1.45,uptime:92;CMP-02:yield:97.2,cpk:1.28,uptime:88;CMP-03:yield:98.1,cpk:1.38,uptime:91",
    "weights_csv": "yield:0.4,cpk:0.3,uptime:0.3",
    "benchmark_csv": "yield:98,cpk:1.33,uptime:90"
  }
}
```

---

## 13. 레시피 최적화 방향

**사용자:**
```
CVD 공정 레시피를 개선하고 싶어.

현재 레시피:
- 온도: 450°C
- 압력: 1.0 Torr
- 시간: 300초

현재 성과:
- 박막 두께: 950 nm
- 균일성: 92%
- 수율: 97%

목표 성과:
- 박막 두께: 1000 nm
- 균일성: 95%
- 수율: 98%
```

**MCP 도구 호출:**
```json
{
  "name": "optimize_recipe_direction",
  "arguments": {
    "recipe_csv": "temperature:450,pressure:1.0,time:300",
    "perf_csv": "thickness:950,uniformity:92,yield:97",
    "target_csv": "thickness:1000,uniformity:95,yield:98"
  }
}
```

---

## 14. 파라미터 변경 시뮬레이션

**사용자:**
```
ETCH 시간을 300초에서 250초로 줄일 수 있을까?

현재 상태:
- 레시피: temperature 120, time 300, pressure 75
- 성과: etch_rate 50, uniformity 91, yield 97
- 윈도우: temp 100-140, pressure 50-100

시간 단축 시 예상 영향:
- etch_rate는 시간 단축 시 10 감소
- uniformity는 2% 악화
```

**MCP 도구 호출:**
```json
{
  "name": "simulate_parameter_change",
  "arguments": {
    "state_csv": "recipe:temperature:120,time:300,pressure:75;performance:etch_rate:50,uniformity:91,yield:97",
    "changes_csv": "time:250",
    "rules_csv": "time->etch_rate:-10;time->uniformity:-2",
    "window_csv": "temperature:100-140,pressure:50-100"
  }
}
```

---

## 15. 수율 영향도 계산 (DOE)

**사용자:**
```
온도를 +5°C, 압력을 +3 mTorr 올릴 경우
수율이 어떻게 변할까?

현재 기준 수율: 97.5%

파라미터 변경:
1. 온도: 65 → 70°C (영향도: 0.8%/°C)
2. 압력: 30 → 33 mTorr (영향도: 0.1%/mTorr)

상호작용 효과:
- 온도×압력: -0.2%

신뢰도: 95%
```

**MCP 도구 호출:**
```json
{
  "name": "calculate_yield_impact",
  "arguments": {
    "baseline_yield": 97.5,
    "changes_csv": "temperature:start:65,end:70,sensitivity:0.8;pressure:start:30,end:33,sensitivity:0.1",
    "interactions_csv": "temperature×pressure:-0.2",
    "confidence_level": 0.95,
    "model_type": "linear"
  }
}
```

---

**Last Updated**: 2025-01-15  
**MCP Version**: 2.0.0  
**Format**: CSV-based input schema
