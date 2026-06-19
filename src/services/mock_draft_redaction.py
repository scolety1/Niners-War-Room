from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RedactedInputSummary:
    role: str
    display_path: str
    headers: tuple[str, ...]
    row_count: int
    rows: tuple[Mapping[str, object], ...]
    real_mode_redacted: bool
    no_files_written: bool = True


def summarize_input_reference(
    *,
    role: str,
    path: str | Path,
    headers: Sequence[str],
    row_count: int,
    mode: str,
    sample_rows: Sequence[Mapping[str, object]] = (),
) -> RedactedInputSummary:
    real_mode = mode == "real"
    return RedactedInputSummary(
        role=role,
        display_path=Path(path).name if real_mode else str(path),
        headers=tuple(headers),
        row_count=row_count,
        rows=() if real_mode else tuple(sample_rows),
        real_mode_redacted=real_mode,
    )
