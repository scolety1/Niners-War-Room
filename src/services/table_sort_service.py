from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SortSpec:
    table_key: str
    label: str
    sort_columns: tuple[str, ...]
    directions: tuple[str, ...]
    meaning: str

    @property
    def caption(self) -> str:
        return f"Sorted by {self.label}. {self.meaning}"


def sort_caption(spec: SortSpec) -> str:
    return spec.caption
