# SemiProcess MCP Server

반도체 공정 분석용 MCP(Model Context Protocol) 서버입니다. **모든 분석은 사용자가 제공한 기준/레시피/조건/이력 데이터를 기반**으로 수행하며, 어떤 공정·기업에도 적용 가능한 범용 분석 도구 15개를 제공합니다. 모든 응답 상단에 면책 문구가 포함되고 Markdown 형식으로 반환됩니다.

## 요구사항
- MCP 사양 버전: 2026-01-14 이상
- Streamable HTTP (SSE) 지원
- Stateless FastAPI 서버
- Python 3.11+, FastAPI, `mcp` 라이브러리
- 공개 URL 배포 가능

## 설치
```bash
pip install -r requirements.txt
```

## 실행
```bash
export PORT=8000  # 필요 시 변경
uvicorn src.server:app --host 0.0.0.0 --port ${PORT}
```

## 엔드포인트
- `GET /health` : 상태 확인
- `GET|POST /mcp` : MCP 엔드포인트 (SSE 포함)
- `GET /` : 서비스 메타 정보

## 제공 Tool 목록 (15개, 모두 사용자 입력 기반)
불량 관리  
1. `analyze_defect(defect_code, defect_description, process_step, ...)`  
2. `get_defect_history(defect_records, analysis_type?)`  
3. `suggest_corrective_action(problem_description, affected_equipment, severity, current_status, ...)`

레시피 관리  
4. `compare_to_baseline(baseline_recipe, current_recipe, recipe_name?)`  
5. `compare_two_recipes(recipe_a, recipe_b, recipe_a_name?, recipe_b_name?, tolerance?)`  
6. `validate_process_window(process_window, test_conditions, critical_params?)`

메트릭 / SPC  
7. `analyze_metrics(metrics_data, targets, period?, equipment_id?)`  
8. `analyze_spc_data(data_points, spec_limits, control_limits?, parameter_name?, equipment_id?)`

예측 / 분석  
9. `predict_defect_risk(process_window, current_conditions, critical_params?, historical_defect_correlation?)`  
10. `optimize_recipe_direction(current_recipe, current_performance, target_performance, ...)`  
11. `simulate_parameter_change(current_state, proposed_changes, impact_rules, process_window?)`  
12. `calculate_yield_impact(baseline_yield, parameter_changes, interaction_effects?)`

비교 / 리포트  
13. `analyze_equipment_comparison(equipment_data, weights?, benchmark?)`  
14. `generate_shift_report(production_summary, equipment_status, quality_summary, ...)`  
15. `analyze_trend(time_series_data, parameter_name, spec_limits?, analysis_options?)`

모든 Tool의 `content`는 `text/markdown`으로 반환합니다. 각 Tool 입력은 JSON Schema로 정의되어 있습니다.

## 퀵 테스트 (PowerShell 예시)
- Tool 목록 및 개수 확인(15개):
```powershell
$body = '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
Invoke-RestMethod -Uri "https://semiprocess-mcp.vercel.app/mcp" -Method POST -Body $body -ContentType "application/json"
```
- 공정 윈도우 검증 예시:
```powershell
$body = @'
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "validate_process_window",
    "arguments": {
      "process_window": {
        "temperature": {"min": 55, "max": 65},
        "pressure": {"min": 25, "max": 35}
      },
      "test_conditions": {
        "temperature": 63,
        "pressure": 28
      }
    }
  }
}
'@
Invoke-RestMethod -Uri "https://semiprocess-mcp.vercel.app/mcp" -Method POST -Body $body -ContentType "application/json"
```

## 대화 예시 (요청/응답 흐름)
- 불량 분석
  - 요청: `analyze_defect` + `{"defect_code":"PARTICLE","defect_description":"웨이퍼 중앙 파티클","process_step":"ETCH"}`
  - 응답: 면책 문구 + 원인/점검/체크리스트 Markdown
- 레시피 기준 비교
  - 요청: `compare_to_baseline` + `baseline_recipe`/`current_recipe` JSON
  - 응답: 기준/현재/편차/이탈 항목 테이블
- 공정 윈도우 검증
  - 요청: `validate_process_window` + `process_window`/`test_conditions`
  - 응답: 파라미터별 PASS/FAIL과 위험 파라미터 목록
- SPC 분석
  - 요청: `analyze_spc_data` + `data_points`, `spec_limits`
  - 응답: 평균, σ, Cp/Cpk, UCL/LCL, 관리 상태 요약
- 교대 리포트
  - 요청: `generate_shift_report` + 생산/장비/품질/이벤트 데이터
  - 응답: 교대 리포트 Markdown (생산 요약, 장비 상태, 품질 이슈, 이벤트, 미결)

## Tool별 상세 대화 예시
- analyze_defect  
  - 요청: `{"defect_code":"SCRATCH","defect_description":"웨이퍼 가장자리 스크래치","process_step":"CMP","known_causes":["패드 마모"],"recent_changes":["슬러리 Lot 교체"]}`  
  - 응답: 원인 매트릭스(사용자+일반 점검), 최근 변경, 체크리스트
