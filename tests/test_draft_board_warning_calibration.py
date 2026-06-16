import csv
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.rookie_framework.build_draft_board_warning_calibration import build_exports  # noqa: E402


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


def trap_row(rank: int, player: str, warning: str, reason: str, tier: str = "Tier 2 strong considers") -> dict[str, object]:
    return {
        "rank": str(rank),
        "position_rank": f"WR{rank}",
        "player": player,
        "position": "WR",
        "tier": tier,
        "draft_action": "consider",
        "trap_guard_warning": warning,
        "trap_guard_reason": reason,
        "main_positive_reason": "strong source-safe CFBD production profile",
        "main_risk_manual_question": "Review role?",
        "candidate_model": "cfbd_enriched_baseline_v1_1",
    }


def source_row(rank: int, player: str, draft_round: str, evidence: str = "72", bust: str = "60") -> dict[str, object]:
    return {
        "candidate_rank": str(rank),
        "player_name": player,
        "position": "WR",
        "status": "rankable_with_warning",
        "candidate_model": "cfbd_enriched_baseline_v1_1",
        "candidate_draft_round_used": draft_round,
        "candidate_cfbd_feature_status": "deterministic_joined",
        "candidate_production_component": "75",
        "candidate_market_share_component": "45",
        "evidence_confidence_index": evidence,
        "bust_risk_index": bust,
    }


def test_warning_calibration_keeps_rank_order_and_separates_views() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        trap = root / "trap.csv"
        source = root / "source.csv"
        focus = root / "focus.csv"
        unmatched = root / "unmatched.csv"
        output_dir = root / "exports"
        write_csv(
            trap,
            [
                trap_row(1, "Priority Player", "none", "", "Tier 1 priority targets"),
                trap_row(2, "Critical Player", "hard_manual_review", "high_bust_risk_index; no_standout_cfbd_production_or_share_edge"),
                trap_row(3, "Soft Player", "hard_manual_review", "very_late_overall_pick"),
            ],
        )
        write_csv(
            source,
            [
                source_row(1, "Priority Player", "1"),
                source_row(2, "Critical Player", "3", evidence="45", bust="95"),
                source_row(3, "Soft Player", "6", evidence="80", bust="40"),
            ],
        )
        write_csv(focus, [])
        write_csv(unmatched, [])

        result = build_exports(trap, source, focus, unmatched, output_dir)
        final_rows = read_csv(output_dir / "rookie_2026_final_manual_draft_board_warning_calibrated_20260615.csv")
        targets = read_csv(output_dir / "rookie_2026_top_model_targets_20260615.csv")
        warnings = read_csv(output_dir / "rookie_2026_highest_warning_priority_20260615.csv")
        verdicts = read_csv(output_dir / "rookie_2026_warning_calibration_verdicts_20260615.csv")

        assert [row["model_rank"] for row in final_rows] == ["1", "2", "3"]
        assert final_rows[0]["target_tier"] == "tier_1_priority_target"
        assert final_rows[0]["trap_guard_severity"] == "none"
        assert final_rows[1]["trap_guard_severity"] == "critical_trap_guard"
        assert targets[0]["player"] == "Priority Player"
        assert warnings[0]["player"] == "Critical Player"
        assert result["final_rows"][0]["board_order_changed"] == "no"
        assert {row["verdict"]: row["status"] for row in verdicts}["board_order_changed"] == "NO"
        assert (output_dir / "README_ROOKIE_DRAFT_BOARD_WARNING_CALIBRATION_20260615.md").exists()


if __name__ == "__main__":
    test_warning_calibration_keeps_rank_order_and_separates_views()
    print("draft_board_warning_calibration direct harness passed")
