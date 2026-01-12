from datetime import datetime, timedelta
from typing import Dict, List

DEFECT_DETAILS: Dict[str, Dict] = {
    "PARTICLE": {
        "description": "Particles causing shorts/opens",
        "likely_causes": [
            "Chamber wall flaking after long PM interval",
            "Worn ESC O-ring leading to backside leakage",
            "Wet clean carry-over or poor DI purge",
        ],
        "process_impacts": {
            "Etch": ["Micro-masking causing incomplete etch", "Random shorts"],
            "CVD": ["Voids or seams due to nucleation on particles"],
            "Lithography": ["Resist bridging, pattern collapse"],
        },
        "recommended_actions": [
            "Run chamber clean recipe and verify seasoning wafers",
            "Inspect and replace shields, focus rings, O-rings",
            "Tighten pre-clean and FOUP purge; increase post-CMP megasonic",
        ],
    },
    "SCRATCH": {
        "description": "Mechanical damage on wafer surface",
        "likely_causes": [
            "Robot end-effector misalignment",
            "Carrier/FOUP particle buildup",
            "Improper brush pressure in post-CMP clean",
        ],
        "process_impacts": {
            "CMP": ["Copper dishing, oxide erosion"],
            "Lithography": ["Focus error due to topography"],
        },
        "recommended_actions": [
            "Recalibrate robot path and check edge-grip pads",
            "Clean/replace carriers; inspect loadport rollers",
            "Lower brush pressure; verify DI flow and spin-dry speed",
        ],
    },
    "PATTERN_DEFECT": {
        "description": "Pattern fidelity loss or bridging",
        "likely_causes": [
            "Resist footing from low post-exposure bake",
            "Dose drift in scanner",
            "Reticle contamination or pellicle damage",
        ],
        "process_impacts": {
            "Lithography": ["CD non-uniformity", "Bridges in dense areas"],
            "Etch": ["Micro-trenching from resist footing"],
        },
        "recommended_actions": [
            "Re-center dose/focus, run focus-exposure matrix",
            "Clean reticle and inspect pellicle for haze",
            "Tighten PEB temperature control and bake time",
        ],
    },
    "CD_VARIATION": {
        "description": "Critical dimension variation across wafer/lot",
        "likely_causes": [
            "RF power drift or matching network instability",
            "Gas MFC offset causing skew",
            "Lens heating or stage leveling drift",
        ],
        "process_impacts": {
            "Etch": ["CD shrink at edge", "Sidewall angle variation"],
            "Lithography": ["Across-wafer CD swing"],
        },
        "recommended_actions": [
            "Re-tune RF matching; verify auto-match recipes",
            "Re-zero MFCs and verify calibration logs",
            "Run leveling calibration and dose mapper",
        ],
    },
    "OVERLAY_ERROR": {
        "description": "Layer-to-layer misalignment",
        "likely_causes": [
            "Stage thermal drift",
            "Chuck vacuum instability",
            "Incorrect W2W alignment model",
        ],
        "process_impacts": {
            "Lithography": ["Overlay shift > spec", "Field rotation"],
        },
        "recommended_actions": [
            "Stabilize stage temp; extend soak time",
            "Check chuck vacuum map and backside helium leak",
            "Rebuild alignment model with fresh targets",
        ],
    },
}


def _days_ago(days: int) -> str:
    return (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")


DEFECT_HISTORY: List[Dict] = [
    {
        "defect_type": "PARTICLE",
        "date": _days_ago(3),
        "process_step": "Etch",
        "equipment_id": "ETCH-01",
        "action": "Chamber clean + shield swap; particle adders reduced 80%",
    },
    {
        "defect_type": "SCRATCH",
        "date": _days_ago(10),
        "process_step": "CMP",
        "equipment_id": "CMP-01",
        "action": "Robot recalibration; replaced worn end-effector pads",
    },
    {
        "defect_type": "CD_VARIATION",
        "date": _days_ago(15),
        "process_step": "Lithography",
        "equipment_id": "LITHO-03",
        "action": "Dose mapper re-center; lens heating compensator enabled",
    },
    {
        "defect_type": "PATTERN_DEFECT",
        "date": _days_ago(20),
        "process_step": "Lithography",
        "equipment_id": "LITHO-02",
        "action": "Reticle clean; PEB temp PID re-tuned",
    },
    {
        "defect_type": "OVERLAY_ERROR",
        "date": _days_ago(25),
        "process_step": "Lithography",
        "equipment_id": "LITHO-03",
        "action": "Rebuilt W2W alignment model; chuck vacuum leak fixed",
    },
]

