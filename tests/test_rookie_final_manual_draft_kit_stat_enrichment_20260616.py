import csv
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.rookie_framework.build_rookie_final_manual_draft_kit_stat_enrichment_20260616 import (  # noqa: E402
    ENRICHED_COLUMNS,
    build_exports,
)


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


def test_stat_enrichment_preserves_order_and_marks_missing_data() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        frozen_dir = root / "frozen"
        source = root / "source.csv"
        output = root / "exports"
        write_csv(
            frozen_dir / "rookie_2026_final_manual_draft_board_frozen_20260615.csv",
            [
                {
                    "rank": "1",
                    "tier": "tier_1_priority_target",
                    "player": "Target Player",
                    "position": "WR",
                    "position_rank": "WR1",
                    "draft_action": "target",
                    "warning_severity": "none",
                    "trap_caution_warning": "No specific draft-capital trap flag",
                    "main_positive_reason": "strong profile",
                    "main_risk_manual_question": "Old question",
                    "unmatched_neutral_feature_flag": "no",
                    "model_formula_version": "cfbd_enriched_baseline_v1_1",
                },
                {
                    "rank": "2",
                    "tier": "tier_2_strong_consider",
                    "player": "Trap Player",
                    "position": "RB",
                    "position_rank": "RB1",
                    "draft_action": "manual_hold",
                    "warning_severity": "critical_trap_guard",
                    "trap_caution_warning": "Critical trap guard",
                    "main_positive_reason": "strong profile",
                    "main_risk_manual_question": "Old question",
                    "unmatched_neutral_feature_flag": "no",
                    "model_formula_version": "cfbd_enriched_baseline_v1_1",
                },
            ],
        )
        write_csv(
            source,
            [
                {
                    "player_name": "Target Player",
                    "position": "WR",
                    "nfl_team": "SF",
                    "draft_capital": "round=2; pick=45",
                    "star_upside_index": "88",
                    "bust_risk_index": "55",
                    "rank_delta": "0",
                    "warning_flags": "manual=route_tree_grade_or_notes",
                    "bust_case": "gaps=injury_history_score",
                    "candidate_model": "cfbd_enriched_baseline_v1_1",
                },
                {
                    "player_name": "Trap Player",
                    "position": "RB",
                    "draft_capital": "",
                    "star_upside_index": "70",
                    "bust_risk_index": "95",
                    "rank_delta": "20",
                    "warning_flags": "soft_flags=SOURCE_LIMITED",
                    "candidate_model": "cfbd_enriched_baseline_v1_1",
                },
            ],
        )

        result = build_exports(frozen_dir, source, output)
        board = read_csv(output / "rookie_2026_final_manual_draft_board_stat_enriched_20260616.csv")
        missing = read_csv(output / "rookie_2026_missing_data_request_for_tim_20260616.csv")
        preview = output / "preview" / "index.html"

        assert list(board[0].keys())[: len(ENRICHED_COLUMNS)] == ENRICHED_COLUMNS
        assert [row["overall_rank"] for row in board] == ["1", "2"]
        assert board[0]["nfl_team"] == "SF"
        assert board[0]["age"] == "needs_data"
        assert board[0]["rookie_adp_or_market_rank"] == "needs_data"
        assert "target-earning path" in board[0]["manual_question"]
        assert "injury concern" not in board[0]["manual_question"]
        assert "draft capital/role" in board[1]["manual_question"]
        assert any(row["field"] == "age" for row in missing)
        assert preview.exists()
        assert len(result["board"]) == 2


if __name__ == "__main__":
    test_stat_enrichment_preserves_order_and_marks_missing_data()
    print("rookie_final_manual_draft_kit_stat_enrichment direct harness passed")
