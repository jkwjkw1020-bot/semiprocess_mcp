# SemiProcess MCP 대화 예시

반도체 공정 분석 및 문제 해결을 위한 MCP 도구 사용 예시입니다.

---

## 1. 불량 분석 시나리오

### 예시 1-1: 웨이퍼 스크래치 불량 분석

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

**예상 응답:**
```
## 🔍 불량 분석

- 코드: SCRATCH
- 설명: 웨이퍼 가장자리 깊은 스크래치
- 공정: CMP
- 장비: CMP-02 / 웨이퍼: W12345

### 사용자 제안 원인
- 패드 마모
- 슬러리 오염

### 일반 점검
- 장비 알람/로그
- 최근 PM/캘리브레이션
- 레시피 변경 이력
- 소재/케미 Lot
- SPC/Lot 편차

### 최근 변경 사항
- 패드 교체
- 슬러리 Lot 변경
```

---

## 2. 불량 이력 패턴 분석

### 예시 2-1: 월별 스크래치 불량 추이 분석

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

**예상 응답:**
```
## 📊 불량 이력 분석 (equipment)

- 총 이력: 4건
- 불량 웨이퍼 합계: 14매
- 사용된 조치: 패드교체, 필터교체, 슬러리교체, PM수행

| 날짜 | 불량 | 장비 | 웨이퍼 | 조치 | 결과 |
|------|------|------|--------|------|------|
| 2025-01-10 | SCRATCH | CMP-01 | 3 | 패드교체 | 해결 |
| 2025-01-08 | SCRATCH | CMP-02 | 5 | 필터교체 | 진행중 |
| 2025-01-06 | SCRATCH | CMP-03 | 2 | 슬러리교체 | 해결 |
| 2025-01-04 | SCRATCH | CMP-01 | 4 | PM수행 | 해결 |

### 패턴 발견
- 장비 집중도 상위
- CMP-01: 2회
- CMP-02: 1회
- CMP-03: 1회
```

---

## 3. 시정 조치 제안

### 예시 3-1: ETCH 장비 압력 불안정 긴급 대응

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

**예상 응답:**
```
## ⚡ 긴급 시정 조치

### 즉시 조치 (Critical)
- 즉시 장비 정지
- 영향 Lot 격리
- 전문 엔지니어 호출

### 1단계 (0~30분)
1. 압력 센서 점검
2. 진공 라인 확인
3. 필터 상태 확인 → 예비 필터 교체 검토

### 2단계 (30~90분)
- 필터 교체 실행
- 시스템 재시작 및 압력 안정화 확인
- 5회 이상 안정성 테스트

### 3단계 (90~120분)
- 로그 분석 및 근본 원인 규명
- 재운영 권고 또는 추가 조사 계획

### 리스크
- 2시간 내 미해결 시 재운영 불가능
```

---

## 4. 레시피 비교

### 예시 4-1: 기준 레시피 대비 현재 레시피 편차 확인

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
    "baseline_params": "temperature:60:55:65:C,pressure:30:25:35:mTorr",
    "current_params": "temperature:67,pressure:28"
  }
}
```

**예상 응답:**
```
## 📊 기준 레시피 비교 (Oxide Etch)

### 파라미터 편차 분석

| 파라미터 | 기준값 | 현재값 | 편차 | 범위 | 상태 |
|----------|--------|--------|------|------|------|
| temperature | 60°C | 67°C | +7°C | 55~65 | ⚠️ 상한초과 |
| pressure | 30 mTorr | 28 mTorr | -2 mTorr | 25~35 | ✓ 정상 |

### ⚠️ 경고
- 온도가 기준값보다 7°C 높음 (상한 65°C 초과)
- 즉시 조정 필요
```

---

## 5. 두 레시피 비교

### 예시 5-1: A라인 vs B라인 레시피 비교

**사용자:**
```
A라인과 B라인의 레시피 설정을 비교하고 싶어.
각 라인의 온도, 압력, RF 파워가 다르거든.

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
    "tolerance_params": "temperature:5,pressure:10,rf_power:5"
  }
}
```

**예상 응답:**
```
## 📈 레시피 비교 분석

