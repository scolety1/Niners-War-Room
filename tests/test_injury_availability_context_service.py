from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.services.injury_availability_context_service import (
    BLOCKED,
    NEED_MODEL_GATE,
    NOT_ENOUGH_INFORMATION,
    SAFE_NOW,
    YELLOW_NEEDS_PLAYER_CONTEXT_ARTIFACT_EXTENSION,
    availability_dataset_status_rows,
    build_injury_availability_display_context,
    build_nflverse_availability_panel_rows,
    display_context_schema_rows,
    lve_injury_durability_reuse_allowed,
    nflverse_availability_artifact_counts,
    nflverse_availability_denominator_artifact_counts,
    proposal_classification_rows,
    unsafe_availability_field_names,
)

DOC_ROOT = Path(
    "docs/hq/injury_availability_context/"
    "injury_availability_display_context_safe_upgrade_20260630"
)
SERVICE_PATH = Path("src/services/injury_availability_context_service.py")
RANKINGS_PAGE = Path("app/pages/20_final_board_v1.py")
PLAYER_COMPARE_PAGE = Path("app/pages/22_player_compare_v1.py")


def test_missing_injury_and_availability_context_remains_nei() -> None:
    row = build_injury_availability_display_context(
        player_id="p1",
        gsis_id="00-0000001",
        player_name="Example RB",
        position="RB",
    )

    assert row["injury_context_available"] == NOT_ENOUGH_INFORMATION
    assert row["prior_season_injury_report_weeks"] == NOT_ENOUGH_INFORMATION
    assert row["season_anchor"] == NOT_ENOUGH_INFORMATION
    assert row["games_while_rostered"] == NOT_ENOUGH_INFORMATION
    assert row["games_missed_while_rostered"] == NOT_ENOUGH_INFORMATION
    assert row["per_game_denominator"] == NOT_ENOUGH_INFORMATION
    assert row["availability_context_status"] == NOT_ENOUGH_INFORMATION
    assert "Not enough information" in row["availability_caveat"]
    assert "healthy" not in _row_text(row)
    assert "clean health" not in _row_text(row)


def test_factual_report_counts_do_not_infer_per_game_availability() -> None:
    row = build_injury_availability_display_context(
        player_id="p1",
        gsis_id="00-0000001",
        player_name="Example RB",
        position="RB",
        prior_season_injury_report_weeks=3,
        prior_season_out_or_doubtful_weeks=2,
    )

    assert row["injury_context_available"] == "true"
    assert row["prior_season_injury_report_weeks"] == "3"
    assert row["prior_season_out_or_doubtful_weeks"] == "2"
    for field_name in (
        "season_anchor",
        "games_while_rostered",
        "games_with_snaps",
        "games_with_recorded_stats",
        "games_played_context",
        "games_missed_while_rostered",
        "per_game_denominator",
    ):
        assert row[field_name] == NOT_ENOUGH_INFORMATION
    assert "missed due to injury" not in _row_text(row)
    assert "do not infer unavailable games from report counts" in _row_text(row)


def test_ambiguous_identity_keeps_context_not_enough_information() -> None:
    row = build_injury_availability_display_context(
        player_id="p2",
        gsis_id="00-0000002",
        player_name="Ambiguous WR",
        position="WR",
        identity_match_status="ambiguous",
        prior_season_injury_report_weeks=4,
        prior_season_out_or_doubtful_weeks=1,
    )

    assert row["identity_match_status"] == "ambiguous"
    assert row["injury_context_available"] == NOT_ENOUGH_INFORMATION
    assert row["prior_season_injury_report_weeks"] == NOT_ENOUGH_INFORMATION
    assert row["prior_season_out_or_doubtful_weeks"] == NOT_ENOUGH_INFORMATION


def test_no_projection_scoring_or_blocked_fields_in_display_row() -> None:
    row = build_injury_availability_display_context()
    unsafe = unsafe_availability_field_names(tuple(row))

    assert unsafe == ()
    assert row["model_input_allowed"] == "false"
    assert row["rank_use_allowed"] == "false"
    assert row["source_truth_allowed"] == "false"
    forbidden_terms = (
        "risk score",
        "durability score",
        "medical projection",
        "recovery probability",
        "comeback probability",
        "acl comeback",
        "achilles comeback",
    )
    display_text = _row_text(row)
    for term in forbidden_terms:
        assert term not in display_text


