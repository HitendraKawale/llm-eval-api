import re

_WHITESPACE_RE_ = re.compile(r"\s+")


def normalize_text(value: str) -> str:
    value = value.strip().lower()
    value = _WHITESPACE_RE_.sub(" ", value)
    return value


def exact_match_score(
    expected: str | None, actual: str | None
) -> tuple[float | None, bool | None, str | None]:
    if expected is None:
        return None, None, None

    normalize_expected = normalize_text(expected)
    normalize_actual = normalize_text(actual or "")

    passed = normalize_expected == normalize_actual
    score = 1.0 if passed else 0.0

    return score, passed, "exact_match_normalized"