### 파라미터별 비교

| 파라미터 | A라인 | B라인 | 차이 | 허용편차 | 평가 |
|----------|-------|-------|------|---------|------|
| temperature | 60 | 62 | +2 | 5% | ✓ 범위내 |
| pressure | 30 | 28 | -2 | 10% | ✓ 범위내 |
| rf_power | 800 | 820 | +20 | 5% | ⚠️ 초과 |

### 종합 평가
- RF 파워 편차가 2.5% 초과
- 다른 파라미터는 모두 정상
- B라인이 더 높은 에너지 공급
```

---

## 6. 공정 윈도우 검증

### 예시 6-1: CVD 공정 현재 조건 검증

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
    "window_params": "temperature:450:500,pressure:0.5:1.5",
    "test_params": "temperature:480,pressure:0.8",
    "critical_params": "temperature"
  }
}
```

**예상 응답:**
```
## ✓ 공정 윈도우 검증 결과

### 검증 조건
- 공정: CVD
- 중요 파라미터: temperature

### 파라미터별 상태

| 파라미터 | 현재값 | 범위 | 마진 | 상태 |
|----------|--------|------|------|------|
| temperature | 480 | 450~500 | 60% | ✓ 정상 |
| pressure | 0.8 | 0.5~1.5 | 60% | ✓ 정상 |

### ✓ 결론
모든 조건이 공정 윈도우 내에 있습니다.
운영 가능합니다.
```

---

## 7. SPC 데이터 분석

### 예시 7-1: CD (Critical Dimension) SPC 분석

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

**예상 응답:**
```
## 📊 SPC 분석 (ISO 22514 기준)

### 통계

| 항목 | 값 |
|------|-----|
| 평균 | 45.44 |
| 표준편차 | 0.49 |
| 최소/최대 | 44.9 / 46.1 |
| 범위 | 1.2 |

### 공정능력지수

| 지수 | 값 |
|------|-----|
| Cp / Pp | 1.70 / 1.68 |
| Cpk / Ppk | 1.61 / 1.59 |

### ✓ 평가
- Cpk > 1.33 (양호)
- 공정이 목표에 가깝고 안정적
- 모든 데이터가 스펙 범위 내
```

---

## 8. 불량 위험도 예측 (FMEA)

### 예시 8-1: ETCH 공정 위험도 평가

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
    "window_params": "temperature:100:130,pressure:50:100",
    "current_params": "temperature:128,pressure:92",
    "severity_params": "temperature:8,pressure:5",
    "critical_params": "temperature"
  }
}
```

**예상 응답:**
```
## 🔍 FMEA 기반 불량 위험도 평가
- 적용 기준: AIAG & VDA FMEA (단순화)
- 중요 파라미터: temperature

### 종합 위험도
🟡 중위험 - 계획 조치
- 최대 RPN: 120

### 파라미터별 FMEA 테이블
| 파라미터 | 현재값 | 마진 | S | O | D | RPN | AP | O 근거 | 과거 상관 |
|----------|--------|------|---|---|---|-----|----|--------|-----------|
| temperature | 128 | 75% | 8 | 3 | 5 | 120 | M | 마진 여유 | N/A |
| pressure | 92 | 87% | 5 | 2 | 5 | 50 | L | 마진 여유 | N/A |
```

---

## 9. 트렌드 분석

### 예시 9-1: 시간대별 온도 변화 추세 분석

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

**예상 응답:**
```
## 📈 트렌드 분석

### 통계

| 항목 | 값 |
|------|-----|
| 추세 | 상승 (+0.43°C/h) |
| R² | 0.98 |
| Mann-Kendall | p-value 0.08 (약한 상승) |

### ⚠️ 경고
- 온도가 지속적으로 상승 중
- 현재 추세 유지 시 2시간 후 상한(125°C) 근접

