from datetime import datetime, timedelta
from typing import Dict, List


def _ts(minutes_ago: int) -> str:
    return (datetime.utcnow() - timedelta(minutes=minutes_ago)).strftime("%Y-%m-%d %H:%M")


REALTIME_METRICS: List[Dict] = [
    {
        "equipment_id": "ETCH-01",
        "process_type": "etch",
        "cpk": 1.85,
        "yield_pct": 98.4,
        "uptime_pct": 92.1,
        "last_maintenance": _ts(720),
    },
    {
        "equipment_id": "CVD-02",
        "process_type": "deposition",
        "cpk": 1.62,
        "yield_pct": 97.3,
        "uptime_pct": 95.5,
        "last_maintenance": _ts(1440),
    },
    {
        "equipment_id": "LITHO-03",
        "process_type": "lithography",
        "cpk": 1.72,
        "yield_pct": 99.1,
        "uptime_pct": 90.4,
        "last_maintenance": _ts(360),
    },
]


SPC_FLAGS: List[Dict] = [
    {
        "parameter": "CD@Center",
        "equipment_id": "LITHO-03",
        "chart_type": "xbar",
        "status": "in_control",
        "notes": "All points within 1.2σ; no runs detected",
    },
    {
        "parameter": "Overlay X",
        "equipment_id": "LITHO-03",
        "chart_type": "sigma",
        "status": "warning",
        "notes": "2 of last 3 points exceeded 2σ; monitor closely",
    },
    {
        "parameter": "Removal Rate",
        "equipment_id": "CMP-01",
        "chart_type": "range",
        "status": "out_of_control",
        "notes": "One point beyond UCL; investigate slurry flow",
    },
]

