from __future__ import annotations

from pathlib import Path

from pytest import MonkeyPatch

import src.services.command_board_service as command_board_service
from src.data.validators import ValidatedDataPack
from src.services.command_board_service import (
    TEAM_COLUMN_LABELS,
    TEAM_DECISION_COLUMNS,
    TEAM_SECTION_ORDER,
    WAR_BOARD_COLUMN_LABELS,
    WAR_BOARD_DISPLAY_COLUMNS,
    build_import_review_board,
    build_team_command_board,
    build_war_board,
)

SAMPLE_PACK = "sample_data/2026_pre_declaration"


def test_import_review_board_exposes_validation_warnings_and_row_counts() -> None:
    board = build_import_review_board(SAMPLE_PACK)

    assert board.data_pack_name == "2026_pre_declaration"
    assert board.issue_counts["error"] == 0
    assert board.issue_counts["warning"] == 0
    assert {"table": "rosters", "rows": 24} in board.row_counts


def test_team_command_board_shows_niners_top_five_and_forced_release() -> None:
    board = build_team_command_board(SAMPLE_PACK)

    assert board.rules.protect_limit == 23
    assert board.rules.official_top_five_keep_limit == 4
    assert [row["player"] for row in board.top_five_rows] == [
        "De'Von Achane",
        "Lamar Jackson",
        "Chase Brown",
        "Luther Burden",
        "Brian Thomas",
    ]
    assert [row["player"] for row in board.forced_release_rows] == ["Luther Burden"]
    assert board.forced_release_rows[0]["top_five_rule"] == (
        "Required Top-Five Release Slot"
    )
    assert board.forced_release_rows[0]["model_recommendation"] == "shop/release"
    assert board.keeper_board.pressure.forced_release_count == 1


def test_team_command_board_roster_rows_include_keeper_drop_shop_actions() -> None:
    board = build_team_command_board(SAMPLE_PACK)
    recommendations = {row["recommendation"] for row in board.roster_rows}

    assert "keep" in recommendations
    assert "shop/release" in recommendations


def test_team_command_board_exposes_my_team_decision_sections_and_labels() -> None:
    board = build_team_command_board(SAMPLE_PACK)

    assert board.section_order == TEAM_SECTION_ORDER
    assert set(TEAM_DECISION_COLUMNS).issubset(board.roster_rows[0])
    assert TEAM_COLUMN_LABELS["keep_priority"] == "Keep Priority"
    assert TEAM_COLUMN_LABELS["cut_risk"] == "Cut Risk"
    assert TEAM_COLUMN_LABELS["stats_value"] == "Model Value"
    assert TEAM_COLUMN_LABELS["market_edge"] == "Model vs Market"
    forced_row = board.rows_by_section["Forced-Release Decision"][0]
    assert forced_row["player"] == "Luther Burden"
    assert forced_row["top_five_rule"] == "Required Top-Five Release Slot"
    assert forced_row["model_recommendation"] == "shop/release"
    assert forced_row["release_pain"] is not None
    assert "top-five" in str(forced_row["decision_explanation"])
    assert "non-top-five" not in str(forced_row["decision_explanation"]).lower()
    assert "easy" not in str(forced_row["decision_explanation"]).lower()
    assert "release_pain" in TEAM_DECISION_COLUMNS
    assert "decision_explanation" in TEAM_DECISION_COLUMNS
    assert TEAM_COLUMN_LABELS["release_pain"] == "Release Pain"
    assert all(
        row["top_five_rule"] == "Not in Roster's League-Rank Top Five"
        for row in board.roster_rows
        if row["league_rank"] not in {10, 31, 35, 56, 66}
    )


def test_team_command_board_forced_release_is_chosen_from_top_five_only() -> None:
    board = build_team_command_board(SAMPLE_PACK)

    top_five_players = {row["player"] for row in board.top_five_rows}
    forced_players = {row["player"] for row in board.forced_release_rows}

    assert forced_players
    assert forced_players.issubset(top_five_players)
    assert board.forced_release_rows[0]["player"] == "Luther Burden"
    assert board.forced_release_rows[0]["top_five_rule"] == (
        "Required Top-Five Release Slot"
    )
    forced_roster_row = board.rows_by_section["Forced-Release Decision"][0]
    assert "lowest Keep Priority" in str(
        forced_roster_row["decision_explanation"]
    )


