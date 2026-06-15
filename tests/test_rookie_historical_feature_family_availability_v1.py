import csv
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.rookie_framework.audit_rookie_historical_feature_family_availability_v1 import (  # noqa: E402
    build_exports,
    classify_column,
)


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_column_classification_blocks_future_and_market_fields() -> None:
    assert classify_column("draft", "round")[0] == "allowed_feature"
    assert classify_column("draft", "w_av")[0] == "blocked_future_or_career"
    assert classify_column("market", "rookie_adp")[0] == "blocked_public_rank_projection_adp"
    assert classify_column("labels", "star_label")[0] == "evaluation_label_only"
    assert classify_column("combine", "forty_yard")[0] == "allowed_feature"


def test_feature_family_audit_exports_expected_files() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        labels = root / "labels.csv"
        current = root / "current.csv"
        out = root / "out"
        write_csv(
            labels,
            [
                {
                    "historical_label_key": "backtest:2021:alpharunner:RB:40",
                    "draft_year": "2021",
                    "player_name": "Alpha Runner",
                    "position": "RB",
                    "backtest_ready": "yes",
                    "partial_window_only": "no",
                }
            ],
        )
        write_csv(
            current,
            [
                {
                    "canonical_prospect_key": "prospect:2026:betawide:WR",
                    "draft_year": "2026",
                    "prospect_name": "Beta Wide",
                    "position": "WR",
                }
            ],
        )

        counts = build_exports(labels, current, out)
        inventory = read_csv(out / "historical_feature_source_inventory_20260615.csv")
        matrix = read_csv(out / "feature_family_availability_matrix_20260615.csv")
        missing = read_csv(out / "missing_data_request_for_tim_20260615.csv")
        columns = read_csv(out / "allowed_blocked_column_audit_20260615.csv")

        assert counts["source_inventory_rows"] >= 10
        assert any(row["feature_family"] == "college_target_earning" for row in matrix)
        assert any(row["priority"] == "1" and "college" in row["requested_file_type"] for row in missing)
        assert any(row["column_name"] == "round" and row["private_score_allowed"] == "yes" for row in columns)
        assert all(row["path"] for row in inventory)


if __name__ == "__main__":
    test_column_classification_blocks_future_and_market_fields()
    test_feature_family_audit_exports_expected_files()
    print("rookie_historical_feature_family_availability_v1 direct harness passed")