def test_dataset_statuses_move_safe_direct_fields_from_wait_to_safe_now() -> None:
    rows = {row["dataset"]: row for row in availability_dataset_status_rows()}

    assert rows["nflverse_injuries"]["classification"] == SAFE_NOW
    assert rows["nflverse_rosters"]["classification"] == SAFE_NOW
    assert rows["nflverse_weekly_rosters"]["classification"] == SAFE_NOW
    assert rows["nflverse_schedules"]["classification"] == SAFE_NOW
    assert rows["nflverse_snap_counts"]["classification"] == SAFE_NOW
    assert rows["nflverse_player_stats"]["classification"] == SAFE_NOW
    assert rows["refresh_metadata"]["classification"] == SAFE_NOW
    assert rows["ff_rankings"]["classification"] == BLOCKED


def test_schema_explains_denominator_and_per_game_caveats() -> None:
    rows = {row["field_name"]: row for row in display_context_schema_rows()}

    assert rows["prior_season_injury_report_weeks"]["status"] == SAFE_NOW
    assert "Season-total" in rows["prior_season_injury_report_weeks"]["notes"]
    assert rows["roster_status"]["status"] == SAFE_NOW
    assert rows["injury_report_status"]["status"] == SAFE_NOW
    assert rows["snap_sample_size"]["status"] == SAFE_NOW
    assert rows["season_anchor"]["status"] == SAFE_NOW
    assert rows["games_while_rostered"]["status"] == SAFE_NOW
    assert rows["games_with_snaps"]["status"] == SAFE_NOW
    assert rows["games_with_recorded_stats"]["status"] == SAFE_NOW
    assert rows["games_played_context"]["status"] == SAFE_NOW
    assert rows["per_game_denominator"]["status"] == SAFE_NOW
    assert rows["games_missed_while_rostered"]["status"] == (
        YELLOW_NEEDS_PLAYER_CONTEXT_ARTIFACT_EXTENSION
    )


def test_actual_tracked_artifact_has_expected_safe_and_review_coverage() -> None:
    counts = nflverse_availability_artifact_counts()
    denominator_counts = nflverse_availability_denominator_artifact_counts()

    assert counts["rows"] == 294
    assert counts["safe_display_rows"] == 281
    assert counts["identity_review_rows"] == 13
    assert counts["schedule_current_future_rows"] == 240
    assert denominator_counts["rows"] == 588
    assert denominator_counts["safe_denominator_rows"] == 437
    assert denominator_counts["need_source_fields_rows"] == 43
    assert denominator_counts["identity_review_rows"] == 108
    assert denominator_counts["games_missed_populated_rows"] == 0


def test_safe_identity_row_exposes_only_schema_safe_factual_availability_context() -> None:
    rows = build_nflverse_availability_panel_rows(
        [{"player_id": "p-safe", "player": "Safe WR", "position": "WR"}],
        artifact_frame=_artifact_rows(),
        schema_frame=_schema_rows(),
        denominator_frame=_denominator_rows(),
        denominator_schema_frame=_denominator_schema_rows(),
    )
    row = rows[0]

    assert row["NFLVerse Availability Context"] == "Availability context present"
    assert row["NFLVerse Identity Status"] == "Matched"
    assert row["Roster Status"] == "ACT"
    assert row["Weekly Roster Status"] == "ACT"
    assert row["Injury Report Status"] == NOT_ENOUGH_INFORMATION
    assert row["Practice Status"] == NOT_ENOUGH_INFORMATION
    assert row["Snap Sample Size"] == NOT_ENOUGH_INFORMATION
    assert row["Last Active"] == "season=2025; week=17"
    assert row["Schedule Context"] == NOT_ENOUGH_INFORMATION
    assert row["Season Anchor"] == "2024 | 2025"
    assert row["Games While Rostered"] == "2024: 17 | 2025: 17"
    assert row["Games With Snaps"] == "2024: 11 | 2025: 16"
    assert row["Games With Recorded Stats"] == "2024: 11 | 2025: 16"
    assert row["Games Played Context"] == (
        "2024: rostered_games=17; snap_games=11; recorded_stat_games=11 | "
        "2025: rostered_games=17; snap_games=16; recorded_stat_games=16"
    )
    assert row["Per-Game Denominator"] == "2024: 17 | 2025: 17"
    assert row["Games Missed While Rostered"] == NOT_ENOUGH_INFORMATION
    assert "healthy" not in _row_text(row)
    assert "risk" not in _row_text(row)
    assert "medical" not in _row_text(row)
    assert "durability" not in _row_text(row)