def test_war_board_is_sorted_and_filter_metadata_is_available() -> None:
    board = build_war_board(SAMPLE_PACK)

    assert [row["player"] for row in board.rows[:2]] == [
        "De'Von Achane",
        "Lamar Jackson",
    ]
    assert [row["overall_rank"] for row in board.rows[:2]] == [1, 2]
    assert board.positions == ["QB", "RB", "TE", "WR"]
    assert board.teams == ["Niners"]
    assert board.actions == [
        "drop",
        "shop",
        "bubble",
        "risk",
        "hold",
        "keep",
    ]
    assert board.recommendations == [
        "bubble",
        "drop",
        "hold",
        "keep",
        "risk",
        "shop",
    ]
    assert "market close" in board.edge_types
    assert board.confidence_buckets == ["weak", "review", "usable", "strong"]


def test_war_board_exposes_decision_display_fields_and_labels() -> None:
    board = build_war_board(SAMPLE_PACK)
    row = board.rows[0]

    assert WAR_BOARD_DISPLAY_COLUMNS == (
        "overall_rank",
        "position_rank_label",
        "player",
        "pos",
        "asset_lifecycle_label",
        "team",
        "action",
        "stats_value",
        "market_value",
        "market_edge",
        "confidence",
        "confidence_label",
        "warning_reason",
    )
    assert WAR_BOARD_COLUMN_LABELS["stats_value"] == "Model Value"
    assert WAR_BOARD_COLUMN_LABELS["asset_lifecycle_label"] == "Lifecycle"
    assert WAR_BOARD_COLUMN_LABELS["team"] == "Fantasy Team"
    assert WAR_BOARD_COLUMN_LABELS["market_value"] == "Trade Market"
    assert WAR_BOARD_COLUMN_LABELS["market_edge"] == "Model vs Market"
    assert WAR_BOARD_COLUMN_LABELS["confidence_label"] == "Confidence Label"
    assert set(WAR_BOARD_DISPLAY_COLUMNS).issubset(row)
    assert row["overall_rank"] >= 1
    assert row["confidence_label"] in {"weak", "review", "usable", "strong"}
    assert str(row["position_rank_label"]).startswith(str(row["pos"]))
    assert "Model value" in str(row["why_ranked_here"])
    assert "_" not in str(row["warning_reason"])


def test_command_boards_hide_kickers_from_decision_surfaces(
    monkeypatch: MonkeyPatch,
) -> None:
    rows_by_table = {
        "rosters": [
            {
                "snapshot_date": "2026-pre-draft",
                "season": "2026",
                "team_id": "niners",
                "team_name": "Niners",
                "player_id": "rb_1",
                "player_name": "Useful Back",
                "position": "RB",
                "league_rank": "12",
            },
            {
                "snapshot_date": "2026-pre-draft",
                "season": "2026",
                "team_id": "niners",
                "team_name": "Niners",
                "player_id": "k_1",
                "player_name": "Ignored Kicker",
                "position": "K",
                "league_rank": "13",
            },
        ],
        "official_rankings": [],
        "model_outputs": [
            {
                "player_id": "rb_1",
                "player_name": "Useful Back",
                "position": "RB",
                "war_score": "80",
                "private_score": "80",
                "keeper_score": "82",
                "drop_candidate_score": "12",
                "confidence_score": "88",
                "risk_level": "low",
                "warning_status": "ready",
            },
            {
                "player_id": "k_1",
                "player_name": "Ignored Kicker",
                "position": "K",
                "war_score": "99",
                "private_score": "99",
                "keeper_score": "99",
                "drop_candidate_score": "0",
                "confidence_score": "100",
                "risk_level": "ignored_position",
                "warning_status": "excluded",
            },
        ],
    }
    monkeypatch.setattr(
        command_board_service,
        "validate_data_pack",
        lambda path: ValidatedDataPack(
            data_pack_path=Path(str(path)),
            data_pack_name="kicker-test",
            snapshot_date="2026-pre-draft",
            rows_by_table=rows_by_table,
            issues=(),
        ),
    )

    board = build_war_board("kicker-test")

    assert [row["player"] for row in board.rows] == ["Useful Back"]
    assert board.positions == ["RB"]


