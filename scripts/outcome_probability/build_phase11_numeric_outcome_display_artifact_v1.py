from __future__ import annotations

import csv
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.services.nwr_outcome_numeric_probability_display_service import (  # noqa: E402
    APPROVED_NUMERIC_OUTCOME_HEADS,
    ARTIFACT_REQUIRED_COLUMNS,
    DEFAULT_NUMERIC_OUTCOME_DISPLAY_ARTIFACT,
    DISPLAY_COLUMNS,
    HEAD_POSITION,
    _validate_artifact_rows,
)

DRY_RUN_ROWS = REPO_ROOT / (
    "local_exports/outcome_probability/phase10_numeric_probability_display_runway/"
    "sprint_5ed_current_player_probability_dry_run/current_player_probability_dry_run.csv"
)
ARTIFACT_VERSION = "phase11_numeric_outcome_display_v1"
SOURCE_EVIDENCE_VERSION = "phase10_5ed_5ee_green_local_dry_run"
EXPECTED_ROWS = 240
EXPECTED_AVAILABLE = 227
EXPECTED_UNAVAILABLE = 13

FORBIDDEN_HEADS = (
    "qb_t6",
    "rb_t6",
    "wr_t6",
    "te_t3",
    "te_t6",
    "qb_t18",
    "qb_t24",
    "rb_t36",
    "rb_t48",
    "wr_t48",
    "te_t18",
    "te_t24",
)


def main() -> None:
    source_rows = _read_rows(DRY_RUN_ROWS)
    artifact_rows = [_artifact_row(row) for row in source_rows]
    _validate_counts(artifact_rows)
    _validate_no_forbidden_heads(artifact_rows)
    _validate_artifact_rows(artifact_rows)
    DEFAULT_NUMERIC_OUTCOME_DISPLAY_ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    _write_csv(DEFAULT_NUMERIC_OUTCOME_DISPLAY_ARTIFACT, artifact_rows)
    print(f"VERDICT=GREEN")
    print(f"artifact_path={DEFAULT_NUMERIC_OUTCOME_DISPLAY_ARTIFACT.relative_to(REPO_ROOT)}")
    print(f"rows={len(artifact_rows)}")
    print(f"available={sum(row['outcome_status'] == 'available' for row in artifact_rows)}")
    print(f"unavailable={sum(row['outcome_status'] == 'unavailable' for row in artifact_rows)}")
    print(f"approved_heads={','.join(APPROVED_NUMERIC_OUTCOME_HEADS)}")
    print("sorting_fields_created=false")
    print("hidden_sort_keys_created=false")
    print("promoted_artifacts_created=false")


def _artifact_row(row: dict[str, str]) -> dict[str, str]:
    status = row.get("outcome_probability_status", "")
    available = status == "local_dry_run_probability_available"
    position = str(row.get("position") or "").upper()
    artifact = {
        "player_id": row.get("player_id", ""),
        "player_display_name": row.get("player_display_name", ""),
        "position": position,
        "outcome_status": "available" if available else "unavailable",
        "unavailable_reason_public": _public_unavailable_reason(row),
        "artifact_version": ARTIFACT_VERSION,
        "source_evidence_version": SOURCE_EVIDENCE_VERSION,
        "generated_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    for head in APPROVED_NUMERIC_OUTCOME_HEADS:
        value = row.get(f"{head}_probability_audit_unit", "")
        if available and HEAD_POSITION[head] == position and value:
            artifact[f"{head}_display_pct"] = _whole_percent(value)
        else:
            artifact[f"{head}_display_pct"] = ""
    return {column: artifact.get(column, "") for column in ARTIFACT_REQUIRED_COLUMNS}


def _whole_percent(value: str) -> str:
    parsed = float(value)
    if parsed < 0 or parsed > 1:
        raise ValueError(f"Probability out of bounds: {value}")
    return f"{round(parsed * 100):.0f}%"


def _public_unavailable_reason(row: dict[str, str]) -> str:
    reason = row.get("unavailable_reason", "")
    if not reason:
        return ""
    if reason == "unsupported_position":
        return "unavailable"
    if reason == "missing_feature_snapshot":
        return "under_review"
    return "under_review"


def _validate_counts(rows: list[dict[str, str]]) -> None:
    available = sum(row["outcome_status"] == "available" for row in rows)
    unavailable = sum(row["outcome_status"] == "unavailable" for row in rows)
    if len(rows) != EXPECTED_ROWS or available != EXPECTED_AVAILABLE or unavailable != EXPECTED_UNAVAILABLE:
        raise SystemExit(
            "YELLOW unexpected row counts: "
            f"rows={len(rows)} available={available} unavailable={unavailable}"
        )


def _validate_no_forbidden_heads(rows: list[dict[str, str]]) -> None:
    columns = set(rows[0]) if rows else set()
    for head in FORBIDDEN_HEADS:
        if any(column.startswith(f"{head}_") for column in columns):
            raise ValueError(f"Forbidden head present in artifact: {head}")
    for row in rows:
        for column in DISPLAY_COLUMNS:
            if "sort" in column.lower() or "rank" in column.lower() or "hidden" in column.lower():
                raise ValueError(f"Forbidden display artifact field: {column}")
            value = row[column]
            if value and not value.endswith("%"):
                raise ValueError(f"Non-display-safe value in {column}: {value}")


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=ARTIFACT_REQUIRED_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
