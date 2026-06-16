import csv
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.rookie_framework.build_current_2026_cfbd_feature_ingestion import build_exports  # noqa: E402


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


def raw_player_row(season: int, player: str, player_id: str, team: str, position: str, category: str, stat_type: str, stat: str) -> dict[str, object]:
    return {
        "season": str(season),
        "playerId": player_id,
        "player": player,
        "team": team,
        "conference": "Test",
        "position": position,
        "category": category,
        "statType": stat_type,
        "stat": stat,
    }


def raw_team_row(season: int, team: str, stat_name: str, stat_value: str) -> dict[str, object]:
    return {
        "season": str(season),
        "team": team,
        "conference": "Test",
        "statName": stat_name,
        "statValue": stat_value,
    }


def test_current_2026_cfbd_feature_ingestion_cache_only() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        output_dir = root / "exports"
        current_board = root / "board.csv"
        write_csv(
            current_board,
            [
                {
                    "rookie_rank": "1",
                    "player_id": "prospect:2026:testwr:WR",
                    "player_name": "Test WR",
                    "normalized_name": "testwr",
                    "position": "WR",
                    "school": "Test State",
                    "draft_capital": "round=2.0; pick=20.0",
                    "warning_flags": "SOURCE_LIMITED",
                },
                {
                    "rookie_rank": "2",
                    "player_id": "prospect:2026:testrb:RB",
                    "player_name": "Test RB",
                    "normalized_name": "testrb",
                    "position": "RB",
                    "school": "Test State",
                    "draft_capital": "round=3.0; pick=80.0",
                    "warning_flags": "none",
                },
            ],
        )
        for season in [2024, 2025]:
            write_csv(
                output_dir / "raw_cfbd_csv" / f"player_stats_season_{season}_regular_receiving.csv",
                [
                    raw_player_row(season, "Test WR", "1", "Test State", "WR", "receiving", "YDS", "900"),
                    raw_player_row(season, "Test WR", "1", "Test State", "WR", "receiving", "REC", "60"),
                    raw_player_row(season, "Test WR", "1", "Test State", "WR", "receiving", "TD", "8"),
                    raw_player_row(season, "Test RB", "2", "Test State", "RB", "receiving", "YDS", "200"),
                    raw_player_row(season, "Test RB", "2", "Test State", "RB", "receiving", "REC", "20"),
                ],
            )
            write_csv(
                output_dir / "raw_cfbd_csv" / f"player_stats_season_{season}_regular_rushing.csv",
                [raw_player_row(season, "Test RB", "2", "Test State", "RB", "rushing", "YDS", "1000")],
            )
            write_csv(
                output_dir / "raw_cfbd_csv" / f"player_stats_season_{season}_regular_passing.csv",
                [],
            )
            write_csv(
                output_dir / "raw_cfbd_csv" / f"team_stats_season_{season}_regular.csv",
                [
                    raw_team_row(season, "Test State", "netPassingYards", "3000"),
                    raw_team_row(season, "Test State", "passCompletions", "250"),
                    raw_team_row(season, "Test State", "passingTDs", "30"),
                    raw_team_row(season, "Test State", "rushingYards", "2200"),
                    raw_team_row(season, "Test State", "rushingAttempts", "450"),
                    raw_team_row(season, "Test State", "rushingTDs", "25"),
                ],
            )

        result = build_exports(output_dir=output_dir, current_board=current_board, skip_fetch=True)
        coverage = read_csv(output_dir / "current_2026_cfbd_feature_coverage_by_position_20260615.csv")
        wr_features = read_csv(output_dir / "current_2026_wr_feature_quality_table_20260615.csv")
        board = read_csv(output_dir / "current_2026_feature_ingested_manual_board_20260615.csv")

        assert len(result["joined"]) == 2
        assert any(row["position"] == "WR" and row["matched_rows"] == "1" for row in coverage)
        assert wr_features[0]["wr_feature_signal_score"] != ""
        assert board[0]["rookie_rank"] == "1"
        assert board[0]["cfbd_current_join_status"].startswith("matched")


if __name__ == "__main__":
    test_current_2026_cfbd_feature_ingestion_cache_only()
    print("current_2026_cfbd_feature_ingestion direct harness passed")