### 📊 3시간 예측
| 시간 | 예측온도 |
|------|---------|
| 14:00 | 122.8°C |
| 15:00 | 123.3°C |
| 16:00 | 123.8°C |

### 🔧 권장사항
- PM 또는 냉각 시스템 점검 필요
- 1시간 내 조치 필요
```

---

## 10. 메트릭 분석

### 예시 10-1: 주간 KPI 목표 대비 성과 분석

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

**예상 응답:**
```
## 📊 KPI 목표 대비 분석 (2025년 1월 2주차)

### 성과 요약

| 지표 | 현재 | 목표 | 차이 | 달성도 |
|------|------|------|------|--------|
| yield | 97.8% | 98% | -0.2 | 99.8% |
| cpk | 1.28 | 1.33 | -0.05 | 96.2% |
| uptime | 89.5% | 90% | -0.5 | 99.4% |

### 📈 평가
- 수율: 거의 목표 달성 (마이너 미달)
- CPK: 허용 수준이지만 개선 필요
- 가동률: 거의 목표 달성

### 🔧 개선 권장
1. 불량 5개 더 감소 필요 → 수율 98% 달성
2. CPK 개선을 위한 공정 안정화
3. PM 효율 개선으로 가동률 향상
```

---

## 11. 교대 리포트 생성

### 예시 11-1: 일근 교대 인수인계 리포트

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

**예상 응답:**
```
## 📋 일근 교대 리포트 (2025-01-15)

### 생산 요약
- 투입: 200매
- 완료: 195매
- 목표: 200매
- 달성도: 97.5%
- 수율: 98.2%

### 장비 상태
| 장비 | 상태 | 이슈 |
|------|------|------|
| ETCH-01 | ✓ 정상 | - |
| ETCH-02 | ⚠️ 다운 | PM 중 |
| CVD-01 | ✓ 정상 | - |

### 품질
- 불량: 5개
- 주요: 파티클 3건, 스크래치 2건

### 주요 이벤트
- 14:00 PM 시작
- 16:00 온도 경고

### 미결 조치 (야근으로 인수)
1. ETCH-02 복구 확인
2. 온도 모니터링 계속
```

---

## 12. 장비 비교 분석

### 예시 12-1: CMP 장비 3대 성능 비교

**사용자:**
```
우리 CMP 장비 3대의 성능을 비교하고 싶어.

CMP-01: 수율 98.5%, CPK 1.45
CMP-02: 수율 97.2%, CPK 1.28
CMP-03: 수율 98.1%, CPK 1.38

가중치: 수율 40%, CPK 30%, 가동률 30%

벤치마크:
수율 98%, CPK 1.33, 가동률 90%

장비별 가동률:
CMP-01: 92%
CMP-02: 88%
CMP-03: 91%
```

**MCP 도구 호출:**
```json
{
  "name": "analyze_equipment_comparison",
  "arguments": {
    "equipment_list": "CMP-01,CMP-02,CMP-03",
    "metrics_data": "CMP-01:yield=98.5+cpk=1.45+uptime=92;CMP-02:yield=97.2+cpk=1.28+uptime=88;CMP-03:yield=98.1+cpk=1.38+uptime=91",
    "weights": "yield:0.4,cpk:0.3,uptime:0.3",
    "benchmark": "yield:98,cpk:1.33,uptime:90"
  }
}
```

**예상 응답:**
```
## 📊 장비 비교 분석

### 정규화 점수 (벤치마크 기준)

| 장비 | 수율 | CPK | 가동률 | 종합점수 |
|------|------|-----|--------|---------|
| CMP-01 | 100 | 109 | 102 | 104 |
| CMP-02 | 97 | 96 | 98 | 97 |
| CMP-03 | 100 | 104 | 101 | 102 |

### 순위
1️⃣ CMP-01: 104점 (최우수)
2️⃣ CMP-03: 102점 (양호)
3️⃣ CMP-02: 97점 (개선 필요)