def test_identity_review_row_does_not_expose_detailed_nflverse_context() -> None:
    rows = build_nflverse_availability_panel_rows(
        [{"player_id": "p-review", "player": "Review RB", "position": "RB"}],
        artifact_frame=_artifact_rows(),
        schema_frame=_schema_rows(),
        denominator_frame=_denominator_rows(),
        denominator_schema_frame=_denominator_schema_rows(),
    )
    row = rows[0]

    assert row["NFLVerse Availability Context"] == "Review needed"
    assert row["NFLVerse Identity Status"] == "Review needed"
    assert row["Identity Caveat"] == "Review needed"
    assert row["Roster Status"] == NOT_ENOUGH_INFORMATION
    assert row["Injury Report Status"] == NOT_ENOUGH_INFORMATION
    assert row["Snap Sample Size"] == NOT_ENOUGH_INFORMATION
    assert row["Season Anchor"] == NOT_ENOUGH_INFORMATION
    assert row["Games While Rostered"] == NOT_ENOUGH_INFORMATION
    assert row["Per-Game Denominator"] == NOT_ENOUGH_INFORMATION


def test_missing_roster_snap_and_injury_values_do_not_become_clean_zero_or_safe() -> None:
    rows = build_nflverse_availability_panel_rows(
        [{"player_id": "p-missing", "player": "Missing TE", "position": "TE"}],
        artifact_frame=_artifact_rows(),
        schema_frame=_schema_rows(),
        denominator_frame=_denominator_rows(),
        denominator_schema_frame=_denominator_schema_rows(),
    )
    row = rows[0]

    assert row["Roster Status"] == NOT_ENOUGH_INFORMATION
    assert row["Weekly Roster Status"] == NOT_ENOUGH_INFORMATION
    assert row["Injury Report Status"] == NOT_ENOUGH_INFORMATION
    assert row["Snap Sample Size"] == NOT_ENOUGH_INFORMATION
    assert row["Snap Sample Size"] != "0"
    assert row["Season Anchor"] == NOT_ENOUGH_INFORMATION
    assert row["Games While Rostered"] == NOT_ENOUGH_INFORMATION
    assert row["Games With Snaps"] == NOT_ENOUGH_INFORMATION
    assert row["Games With Snaps"] != "0"
    assert row["Per-Game Denominator"] == NOT_ENOUGH_INFORMATION
    assert "clean" not in _row_text(row)
    assert "safe" not in _row_text(row)


def test_safe_denominator_missing_values_remain_nei_not_zero() -> None:
    rows = build_nflverse_availability_panel_rows(
        [{"player_id": "p-partial", "player": "Partial WR", "position": "WR"}],
        artifact_frame=_artifact_rows(),
        schema_frame=_schema_rows(),
        denominator_frame=_denominator_rows(),
        denominator_schema_frame=_denominator_schema_rows(),
    )
    row = rows[0]

    assert row["NFLVerse Availability Context"] == "Availability context present"
    assert row["Season Anchor"] == "2025"
    assert row["Games While Rostered"] == "17"
    assert row["Games With Snaps"] == NOT_ENOUGH_INFORMATION
    assert row["Games With Snaps"] != "0"
    assert row["Games With Recorded Stats"] == NOT_ENOUGH_INFORMATION
    assert row["Games Missed While Rostered"] == NOT_ENOUGH_INFORMATION


def test_proposal_classification_matrix_preserves_hq_guardrails() -> None:
    rows = {row["proposal_id"]: row for row in proposal_classification_rows()}

    assert rows["IAC-01"]["classification"] == SAFE_NOW
    assert rows["IAC-04"]["classification"] == SAFE_NOW
    assert rows["IAC-05"]["classification"] == SAFE_NOW
    assert rows["IAC-06"]["classification"] == SAFE_NOW
    assert rows["IAC-07"]["classification"] == SAFE_NOW
    assert rows["IAC-08"]["classification"] == (
        YELLOW_NEEDS_PLAYER_CONTEXT_ARTIFACT_EXTENSION
    )
    assert rows["IAC-09"]["classification"] == SAFE_NOW
    assert rows["IAC-10"]["classification"] == SAFE_NOW
    assert rows["IAC-11"]["classification"] == NEED_MODEL_GATE
    assert rows["IAC-12"]["classification"] == BLOCKED
    assert rows["IAC-13"]["classification"] == BLOCKED
    assert rows["IAC-14"]["classification"] == BLOCKED


