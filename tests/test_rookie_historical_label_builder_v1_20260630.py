from __future__ import annotations

from scripts.build_rookie_historical_label_builder_v1_20260630 import (
    EXPECTED_SCORING_MODE,
    LABEL_COLUMNS,
    NOT_ENOUGH,
    SHARED_OUTPUT_ROOT,
    build_coverage_rows,
    build_label_rows,
    horizon_hit,
    season_hit,
    validate_label_rows,
    validate_review_rows,
)


def test_label_builder_creates_only_linked_review_only_rows() -> None:
    rows = build_label_rows(
        bridge_rows=_bridge_rows(),
        season_rows=_season_rows(),
        scoring_mode=EXPECTED_SCORING_MODE,
        latest_label_season=2024,
    )

    validate_label_rows(rows)
    assert len(rows) == 3
    assert {row["review_only"] for row in rows} == {"true"}
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}
    assert {row["scoring_mode"] for row in rows} == {EXPECTED_SCORING_MODE}


def test_rookie_year_year_2_and_threshold_map_logic() -> None:
    rows = build_label_rows(
        bridge_rows=_bridge_rows(),
        season_rows=_season_rows(),
        scoring_mode=EXPECTED_SCORING_MODE,
        latest_label_season=2024,
    )
    qb = next(row for row in rows if row["player_name"] == "Fixture QB")

    assert qb["rookie_year_position_finish"] == "8"
    assert qb["year_2_position_finish"] == "5"
    assert qb["rookie_year_top_6_hit"] == "miss"
    assert qb["rookie_year_top_12_hit"] == "hit"
    assert qb["rookie_year_top_24_hit"] == "not_applicable"
    assert qb["year_2_top_6_hit"] == "hit"
    assert qb["first_3y_top_6_hit"] == "hit"
    assert qb["first_5y_top_12_hit"] == "hit"


def test_right_censored_windows_preserve_hits_but_do_not_fake_misses() -> None:
    rows = build_label_rows(
        bridge_rows=_bridge_rows(),
        season_rows=_season_rows(),
        scoring_mode=EXPECTED_SCORING_MODE,
        latest_label_season=2024,
    )
    rb = next(row for row in rows if row["player_name"] == "Fixture RB")

    assert rb["first_3y_window_complete"] == "false"
    assert rb["first_5y_window_complete"] == "false"
    assert rb["censoring_status"] == "right_censored"
    assert rb["first_3y_top_24_hit"] == "hit"
    assert rb["first_5y_top_24_hit"] == "hit"
    assert rb["first_3y_top_6_hit"] == NOT_ENOUGH
    assert rb["first_5y_top_6_hit"] == NOT_ENOUGH


def test_missing_season_rows_remain_not_enough_information() -> None:
    rows = build_label_rows(
        bridge_rows=_bridge_rows(),
        season_rows=_season_rows(),
        scoring_mode=EXPECTED_SCORING_MODE,
        latest_label_season=2024,
    )
    wr = next(row for row in rows if row["player_name"] == "Missing Rookie Row")

    assert wr["rookie_year_position_finish"] == NOT_ENOUGH
    assert wr["rookie_year_top_12_hit"] == NOT_ENOUGH
    assert wr["first_3y_top_24_hit"] == NOT_ENOUGH
    assert "0%" not in ",".join(wr.values())


def test_helper_logic_does_not_count_incomplete_windows_as_misses() -> None:
    season_rows = {
        ("00-fixture", 2023): {
            "top_6_hit": "miss",
            "top_12_hit": "miss",
            "top_24_hit": "hit",
            "top_36_hit": "hit",
        }
    }

    assert season_hit(season_rows[("00-fixture", 2023)], position="TE", threshold=24) == (
        "not_applicable"
    )
    assert horizon_hit(
        player_id="00-fixture",
        position="RB",
        threshold=6,
        start_year=2023,
        horizon_years=3,
        latest_label_season=2024,
        season_by_player_year=season_rows,
    ) == NOT_ENOUGH


