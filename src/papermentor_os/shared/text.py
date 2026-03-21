from __future__ import annotations

import re
from collections.abc import Iterable


TOKEN_PATTERN = re.compile(r"[\u4e00-\u9fff]{2,}|[A-Za-z]{3,}")


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_keywords(text: str) -> set[str]:
    normalized = normalize_whitespace(text).lower()
    return {token for token in TOKEN_PATTERN.findall(normalized)}


def keyword_overlap(left: str, right: str) -> float:
    left_keywords = extract_keywords(left)
    right_keywords = extract_keywords(right)
    if not left_keywords or not right_keywords:
        return 0.0
    overlap = left_keywords & right_keywords
    return len(overlap) / min(len(left_keywords), len(right_keywords))


def first_non_empty(items: Iterable[str]) -> str | None:
    for item in items:
        normalized = normalize_whitespace(item)
        if normalized:
            return normalized
    return None

