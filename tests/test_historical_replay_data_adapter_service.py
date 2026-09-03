"""Tests for the historical redraft replay data adapter (section 18).

No real Dataset Research Engine handoff exists in this repo (see
docs/codex/HISTORICAL_REPLAY_SUBSTRATE_INVENTORY_20260903.md) -- these
fixtures are small, clearly-synthetic rows built only to exercise the
adapter's own validators/loader/splitter/runner, never presented as real
historical evidence.
"""

from __future__ import annotations

import pytest

from src.services.historical_replay_data_adapter_service import (
    HistoricalReplayDataError,
    HistoricalReplayDataset,
    HistoricalReplayUnavailable,
    chronological_split,
    find_duplicate_player_seasons,
    find_immature_outcome_rows,
    load_historical_replay_dataset,
    run_replay_evaluation,
    validate_historical_dataset,
    validate_identity_completeness,
    validate_leakage,
    validate_schema,
)


def _row(player_id: str, season: int, **overrides) -> dict:
    base = {
        "player_id": player_id,
        "player_name": f"Player {player_id}",
        "position": "RB",
        "team": "TST",
        "season": season,
        "draft_date": "2020-09-01",
        "projection_as_of": "2020-08-15",
        "platform_adp": 42.0,
        "adp_as_of": "2020-08-20",
        "status_as_of": "2020-08-31",
        "scoring_format": "PPR",
    }
    base.update(overrides)
    return base


def test_validate_schema_passes_a_complete_row() -> None:
    result = validate_schema([_row("p1", 2020)])
    assert result.valid is True
    assert result.missing_field_rows == ()
    assert result.unparseable_date_rows == ()


def test_validate_schema_flags_missing_fields() -> None:
    row = _row("p1", 2020)
    del row["platform_adp"]
    result = validate_schema([row])
    assert result.valid is False
    assert result.missing_field_rows == (("p1", ("platform_adp",)),)


def test_validate_schema_flags_unparseable_dates() -> None:
    result = validate_schema([_row("p1", 2020, draft_date="not-a-date")])
    assert result.valid is False
    assert result.unparseable_date_rows == (("p1", "draft_date"),)


def test_validate_leakage_passes_a_clean_row() -> None:
    result = validate_leakage([_row("p1", 2020)])
    assert result.valid is True


def test_validate_leakage_blocks_an_unexpected_leakage_shaped_column() -> None:
    row = _row("p1", 2020, current_season_fantasy_points=250.0)
    result = validate_leakage([row])
    assert result.valid is False
    assert result.blocked_column_rows == (("p1", ("current_season_fantasy_points",)),)


def test_validate_leakage_does_not_block_a_legitimate_outcome_field() -> None:
    row = _row("p1", 2020, realized_weekly_points=[10.0, 12.0], outcome_as_of="2021-01-05")
    result = validate_leakage([row])
    assert result.valid is True


def test_validate_leakage_catches_a_projection_dated_on_or_after_the_draft() -> None:
    result = validate_leakage([_row("p1", 2020, projection_as_of="2020-09-01")])
    assert result.valid is False
    assert ("p1", "projection_as_of") in result.future_dated_rows


def test_validate_leakage_catches_a_status_dated_after_the_draft() -> None:
    result = validate_leakage([_row("p1", 2020, status_as_of="2020-09-02")])
    assert result.valid is False
    assert ("p1", "status_as_of") in result.future_dated_rows


def test_validate_leakage_catches_an_outcome_dated_before_the_draft() -> None:
    row = _row("p1", 2020, realized_weekly_points=[10.0], outcome_as_of="2020-01-01")
    result = validate_leakage([row])
    assert result.valid is False
    assert "p1" in result.outcome_before_draft_rows


def test_validate_identity_completeness_counts_resolved_and_flags_unresolved() -> None:
    rows = [_row("p1", 2020), _row("p2", 2020)]
    picks = [
        {"player_id": "p1"},
        {"player_id": "unknown-player"},  # no identity_status -> flagged invalid
        {"player_id": "unknown-player-2", "identity_status": "UNMATCHED"},  # disclosed, OK
    ]
    result = validate_identity_completeness(picks, rows)
    assert result.resolved_pick_count == 1
    assert result.valid is False  # the undisclosed unresolved pick makes this invalid
    reasons = {p["player_id"]: p["identity_status"] for p in result.unresolved_picks}
    assert reasons["unknown-player"] == "UNFLAGGED_UNRESOLVED"
    assert reasons["unknown-player-2"] == "UNMATCHED"


def test_validate_identity_completeness_is_valid_when_every_gap_is_disclosed() -> None:
    rows = [_row("p1", 2020)]
    picks = [
        {"player_id": "p1"},
        {"player_id": "unknown", "identity_status": "K_DST_UNREPRESENTABLE"},
    ]
    result = validate_identity_completeness(picks, rows)
    assert result.valid is True