def test_lve_durability_service_is_not_reused_by_safe_display_service() -> None:
    text = SERVICE_PATH.read_text(encoding="utf-8")

    assert lve_injury_durability_reuse_allowed() is False
    assert "lve_injury_durability_service" not in text


def test_existing_display_context_surfaces_remain_display_only() -> None:
    rankings_text = RANKINGS_PAGE.read_text(encoding="utf-8")
    player_compare_text = PLAYER_COMPARE_PAGE.read_text(encoding="utf-8")

    assert "Injury context is review-only" in rankings_text
    assert "Missing injury context is not clean health" in rankings_text
    assert "Injury / Availability Context" in player_compare_text
    assert "NFLVerse Availability Context" in player_compare_text
    assert "build_nflverse_availability_panel_rows" in player_compare_text
    assert (
        "Review-only context. No medical projection or injury-risk score is made."
        in player_compare_text
    )
    assert "does not change comparison scoring" in player_compare_text
    assert "ranking, visible-context read, or hidden decision logic" in player_compare_text


def test_player_compare_page_does_not_read_raw_shared_nflverse_data() -> None:
    text = PLAYER_COMPARE_PAGE.read_text(encoding="utf-8")

    assert "C:\\NWR_SHARED_DATA" not in text
    assert "NWR_SHARED_DATA" not in text


def test_display_service_reads_tracked_artifacts_not_raw_shared_cache() -> None:
    text = SERVICE_PATH.read_text(encoding="utf-8")

    assert "C:\\NWR_SHARED_DATA" not in text
    assert "NWR_SHARED_DATA" not in text
    assert "nflverse_availability_denominator_display_v1_20260630" in text


def test_required_documentation_packet_files_exist() -> None:
    expected = {
        "MANIFEST.md",
        "DEEP_RESEARCH_PROPOSAL_CLASSIFICATION.md",
        "INJURY_AVAILABILITY_SOURCE_GATE.md",
        "NFLVERSE_INJURY_AVAILABILITY_DATASET_COVERAGE.csv",
        "DISPLAY_CONTEXT_SCHEMA.md",
        "UI_COPY_AND_GUARDRAILS.md",
        "MODEL_RANK_SOURCE_TRUTH_NON_MUTATION_REPORT.md",
        "TEST_RESULTS.md",
        "FINAL_VERDICT.md",
        "nflverse_availability_context_activation_summary.md",
        "nflverse_availability_field_map.csv",
        "nflverse_availability_guardrail_audit.md",
    }

    assert expected <= {path.name for path in DOC_ROOT.iterdir()}
    verdict = (DOC_ROOT / "FINAL_VERDICT.md").read_text(encoding="utf-8")
    assert "GREEN_AVAILABILITY_DENOMINATOR_DISPLAY_READY" in verdict


def _row_text(row: dict[str, str]) -> str:
    return " ".join(row.values()).lower()


def _schema_rows() -> pd.DataFrame:
    columns = (
        "identity_join_status",
        "identity_caveat",
        "roster_birth_date_derived_age",
        "age_source",
        "roster_status",
        "weekly_roster_status",
        "injury_report_status",
        "injury_report_date_week",
        "practice_status",
        "snap_count_recency",
        "latest_snap_season",
        "latest_snap_week",
        "snap_sample_size",
        "last_active_season",
        "last_active_week",
        "data_coverage_status",
    )
    return pd.DataFrame(
        [
            {
                "column_name": column,
                "field_status": "SAFE_NOW_DISPLAY_ONLY",
                "display_only": "true",
                "model_use_allowed": "false",
                "training_allowed": "false",
                "source_truth_allowed": "false",
                "rank_logic_allowed": "false",
                "hidden_sort_allowed": "false",
                "trade_value_allowed": "false",
                "pick_value_allowed": "false",
            }
            for column in columns
        ]
    )


