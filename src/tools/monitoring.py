from typing import Dict, List, Optional

from mcp.types import TextContent

from src.data.metrics_db import REALTIME_METRICS, SPC_FLAGS
from src.utils import formatter


GET_PROCESS_METRICS_SCHEMA: Dict = {
    "type": "object",
    "properties": {
        "equipment_id": {"type": "string", "description": "Optional equipment ID"},
        "process_type": {"type": "string", "description": "Optional process type"},
        "time_range": {
            "type": "string",
            "enum": ["1h", "8h", "24h"],
            "description": "Time window (informational)",
        },
    },
}

CHECK_SPC_STATUS_SCHEMA: Dict = {
    "type": "object",
    "properties": {
        "parameter_name": {"type": "string", "description": "Parameter name"},
        "equipment_id": {"type": "string", "description": "Equipment ID"},
        "chart_type": {
            "type": "string",
            "enum": ["xbar", "range", "sigma"],
            "description": "SPC chart type",
        },
    },
    "required": ["parameter_name", "equipment_id", "chart_type"],
}


def _error(message: str) -> TextContent:
    return TextContent(type="text/markdown", text=f"**Error**: {message}")


async def get_process_metrics(
    equipment_id: Optional[str] = None, process_type: Optional[str] = None, time_range: str = "8h"
) -> TextContent:
    rows: List[Dict] = REALTIME_METRICS
    if equipment_id:
        rows = [r for r in rows if r["equipment_id"].lower() == equipment_id.lower()]
    if process_type:
        rows = [r for r in rows if r["process_type"].lower() == process_type.lower()]

    if not rows:
        return _error("조건에 맞는 메트릭 데이터가 없습니다.")

    table_rows = [
        [
            r["equipment_id"],
            r["process_type"],
            f"{r['cpk']:.2f}",
            f"{r['yield_pct']:.1f}%",
            f"{r['uptime_pct']:.1f}%",
            r["last_maintenance"],
        ]
        for r in rows
    ]

    body = "\n".join(
        [
            f"### 실시간 메트릭 (최근 {time_range})",
            formatter.markdown_table(
                ["EQP", "Process", "Cpk", "Yield", "Uptime", "Last Maint"], table_rows
            ),
            "\n- Cpk < 1.33 또는 Yield < 95%는 조사 대상입니다.",
        ]
    )
    return TextContent(type="text/markdown", text=body)


async def check_spc_status(parameter_name: str, equipment_id: str, chart_type: str) -> TextContent:
    matched = [
        r
        for r in SPC_FLAGS
        if r["parameter"].lower() == parameter_name.lower()
        and r["equipment_id"].lower() == equipment_id.lower()
        and r["chart_type"].lower() == chart_type.lower()
    ]
    if not matched:
        return _error("SPC 데이터가 없습니다. 파라미터/장비/차트를 확인하세요.")

    rows = [(m["parameter"], m["equipment_id"], m["chart_type"], m["status"], m["notes"]) for m in matched]
    status_table = formatter.markdown_table(
        ["Parameter", "EQP", "Chart", "Status", "Notes"],
        rows,
    )
    guidance = formatter.bullet_list(
        [
            "상태가 out_of_control이면 즉시 공정 정지 후 원인 분석을 수행합니다.",
            "warning 상태는 추세 확인 및 레시피/장비 점검을 권장합니다.",
            "in_control 상태라도 장기 트렌드(8h/24h)를 주기적으로 확인하세요.",
        ]
    )
    body = "\n".join(
        [
            "### SPC 상태 리포트",
            status_table,
            "\n**조치 가이드**",
            guidance,
        ]
    )
    return TextContent(type="text/markdown", text=body)


def register_monitoring_tools(registry: Dict[str, Dict]) -> None:
    registry["get_process_metrics"] = {
        "description": "특정 장비/공정의 주요 메트릭을 조회합니다.",
        "schema": GET_PROCESS_METRICS_SCHEMA,
        "handler": get_process_metrics,
    }
    registry["check_spc_status"] = {
        "description": "SPC 차트 상태를 확인합니다.",
        "schema": CHECK_SPC_STATUS_SCHEMA,
        "handler": check_spc_status,
    }
