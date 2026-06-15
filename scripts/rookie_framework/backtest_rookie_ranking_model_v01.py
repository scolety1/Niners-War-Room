"""Inventory and scaffold rookie ranking historical backtest v1.

This script intentionally refuses to fabricate historical labels. It inventories
local point-in-time historical rookie feature data and only writes backtest
results when evaluation label columns are already present.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path


DEFAULT_HISTORICAL = Path(
    "local_exports/model_v4/current_value/latest/full_board_active_support/evidence_matrices/"
    "historical_rookie_backtest_feature_matrix.csv"
)
DEFAULT_OUTPUT_DIR = Path("local_exports/rookie_framework/historical_backtest_v1_20260615")

INVENTORY_COLUMNS = [
    "source_path",
    "exists",
    "rows",
    "draft_years",
    "positions",
    "feature_columns",
    "label_columns",
    "market_context_present",
    "leakage_guardrail",
    "backtest_runnable",
    "reason",
]

RESULT_COLUMNS = [
    "backtest_status",
    "draft_year",
    "rows_evaluated",
    "star_capture_top_12",
    "bust_avoidance_top_12",
    "notes",
]

FAILURE_COLUMNS = ["failure_type", "source_path", "details", "safe_next_step"]

LABEL_HINTS = [
    "outcome",
    "starter_seasons",
    "top_12",
    "top_24",
    "top_36",
    "year1",
    "year_1",
    "year2",
    "year_2",
    "year3",
    "year_3",
    "vbd",
    "fantasy_points_result",
]


class RookieBacktestError(RuntimeError):
    """Raised when historical backtest scaffolding fails."""


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def label_columns(fieldnames: list[str]) -> list[str]:
    return [field for field in fieldnames if any(hint in field.lower() for hint in LABEL_HINTS)]


def has_market_context(rows: list[dict[str, str]]) -> bool:
    if not rows:
        return False
    names = set(rows[0].keys())
    if any("market" in name.lower() or "adp" in name.lower() or "ranking" in name.lower() for name in names):
        return True
    return any(row.get("market_context_fields_json", "").strip() not in {"", "{}", "null"} for row in rows[:50])


def json_keys_present(rows: list[dict[str, str]], field: str) -> int:
    count = 0
    for row in rows:
        raw = row.get(field, "")
        if not raw:
            continue
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if parsed:
            count += 1
    return count


def build_inventory(path: Path) -> tuple[list[dict[str, str]], list[str], list[dict[str, str]]]:
    rows = read_csv(path)
    if not rows:
        return (
            [
                {
                    "source_path": str(path),
                    "exists": "no",
                    "rows": "0",
                    "draft_years": "",
                    "positions": "",
                    "feature_columns": "0",
                    "label_columns": "",
                    "market_context_present": "no",
                    "leakage_guardrail": "not_runnable",
                    "backtest_runnable": "no",
                    "reason": "historical feature matrix missing",
                }
            ],
            [],
            rows,
        )
    fieldnames = list(rows[0].keys())
    labels = label_columns(fieldnames)
    years = sorted({row.get("draft_year", "") for row in rows if row.get("draft_year")})
    positions = sorted({row.get("position", "") for row in rows if row.get("position")})
    factual_json_count = json_keys_present(rows, "factual_evidence_json")
    derived_json_count = json_keys_present(rows, "derived_evidence_json")
    runnable = bool(labels)
    reason = "label columns available" if runnable else "historical features exist, but no evaluation label columns were found"
    return (
        [
            {
                "source_path": str(path),
                "exists": "yes",
                "rows": str(len(rows)),
                "draft_years": "|".join(years),
                "positions": "|".join(positions),
                "feature_columns": str(len(fieldnames)),
                "label_columns": "|".join(labels),
                "market_context_present": "yes" if has_market_context(rows) else "no",
                "leakage_guardrail": (
                    f"features inventoried only; factual_json_rows={factual_json_count}; "
                    f"derived_json_rows={derived_json_count}; outcome labels evaluation-only if later added"
                ),
                "backtest_runnable": "yes" if runnable else "no",
                "reason": reason,
            }
        ],
        labels,
        rows,
    )


def write_readme(output_dir: Path, inventory: list[dict[str, str]]) -> None:
    item = inventory[0]
    text = f"""# Rookie Historical Backtest Framework v1

Status: scaffold/inventory unless `backtest_runnable=yes`.

Historical source: `{item['source_path']}`

- Exists: {item['exists']}
- Rows: {item['rows']}
- Draft years: {item['draft_years']}
- Positions: {item['positions']}
- Backtest runnable: {item['backtest_runnable']}
- Reason: {item['reason']}

No hindsight labels were fabricated. Market context, if present, is audit/display
context only and not a ranking input.
"""
    (output_dir / "README_ROOKIE_HISTORICAL_BACKTEST_V1_20260615.md").write_text(text, encoding="utf-8")


def build_exports(historical_path: Path, output_dir: Path) -> dict[str, int]:
    inventory, labels, rows = build_inventory(historical_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "rookie_historical_backtest_inventory_20260615.csv", inventory, INVENTORY_COLUMNS)
    failures = []
    results = []
    if labels:
        years = sorted({row.get("draft_year", "") for row in rows if row.get("draft_year")})
        for year in years:
            year_rows = [row for row in rows if row.get("draft_year") == year]
            results.append(
                {
                    "backtest_status": "labels_detected_scaffold_only",
                    "draft_year": year,
                    "rows_evaluated": str(len(year_rows)),
                    "star_capture_top_12": "not_computed_in_v1_scaffold",
                    "bust_avoidance_top_12": "not_computed_in_v1_scaffold",
                    "notes": "Labels detected, but v1 does not tune or promote weights.",
                }
            )
    else:
        failures.append(
            {
                "failure_type": "missing_evaluation_labels",
                "source_path": str(historical_path),
                "details": inventory[0]["reason"],
                "safe_next_step": "register point-in-time historical outcome labels before computing star/bust metrics",
            }
        )
    write_csv(output_dir / "rookie_historical_backtest_results_v1_20260615.csv", results, RESULT_COLUMNS)
    write_csv(output_dir / "rookie_historical_backtest_metrics_v1_20260615.csv", [], ["metric", "value", "notes"])
    write_csv(output_dir / "rookie_historical_backtest_failures_v1_20260615.csv", failures, FAILURE_COLUMNS)
    write_readme(output_dir, inventory)
    return {
        "inventory_rows": len(inventory),
        "historical_rows": len(rows),
        "label_columns": len(labels),
        "result_rows": len(results),
        "failure_rows": len(failures),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inventory rookie historical backtest framework v1.")
    parser.add_argument("--historical", type=Path, default=DEFAULT_HISTORICAL)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        counts = build_exports(args.historical, args.output_dir)
    except RookieBacktestError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    for key in sorted(counts):
        print(f"{key}={counts[key]}")
    print(f"output_dir={args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