### 권장사항
- CMP-02: 수율과 CPK 개선 필요
- CMP-01을 벤치마크로 CMP-02 개선안 도출
```

---

## 13. 레시피 최적화 방향

### 예시 13-1: CVD 레시피 최적화 방향 제시

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
- 박막 두께: 1000 nm (대략 5.3% 증가)
- 균일성: 95%
- 수율: 98%

온도가 가장 중요한 파라미터고,
제약은 온도 400~500°C, 압력 0.8~1.5 Torr야.
```

**MCP 도구 호출:**
```json
{
  "name": "optimize_recipe_direction",
  "arguments": {
    "current_recipe": {
      "temperature": 450,
      "pressure": 1.0,
      "time": 300
    },
    "current_performance": {
      "thickness": 950,
      "uniformity": 92,
      "yield": 97
    },
    "target_performance": {
      "thickness": 1000,
      "uniformity": 95,
      "yield": 98
    },
    "param_sensitivity": {
      "temperature": "HIGH",
      "pressure": "MEDIUM",
      "time": "MEDIUM"
    },
    "constraints": {
      "temperature": {"min": 400, "max": 500},
      "pressure": {"min": 0.8, "max": 1.5}
    }
  }
}
```

**예상 응답:**
```
## ⚙️ 레시피 최적화 방향

### 성과 갭 분석
- thickness: 목표 대비 +50nm (5.3% 증가 필요)
- uniformity: 목표 대비 +3% (개선 필요)
- yield: 목표 대비 +1% (소폭 개선)

### 조정 권장 파라미터
- temperature: 상향 (민감도 HIGH, 제약 400-500°C)
  → 현재 450°C에서 460~470°C로 상향 조정
- pressure: 상향 (민감도 MEDIUM, 제약 0.8-1.5 Torr)
  → 현재 1.0 Torr에서 1.1~1.2 Torr로 소폭 상향
- time: 상향 (민감도 MEDIUM)
  → 현재 300초에서 320초로 증가

### 🧪 추천 시험 계획
1. 온도 상향이 주요 목표 (박막 두께 증가)
2. 압력/시간 협업으로 균일성 개선
3. DOE 활용하여 상호작용 확인
```

---

## 14. 파라미터 변경 시뮬레이션

### 예시 14-1: ETCH 공정 시간 단축 시뮬레이션

**사용자:**
```
ETCH 시간을 300초에서 250초로 줄일 수 있을까?

현재 상태:
- 레시피: temperature 120, time 300, pressure 75
- 성과: etch_rate 50 nm/s, uniformity 91%, yield 97%
- 윈도우: temp 100-140, pressure 50-100

시간 단축 시 예상 영향:
- etch_rate는 시간의 0.8배 비율로 감소
- uniformity는 시간 단축 시 2% 악화
- 공정 윈도우는 유지되어야 함
```

**MCP 도구 호출:**
```json
{
  "name": "simulate_parameter_change",
  "arguments": {
    "current_state": {
      "recipe": {
        "temperature": 120,
        "time": 300,
        "pressure": 75
      },
      "performance": {
        "etch_rate": 50,
        "uniformity": 91,
        "yield": 97
      }
    },
    "proposed_changes": {
      "time": 250
    },
    "impact_rules": [
      {
        "if": {"parameter": "time", "change": -50},
        "impact": {"etch_rate": -10, "uniformity": -2}
      }
    ],
    "process_window": {
      "temperature": {"min": 100, "max": 140},
      "pressure": {"min": 50, "max": 100}
    }
  }
}
```

**예상 응답:**
```
## 🧪 파라미터 변경 시뮬레이션

### 레시피 변경 전/후
| 파라미터 | Before | After |
|----------|--------|-------|
| temperature | 120 | 120 |
| time | 300 | 250 |
| pressure | 75 | 75 |

### 예상 성과 변화
| 지표 | Before | After | 변화 |
|------|--------|-------|------|
| etch_rate | 50 | 40 | -20% |
| uniformity | 91 | 89 | -2% |
| yield | 97 | 97 | - |

### 리스크 평가
- 범위 초과 없음: ✓
- 에치율 20% 감소 → 수율 저하 위험
- 균일성 2% 악화 → 허용 범위 내

### ⚠️ 평가
시간 단축은 공정 윈도우 내이지만
성과 저하가 예상되므로 권장하지 않음.
```

