import csv
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.rookie_framework.build_rookie_cfbd_historical_feature_cache_v1 import (  # noqa: E402
    build_exports,
    endpoint_cache_path,
    team_cache_path,
)


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


def test_cfbd_feature_cache_builds_features_and_time_safe_join() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        out = root / "out"
        labels = root / "labels.csv"
        write_csv(
            endpoint_cache_path(out, 2010, "rushing"),
            [
                {
                    "season": "2010",
                    "playerId": "1",
                    "player": "Alpha Runner",
                    "team": "Oklahoma",
                    "conference": "Big 12",
                    "position": "RB",
                    "category": "rushing",
                    "statType": "YDS",
                    "stat": "1000",
                },
                {
                    "season": "2010",
                    "playerId": "1",
                    "player": "Alpha Runner",
                    "team": "Oklahoma",
                    "conference": "Big 12",
                    "position": "RB",
                    "category": "rushing",
                    "statType": "CAR",
                    "stat": "200",
                },
            ],
        )
        write_csv(
            endpoint_cache_path(out, 2010, "receiving"),
            [
                {
                    "season": "2010",
                    "playerId": "1",
                    "player": "Alpha Runner",
                    "team": "Oklahoma",
                    "conference": "Big 12",
                    "position": "RB",
                    "category": "receiving",
                    "statType": "YDS",
                    "stat": "250",
                }
            ],
        )
        write_csv(endpoint_cache_path(out, 2010, "passing"), [])
        write_csv(
            team_cache_path(out, 2010),
            [
                {"season": "2010", "team": "Oklahoma", "conference": "Big 12", "statName": "rushingYards", "statValue": "5000"},
                {"season": "2010", "team": "Oklahoma", "conference": "Big 12", "statName": "rushingAttempts", "statValue": "800"},
                {"season": "2010", "team": "Oklahoma", "conference": "Big 12", "statName": "netPassingYards", "statValue": "4000"},
            ],
        )
        write_csv(
            labels,
            [
                {
                    "historical_label_key": "expanded:2011:alpharunner:RB:1",
                    "draft_year": "2011",
                    "player_name": "Alpha Runner",
                    "normalized_player_name": "alpharunner",
                    "position": "RB",
                    "college": "Oklahoma",
                    "draft_round": "1",
                    "overall_pick": "1",
                    "historical_label_status": "GREEN_COMPLETE",
                    "backtest_ready": "yes",
                    "partial_window_only": "no",
                },
                {
                    "historical_label_key": "expanded:2010:betarunner:RB:1",
                    "draft_year": "2010",
                    "player_name": "Beta Runner",
                    "normalized_player_name": "betarunner",
                    "position": "RB",
                    "college": "Oklahoma",
                    "draft_round": "1",
                    "overall_pick": "1",
                    "historical_label_status": "GREEN_COMPLETE",
                    "backtest_ready": "yes",
                    "partial_window_only": "no",
                },
            ],
        )
        counts = build_exports(out, labels, skip_fetch=True)
        features = read_csv(out / "cfbd_player_season_features_v1_20260615.csv")
        joined = read_csv(out / "cfbd_drafted_rookie_feature_join_v1_20260615.csv")

        assert counts["player_feature_rows"] == 1
        assert features[0]["rushing_yards"] == "1000.000"
        assert features[0]["rushing_yard_share"] == "0.200000"
        assert any(row["cfbd_join_status"] == "matched_name_position_season" for row in joined)
        assert any(row["cfbd_join_status"] == "blocked_expected_season_outside_cache" for row in joined)
        assert all(row["production_allowed"] == "no" for row in joined)
        assert all(row["promotion_status"] == "local_feature_cache_only" for row in joined)


if __name__ == "__main__":
    test_cfbd_feature_cache_builds_features_and_time_safe_join()
    print("rookie_cfbd_historical_feature_cache_v1 direct harness passed")
