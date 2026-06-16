import csv
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.rookie_framework.build_rookie_final_manual_draft_kit_20260615 import build_exports  # noqa: E402


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


def calibrated_row(rank: int, player: str, severity: str, action: str = "target") -> dict[str, object]:
    return {
        "model_rank": str(rank),
        "target_tier": "tier_1_priority_target" if rank == 1 else "tier_2_strong_consider",
        "draft_action": action,
        "trap_guard_severity": severity,
        "player": player,
        "position": "WR",
        "position_rank": f"WR{rank}",
        "primary_positive_reason": "strong profile",
        "primary_risk_or_warning": "risk note",
        "manual_question_for_tim": "Question?",
        "draft_room_note": "Use manually.",
        "candidate_model": "cfbd_enriched_baseline_v1_1",
    }


def source_row(player: str, joined: bool = True) -> dict[str, object]:
    return {
        "player_name": player,
        "candidate_cfbd_feature_status": "deterministic_joined" if joined else "unmatched_current_neutral",
        "cfbd_current_join_status": "matched_name_position_school" if joined else "unmatched_current_identity",
    }


def test_final_manual_draft_kit_freeze_exports() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        calibrated = root / "calibrated.csv"
        source = root / "source.csv"
        output_dir = root / "exports"
        write_csv(
            calibrated,
            [
                calibrated_row(1, "Target Player", "none"),
                calibrated_row(2, "Manual Player", "manual_review", "consider_at_value"),
                calibrated_row(3, "Critical Player", "critical_trap_guard", "manual_hold"),
            ],
        )
        write_csv(
            source,
            [
                source_row("Target Player"),
                source_row("Manual Player"),
                source_row("Critical Player", joined=False),
            ],
        )

        result = build_exports(calibrated, source, output_dir)
        board = read_csv(output_dir / "rookie_2026_final_manual_draft_board_frozen_20260615.csv")
        quick = read_csv(output_dir / "rookie_2026_draft_day_quick_sheet_20260615.csv")
        checklist = read_csv(output_dir / "rookie_2026_manual_decisions_checklist_20260615.csv")
        verdicts = read_csv(output_dir / "rookie_2026_final_manual_draft_kit_verdicts_20260615.csv")

        assert [row["rank"] for row in board] == ["1", "2", "3"]
        assert all(row["model_formula_version"] == "cfbd_enriched_baseline_v1_1" for row in board)
        assert board[2]["unmatched_neutral_feature_flag"] == "yes"
        assert len(quick) == 3
        assert len(checklist) == 2
        assert {row["verdict"]: row["status"] for row in verdicts}["board_order_changed"] == "NO"
        assert (output_dir / "rookie_2026_tier_cards_20260615.csv").exists()
        assert (output_dir / "rookie_2026_warning_priority_sheet_20260615.csv").exists()
        assert (output_dir / "README_ROOKIE_FINAL_MANUAL_DRAFT_KIT_20260615.md").exists()
        assert len(result["board"]) == 3


if __name__ == "__main__":
    test_final_manual_draft_kit_freeze_exports()
    print("rookie_final_manual_draft_kit direct harness passed")
