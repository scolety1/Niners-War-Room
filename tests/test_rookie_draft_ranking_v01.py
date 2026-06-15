from __future__ import annotations

import csv
import importlib.util
import tempfile
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "rookie_framework" / "build_rookie_draft_ranking_v01.py"
spec = importlib.util.spec_from_file_location("build_rookie_draft_ranking_v01", SCRIPT_PATH)
ranking = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(ranking)


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


ANALYZER_FIELDS = [
    "analyzer_rank",
    "analyzer_group",
    "player_id",
    "player",
    "position",
    "school",
    "pick_zone",
    "production_ready_status",
    "tag_summary",
    "source_confidence",
    "warnings",
    "blockers",
    "evidence_summary",
    "remaining_gaps",
    "draft_only_if",
    "do_not_draft_if",
    "why_ranked_here",
]

FEATURE_FIELDS = [
    "player_id",
    "player_name",
    "position",
    "school",
    "nfl_team",
    "nfl_draft_round",
    "nfl_draft_pick",
    "final_year_target_share",
    "final_year_target_share_field_status",
    "final_year_touch_share",
    "final_year_touch_share_field_status",
    "cfbd_rushing_yards",
    "cfbd_rushing_yards_field_status",
    "cfbd_receiving_yards",
    "cfbd_receiving_yards_field_status",
    "cfbd_rushing_tds",
    "cfbd_rushing_tds_field_status",
    "cfbd_receiving_tds",
    "cfbd_receiving_tds_field_status",
]


def make_fixture(root: Path) -> tuple[Path, Path, Path]:
    analyzer_rows = [
        {
            "analyzer_rank": "1",
            "analyzer_group": "premium_review",
            "player_id": "p1",
            "player": "Alpha Back",
            "position": "RB",
            "school": "State",
            "pick_zone": "1.04",
            "production_ready_status": "rankable_with_warning",
            "tag_summary": "RB_PREMIUM_THREE_DOWN|RB_RECEIVING_BACK",
            "source_confidence": "high",
            "warnings": "pass_protection_grade_or_notes: manual_review_only",
            "blockers": "none",
            "evidence_summary": "official stats",
            "remaining_gaps": "pass_protection_grade_or_notes",
            "draft_only_if": "warnings acceptable",
            "do_not_draft_if": "warnings hidden",
            "why_ranked_here": "source-safe evidence",
        },
        {
            "analyzer_rank": "2",
            "analyzer_group": "blocked",
            "player_id": "p2",
            "player": "Beta Passer",
            "position": "QB",
            "school": "Tech",
            "pick_zone": "5.04",
            "production_ready_status": "blocked",
            "tag_summary": "QB_EXCEPTION",
            "source_confidence": "low",
            "warnings": "low_source_confidence",
            "blockers": "hard_caps=non-rushing QB in 1QB",
            "evidence_summary": "manual context",
            "remaining_gaps": "designed_rush_share",
            "draft_only_if": "exception cleared",
            "do_not_draft_if": "1QB cap remains",
            "why_ranked_here": "blocked",
        },
    ]
    feature_rows = [
        {
            "player_id": "p1",
            "player_name": "Alpha Back",
            "position": "RB",
            "school": "State",
            "nfl_team": "SF",
            "nfl_draft_round": "2",
            "nfl_draft_pick": "45",
            "final_year_target_share": "0.12",
            "final_year_target_share_field_status": "use_as_soft_flag",
            "final_year_touch_share": "0.28",
            "final_year_touch_share_field_status": "use_as_soft_flag",
            "cfbd_rushing_yards": "1100",
            "cfbd_rushing_yards_field_status": "use_now",
            "cfbd_receiving_yards": "260",
            "cfbd_receiving_yards_field_status": "use_now",
            "cfbd_rushing_tds": "12",
            "cfbd_rushing_tds_field_status": "use_now",
            "cfbd_receiving_tds": "2",
            "cfbd_receiving_tds_field_status": "use_now",
        },
        {
            "player_id": "p2",
            "player_name": "Beta Passer",
            "position": "QB",
            "school": "Tech",
            "nfl_team": "NYJ",
            "nfl_draft_round": "1",
            "nfl_draft_pick": "12",
            "final_year_target_share": "",
            "final_year_target_share_field_status": "",
            "final_year_touch_share": "",
            "final_year_touch_share_field_status": "",
            "cfbd_rushing_yards": "20",
            "cfbd_rushing_yards_field_status": "use_now",
            "cfbd_receiving_yards": "0",
            "cfbd_receiving_yards_field_status": "use_now",
            "cfbd_rushing_tds": "0",
            "cfbd_rushing_tds_field_status": "use_now",
            "cfbd_receiving_tds": "0",
            "cfbd_receiving_tds_field_status": "use_now",
        },
    ]
    analyzer_path = root / "analyzer.csv"
    feature_path = root / "features.csv"
    output_dir = root / "out"
    write_csv(analyzer_path, analyzer_rows, ANALYZER_FIELDS)
    write_csv(feature_path, feature_rows, FEATURE_FIELDS)
    return analyzer_path, feature_path, output_dir


def test_ranking_export_orders_star_before_blocked_qb_and_writes_overlay() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        analyzer_path, feature_path, output_dir = make_fixture(Path(tmp))
        ranking.build_exports(analyzer_path, feature_path, output_dir)
        rows = read_csv(output_dir / "rookie_draft_ranking_v1_20260615.csv")
        assert rows[0]["player_name"] == "Alpha Back"
        assert rows[0]["draft_action"] == "draft_candidate_with_visible_warnings"
        assert rows[1]["draft_action"] == "do_not_draft"
        assert rows[0]["market_overlay_status"] == "schema_only_no_player_level_market_source_loaded"
        assert "ADP/market excluded from score" in rows[0]["ranking_component_summary"]
        assert (output_dir / "rookie_market_overlay_v1_20260615.csv").exists()


def test_warning_rows_keep_visible_warnings() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        analyzer_path, feature_path, output_dir = make_fixture(Path(tmp))
        ranking.build_exports(analyzer_path, feature_path, output_dir)
        rows = read_csv(output_dir / "rookie_draft_ranking_v1_20260615.csv")
        warning_rows = [row for row in rows if row["status"] == "rankable_with_warning"]
        assert warning_rows
        assert all(row["warning_flags"] for row in warning_rows)


if __name__ == "__main__":
    test_ranking_export_orders_star_before_blocked_qb_and_writes_overlay()
    test_warning_rows_keep_visible_warnings()
