from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

OUTLIER_ACCEPTANCE_FILE = "model_outlier_acceptances.csv"
OUTLIER_ACCEPTANCE_FIELDS = (
    "player_id",
    "player_name",
    "outlier_type",
    "component",
    "source_feature",
    "review_status",
    "accepted_reason",
    "reviewed_by",
    "reviewed_at",
)


@dataclass(frozen=True)
class OutlierAcceptanceReport:
    rows: list[dict[str, object]]
    invalid_rows: list[dict[str, object]]
    accepted_keys: set[tuple[str, str, str, str]]
    summary_rows: list[dict[str, object]]
    source_path: str


def build_outlier_acceptance_report(path: str | Path) -> OutlierAcceptanceReport:
    source_path = Path(path)
    if not source_path.exists():
        return OutlierAcceptanceReport(
            rows=[],
            invalid_rows=[],
            accepted_keys=set(),
            summary_rows=[
                {
                    "status": "missing",
                    "rows": 0,
                    "accepted": 0,
                    "invalid": 0,
                    "source_path": str(source_path),
                }
            ],
            source_path=str(source_path),
        )
    rows = _read_rows(source_path)
    valid_rows: list[dict[str, object]] = []
    invalid_rows: list[dict[str, object]] = []
    for index, row in enumerate(rows, start=2):
        errors = _row_errors(row)
        enriched = dict(row)
        enriched["row_number"] = index
        enriched["acceptance_key"] = "|".join(outlier_acceptance_key(row))
        if errors:
            enriched["validation_errors"] = "; ".join(errors)
            invalid_rows.append(enriched)
        else:
            enriched["validation_errors"] = ""
            valid_rows.append(enriched)
    accepted_rows = [
        row for row in valid_rows if _normalized_status(row.get("review_status")) == "accepted"
    ]
    accepted_keys = {outlier_acceptance_key(row) for row in accepted_rows}
    return OutlierAcceptanceReport(
        rows=valid_rows,
        invalid_rows=invalid_rows,
        accepted_keys=accepted_keys,
        summary_rows=[
            {
                "status": "loaded",
                "rows": len(rows),
                "accepted": len(accepted_rows),
                "invalid": len(invalid_rows),
                "source_path": str(source_path),
            }
        ],
        source_path=str(source_path),
    )


def apply_outlier_acceptances(
    outlier_rows: list[dict[str, object]],
    acceptance_path: str | Path,
) -> tuple[list[dict[str, object]], OutlierAcceptanceReport]:
    report = build_outlier_acceptance_report(acceptance_path)
    accepted_by_key = {
        outlier_acceptance_key(row): row
        for row in report.rows
        if outlier_acceptance_key(row) in report.accepted_keys
    }
    output: list[dict[str, object]] = []
    for row in outlier_rows:
        updated = dict(row)
        acceptance = accepted_by_key.get(outlier_acceptance_key(row))
        if acceptance:
            updated["acceptance_status"] = "accepted"
            updated["review_status"] = "accepted"
            updated["accepted_reason"] = acceptance.get("accepted_reason", "")
            updated["reviewed_by"] = acceptance.get("reviewed_by", "")
            updated["reviewed_at"] = acceptance.get("reviewed_at", "")
            updated["next_action"] = "Accepted with audited reason; scores unchanged."
        else:
            updated["acceptance_status"] = "unresolved"
            updated.setdefault("accepted_reason", "")
            updated.setdefault("reviewed_by", "")
            updated.setdefault("reviewed_at", "")
        output.append(updated)
    return output, report


def outlier_acceptance_key(row: dict[str, object]) -> tuple[str, str, str, str]:
    return (
        str(row.get("player_id") or "").strip(),
        str(row.get("outlier_type") or "").strip(),
        str(row.get("component") or "").strip(),
        str(row.get("source_feature") or "").strip(),
    )


def outlier_acceptance_template_rows(
    outlier_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    return [
        {
            "player_id": row.get("player_id", ""),
            "player_name": row.get("player") or row.get("player_name") or "",
            "outlier_type": row.get("outlier_type", ""),
            "component": row.get("component", ""),
            "source_feature": row.get("source_feature", ""),
            "review_status": "accepted",
            "accepted_reason": "",
            "reviewed_by": "",
            "reviewed_at": "",
        }
        for row in outlier_rows
    ]


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _row_errors(row: dict[str, object]) -> list[str]:
    errors: list[str] = []
    missing_columns = [
        field
        for field in OUTLIER_ACCEPTANCE_FIELDS
        if field not in row
    ]
    if missing_columns:
        errors.append("missing columns: " + ", ".join(missing_columns))
    required_values = [
        "player_id",
        "player_name",
        "outlier_type",
        "review_status",
        "accepted_reason",
        "reviewed_by",
        "reviewed_at",
    ]
    for field in required_values:
        if not str(row.get(field) or "").strip():
            errors.append(f"{field} is required")
    if _normalized_status(row.get("review_status")) != "accepted":
        errors.append("review_status must be accepted")
    if row.get("reviewed_at") and not _valid_datetime(row.get("reviewed_at")):
        errors.append("reviewed_at must be ISO 8601 date or datetime")
    return errors


def _normalized_status(value: object) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _valid_datetime(value: object) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True
