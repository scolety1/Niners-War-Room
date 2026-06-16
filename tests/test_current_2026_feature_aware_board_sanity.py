import csv
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.rookie_framework.audit_current_2026_feature_aware_board_sanity import build_exports  # noqa: E402


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


def board_row(rank: int, name: str, position: str, matched: bool = True) -> dict[str, object]:
    return {
        "candidate_rank": str(rank),
        "candidate_position_rank": f"{position}{rank}",
        "rookie_rank": str(rank + 1),
        "rank_delta": "1",
        "player_id": f"prospect:2026:{name.lower().replace(' ', '')}:{position}",
        "player_name": name,
        "position": position,
        "school": "Test State",
        "status": "rankable_with_warning",
        "warning_flags": "manual=test_flag: manual_review_only" if rank == 1 else "none",
        "candidate_feature_aware_score": str(100 - rank),
        "candidate_production_component": "80",
        "candidate_market_share_component": "50",
        "candidate_cfbd_feature_status": "deterministic_joined" if matched else "unmatched_current_neutral",
        "candidate_safety_label": "rankable_with_visible_warnings",
        "candidate_cfbd_policy": "matched_source_safe_cfbd_context" if matched else "unmatched_neutral_cfbd_context_not_zero_filled_as_bad_production",
        "cfbd_current_join_status": "matched_name_position_school" if matched else "unmatched_current_identity",
        "cfbd_denominator_status": "denominator_ready" if matched else "not_available_unmatched",
        "cfbd_warning_flags": "none" if matched else "CFBD_UNMATCHED_CURRENT_IDENTITY",
    }


def test_board_sanity_exports() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        board_path = root / "board.csv"
        movement_path = root / "movement.csv"
        output_dir = root / "exports"
        rows = [board_row(i, f"Player {i}", "WR" if i % 2 else "RB") for i in range(1, 40)]
        rows.append(board_row(40, "Reggie Virgil", "WR", matched=False))
        write_csv(board_path, rows)
        write_csv(
            movement_path,
            [
                {
                    "player_name": "Reggie Virgil",
                    "movement_explanation": "fell because unmatched current CFBD row stayed neutral",
                }
            ],
        )

        result = build_exports(board_path, movement_path, output_dir)
        top12 = read_csv(output_dir / "current_2026_board_top12_20260615.csv")
        draft_sheet = read_csv(output_dir / "current_2026_clean_draft_use_sheet_20260615.csv")
        unmatched = read_csv(output_dir / "current_2026_unmatched_neutral_rows_20260615.csv")

        assert len(result["top36"]) == 36
        assert len(top12) == 12
        assert draft_sheet
        assert unmatched[0]["player_name"] == "Reggie Virgil"
        assert (output_dir / "README_CURRENT_2026_BOARD_SANITY_AUDIT_20260615.md").exists()


if __name__ == "__main__":
    test_board_sanity_exports()
    print("current_2026_feature_aware_board_sanity direct harness passed")