---

## 15. 수율 영향도 계산 (DOE)

### 예시 15-1: 온도/압력 변경에 따른 수율 영향

**사용자:**
```
온도를 +5°C, 압력을 +3 mTorr 올릴 경우
수율이 어떻게 변할까?

현재 기준 수율: 97.5%

파라미터 변경:
1. 온도 +5°C (영향도: +0.8%)
2. 압력 +3 mTorr (영향도: +0.3%)

상호작용 효과:
- 온도×압력: -0.2% (음의 상호작용)

신뢰도: 95%
```

**MCP 도구 호출:**
```json
{
  "name": "calculate_yield_impact",
  "arguments": {
    "baseline_yield": 97.5,
    "parameter_changes": [
      {
        "parameter": "temperature",
        "change": 5,
        "main_effect": 0.8
      },
      {
        "parameter": "pressure",
        "change": 3,
        "main_effect": 0.3
      }
    ],
    "interaction_effects": [
      {
        "parameters": ["temperature", "pressure"],
        "effect": -0.2
      }
    ],
    "confidence_level": 0.95,
    "model_type": "linear_with_interaction"
  }
}
```

**예상 응답:**
```
## 📊 DOE 기반 수율 영향도 분석

### 주효과 (Main Effects)
| 파라미터 | 변경 | 영향도 | 누적 수율 |
|----------|------|--------|---------|
| 기준 | - | - | 97.5% |
| temperature +5°C | 기준 → +5 | +0.8% | 98.3% |
| pressure +3mTorr | 기준 → +3 | +0.3% | 98.6% |

### 상호작용 효과 (Interaction)
- temperature × pressure: -0.2% (양수 상호작용 감소)

### 최종 예측 수율
**98.7% (신뢰도 95%)**

### 📈 평가
- 전체적으로 긍정적 영향
- 주요 기여: 온도 상향 (+0.8%)
- 리스크: 상호작용으로 일부 상쇄

### 🔧 권장사항
변경 진행 권장 (예상 수율 98.7%)
단, 운영 후 실제 데이터로 검증 필요
```

---

## 전체 워크플로우 예시

### 시나리오: 파티클 불량 다발 → 해결까지

**1단계: 현상 파악**
```
사용자: "어제 CMP 공정에서 파티클 불량이 갑자기 5배 증가했어!"
→ analyze_defect 호출
```

**2단계: 이력 분석**
```
사용자: "이런 불량이 예전에도 있었나?"
→ get_defect_history 호출 (지난 3개월 데이터)
```

**3단계: 긴급 대응**
```
사용자: "지금 어떻게 해야 해?"
→ suggest_corrective_action 호출
```

**4단계: 원인 확인**
```
사용자: "공정 파라미터 변화가 있나?"
→ compare_to_baseline 호출
```

**5단계: 리스크 평가**
```
사용자: "지금 운영해도 되나?"
→ predict_defect_risk 호출
```

**6단계: 복구 검증**
```
사용자: "대응 후 SPC 데이터 분석 결과는?"
→ analyze_spc_data 호출
```

**7단계: 교대 인수**
```
사용자: "교대 리포트 생성해줘"
→ generate_shift_report 호출
```

---

## 활용 팁

1. **도구 조합**: 복합 분석이 필요하면 여러 도구를 순차적으로 호출
2. **CSV 형식**: 복잡한 데이터는 CSV 문자열로 전달
3. **예시 활용**: description의 예시를 참고하여 입력 형식 구성
4. **필수 필드**: required 필드는 반드시 입력
5. **선택 필드**: 선택 필드는 분석 깊이를 높이는 선택적 입력

---

**Last Updated**: 2025-01-15  
**MCP Version**: 2.0.0
