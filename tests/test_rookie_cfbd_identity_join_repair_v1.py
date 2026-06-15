import csv
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.rookie_framework.audit_rookie_cfbd_identity_join_repair_v1 import (  # noqa: E402
    build_exports,
)


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if columns is None:
        columns = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_identity_join_repair_uses_2009_cache_and_flags_position_mismatch() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        base = root / "base"
        out = root / "out"
        base_columns = [
            "historical_label_key",
            "draft_year",
            "expected_cfbd_feature_season",
            "player_name",
            "normalized_player_name",
            "position",
            "college",
            "draft_round",
            "overall_pick",
            "label_status",
            "backtest_ready",
            "partial_window_only",
            "cfbd_join_status",
        ]
        write_csv(
            base / "cfbd_drafted_rookie_feature_join_v1_20260615.csv",
            [
                {
                    "historical_label_key": "expanded:2010:alpharunner:RB:1",
                    "draft_year": "2010",
                    "expected_cfbd_feature_season": "2009",
                    "player_name": "Alpha Runner",
                    "normalized_player_name": "alpharunner",
                    "position": "RB",
                    "college": "Oklahoma",
                    "draft_round": "1",
                    "overall_pick": "1",
                    "cfbd_join_status": "blocked_expected_season_outside_cache",
                },
                {
                    "historical_label_key": "expanded:2011:jordantight:TE:1",
                    "draft_year": "2011",
                    "expected_cfbd_feature_season": "2010",
                    "player_name": "Jordan Tight",
                    "normalized_player_name": "jordantight",
                    "position": "TE",
                    "college": "USC",
                    "draft_round": "1",
                    "overall_pick": "1",
                    "cfbd_join_status": "unmatched_name_position_season",
                },
            ],
            base_columns,
        )
        write_csv(
            base / "cfbd_player_season_features_v1_20260615.csv",
            [
                {
                    "season": "2010",
                    "cfbd_player_id": "2",
                    "player_name": "Jordan Tight",
                    "normalized_player_name": "jordantight",
                    "team": "USC",
                    "conference": "Pac-10",
                    "position": "WR",
                    "receiving_yards": "300",
                    "source_safety": "cfbd_factual_regular_season_only",
                    "promotion_status": "local_feature_cache_only",
                    "production_allowed": "no",
                }
            ],
        )
        raw = out / "raw_cfbd_2009_csv"
        write_csv(
            raw / "player_stats_season_2009_regular_rushing.csv",
            [
                {
                    "season": "2009",
                    "playerId": "1",
                    "player": "Alpha Runner",
                    "team": "Oklahoma",
                    "conference": "Big 12",
                    "position": "RB",
                    "category": "rushing",
                    "statType": "YDS",
                    "stat": "1000",
                }
            ],
        )
        write_csv(raw / "player_stats_season_2009_regular_passing.csv", [])
        write_csv(raw / "player_stats_season_2009_regular_receiving.csv", [])
        write_csv(
            raw / "team_stats_season_2009_regular.csv",
            [
                {"season": "2009", "team": "Oklahoma", "conference": "Big 12", "statName": "rushingYards", "statValue": "5000"}
            ],
        )

        counts = build_exports(out, base_cache=base, fetch_2009=False)
        repaired = read_csv(out / "cfbd_drafted_rookie_feature_join_repaired_20260615.csv")

        assert counts["after_matched_rows"] == 2
        assert any(row["cfbd_join_status_after_repair"] == "matched_exact_after_repair" for row in repaired)
        assert any(row["cfbd_join_status_after_repair"] == "matched_position_mismatch_repaired" for row in repaired)
        assert all(row["production_allowed"] == "no" for row in repaired)


if __name__ == "__main__":
    test_identity_join_repair_uses_2009_cache_and_flags_position_mismatch()
    print("rookie_cfbd_identity_join_repair_v1 direct harness passed")
