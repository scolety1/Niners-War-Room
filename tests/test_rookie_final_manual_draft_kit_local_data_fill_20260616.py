import csv
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.rookie_framework.build_rookie_final_manual_draft_kit_local_data_fill_20260616 import (  # noqa: E402
    DISPLAY_COLUMNS,
    build_local_data_fill,
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


def test_local_data_fill_preserves_board_and_display_only_guards() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        cleanup = root / "cleanup"
        output = root / "output"
        fantasypros = root / "fantasypros.csv"
        rookie_adp = root / "rookie_adp.csv"
        identity = root / "identity.csv"
        age = root / "age.csv"

        write_csv(
            cleanup / "rookie_2026_final_manual_draft_board_display_cleanup_20260616.csv",
            [
                {
                    "Rank": "1",
                    "Player": "Alpha WR",
                    "Pos": "WR",
                    "NFL Team": "needs_data",
                    "Depth Chart / Role": "needs_data: nfl_depth_chart_target_earning_role",
                    "Age": "needs_data",
                    "NFL Draft Capital": "round=1; pick=8",
                    "ADP / Market": "needs_data",
                    "Upside": "score=90.0; band=elite",
                    "Bust Risk": "score=50.0; band=lower",
                    "Draft Action": "target",
                    "Warning Severity": "none",
                    "Main Positive Reason": "strong profile",
                    "Main Risk": "needs_data",
                    "Manual Question": "Does Alpha WR have a credible target-earning path?",
                },
                {
                    "Rank": "2",
                    "Player": "Beta RB",
                    "Pos": "RB",
                    "NFL Team": "needs_data",
                    "Depth Chart / Role": "needs_data: nfl_depth_chart_rush_goal_line_first_down_role",
                    "Age": "needs_data",
                    "NFL Draft Capital": "unavailable",
                    "ADP / Market": "needs_data",
                    "Upside": "score=70.0; band=solid",
                    "Bust Risk": "score=70.0; band=moderate",
                    "Draft Action": "manual_hold",
                    "Warning Severity": "manual_review",
                    "Main Positive Reason": "profile",
                    "Main Risk": "manual review",
                    "Manual Question": "Does Beta RB have role?",
                },
            ],
        )
        write_csv(
            cleanup / "rookie_2026_tier_summary_display_cleanup_20260616.csv",
            [
                {"Tier": "Tier 1 - Priority Targets", "Player Count": "1", "Players": "Alpha WR"},
                {"Tier": "Tier 2 - Strong Considers", "Player Count": "1", "Players": "Beta RB"},
            ],
        )
        write_csv(
            cleanup / "rookie_2026_display_cleanup_guardrails_20260616.csv",
            [
                {"check": "board_order_changed", "status": "NO"},
                {"check": "formula_changed", "status": "NO"},
            ],
        )
        write_csv(fantasypros, [{"source": "FantasyPros", "rank": "9", "player": "Beta RB", "position": "RB", "average_adp": "9.5"}])
        write_csv(rookie_adp, [{"source": "Rookie ADP", "player": "Alpha WR", "position": "WR", "adp": "1.2", "adp_rank": "1"}])
        write_csv(
            identity,
            [
                {
                    "prospect_name": "Alpha WR",
                    "position": "WR",
                    "nfl_team": "SF",
                    "formula_identity_admitted": "True",
                }
            ],
        )
        write_csv(
            age,
            [
                {
                    "player": "Alpha WR",
                    "position": "WR",
                    "age_years_decimal": "22.5000",
                    "allowed_use": "local_review_only",
                }
            ],
        )

        result = build_local_data_fill(cleanup, fantasypros, rookie_adp, identity, age, output)
        board = read_csv(output / "rookie_2026_final_manual_draft_board_display_cleanup_data_filled_20260616.csv")
        coverage = read_csv(output / "rookie_2026_display_data_fill_coverage_20260616.csv")
        guardrails = read_csv(output / "rookie_2026_display_data_fill_guardrails_20260616.csv")
        html = (output / "preview" / "index.html").read_text(encoding="utf-8")

        assert list(board[0].keys()) == DISPLAY_COLUMNS
        assert [row["Rank"] for row in board] == ["1", "2"]
        assert board[0]["NFL Team"] == "SF"
        assert board[0]["Age"] == "22.5"
        assert "Rookie ADP" in board[0]["ADP / Market"]
        assert "FantasyPros" in board[1]["ADP / Market"]
        assert board[1]["NFL Team"] == "needs_data"
        assert "Tier 1 - Priority Targets" in html
        assert "Tier 2 - Strong Considers" in html
        assert any(row["field"] == "ADP / Market" and row["populated_rows"] == "2" for row in coverage)
        assert any(row["check"] == "adp_market_display_only" and row["status"] == "YES" for row in guardrails)
        assert any(row["check"] == "formula_changed" and row["status"] == "NO" for row in guardrails)
        assert len(result["rows"]) == 2


if __name__ == "__main__":
    test_local_data_fill_preserves_board_and_display_only_guards()
    print("rookie_final_manual_draft_kit_local_data_fill direct harness passed")
