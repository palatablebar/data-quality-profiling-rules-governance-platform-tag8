"""Character-class pattern inference for text columns.

数字 -> \\d, 字母 -> [A-Za-z], 日期形态 -> \\d{4}-\\d{2}-\\d{2}; runs are collapsed
into `{n}` quantifiers. The two most frequent patterns and their hit rates are
returned, so the profile page can show e.g. ``\\d{18}`` 命中 99.4%.
"""
import re
from collections import Counter

SAMPLE_SIZE = 500

DATE_PATTERN = re.compile(r"^\d{4}[-/]\d{2}[-/]\d{2}$")


def _class_of(char: str) -> str:
    if char.isdigit():
        return "digit"
    if ("a" <= char <= "z") or ("A" <= char <= "Z"):
        return "alpha"
    if char.isspace():
        return "space"
    if "\u4e00" <= char <= "\u9fff":
        return "cjk"
    return "other"


TOKEN = {
    "digit": r"\d",
    "alpha": "[A-Za-z]",
    "space": r"\s",
    "cjk": ".",
}


def value_pattern(value: str) -> str:
    if DATE_PATTERN.match(value):
        return r"\d{4}-\d{2}-\d{2}"
    tokens: list[list] = []
    for char in value:
        cls = _class_of(char)
        token = TOKEN.get(cls) or re.escape(char)
        if tokens and tokens[-1][0] == token:
            tokens[-1][1] += 1
        else:
            tokens.append([token, 1])
    parts = []
    for token, count in tokens:
        parts.append(token if count == 1 else f"{token}{{{count}}}")
    rendered = "".join(parts)
    return rendered[:120] + ("..." if len(rendered) > 120 else "")


def pattern_summary(values) -> str | None:
    sample = [str(v) for v in values if str(v) != ""][:SAMPLE_SIZE]
    if not sample:
        return None
    counter = Counter(value_pattern(value) for value in sample)
    total = len(sample)
    ranked = counter.most_common(2)
    parts = []
    for pattern, count in ranked:
        rate = round(count / total, 3)
        if rate < 0.01:
            continue
        parts.append(f"{pattern} · 命中 {rate * 100:.1f}%")
    return "；".join(parts) if parts else "unknown"


def primary_pattern(values, min_rate: float = 0.5) -> str | None:
    sample = [str(v) for v in values if str(v) != ""][:SAMPLE_SIZE]
    if not sample:
        return None
    counter = Counter(value_pattern(value) for value in sample)
    pattern, count = counter.most_common(1)[0]
    if count / len(sample) < min_rate:
        return None
    if pattern.endswith("..."):
        return None
    return pattern
