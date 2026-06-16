import csv
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.rookie_framework.build_current_2026_top36_draft_decision_review import build_exports  # noqa: E402


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                columns.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def top36_row(rank: int, player: str, position: str, warning: str = "warnings visible; no extra audit flag") -> dict[str, str]:
    return {
        "candidate_rank": str(rank),
        "candidate_position_rank": f"{position}{rank}",
        "player_name": player,
        "position": position,
        "status": "rankable_with_warning",
        "manual_review_flag": warning,
        "feature_reason": "strong source-safe CFBD production profile",
    }


def test_top36_decision_review_exports() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        sanity_dir = root / "sanity"
        output_dir = root / "exports"
        top36_rows = [
            top36_row(1, "Jeremiyah Love", "RB", "manual evidence flags remain"),
            top36_row(2, "Makai Lemon", "WR", "source-limited profile"),
        ]
        top36_rows.extend(top36_row(rank, f"Player {rank}", "WR") for rank in range(3, 37))
        write_csv(sanity_dir / "current_2026_board_top36_20260615.csv", top36_rows)
        write_csv(
            sanity_dir / "current_2026_focus_player_sanity_20260615.csv",
            [
                {
                    "candidate_rank": "183",
                    "candidate_position_rank": "RB45",
                    "player_name": "Jam Miller",
                    "position": "RB",
                    "status": "unavailable",
                    "manual_review_flag": "status=unavailable; unmatched current CFBD identity",
                    "feature_reason": "neutral CFBD context because current identity was unmatched",
                    "cfbd_join_status": "unmatched_current_identity",
                }
            ],
        )
        write_csv(sanity_dir / "current_2026_unmatched_neutral_rows_20260615.csv", [])

        result = build_exports(sanity_dir, output_dir)
        top36 = read_csv(output_dir / "top36_draft_decision_review_20260615.csv")
        draft_sheet = read_csv(output_dir / "draft_day_decision_sheet_20260615.csv")
        focus = read_csv(output_dir / "focus_player_decision_review_20260615.csv")
        verdicts = read_csv(output_dir / "decision_review_verdicts_20260615.csv")

        assert len(result["top36"]) == 36
        assert len(top36) == 36
        assert draft_sheet[0]["production_allowed"] == "no"
        assert draft_sheet[0]["promotion_status"] == "local_manual_review_only"
        assert focus[0]["player"] == "Jam Miller"
        assert focus[0]["model_clearance"] == "not_model_cleared"
        assert {row["verdict"]: row["status"] for row in verdicts}["anti_cheat_leakage"] == "GREEN"
        assert (output_dir / "README_CURRENT_2026_TOP36_DRAFT_DECISION_REVIEW_20260615.md").exists()


if __name__ == "__main__":
    test_top36_decision_review_exports()
    print("current_2026_top36_draft_decision_review direct harness passed")
