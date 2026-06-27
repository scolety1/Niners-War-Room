from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
STATUS_MATRIX_PATH = (
    REPO_ROOT / "docs" / "hq" / "future_tools" / "future_tools_status_matrix_20260626.csv"
)

ALLOWED_DECISIONS = {
    "SAFE_NOW_DISPLAY_ONLY",
    "SAFE_NOW_FRAMEWORK_ONLY",
    "BLOCKED_NEEDS_DATA",
    "BLOCKED_NEEDS_API",
    "BLOCKED_NEEDS_MODEL_GATE",
    "BLOCKED_NEEDS_HUMAN_APPROVAL",
    "BLOCKED_NEEDS_SOURCE_POLICY",
    "DEFER",
}

REQUIRED_COLUMNS = (
    "tool_id",
    "tool_name",
    "tool_group",
    "decision",
    "status_label",
    "output_type",
    "required_data_summary",
    "nwr_coverage_summary",
    "blocker_next_gate",
    "scaffold_status",
    "active_output_allowed",
    "model_input_allowed",
    "uses_market_or_adp",
    "uses_cfbd_or_nfl_usage",
    "docs_spec",
    "next_step",
    "notes",
)


@dataclass(frozen=True)
class FutureToolStatus:
    tool_id: str
    tool_name: str
    tool_group: str
    decision: str
    status_label: str
    output_type: str
    required_data_summary: str
    nwr_coverage_summary: str
    blocker_next_gate: str
    scaffold_status: str
    active_output_allowed: str
    model_input_allowed: str
    uses_market_or_adp: str
    uses_cfbd_or_nfl_usage: str
    docs_spec: str
    next_step: str
    notes: str

    @property
    def is_blocked(self) -> bool:
        return self.decision.startswith("BLOCKED") or self.decision == "DEFER"

    @property
    def is_framework_only(self) -> bool:
        return self.decision == "SAFE_NOW_FRAMEWORK_ONLY"


def load_future_tools_status_matrix(path: Path | None = None) -> list[FutureToolStatus]:
    source = path or STATUS_MATRIX_PATH
    with source.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"Future Tools status matrix missing columns: {', '.join(missing)}")
        rows = [
            FutureToolStatus(**{column: row.get(column, "") for column in REQUIRED_COLUMNS})
            for row in reader
        ]
    validate_future_tools_statuses(rows)
    return rows


def validate_future_tools_statuses(rows: list[FutureToolStatus]) -> None:
    if not rows:
        raise ValueError("Future Tools status matrix is empty.")
    for row in rows:
        if row.decision not in ALLOWED_DECISIONS:
            raise ValueError(f"{row.tool_id} has unsupported decision {row.decision!r}.")
        if row.active_output_allowed.lower() != "no":
            raise ValueError(f"{row.tool_id} incorrectly allows active output.")
        if row.model_input_allowed.lower() != "no":
            raise ValueError(f"{row.tool_id} incorrectly allows model input.")


def group_future_tools(rows: list[FutureToolStatus]) -> dict[str, list[FutureToolStatus]]:
    grouped: dict[str, list[FutureToolStatus]] = {}
    for row in rows:
        grouped.setdefault(row.tool_group, []).append(row)
    return grouped


def future_tools_summary(rows: list[FutureToolStatus]) -> dict[str, int]:
    return {
        "total_tools": len(rows),
        "blocked": sum(1 for row in rows if row.is_blocked),
        "framework_only": sum(1 for row in rows if row.is_framework_only),
        "active_outputs": sum(1 for row in rows if row.active_output_allowed.lower() == "yes"),
        "model_inputs": sum(1 for row in rows if row.model_input_allowed.lower() == "yes"),
    }