def test_coverage_rows_keep_review_flags_and_no_probability_wiring() -> None:
    rows = build_label_rows(
        bridge_rows=_bridge_rows(),
        season_rows=_season_rows(),
        scoring_mode=EXPECTED_SCORING_MODE,
        latest_label_season=2024,
    )
    coverage = build_coverage_rows(
        bridge_rows=_bridge_rows(),
        label_rows=rows,
        latest_label_season=2024,
        scoring_mode=EXPECTED_SCORING_MODE,
    )
    metrics = {row["metric"]: row["value"] for row in coverage}

    validate_review_rows(coverage)
    assert metrics["label_rows_built"] == "3"
    assert metrics["blocked_bridge_rows"] == "1"
    assert metrics["rookie_probabilities_created"] == "0"
    assert metrics["rankings_wiring_created"] == "0"
    assert all("probability" not in column for column in LABEL_COLUMNS)


def test_validation_rejects_model_or_training_promotion() -> None:
    rows = build_label_rows(
        bridge_rows=_bridge_rows(),
        season_rows=_season_rows(),
        scoring_mode=EXPECTED_SCORING_MODE,
        latest_label_season=2024,
    )
    rows[0]["model_use_allowed"] = "true"

    try:
        validate_label_rows(rows)
    except ValueError as exc:
        assert "model_use_allowed=false" in str(exc)
    else:
        raise AssertionError("Expected label validation to reject model-use promotion")


def test_shared_outputs_are_outside_repo_and_not_local_exports() -> None:
    shared_text = str(SHARED_OUTPUT_ROOT)

    assert "C:\\NWR_SHARED_DATA" in shared_text
    assert "local_exports" not in shared_text


def test_lane_code_does_not_reference_protected_nfl_usage_paths() -> None:
    protected_paths = (
        "docs/hq/data_sources/nfl_usage/historical_panel/",
        "scripts/build_historical_nfl_usage_panel_v0.py",
        "src/services/nfl_usage_historical_panel_service.py",
        "tests/test_nfl_usage_historical_panel_service.py",
    )

    assert all("rookie_historical_label_builder" not in path for path in protected_paths)


def _bridge_rows() -> list[dict[str, str]]:
    return [
        _bridge_row("Fixture QB", "QB", "2020", "00-qb", "linked_to_outcome_labels"),
        _bridge_row("Fixture RB", "RB", "2023", "00-rb", "linked_to_outcome_labels"),
        _bridge_row("Missing Rookie Row", "WR", "2020", "00-wr", "linked_to_outcome_labels"),
        _bridge_row("Unlinked TE", "TE", "2020", "00-te", "blocked_no_outcome_label_rows"),
    ]


def _bridge_row(
    name: str,
    position: str,
    draft_year: str,
    player_id: str,
    link_status: str,
) -> dict[str, str]:
    return {
        "player_name": name,
        "position": position,
        "draft_year": draft_year,
        "rookie_class_year": draft_year,
        "draft_round": "1",
        "draft_pick": "1",
        "drafted_team": "TST",
        "college_team": "Example",
        "nfl_player_id": player_id,
        "gsis_id": player_id,
        "player_stats_id": player_id,
        "nwr_player_id": NOT_ENOUGH,
        "cfbd_player_id": NOT_ENOUGH,
        "outcome_label_link_status": link_status,
        "bridge_status": "linked_review_only_complete_5y",
    }


def _season_rows() -> list[dict[str, str]]:
    return [
        _season_row("00-qb", "2020", "QB", "8", "miss", "hit", "hit", "hit"),
        _season_row("00-qb", "2021", "QB", "5", "hit", "hit", "hit", "hit"),
        _season_row("00-qb", "2022", "QB", "20", "miss", "miss", "hit", "hit"),
        _season_row("00-qb", "2023", "QB", "30", "miss", "miss", "hit", "hit"),
        _season_row("00-qb", "2024", "QB", "31", "miss", "miss", "hit", "hit"),
        _season_row("00-rb", "2023", "RB", "18", "miss", "miss", "hit", "hit"),
        _season_row("00-rb", "2024", "RB", "28", "miss", "miss", "miss", "hit"),
    ]


def _season_row(
    player_id: str,
    season: str,
    position: str,
    finish: str,
    top_6: str,
    top_12: str,
    top_24: str,
    top_36: str,
) -> dict[str, str]:
    return {
        "player_id": player_id,
        "season": season,
        "position": position,
        "position_finish": finish,
        "scoring_mode": EXPECTED_SCORING_MODE,
        "top_6_hit": top_6,
        "top_12_hit": top_12,
        "top_24_hit": top_24,
        "top_36_hit": top_36,
    }
