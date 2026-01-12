# SemiProcess MCP Server

반도체 공정 관리용 MCP(Model Context Protocol) 서버입니다. 불량 해결, 공정조건 표준화, 공정 모니터링 관련 8개 MCP Tool을 제공합니다.

## 요구사항
- MCP 사양 버전: 2025-03-26 이상
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

## 제공 Tool 목록
불량 해결
1. `analyze_defect(defect_code, process_step, wafer_id?)`
2. `get_defect_history(defect_type, date_range?)`
3. `suggest_corrective_action(defect_code, equipment_id, current_conditions)`

공정조건 표준화
4. `get_standard_recipe(process_type, layer)`
5. `compare_recipe(process_type, current_recipe{layer, ...}, equipment_id)`
6. `validate_process_window(process_type, parameters{layer, ...})`

데이터 모니터링
7. `get_process_metrics(equipment_id?, process_type?, time_range)`
8. `check_spc_status(parameter_name, equipment_id, chart_type)`

모든 Tool의 `content`는 `text/markdown`(`TextContent`)으로 반환합니다. 각 Tool 입력은 JSON Schema로 정의되어 있으며 MCP Inspector에서 자동 인식됩니다.

## Mock 데이터
- 불량 코드: PARTICLE, SCRATCH, PATTERN_DEFECT, CD_VARIATION, OVERLAY_ERROR
- 공정: Etch, CVD, PVD, Lithography, CMP, Ion Implant
- 장비: ETCH-01, CVD-02, LITHO-03 등
- 파라미터: 온도(°C), 압력(mTorr), RF Power(W), Gas Flow(sccm) 등

## MCP Inspector 테스트
1. 서버 실행 후 MCP Inspector를 열고 HTTP Transport를 선택합니다.
2. URL에 `http://<host>:<port>/mcp` 입력 후 연결합니다.
3. Tool 목록이 표시되며, 입력 스키마에 따라 호출할 수 있습니다.

## Docker 빌드/실행
```bash
docker build -t semiprocess-mcp .
docker run -p 8000:8000 -e PORT=8000 semiprocess-mcp
```

## 로깅
- 기본 INFO 레벨, 포맷: `%(asctime)s %(levelname)s %(name)s - %(message)s`
- 예외 발생 시 스택 트레이스가 로그에 남습니다.
