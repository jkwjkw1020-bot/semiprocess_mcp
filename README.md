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
