import csv
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.rookie_framework.build_current_2026_feature_aware_rescore_candidate import build_exports  # noqa: E402


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


def board_row(rank: int, name: str, position: str, status: str, matched: bool = True) -> dict[str, object]:
    return {
        "rookie_rank": str(rank),
        "player_id": f"prospect:2026:{name.lower().replace(' ', '')}:{position}",
        "player_name": name,
        "position": position,
        "school": "Test State",
        "draft_capital": f"round={rank}.0; pick={rank * 10}.0",
        "status": status,
        "warning_flags": "SOURCE_LIMITED",
        "final_rookie_rank_score": str(70 - rank),
        "cfbd_current_join_status": "matched_name_position_school" if matched else "unmatched_current_identity",
        "cfbd_denominator_status": "denominator_ready" if matched else "not_available_unmatched",
        "cfbd_warning_flags": "none" if matched else "CFBD_UNMATCHED_CURRENT_IDENTITY",
        "cfbd_rushing_yards": "1200" if position == "RB" and matched else "",
        "cfbd_rushing_tds": "12" if position == "RB" and matched else "",
        "cfbd_rushing_yard_share": "0.30" if position == "RB" and matched else "",
        "cfbd_rushing_td_share": "0.28" if position == "RB" and matched else "",
        "cfbd_receiving_yards": "1000" if position in {"WR", "TE"} and matched else "200" if position == "RB" and matched else "",
        "cfbd_receiving_tds": "8" if position in {"WR", "TE"} and matched else "",
        "cfbd_receptions": "70" if position in {"WR", "TE"} and matched else "20" if position == "RB" and matched else "",
        "cfbd_receiving_yard_share": "0.30" if position in {"WR", "TE"} and matched else "",
        "cfbd_reception_share": "0.25" if position in {"WR", "TE"} and matched else "0.08" if position == "RB" and matched else "",
        "cfbd_receiving_td_share": "0.22" if position in {"WR", "TE"} and matched else "",
    }


def test_feature_aware_rescore_candidate_exports() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        input_path = root / "board.csv"
        coverage_path = root / "coverage.csv"
        output_dir = root / "exports"
        write_csv(
            input_path,
            [
                board_row(1, "Test WR", "WR", "rankable_with_warning"),
                board_row(2, "Test RB", "RB", "rankable_with_warning"),
                board_row(3, "Missing WR", "WR", "rankable_with_warning", matched=False),
                board_row(4, "Blocked WR", "WR", "blocked"),
            ],
        )
        write_csv(
            coverage_path,
            [{"position": "WR", "current_rows": "3", "matched_rows": "2"}],
        )
        result = build_exports(input_path, coverage_path, output_dir)
        board = read_csv(output_dir / "current_2026_feature_aware_candidate_board_20260615.csv")
        unmatched = read_csv(output_dir / "current_2026_feature_aware_unmatched_policy_20260615.csv")
        movement = read_csv(output_dir / "current_2026_feature_aware_rank_movement_20260615.csv")

        assert len(result["candidate_rows"]) == 4
        assert board[0]["candidate_rank"] == "1"
        assert unmatched[0]["candidate_cfbd_policy"].startswith("unmatched_neutral")
        assert any(row["rank_delta"] for row in movement)
        assert (output_dir / "README_CURRENT_2026_FEATURE_AWARE_RESCORE_CANDIDATE_20260615.md").exists()


if __name__ == "__main__":
    test_feature_aware_rescore_candidate_exports()
    print("current_2026_feature_aware_rescore_candidate direct harness passed")