def test_load_historical_replay_dataset_is_unavailable_when_empty() -> None:
    result = load_historical_replay_dataset(None)
    assert isinstance(result, HistoricalReplayUnavailable)
    assert "no Dataset Research Engine handoff" in result.reason
    result = load_historical_replay_dataset([])
    assert isinstance(result, HistoricalReplayUnavailable)


def test_load_historical_replay_dataset_is_unavailable_when_invalid() -> None:
    bad_row = _row("p1", 2020, draft_date="not-a-date")
    result = load_historical_replay_dataset([bad_row])
    assert isinstance(result, HistoricalReplayUnavailable)
    assert "failed validation" in result.reason


def test_load_historical_replay_dataset_separates_pre_draft_from_outcome() -> None:
    row = _row("p1", 2020, realized_weekly_points=[10.0, 5.0], outcome_as_of="2021-01-05")
    result = load_historical_replay_dataset([row])
    assert isinstance(result, HistoricalReplayDataset)
    assert result.seasons == (2020,)
    assert len(result.rows) == 1
    loaded = result.rows[0]
    assert "realized_weekly_points" not in loaded.pre_draft
    assert "platform_adp" not in loaded.outcome
    assert loaded.outcome["realized_weekly_points"] == [10.0, 5.0]
    assert loaded.pre_draft["platform_adp"] == 42.0


def _dataset(seasons: list[int]) -> HistoricalReplayDataset:
    rows = [_row(f"p{season}-{i}", season) for season in seasons for i in range(3)]
    loaded = load_historical_replay_dataset(rows)
    assert isinstance(loaded, HistoricalReplayDataset)
    return loaded


def test_chronological_split_partitions_by_season() -> None:
    dataset = _dataset([2018, 2019, 2020])
    split = chronological_split(
        dataset, train_seasons=[2018], validate_seasons=[2019], test_seasons=[2020]
    )
    assert {row.season for row in split.train} == {2018}
    assert {row.season for row in split.validate} == {2019}
    assert {row.season for row in split.test} == {2020}
    assert len(split.train) == 3


def test_chronological_split_rejects_overlapping_seasons() -> None:
    dataset = _dataset([2018, 2019])
    with pytest.raises(HistoricalReplayDataError, match="more than one split"):
        chronological_split(
            dataset, train_seasons=[2018, 2019], validate_seasons=[2019], test_seasons=[]
        )


def test_chronological_split_rejects_an_unassigned_season() -> None:
    dataset = _dataset([2018, 2019, 2020])
    with pytest.raises(HistoricalReplayDataError, match="not assigned"):
        chronological_split(
            dataset, train_seasons=[2018], validate_seasons=[2019], test_seasons=[]
        )


def test_chronological_split_rejects_a_non_chronological_assignment() -> None:
    dataset = _dataset([2018, 2019])
    with pytest.raises(HistoricalReplayDataError, match="strictly earlier"):
        chronological_split(
            dataset, train_seasons=[2019], validate_seasons=[2018], test_seasons=[]
        )


def test_run_replay_evaluation_scores_strategies_by_realized_points() -> None:
    rows = [
        _row(f"p{i}", 2020, realized_weekly_points=[float(100 - i * 5)])
        for i in range(8)
    ]
    dataset = load_historical_replay_dataset(rows)
    assert isinstance(dataset, HistoricalReplayDataset)

    def best_points_first(available):
        return sorted(
            available, key=lambda row: -row.outcome.get("realized_weekly_points", [0])[0]
        )

    def worst_points_first(available):
        return sorted(
            available, key=lambda row: row.outcome.get("realized_weekly_points", [0])[0]
        )

    results = run_replay_evaluation(
        dataset.rows,
        season=2020,
        team_count=2,
        rounds=2,
        strategies={"BEST_FIRST": best_points_first, "WORST_FIRST": worst_points_first},
    )
    by_name = {r.strategy_name: r for r in results}
    best, worst = by_name["BEST_FIRST"], by_name["WORST_FIRST"]
    assert best.total_realized_points > worst.total_realized_points
    assert best.team_count == 2
    assert len(by_name["BEST_FIRST"].per_team_points) == 2


def test_run_replay_evaluation_rejects_too_few_available_players() -> None:
    rows = [_row("p1", 2020, realized_weekly_points=[10.0])]
    dataset = load_historical_replay_dataset(rows)
    assert isinstance(dataset, HistoricalReplayDataset)
    with pytest.raises(HistoricalReplayDataError, match="cannot run a replay"):
        run_replay_evaluation(
            dataset.rows, season=2020, team_count=4, rounds=1, strategies={"X": lambda a: a}
        )


