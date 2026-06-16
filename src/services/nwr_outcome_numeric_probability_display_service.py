from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_NUMERIC_OUTCOME_DISPLAY_ARTIFACT = (
    REPO_ROOT / "app/generated/outcome_probability/numeric_outcome_display_v1.csv"
)

APPROVED_NUMERIC_OUTCOME_HEADS = (
    "qb_t12",
    "rb_t12",
    "rb_t24",
    "wr_t12",
    "wr_t24",
    "wr_t36",
    "te_t12",
)
BLOCKED_NUMERIC_OUTCOME_HEADS = (
    "qb_t6",
    "rb_t6",
    "wr_t6",
    "te_t3",
    "te_t6",
)
HEAD_LABELS = {
    "qb_t12": "QB T12",
    "rb_t12": "RB T12",
    "rb_t24": "RB T24",
    "wr_t12": "WR T12",
    "wr_t24": "WR T24",
    "wr_t36": "WR T36",
    "te_t12": "TE T12",
}
HEAD_POSITION = {
    "qb_t12": "QB",
    "rb_t12": "RB",
    "rb_t24": "RB",
    "wr_t12": "WR",
    "wr_t24": "WR",
    "wr_t36": "WR",
    "te_t12": "TE",
}
DISPLAY_COLUMNS = tuple(f"{head}_display_pct" for head in APPROVED_NUMERIC_OUTCOME_HEADS)
ARTIFACT_REQUIRED_COLUMNS = (
    "player_id",
    "player_display_name",
    "position",
    "outcome_status",
    *DISPLAY_COLUMNS,
    "unavailable_reason_public",
    "artifact_version",
    "source_evidence_version",
    "generated_at_utc",
)
FORBIDDEN_ARTIFACT_FRAGMENTS = (
    "sort",
    "hidden",
    "rank_delta",
    "ranking_delta",
    "market",
    "projection",
    "adp",
    "trade",
    "raw_probability",
    "probability_audit_unit",
)


@dataclass(frozen=True)
class NumericOutcomeDisplayRow:
    player_id: str
    player_display_name: str
    position: str
    outcome_status: str
    display_values_by_head: dict[str, str]
    unavailable_reason_public: str


def load_numeric_outcome_display_rows(
    artifact_path: str | Path = DEFAULT_NUMERIC_OUTCOME_DISPLAY_ARTIFACT,
) -> dict[str, NumericOutcomeDisplayRow]:
    path = Path(artifact_path)
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    _validate_artifact_rows(rows)
    return {
        row["player_id"]: NumericOutcomeDisplayRow(
            player_id=row["player_id"],
            player_display_name=row["player_display_name"],
            position=row["position"],
            outcome_status=row["outcome_status"],
            display_values_by_head={
                head: row.get(f"{head}_display_pct", "")
                for head in APPROVED_NUMERIC_OUTCOME_HEADS
            },
            unavailable_reason_public=row.get("unavailable_reason_public", ""),
        )
        for row in rows
    }


def numeric_outcome_display_for_player(
    player_id: object,
    position: object,
    rows_by_player_id: dict[str, NumericOutcomeDisplayRow],
) -> dict[str, str]:
    row = rows_by_player_id.get(str(player_id or ""))
    if row is None:
        return _unavailable_values("unavailable")
    if row.outcome_status != "available":
        return _unavailable_values(row.unavailable_reason_public or "unavailable")
    player_position = str(position or row.position or "").upper()
    values: dict[str, str] = {}
    for head in APPROVED_NUMERIC_OUTCOME_HEADS:
        if HEAD_POSITION[head] == player_position:
            values[head] = row.display_values_by_head.get(head) or "unavailable"
        else:
            values[head] = ""
    return values


def numeric_outcome_column_labels() -> dict[str, str]:
    return dict(HEAD_LABELS)


def numeric_outcome_display_sort_value(_row: NumericOutcomeDisplayRow) -> None:
    return None


def _unavailable_values(reason: str) -> dict[str, str]:
    _ = reason
    return {head: "unavailable" for head in APPROVED_NUMERIC_OUTCOME_HEADS}


def _validate_artifact_rows(rows: list[dict[str, str]]) -> None:
    if not rows:
        raise ValueError("Numeric Outcome display artifact is empty.")
    columns = tuple(rows[0].keys())
    if columns != ARTIFACT_REQUIRED_COLUMNS:
        raise ValueError(f"Unexpected Numeric Outcome artifact columns: {columns!r}")
    for column in columns:
        lower = column.lower()
        if any(fragment in lower for fragment in FORBIDDEN_ARTIFACT_FRAGMENTS):
            raise ValueError(f"Forbidden Numeric Outcome artifact column: {column}")
    for blocked_head in BLOCKED_NUMERIC_OUTCOME_HEADS:
        blocked_prefix = f"{blocked_head}_"
        if any(column.startswith(blocked_prefix) for column in columns):
            raise ValueError(f"Blocked Numeric Outcome head present: {blocked_head}")
    for row in rows:
        status = row["outcome_status"]
        if status not in {"available", "unavailable"}:
            raise ValueError(f"Unsupported Numeric Outcome status: {status}")
        for head in APPROVED_NUMERIC_OUTCOME_HEADS:
            value = row[f"{head}_display_pct"]
            if not value:
                continue
            if status != "available":
                raise ValueError("Unavailable rows must not contain display percentages.")
            if not value.endswith("%"):
                raise ValueError(f"Display value must be a percentage string: {value}")
            digits = value[:-1]
            if not digits.isdigit():
                raise ValueError(f"Display percentage must be whole-number only: {value}")
            parsed = int(digits)
            if parsed < 0 or parsed > 100:
                raise ValueError(f"Display percentage out of bounds: {value}")
