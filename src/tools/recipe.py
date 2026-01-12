import re
from typing import Dict, Iterable, Optional, Tuple

from mcp.types import TextContent

from src.data.recipe_db import PROCESS_WINDOWS, STANDARD_RECIPES
from src.utils import formatter


GET_STANDARD_RECIPE_SCHEMA: Dict = {
    "type": "object",
    "properties": {
        "process_type": {
            "type": "string",
            "enum": ["etch", "deposition", "lithography", "implant", "cmp"],
        },
        "layer": {"type": "string", "description": "Layer or module name (e.g., poly_si)"},
    },
    "required": ["process_type", "layer"],
}

COMPARE_RECIPE_SCHEMA: Dict = {
    "type": "object",
    "properties": {
        "process_type": {"type": "string", "description": "Process type (e.g., etch)"},
        "current_recipe": {"type": "object", "description": "Current recipe map; include 'layer' key"},
        "equipment_id": {"type": "string", "description": "Equipment ID"},
    },
    "required": ["process_type", "current_recipe", "equipment_id"],
}

VALIDATE_PROCESS_WINDOW_SCHEMA: Dict = {
    "type": "object",
    "properties": {
        "process_type": {"type": "string", "description": "Process type (e.g., etch, lithography)"},
        "parameters": {
            "type": "object",
            "description": "Parameter map to validate; include 'layer'",
        },
    },
    "required": ["process_type", "parameters"],
}


def _error(message: str) -> TextContent:
    return TextContent(type="text/markdown", text=f"**Error**: {message}")


def _normalize(value: str) -> str:
    return value.strip().lower()


def _parse_number(value) -> Optional[float]:
    match = re.search(r"[-+]?\d*\.?\d+", str(value))
    return float(match.group()) if match else None


async def get_standard_recipe(process_type: str, layer: str) -> TextContent:
    pt = _normalize(process_type)
    recipes = STANDARD_RECIPES.get(pt, {})
    recipe = recipes.get(layer)
    if not recipe:
        known = ", ".join(recipes) if recipes else "없음"
        return _error(f"표준 레시피를 찾을 수 없습니다. layer 후보: {known}")

    table_rows = [[k, v] for k, v in recipe.items()]
    body = "\n".join(
        [
            f"### 표준 레시피: {pt} / {layer}",
            formatter.markdown_table(["Parameter", "Target"], table_rows),
        ]
    )
    return TextContent(type="text/markdown", text=body)


def _compare_rows(std: Dict[str, str], cur: Dict[str, str]) -> Iterable[Tuple[str, str, str, str]]:
    keys = sorted(set(std.keys()) | set(cur.keys()))
    for key in keys:
        std_val = std.get(key, "-")
        cur_val = cur.get(key, "-")
        note = "OK" if std_val == cur_val else "검토 필요"
        yield (key, std_val, cur_val, note)


async def compare_recipe(process_type: str, current_recipe: Dict[str, str], equipment_id: str) -> TextContent:
    pt = _normalize(process_type)
    layer = current_recipe.get("layer")
    if not layer:
        return _error("current_recipe에 'layer' 키를 포함해 주세요.")

    std = STANDARD_RECIPES.get(pt, {}).get(layer)
    if not std:
        return _error(f"표준 레시피 없음: {pt}/{layer}")

    rows = _compare_rows(std, current_recipe)
    body = "\n".join(
        [
            f"### 레시피 비교: {pt} / {layer} (장비 {equipment_id})",
            formatter.markdown_table(["Parameter", "Standard", "Current", "Note"], rows),
            "\n**하이라이트**",
            "- Note가 '검토 필요'인 항목은 허용 범위 확인 및 설정 보정이 필요합니다.",
        ]
    )
    return TextContent(type="text/markdown", text=body)


async def validate_process_window(process_type: str, parameters: Dict[str, str]) -> TextContent:
    pt = _normalize(process_type)
    layer = parameters.get("layer")
    if not layer:
        return _error("parameters에 'layer' 키를 포함해 주세요.")

    windows = PROCESS_WINDOWS.get(pt, {}).get(layer)
    if not windows:
        return _error(f"유효성 확인 가능한 윈도우가 없습니다: {pt}/{layer}")

    results = []
    for name, (low, high, unit) in windows.items():
        raw_value = parameters.get(name)
        parsed = _parse_number(raw_value)
        if parsed is None:
            status = "N/A"
            note = "값 해석 불가"
        elif parsed < low:
            status = "Fail"
            note = f"Low ({parsed} {unit}, min {low})"
        elif parsed > high:
            status = "Fail"
            note = f"High ({parsed} {unit}, max {high})"
        else:
            status = "Pass"
            margin_low = parsed - low
            margin_high = high - parsed
            note = f"Margin +{margin_high:.2f}/{margin_low:.2f} {unit}"
        results.append((name, raw_value or "-", f"{low}-{high} {unit}", status, note))

    body = "\n".join(
        [
            f"### 공정 윈도우 검증: {pt} / {layer}",
            formatter.markdown_table(["Parameter", "Input", "Window", "Result", "Note"], results),
        ]
    )
    return TextContent(type="text/markdown", text=body)


def register_recipe_tools(registry: Dict[str, Dict]) -> None:
    registry["get_standard_recipe"] = {
        "description": "특정 공정 단계의 표준 레시피를 조회합니다.",
        "schema": GET_STANDARD_RECIPE_SCHEMA,
        "handler": get_standard_recipe,
    }
    registry["compare_recipe"] = {
        "description": "현재 레시피와 표준 레시피를 비교합니다.",
        "schema": COMPARE_RECIPE_SCHEMA,
        "handler": compare_recipe,
    }
    registry["validate_process_window"] = {
        "description": "입력된 공정 조건이 윈도우 내에 있는지 검증합니다.",
        "schema": VALIDATE_PROCESS_WINDOW_SCHEMA,
        "handler": validate_process_window,
    }