def test_war_board_excludes_stale_and_duplicate_identity_rows(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    empty_model_dir = tmp_path / "empty_active_model"
    empty_model_dir.mkdir()
    monkeypatch.setattr(
        command_board_service,
        "ACTIVE_STATS_FIRST_MODEL_DIR",
        empty_model_dir,
    )
    rows_by_table = {
        "players": [
            {
                "player_id": "keep_1",
                "player_name": "Clean Player",
                "position": "WR",
                "active_flag": "1",
            },
            {
                "player_id": "stale_1",
                "player_name": "Retired Player",
                "position": "RB",
                "active_flag": "0",
            },
            {
                "player_id": "dupe_1",
                "player_name": "Duplicate Player",
                "position": "TE",
                "active_flag": "1",
            },
        ],
        "rosters": [
            _roster_row("keep_1", "Clean Player", "WR"),
            _roster_row("stale_1", "Retired Player", "RB"),
            _roster_row("dupe_1", "Duplicate Player", "TE"),
            _roster_row("dupe_1", "Duplicate Player", "TE", team_id="other"),
        ],
        "official_rankings": [],
        "model_outputs": [
            _model_row("keep_1", "Clean Player", "WR", "70"),
            _model_row("stale_1", "Retired Player", "RB", "99"),
            _model_row("dupe_1", "Duplicate Player", "TE", "98"),
        ],
    }
    monkeypatch.setattr(
        command_board_service,
        "validate_data_pack",
        lambda path: ValidatedDataPack(
            data_pack_path=Path(str(path)),
            data_pack_name="identity-cleanup-test",
            snapshot_date="2026-pre-draft",
            rows_by_table=rows_by_table,
            issues=(),
        ),
    )

    board = build_war_board("identity-cleanup-test")

    assert [row["player"] for row in board.rows] == ["Clean Player"]


def test_war_board_prefers_active_stats_first_preview_matched_by_sleeper_id(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    model_dir = tmp_path / "active_model"
    model_dir.mkdir()
    (model_dir / "stats_first_normalized_features.csv").write_text(
        (
            "player_id,gsis_id,sleeper_id,player_name,position\n"
            "00-0037239,00-0037239,8144,Chris Olave,WR\n"
        ),
        encoding="utf-8",
    )
    (model_dir / "stats_first_veteran_model_preview_outputs.csv").write_text(
        (
            "player_id,player_name,position,overall_rank,position_rank,"
            "position_rank_label,private_lve_value,keeper_score,"
            "drop_candidate_score,trade_value,market_trade_value,"
            "market_edge_score,confidence_score,warning_status,warning_reasons,"
            "risk_flags,model_version,computed_at\n"
            "00-0037239,Chris Olave,WR,58,27,WR27,62.06,55.0,42.88,"
            "59.67,50.0,12.06,81.5,model_warning,injury_risk,"
            "keeper_bubble,stats_first_test,2026-05-10T20:15:14Z\n"
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(command_board_service, "ACTIVE_STATS_FIRST_MODEL_DIR", model_dir)
    rows_by_table = {
        "rosters": [
            {
                "snapshot_date": "2026-pre-draft",
                "season": "2026",
                "team_id": "niners",
                "team_name": "Niners",
                "player_id": "8144",
                "player_name": "Chris Olave",
                "position": "WR",
                "league_rank": "14",
            }
        ],
        "official_rankings": [],
        "model_outputs": [
            {
                "player_id": "8144",
                "player_name": "Chris Olave",
                "position": "WR",
                "overall_rank": "14",
                "position_rank_label": "WR14",
                "war_score": "91.33",
                "private_score": "92.26",
                "keeper_score": "91.33",
                "drop_candidate_score": "12",
                "confidence_score": "88",
                "warning_status": "ready",
            }
        ],
    }
    monkeypatch.setattr(
        command_board_service,
        "validate_data_pack",
        lambda path: ValidatedDataPack(
            data_pack_path=Path(str(path)),
            data_pack_name="stale-pack",
            snapshot_date="2026-pre-draft",
            rows_by_table=rows_by_table,
            issues=(),
        ),
    )

    board = build_war_board("stale-pack")

    assert board.rows[0]["player"] == "Chris Olave"
    assert board.rows[0]["overall_rank"] == 58
    assert board.rows[0]["position_rank_label"] == "WR27"
    assert board.rows[0]["stats_value"] == 62.06
    assert board.rows[0]["keeper_score"] == 55.0
    assert board.rows[0]["market_value_status"] == "neutral_market_placeholder"
    assert board.rows[0]["market_edge"] is None
    assert board.rows[0]["edge_type"] == "neutral market placeholder"
    assert board.rows[0]["warning_status"] == "model_warning"
    assert board.rows[0]["score_source"] == "active_stats_first_preview"
    assert board.rows[0]["identity_match_method"] == (
        "gsis_to_sleeper_from_normalized_features"
    )
    assert "active stats-first preview" in str(board.rows[0]["notes"])
    audit = board.data_source_audit_rows[0]
    assert audit["visible_score_source"] == "active_stats_first_preview"
    assert audit["active_stats_first_preview_timestamp"] == "2026-05-10T20:15:14Z"
    assert audit["active_pack_model_output_timestamp"] == ""
    assert audit["active_preview_matched_rows"] == 1
    assert audit["stale_pack_fallback_rows"] == 0


def test_war_board_supports_active_preview_rows_that_already_use_sleeper_ids(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    model_dir = tmp_path / "active_model"
    model_dir.mkdir()
    (model_dir / "stats_first_normalized_features.csv").write_text(
        "player_id,gsis_id,sleeper_id,player_name,position\n8144,,8144,Chris Olave,WR\n",
        encoding="utf-8",
    )
    (model_dir / "stats_first_veteran_model_preview_outputs.csv").write_text(
        (
            "player_id,player_name,position,overall_rank,position_rank,"
            "position_rank_label,private_lve_value,keeper_score,"
            "drop_candidate_score,trade_value,market_trade_value,"
            "market_edge_score,confidence_score,warning_status,warning_reasons,"
            "risk_flags,model_version,computed_at\n"
            "8144,Chris Olave,WR,58,27,WR27,62.06,55.0,42.88,"
            "59.67,50.0,12.06,81.5,model_warning,injury_risk,"
            "keeper_bubble,stats_first_test,2026-05-10T20:15:14Z\n"
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(command_board_service, "ACTIVE_STATS_FIRST_MODEL_DIR", model_dir)
    rows_by_table = _single_roster_rows(
        pack_private_score="92.26",
        computed_at="2026-05-07T23:23:32Z",
    )
    monkeypatch.setattr(
        command_board_service,
        "validate_data_pack",
        lambda path: ValidatedDataPack(
            data_pack_path=Path(str(path)),
            data_pack_name="sleeper-direct-pack",
            snapshot_date="2026-pre-draft",
            rows_by_table=rows_by_table,
            issues=(),
        ),
    )

    board = build_war_board("sleeper-direct-pack")

    assert board.rows[0]["stats_value"] == 62.06
    assert board.rows[0]["identity_match_method"] == "sleeper_id"
    assert board.data_source_audit_rows[0]["active_preview_matched_rows"] == 1


def test_active_preview_recalculates_visible_action_from_active_scores(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    model_dir = tmp_path / "active_model"
    model_dir.mkdir()
    (model_dir / "stats_first_normalized_features.csv").write_text(
        "player_id,gsis_id,sleeper_id,player_name,position\n8144,,8144,Core Player,WR\n",
        encoding="utf-8",
    )
    (model_dir / "stats_first_veteran_model_preview_outputs.csv").write_text(
        (
            "player_id,player_name,position,overall_rank,position_rank,"
            "position_rank_label,private_lve_value,keeper_score,"
            "drop_candidate_score,trade_value,market_trade_value,"
            "market_edge_score,confidence_score,warning_status,warning_reasons,"
            "risk_flags,model_version,computed_at\n"
            "8144,Core Player,WR,3,1,WR1,84.0,81.0,12.0,"
            "83.0,50.0,34.0,88.0,ready,,,"
            "stats_first_test,2026-05-10T20:15:14Z\n"
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(command_board_service, "ACTIVE_STATS_FIRST_MODEL_DIR", model_dir)
    rows_by_table = _single_roster_rows(
        pack_private_score="40.0",
        computed_at="2026-05-07T23:23:32Z",
    )
    rows_by_table["rosters"][0]["player_name"] = "Core Player"
    rows_by_table["model_outputs"][0]["player_name"] = "Core Player"
    rows_by_table["model_outputs"][0]["recommendation"] = "bubble"
    monkeypatch.setattr(
        command_board_service,
        "validate_data_pack",
        lambda path: ValidatedDataPack(
            data_pack_path=Path(str(path)),
            data_pack_name="active-action-pack",
            snapshot_date="2026-pre-draft",
            rows_by_table=rows_by_table,
            issues=(),
        ),
    )

    war_board = build_war_board("active-action-pack")
    team_board = build_team_command_board("active-action-pack")

    assert war_board.rows[0]["score_source"] == "active_stats_first_preview"
    assert war_board.rows[0]["action"] == "keep"
    assert team_board.roster_rows[0]["model_recommendation"] == "keep"


def test_blocking_active_preview_rows_are_needs_data_review_not_shop(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    model_dir = tmp_path / "active_model"
    model_dir.mkdir()
    (model_dir / "stats_first_normalized_features.csv").write_text(
        "player_id,gsis_id,sleeper_id,player_name,position\n8144,,8144,Low Confidence RB,RB\n",
        encoding="utf-8",
    )
    (model_dir / "stats_first_veteran_model_preview_outputs.csv").write_text(
        (
            "player_id,player_name,position,overall_rank,position_rank,"
            "position_rank_label,private_lve_value,keeper_score,"
            "drop_candidate_score,trade_value,market_trade_value,"
            "market_edge_score,confidence_score,warning_status,warning_reasons,"
            "risk_flags,model_version,computed_at\n"
            "8144,Low Confidence RB,RB,81,33,RB33,58.43,54.43,42.99,"
            "50.0,50.0,8.43,36.0,blocking,blocking_low_confidence,"
            "keeper_bubble,stats_first_test,2026-05-10T20:15:14Z\n"
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(command_board_service, "ACTIVE_STATS_FIRST_MODEL_DIR", model_dir)
    rows_by_table = _single_roster_rows(
        pack_private_score="58.43",
        computed_at="2026-05-07T23:23:32Z",
    )
    rows_by_table["rosters"][0]["player_name"] = "Low Confidence RB"
    rows_by_table["rosters"][0]["position"] = "RB"
    rows_by_table["model_outputs"][0]["player_name"] = "Low Confidence RB"
    rows_by_table["model_outputs"][0]["position"] = "RB"
    monkeypatch.setattr(
        command_board_service,
        "validate_data_pack",
        lambda path: ValidatedDataPack(
            data_pack_path=Path(str(path)),
            data_pack_name="low-confidence-pack",
            snapshot_date="2026-pre-draft",
            rows_by_table=rows_by_table,
            issues=(),
        ),
    )

    war_board = build_war_board("low-confidence-pack")
    team_board = build_team_command_board("low-confidence-pack")

    assert war_board.rows[0]["action"] == "review"
    assert team_board.roster_rows[0]["model_recommendation"] == "review"
    assert team_board.roster_rows[0]["team_section"] == "Needs Data Review"


def test_review_confidence_keep_rows_are_not_clean_core_holds(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    model_dir = tmp_path / "active_model"
    model_dir.mkdir()
    (model_dir / "stats_first_normalized_features.csv").write_text(
        "player_id,gsis_id,sleeper_id,player_name,position\n8144,,8144,Review Hold WR,WR\n",
        encoding="utf-8",
    )
    (model_dir / "stats_first_veteran_model_preview_outputs.csv").write_text(
        (
            "player_id,player_name,position,overall_rank,position_rank,"
            "position_rank_label,private_lve_value,keeper_score,"
            "drop_candidate_score,trade_value,market_trade_value,"
            "market_edge_score,confidence_score,warning_status,warning_reasons,"
            "risk_flags,model_version,computed_at\n"
            "8144,Review Hold WR,WR,8,4,WR4,76.0,72.0,22.0,"
            "70.0,50.0,26.0,66.5,data_warning,"
            "data_warning_confidence_below_target,,"
            "stats_first_test,2026-05-10T20:15:14Z\n"
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(command_board_service, "ACTIVE_STATS_FIRST_MODEL_DIR", model_dir)
    rows_by_table = _single_roster_rows(
        pack_private_score="76.0",
        computed_at="2026-05-07T23:23:32Z",
    )
    rows_by_table["rosters"][0]["player_name"] = "Review Hold WR"
    rows_by_table["model_outputs"][0]["player_name"] = "Review Hold WR"
    monkeypatch.setattr(
        command_board_service,
        "validate_data_pack",
        lambda path: ValidatedDataPack(
            data_pack_path=Path(str(path)),
            data_pack_name="review-hold-pack",
            snapshot_date="2026-pre-draft",
            rows_by_table=rows_by_table,
            issues=(),
        ),
    )

    team_board = build_team_command_board("review-hold-pack")

    assert team_board.roster_rows[0]["model_recommendation"] == "keep"
    assert team_board.roster_rows[0]["confidence_label"] == "review"
    assert team_board.roster_rows[0]["team_section"] == "Needs Data Review"


def test_war_board_warns_when_newer_active_preview_cannot_map_to_sleeper(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    model_dir = tmp_path / "active_model"
    model_dir.mkdir()
    (model_dir / "stats_first_normalized_features.csv").write_text(
        (
            "player_id,gsis_id,sleeper_id,player_name,position\n"
            "00-0037239,00-0037239,9999,Chris Olave,WR\n"
        ),
        encoding="utf-8",
    )
    (model_dir / "stats_first_veteran_model_preview_outputs.csv").write_text(
        (
            "player_id,player_name,position,overall_rank,position_rank,"
            "position_rank_label,private_lve_value,keeper_score,"
            "drop_candidate_score,trade_value,market_trade_value,"
            "market_edge_score,confidence_score,warning_status,warning_reasons,"
            "risk_flags,model_version,computed_at\n"
            "00-0037239,Chris Olave,WR,58,27,WR27,62.06,55.0,42.88,"
            "59.67,50.0,12.06,81.5,model_warning,injury_risk,"
            "keeper_bubble,stats_first_test,2026-05-10T20:15:14Z\n"
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(command_board_service, "ACTIVE_STATS_FIRST_MODEL_DIR", model_dir)
    rows_by_table = _single_roster_rows(
        pack_private_score="92.26",
        computed_at="2026-05-07T23:23:32Z",
    )
    monkeypatch.setattr(
        command_board_service,
        "validate_data_pack",
        lambda path: ValidatedDataPack(
            data_pack_path=Path(str(path)),
            data_pack_name="unmapped-pack",
            snapshot_date="2026-pre-draft",
            rows_by_table=rows_by_table,
            issues=(),
        ),
    )

    board = build_war_board("unmapped-pack")

    assert board.rows[0]["stats_value"] == 92.26
    assert board.rows[0]["score_source"] == "data_pack_model_outputs"
    assert "did not map" in str(board.rows[0]["score_source_warning"])
    audit = board.data_source_audit_rows[0]
    assert audit["status"] == "warning"
    assert audit["visible_score_source"] == "data_pack_model_outputs"
    assert audit["stale_pack_fallback_rows"] == 1
    assert "falling back to older data-pack outputs" in str(audit["warning"])


def _single_roster_rows(
    *,
    pack_private_score: str,
    computed_at: str,
) -> dict[str, list[dict[str, object]]]:
    return {
        "rosters": [
            {
                "snapshot_date": "2026-pre-draft",
                "season": "2026",
                "team_id": "niners",
                "team_name": "Niners",
                "player_id": "8144",
                "player_name": "Chris Olave",
                "position": "WR",
                "league_rank": "14",
            }
        ],
        "official_rankings": [],
        "model_outputs": [
            {
                "player_id": "8144",
                "player_name": "Chris Olave",
                "position": "WR",
                "overall_rank": "14",
                "position_rank_label": "WR14",
                "war_score": "91.33",
                "private_score": pack_private_score,
                "keeper_score": "91.33",
                "drop_candidate_score": "12",
                "confidence_score": "88",
                "warning_status": "ready",
                "computed_at": computed_at,
            }
        ],
    }


def _roster_row(
    player_id: str,
    player_name: str,
    position: str,
    *,
    team_id: str = "niners",
) -> dict[str, object]:
    return {
        "snapshot_date": "2026-pre-draft",
        "season": "2026",
        "team_id": team_id,
        "team_name": "Niners" if team_id == "niners" else "Other Team",
        "player_id": player_id,
        "player_name": player_name,
        "position": position,
        "league_rank": "99",
        "roster_status": "rostered",
    }


def _model_row(
    player_id: str,
    player_name: str,
    position: str,
    score: str,
) -> dict[str, object]:
    return {
        "player_id": player_id,
        "player_name": player_name,
        "position": position,
        "war_score": score,
        "private_score": score,
        "keeper_score": score,
        "drop_candidate_score": "10",
        "confidence_score": "88",
        "risk_level": "low",
        "warning_status": "ready",
    }