def _denominator_schema_rows() -> pd.DataFrame:
    safe_fields = {
        "season_anchor": "SAFE_NOW_DISPLAY_ONLY",
        "games_while_rostered": "SAFE_NOW_DISPLAY_ONLY_WHEN_POPULATED",
        "games_with_snaps": "SAFE_NOW_DISPLAY_ONLY_WHEN_POPULATED",
        "games_with_recorded_stats": "SAFE_NOW_DISPLAY_ONLY_WHEN_POPULATED",
        "games_played_context": "SAFE_NOW_DISPLAY_ONLY_WHEN_POPULATED",
        "per_game_denominator": "SAFE_NOW_DISPLAY_ONLY_WHEN_POPULATED",
        "denominator_status": "SAFE_NOW_DISPLAY_ONLY",
        "identity_join_status": "SAFE_NOW_DISPLAY_ONLY",
        "review_required": "SAFE_NOW_DISPLAY_ONLY",
    }
    rows = [
        {
            "column_name": column,
            "field_status": status,
            "display_only": "true",
            "model_use_allowed": "false",
            "training_allowed": "false",
            "source_truth_allowed": "false",
            "rank_logic_allowed": "false",
            "hidden_sort_allowed": "false",
            "trade_value_allowed": "false",
            "pick_value_allowed": "false",
        }
        for column, status in safe_fields.items()
    ]
    rows.append(
        {
            "column_name": "games_missed_while_rostered",
            "field_status": "BLOCKED_NEEDS_EXPLICIT_GAME_STATUS_SOURCE",
            "display_only": "true",
            "model_use_allowed": "false",
            "training_allowed": "false",
            "source_truth_allowed": "false",
            "rank_logic_allowed": "false",
            "hidden_sort_allowed": "false",
            "trade_value_allowed": "false",
            "pick_value_allowed": "false",
        }
    )
    return pd.DataFrame(rows)


def _denominator_flags() -> dict[str, str]:
    return {
        "display_only": "true",
        "review_only": "true",
        "model_use_allowed": "false",
        "training_allowed": "false",
        "source_truth_allowed": "false",
        "rank_logic_allowed": "false",
        "hidden_sort_allowed": "false",
        "trade_value_allowed": "false",
        "pick_value_allowed": "false",
    }


def _denominator_rows() -> pd.DataFrame:
    flags = _denominator_flags()
    return pd.DataFrame(
        [
            {
                **flags,
                "nwr_player_id": "p-safe",
                "season_anchor": "2024",
                "games_while_rostered": "17",
                "games_with_snaps": "11",
                "games_with_recorded_stats": "11",
                "games_missed_while_rostered": "6",
                "games_played_context": (
                    "rostered_games=17; snap_games=11; recorded_stat_games=11; "
                    "not an injury-risk/durability/medical score"
                ),
                "per_game_denominator": "17",
                "denominator_status": "SAFE_NOW_DISPLAY_ONLY",
                "identity_join_status": "SAFE_NOW_DISPLAY_ONLY",
                "review_required": "false",
            },
            {
                **flags,
                "nwr_player_id": "p-safe",
                "season_anchor": "2025",
                "games_while_rostered": "17",
                "games_with_snaps": "16",
                "games_with_recorded_stats": "16",
                "games_missed_while_rostered": NOT_ENOUGH_INFORMATION,
                "games_played_context": (
                    "rostered_games=17; snap_games=16; recorded_stat_games=16; "
                    "not an injury-risk/durability/medical score"
                ),
                "per_game_denominator": "17",
                "denominator_status": "SAFE_NOW_DISPLAY_ONLY",
                "identity_join_status": "SAFE_NOW_DISPLAY_ONLY",
                "review_required": "false",
            },
            {
                **flags,
                "nwr_player_id": "p-review",
                "season_anchor": "2025",
                "games_while_rostered": "17",
                "games_with_snaps": "10",
                "games_with_recorded_stats": "10",
                "games_missed_while_rostered": NOT_ENOUGH_INFORMATION,
                "games_played_context": "rostered_games=17; snap_games=10",
                "per_game_denominator": "17",
                "denominator_status": "NEED_IDENTITY_APPROVAL",
                "identity_join_status": "NEED_IDENTITY_REVIEW",
                "review_required": "true",
            },
            {
                **flags,
                "nwr_player_id": "p-missing",
                "season_anchor": "2025",
                "games_while_rostered": "0",
                "games_with_snaps": "0",
                "games_with_recorded_stats": "0",
                "games_missed_while_rostered": NOT_ENOUGH_INFORMATION,
                "games_played_context": "clean",
                "per_game_denominator": "0",
                "denominator_status": "NEED_SOURCE_FIELDS",
                "identity_join_status": "SAFE_NOW_DISPLAY_ONLY",
                "review_required": "false",
            },
            {
                **flags,
                "nwr_player_id": "p-partial",
                "season_anchor": "2025",
                "games_while_rostered": "17",
                "games_with_snaps": "",
                "games_with_recorded_stats": "",
                "games_missed_while_rostered": NOT_ENOUGH_INFORMATION,
                "games_played_context": "",
                "per_game_denominator": "17",
                "denominator_status": "SAFE_NOW_DISPLAY_ONLY",
                "identity_join_status": "SAFE_NOW_DISPLAY_ONLY",
                "review_required": "false",
            },
        ]
    )


