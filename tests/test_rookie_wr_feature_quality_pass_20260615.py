import csv
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.rookie_framework.build_rookie_wr_feature_quality_pass_20260615 import build_exports  # noqa: E402


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def label_row(index: int, year: int, position: str, player_id: str) -> dict[str, object]:
    return {
        "historical_label_key": f"label:{year}:{position}:{index}",
        "draft_year": str(year),
        "expected_cfbd_feature_season": str(year - 1),
        "player_name": f"Player {year} {position} {index}",
        "normalized_player_name": f"player{year}{position.lower()}{index}",
        "position": position,
        "college": "Test State",
        "draft_round": "1" if index <= 2 else "3",
        "overall_pick": str(index),
        "historical_label_status": "GREEN_COMPLETE",
        "backtest_ready": "yes",
        "partial_window_only": "no",
        "star_label": "1" if position == "WR" and index == 1 else "0",
        "bust_label": "1" if position == "WR" and index == 4 else "0",
        "useful_label": "1",
        "starter_season_count": "1",
        "best_first_3_years_pos_finish": "9",
        "year1_points": "20",
        "year2_points": "20",
        "year3_points": "20",
        "three_year_points": "60",
        "label_quality_notes": "",
        "label_scoring_quality": "test",
        "guardrails": "labels_eval_only",
        "cfbd_player_id": player_id,
    }


def join_row(label: dict[str, object], player_id: str, receiving_yards: str) -> dict[str, object]:
    return {
        "historical_label_key": label["historical_label_key"],
        "draft_year": label["draft_year"],
        "expected_cfbd_feature_season": label["expected_cfbd_feature_season"],
        "player_name": label["player_name"],
        "normalized_player_name": label["normalized_player_name"],
        "position": label["position"],
        "college": label["college"],
        "draft_round": label["draft_round"],
        "overall_pick": label["overall_pick"],
        "label_status": "GREEN_COMPLETE",
        "backtest_ready": "yes",
        "partial_window_only": "no",
        "cfbd_join_status_after_repair": "matched_name_position_season",
        "repair_classification": "already_matched",
        "season": label["expected_cfbd_feature_season"],
        "cfbd_player_id": player_id,
        "team": "Test State",
        "conference": "Test",
        "receiving_yards": receiving_yards,
        "receiving_tds": "8",
        "receptions": "65",
        "receiving_yard_share": "0.30",
        "reception_share": "0.26",
        "receiving_td_share": "0.25",
        "source_safety": "cfbd_factual_regular_season_only",
        "promotion_status": "local_feature_cache_only",
        "production_allowed": "no",
    }


def season_feature(season: int, player_id: str, yards: str) -> dict[str, object]:
    return {
        "season": str(season),
        "cfbd_player_id": player_id,
        "player_name": "Synthetic WR",
        "normalized_player_name": "syntheticwr",
        "team": "Test State",
        "conference": "Test",
        "position": "WR",
        "receiving_yards": yards,
        "receiving_tds": "8",
        "receptions": "65",
        "receiving_yard_share": "0.30",
        "reception_share": "0.26",
        "receiving_td_share": "0.25",
        "source_safety": "cfbd_factual_regular_season_only",
        "promotion_status": "local_feature_cache_only",
        "production_allowed": "no",
    }


def test_wr_feature_quality_pass_exports() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        labels = []
        joins = []
        seasons = []
        for year in range(2010, 2024):
            for idx, pos in enumerate(["WR", "RB", "QB", "WR"], start=1):
                player_id = f"{year}{idx}"
                label = label_row(idx, year, pos, player_id)
                labels.append(label)
                joins.append(join_row(label, player_id, "950" if pos == "WR" and idx == 1 else "250"))
                if pos == "WR":
                    seasons.append(season_feature(year - 1, player_id, "950" if idx == 1 else "250"))
                    seasons.append(season_feature(year - 2, player_id, "700" if idx == 1 else "150"))
        labels_path = root / "labels.csv"
        join_path = root / "join.csv"
        seasons_path = root / "seasons.csv"
        seasons_2009_path = root / "seasons_2009.csv"
        current_path = root / "current.csv"
        output_dir = root / "exports"
        write_csv(labels_path, labels)
        write_csv(join_path, joins)
        write_csv(seasons_path, seasons)
        write_csv(seasons_2009_path, [])
        write_csv(current_path, [{"player_name": "Current WR", "position": "WR"}])

        result = build_exports(labels_path, join_path, seasons_path, seasons_2009_path, current_path, output_dir)
        features = read_csv(output_dir / "wr_feature_table_historical_20260615.csv")
        decisions = read_csv(output_dir / "wr_feature_candidate_decision_20260615.csv")

        assert result["wr_features"]
        assert any(row["wr_feature_status"] == "wr_features_ready" for row in features)
        assert any(row["candidate_name"] == "wr_feature_enhanced_conservative" for row in decisions)
        assert (output_dir / "wr_feature_baseline_comparison_20260615.csv").exists()
        assert (output_dir / "README_WR_FEATURE_QUALITY_IMPROVEMENT_PASS_20260615.md").exists()


if __name__ == "__main__":
    test_wr_feature_quality_pass_exports()
    print("rookie_wr_feature_quality_pass_20260615 direct harness passed")
