from __future__ import annotations

import csv
import json
from pathlib import Path

from src.services.draft_state_service import create_empty_draft_state
from src.services.mock_draft_simulator_service import build_review_mock_draft_scenario
from src.services.mock_draft_snapshot_service import (
    load_mock_draft_input_snapshot,
    review_available_player_rows_from_snapshot,
    simulator_pick_rows_from_snapshot,
    snapshot_audit_summary,
)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _snapshot_root(tmp_path: Path) -> Path:
    root = tmp_path / "lve_rosters_061326"
    root.mkdir()
    manifest = {
        "review_only": True,
        "roster_rows": 2,
        "draft_pick_rows": 4,
        "free_agent_rows": 2,
        "declared_drop_rows": 3,
        "declared_drop_unique_players": 2,
        "duplicate_declared_drops": {"brockpurdy": 2},
        "guardrails": ["local_exports_only", "adp_market_not_nwr_quality"],
    }
    (root / "extraction_manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )
    _write_csv(
        root / "roster_rows_normalized_review.csv",
        [
            {
                "team_name": "Niners",
                "manager": "Tim Pounders",
                "player_name": "Brian Thomas",
                "position": "WR",
                "nfl_team": "JAC",
                "overall_rank": 66,
                "input_status": "pdf_table_extraction_review_required",
            },
            {
                "team_name": "WhoDat?",
                "manager": "Thomas Ackeret",
                "player_name": "Brock Purdy",
                "position": "QB",
                "nfl_team": "SF",
                "overall_rank": 90,
                "input_status": "pdf_table_extraction_review_required",
            },
        ],
    )
    _write_csv(
        root / "draft_pick_rows_normalized_review.csv",
        [
            {
                "current_owner": "Niners",
                "manager": "Mike Colety",
                "pick_label": "1.03",
                "season": "2026",
                "round_text": "1st Round",
                "asset_type": "DP",
                "original_owner": "Golden Boy Productions",
                "is_niners_pick": "True",
                "input_status": "pdf_table_extraction_review_required",
            },
            {
                "current_owner": "Niners",
                "manager": "Mike Colety",
                "pick_label": "5.04",
                "season": "2026",
                "round_text": "5th Round",
                "asset_type": "DP",
                "original_owner": "Niners",
                "is_niners_pick": "True",
                "input_status": "pdf_table_extraction_review_required",
            },
            {
                "current_owner": "Other",
                "manager": "Other",
                "pick_label": "1.01",
                "season": "2026",
                "round_text": "1st Round",
                "asset_type": "DP",
                "original_owner": "Other",
                "is_niners_pick": "False",
                "input_status": "pdf_table_extraction_review_required",
            },
            {
                "current_owner": "Niners",
                "manager": "Mike Colety",
                "pick_label": "1.00",
                "season": "2027",
                "round_text": "1st Round",
                "asset_type": "DP",
                "original_owner": "Mighty Canucks",
                "is_niners_pick": "True",
                "input_status": "pdf_table_extraction_review_required",
            },
        ],
    )
    _write_csv(
        root / "free_agent_rows_normalized_review.csv",
        [
            {
                "player_name": "Tyreek Hill",
                "nfl_team": "MIA",
                "position": "WR",
                "overall_rank": 115,
                "position_rank": 48,
                "input_status": "pdf_table_extraction_review_required",
            },
            {
                "player_name": "Dallas Goedert",
                "nfl_team": "PHI",
                "position": "TE",
                "overall_rank": 116,
                "position_rank": 12,
                "input_status": "pdf_table_extraction_review_required",
            },
        ],
    )
    _write_csv(
        root / "declared_top_five_drops_20260616.csv",
        [
            {
                "declared_drop_sequence": 1,
                "player_name": "Brock Purdy",
                "normalized_player_key": "brockpurdy",
                "duplicate_declared_count": 2,
                "duplicate_instance": 1,
                "matched_roster_team": "WhoDat?",
                "matched_roster_manager": "Thomas Ackeret",
                "matched_position": "QB",
                "matched_nfl_team": "SF",
                "matched_overall_rank": 90,
                "matched_free_agent": "False",
                "input_status": "manual_declared_top_five_drop_review_required",
            },
            {
                "declared_drop_sequence": 2,
                "player_name": "Brock Purdy",
                "normalized_player_key": "brockpurdy",
                "duplicate_declared_count": 2,
                "duplicate_instance": 2,
                "matched_roster_team": "WhoDat?",
                "matched_roster_manager": "Thomas Ackeret",
                "matched_position": "QB",
                "matched_nfl_team": "SF",
                "matched_overall_rank": 90,
                "matched_free_agent": "False",
                "input_status": "manual_declared_top_five_drop_review_required",
            },
            {
                "declared_drop_sequence": 3,
                "player_name": "Brian Thomas",
                "normalized_player_key": "brianthomas",
                "duplicate_declared_count": 1,
                "duplicate_instance": 1,
                "matched_roster_team": "Niners",
                "matched_roster_manager": "Tim Pounders",
                "matched_position": "WR",
                "matched_nfl_team": "JAC",
                "matched_overall_rank": 66,
                "matched_free_agent": "False",
                "input_status": "manual_declared_top_five_drop_review_required",
            },
        ],
    )
    return root


def test_snapshot_loader_preserves_duplicate_declared_drops_and_review_warnings(tmp_path) -> None:
    snapshot = load_mock_draft_input_snapshot(_snapshot_root(tmp_path))

    assert snapshot.duplicate_declared_drop_counts == {"brockpurdy": 2}
    assert any("brockpurdy x2" in warning for warning in snapshot.review_warnings)
    assert any("future placeholder pick rows" in warning for warning in snapshot.review_warnings)


def test_snapshot_builds_2026_simulator_picks_and_flags_future_placeholders(tmp_path) -> None:
    snapshot = load_mock_draft_input_snapshot(_snapshot_root(tmp_path))

    rows = simulator_pick_rows_from_snapshot(snapshot)
    summary = snapshot_audit_summary(snapshot)

    assert [row["pick_label"] for row in rows] == ["1.01", "1.03", "5.04"]
    assert [row["pick_label"] for row in rows if row["is_my_pick"]] == ["1.03", "5.04"]
    assert "1.00" not in {row["pick_label"] for row in rows}
    assert summary["future_placeholder_pick_rows"] == 1


def test_snapshot_available_rows_do_not_treat_pdf_rank_as_nwr_quality(tmp_path) -> None:
    snapshot = load_mock_draft_input_snapshot(_snapshot_root(tmp_path))

    rows = review_available_player_rows_from_snapshot(snapshot)
    brock_rows = [row for row in rows if row["player"] == "Brock Purdy"]

    assert len(brock_rows) == 2
    assert {row["asset_id"] for row in brock_rows} == {
        "declared_drop:brockpurdy:seq1:instance1",
        "declared_drop:brockpurdy:seq2:instance2",
    }
    assert all(row["stats_model_value"] == 0.0 for row in rows)
    assert all(row["nwr_score_status"] == "not_populated_from_snapshot_rank" for row in rows)
    assert rows[0]["player"] == "Brian Thomas"
    assert rows[0]["source_overall_rank"] == "66"


def test_snapshot_rows_can_feed_review_only_simulator_without_app_wiring(tmp_path) -> None:
    snapshot = load_mock_draft_input_snapshot(_snapshot_root(tmp_path))
    state = create_empty_draft_state(
        pick_rows=simulator_pick_rows_from_snapshot(snapshot),
        available_rows=review_available_player_rows_from_snapshot(snapshot),
    )

    scenario = build_review_mock_draft_scenario(
        state,
        market_context_rows=[
            {
                "asset_id": "free_agent:tyreekhill:row1",
                "player": "Tyreek Hill",
                "market_adp": 1.0,
                "stats_model_value": 99.0,
            }
        ],
    )

    assert scenario.review_only is True
    assert scenario.simulated_picks[0].player == "Tyreek Hill"
    assert scenario.simulated_picks[0].stats_model_value == 0.0
    assert scenario.ending_current_pick == 3
    assert any("Ignored market context score/value fields" in row for row in scenario.warnings)
