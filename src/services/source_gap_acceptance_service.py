from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

SOURCE_GAP_ACCEPTANCE_FILE = "source_coverage_gap_acceptances.csv"
SOURCE_GAP_ACCEPTANCE_FIELDS = (
    "player_id",
    "bucket",
    "gap_type",
    "review_status",
    "accepted_reason",
    "confidence_penalty_retained",
    "reviewed_by",
    "reviewed_at",
)
OPTIONAL_BUCKETS = {"projections", "injury", "market"}
BUCKET_ALIASES = {
    "projection": "projections",
    "projections": "projections",
    "injury": "injury",
    "market": "market",
    "market/liquidity": "market",
    "market_liquidity": "market",
    "liquidity": "market",
}


@dataclass(frozen=True)
class SourceGapAcceptanceReport:
    rows: list[dict[str, object]]
    invalid_rows: list[dict[str, object]]
    accepted_keys: set[tuple[str, str]]
    accepted_global_bucket_keys: set[str]
    summary_rows: list[dict[str, object]]
    source_path: str


def build_source_gap_acceptance_report(path: str | Path) -> SourceGapAcceptanceReport:
    source_path = Path(path)
    if not source_path.exists():
        return SourceGapAcceptanceReport(
            rows=[],
            invalid_rows=[],
            accepted_keys=set(),
            accepted_global_bucket_keys=set(),
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
        normalized_row = _normalized_row(row)
        errors = _row_errors(normalized_row)
        enriched = dict(normalized_row)
        enriched["row_number"] = index
        enriched["acceptance_key"] = "|".join(source_gap_acceptance_key(enriched))
        if errors:
            enriched["validation_errors"] = "; ".join(errors)
            invalid_rows.append(enriched)
        else:
            enriched["validation_errors"] = ""
            valid_rows.append(enriched)
    accepted_rows = [
        row
        for row in valid_rows
        if _normalized_status(row.get("review_status")) == "accepted"
    ]
    accepted_keys = {
        source_gap_acceptance_key(row)
        for row in accepted_rows
        if row.get("player_id")
    }
    global_bucket_keys = {
        str(row["bucket"])
        for row in accepted_rows
        if not row.get("player_id") and row.get("bucket")
    }
    return SourceGapAcceptanceReport(
        rows=valid_rows,
        invalid_rows=invalid_rows,
        accepted_keys=accepted_keys,
        accepted_global_bucket_keys=global_bucket_keys,
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


def source_gap_acceptance_lookup(
    path: str | Path,
) -> tuple[dict[tuple[str, str], dict[str, object]], SourceGapAcceptanceReport]:
    report = build_source_gap_acceptance_report(path)
    lookup: dict[tuple[str, str], dict[str, object]] = {}
    for row in report.rows:
        if source_gap_acceptance_key(row) in report.accepted_keys:
            lookup[source_gap_acceptance_key(row)] = row
        elif (
            not row.get("player_id")
            and str(row.get("bucket")) in report.accepted_global_bucket_keys
        ):
            lookup[("", str(row["bucket"]))] = row
    return lookup, report


def source_gap_acceptance_key(row: dict[str, object]) -> tuple[str, str]:
    return (
        str(row.get("player_id") or "").strip(),
        normalize_bucket(row.get("bucket")),
    )


def normalize_bucket(value: object) -> str:
    text = str(value or "").strip().lower().replace("_", " ")
    text = " ".join(text.split())
    text = text.replace(" ", "_") if text == "market liquidity" else text
    return BUCKET_ALIASES.get(text, text)


def _normalized_row(row: dict[str, object]) -> dict[str, object]:
    output = dict(row)
    output["bucket"] = normalize_bucket(output.get("bucket"))
    if not output.get("accepted_reason") and output.get("reason"):
        output["accepted_reason"] = output.get("reason")
    return output


def _row_errors(row: dict[str, object]) -> list[str]:
    errors: list[str] = []
    missing_columns = [
        field
        for field in SOURCE_GAP_ACCEPTANCE_FIELDS
        if field not in row
    ]
    if missing_columns:
        errors.append("missing columns: " + ", ".join(missing_columns))
    player_id = str(row.get("player_id") or "").strip()
    bucket = normalize_bucket(row.get("bucket"))
    if not player_id and not bucket:
        errors.append("player_id or bucket is required")
    if bucket not in OPTIONAL_BUCKETS:
        errors.append("bucket must be projection, injury, or market/liquidity")
    for field in (
        "gap_type",
        "review_status",
        "accepted_reason",
        "confidence_penalty_retained",
        "reviewed_by",
        "reviewed_at",
    ):
        if not str(row.get(field) or "").strip():
            errors.append(f"{field} is required")
    if _normalized_status(row.get("review_status")) != "accepted":
        errors.append("review_status must be accepted")
    if not _truthy(row.get("confidence_penalty_retained")):
        errors.append("confidence_penalty_retained must be true")
    if row.get("reviewed_at") and not _valid_datetime(row.get("reviewed_at")):
        errors.append("reviewed_at must be ISO 8601 date or datetime")
    return errors


def _normalized_status(value: object) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _truthy(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def _valid_datetime(value: object) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))
