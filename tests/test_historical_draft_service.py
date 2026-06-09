from __future__ import annotations

from src.services.historical_draft_service import (
    OFFLINE_NOTE_PROVENANCE_NOTE,
    ROOKIE_PROVENANCE_NOTE,
    compare_historical_rookie_replay,
    extract_final_picks_as_rookie_drafts,
    load_historical_rookie_model_replay,
    load_offline_rookie_notes,
    load_yahoo_draft_results,
    reconstruct_historical_rookie_drafts,
)

FIXTURE = "sample_data/historical_yahoo_drafts/final_five_two_seasons.csv"
OFFLINE_NOTES_FIXTURE = (
    "sample_data/historical_rookie_notes/offline_notes_four_seasons.csv"
)
MODEL_REPLAY_FIXTURE = "sample_data/historical_rookie_notes/model_replay_sample.csv"


def test_reconstructor_extracts_final_five_per_season() -> None:
    board = reconstruct_historical_rookie_drafts(FIXTURE)

    assert board.seasons == [2021, 2022]
    assert len(board.entries) == 10
    assert [entry.drafted_player for entry in board.entries if entry.season == 2021] == [
        "Najee Harris",
        "Ja'Marr Chase",
        "Jaylen Waddle",
        "DeVonta Smith",
        "Kyle Pitts",
    ]
    assert [entry.platform_overall_pick for entry in board.entries if entry.season == 2022] == [
        5,
        6,
        7,
        8,
        9,
    ]


def test_reconstructor_stores_rough_confidence_and_traded_pick_warning() -> None:
    board = reconstruct_historical_rookie_drafts(FIXTURE)

    assert board.confidence_labels == ["rough"]
    assert board.review_warning == ROOKIE_PROVENANCE_NOTE
    assert {
        (entry.confidence, entry.provenance_note, entry.needs_traded_pick_review)
        for entry in board.entries
    } == {("rough", ROOKIE_PROVENANCE_NOTE, True)}


def test_final_five_extraction_is_deterministic_even_with_unsorted_input() -> None:
    picks = list(reversed(load_yahoo_draft_results(FIXTURE)))

    first_run = extract_final_picks_as_rookie_drafts(picks)
    second_run = extract_final_picks_as_rookie_drafts(picks)

    assert first_run == second_run
    assert [
        (entry.season, entry.rookie_pick_number, entry.drafted_player)
        for entry in first_run
    ] == [
        (2021, 1, "Najee Harris"),
        (2021, 2, "Ja'Marr Chase"),
        (2021, 3, "Jaylen Waddle"),
        (2021, 4, "DeVonta Smith"),
        (2021, 5, "Kyle Pitts"),
        (2022, 1, "Breece Hall"),
        (2022, 2, "Drake London"),
        (2022, 3, "Garrett Wilson"),
        (2022, 4, "Kenneth Walker"),
        (2022, 5, "Chris Olave"),
    ]


def test_offline_handwritten_notes_are_preferred_source_records() -> None:
    board = load_offline_rookie_notes(OFFLINE_NOTES_FIXTURE)

    assert board.seasons == [2022, 2023, 2024, 2025]
    assert len(board.entries) == 20
    assert board.confidence_labels == ["handwritten_note"]
    assert board.review_warning == OFFLINE_NOTE_PROVENANCE_NOTE
    assert [entry.drafted_player for entry in board.entries if entry.season == 2024] == [
        "Marvin Harrison Jr.",
        "Malik Nabers",
        "Rome Odunze",
        "Brock Bowers",
        "Jayden Daniels",
    ]
    assert {entry.platform_overall_pick for entry in board.entries} == {None}
    assert {entry.needs_traded_pick_review for entry in board.entries} == {True}


def test_historical_model_replay_loads_as_calibration_only_fixture() -> None:
    rows = load_historical_rookie_model_replay(MODEL_REPLAY_FIXTURE)

    assert len(rows) == 15
    assert rows[0].player == "Breece Hall"
    assert rows[0].model_rank == 1
    assert rows[0].outcome_score == 76.0
    assert rows[-1].outcome_score is None


def test_historical_replay_comparison_marks_rank_gaps_and_missing_outcomes() -> None:
    actual = load_offline_rookie_notes(OFFLINE_NOTES_FIXTURE)
    replay = load_historical_rookie_model_replay(MODEL_REPLAY_FIXTURE)
    comparison = compare_historical_rookie_replay(actual, replay)

    assert comparison.seasons == [2022, 2023, 2024, 2025]
    assert comparison.missing_model_count == 5
    assert "missing_model_replay" in comparison.verdicts
    assert "rank_aligned_needs_outcome" in comparison.verdicts

    garrett = next(row for row in comparison.rows if row.drafted_player == "Garrett Wilson")
    assert garrett.rookie_pick_number == 3
    assert garrett.model_rank == 2
    assert garrett.rank_delta == -1
    assert garrett.replay_verdict == "model_aligned"

    missing = next(row for row in comparison.rows if row.drafted_player == "Ashton Jeanty")
    assert missing.model_rank is None
    assert missing.replay_verdict == "missing_model_replay"
