import csv
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.rookie_framework.build_draft_capital_trap_guard_overlay import build_exports  # noqa: E402


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


def board_row(rank: int, name: str, draft_round: str, evidence: str = "72", bust: str = "60") -> dict[str, object]:
    return {
        "candidate_rank": str(rank),
        "candidate_position_rank": f"WR{rank}",
        "player_name": name,
        "position": "WR",
        "status": "rankable_with_warning",
        "warning_flags": "soft_flags=SOURCE_LIMITED",
        "cfbd_warning_flags": "none",
        "candidate_model": "cfbd_enriched_baseline_v1_1",
        "candidate_draft_round_used": draft_round,
        "candidate_overall_pick_used": "180" if draft_round == "6" else "80",
        "candidate_cfbd_feature_status": "deterministic_joined",
        "candidate_production_component": "55",
        "candidate_market_share_component": "30",
        "evidence_confidence_index": evidence,
        "bust_risk_index": bust,
    }


def test_draft_capital_trap_guard_overlay_is_warning_only() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        board = root / "board.csv"
        decision = root / "decision.csv"
        output_dir = root / "exports"
        write_csv(
            board,
            [
                board_row(1, "Round One Player", "1"),
                board_row(2, "Round Three Player", "3", evidence="50", bust="80"),
                board_row(3, "Round Six Player", "6"),
                board_row(4, "Unknown Capital Player", ""),
            ],
        )
        write_csv(
            decision,
            [
                {
                    "player": "Round One Player",
                    "draft_action": "target",
                    "feature_reason": "strong profile",
                    "manual_question": "Review role?",
                }
            ],
        )
        result = build_exports(board, decision, output_dir)
        final_board = read_csv(output_dir / "draft_capital_trap_guard_final_draft_board_20260615.csv")
        flagged = read_csv(output_dir / "draft_capital_trap_guard_flagged_players_20260615.csv")
        verdicts = read_csv(output_dir / "draft_capital_trap_guard_verdicts_20260615.csv")

        assert [row["rank"] for row in final_board] == ["1", "2", "3", "4"]
        assert len(result["top54"]) == 4
        assert len(flagged) == 3
        assert all(row["production_allowed"] == "no" for row in final_board)
        assert all(row["promotion_status"] == "local_manual_overlay_only" for row in final_board)
        assert {row["verdict"]: row["status"] for row in verdicts}["main_ranking_formula_changed"] == "NO"
        assert (output_dir / "README_DRAFT_CAPITAL_TRAP_GUARD_OVERLAY_20260615.md").exists()


if __name__ == "__main__":
    test_draft_capital_trap_guard_overlay_is_warning_only()
    print("draft_capital_trap_guard_overlay direct harness passed")
