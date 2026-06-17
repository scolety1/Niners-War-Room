import csv
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.rookie_framework.build_rookie_final_post_fill_runway_20260616 import (  # noqa: E402
    MOCK_DRAFT_COLUMNS,
    build_runway,
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


def test_final_post_fill_runway_builds_safe_handoff_outputs() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        input_dir = root / "input"
        cleanup_dir = root / "cleanup"
        output_dir = root / "output"
        write_csv(
            input_dir / "rookie_2026_final_manual_draft_board_display_cleanup_data_filled_20260616.csv",
            [
                {
                    "Rank": "1",
                    "Player": "Alpha WR",
                    "Pos": "WR",
                    "NFL Team": "SF",
                    "Depth Chart / Role": "needs_data: nfl_depth_chart_target_earning_role",
                    "Age": "22.5",
                    "NFL Draft Capital": "round=1; pick=8",
                    "ADP / Market": "Rookie ADP rank 1; ADP 1.2; source=Rookie ADP",
                    "Upside": "score=90.0; band=elite",
                    "Bust Risk": "score=50.0; band=lower",
                    "Draft Action": "target",
                    "Warning Severity": "none",
                    "Main Positive Reason": "strong profile",
                    "Main Risk": "needs_data",
                    "Manual Question": "Does Alpha WR have a target path?",
                },
                {
                    "Rank": "2",
                    "Player": "Beta RB",
                    "Pos": "RB",
                    "NFL Team": "needs_data",
                    "Depth Chart / Role": "needs_data: nfl_depth_chart_rush_goal_line_first_down_role",
                    "Age": "needs_data",
                    "NFL Draft Capital": "round=4; pick=120",
                    "ADP / Market": "needs_data",
                    "Upside": "score=70.0; band=solid",
                    "Bust Risk": "score=75.0; band=high",
                    "Draft Action": "manual_hold",
                    "Warning Severity": "manual_review",
                    "Main Positive Reason": "profile",
                    "Main Risk": "manual review",
                    "Manual Question": "Does Beta RB have role?",
                },
            ],
        )
        write_csv(
            input_dir / "rookie_2026_display_data_fill_guardrails_20260616.csv",
            [
                {"check": "board_order_changed", "status": "NO"},
                {"check": "formula_changed", "status": "NO"},
                {"check": "adp_market_display_only", "status": "YES"},
                {"check": "production_allowed", "status": "NO"},
            ],
        )
        write_csv(
            cleanup_dir / "rookie_2026_tier_summary_display_cleanup_20260616.csv",
            [
                {"Tier": "Tier 1 - Priority Targets", "Player Count": "1", "Players": "Alpha WR"},
                {"Tier": "Tier 2 - Strong Considers", "Player Count": "1", "Players": "Beta RB"},
            ],
        )

        result = build_runway(input_dir, cleanup_dir, output_dir)
        mock_rows = read_csv(output_dir / "rookie_2026_mock_draft_input_20260616.csv")
        qa = read_csv(output_dir / "rookie_2026_post_fill_qa_20260616.csv")
        phases = read_csv(output_dir / "rookie_2026_post_fill_phase_completion_20260616.csv")
        adp_template = read_csv(output_dir / "missing_data_templates" / "rookie_missing_adp_market_template_20260616.csv")
        html = (output_dir / "preview" / "index.html").read_text(encoding="utf-8")

        assert [row["rookie_rank"] for row in mock_rows] == ["1", "2"]
        assert list(mock_rows[0].keys()) == MOCK_DRAFT_COLUMNS
        assert mock_rows[0]["formula_name"] == "cfbd_enriched_baseline_v1_1"
        assert mock_rows[0]["board_order_frozen"] == "yes"
        assert mock_rows[0]["adp_market_rank"].startswith("Rookie ADP rank 1")
        assert mock_rows[1]["rookie_source_status"].startswith("needs_data:")
        assert all(row["status"] == "PASS" for row in qa)
        assert len(phases) == 5
        assert len(adp_template) == 1
        assert adp_template[0]["player_name"] == "Beta RB"
        assert "Tier 1 - Priority Targets" in html
        assert "Tier 2 - Strong Considers" in html
        assert result["mock_input"].exists()
        assert result["latest"].exists()


if __name__ == "__main__":
    test_final_post_fill_runway_builds_safe_handoff_outputs()
    print("rookie_final_post_fill_runway direct harness passed")
