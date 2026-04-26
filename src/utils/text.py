from __future__ import annotations


def merge_name(value: str) -> str:
    return " ".join(value.lower().replace("'", "").split())