def _artifact_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "nwr_player_id": "p-safe",
                "identity_join_status": "SAFE_NOW_DISPLAY_ONLY",
                "review_required": "false",
                "identity_caveat": "exact_nwr_player_id_to_rosters_sleeper_id",
                "roster_birth_date_derived_age": "25.0",
                "age_source": "rosters.birth_date",
                "roster_status": "ACT",
                "weekly_roster_status": "ACT",
                "injury_report_status": NOT_ENOUGH_INFORMATION,
                "injury_report_date_week": NOT_ENOUGH_INFORMATION,
                "practice_status": NOT_ENOUGH_INFORMATION,
                "snap_count_recency": NOT_ENOUGH_INFORMATION,
                "latest_snap_season": NOT_ENOUGH_INFORMATION,
                "latest_snap_week": NOT_ENOUGH_INFORMATION,
                "snap_sample_size": NOT_ENOUGH_INFORMATION,
                "last_active_season": "2025",
                "last_active_week": "17",
                "data_coverage_status": "ready=rosters;weekly_rosters;injuries",
            },
            {
                "nwr_player_id": "p-review",
                "identity_join_status": "NEED_IDENTITY_REVIEW",
                "review_required": "true",
                "identity_caveat": "ambiguous",
                "roster_birth_date_derived_age": "24.0",
                "age_source": "rosters.birth_date",
                "roster_status": "ACT",
                "weekly_roster_status": "ACT",
                "injury_report_status": "Questionable",
                "injury_report_date_week": "season=2025; week=18",
                "practice_status": "Limited",
                "snap_count_recency": "season=2025; week=18",
                "latest_snap_season": "2025",
                "latest_snap_week": "18",
                "snap_sample_size": "10",
                "last_active_season": "2025",
                "last_active_week": "18",
                "data_coverage_status": "ready=rosters",
            },
            {
                "nwr_player_id": "p-missing",
                "identity_join_status": "SAFE_NOW_DISPLAY_ONLY",
                "review_required": "false",
                "identity_caveat": "exact_nwr_player_id_to_rosters_sleeper_id",
                "roster_birth_date_derived_age": NOT_ENOUGH_INFORMATION,
                "age_source": NOT_ENOUGH_INFORMATION,
                "roster_status": NOT_ENOUGH_INFORMATION,
                "weekly_roster_status": NOT_ENOUGH_INFORMATION,
                "injury_report_status": NOT_ENOUGH_INFORMATION,
                "injury_report_date_week": NOT_ENOUGH_INFORMATION,
                "practice_status": NOT_ENOUGH_INFORMATION,
                "snap_count_recency": NOT_ENOUGH_INFORMATION,
                "latest_snap_season": NOT_ENOUGH_INFORMATION,
                "latest_snap_week": NOT_ENOUGH_INFORMATION,
                "snap_sample_size": NOT_ENOUGH_INFORMATION,
                "last_active_season": NOT_ENOUGH_INFORMATION,
                "last_active_week": NOT_ENOUGH_INFORMATION,
                "data_coverage_status": NOT_ENOUGH_INFORMATION,
            },
            {
                "nwr_player_id": "p-partial",
                "identity_join_status": "SAFE_NOW_DISPLAY_ONLY",
                "review_required": "false",
                "identity_caveat": "exact_nwr_player_id_to_rosters_sleeper_id",
                "roster_birth_date_derived_age": NOT_ENOUGH_INFORMATION,
                "age_source": NOT_ENOUGH_INFORMATION,
                "roster_status": "ACT",
                "weekly_roster_status": "ACT",
                "injury_report_status": NOT_ENOUGH_INFORMATION,
                "injury_report_date_week": NOT_ENOUGH_INFORMATION,
                "practice_status": NOT_ENOUGH_INFORMATION,
                "snap_count_recency": NOT_ENOUGH_INFORMATION,
                "latest_snap_season": NOT_ENOUGH_INFORMATION,
                "latest_snap_week": NOT_ENOUGH_INFORMATION,
                "snap_sample_size": NOT_ENOUGH_INFORMATION,
                "last_active_season": NOT_ENOUGH_INFORMATION,
                "last_active_week": NOT_ENOUGH_INFORMATION,
                "data_coverage_status": NOT_ENOUGH_INFORMATION,
            },
        ]
    )
