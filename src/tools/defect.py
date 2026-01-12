from datetime import datetime, timedelta
from typing import Dict, List, Optional

from mcp.types import TextContent

from src.data.defect_db import DEFECT_DETAILS, DEFECT_HISTORY
from src.utils import formatter


ANALYZE_DEFECT_SCHEMA: Dict = {
    "type": "object",
    "properties": {
        "defect_code": {"type": "string", "description": "Defect code (e.g., PARTICLE)"},
        "process_step": {"type": "string", "description": "Process step name (e.g., Etch)"},
        "wafer_id": {"type": "string", "description": "Optional wafer ID", "nullable": True},
    },
    "required": ["defect_code", "process_step"],
}

GET_DEFECT_HISTORY_SCHEMA: Dict = {
    "type": "object",
    "properties": {
        "defect_type": {"type": "string", "description": "Defect type"},
        "date_range": {
            "type": "string",
            "enum": ["7d", "30d", "90d"],
            "description": "Optional lookback window",
        },
    },
    "required": ["defect_type"],
}

SUGGEST_CORRECTIVE_ACTION_SCHEMA: Dict = {
    "type": "object",
    "properties": {
        "defect_code": {"type": "string", "description": "Defect code (e.g., PARTICLE)"},
        "equipment_id": {"type": "string", "description": "Equipment ID (e.g., ETCH-01)"},
        "current_conditions": {"type": "object", "description": "Key/value map of current recipe inputs"},
    },
    "required": ["defect_code", "equipment_id", "current_conditions"],
}


def _error(message: str) -> TextContent:
    return TextContent(type="text/markdown", text=f"**Error**: {message}")


def _normalize(code: str) -> str:
    return code.strip().upper()


async def analyze_defect(defect_code: str, process_step: str, wafer_id: Optional[str] = None) -> TextContent:
    code = _normalize(defect_code)
    detail = DEFECT_DETAILS.get(code)
    if not detail:
        return _error(f"Unknown defect code '{defect_code}'. Known: {', '.join(DEFECT_DETAILS)}")

    impacts = detail["process_impacts"].get(process_step, [])
    impact_section = (
        formatter.bullet_list(impacts) if impacts else "해당 공정 단계에 대한 기록된 영향 정보가 없습니다."
    )
    wafer_note = f"\n- **Wafer**: {wafer_id}" if wafer_id else ""

    body = "\n".join(
        [
            f"### 불량 분석: {code}",
            formatter.key_values(
                {
                    "공정 단계": process_step,
                    "설명": detail["description"],
                }
            )
            + wafer_note,
            "\n**가능 원인**",
            formatter.bullet_list(detail["likely_causes"]),
            "\n**공정 영향**",
            impact_section,
            "\n**권장 조치**",
            formatter.bullet_list(detail["recommended_actions"]),
        ]
    )
    return TextContent(type="text/markdown", text=body)


async def get_defect_history(defect_type: str, date_range: Optional[str] = None) -> TextContent:
    code = _normalize(defect_type)
    if code not in DEFECT_DETAILS:
        return _error(f"Unknown defect type '{defect_type}'. Known: {', '.join(DEFECT_DETAILS)}")

    days_lookup = {"7d": 7, "30d": 30, "90d": 90}
    limit_days = days_lookup.get(date_range or "90d", 90)

    cutoff = datetime.utcnow() - timedelta(days=limit_days)

    filtered: List[Dict] = [
        row
        for row in DEFECT_HISTORY
        if row["defect_type"] == code
        and datetime.strptime(row["date"], "%Y-%m-%d") >= cutoff
    ]

    table_rows = [
        [row["date"], row["process_step"], row["equipment_id"], row["action"]] for row in filtered
    ]
    table_text = (
        formatter.markdown_table(["Date", "Step", "EQP", "Action"], table_rows)
        if table_rows
        else "선택한 기간에 해당 불량 이력이 없습니다."
    )

    body = "\n".join(
        [
            f"### 불량 이력: {code} (최근 {limit_days}일)",
            table_text,
        ]
    )
    return TextContent(type="text/markdown", text=body)


async def suggest_corrective_action(
    defect_code: str, equipment_id: str, current_conditions: Dict[str, str]
) -> TextContent:
    code = _normalize(defect_code)
    detail = DEFECT_DETAILS.get(code)
    if not detail:
        return _error(f"Unknown defect code '{defect_code}'. Known: {', '.join(DEFECT_DETAILS)}")

    condition_lines = [
        f"- **{k}**: {v}" for k, v in current_conditions.items()
    ] or ["- 현재 조건 입력 없음"]

    body = "\n".join(
        [
            f"### 시정 조치 제안: {code}",
            formatter.key_values({"장비": equipment_id, "설명": detail['description']}),
            "\n**현재 조건**",
            "\n".join(condition_lines),
            "\n**즉각 조치**",
            formatter.bullet_list(detail["recommended_actions"]),
            "\n**추가 확인 포인트**",
            formatter.bullet_list(
                [
                    "SPC 추세 확인 및 3σ 이탈 여부 체크",
                    "유사 배치의 이력과 레시피 변경 로그 비교",
                    "최근 PM/CM 이후 챔버 상태 확인",
                ]
            ),
        ]
    )
    return TextContent(type="text/markdown", text=body)


def register_defect_tools(registry: Dict[str, Dict]) -> None:
    registry["analyze_defect"] = {
        "description": "반도체 웨이퍼 불량 유형을 분석하고 원인을 추정합니다.",
        "schema": ANALYZE_DEFECT_SCHEMA,
        "handler": analyze_defect,
    }
    registry["get_defect_history"] = {
        "description": "특정 불량 유형의 과거 발생 이력과 해결 사례를 조회합니다.",
        "schema": GET_DEFECT_HISTORY_SCHEMA,
        "handler": get_defect_history,
    }
    registry["suggest_corrective_action"] = {
        "description": "현재 발생한 불량에 대해 권장 시정 조치를 제안합니다.",
        "schema": SUGGEST_CORRECTIVE_ACTION_SCHEMA,
        "handler": suggest_corrective_action,
    }

