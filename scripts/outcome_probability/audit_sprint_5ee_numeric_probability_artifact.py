from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

DRY_RUN_DIR = Path(
    "local_exports/outcome_probability/phase10_numeric_probability_display_runway/"
    "sprint_5ed_current_player_probability_dry_run"
)
DRY_RUN_ROWS = DRY_RUN_DIR / "current_player_probability_dry_run.csv"
DRY_RUN_SUMMARY = DRY_RUN_DIR / "current_player_probability_dry_run_summary.json"
OUTPUT_DIR = Path(
    "local_exports/outcome_probability/phase10_numeric_probability_display_runway/"
    "sprint_5ee_numeric_probability_artifact_audit"
)

APPROVED_HEADS = ("qb_t12", "rb_t12", "rb_t24", "wr_t12", "wr_t24", "wr_t36", "te_t12")
BLOCKED_HEADS = ("qb_t6", "rb_t6", "wr_t6", "te_t3", "te_t6")
DEFERRED_HEADS = ("qb_t18", "qb_t24", "rb_t36", "rb_t48", "wr_t48", "te_t18", "te_t24")
PROBABILITY_COLUMNS = tuple(f"{head}_probability_audit_unit" for head in APPROVED_HEADS)
FORBIDDEN_COLUMN_TERMS = (
    "sort",
    "rank_delta",
    "ranking_delta",
    "market",
    "projection",
    "adp",
    "trade",
    "rotowire",
    "private_score",
)


def main() -> None:
    rows = _read_rows(DRY_RUN_ROWS)
    summary = json.loads(DRY_RUN_SUMMARY.read_text(encoding="utf-8"))
    audit = _audit(rows, summary)
    sample = _human_review_sample(rows)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "numeric_probability_artifact_audit_summary.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    _write_csv(
        OUTPUT_DIR / "numeric_probability_human_review_sample.csv",
        sample,
        (
            "sample_reason",
            "player_id",
            "player_display_name",
            "position",
            "head",
            "probability_audit_unit",
            "outcome_probability_status",
            "unavailable_reason",
        ),
    )
    print(json.dumps(audit, indent=2, sort_keys=True))


def _audit(rows: list[dict[str, str]], summary: dict[str, object]) -> dict[str, object]:
    columns = set(rows[0]) if rows else set()
    unexpected_probability_columns = sorted(
        column
        for column in columns
        if column.endswith("_probability_audit_unit") and column not in PROBABILITY_COLUMNS
    )
    forbidden_columns = sorted(
        column
        for column in columns
        if any(term in column.lower() for term in FORBIDDEN_COLUMN_TERMS)
    )
    bounded_failures = []
    null_failures = []
    emitted_counts = Counter()
    for row in rows:
        status = row.get("outcome_probability_status", "")
        for column in PROBABILITY_COLUMNS:
            value = row.get(column, "")
            head = column.removesuffix("_probability_audit_unit")
            if value:
                emitted_counts[head] += 1
                parsed = float(value)
                if parsed < 0 or parsed > 1:
                    bounded_failures.append(f"{row.get('player_id')}:{column}:{value}")
                if status != "local_dry_run_probability_available":
                    null_failures.append(f"{row.get('player_id')}:{column}:probability_on_unavailable")
        if status == "local_dry_run_probability_available" and not any(
            row.get(column) for column in PROBABILITY_COLUMNS
        ):
            null_failures.append(f"{row.get('player_id')}:available_without_probability")
        if status == "unavailable" and any(row.get(column) for column in PROBABILITY_COLUMNS):
            null_failures.append(f"{row.get('player_id')}:unavailable_with_probability")

    rb_t24_ok = bool(summary.get("rb_t24_included")) and emitted_counts["rb_t24"] > 0
    verdict = (
        "GREEN"
        if not unexpected_probability_columns
        and not forbidden_columns
        and not bounded_failures
        and not null_failures
        and rb_t24_ok
        else "RED"
    )
    return {
        "verdict": verdict,
        "dry_run_dir": str(DRY_RUN_DIR),
        "rows_audited": len(rows),
        "approved_heads": list(APPROVED_HEADS),
        "blocked_heads_absent": not unexpected_probability_columns,
        "unexpected_probability_columns": unexpected_probability_columns,
        "forbidden_columns": forbidden_columns,
        "probability_bounds_pass": not bounded_failures,
        "bounded_failures": bounded_failures[:20],
        "null_unavailable_policy_pass": not null_failures,
        "null_failures": null_failures[:20],
        "emitted_counts_by_head": dict(sorted(emitted_counts.items())),
        "rb_t24_emitted_only_after_5ec_green": rb_t24_ok,
        "hidden_sort_keys_created": False,
        "rankings_sorting_fields_created": False,
        "app_readable_output_created": False,
        "exact_app_percentages_created": False,
        "coarse_app_bands_created": False,
        "promoted_artifacts_created": False,
        "human_review_sample_created": True,
    }


def _human_review_sample(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    sample: list[dict[str, str]] = []
    for head in APPROVED_HEADS:
        column = f"{head}_probability_audit_unit"
        values = [row for row in rows if row.get(column)]
        if values:
            high = max(values, key=lambda row: float(row[column]))
            low = min(values, key=lambda row: float(row[column]))
            sample.append(_sample_row("high_local_estimate", high, head, column))
            sample.append(_sample_row("low_local_estimate", low, head, column))
    unavailable = [row for row in rows if row.get("outcome_probability_status") == "unavailable"]
    for row in unavailable[:10]:
        sample.append(_sample_row("unavailable_row", row, "", ""))
    for position in ("QB", "RB", "WR", "TE"):
        position_rows = [
            row
            for row in rows
            if row.get("position") == position
            and row.get("outcome_probability_status") == "local_dry_run_probability_available"
        ]
        if position_rows:
            row = position_rows[0]
            first_head = next(
                head
                for head in APPROVED_HEADS
                if row.get(f"{head}_probability_audit_unit")
            )
            sample.append(_sample_row("position_example", row, first_head, f"{first_head}_probability_audit_unit"))
    return sample


def _sample_row(reason: str, row: dict[str, str], head: str, column: str) -> dict[str, str]:
    return {
        "sample_reason": reason,
        "player_id": row.get("player_id", ""),
        "player_display_name": row.get("player_display_name", ""),
        "position": row.get("position", ""),
        "head": head,
        "probability_audit_unit": row.get(column, "") if column else "",
        "outcome_probability_status": row.get("outcome_probability_status", ""),
        "unavailable_reason": row.get("unavailable_reason", ""),
    }


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, str]], fieldnames: tuple[str, ...]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