# --- Section 20: explicit BLOCKED_* status codes against synthetic
# contract data -- these fixtures exercise adapter mechanics only, never
# treated as real historical evidence.


def test_find_duplicate_player_seasons_flags_a_real_duplicate() -> None:
    rows = [_row("p1", 2020), _row("p1", 2020, player_name="Player p1 (dup row)"), _row("p2", 2020)]
    duplicates = find_duplicate_player_seasons(rows)
    assert duplicates == (("p1", 2020),)


def test_find_duplicate_player_seasons_allows_the_same_player_across_different_seasons() -> None:
    rows = [_row("p1", 2020), _row("p1", 2021)]
    assert find_duplicate_player_seasons(rows) == ()


def test_find_immature_outcome_rows_flags_a_too_recent_outcome_snapshot() -> None:
    mature = _row("p1", 2020, realized_weekly_points=[10.0], outcome_as_of="2021-01-25")  # ~146d
    immature = _row("p2", 2020, realized_weekly_points=[10.0], outcome_as_of="2020-10-01")  # ~30d
    no_outcome_yet = _row("p3", 2020)  # pre-draft-only row -- not flagged
    result = find_immature_outcome_rows([mature, immature, no_outcome_yet])
    assert result == ("p2",)


def test_validate_historical_dataset_reports_ok_for_a_fully_clean_dataset() -> None:
    rows = [_row("p1", 2020, realized_weekly_points=[10.0], outcome_as_of="2021-02-01")]
    outcome = validate_historical_dataset(rows)
    assert outcome.status == "OK"
    assert outcome.duplicate_player_seasons == ()
    assert outcome.immature_outcome_rows == ()


@pytest.mark.parametrize(
    "rows_factory,expected_status",
    [
        pytest.param(
            lambda: [{**_row("p1", 2020), "draft_date": "not-a-date"}],
            "BLOCKED_SCHEMA", id="missing-required-field-shape",
        ),
        pytest.param(
            lambda: [_row("p1", 2020, current_season_fantasy_points=250.0)],
            "BLOCKED_LEAKAGE", id="leakage-shaped-column",
        ),
        pytest.param(
            lambda: [_row("p1", 2020), _row("p1", 2020, player_name="dup")],
            "BLOCKED_DUPLICATE_PLAYER_SEASON", id="duplicate-player-season",
        ),
        pytest.param(
            lambda: [
                _row("p1", 2020, realized_weekly_points=[10.0], outcome_as_of="2020-10-01")
            ],
            "BLOCKED_IMMATURE_OUTCOME", id="immature-outcome",
        ),
    ],
)
def test_validate_historical_dataset_named_statuses(rows_factory, expected_status) -> None:
    outcome = validate_historical_dataset(rows_factory())
    assert outcome.status == expected_status


def test_validate_historical_dataset_reports_blocked_identity_when_picks_supplied() -> None:
    rows = [_row("p1", 2020)]
    picks = [{"player_id": "p1"}, {"player_id": "unknown-player"}]  # unknown, undisclosed
    outcome = validate_historical_dataset(rows, historical_picks=picks)
    assert outcome.status == "BLOCKED_IDENTITY"
    assert outcome.identity is not None
    assert outcome.identity.valid is False


def test_validate_historical_dataset_skips_identity_check_when_no_picks_supplied() -> None:
    rows = [_row("p1", 2020, realized_weekly_points=[10.0], outcome_as_of="2021-02-01")]
    outcome = validate_historical_dataset(rows)
    assert outcome.identity is None
    assert outcome.status == "OK"


def test_validate_historical_dataset_priority_order_schema_before_everything_else() -> None:
    """A row that fails schema AND would also trigger leakage/duplicate
    checks still reports BLOCKED_SCHEMA -- nothing else is meaningful to
    check once the shape itself is wrong."""
    bad_rows = [
        {**_row("p1", 2020), "draft_date": "not-a-date"},
        {**_row("p1", 2020), "draft_date": "not-a-date"},  # also a duplicate player-season
    ]
    outcome = validate_historical_dataset(bad_rows)
    assert outcome.status == "BLOCKED_SCHEMA"


def test_chronological_split_is_the_explicit_train_validation_test_chronology_check() -> None:
    """Section 20's "train/validation/test chronology" check is
    chronological_split's own strictly-earlier enforcement (already
    tested elsewhere in this file) -- re-asserted here as the named
    outcome for this exact scenario category."""
    rows = [_row("p1", 2018), _row("p1", 2019)]
    dataset = load_historical_replay_dataset(rows)
    assert isinstance(dataset, HistoricalReplayDataset)
    with pytest.raises(HistoricalReplayDataError, match="strictly earlier"):
        chronological_split(
            dataset, train_seasons=[2019], validate_seasons=[2018], test_seasons=[]
        )
