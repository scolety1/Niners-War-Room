from __future__ import annotations

import csv
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.services.nwr_outcome_numeric_probability_display_service import (
    APPROVED_NUMERIC_OUTCOME_HEADS,
    ARTIFACT_REQUIRED_COLUMNS,
    BLOCKED_NUMERIC_OUTCOME_HEADS,
    DEFAULT_NUMERIC_OUTCOME_DISPLAY_ARTIFACT,
    DISPLAY_COLUMNS,
    load_numeric_outcome_display_rows,
    numeric_outcome_display_for_player,
    numeric_outcome_display_sort_value,
)


class NumericOutcomeProbabilityDisplayServiceTests(unittest.TestCase):
    def test_numeric_artifact_exists_and_uses_exact_contract(self) -> None:
        self.assertTrue(DEFAULT_NUMERIC_OUTCOME_DISPLAY_ARTIFACT.exists())
        with DEFAULT_NUMERIC_OUTCOME_DISPLAY_ARTIFACT.open(
            newline="",
            encoding="utf-8-sig",
        ) as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)

        self.assertEqual(tuple(reader.fieldnames or ()), ARTIFACT_REQUIRED_COLUMNS)
        self.assertEqual(len(rows), 240)
        self.assertEqual(sum(row["outcome_status"] == "available" for row in rows), 227)
        self.assertEqual(sum(row["outcome_status"] == "unavailable" for row in rows), 13)

    def test_numeric_artifact_contains_only_approved_heads_and_no_sort_fields(self) -> None:
        columns = set(ARTIFACT_REQUIRED_COLUMNS)

        for head in APPROVED_NUMERIC_OUTCOME_HEADS:
            self.assertIn(f"{head}_display_pct", columns)
        for head in BLOCKED_NUMERIC_OUTCOME_HEADS:
            self.assertFalse(any(column.startswith(f"{head}_") for column in columns))
        self.assertFalse(any("sort" in column.lower() for column in columns))
        self.assertFalse(any("hidden" in column.lower() for column in columns))
        self.assertFalse(any("rank_delta" in column.lower() for column in columns))

    def test_numeric_display_values_are_whole_percentages_or_blank(self) -> None:
        with DEFAULT_NUMERIC_OUTCOME_DISPLAY_ARTIFACT.open(
            newline="",
            encoding="utf-8-sig",
        ) as handle:
            rows = list(csv.DictReader(handle))

        for row in rows:
            for column in DISPLAY_COLUMNS:
                value = row[column]
                if not value:
                    continue
                self.assertTrue(value.endswith("%"))
                digits = value[:-1]
                self.assertTrue(digits.isdigit())
                self.assertGreaterEqual(int(digits), 0)
                self.assertLessEqual(int(digits), 100)

    def test_unavailable_rows_do_not_receive_fake_zeroes(self) -> None:
        with DEFAULT_NUMERIC_OUTCOME_DISPLAY_ARTIFACT.open(
            newline="",
            encoding="utf-8-sig",
        ) as handle:
            rows = list(csv.DictReader(handle))

        unavailable_rows = [row for row in rows if row["outcome_status"] == "unavailable"]
        self.assertTrue(unavailable_rows)
        for row in unavailable_rows:
            self.assertIn(row["unavailable_reason_public"], {"unavailable", "under_review"})
            self.assertTrue(all(row[column] == "" for column in DISPLAY_COLUMNS))

    def test_service_joins_by_player_id_and_returns_position_relevant_heads(self) -> None:
        rows_by_player_id = load_numeric_outcome_display_rows()
        rb_row = next(
            row
            for row in rows_by_player_id.values()
            if row.position == "RB" and row.outcome_status == "available"
        )

        display = numeric_outcome_display_for_player(rb_row.player_id, "RB", rows_by_player_id)

        self.assertTrue(display["rb_t12"].endswith("%"))
        self.assertTrue(display["rb_t24"].endswith("%"))
        self.assertEqual(display["qb_t12"], "")
        self.assertEqual(display["wr_t12"], "")
        self.assertEqual(display["te_t12"], "")

    def test_service_exposes_no_sortable_value(self) -> None:
        row = next(iter(load_numeric_outcome_display_rows().values()))

        self.assertIsNone(numeric_outcome_display_sort_value(row))

    def test_service_rejects_unexpected_columns(self) -> None:
        artifact = Path("tmp") / "test_numeric_outcome_bad.csv"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        columns = (*ARTIFACT_REQUIRED_COLUMNS, "outcome_sort_value")
        with artifact.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns)
            writer.writeheader()
            row = {column: "" for column in columns}
            row.update({"player_id": "p1", "outcome_status": "available"})
            writer.writerow(row)

        try:
            with self.assertRaisesRegex(ValueError, "Unexpected Numeric Outcome artifact columns"):
                load_numeric_outcome_display_rows(artifact)
        finally:
            artifact.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
