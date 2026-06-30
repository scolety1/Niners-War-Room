from __future__ import annotations

from pathlib import Path

from src.services.injury_availability_context_service import (
    BLOCKED,
    NEED_MODEL_GATE,
    NOT_ENOUGH_INFORMATION,
    SAFE_NOW,
    WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN,
    availability_dataset_status_rows,
    build_injury_availability_display_context,
    display_context_schema_rows,
    lve_injury_durability_reuse_allowed,
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
    assert row["games_while_rostered"] == NOT_ENOUGH_INFORMATION
    assert row["games_missed_while_rostered"] == NOT_ENOUGH_INFORMATION
    assert row["per_game_denominator"] == NOT_ENOUGH_INFORMATION
    assert row["availability_context_status"] == WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN
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


def test_dataset_statuses_wait_until_nflverse_refresh_health_green() -> None:
    rows = {row["dataset"]: row for row in availability_dataset_status_rows()}

    assert rows["nflverse_injuries"]["classification"] == SAFE_NOW
    for dataset in (
        "nflverse_weekly_rosters",
        "nflverse_rosters",
        "nflverse_schedules",
        "nflverse_snap_counts",
        "nflverse_player_stats",
        "refresh_metadata",
    ):
        assert rows[dataset]["classification"] == WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN
        assert "until refresh health is green" in rows[dataset]["active_compute_use"]


def test_schema_explains_season_total_and_per_game_caveats() -> None:
    rows = {row["field_name"]: row for row in display_context_schema_rows()}

    assert rows["prior_season_injury_report_weeks"]["status"] == SAFE_NOW
    assert "Season-total" in rows["prior_season_injury_report_weeks"]["notes"]
    assert rows["games_while_rostered"]["status"] == (
        WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN
    )
    assert rows["per_game_denominator"]["status"] == (
        WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN
    )


def test_proposal_classification_matrix_preserves_hq_guardrails() -> None:
    rows = {row["proposal_id"]: row for row in proposal_classification_rows()}

    assert rows["IAC-01"]["classification"] == SAFE_NOW
    assert rows["IAC-04"]["classification"] == SAFE_NOW
    assert rows["IAC-05"]["classification"] == WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN
    assert rows["IAC-10"]["classification"] == WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN
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
    assert (
        "Review-only context. No medical projection or injury-risk score is made."
        in player_compare_text
    )
    assert "does not change comparison scoring" in player_compare_text
    assert "ranking, lean, or hidden decision logic" in player_compare_text


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
    }

    assert expected <= {path.name for path in DOC_ROOT.iterdir()}
    verdict = (DOC_ROOT / "FINAL_VERDICT.md").read_text(encoding="utf-8")
    assert "YELLOW_WAITING_FOR_NFLVERSE_REFRESH_HEALTH_GREEN" in verdict


def _row_text(row: dict[str, str]) -> str:
    return " ".join(row.values()).lower()
