from __future__ import annotations

from src.services.nflverse_schedule_context_display_service import (
    NOT_ENOUGH_INFORMATION,
    SAFE_NOW_DISPLAY_ONLY,
    load_schedule_context_index,
    schedule_context_counts,
    schedule_context_display_for_row,
)


def test_tracked_schedule_context_counts_match_display_gate() -> None:
    index = load_schedule_context_index()
    counts = schedule_context_counts(index)

    assert index.errors == ()
    assert counts["artifact_rows"] == 294
    assert counts["safe_schedule_rows"] == 240
    assert counts["identity_review_rows"] == 54
    assert counts["safe_next_game_rows"] == 240
    assert counts["safe_opponent_rows"] == 240
    assert counts["safe_bye_rows"] == 240


def test_safe_row_displays_raw_and_parsed_schedule_context() -> None:
    index = load_schedule_context_index()
    puka = next(row for row in index.artifact_rows if row["nwr_player_id"] == "9493")

    display = schedule_context_display_for_row(puka, index.schema_safe_fields)

    assert display.available
    assert display.status == SAFE_NOW_DISPLAY_ONLY
    assert display.next_game_context == (
        "season=2026; week=1; date=2026-09-10; game_id=2026_01_SF_LA"
    )
    assert display.opponent_context == "opponent=SF; home_away=home"
    assert display.bye_context == "week=11"
    assert display.game_date == "2026-09-10"
    assert display.game_week == "1"
    assert display.home_away == "home"
    assert display.season == "2026"
    assert display.team == "LA"


def test_identity_review_row_exposes_no_schedule_detail_even_if_values_exist() -> None:
    row = _safe_base_row()
    row.update(
        {
            "identity_join_status": "NEED_IDENTITY_REVIEW",
            "review_required": "true",
            "next_game_context": "season=2026; week=1; date=2026-09-10",
            "opponent_context": "opponent=SF; home_away=home",
            "bye_context": "week=11",
        }
    )

    display = schedule_context_display_for_row(row, _schema_safe_fields())

    assert not display.available
    assert display.next_game_context == NOT_ENOUGH_INFORMATION
    assert display.opponent_context == NOT_ENOUGH_INFORMATION
    assert display.bye_context == NOT_ENOUGH_INFORMATION
    assert display.game_date == NOT_ENOUGH_INFORMATION
    assert display.game_week == NOT_ENOUGH_INFORMATION
    assert display.home_away == NOT_ENOUGH_INFORMATION


def test_missing_schedule_data_is_not_presented_as_positive_or_zero_context() -> None:
    row = _safe_base_row()
    row.update(
        {
            "next_game_context": NOT_ENOUGH_INFORMATION,
            "opponent_context": "",
            "bye_context": "NEED_DATASET_REFRESH",
        }
    )

    display = schedule_context_display_for_row(row, _schema_safe_fields())
    text = " ".join(display.as_display_row().values()).lower()

    assert not display.available
    assert display.next_game_context == NOT_ENOUGH_INFORMATION
    assert display.opponent_context == NOT_ENOUGH_INFORMATION
    assert display.bye_context == NOT_ENOUGH_INFORMATION
    for forbidden in ("favorable", "neutral", "easy", "hard", "healthy", "clean", "safe", "0"):
        assert forbidden not in text


def test_missing_schema_gate_blocks_schedule_context_for_safe_row() -> None:
    row = _safe_base_row()

    display = schedule_context_display_for_row(
        row,
        _schema_safe_fields() - {"opponent_context"},
    )

    assert not display.available
    assert display.next_game_context == NOT_ENOUGH_INFORMATION
    assert display.opponent_context == NOT_ENOUGH_INFORMATION
    assert display.bye_context == NOT_ENOUGH_INFORMATION


def _safe_base_row() -> dict[str, str]:
    return {
        "nwr_player_id": "player-1",
        "nwr_player_name": "Example Player",
        "nwr_position": "WR",
        "nwr_team": "LAR",
        "nflverse_team": "LA",
        "identity_join_status": SAFE_NOW_DISPLAY_ONLY,
        "review_required": "false",
        "display_only": "true",
        "model_use_allowed": "false",
        "training_allowed": "false",
        "source_truth_allowed": "false",
        "rank_logic_allowed": "false",
        "hidden_sort_allowed": "false",
        "trade_value_allowed": "false",
        "pick_value_allowed": "false",
        "next_game_context": "season=2026; week=1; date=2026-09-10",
        "opponent_context": "opponent=SF; home_away=home",
        "bye_context": "week=11",
    }


def _schema_safe_fields() -> set[str]:
    return set(_safe_base_row())
