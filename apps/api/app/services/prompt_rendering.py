import re
from typing import Any

_PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")


def render_prompt_template(
    *,
    template_text: str,
    input_text: str,
    expected_output: str | None,
    metadata_json: dict[str, Any] | None,
    input_variables: list[str] | None,
) -> str:
    context: dict[str, Any] = {
        "input": input_text,
        "expected_output": expected_output or "",
        **(metadata_json or {}),
    }

    required_vars = set(input_variables or [])
    if not required_vars:
        required_vars = set(_PLACEHOLDER_PATTERN.findall(template_text))

    missing = sorted(var for var in required_vars if var not in context)
    if missing:
        raise ValueError(f"Missing prompt variables: {', '.join(missing)}")

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in context:
            raise ValueError(f"Missing prompt variable: {key}")
        value = context[key]
        return "" if value is None else str(value)

    return _PLACEHOLDER_PATTERN.sub(replace, template_text)