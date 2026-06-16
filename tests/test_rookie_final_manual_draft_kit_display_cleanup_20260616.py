import csv
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.rookie_framework.build_rookie_final_manual_draft_kit_display_cleanup_20260616 import (  # noqa: E402
    build_display_cleanup,
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


def test_display_cleanup_keeps_order_and_removes_rank_tier_clutter() -> None:
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
                    "player": "Alpha WR",
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
                    "player": "Beta RB",
                    "position": "RB",
                    "position_rank": "RB1",
                    "draft_action": "consider_at_value",
                    "warning_severity": "manual_review",
                    "trap_caution_warning": "Manual review",
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
                    "player_name": "Alpha WR",
                    "position": "WR",
                    "nfl_team": "SF",
                    "draft_capital": "round=1; pick=8",
                    "star_upside_index": "92",
                    "bust_risk_index": "55",
                    "rank_delta": "0",
                    "candidate_model": "cfbd_enriched_baseline_v1_1",
                },
                {
                    "player_name": "Beta RB",
                    "position": "RB",
                    "nfl_team": "",
                    "draft_capital": "",
                    "star_upside_index": "75",
                    "bust_risk_index": "70",
                    "rank_delta": "0",
                    "candidate_model": "cfbd_enriched_baseline_v1_1",
                },
            ],
        )

        result = build_display_cleanup(frozen_dir, source, output)
        board = read_csv(output / "rookie_2026_final_manual_draft_board_display_cleanup_20260616.csv")
        guardrails = read_csv(output / "rookie_2026_display_cleanup_guardrails_20260616.csv")
        html = (output / "preview" / "index.html").read_text(encoding="utf-8")

        assert [row["Rank"] for row in board] == ["1", "2"]
        assert "tier" not in board[0]
        assert "overall_rank" not in board[0]
        assert "nwr_overall_ranking" not in board[0]
        assert "model_rank" not in board[0]
        assert list(board[0].keys())[:5] == ["Rank", "Player", "Pos", "NFL Team", "Depth Chart / Role"]
        assert board[1]["NFL Team"] == "needs_data"
        assert "Tier 1 - Priority Targets" in html
        assert "Tier 2 - Strong Considers" in html
        assert "visible_tier_column_removed" in {row["check"] for row in guardrails}
        assert any(row["check"] == "formula_changed" and row["status"] == "NO" for row in guardrails)
        assert len(result["display"]) == 2


if __name__ == "__main__":
    test_display_cleanup_keeps_order_and_removes_rank_tier_clutter()
    print("rookie_final_manual_draft_kit_display_cleanup direct harness passed")
