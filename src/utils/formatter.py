from typing import Dict, Iterable, Sequence


def markdown_table(headers: Sequence[str], rows: Iterable[Sequence[str]]) -> str:
    """Return a markdown table string."""
    header_line = " | ".join(headers)
    separator = " | ".join(["---"] * len(headers))
    body_lines = [" | ".join(str(cell) for cell in row) for row in rows]
    return "\n".join([header_line, separator, *body_lines])


def bullet_list(items: Iterable[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def key_values(pairs: Dict[str, str]) -> str:
    return "\n".join(f"- **{key}**: {value}" for key, value in pairs.items())