- get_defect_history  
  - 요청: `{"defect_records":[{"date":"2025-01-10","defect_type":"SCRATCH","equipment_id":"CMP-01","wafer_count":3,"action_taken":"패드 교체","result":"해결"}]}`  
  - 응답: 이력 테이블, 패턴 요약, 개선 권장
- suggest_corrective_action  
  - 요청: `{"problem_description":"압력 불안정","affected_equipment":"ETCH-01","severity":"major","current_status":"알람 반복"}`  
  - 응답: 즉시 조치(우선순위), 단계별 가이드, 자원/에스컬레이션
- compare_to_baseline  
  - 요청: `{"baseline_recipe":{"temp":{"value":60,"min":55,"max":65}},"current_recipe":{"temp":67},"recipe_name":"Oxide Etch"}`  
  - 응답: 기준/현재/편차/이탈 테이블, 조정 권장
- compare_two_recipes  
  - 요청: `{"recipe_a":{"pressure":30},"recipe_b":{"pressure":33},"tolerance":{"pressure":5}}`  
  - 응답: 파라미터별 비교, 허용 초과 여부
- validate_process_window  
  - 요청: `{"process_window":{"temp":{"min":55,"max":65}},"test_conditions":{"temp":52},"critical_params":["temp"]}`  
  - 응답: PASS/FAIL 표, 위험 파라미터 경고
- analyze_metrics  
  - 요청: `{"metrics_data":{"yield":98.1,"cpk":1.4},"targets":{"yield":98,"cpk":1.33},"period":"8h"}`  
  - 응답: KPI 달성 여부, 미달 항목 요약
- analyze_spc_data  
  - 요청: `{"data_points":[45,46,47,44,45,46,47,48,44,45],"spec_limits":{"usl":50,"lsl":40,"target":45}}`  
  - 응답: 평균/σ/Cp/Cpk, UCL/LCL, 이탈/트렌드 여부
- predict_defect_risk  
  - 요청: `{"process_window":{"temp":{"min":55,"max":65}},"current_conditions":{"temp":64},"critical_params":["temp"]}`  
  - 응답: 위험도 점수, 파라미터별 위험 요약, 예방 조치
- optimize_recipe_direction  
  - 요청: `{"current_recipe":{"pressure":30},"current_performance":{"yield":97},"target_performance":{"yield":99},"param_sensitivity":{"pressure":"HIGH"}}`  
  - 응답: 성과 갭, 조정 권장 파라미터와 방향
- simulate_parameter_change  
  - 요청: `{"current_state":{"recipe":{"temp":60},"performance":{"yield":98}},"proposed_changes":{"temp":62},"impact_rules":[{"impact":{"yield":-0.2}}]}`  
  - 응답: Before/After, 예상 성과 변화, 범위 이탈 경고
- calculate_yield_impact  
  - 요청: `{"baseline_yield":98,"parameter_changes":[{"param":"temp","from":60,"to":62,"yield_sensitivity":0.5}]}`  
  - 응답: 파라미터별 영향, 총 예상 수율 변화
- analyze_equipment_comparison  
  - 요청: `{"equipment_data":[{"equipment_id":"EQ1","metrics":{"yield":98,"cpk":1.4}},{"equipment_id":"EQ2","metrics":{"yield":97,"cpk":1.2}}],"weights":{"yield":0.5,"cpk":0.5}}`  
  - 응답: 장비별 점수/랭킹, 개선 우선순위
- generate_shift_report  
  - 요청: `{"production_summary":{"wafer_in":200,"wafer_out":195,"yield":98},"equipment_status":[{"equipment_id":"ETCH-01","status":"running"}],"quality_summary":{"defect_count":3},"key_events":[{"time":"01:00","event":"레시피 변경","action":"검증","status":"진행"}]}`  
  - 응답: 생산/장비/품질/이벤트/미결을 포함한 교대 리포트
- analyze_trend  
  - 요청: `{"time_series_data":[{"timestamp":"2025-01-10 10:00","value":45},{"timestamp":"2025-01-10 11:00","value":46}],"parameter_name":"thickness","spec_limits":{"usl":50,"lsl":40}}`  
  - 응답: 평균/추세/시프트 여부, 이상점/예측 요약

## Docker 빌드/실행
```bash
docker build -t semiprocess-mcp .
docker run -p 8000:8000 -e PORT=8000 semiprocess-mcp
```

## Vercel 배포
1. `vercel.json` 및 `api/index.py`가 포함되어 있습니다.
2. Vercel 프로젝트에서 Python Runtime(3.11) 사용.
3. 환경 변수 필요 시 Vercel Dashboard에 등록.
4. 배포 후 엔드포인트:
   - `GET /health`
   - `GET|POST /mcp`

## 로깅
- 기본 INFO 레벨, 포맷: `%(asctime)s %(levelname)s %(name)s - %(message)s`
- 예외 발생 시 스택 트레이스가 로그에 남습니다.
