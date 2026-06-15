import csv
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.rookie_framework.build_rookie_historical_outcome_labels_v1 import build_exports  # noqa: E402


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


def test_historical_outcome_label_builder_uses_eval_labels_only() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        features = root / "historical_features.csv"
        stats = root / "player_stats.csv"
        stats_2025 = root / "player_stats_2025.csv"
        output_dir = root / "labels"

        write_csv(
            features,
            [
                {
                    "historical_prospect_key": "backtest:2021:alpharunner:RB:1",
                    "prospect_name": "Alpha Runner",
                    "normalized_player_name": "alpharunner",
                    "position": "RB",
                    "college": "Test State",
                    "nfl_team": "testers",
                    "draft_year": "2021",
                },
                {
                    "historical_prospect_key": "backtest:2025:betawideout:WR:2",
                    "prospect_name": "Beta Wideout",
                    "normalized_player_name": "betawideout",
                    "position": "WR",
                    "college": "Example",
                    "nfl_team": "examples",
                    "draft_year": "2025",
                },
            ],
        )
        write_csv(
            stats,
            [
                {
                    "season": "2021",
                    "season_type": "REG",
                    "player_display_name": "Alpha Runner",
                    "position_group": "RB",
                    "rushing_yards": "1000",
                    "rushing_tds": "5",
                    "rushing_first_downs": "50",
                },
                {
                    "season": "2022",
                    "season_type": "REG",
                    "player_display_name": "Alpha Runner",
                    "position_group": "RB",
                    "rushing_yards": "500",
                    "rushing_tds": "2",
                    "rushing_first_downs": "20",
                },
            ],
        )
        write_csv(
            stats_2025,
            [
                {
                    "season": "2025",
                    "season_type": "REG",
                    "player_display_name": "Beta Wideout",
                    "position_group": "WR",
                    "receiving_yards": "700",
                    "receiving_tds": "4",
                    "receiving_first_downs": "35",
                    "punt_return_yards": "90",
                },
            ],
        )

        counts = build_exports(features, stats, stats_2025, output_dir)
        labels = read_csv(output_dir / "rookie_historical_outcome_labels_v1_20260615.csv")
        readiness = read_csv(output_dir / "rookie_historical_backtest_readiness_20260615.csv")

        assert counts["label_rows"] == 2
        assert counts["backtest_ready_rows"] == 1
        assert counts["partial_rows"] == 1
        assert {row["historical_prospect_key"] for row in labels} == {
            "backtest:2021:alpharunner:RB:1",
            "backtest:2025:betawideout:WR:2",
        }
        assert all(row["eval_label_source"] for row in labels)
        assert all(row["eval_backtest_ready_flag"] in {"yes", "partial"} for row in labels)
        assert all(row["eval_reach_flag"] == "market_labels_blocked_no_admitted_source" for row in labels)
        assert all(row["eval_value_pick_flag"] == "market_labels_blocked_no_admitted_source" for row in labels)
        assert all("feature_" not in column for column in labels[0])
        assert not any(row["label_star_flag"] == "1" and row["label_bust_flag"] == "1" for row in labels)
        assert any(row["check_name"] == "market_labels" and row["status"] == "blocked" for row in readiness)


if __name__ == "__main__":
    test_historical_outcome_label_builder_uses_eval_labels_only()
    print("rookie_historical_outcome_labels_v1 direct harness passed")
